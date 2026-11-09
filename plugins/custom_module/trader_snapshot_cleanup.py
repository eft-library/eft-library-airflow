"""Bound trader snapshot storage after a successful manifest publication."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import time

DEFAULT_OUTPUT_DIR = Path('/opt/airflow/next-public')
GENERATION = re.compile(r'^[a-f0-9]{32}$')
SNAPSHOT_URL = re.compile(r'^/static/trader/v3/snapshots/([a-f0-9]{32})/')


def referenced_generations(base):
    """Fail closed if the manifest cannot safely identify active generations."""
    payload = json.loads((base / 'index.json').read_text(encoding='utf-8'))
    data = payload.get('data')
    if (payload.get('status') != 200 or payload.get('msg') != 'OK'
            or not isinstance(data, dict)
            or not isinstance(data.get('generation'), str)
            or not GENERATION.fullmatch(data['generation'])
            or not isinstance(data.get('modes'), dict) or not data['modes']):
        raise ValueError('Cannot clean snapshots: invalid trader manifest')
    protected = {data['generation']}
    for mode in data['modes'].values():
        if not isinstance(mode, dict) or not isinstance(mode.get('offers'), dict):
            raise ValueError('Cannot clean snapshots: invalid mode paths')
        for url in [mode.get('list'), *mode['offers'].values()]:
            match = SNAPSHOT_URL.match(url) if isinstance(url, str) else None
            if not match:
                raise ValueError('Cannot clean snapshots: invalid snapshot URL')
            protected.add(match.group(1))
    if any(not (base / 'snapshots' / generation).is_dir() for generation in protected):
        raise ValueError('Cannot clean snapshots: active generation is missing')
    return protected


def cleanup_trader_snapshots(output_dir=None, *, retention_hours=None,
                             min_generations=None, now=None, dry_run=False):
    """Keep active references, at least N recent folders, and the age grace period.

    Only UUID-named real directories are candidates. This function does not
    remove arbitrary files, follow generation symlinks, or publish the index.
    The owning DAG serializes generation/cleanup with max_active_runs=1.
    """
    retention_hours = float(os.getenv('TRADER_SNAPSHOT_RETENTION_HOURS', '24')
                            if retention_hours is None else retention_hours)
    min_generations = int(os.getenv('TRADER_SNAPSHOT_MIN_GENERATIONS', '12')
                          if min_generations is None else min_generations)
    if not math.isfinite(retention_hours) or retention_hours < 1 or min_generations < 2:
        raise ValueError('Snapshot retention must be >= 1 hour and >= 2 generations')
    root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    base = root / 'static/trader/v3'
    referenced_generations(base)  # Validate before touching any stored data.
    cutoff = (time.time() if now is None else now) - retention_hours * 3600
    folders = []
    for folder in (base / 'snapshots').iterdir():
        if GENERATION.fullmatch(folder.name) and not folder.is_symlink() and folder.is_dir():
            folders.append((folder.stat().st_mtime, folder))
    folders.sort(key=lambda entry: (entry[0], entry[1].name), reverse=True)
    eligible = 0
    for modified, folder in folders[min_generations:]:
        if modified >= cutoff:
            continue
        # Re-read the atomic manifest in case another publisher/rollback moved it.
        if folder.name in referenced_generations(base):
            continue
        if folder.is_symlink():
            continue
        if not dry_run:
            shutil.rmtree(folder)
        eligible += 1
    result = {
        'scanned': len(folders), 'deleted': 0 if dry_run else eligible,
        'would_delete': eligible if dry_run else 0,
        'retained': len(folders) - (0 if dry_run else eligible),
        'retention_hours': retention_hours, 'min_generations': min_generations,
        'dry_run': dry_run,
    }
    print('Trader snapshot cleanup:', result)
    return result
