"""Synchronize KORD BREACH metadata without changing user selections."""
from contextlib import closing
from custom_module.tarkov_json_api import get_json_data

TABLES = ('kord_breach_modifier', 'kord_breach_modifier_conflict',
          'user_kord_breach_preset', 'user_kord_breach_preset_modifier')


def _index(payload, season_id):
    if payload.get('id') != season_id:
        raise ValueError('Season changed during collection')
    perks = payload.get('perks')
    if not isinstance(perks, dict) or set(perks) != {'common', 'personal'}:
        raise ValueError('Invalid season perks')
    result = {}
    for group, rows in perks.items():
        if not isinstance(rows, list):
            raise ValueError('Empty perk group')
        for row in rows:
            identity = row.get('id')
            if not isinstance(identity, str) or not identity or identity in result:
                raise ValueError('Invalid/duplicate perk ID')
            points = row.get('points')
            if (group == 'personal' and type(points) is not int) or (group == 'common' and points is not None and type(points) is not int):
                raise ValueError('Invalid perk points')
            conflicts = row.get('exclusiveToPerks')
            if not isinstance(conflicts, list) or any(not isinstance(v, str) or not v for v in conflicts):
                raise ValueError('Invalid conflict list')
            if identity in conflicts:
                raise ValueError('Self-conflicting perk')
            result[identity] = (group, row)
    if not result:
        raise ValueError('Empty season perks')
    if any(target not in result for _, row in result.values() for target in row['exclusiveToPerks']):
        raise ValueError('Conflict references unknown perk')
    return result


def _signature(index):
    return [(key, group, row['points'], sorted(row['exclusiveToPerks']), row.get('imageLink'))
            for key, (group, row) in index.items()]


def normalize_season(localized):
    if set(localized) != {'en', 'ko', 'ja'}:
        raise ValueError('Missing language response')
    season_id = localized['en'].get('id')
    if not isinstance(season_id, str) or not season_id.strip():
        raise ValueError('Missing season ID')
    indices = {lang: _index(payload, season_id) for lang, payload in localized.items()}
    initial = indices['en']
    if any(_signature(index) != _signature(initial) for index in indices.values()):
        raise ValueError('Season metadata changed between language requests')

    def translated(lang, identity, field):
        value = indices[lang][identity][1].get(field)
        if not isinstance(value, str) or not value.strip() or value in (identity + ' name', identity + ' description'):
            if lang == 'en':
                raise ValueError('Missing English perk text')
            return None
        return value

    rows, conflicts = [], set()
    for sort_order, (identity, (group, source)) in enumerate(initial.items(), start=1):
        points = source['points'] if source['points'] is not None else 0
        # Match the existing UI/scoring convention: benefits spend points and
        # penalties grant points. Common perks are always displayed separately.
        category = 'global' if group == 'common' else ('positive' if points < 0 else 'negative')
        image = source.get('imageLink')
        if not isinstance(image, str) or not image.startswith('https://'):
            raise ValueError('Invalid perk icon URL')
        rows.append((identity, category,
                     *(translated(lang, identity, 'name') for lang in ('en', 'ko', 'ja')),
                     *(translated(lang, identity, 'description') for lang in ('en', 'ko', 'ja')),
                     points, image, sort_order))
        for target in source['exclusiveToPerks']:
            conflicts.update(((identity, target), (target, identity)))
    return rows, sorted(conflicts)


def get_season_snapshot():
    localized = {lang: get_json_data('season', lang, 'pvp-season') for lang in ('en', 'ko', 'ja')}
    final = get_json_data('season', None, 'pvp-season')
    return {'localized': localized, 'final': final}


def normalize_snapshot(snapshot):
    payloads, final = snapshot['localized'], snapshot['final']
    rows, conflicts = normalize_season(payloads)
    # Raw names are translation keys, so compare structural content only.
    initial_index = _index(payloads['en'], payloads['en']['id'])
    final_index = _index(final, payloads['en']['id'])
    if _signature(initial_index) != _signature(final_index):
        raise ValueError('Season changed during collection')
    return rows, conflicts


def persist_modifiers(cursor, rows, conflicts, execute_values):
    from custom_module.queries import kord_breach as sql

    if not rows:
        raise ValueError('Empty season perks')
    cursor.execute("SET LOCAL lock_timeout = '10s'")
    cursor.execute('LOCK TABLE ' + ', '.join(TABLES) + ' IN SHARE ROW EXCLUSIVE MODE')
    execute_values(cursor, sql.UPSERT_MODIFIERS, rows, page_size=100)
    cursor.execute(sql.DEACTIVATE_MISSING, ([row[0] for row in rows],))
    # Retain missing modifier rows so saved user selections still reference them.
    # Keep curated reasons on surviving edges; new edges need no invented reason.
    cursor.execute('SELECT modifier_id, conflict_modifier_id, reason FROM kord_breach_modifier_conflict')
    reasons = {(a, b): reason for a, b, reason in cursor.fetchall()}
    cursor.execute('DELETE FROM kord_breach_modifier_conflict')
    if conflicts:
        execute_values(cursor, sql.INSERT_CONFLICTS,
                       [(a, b, reasons.get((a, b))) for a, b in conflicts], page_size=100)
    cursor.execute(sql.RECALCULATE_SCORES)


def upsert_kord_breach_modifiers(snapshot, postgres_conn_id='platform_db'):
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    rows, conflicts = normalize_snapshot(snapshot)
    with closing(PostgresHook(postgres_conn_id).get_conn()) as connection:
        with connection, closing(connection.cursor()) as cursor:
            persist_modifiers(cursor, rows, conflicts, execute_values)
    print(f'KORD BREACH synced: modifiers={len(rows)}, directed conflicts={len(conflicts)}')
