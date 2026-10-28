
#!/usr/bin/env python3
"""Incremental official Lotto 6/45 updater."""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'draws.json'
LATEST_URL = 'https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do'


def valid(draw):
    n = draw['nums']
    r = draw['round']
    d = dt.date.fromisoformat(draw['date'])
    expected = dt.date(2002, 12, 7) + dt.timedelta(days=7 * (r - 1))
    return (
        isinstance(r, int) and r > 0 and d == expected
        and len(n) == 6 and len(set(n)) == 6
        and all(isinstance(x, int) and 1 <= x <= 45 for x in n)
        and isinstance(draw['bonus'], int)
        and 1 <= draw['bonus'] <= 45 and draw['bonus'] not in n
    )


def fetch_latest():
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://www.dhlottery.co.kr/lt645/result',
        'X-Requested-With': 'XMLHttpRequest',
    }
    for attempt in range(3):
        try:
            req = Request(LATEST_URL, headers=headers)
            with urlopen(req, timeout=15) as response:
                body = response.read(1_000_000)
            obj = json.loads(body)
            rows = obj.get('data', {}).get('list', [])
            if not rows:
                raise ValueError('Official response has no winning numbers')
            row = max(rows, key=lambda x: int(x['ltEpsd']))
            date = str(row['ltRflYmd'])
            result = {
                'round': int(row['ltEpsd']),
                'date': f'{date[:4]}-{date[4:6]}-{date[6:8]}',
                'nums': sorted(int(row[f'tm{i}WnNo']) for i in range(1, 7)),
                'bonus': int(row['bnsWnNo']),
            }
            if not valid(result):
                raise ValueError('Official response failed lottery validation')
            return result
        except (URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            print(f'Latest endpoint attempt {attempt + 1} failed: {exc}', flush=True)
            if attempt == 2:
                raise RuntimeError('Official latest draw unavailable; archive preserved') from exc
            time.sleep(2 + attempt * 2)


def main():
    archive = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    draws = archive.get('draws', [])
    if not isinstance(draws, list) or not draws:
        raise ValueError('Existing draw archive is empty or invalid')
    if not all(valid(d) for d in draws):
        raise ValueError('Existing archive failed validation')
    by_round = {d['round']: d for d in draws}
    newest_saved = max(by_round)
    latest = fetch_latest()

    print(f'Official latest: {latest["round"]} / {latest["date"]}', flush=True)
    if latest['round'] < newest_saved:
        raise ValueError('Official result is older than archive')
    if latest['round'] > newest_saved + 1:
        raise ValueError('Multiple new rounds missing; manual backfill required')
    if latest['round'] == newest_saved and by_round[newest_saved] == latest:
        print('Latest round already saved. No data changes.', flush=True)
        return

    by_round[latest['round']] = latest
    ordered = [by_round[n] for n in sorted(by_round)]
    archive['draws'] = ordered
    archive['latestRound'] = latest['round']
    archive['updatedAt'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    archive['source'] = 'Official Donghaeng latest draws; older cached draws retained (historical coverage may be incomplete)'
    archive['historicalCoverage'] = 'partial' if len(ordered) < latest['round'] else 'complete'

    temp = DATA_PATH.with_suffix('.tmp')
    temp.write_text(json.dumps(archive, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    os.replace(temp, DATA_PATH)
    print(f'Saved latest round {latest["round"]}; archive has {len(ordered)} rounds.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Update failed; existing archive preserved:', exc, file=sys.stderr)
        sys.exit(1)
