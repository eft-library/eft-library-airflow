"""Publish validated trader snapshots through a manifest written last."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, quote
from uuid import uuid4

from custom_module.static_api_client import get_api_response

API_BASE_URL = 'https://back.eftlibrary.com/api'
OUTPUT_DIR = Path('/opt/airflow/next-public')
PUBLIC_BASE_PATH = '/static/trader/v3'
PAGE_SIZE = 500
MAX_PAGES = 1000


def fetch_data(endpoint, **params):
    response = get_api_response(f'{API_BASE_URL}/trader/v3/{endpoint}?{urlencode(params)}', 60)
    payload = response.json()
    if not isinstance(payload, dict) or payload.get('status') != 200 or not isinstance(payload.get('data'), dict):
        raise ValueError('Invalid trader API response')
    return payload['data']


def valid_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing trader/offer ID')
    return value


def collect_mode(mode, fetch=fetch_data):
    listing = fetch('list', game_mode=mode)
    season = listing.get('season_id')
    if listing.get('game_mode') != mode or ((mode == 'pvp-season') != (isinstance(season, str) and bool(season))):
        raise ValueError('Invalid trader mode/season')
    if mode != 'pvp-season' and season is not None:
        raise ValueError('Unexpected season')
    traders = listing.get('traders')
    if not isinstance(traders, list) or not traders:
        raise ValueError('Empty trader list')
    grouped = {}
    for trader in traders:
        trader_id = valid_id(trader['id'])
        if trader_id in grouped:
            raise ValueError('Duplicate trader ID')
        grouped[trader_id] = []
    params = {'game_mode': mode, 'page_size': PAGE_SIZE}
    if season is not None:
        params['season_id'] = season
    seen, total = set(), None
    for page in range(1, MAX_PAGES + 1):
        data = fetch('offers', **params, page=page)
        if data.get('game_mode') != mode or data.get('season_id') != season:
            raise ValueError('Offer scope changed during pagination')
        count = data.get('total')
        if type(count) is not int or count < 0 or data.get('page') != page or data.get('page_size') != PAGE_SIZE:
            raise ValueError('Invalid pagination metadata')
        if total is not None and total != count:
            raise ValueError('Offer total changed during pagination')
        total = count
        offers = data.get('offers')
        if not isinstance(offers, list) or len(offers) != min(PAGE_SIZE, max(0, total - (page - 1) * PAGE_SIZE)):
            raise ValueError('Incomplete offer page')
        for offer in offers:
            offer_id = valid_id(offer['id'])
            if offer_id in seen or offer.get('game_mode') != mode or offer.get('season_id') != season:
                raise ValueError('Duplicate offer or invalid offer scope')
            seen.add(offer_id)
            trader_id = offer.get('trader_id')
            if trader_id not in grouped:
                raise ValueError('Offer references unknown trader')
            for field in ('costs', 'rewards', 'task_unlocks'):
                if not isinstance(offer.get(field), list) or (field != 'task_unlocks' and not offer[field]):
                    raise ValueError('Missing offer details')
            grouped[trader_id].append(offer)
        if len(seen) == total:
            break
    else:
        raise ValueError('Pagination limit exceeded')
    # Check source metadata again before publishing, including current season rollover.
    if fetch('list', game_mode=mode) != listing:
        raise ValueError('Trader list/season/restock changed during collection')
    return listing, grouped


def write_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            stream.write('\n')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def generate_trader_static_json(output_dir=None, fetch=fetch_data):
    # All API reads and validations finish before publishing any files.
    snapshots = {mode: collect_mode(mode, fetch) for mode in ('pvp', 'pve', 'pvp-season')}
    generated = datetime.now(timezone.utc).isoformat()
    generation = uuid4().hex
    root = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    base = root / 'static' / 'trader' / 'v3'
    relative = Path('snapshots') / generation
    public = f'{PUBLIC_BASE_PATH}/{relative.as_posix()}'
    manifest = {}

    def envelope(data):
        return {'status': 200, 'msg': 'OK', 'generated_at': generated, 'data': data}

    for mode, (listing, grouped) in snapshots.items():
        folder = relative / mode
        write_atomic(base / folder / 'list.json', envelope(listing))
        paths = {}
        for trader_id, offers in grouped.items():
            filename = quote(trader_id, safe='') + '.json'
            write_atomic(base / folder / 'offers' / filename, envelope({
                'game_mode': mode, 'season_id': listing['season_id'], 'trader_id': trader_id,
                'total': len(offers), 'offers': offers}))
            paths[trader_id] = f'{public}/{mode}/offers/{filename}'
        manifest[mode] = {'season_id': listing['season_id'],
                          'list': f'{public}/{mode}/list.json', 'offers': paths,
                          'total': sum(map(len, grouped.values()))}
    # Existing manifest and files remain readable if a request or write fails.
    write_atomic(base / 'index.json', envelope({'generation': generation, 'modes': manifest}))
    print('Trader static JSON published:', {mode: data['total'] for mode, data in manifest.items()})
