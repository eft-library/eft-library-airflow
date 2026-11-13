"""Export manually curated rewards only on explicit request after input is complete."""
from datetime import datetime, timezone
from pathlib import Path
from custom_module.static_api_client import get_api_response
from custom_module.trader_static_json import write_atomic

API_URL = 'https://back.eftlibrary.com/api/kord-breach/v3/rewards'
OUTPUT = Path('/opt/airflow/next-public/static/kord-breach/v3/rewards.json')


def generate_kord_breach_reward_static_json(output=None, fetch=None):
    payload = (fetch or (lambda: get_api_response(API_URL, 60).json()))()
    if not isinstance(payload, dict) or payload.get('status') != 200 or payload.get('msg') != 'OK':
        raise ValueError('Invalid rewards API response')
    data = payload.get('data')
    if not isinstance(data, dict) or not isinstance(data.get('rewards'), list):
        raise ValueError('Invalid rewards data')
    if type(data.get('total')) is not int or data['total'] != len(data['rewards']):
        raise ValueError('Incomplete rewards list')
    if not data.get('source_revision') or not data.get('collected_at') or not data.get('source_url') or not data.get('season_id'):
        raise ValueError('Missing curated snapshot provenance')
    if data.get('condition_logic') != 'or_groups_of_and_conditions':
        raise ValueError('Unknown reward condition semantics')
    keys = [(r['sort_order'], r['id']) for r in data['rewards']]
    if keys != sorted(keys) or len({r['id'] for r in data['rewards']}) != data['total']:
        raise ValueError('Invalid reward order or duplicate ID')
    result = {**payload, 'generated_at':datetime.now(timezone.utc).isoformat()}
    write_atomic(Path(output) if output is not None else OUTPUT, result)
    return {'total':data['total'], 'source_revision':data['source_revision']}
