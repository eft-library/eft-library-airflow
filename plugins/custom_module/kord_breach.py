"""Synchronize KORD BREACH metadata without changing user selections."""
from contextlib import closing
import json
from pathlib import Path

from custom_module.tarkov_json_api import get_json_data

MAPPING_PATH = Path(__file__).with_name('kord_breach_mapping.json')
TABLES = ('kord_breach_modifier', 'kord_breach_modifier_conflict',
          'user_kord_breach_preset', 'user_kord_breach_preset_modifier')


def load_mapping():
    mapping = json.loads(MAPPING_PATH.read_text())
    entries = mapping['modifiers']
    for key in ('source_id', 'legacy_id'):
        values = [row[key] for row in entries]
        if not values or len(values) != len(set(values)):
            raise ValueError(f'Duplicate or missing mapping {key}')
    if any(row['category'] not in ('global', 'positive', 'negative') for row in entries):
        raise ValueError('Unknown modifier category')
    return mapping


def _index(payload, season_id):
    if payload.get('id') != season_id:
        raise ValueError('Season changed: KORD BREACH requires explicit season mapping review')
    perks = payload.get('perks')
    if not isinstance(perks, dict) or set(perks) != {'common', 'personal'}:
        raise ValueError('Invalid season perks')
    result = {}
    for group, rows in perks.items():
        if not isinstance(rows, list) or not rows:
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
    if any(target not in result for _, row in result.values() for target in row['exclusiveToPerks']):
        raise ValueError('Conflict references unknown perk')
    return result


def normalize_season(localized, mapping):
    indices = {lang: _index(payload, mapping['season_id']) for lang, payload in localized.items()}
    expected = {row['source_id'] for row in mapping['modifiers']}
    if set(indices) != {'en', 'ko', 'ja'} or any(set(index) != expected for index in indices.values()):
        raise ValueError('Source perk IDs differ from reviewed mapping; review additions/removals first')
    def translated(lang, identity, field):
        value = indices[lang][identity][1].get(field)
        if not isinstance(value, str) or not value.strip() or value in (identity + ' name', identity + ' description'):
            if lang == 'en':
                raise ValueError('Missing English perk text')
            return None
        return value
    rows, conflicts = [], set()
    for entry in mapping['modifiers']:
        identity = entry['source_id']
        group, source = indices['en'][identity]
        if (group == 'common') != (entry['category'] == 'global'):
            raise ValueError('Common/personal category changed')
        signature = (group, source['points'], set(source['exclusiveToPerks']))
        for index in indices.values():
            current_group, current = index[identity]
            if (current_group, current['points'], set(current['exclusiveToPerks'])) != signature:
                raise ValueError('Season metadata changed between language requests')
        image = source.get('imageLink')
        if not isinstance(image, str) or not image.startswith('https://'):
            raise ValueError('Invalid perk icon URL')
        rows.append((identity, entry['category'],
                     *(translated(lang, identity, 'name') for lang in ('en', 'ko', 'ja')),
                     *(translated(lang, identity, 'description') for lang in ('en', 'ko', 'ja')),
                     source['points'] if source['points'] is not None else 0, image, entry['sort_order']))
        for target in source['exclusiveToPerks']:
            # Exclusivity is symmetric even if the source only lists one direction.
            conflicts.update(((identity, target), (target, identity)))
    return rows, sorted(conflicts)


def fetch_modifiers(mapping):
    payloads = {lang: get_json_data('season', lang, 'pvp-season') for lang in ('en', 'ko', 'ja')}
    rows, conflicts = normalize_season(payloads, mapping)
    final = get_json_data('season', None, 'pvp-season')
    # Names are translation keys in the raw response; compare structural content only.
    initial_index = _index(payloads['en'], mapping['season_id'])
    final_index = _index(final, mapping['season_id'])
    def signature(index):
        return {key: (group, row['points'], sorted(row['exclusiveToPerks'])) for key, (group, row) in index.items()}
    if signature(initial_index) != signature(final_index):
        raise ValueError('Season changed during collection')
    return rows, conflicts


def persist_modifiers(cursor, rows, conflicts, mapping, execute_values):
    from custom_module.queries import kord_breach as sql

    cursor.execute('SET LOCAL lock_timeout = \'10s\'')
    cursor.execute('LOCK TABLE ' + ', '.join(TABLES) + ' IN SHARE ROW EXCLUSIVE MODE')
    cursor.execute('SELECT id FROM kord_breach_modifier')
    current = {row[0] for row in cursor.fetchall()}
    expected = {entry['source_id'] for entry in mapping['modifiers']}
    if current - expected:
        raise ValueError('Legacy/unknown modifier IDs found; run the reviewed ID migration first')
    execute_values(cursor, sql.UPSERT_MODIFIERS, rows, page_size=100)
    cursor.execute('SELECT DISTINCT modifier_id FROM user_kord_breach_preset_modifier')
    if {row[0] for row in cursor.fetchall()} - expected:
        raise ValueError('Preset references unknown modifier ID; transaction cancelled')
    # Keep curated reasons on surviving edges; new edges have no invented explanation.
    cursor.execute('SELECT modifier_id, conflict_modifier_id, reason FROM kord_breach_modifier_conflict')
    reasons = {(a, b): reason for a, b, reason in cursor.fetchall()}
    cursor.execute('DELETE FROM kord_breach_modifier_conflict')
    if conflicts:
        execute_values(cursor, sql.INSERT_CONFLICTS,
                       [(a, b, reasons.get((a, b))) for a, b in conflicts], page_size=100)
    cursor.execute(sql.RECALCULATE_SCORES)


def sync_kord_breach_modifiers(postgres_conn_id='platform_db'):
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    mapping = load_mapping()
    rows, conflicts = fetch_modifiers(mapping)
    with closing(PostgresHook(postgres_conn_id).get_conn()) as connection:
        with connection, closing(connection.cursor()) as cursor:
            persist_modifiers(cursor, rows, conflicts, mapping, execute_values)
    print(f'KORD BREACH synced: modifiers={len(rows)}, directed conflicts={len(conflicts)}')
