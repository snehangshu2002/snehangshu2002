"""Shared look for the generated README SVGs (radar.py, cards.py): the terminal
palette from the banner and a few SVG building blocks."""
from xml.sax.saxutils import escape

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace"
CHAR = 0.605                   # monospace advance per unit of font size

# ramp: contribution levels 1-4, one hue, validated as an ordinal ramp against panel2.
# series: categorical slots, validated all-pairs (any two can sit side by side) against
# panel2 - only three pass in both modes, so a fourth category folds into `other`.
THEMES = {
    "dark": dict(bg="#0A101F", panel="#0D1628", panel2="#101B30", cell="#182338", line="#25344C",
                 muted="#8291A8", text="#DDE7F5", chrome="#22D3EE", violet="#AA9BEF", accent="#10B981",
                 live="#FF4D5A", shadow="#02050B",
                 ramp=["#4E4899", "#6C62C0", "#9387E3", "#C4BBFF"],
                 series=["#9085E9", "#199E70", "#D95926"], other="#5B6B84"),
    "light": dict(bg="#F6F8FA", panel="#FFFFFF", panel2="#EDF3F7", cell="#DCE4EC", line="#CBD7E1",
                  muted="#64748B", text="#172033", chrome="#0891B2", violet="#6553C4", accent="#0E9F6E",
                  live="#CF222E", shadow="#AAB7C4",
                  ramp=["#ADA1EC", "#8C7DE0", "#6553C4", "#40336E"],
                  series=["#4A3AA7", "#1BAF7A", "#EB6834"], other="#94A3B8"),
}


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".") if v % 1 else f"{v:.0f}"


def text(x, y, s, size, fill, anchor="start", weight=400, extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    w = f' font-weight="{weight}"' if weight != 400 else ""
    return f'<text x="{num(x)}" y="{num(y)}" font-size="{size}" fill="{fill}"{a}{w}{extra}>{escape(str(s))}</text>'


def svg_open(w, h, label, t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}" font-family="{FONT}"><defs>'
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
            f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".28"/></filter>'
            '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
            f'<feGaussianBlur stdDeviation="3" result="b"/><feFlood flood-color="{t["chrome"]}" flood-opacity=".35"/>'
            '<feComposite in2="b" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
            '</filter></defs>')


def window(w, h, title, t, right=""):
    """Terminal window chrome: backdrop, shadowed frame, title bar with traffic lights."""
    o = [f'<rect width="{w}" height="{h}" rx="18" fill="{t["bg"]}"/>',
         f'<rect x="13" y="13" width="{w - 26}" height="{h - 26}" rx="13" fill="{t["panel"]}" '
         f'stroke="{t["line"]}" filter="url(#shadow)"/>',
         f'<path d="M13 62H{w - 13}" stroke="{t["line"]}"/>']
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        o.append(f'<circle cx="{38 + 21 * i}" cy="38" r="6" fill="{c}"/>')
    o.append(text(w / 2, 43, title, 13, t["muted"], "middle", extra=' letter-spacing=".4"'))
    if right:
        o.append(text(w - 35, 43, right, 11, t["muted"], "end"))
    return o


def panel(x, y, w, h, tag, t, right=""):
    """An inner panel with a cyan TAG header and a divider, like VISUAL.MAP in the banner."""
    o = [f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="6" fill="{t["panel2"]}" '
         f'stroke="{t["line"]}"/>',
         f'<path d="M{num(x)} {num(y + 36)}h{num(w)}" stroke="{t["line"]}"/>',
         text(x + 14, y + 23, tag, 13, t["chrome"], weight=700, extra=' letter-spacing="1.2"')]
    if right:
        o.append(text(x + w - 14, y + 23, right, 11, t["muted"], "end"))
    return o


def odometer(x, y, value, size, fill, clip_id, delay):
    """A number whose digits spin up into place; a static renderer shows the final value."""
    s = f"{value:,}" if isinstance(value, int) else str(value)
    adv, lh = size * CHAR, size * 1.3                  # digits sit further apart than the clip is tall
    o = [f'<clipPath id="{clip_id}"><rect x="{num(x - 2)}" y="{num(y - size * 0.8)}" width="{num(len(s) * adv + 4)}" '
         f'height="{num(size * 1.02)}"/></clipPath><g clip-path="url(#{clip_id})" font-size="{size}" '
         f'font-weight="700" fill="{fill}">']
    for i, ch in enumerate(s):
        cx = x + i * adv
        if not ch.isdigit():
            o.append(f'<text x="{num(cx)}" y="{num(y)}">{escape(ch)}</text>')
            continue
        rows = 10 + int(ch)                            # one full turn, then land on the digit
        shift = f"0 {num(-rows * lh)}"
        dur = 1.4 + 0.12 * i + delay
        spans = "".join(f'<tspan x="{num(cx)}" dy="{num(lh)}">{k % 10}</tspan>' for k in range(1, 20))
        o.append(f'<g transform="translate({shift})"><animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;0 0;{shift}" keyTimes="0;{delay / dur:.3f};1" dur="{dur:.2f}s" calcMode="spline" '
                 f'keySplines="0 0 1 1;0.3 0.7 0.2 1" fill="freeze"/><text x="{num(cx)}" y="{num(y)}">0{spans}</text></g>')
    o.append("</g>")
    return "".join(o)
