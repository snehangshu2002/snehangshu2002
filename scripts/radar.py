"""Draw a radar chart from a JSON file of {title, axes: [{label, value}]}.

Writes <out>-dark.svg and <out>-light.svg so the README can swap them with
<picture> and prefers-color-scheme.

    python scripts/radar.py --data assets/skills.json -o assets/radar [--values]
"""
import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

THEMES = {
    "dark": dict(title="#e6edf3", label="#c9d1d9", value="#8b949e", ring="#30363d",
                 spoke="#21262d", fill="#00d9ff", stroke="#00d9ff", dot="#7df3ff"),
    "light": dict(title="#1f2328", label="#24292f", value="#57606a", ring="#d0d7de",
                  spoke="#eaeef2", fill="#0096b4", stroke="#0086a3", dot="#ffffff"),
}
W, H, R, RINGS = 746, 526, 200, 4


def point(i, n, r):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return r * math.cos(a), r * math.sin(a)


def pts(values, n):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, n, v) for i, v in enumerate(values)))


def render(data, theme, show_values):
    t = THEMES[theme]
    axes = data["axes"]
    n = len(axes)
    cx, cy = W / 2, H / 2 + 22
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(data["title"])}" '
        'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<text x="{W / 2}" y="25" text-anchor="middle" font-size="15" font-weight="700" '
        f'fill="{t["title"]}">{escape(data["title"])}</text>',
        f'<g transform="translate({cx:.1f},{cy:.1f})">',
    ]
    for k in range(RINGS, 0, -1):
        opacity = 0.45 + 0.4 * k / RINGS
        out.append(f'<polygon points="{pts([R * k / RINGS] * n, n)}" fill="none" '
                   f'stroke="{t["ring"]}" stroke-width="1" opacity="{opacity:.2f}"/>')
    for i in range(n):
        x, y = point(i, n, R)
        out.append(f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" stroke="{t["spoke"]}" stroke-width="1"/>')

    radii = [R * max(0, min(100, a["value"])) / 100 for a in axes]
    out.append('<g><animateTransform attributeName="transform" type="scale" values="0.04;1" dur="1.1s" '
               'calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1" fill="freeze"/>')
    out.append(f'<polygon points="{pts(radii, n)}" fill="{t["fill"]}" fill-opacity="0.2" '
               f'stroke="{t["stroke"]}" stroke-width="2.5" stroke-linejoin="round"/>')
    for i, r in enumerate(radii):
        x, y = point(i, n, r)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{t["dot"]}" '
                   f'stroke="{t["stroke"]}" stroke-width="1.2"/>')
    out.append("</g>")

    for i, a in enumerate(axes):
        x, y = point(i, n, R + 24)
        anchor = "middle" if abs(x) < 1 else ("start" if x > 0 else "end")
        y += 5 if abs(x) >= 1 else (-4 if y < 0 else 14)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="13" '
                   f'font-weight="600" fill="{t["label"]}">{escape(a["label"])}'
                   + (f'<tspan fill="{t["value"]}" font-weight="400"> {a["value"]}</tspan>' if show_values else "")
                   + "</text>")
    out.append("</g></svg>")
    return "".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("-o", "--out", required=True, help="output prefix, e.g. assets/radar")
    p.add_argument("--values", action="store_true", help="print the value next to each label")
    args = p.parse_args()
    data = json.loads(Path(args.data).read_text())
    for theme in THEMES:
        Path(f"{args.out}-{theme}.svg").write_text(render(data, theme, args.values))


if __name__ == "__main__":
    main()
