"""Self-hosted GitHub stats card (dark + light), so the README doesn't depend on
shared public stat services that go down.

Stars, repos and followers come from the REST API. Contributions and streaks
need GraphQL, which needs GITHUB_TOKEN; without one those tiles show "-".

    python scripts/cards.py --user snehangshu2002 --out assets
"""
import argparse
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

API = "https://api.github.com"
THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", accent="#00d9ff", big="#e6edf3", small="#8b949e"),
    "light": dict(bg="#ffffff", border="#d0d7de", accent="#0086a3", big="#1f2328", small="#57606a"),
}


def request(url, token, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    with urllib.request.urlopen(urllib.request.Request(url, data, headers)) as r:
        return json.load(r)


def repo_stats(user, token):
    repos, page = [], 1
    while batch := request(f"{API}/users/{user}/repos?per_page=100&type=owner&page={page}", token):
        repos += batch
        page += 1
    own = [r for r in repos if not r["fork"]]
    return sum(r["stargazers_count"] for r in own), len(repos)


def contributions(user, token):
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
           totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    cal = request(f"{API}/graphql", token, {"query": q, "variables": {"u": user}})
    cal = cal["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days = [d for d in days if d["date"] <= dt.date.today().isoformat()]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current = 0
    # today not having a commit yet shouldn't break the streak
    for d in reversed(days[:-1] if days and not days[-1]["contributionCount"] else days):
        if not d["contributionCount"]:
            break
        current += 1
    return cal["totalContributions"], current, longest


def render(user, tiles, t):
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 159" width="480" height="159" role="img" '
        f'aria-label="{user} GitHub statistics" font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<rect x="0.5" y="0.5" width="479" height="158" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="22" y="36" font-size="15" font-weight="700" fill="{t["accent"]}">{user}</text>',
        f'<text x="458" y="36" font-size="11" text-anchor="end" fill="{t["small"]}">at a glance</text>',
        f'<line x1="22" y1="48" x2="458" y2="48" stroke="{t["border"]}"/>',
    ]
    for i, (label, value) in enumerate(tiles):
        x, y = 22 + 145.5 * (i % 3), 74 + 46 * (i // 3)
        out.append(f'<text x="{x:.0f}" y="{y}" font-size="23" font-weight="700" fill="{t["big"]}">{value}</text>')
        out.append(f'<text x="{x:.0f}" y="{y + 17}" font-size="10.5" fill="{t["small"]}">{label}</text>')
    out.append("</svg>")
    return "".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--out", default="assets")
    args = p.parse_args()
    token = os.environ.get("GITHUB_TOKEN")

    stars, repos = repo_stats(args.user, token)
    followers = request(f"{API}/users/{args.user}", token)["followers"]
    total = current = longest = "-"
    if token:
        try:
            total, current, longest = contributions(args.user, token)
        except Exception as e:  # keep the REST tiles even if GraphQL fails
            print(f"contributions unavailable: {e}")

    tiles = [("Total stars", stars), ("Public repos", repos), ("Followers", followers),
             ("Contributions (1y)", total), ("Current streak", current), ("Longest streak", longest)]
    for name, theme in THEMES.items():
        Path(args.out, f"card-stats-{name}.svg").write_text(render(args.user, tiles, theme))


if __name__ == "__main__":
    main()
