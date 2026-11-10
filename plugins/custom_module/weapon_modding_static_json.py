"""Publish complete firearm modding bundles from the public modding API."""
from collections import deque
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from uuid import uuid4

from custom_module.static_api_client import get_api_response
from custom_module.preset_reconstruction_contract import validate_preset_reconstruction
from custom_module.trader_static_json import write_atomic

API_BASE_URL = 'https://back.eftlibrary.com/api/modding/v3'
OUTPUT_DIR = Path('/opt/airflow/next-public')
PUBLIC_BASE_PATH = '/static/modding/v3'
PAGE_SIZE = 100
MAX_PAGES = 10000
MAX_ITEMS = 50000
SOURCE_LOCK = 724106110  # Same transaction lock as dags_item.


def fetch_data(endpoint, **params):
    query = '?' + urlencode(params) if params else ''
    payload = get_api_response(f'{API_BASE_URL}/{endpoint}{query}', 60).json()
    if (not isinstance(payload, dict) or payload.get('status') != 200
            or payload.get('msg') != 'OK' or not isinstance(payload.get('data'), dict)):
        raise ValueError('Invalid modding API response')
    return payload['data']


def valid_id(value):
    # IDs are used as filenames. Reject special path components even when URL-encoded.
    if not isinstance(value, str) or not value or value.strip() != value or value in ('.', '..'):
        raise ValueError('Invalid modding ID')
    return value


def item_id(entry):
    return valid_id(entry['item']['id'])


def path_id(value):
    return quote(valid_id(value), safe='')


def array(data, key):
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f'Invalid modding array: {key}')
    return value


def collect_pages(endpoint, field, fetch, expected=None):
    """Flatten complete API pages, retaining context but removing pagination fields."""
    result, seen, metadata = [], set(), None
    for page in range(1, MAX_PAGES + 1):
        data = fetch(endpoint, page=page, page_size=PAGE_SIZE)
        total = data.get('total')
        if (type(total) is not int or total < 0 or data.get('page') != page
                or data.get('page_size') != PAGE_SIZE):
            raise ValueError('Invalid pagination metadata')
        context = {k: v for k, v in data.items() if k not in (field, 'page', 'page_size')}
        if expected and any(data.get(k) != v for k, v in expected.items()):
            raise ValueError('Modding response scope mismatch')
        if metadata is not None and context != metadata:
            raise ValueError('Modding pagination metadata changed')
        metadata = context
        values = array(data, field)
        if len(values) != min(PAGE_SIZE, max(0, total - len(result))):
            raise ValueError('Incomplete modding page')
        for entry in values:
            key = item_id(entry)
            if key in seen:
                raise ValueError('Duplicate modding item across pages')
            seen.add(key)
            result.append(entry)
        if len(result) == total:
            return {**metadata, field: result}
    raise ValueError('Modding pagination limit exceeded')


def collect_snapshot(fetch=fetch_data):
    """Cache each reachable item/slot once; traverse candidates and preset components."""
    listing = collect_pages('weapons', 'weapons', fetch)
    if not listing['weapons']:
        raise ValueError('Cannot publish an empty firearm list')
    items, candidates, presets, references, seeds = {}, {}, {}, {}, {}
    summaries = {}
    pending, queued = deque(), set()

    def enqueue(summary):
        key = valid_id(summary['id'])
        slot_count = summary.get('slot_count')
        if type(slot_count) is not int or slot_count < 0:
            raise ValueError('Invalid item slot_count')
        if key in summaries and summaries[key] != summary:
            raise ValueError('Item summary changed during collection')
        summaries[key] = summary
        if key not in queued:
            if len(queued) >= MAX_ITEMS:
                raise ValueError('Modding item traversal limit exceeded')
            queued.add(key)
            pending.append(key)
        return key

    for weapon in listing['weapons']:
        wid = enqueue(weapon['item'])
        links = collect_pages(f'weapons/{path_id(wid)}/presets', 'presets', fetch,
                              {'weapon_item_id': wid})
        if weapon.get('preset_count') != links['total']:
            raise ValueError('Weapon preset count changed')
        if 'default_preset' not in weapon:
            raise ValueError('Missing default_preset summary; deploy the new modding API first')
        defaults = [entry for entry in links['presets'] if entry['link']['is_default_reference']]
        if len(defaults)>1:
            raise ValueError('Multiple default preset references')
        expected_default = ({field: defaults[0]['item'].get(field)
                             for field in ('id','name_en','name_ko','name_ja','image')}
                            if defaults else None)
        if weapon['default_preset'] != expected_default:
            raise ValueError('Default preset summary/reference mismatch')
        references[wid] = links
        seeds[wid] = {wid}
        for entry in links['presets']:
            pid = item_id(entry)
            if pid not in presets:
                detail = fetch(f'presets/{path_id(pid)}')
                if (item_id(detail['preset']) != pid
                        or detail.get('composition_type') != 'flat_source_list'):
                    raise ValueError('Invalid preset detail')
                array(detail, 'weapon_links')
                for component in array(detail, 'components'):
                    if type(component['quantity']) is not int or component['quantity'] <= 0:
                        raise ValueError('Invalid preset component quantity')
                    enqueue(component['item'])
                validate_preset_reconstruction(detail)
                presets[pid] = detail
            # Link flags are separate from the preset's own is_default value.
            if {k: v for k, v in entry.items() if k != 'link'} != presets[pid]['preset']:
                raise ValueError('Preset summary changed during collection')
            seeds[wid].update(component['item']['id'] for component in presets[pid]['components'])

    edges = {}
    while pending:
        key = pending.popleft()
        detail = fetch(f'items/{path_id(key)}')
        if item_id(detail) != key or detail['item'] != summaries[key]:
            raise ValueError('Item detail/summary mismatch')
        slots = array(detail, 'slots')
        if len(slots) != summaries[key]['slot_count']:
            raise ValueError('Item slot count changed')
        array(detail, 'categories')
        array(detail, 'allowed_ammo')
        for field in ('items', 'categories', 'slots'):
            array(detail['conflicts'], field)
        items[key] = detail
        candidates[key], edges[key] = {}, set()
        for slot in slots:
            sid = valid_id(slot['slot_id'])
            if slot['item_id'] != key or sid in candidates[key]:
                raise ValueError('Duplicate slot or invalid owner')
            for field in ('allowed_items', 'excluded_items', 'allowed_categories', 'excluded_categories'):
                array(slot['filters'], field)
            page = collect_pages(f'items/{path_id(key)}/slots/{path_id(sid)}/candidates',
                                 'candidates', fetch, {'item_id': key, 'slot_id': sid,
                                                      'validation_scope': 'slot_filters_only'})
            candidates[key][sid] = page
            edges[key].update(enqueue(entry['item']) for entry in page['candidates'])

    # The production caller also holds the ingestion lock across all API reads.
    if collect_pages('weapons', 'weapons', fetch) != listing:
        raise ValueError('Weapon list changed during collection')
    bundles = {}
    for weapon in listing['weapons']:
        wid = item_id(weapon)
        reachable, work = set(), list(seeds[wid])
        while work:
            key = work.pop()
            if key in reachable:
                continue
            reachable.add(key)
            work.extend(edges[key] - reachable)
        bundles[wid] = {
            'weapon': weapon,
            'items': {key: items[key] for key in sorted(reachable)},
            'slot_candidates': {key: candidates[key] for key in sorted(reachable)},
            'preset_references': references[wid],
            'presets': {item_id(entry): presets[item_id(entry)] for entry in references[wid]['presets']},
            'validation_scope': 'slot_filters_only',
            'composition_type': 'flat_source_list',
            'preset_reconstruction_version': 1,
        }
    return listing, bundles


def generate_weapon_modding_static_json(output_dir=None, fetch=fetch_data):
    """Build every bundle before atomically publishing the new index."""
    listing, bundles = collect_snapshot(fetch)
    root = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    base = root / 'static/modding/v3'
    generation = uuid4().hex
    folder = Path('snapshots') / generation
    public = f'{PUBLIC_BASE_PATH}/{folder.as_posix()}'
    generated = datetime.now(timezone.utc).isoformat()

    def envelope(data):
        return {'status': 200, 'msg': 'OK', 'generated_at': generated, 'data': data}

    write_atomic(base / folder / 'weapons.json', envelope(listing))
    paths = {}
    for key, bundle in bundles.items():
        filename = path_id(key) + '.json'
        write_atomic(base / folder / 'weapons' / filename, envelope(bundle))
        paths[key] = f'{public}/weapons/{filename}'
    manifest = {'generation': generation, 'schema_version': 1,
                'weapons_list': f'{public}/weapons.json', 'weapons': paths,
                'total': len(paths), 'preset_reconstruction_version': 1}
    write_atomic(base / 'index.json', envelope(manifest))
    print('Weapon modding static JSON published:', {'generation': generation, 'weapons': len(paths)})
    return manifest


def publish_weapon_modding_static_json(postgres_conn_id='platform_db'):
    """Prevent dags_item from changing the API's DB during this multi-request export."""
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    with closing(PostgresHook(postgres_conn_id).get_conn()) as conn:
        conn.autocommit = False
        with conn.cursor() as cursor:
            cursor.execute('SET LOCAL lock_timeout = \'60s\'')
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', (SOURCE_LOCK,))
            return generate_weapon_modding_static_json()
