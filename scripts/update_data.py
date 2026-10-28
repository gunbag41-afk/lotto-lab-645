#!/usr/bin/env python3
"""Publish *verified* 6/45 draw archive from Donghaeng Lottery official JSON endpoints.

No third-party data is silently promoted to official data. On fetch or validation errors,
existing data/draws.json is left untouched; GitHub Actions reports failure.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / 'data' / 'draws.json'
BASE = 'https://www.dhlottery.co.kr/lt645/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://www.dhlottery.co.kr/lt645/result',
    'X-Requested-With': 'XMLHttpRequest',
}


def get_list(endpoint, params=None, retries=3):
    url = BASE + endpoint + (('?' + urllib.parse.urlencode(params)) if params else '')
    last_exc = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=24) as response:
                typ = response.headers.get('Content-Type', '')
                blob = response.read(2500000)
                if 'json' not in typ and not blob.lstrip().startswith(b'{'):
                    raise ValueError('Official provider returned non-JSON data (possibly blocking automation)')
                payload = json.loads(blob)
            rows = payload.get('data', {}).get('list')
            if not isinstance(rows, list) or not rows:
                raise ValueError('Official response has no data.list rows')
            return rows
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(1.3 * (attempt + 1))
    raise RuntimeError(f'Failed to fetch {endpoint}: {last_exc}')


def decode(row):
    r = int(row['ltEpsd'])
    raw = str(row['ltRflYmd'])
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(f'Invalid draw date for round {r}')
    d = {
        'round': r,
        'date': f'{raw[:4]}-{raw[4:6]}-{raw[6:]}',
        'nums': sorted(int(row[f'tm{i}WnNo']) for i in range(1, 7)),
        'bonus': int(row['bnsWnNo']),
    }
    validate(d)
    return d


def validate(d):
    r, ns, bonus = d['round'], d['nums'], d['bonus']
    if not (isinstance(r, int) and r >= 1 and len(ns) == 6 and len(set(ns)) == 6
            and all(isinstance(x, int) and 1 <= x <= 45 for x in ns)
            and isinstance(bonus, int) and 1 <= bonus <= 45 and bonus not in ns):
        raise ValueError(f'Invalid combination in round {r}')
    date = dt.date.fromisoformat(d['date'])
    if date.weekday() != 5:
        raise ValueError(f'Round {r} date is not Saturday')
    expected = dt.date(2002, 12, 7) + dt.timedelta(days=(r - 1) * 7)
    if date != expected:
        raise ValueError(f'Round {r} fails chronological validation: {date} vs {expected}')
    return True


def run():
    existing = json.loads(DB.read_text(encoding='utf-8'))
    existing_draws = existing.get('draws', [])
    cached = {d['round']: d for d in existing_draws if validate(d)}
    official_latest = [decode(x) for x in get_list('selectPstLt645Info.do')]
    newest = max(official_latest, key=lambda x: x['round'])
    if newest['round'] < max(cached, default=0):
        raise RuntimeError('Official source is older than cached archive; refusing to downgrade')
    print(f'Latest official draw: #{newest["round"]}, {newest["date"]}', flush=True)
    for d in official_latest:
        cached[d['round']] = d
    # Always refresh latest results from the official batch endpoint as an independent
    # consistency check, including recently corrected draw numbers.
    near_latest = [decode(x) for x in get_list('selectPstLt645InfoNew.do',
                         {'srchDir': 'center', 'srchLtEpsd': newest['round']})]
    if not any(x['round'] == newest['round'] and x == newest for x in near_latest):
        raise RuntimeError('Latest official detail and list endpoints disagree')
    for d in near_latest:
        if d['round'] <= newest['round']:
            cached[d['round']] = d
    # Request missing rounds in groups of approximately ten. The batch endpoint
    # centers near requested round; step based on actually returned rounds to avoid holes.
    missing = [n for n in range(1, newest['round'] + 1) if n not in cached]
    calls = 0
    while missing:
        target = min(newest['round'], missing[0] + 4)
        rows = get_list('selectPstLt645InfoNew.do', {'srchDir': 'center', 'srchLtEpsd': target})
        added = 0
        for row in rows:
            d = decode(row)
            if 1 <= d['round'] <= newest['round']:
                added += d['round'] not in cached
                cached[d['round']] = d
        calls += 1
        if not added:
            raise RuntimeError(f'Batch API made no progress near round {target}')
        missing = [n for n in range(1, newest['round'] + 1) if n not in cached]
        if calls > newest['round']:
            raise RuntimeError('Too many requests; possible API or data inconsistency')
        if calls % 15 == 0:
            print(f'Fetched {len(cached)}/{newest["round"]} rounds', flush=True)
        time.sleep(0.12)
    arr = [cached[n] for n in range(1, newest['round']+1)]
    known = arr[1246] if len(arr) >= 1247 else None
    if known and known['nums'] != [8,14,21,22,42,45]:
        raise RuntimeError('Known 1247 result does not match verified reference')
    # Detect changes to cached results; an official correction is kept (with log).
    changed = [d['round'] for d in arr if d['round'] in {x['round'] for x in existing_draws}
               and d != next((x for x in existing_draws if x['round']==d['round']), None)]
    if changed:
        print('Official revisions detected:', changed[:20], flush=True)
    new_doc = {
        'schemaVersion': 2,
        'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'source': 'Donghaeng Lottery official public results JSON',
        'latestRound': newest['round'],
        'draws': arr,
    }
    if arr == existing_draws and existing.get('source') == new_doc['source']:
        print('No change to data; keeping old updatedAt', flush=True)
        return
    tmp = DB.with_suffix('.tmp')
    tmp.write_text(json.dumps(new_doc, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    os.replace(tmp, DB)
    print(f'Archive updated: {len(arr)} consecutive rounds. {calls} batch requests.', flush=True)


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Official data update FAILED; existing archive preserved:', exc, file=sys.stderr)
        sys.exit(1)
