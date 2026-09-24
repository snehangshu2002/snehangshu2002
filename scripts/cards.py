"""Self-hosted GitHub stats dashboard (dark + light) in the banner's terminal style,
so the README doesn't depend on shared public stat services that go down.

    KPI tiles      stars, repos, followers, contributions, streaks - odometer roll-in
    CONTRIB.MAP    12-month contribution heatmap + totals by weekday, with a scan line
    LANG.MIX       primary language of each own repo
    PUSH.LOG       most recently pushed repos

Repos and followers come from the REST API. The contribution calendar comes from
GraphQL when GITHUB_TOKEN is set, else from the public calendar page, which has the
same per-day counts.

    python scripts/cards.py --user snehangshu2002 --out assets
"""
import argparse
import datetime as dt
import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from style import CHAR, THEMES, num, odometer, panel, svg_open, text, window

API = "https://api.github.com"
W, H = 1180, 610
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
PITCH, CELL = 16, 13            # heatmap column pitch and cell size
GRID_X, GRID_Y = 83, 258        # top-left of the heatmap
LOG_LINES = 4


def request(url, token, body=None, raw=False):
    headers = {"User-Agent": "profile-cards"}
    if not raw:
        headers["Accept"] = "application/vnd.github+json"
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    with urllib.request.urlopen(urllib.request.Request(url, data, headers)) as r:
        return r.read().decode() if raw else json.load(r)


def repos(user, token):
    out, page = [], 1
    while batch := request(f"{API}/users/{user}/repos?per_page=100&type=owner&page={page}", token):
        out += batch
        page += 1
    return out


def calendar_graphql(user, token):
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
           totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    cal = request(f"{API}/graphql", token, {"query": q, "variables": {"u": user}})
    cal = cal["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]])
            for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def calendar_page(user):
    """The public calendar page: each day cell has a date and level, and a tooltip with its count."""
    page = request(f"https://github.com/users/{user}/contributions", None, raw=True)
    counts = {}
    for cell_id, tip in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        m = re.match(r"\s*([\d,]+) contributions?", tip)
        counts[cell_id] = int(m.group(1).replace(",", "")) if m else 0
    days = []
    for cell in re.findall(r'<td\b[^>]*\bdata-date="[^"]+"[^>]*>', page):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', cell))
        days.append((a["data-date"], counts.get(a.get("id"), 0), int(a.get("data-level", 0))))
    if not days:
        raise ValueError("no calendar cells on the page")
    days.sort()
    return sum(c for _, c, _ in days), days


def streaks(days):
    longest = run = 0
    for _, c, _ in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    # today not having a commit yet shouldn't break the streak
    for _, c, _ in reversed(days[:-1] if days and not days[-1][1] else days):
        if not c:
            break
        current += 1
    return current, longest


def short_date(iso, today):
    d = dt.date.fromisoformat(iso[:10])
    return d.strftime("%b %d") if d.year == today.year else d.strftime("%b %Y")


# ---- drawing

def tiles(stats, t):
    o = []
    gap, top, h = 14, 84, 92
    w = (W - 70 - 5 * gap) / 6
    for i, (label, value, caption) in enumerate(stats):
        x = 35 + i * (w + gap)
        o.append(f'<rect x="{num(x)}" y="{top}" width="{num(w)}" height="{h}" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>')
        o.append(f'<path d="M{num(x + 8)} {top + 20}V{top + 8}H{num(x + 20)}" fill="none" stroke="{t["chrome"]}" opacity=".55"/>')
        o.append(text(x + 16, top + 26, label, 11, t["muted"], weight=700, extra=' letter-spacing=".8"'))
        o.append(odometer(x + 16, top + 62, value, 30, t["text"], f"odo{i}", 0.1 + 0.15 * i))
        o.append(text(x + 16, top + 80, caption, 10, t["muted"]))
    return o


def contrib_map(total, days, t):
    x, y, w, h = 35, 192, W - 70, 228
    o = panel(x, y, w, h, "CONTRIB.MAP", t, f"{total:,} CONTRIBUTIONS · LAST 12 MONTHS" if days else "")
    if not days:
        o.append(text(x + w / 2, y + 130, "calendar unavailable", 12, t["muted"], "middle"))
        return o

    first = dt.date.fromisoformat(days[0][0])
    offset = (first.weekday() + 1) % 7              # rows run Sunday..Saturday, like GitHub
    cols = (offset + len(days) + 6) // 7
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(text(GRID_X - 8, GRID_Y + r * PITCH + 10, name, 10, t["muted"], "end"))

    # month labels where a column starts a new month; a stub first month too short to label is dropped
    col_start = {}
    for i, (date, _, _) in enumerate(days):
        col_start.setdefault((offset + i) // 7, date)
    labels = [(c, d) for c, d in col_start.items() if c == 0 or d[:7] != col_start[c - 1][:7]]
    if len(labels) > 1 and labels[1][0] < 3:
        labels.pop(0)
    for c, date in labels:
        o.append(text(GRID_X + c * PITCH, GRID_Y - 8, dt.date.fromisoformat(date).strftime("%b"), 10, t["muted"]))

    # cells, one fading group per week column so the map sweeps in left to right
    columns = [[] for _ in range(cols)]
    for i, (date, count, level) in enumerate(days):
        c, r = divmod(offset + i, 7)
        fill = t["ramp"][level - 1] if level else t["cell"]
        columns[c].append(f'<rect x="{GRID_X + c * PITCH}" y="{GRID_Y + r * PITCH}" width="{CELL}" height="{CELL}" '
                          f'rx="2.5" fill="{fill}"/>')
    for c, cells in enumerate(columns):
        start = 0.2 + 0.022 * c
        dur = start + 0.35
        o.append(f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{start / dur:.3f};1" '
                 f'dur="{dur:.2f}s" fill="freeze"/>{"".join(cells)}</g>')

    # today: a pulsing outline on the newest cell
    c, r = divmod(offset + len(days) - 1, 7)
    o.append(f'<rect x="{GRID_X + c * PITCH - 1.5}" y="{GRID_Y + r * PITCH - 1.5}" width="{CELL + 3}" height="{CELL + 3}" '
             f'rx="3.5" fill="none" stroke="{t["chrome"]}" stroke-width="1.5">'
             '<animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></rect>')

    # scan line sweeping across the weeks, fading in and out at the ends
    grid_w, grid_h = cols * PITCH, 7 * PITCH
    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.06;.94;1" begin="2.2s" '
             'dur="9s" repeatCount="indefinite"/>'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;{grid_w} 0" begin="2.2s" '
             'dur="9s" repeatCount="indefinite"/>'
             f'<rect x="{GRID_X - PITCH}" y="{GRID_Y - 4}" width="{PITCH}" height="{grid_h + 5}" fill="{t["chrome"]}" opacity=".1"/>'
             f'<rect x="{GRID_X - 2}" y="{GRID_Y - 4}" width="2" height="{grid_h + 5}" fill="{t["chrome"]}" '
             'filter="url(#glow)"/></g>')

    # totals by weekday, one bar per heatmap row
    by_day = [0] * 7
    for i, (_, count, _) in enumerate(days):
        by_day[(offset + i) % 7] += count
    bx = GRID_X + cols * PITCH + 34
    span = x + w - 14 - 40 - bx
    top = max(by_day) or 1
    o.append(text(bx, GRID_Y - 8, "BY WEEKDAY", 10, t["muted"], weight=700, extra=' letter-spacing=".8"'))
    for r, total_r in enumerate(by_day):
        by = GRID_Y + r * PITCH + 2.5
        length = max(2, span * total_r / top)
        o.append(f'<rect x="{bx}" y="{num(by)}" width="{num(length)}" height="8" rx="2" fill="{t["ramp"][2]}">'
                 f'<animate attributeName="width" values="0;0;{num(length)}" keyTimes="0;{0.8 + 0.08 * r:.2f};1" '
                 f'dur="{1.8 + 0.08 * r:.2f}s" calcMode="spline" keySplines="0 0 1 1;0.3 0.7 0.2 1" fill="freeze"/></rect>')
        o.append(text(bx + length + 6, by + 8, f"{total_r:,}", 10, t["muted"]))
    for r, name in enumerate("SMTWTFS"):
        o.append(text(bx - 8, GRID_Y + r * PITCH + 10, name, 10, t["muted"], "end"))

    # footer: best day, active days, legend
    fy = y + h - 20
    counts = [c for _, c, _ in days]
    best = max(range(len(days)), key=lambda i: counts[i])
    active = sum(1 for c in counts if c)
    best_day = dt.date.fromisoformat(days[best][0]).strftime("%b %d").upper()
    strong = f'fill="{t["text"]}" font-weight="700"'
    o.append(f'<text x="{x + 14}" y="{fy}" font-size="11" fill="{t["muted"]}">BEST DAY <tspan {strong}>{counts[best]}</tspan>'
             f' · {best_day} · ACTIVE <tspan {strong}>{active}</tspan>/{len(days)} DAYS · AVG '
             f'<tspan {strong}>{sum(counts) / max(active, 1):.1f}</tspan> PER ACTIVE DAY</text>')
    lx = x + w - 14 - 5 * 16 - 34
    o.append(text(lx - 8, fy, "LESS", 10, t["muted"], "end"))
    for k, fill in enumerate([t["cell"]] + t["ramp"]):
        o.append(f'<rect x="{lx + k * 16}" y="{fy - 10}" width="{CELL - 1}" height="{CELL - 1}" rx="2.5" fill="{fill}"/>')
    o.append(text(lx + 5 * 16 + 4, fy, "MORE", 10, t["muted"]))
    return o


def lang_mix(own, t):
    x, y, w, h = 35, 436, 420, 144
    langs = Counter(r["language"] for r in own if r["language"])
    o = panel(x, y, w, h, "LANG.MIX", t, f"{sum(langs.values())} REPOS · PRIMARY LANGUAGE")
    if not langs:
        return o
    # three hues pass as a categorical set; everything past the top three folds into Other.
    # Colors follow the language (alphabetical among the three), not its rank.
    top = [name for name, _ in langs.most_common(3)]
    color = {name: t["series"][i] for i, name in enumerate(sorted(top))}
    parts = [(name, langs[name], color[name]) for name in top]
    rest = sum(langs.values()) - sum(c for _, c, _ in parts)
    if rest:
        parts.append(("Other", rest, t["other"]))
    total = sum(c for _, c, _ in parts)

    bx, by, bw, gap = x + 14, y + 56, w - 28, 2
    usable = bw - gap * (len(parts) - 1)
    cx = bx
    for i, (name, count, fill) in enumerate(parts):
        seg = usable * count / total
        start = 0.4 + 0.25 * i
        o.append(f'<rect x="{num(cx)}" y="{by}" width="{num(seg)}" height="12" rx="2" fill="{fill}">'
                 f'<animate attributeName="width" values="0;0;{num(seg)}" keyTimes="0;{start / (start + .6):.3f};1" '
                 f'dur="{start + .6:.2f}s" calcMode="spline" keySplines="0 0 1 1;0.3 0.7 0.2 1" fill="freeze"/></rect>')
        cx += seg + gap
    for i, (name, count, fill) in enumerate(parts):
        lx, ly = bx + (i % 2) * (bw / 2), by + 42 + (i // 2) * 24
        o.append(f'<rect x="{num(lx)}" y="{ly - 10}" width="10" height="10" rx="2" fill="{fill}"/>')
        o.append(f'<text x="{num(lx + 18)}" y="{ly}" font-size="12" fill="{t["text"]}">{escape(name)} '
                 f'<tspan fill="{t["muted"]}">{100 * count / total:.0f}%</tspan></text>')
    return o


def push_log(own, user, t, today):
    x, y, w, h = 471, 436, W - 35 - 471, 144
    o = panel(x, y, w, h, "PUSH.LOG", t, "$ git log --all-repos -n 4")
    recent = sorted((r for r in own if r["name"].lower() != user.lower()), key=lambda r: r["pushed_at"], reverse=True)
    name_x, lang_end, star_x = x + 88, x + w - 88, x + w - 14
    for i, r in enumerate(recent[:LOG_LINES]):
        ly = y + 58 + i * 20
        lang = r["language"] or "—"
        lang_start = lang_end - len(lang) * 12 * CHAR
        max_name = int((lang_start - 30 - name_x) / (13 * CHAR))
        name = r["name"] if len(r["name"]) <= max_name else r["name"][:max_name - 1] + "…"
        dots_from = name_x + len(name) * 13 * CHAR + 10
        leader = "".join(f"M{num(d)} {ly - 4}h1" for d in range(int(dots_from), int(lang_start - 10), 5))
        start = 0.6 + 0.35 * i
        # each line types itself out: a clip that widens left to right
        o.append(f'<clipPath id="line{i}"><rect x="{x}" y="{ly - 15}" width="{w}" height="20">'
                 f'<animate attributeName="width" values="0;0;{w}" keyTimes="0;{start / (start + .5):.3f};1" '
                 f'dur="{start + .5:.2f}s" fill="freeze"/></rect></clipPath><g clip-path="url(#line{i})">')
        o.append(text(x + 14, ly, "▸", 13, t["chrome"]))
        o.append(text(x + 30, ly, short_date(r["pushed_at"], today), 12, t["muted"]))
        o.append(text(name_x, ly, name, 13, t["text"], weight=600))
        o.append(f'<path d="{leader}" fill="none" stroke="{t["line"]}" shape-rendering="crispEdges"/>')
        o.append(text(lang_end, ly, lang, 12, t["muted"], "end"))
        o.append(text(star_x, ly, f"★ {r['stargazers_count']}", 12, t["muted"], "end"))
        o.append("</g>")
    cy = y + 58 + LOG_LINES * 20
    o.append(text(x + 14, cy, "$", 13, t["chrome"], weight=700))
    o.append(f'<rect x="{x + 30}" y="{cy - 11}" width="8" height="14" fill="{t["chrome"]}">'
             '<animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" calcMode="discrete" dur="1.1s" '
             'repeatCount="indefinite"/></rect>')
    return o


def render(user, stats, total, days, own, t, today):
    o = [svg_open(W, H, f"{user} GitHub statistics", t)]
    o += window(W, H, "stats.sh --watch", t, f"SYNC {today.isoformat()}")
    o += tiles(stats, t)
    o += contrib_map(total, days, t)
    o += lang_mix(own, t)
    o += push_log(own, user, t, today)
    o.append("</svg>")
    return "".join(o)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--out", default="assets")
    args = p.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    today = dt.date.today()

    all_repos = repos(args.user, token)
    own = [r for r in all_repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    followers = request(f"{API}/users/{args.user}", token)["followers"]

    total, days = "-", []
    sources = ([lambda: calendar_graphql(args.user, token)] if token else []) + [lambda: calendar_page(args.user)]
    for source in sources:
        try:
            total, days = source()
            break
        except Exception as e:  # keep the REST tiles even if the calendar fails
            print(f"calendar source failed: {e}")
    days = [d for d in days if d[0] <= today.isoformat()]
    current, longest = streaks(days) if days else ("-", "-")

    stats = [("TOTAL STARS", stars, "across own repos"),
             ("REPOSITORIES", len(all_repos), f"{len(own)} own · {len(all_repos) - len(own)} forks"),
             ("FOLLOWERS", followers, "on github"),
             ("CONTRIBUTIONS", total, "last 12 months"),
             ("CURRENT STREAK", current, "days · ongoing" if current not in ("-", 0) else "days"),
             ("LONGEST STREAK", longest, "days in 12 months")]
    for name, theme in THEMES.items():
        Path(args.out, f"card-stats-{name}.svg").write_text(render(args.user, stats, total, days, own, theme, today))


if __name__ == "__main__":
    main()
