"""Publish complete firearm modding bundles from the public modding API."""
from collections import deque
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
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


def log_progress(message):
    print(f'[modding-static] {message}', flush=True)


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
        page_started = monotonic()
        log_progress(f'API start: {endpoint} page={page} page_size={PAGE_SIZE}')
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
        log_progress(f'API done: {endpoint} page={page} rows={len(result)}/{total} '
                     f'elapsed={monotonic() - page_started:.2f}s')
        if len(result) == total:
            return {**metadata, field: result}
    raise ValueError('Modding pagination limit exceeded')


def collect_snapshot(fetch=fetch_data):
    """Cache each reachable item/slot once; traverse candidates and preset components."""
    started = monotonic()
    log_progress('collection start: fetching firearm list')
    listing = collect_pages('weapons', 'weapons', fetch)
    if not listing['weapons']:
        raise ValueError('Cannot publish an empty firearm list')
    log_progress(f'firearm list ready: weapons={listing["total"]}')
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

    for index, weapon in enumerate(listing['weapons'], start=1):
        wid = enqueue(weapon['item'])
        log_progress(f'weapon {index}/{listing["total"]}: {wid} presets start')
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
                preset_started = monotonic()
                log_progress(f'preset detail start: weapon={wid} preset={pid}')
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
                log_progress(f'preset detail done: {pid} components={len(detail["components"])} '
                             f'cached_presets={len(presets)} elapsed={monotonic() - preset_started:.2f}s')
            # Link flags are separate from the preset's own is_default value.
            if {k: v for k, v in entry.items() if k != 'link'} != presets[pid]['preset']:
                raise ValueError('Preset summary changed during collection')
            seeds[wid].update(component['item']['id'] for component in presets[pid]['components'])
        log_progress(f'weapon {index}/{listing["total"]}: {wid} presets done '
                     f'references={links["total"]} queued_items={len(queued)}')

    edges = {}
    while pending:
        key = pending.popleft()
        item_started = monotonic()
        log_progress(f'item {len(items) + 1}/{len(queued)}: {key} detail start '
                     f'pending={len(pending)}')
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
        if 'ballistics' not in detail:
            raise ValueError('Missing ballistics field; deploy the new modding API first')
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
        log_progress(f'item done: {key} slots={len(slots)} candidates={len(edges[key])} '
                     f'collected_items={len(items)} discovered_items={len(queued)} pending={len(pending)} '
                     f'elapsed={monotonic() - item_started:.2f}s')

    log_progress('validation start: rechecking firearm list')
    # The production caller also holds the ingestion lock across all API reads.
    if collect_pages('weapons', 'weapons', fetch) != listing:
        raise ValueError('Weapon list changed during collection')
    bundles = {}
    for index, weapon in enumerate(listing['weapons'], start=1):
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
        log_progress(f'bundle {index}/{listing["total"]}: {wid} '
                     f'items={len(reachable)} presets={len(bundles[wid]["presets"])}')
    log_progress(f'collection done: weapons={len(bundles)} items={len(items)} '
                 f'slots={sum(len(v) for v in candidates.values())} presets={len(presets)} '
                 f'elapsed={monotonic() - started:.2f}s')
    return listing, bundles


def generate_weapon_modding_static_json(output_dir=None, fetch=fetch_data):
    """Build every bundle before atomically publishing the new index."""
    started = monotonic()
    log_progress(f'generation start: api={API_BASE_URL}')
    listing, bundles = collect_snapshot(fetch)
    root = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    base = root / 'static/modding/v3'
    generation = uuid4().hex
    folder = Path('snapshots') / generation
    public = f'{PUBLIC_BASE_PATH}/{folder.as_posix()}'
    generated = datetime.now(timezone.utc).isoformat()

    def envelope(data):
        return {'status': 200, 'msg': 'OK', 'generated_at': generated, 'data': data}

    log_progress(f'writing generation={generation} output={base / folder}')
    write_atomic(base / folder / 'weapons.json', envelope(listing))
    log_progress(f'weapon list written: weapons={listing["total"]}')
    paths = {}
    for index, (key, bundle) in enumerate(bundles.items(), start=1):
        file_started = monotonic()
        log_progress(f'file {index}/{len(bundles)}: {key} write start')
        filename = path_id(key) + '.json'
        write_atomic(base / folder / 'weapons' / filename, envelope(bundle))
        paths[key] = f'{public}/weapons/{filename}'
        log_progress(f'file {index}/{len(bundles)}: {key} written '
                     f'bytes={(base / folder / "weapons" / filename).stat().st_size} '
                     f'elapsed={monotonic() - file_started:.2f}s')
    manifest = {'generation': generation, 'schema_version': 1,
                'weapons_list': f'{public}/weapons.json', 'weapons': paths,
                'total': len(paths), 'preset_reconstruction_version': 1}
    log_progress(f'manifest publish start: generation={generation}')
    write_atomic(base / 'index.json', envelope(manifest))
    log_progress(f'published: generation={generation} weapons={len(paths)} '
                 f'elapsed={monotonic() - started:.2f}s')
    return manifest


def publish_weapon_modding_static_json(postgres_conn_id='platform_db'):
    """Prevent dags_item from changing the API's DB during this multi-request export."""
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    log_progress(f'connecting to source lock: connection={postgres_conn_id}')
    with closing(PostgresHook(postgres_conn_id).get_conn()) as conn:
        conn.autocommit = False
        with conn.cursor() as cursor:
            cursor.execute('SET LOCAL lock_timeout = \'60s\'')
            log_progress(f'waiting for ingestion lock: {SOURCE_LOCK}')
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', (SOURCE_LOCK,))
            log_progress('ingestion lock acquired; starting API export')
            return generate_weapon_modding_static_json()
