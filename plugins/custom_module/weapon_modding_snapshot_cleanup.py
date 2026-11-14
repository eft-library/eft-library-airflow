"""Keep three recent modding generations and all active manifest references."""
import json
import math
from pathlib import Path
import re
import shutil
import time
from urllib.parse import quote

from custom_module.weapon_modding_static_json import OUTPUT_DIR, PUBLIC_BASE_PATH, valid_id

GENERATION = re.compile(r'^[a-f0-9]{32}$')


def referenced_generations(base):
    payload = json.loads((base / 'index.json').read_text(encoding='utf-8'))
    data = payload.get('data')
    if (payload.get('status') != 200 or payload.get('msg') != 'OK' or not isinstance(data, dict)
            or not isinstance(data.get('generation'), str) or not GENERATION.fullmatch(data['generation'])
            or data.get('schema_version') != 1 or not isinstance(data.get('weapons'), dict)
            or not data['weapons'] or type(data.get('total')) is not int
            or data['total'] != len(data['weapons'])):
        raise ValueError('Cannot clean snapshots: invalid modding manifest')
    generation = data['generation']
    public = f'{PUBLIC_BASE_PATH}/snapshots/{generation}'
    if data.get('weapons_list') != f'{public}/weapons.json':
        raise ValueError('Cannot clean snapshots: invalid weapon list path')
    for key, url in data['weapons'].items():
        if url != f'{public}/weapons/{quote(valid_id(key), safe="")}.json':
            raise ValueError('Cannot clean snapshots: invalid weapon path')
    folder = base / 'snapshots' / generation
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Cannot clean snapshots: active generation is missing')
    for path in [folder / 'weapons.json', *(folder / 'weapons' / f'{quote(key, safe="")}.json' for key in data['weapons'])]:
        if path.is_symlink() or not path.is_file():
            raise ValueError('Cannot clean snapshots: active file is missing')
    return {generation}


def cleanup_weapon_modding_snapshots(output_dir=None, *, min_generations=3,
                                      retention_hours=0, now=None, dry_run=False):
    retention_hours = float(retention_hours)
    if (type(min_generations) is not int or min_generations < 3
            or not math.isfinite(retention_hours) or retention_hours < 0):
        raise ValueError('Retention requires >= 3 generations and >= 0 hours')
    root = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    base = root / 'static/modding/v3'
    print(f'[modding-static] cleanup start: output={base} keep={min_generations} dry_run={dry_run}', flush=True)
    referenced_generations(base)  # No deletion if the manifest is missing/corrupt.
    cutoff = (time.time() if now is None else now) - retention_hours * 3600
    folders = sorted(
        ((p.stat().st_mtime, p) for p in (base / 'snapshots').iterdir()
         if GENERATION.fullmatch(p.name) and not p.is_symlink() and p.is_dir()),
        key=lambda entry: (entry[0], entry[1].name), reverse=True,
    )
    eligible = 0
    for modified, folder in folders[min_generations:]:
        if modified >= cutoff or folder.name in referenced_generations(base) or folder.is_symlink():
            continue
        print(f'[modding-static] cleanup {"would delete" if dry_run else "deleting"}: {folder.name}', flush=True)
        if not dry_run:
            shutil.rmtree(folder)
        eligible += 1
    result = {'scanned': len(folders), 'deleted': 0 if dry_run else eligible,
              'would_delete': eligible if dry_run else 0,
              'retained': len(folders) - (0 if dry_run else eligible)}
    print('[modding-static] cleanup done:', result, flush=True)
    return result
