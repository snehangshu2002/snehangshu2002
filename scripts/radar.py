"""Draw a radar scope from a JSON file of {title, tag, accent, axes: [{label, value}]}.

The chart sits in a terminal window like the banner. The polygon grows in from the
centre, then a radar beam sweeps round and each vertex pings as the beam crosses it.
`accent` is "chrome" (cyan) or "violet". Writes <out>-dark.svg and <out>-light.svg
so the README can swap them with <picture> and prefers-color-scheme.

    python scripts/radar.py --data assets/skills.json -o assets/radar [--values]
"""
import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from style import CHAR, THEMES, num, svg_open, text, window

W = H = 600
CX, CY, R = 300, 330, 132
SWEEP = 6.0                    # seconds per beam revolution
START = 1.2                    # beam starts once the polygon has grown in
TRAIL = 16                     # 3-degree wedges fading out behind the beam


def point(i, n, r):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return r * math.cos(a), r * math.sin(a)


def pts(radii, n):
    return " ".join(f"{num(x)},{num(y)}" for x, y in (point(i, n, r) for i, r in enumerate(radii)))


def wedge(a0, a1, r):
    """Pie slice from angle a0 to a1 (degrees, clockwise from +x)."""
    (x0, y0), (x1, y1) = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (a0, a1)]
    return f"M0 0L{num(x0)} {num(y0)}A{r} {r} 0 0 1 {num(x1)} {num(y1)}Z"


def wrap(label, width=12):
    """Split a long label at the space nearest its middle."""
    if len(label) <= width or " " not in label:
        return [label]
    cut = min((i for i, c in enumerate(label) if c == " "), key=lambda i: abs(i - len(label) / 2))
    return [label[:cut].strip(), label[cut:].strip()]


def render(data, theme, show_values):
    t = THEMES[theme]
    accent = t[data.get("accent", "chrome")]
    axes = data["axes"]
    n = len(axes)
    values = [max(0, min(100, a["value"])) for a in axes]
    radii = [R * v / 100 for v in values]
    tag = data.get("tag", "SIGNAL")

    o = [svg_open(W, H, data["title"], t)]
    o += window(W, H, f"radar.sh --{tag.split('.')[-1].lower()}", t)
    o.append(text(35, 95, tag, 13, t["chrome"], weight=700, extra=' letter-spacing="1.2"'))
    o.append(text(W - 35, 95, "SELF-RATED · 0-100", 11, t["muted"], "end"))
    o.append(f'<path d="M35 110H{W - 35}" stroke="{t["line"]}"/>')

    o.append(f'<g transform="translate({CX},{CY})">')
    # scope face: faint dot texture, dashed rings, spokes, ring values between the first two spokes
    o.append(f'<clipPath id="face"><polygon points="{pts([R] * n, n)}"/></clipPath>'
             f'<pattern id="grain" width="10" height="10" patternUnits="userSpaceOnUse">'
             f'<circle cx="1" cy="1" r=".8" fill="{t["line"]}"/></pattern>'
             f'<rect x="{-R}" y="{-R}" width="{2 * R}" height="{2 * R}" fill="url(#grain)" opacity=".7" clip-path="url(#face)"/>')
    for k in (1, 2, 3, 4):
        dash = "" if k == 4 else ' stroke-dasharray="2 4"'
        o.append(f'<polygon points="{pts([R * k / 4] * n, n)}" fill="none" stroke="{t["line"]}"{dash}/>')
    for i in range(n):
        x, y = point(i, n, R)
        o.append(f'<line x2="{num(x)}" y2="{num(y)}" stroke="{t["line"]}"/>')
    for k in (1, 2, 3, 4):
        x, y = point(0.5, n, R * k / 4)
        o.append(text(x + 4, y + 3, 25 * k, 9, t["muted"]))

    # beam: a bright leading edge with a fading trail, one turn every SWEEP seconds
    o.append(f'<g clip-path="url(#face)"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" '
             f'begin="{START}s" dur="{SWEEP}s" repeatCount="indefinite"/>')
    for k in range(TRAIL):
        opacity = 0.26 * (1 - k / TRAIL) ** 1.6
        o.append(f'<path d="{wedge(-90 - 3 * (k + 1), -90 - 3 * k, R)}" fill="{accent}" opacity="{opacity:.3f}"/>')
    o.append(f'<line y2="{-R}" stroke="{accent}" stroke-width="1.5" opacity=".85"/></g></g>')

    # data polygon grows in from the centre
    o.append('<g><animateTransform attributeName="transform" type="scale" values="0.04;1" dur="1.1s" '
             'calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1" fill="freeze"/>')
    o.append(f'<polygon points="{pts(radii, n)}" fill="{accent}" fill-opacity=".16" stroke="{accent}" '
             'stroke-width="2" stroke-linejoin="round"/>')
    for i, r in enumerate(radii):
        x, y = point(i, n, r)
        # ping: a ring bursts out of the vertex each time the beam crosses its spoke
        o.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="4" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0">'
                 f'<animate attributeName="r" values="4;16;16" keyTimes="0;.3;1" begin="{START + SWEEP * i / n:.2f}s" '
                 f'dur="{SWEEP}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values=".9;0;0" keyTimes="0;.3;1" begin="{START + SWEEP * i / n:.2f}s" '
                 f'dur="{SWEEP}s" repeatCount="indefinite"/></circle>')
        o.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="4.5" fill="{accent}" stroke="{t["panel"]}" stroke-width="2"/>')
    o.append("</g>")

    # labels: muted name, value in text ink; long names wrap onto two lines
    for i, (a, v) in enumerate(zip(axes, values)):
        lines = wrap(a["label"])
        x, y = point(i, n, R + 20)
        anchor = "middle" if abs(x) < 1 else ("start" if x > 0 else "end")
        if abs(x) < 1:
            y += -8 - 18 * (len(lines) - 1) if y < 0 else 17
        else:
            y += 5 - 9 * (len(lines) - 1)
        spans = []
        for j, line in enumerate(lines):
            dy = "" if j == 0 else ' dy="18"'
            spans.append(f'<tspan x="{num(x)}"{dy}>{escape(line)}</tspan>')
        if show_values:
            spans.append(f'<tspan fill="{t["text"]}" font-weight="700"> {v}</tspan>')
        o.append(f'<text x="{num(x)}" y="{num(y)}" text-anchor="{anchor}" font-size="15" fill="{t["muted"]}">'
                 + "".join(spans) + "</text>")
    o.append("</g>")

    # footer: mean and peak
    avg = sum(values) / n
    peak = max(range(n), key=lambda i: values[i])
    o.append(f'<path d="M35 {H - 62}H{W - 35}" stroke="{t["line"]}"/>')
    o.append(f'<text x="35" y="{H - 38}" font-size="11" fill="{t["muted"]}">AVG <tspan fill="{t["text"]}" '
             f'font-weight="700">{avg:.0f}</tspan> · PEAK {escape(axes[peak]["label"].upper())} '
             f'<tspan fill="{t["text"]}" font-weight="700">{values[peak]}</tspan></text>')
    o.append(f'<circle cx="{W - 35 - len("SWEEP ON") * 11 * CHAR - 10:.1f}" cy="{H - 42}" r="3.5" fill="{accent}">'
             '<animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    o.append(text(W - 35, H - 38, "SWEEP ON", 11, t["muted"], "end", 700))
    o.append("</svg>")
    return "".join(o)


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
