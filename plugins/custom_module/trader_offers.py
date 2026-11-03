"""Validate complete trader snapshots before replacing any persisted offers."""

from collections import defaultdict
from contextlib import closing
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json

from custom_module.tarkov_json_api import get_json_data, get_price_season


def identifier(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing source identifier')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def positive(value, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError('Invalid quantity')
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid quantity') from None
    if not number.is_finite() or number <= 0 or (integer and number != number.to_integral_value()):
        raise ValueError('Invalid quantity')
    return int(number) if integer else number


def unlocks(value):
    # Current API: null or one quest ID. Unknown structures must not erase conditions.
    if value is None:
        return []
    if isinstance(value, str):
        return [identifier(value)]
    raise ValueError('Unsupported taskUnlock format')


def quantities(rows, integer=False):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Missing cost/reward items')
    result = defaultdict(lambda: Decimal(0))
    for row in rows:
        result[identifier(row['item'])] += positive(row['count'], integer)
    return dict(sorted(result.items()))


def normalize_snapshot(items_data, barters, traders, game_mode, season_id=None):
    if game_mode not in ('pvp', 'pve', 'pvp-season') or ((game_mode == 'pvp-season') != (season_id is not None)):
        raise ValueError('Invalid mode/season scope')
    items = items_data.get('items') if isinstance(items_data, dict) else None
    if not isinstance(items, dict) or not items or not isinstance(barters, list) or not barters:
        raise ValueError('Incomplete items/barters snapshot')
    if not isinstance(traders, dict) or not traders:
        raise ValueError('Incomplete traders snapshot')
    offers = {}

    def add(raw, source, costs, rewards):
        trader = identifier(raw['trader'])
        if trader not in traders:
            raise ValueError('Offer references missing source trader')
        level = raw['minTraderLevel']
        if type(level) is not int or not 1 <= level <= 4:
            raise ValueError('Invalid trader level')
        tasks = unlocks(raw.get('taskUnlock'))
        limit = raw.get('buyLimit')
        if limit is not None and type(limit) is not int:
            raise ValueError('Invalid buyLimit')
        # Preserve raw values; no special value (including zero) is interpreted.
        known_limit = limit if limit is not None and limit > 0 else None
        unlimited = False if known_limit is not None else None
        if source is None:
            source = 'purchase:' + digest([trader, sorted(rewards), sorted(costs), level, tasks])
        internal = digest([source, game_mode, season_id])
        offer = dict(id=internal, source=source, trader=trader, level=level,
                     type='barter' if source.startswith('barter:') else 'purchase',
                     limit=known_limit, raw_limit=limit, unlimited=unlimited,
                     costs=costs, rewards=rewards, tasks=tasks)
        if internal in offers and offers[internal] != offer:
            raise ValueError('Conflicting offers share a stable identity')
        offers[internal] = offer

    for item in items.values():
        item_id = identifier(item['id'])
        purchases = item.get('buyFromTrader', [])
        if not isinstance(purchases, list):
            raise ValueError('Invalid buyFromTrader')
        for raw in purchases:
            costs = {identifier(raw['currencyItem']): positive(raw['price'])}
            add(raw, None, costs, {item_id: 1})
    for raw in barters:
        add(raw, 'barter:' + identifier(raw['id']), quantities(raw['requiredItems']),
            quantities([raw['offeredItem']], integer=True))
    if not offers or not any(o['type'] == 'purchase' for o in offers.values()):
        raise ValueError('Empty purchase snapshot')
    restocks = []
    for key, trader in sorted(traders.items()):
        trader_id = identifier(trader['id'])
        if key != trader_id:
            raise ValueError('Trader key/ID mismatch')
        timestamp = trader.get('resetTime')
        if timestamp is not None:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if timestamp.utcoffset() is None:
                raise ValueError('Restock time must include timezone')
        restocks.append((trader_id, game_mode, season_id, timestamp))
    return dict(mode=game_mode, season_id=season_id,
                offers=sorted(offers.values(), key=lambda o: o['source']), restocks=restocks)


def fetch_snapshots():
    season = get_price_season()
    snapshots = []
    for source_mode, mode in [('regular', 'pvp'), ('pve', 'pve'), ('pvp-season', 'pvp-season')]:
        snapshots.append(normalize_snapshot(
            get_json_data('items', None, source_mode),
            get_json_data('barters', None, source_mode),
            get_json_data('traders', None, source_mode), mode,
            season['id'] if mode == 'pvp-season' else None))
    if get_price_season()['id'] != season['id']:
        raise ValueError('Season changed during collection')
    return season, snapshots


def persist_snapshots(cursor, season, snapshots, execute_values):
    from custom_module.queries import trader_offers as sql

    item_ids, trader_ids = set(), set()
    for snapshot in snapshots:
        trader_ids.update(r[0] for r in snapshot['restocks'])
        for offer in snapshot['offers']:
            item_ids.update(offer['costs'])
            item_ids.update(offer['rewards'])
    cursor.execute('SELECT id FROM items WHERE id = ANY(%s)', (sorted(item_ids),))
    missing_items = item_ids - {row[0] for row in cursor.fetchall()}
    cursor.execute('SELECT id FROM traders WHERE id = ANY(%s)', (sorted(trader_ids),))
    missing_traders = trader_ids - {row[0] for row in cursor.fetchall()}
    if missing_items or missing_traders:
        raise ValueError(f'Run dags_item/dags_trader first: missing items={sorted(missing_items)}, traders={sorted(missing_traders)}')
    cursor.execute(sql.UPSERT_SEASON, (season['id'], season['name'], season['starts_at'], season['ends_at']))
    for snapshot in snapshots:
        mode, season_id = snapshot['mode'], snapshot['season_id']
        offers = snapshot['offers']
        rows = [(o['id'], o['source'], o['trader'], o['level'], o['type'], mode, season_id,
                 o['limit'], o['raw_limit'], o['unlimited'], i) for i, o in enumerate(offers)]
        execute_values(cursor, sql.UPSERT_OFFERS, rows, page_size=500)
        ids = [o['id'] for o in offers]
        for table in ('trader_offer_costs', 'trader_offer_rewards', 'trader_offer_task_unlocks'):
            cursor.execute(f'DELETE FROM {table} WHERE offer_id = ANY(%s)', (ids,))
        for key, table in [('costs', 'trader_offer_costs'), ('rewards', 'trader_offer_rewards')]:
            children = [(o['id'], item, count, i) for o in offers for i, (item, count) in enumerate(o[key].items())]
            execute_values(cursor, f'INSERT INTO {table} (offer_id, item_id, quantity, sort_order) VALUES %s', children, page_size=500)
        tasks = [(o['id'], task) for o in offers for task in o['tasks']]
        if tasks:
            execute_values(cursor, 'INSERT INTO trader_offer_task_unlocks (offer_id, quest_id) VALUES %s', tasks, page_size=500)
        cursor.execute(sql.DEACTIVATE_MISSING, (mode, season_id, ids))
        execute_values(cursor, sql.UPSERT_RESTOCKS, snapshot['restocks'], page_size=100)


def collect_trader_offers(postgres_conn_id='platform_db'):
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from psycopg2.extras import execute_values

    season, snapshots = fetch_snapshots()
    with closing(PostgresHook(postgres_conn_id).get_conn()) as conn:
        with conn, closing(conn.cursor()) as cursor:
            persist_snapshots(cursor, season, snapshots, execute_values)
    for snapshot in snapshots:
        print(f"Trader offers saved: mode={snapshot['mode']} offers={len(snapshot['offers'])}")
