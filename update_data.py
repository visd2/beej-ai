"""Daily updater: appends new NIFTY 50 closing prices to data/nifty-extra.json.
Source: Yahoo Finance chart API (symbol ^NSEI, same closing price as NSE's price index).
Rows are [days since 2017-01-01, close]. Stops safely (exit 0, file unchanged) on any problem."""
import json, os, sys, time, urllib.request, datetime as dt

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'nifty-extra.json')
BASE = dt.date(2017, 1, 1)
BUILTIN_LAST = 3594          # 4 Nov 2026, last day built into index.html

def parse_yahoo(payload):
    res = payload['chart']['result'][0]
    out = []
    for ts, c in zip(res['timestamp'], res['indicators']['quote'][0]['close']):
        if c is None or not (1000 < c < 200000):
            continue
        day = (dt.datetime.fromtimestamp(ts, dt.timezone(dt.timedelta(hours=5, minutes=30))).date() - BASE).days
        out.append([day, round(float(c), 2)])
    return out

def fetch(p1, p2):
    url = ('https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d'
           f'&period1={p1}&period2={p2}')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main():
    data = json.load(open(OUT))
    rows = data['rows']
    last = rows[-1][0] if rows else BUILTIN_LAST
    start = BASE + dt.timedelta(days=last + 1)
    today = dt.date.today()
    if start > today:
        print('already up to date'); return
    p1 = int(time.mktime((start - dt.timedelta(days=3)).timetuple()))
    p2 = int(time.time()) + 86400
    try:
        new = parse_yahoo(fetch(p1, p2))
    except Exception as e:
        print('fetch failed, leaving data unchanged:', e); return
    seen = {r[0] for r in rows}
    fresh = sorted(r for r in new if r[0] > last and r[0] not in seen)
    if not fresh:
        print('no new days'); return
    if fresh[0][0] - last > 10:
        print('gap too large, not adding; run manually'); return
    rows.extend(fresh)
    json.dump({'d0': '2017-01-01', 'rows': rows}, open(OUT, 'w'))
    print('added', len(fresh), 'days, last day number', rows[-1][0])

if __name__ == '__main__':
    main()
