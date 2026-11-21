#!/usr/bin/env python3
"""Download latest public HawkEye 360 SGP4 mean elements (OMM JSON) from CelesTrak.

Usage:
    python -m pip install requests
    python refresh_hawkeye360.py

This is a live downloader. An internet connection is required when you run it.
"""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
import requests

BASE = 'https://celestrak.org/NORAD/elements/gp.php'
DEST = Path(__file__).resolve().parent
HAWK_NAME = re.compile(r'^HAWK-(?:[A-Z]|[0-9]+[A-Z])$')


def fetch(name):
    for attempt in range(3):
        try:
            resp = requests.get(BASE, params={'NAME': name, 'FORMAT': 'JSON'}, timeout=45,
                                headers={'User-Agent': 'HawkEye360-Research-SGP4/1.0'})
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                raise ValueError(f'Unexpected response for {name!r}: {str(data)[:150]}')
            return data
        except (requests.RequestException, ValueError) as exc:
            if attempt == 2:
                raise RuntimeError(f'Failed CelesTrak request for {name}: {exc}') from exc
            time.sleep(3 * (attempt + 1))


def main():
    hawks = [r for r in fetch('HAWK')
             if HAWK_NAME.fullmatch(str(r.get('OBJECT_NAME', '')).strip())]
    kestrels = [r for r in fetch('KESTREL-0A')
                if str(r.get('OBJECT_NAME', '')).strip().upper() == 'KESTREL-0A']
    objects = {int(r['NORAD_CAT_ID']): r for r in hawks + kestrels}
    if not objects:
        raise RuntimeError('CelesTrak did not return matching satellite elements; no files overwritten.')
    elements = sorted(objects.values(), key=lambda r: (r['OBJECT_NAME'], int(r['NORAD_CAT_ID'])))
    required = {'OBJECT_NAME', 'NORAD_CAT_ID', 'EPOCH', 'MEAN_MOTION', 'INCLINATION',
                'ECCENTRICITY', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY'}
    for r in elements:
        if required - r.keys():
            raise RuntimeError(f"Incomplete OMM record: {r.get('OBJECT_NAME')}: {required-r.keys()}")

    retrieved = datetime.now(timezone.utc)
    omm_path = DEST / 'hawkeye360_latest_omm.json'
    index_path = DEST / 'hawkeye360_latest_index.csv'
    meta_path = DEST / 'hawkeye360_latest_metadata.json'
    omm_path.write_text(json.dumps(elements, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with index_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'norad_cat_id', 'epoch_utc', 'age_days_when_downloaded',
                         'source_url', 'mean_motion_rev_per_day', 'inclination_deg'])
        for r in elements:
            stamp = r['EPOCH']
            stamp_dt = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if stamp_dt.tzinfo is None:
                stamp_dt = stamp_dt.replace(tzinfo=timezone.utc)
            age = (retrieved - stamp_dt).total_seconds()/86400
            source = f"{BASE}?CATNR={r['NORAD_CAT_ID']}&FORMAT=JSON"
            writer.writerow([r['OBJECT_NAME'], r['NORAD_CAT_ID'], stamp, round(age, 3),
                             source, r['MEAN_MOTION'], r['INCLINATION']])
    metadata = {'retrieved_at_utc': retrieved.isoformat(),
                'source': 'CelesTrak current GP data (CCSDS OMM JSON)',
                'count': len(elements),
                'includes': 'HAWK-* and KESTREL-0A, only entries with public GP data',
                'note': 'Current GP may omit decayed or untracked satellites; not historical ephemerides.'}
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Downloaded {len(elements)} satellites: {omm_path}')
    print(f'Index: {index_path}')
    print('Epoch range:', min(r['EPOCH'] for r in elements), 'to', max(r['EPOCH'] for r in elements))
    print('For pass predictions, choose a simulation time near the element epochs.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
