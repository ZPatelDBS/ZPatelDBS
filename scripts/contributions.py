#!/usr/bin/env python3
"""Generate an animated all-time contributions SVG for a GitHub profile.

Usage: GITHUB_TOKEN=... python3 contributions.py <username> <output.svg>
       python3 contributions.py --demo <output.svg>   (fake data, for testing)
"""
import json, os, sys, time, traceback, urllib.request, urllib.error, random
from datetime import datetime, timedelta, timezone, date
from collections import OrderedDict

API = "https://api.github.com/graphql"

def gql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    last = None
    for attempt in range(4):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "contrib-card"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            if "errors" in out:
                raise RuntimeError(f"GraphQL error: {out['errors']}")
            return out["data"]
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
        except Exception as e:
            last = str(e)
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(last)

def fetch_days(user, token):
    created = gql("query($u:String!){user(login:$u){createdAt}}", {"u": user}, token)["user"]["createdAt"]
    start = datetime.fromisoformat(created.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
           contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    days = {}
    cur = start
    while cur < now:
        end = min(cur + timedelta(days=364), now)
        data = gql(q, {"u": user, "f": cur.isoformat(), "t": end.isoformat()}, token)
        for w in data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                dd = date.fromisoformat(d["date"])
                if start.date() <= dd <= now.date():
                    days[dd] = d["contributionCount"]
        cur = end
    return start.date(), days

def demo_days():
    random.seed(4)
    start = date(2024, 11, 4); days = {}; d = start
    while d <= date(2026, 11, 19):
        base = 0 if d.weekday() >= 5 else (3 if d.year == 2024 else 6 if d < date(2026, 7, 1) else 14)
        days[d] = max(0, int(random.gauss(base, base * 0.8))) if random.random() > 0.3 else 0
        d += timedelta(days=1)
    return start, days

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def build_svg(start, days):
    total = sum(days.values())
    months = OrderedDict()
    for d in sorted(days):
        months.setdefault((d.year, d.month), 0)
        months[(d.year, d.month)] += days[d]
    keys = list(months)
    best_m = max(keys, key=lambda k: months[k])
    best_day = max(days, key=lambda k: days[k]) if days else None
    active = sum(1 for v in days.values() if v > 0)
    # longest streak
    longest = run = 0; prev = None
    for d in sorted(days):
        run = run + 1 if days[d] > 0 and prev and (d - prev).days == 1 and run else (1 if days[d] > 0 else 0)
        longest = max(longest, run); prev = d

    W, H = 820, 320
    # --- counter (count-up) ---
    frames, dur = 24, 1.8
    counter = []
    for i in range(frames + 1):
        p = i / frames; v = round(total * (1 - (1 - p) ** 3))
        t0 = 0.3 + dur * i / frames
        last = i == frames
        anim = (f'<set attributeName="opacity" to="1" begin="{t0:.2f}s" fill="freeze"/>' if last else
                f'<set attributeName="opacity" to="1" begin="{t0:.2f}s" dur="{dur/frames:.3f}s"/>')
        counter.append(f'<text x="32" y="112" class="big" opacity="0">{v:,}{anim}</text>')

    # --- monthly bars ---
    cx0, cx1, cy_base, cy_top = 32, W - 32, 278, 168
    n = len(keys); gap = 4 if n < 40 else 2
    bw = max(3, (cx1 - cx0 - gap * (n - 1)) / n)
    mx = max(months.values()) or 1
    bars, labels = [], []
    for i, k in enumerate(keys):
        h = max(2, (cy_top - cy_base) * -1 * months[k] / mx)
        x = cx0 + i * (bw + gap); y = cy_base - h
        b = 2.4 + i * (1.6 / max(1, n))
        fill = "url(#hot)" if k == best_m else "url(#bar)"
        bars.append(
            f'<rect x="{x:.1f}" y="{cy_base}" width="{bw:.1f}" height="0" rx="2" fill="{fill}">'
            f'<title>{date(k[0], k[1], 1):%b %Y}: {months[k]:,}</title>'
            f'<animate attributeName="height" from="0" to="{h:.1f}" begin="{b:.2f}s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/>'
            f'<animate attributeName="y" from="{cy_base}" to="{y:.1f}" begin="{b:.2f}s" dur="0.6s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>')
        if k[1] == 1 or (i == 0 and k[1] <= 10):
            labels.append(f'<text x="{x:.1f}" y="{cy_base + 18}" class="lbl">{k[0] if k[1]==1 else date(k[0],k[1],1).strftime("%b %Y")}</text>')
    bm_i = keys.index(best_m); bm_x = cx0 + bm_i * (bw + gap) + bw / 2
    bm_y = cy_base - (cy_top - cy_base) * -1 * months[best_m] / mx
    peak = (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="4.3s" dur="0.4s" fill="freeze"/>'
            f'<text x="{min(max(bm_x,60),W-60):.1f}" y="{bm_y - 8:.1f}" text-anchor="middle" class="peak">▲ {months[best_m]:,}</text></g>')

    def stat(x, label, value, delay):
        return (f'<g opacity="0" transform="translate({x},0)"><animate attributeName="opacity" from="0" to="1" begin="{delay}s" dur="0.5s" fill="freeze"/>'
                f'<text x="0" y="70" class="sl">{label}</text><text x="0" y="98" class="sv">{esc(value)}</text></g>')
    stats = "".join([
        stat(420, "BEST MONTH", f"{date(best_m[0], best_m[1], 1):%b %Y}", 1.0),
        stat(560, "LONGEST STREAK", f"{longest} days", 1.3),
        stat(700, "ACTIVE DAYS", f"{active:,}", 1.6),
    ])
    span_days = (max(days) - start).days if days else 0
    since = f"since {start:%d %b %Y} · {span_days // 365}y {(span_days % 365) // 30}m on GitHub"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <style>
    text {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; }}
    .ttl {{ fill: #7aa2f7; font-size: 13px; font-weight: 700; letter-spacing: 2px; }}
    .big {{ fill: #c0caf5; font-size: 52px; font-weight: 800; }}
    .sub {{ fill: #565f89; font-size: 13px; }}
    .sl {{ fill: #565f89; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}
    .sv {{ fill: #c0caf5; font-size: 20px; font-weight: 700; }}
    .lbl {{ fill: #565f89; font-size: 11px; }}
    .peak {{ fill: #e0af68; font-size: 11px; font-weight: 700; }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a1b26"/><stop offset="1" stop-color="#16161e"/></linearGradient>
    <linearGradient id="bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#7aa2f7"/><stop offset="1" stop-color="#9ece6a"/></linearGradient>
    <linearGradient id="hot" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#bb9af7"/><stop offset="1" stop-color="#e0af68"/></linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.06"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="12" fill="url(#bg)" stroke="#2f334d"/>
  <rect x="-300" y="0" width="300" height="{H}" fill="url(#shine)">
    <animate attributeName="x" from="-300" to="{W}" begin="2.2s;shine.end+6s" dur="1.6s" id="shine"/>
  </rect>
  <text x="32" y="44" class="ttl">ALL-TIME CONTRIBUTIONS</text>
  {''.join(counter)}
  <text x="32" y="138" class="sub" opacity="0">{esc(since)}<animate attributeName="opacity" from="0" to="1" begin="2.1s" dur="0.5s" fill="freeze"/></text>
  {stats}
  <line x1="32" y1="{cy_base + 0.5}" x2="{W-32}" y2="{cy_base + 0.5}" stroke="#2f334d"/>
  {''.join(bars)}
  {peak}
  {''.join(labels)}
</svg>'''

if __name__ == "__main__":
    try:
        if sys.argv[1] == "--demo":
            start, days = demo_days(); out = sys.argv[2]
        else:
            token = os.environ.get("CONTRIB_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if not token:
                raise RuntimeError("No token found: GITHUB_TOKEN is not set for this step")
            start, days = fetch_days(sys.argv[1], token); out = sys.argv[2]
        if not days:
            raise RuntimeError("GitHub returned no contribution days")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(build_svg(start, days))
        print(f"wrote {out}: {sum(days.values())} contributions since {start}")
    except Exception as e:
        traceback.print_exc()
        msg = str(e).replace("\n", " ")[:400]
        print(f"::error title=Contributions card failed::{type(e).__name__}: {msg}")
        sys.exit(1)
