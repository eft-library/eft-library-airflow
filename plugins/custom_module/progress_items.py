"""Maintain item checklists from reviewed quest objectives, preserving user progress."""
from contextlib import closing

from custom_module.tarkov_json_api import get_json_data

# Rebirth intentionally tracks the first prestige's figurine candidates, not every
# prestige condition, currency requirement, or later-level Collector requirement.
COLLECTOR_TASK_ID = '5c51aac186f77432ea65c552'
REBIRTH_TASK_ID = '6761f28a022f60bb320f3e95'


def normalize_progress_items(data):
    if not isinstance(data, dict):
        raise ValueError('Invalid tasks snapshot')
    tasks = data.get('tasks')
    if isinstance(tasks, dict):
        tasks = list(tasks.values())
    if not isinstance(tasks, list) or not tasks:
        raise ValueError('Empty tasks snapshot')
    indexed = {}
    for task in tasks:
        identity = task.get('id')
        if not isinstance(identity, str) or not identity or identity in indexed:
            raise ValueError('Invalid/duplicate quest ID')
        indexed[identity] = task
    prestige = data.get('prestige')
    if not isinstance(prestige, list):
        raise ValueError('Missing prestige data')
    first_levels = [p for p in prestige if p.get('prestigeLevel') == 1]
    if len(first_levels) != 1:
        raise ValueError('Missing/duplicate first prestige')
    conditions = first_levels[0].get('conditions')
    if not isinstance(conditions, list) or not any(
        c.get('type') == 'taskStatus' and c.get('task') == REBIRTH_TASK_ID
        and c.get('status') == ['complete'] and not c.get('optional', False)
        for c in conditions
    ):
        raise ValueError('First prestige no longer requires the reviewed New Beginning quest')
    result = {}
    for progress_type, task_id in [('Kappa', COLLECTOR_TASK_ID), ('Rebirth', REBIRTH_TASK_ID)]:
        task = indexed.get(task_id)
        if task is None:
            raise ValueError(f'Missing {progress_type} source quest')
        objectives = task.get('objectives')
        if not isinstance(objectives, list) or not objectives:
            raise ValueError(f'Missing {progress_type} objectives')
        item_ids = set()
        for objective in objectives:
            if objective.get('type') != 'giveItem' or objective.get('optional', False):
                continue
            candidates = objective.get('items')
            count = objective.get('count')
            if not isinstance(candidates, list) or not candidates or type(count) is not int or count <= 0:
                raise ValueError('Invalid required giveItem objective')
            for identity in candidates:
                if not isinstance(identity, str) or not identity.strip():
                    raise ValueError('Missing objective item ID')
                item_ids.add(identity)
        if not item_ids:
            raise ValueError(f'Empty {progress_type} checklist')
        result[progress_type] = sorted(item_ids)
    return result


def persist_progress_items(cursor, groups, execute_values):
    from custom_module.queries import progress as sql

    if set(groups) != {'Kappa', 'Rebirth'} or any(not values for values in groups.values()):
        raise ValueError('Both complete checklist groups are required')
    cursor.execute("SET LOCAL lock_timeout = '10s'")
    cursor.execute('LOCK TABLE progress_item IN SHARE ROW EXCLUSIVE MODE')
    cursor.execute(sql.PRIMARY_KEY_COLUMNS)
    if cursor.fetchone()[0] != ['id', 'progress_type']:
        raise ValueError('Apply the progress_item composite-primary-key migration first')
    ids = sorted({identity for values in groups.values() for identity in values})
    cursor.execute('SELECT id FROM items WHERE id = ANY(%s)', (ids,))
    missing = set(ids) - {row[0] for row in cursor.fetchall()}
    if missing:
        raise ValueError(f'Run dags_item first: checklist items missing from DB: {sorted(missing)}')
    execute_values(cursor, sql.UPSERT_ITEMS,
                   [(identity, progress_type) for progress_type, values in groups.items() for identity in values],
                   page_size=500)
    for progress_type, values in groups.items():
        cursor.execute(sql.DELETE_OBSOLETE_ITEMS, (progress_type, values))
    # user_progress_item is deliberately not written or pruned.


def sync_progress_items(postgres_conn_id='platform_db'):
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    groups = normalize_progress_items(get_json_data('tasks', None, 'regular'))
    with closing(PostgresHook(postgres_conn_id).get_conn()) as connection:
        with connection, closing(connection.cursor()) as cursor:
            persist_progress_items(cursor, groups, execute_values)
    print('Progress item checklist synced:', {key: len(values) for key, values in groups.items()})
