"""Generate the `profile.sh --live` terminal banner for the README.

A photo is cut out from its background, dithered to 1-bit with serpentine
Floyd-Steinberg, and drawn as a dot map next to a SYSTEM.INFO panel.
Writes assets/banner-dark.svg and assets/banner-light.svg.

    python scripts/banner.py [--photo assets/source/me.png]
"""
import argparse
from collections import deque
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]

ROWS = [
    ("Subject", "Snehangshu Bhuin"),
    ("Role", "Data Scientist · Data Analyst"),
    ("Origin", "India"),
    ("Education", "M.Sc. Statistics · Visva-Bharati"),
    ("Status", "Open to Full-Time Roles"),
    ("ToolChain", "VS Code · Jupyter · Git"),
    ("Core.Lang", "Python · SQL · R"),
    ("Core.ML", "PyTorch · TensorFlow · scikit-learn"),
    ("Core.LLM", "QLoRA · PEFT · TRL · HuggingFace"),
    ("Core.RAG", "LangChain · LangGraph · FAISS"),
    ("Core.Data", "Pandas · DuckDB · Postgres · Streamlit"),
    ("Core.Auto", "n8n · MCP · Docker"),
    ("Grid.Mail", "snehangshubhuin@gmail.com"),
    ("Grid.HF", "snehangshu511"),
    ("Grid.GitHub", "snehangshu2002"),
]

THEMES = {
    "dark": dict(bg="#0A101F", panel="#0D1628", line="#25344C", muted="#8291A8", text="#DDE7F5",
                 portrait="#AA9BEF", chrome="#22D3EE", accent="#10B981", live="#F43F5E", pill="#12304A"),
    "light": dict(bg="#F6F8FA", panel="#FFFFFF", line="#D0D7DE", muted="#57606A", text="#1F2328",
                  portrait="#4A3D7A", chrome="#0086A3", accent="#1A7F37", live="#CF222E", pill="#DDF4FA"),
}

W, H = 1180, 610
MAP_W, MAP_H = 300, 340        # portrait area in SVG units
COLS, ROWS_PX = MAP_W, MAP_H   # dither grid, one dot per SVG unit
MAX_PTS = 18000                # dots kept, sampled at random: an even grain, not a solid block
FONT = "JetBrains Mono,SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace"
CHAR = 0.6                     # monospace advance per unit of font size


def cut_out(img):
    """Mask of the subject: region-grow the flat backdrop (light or dark) in from the edges."""
    small = img.resize((img.width // 2, img.height // 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
    a = np.asarray(small).astype(float)
    h, w, _ = a.shape
    lum, sat = a.mean(2), a.max(2) - a.min(2)
    backdrop = np.median(np.concatenate([lum[:20, :20].ravel(), lum[:20, -20:].ravel()]))
    dark = backdrop < 60
    # dark hair against a dark backdrop only differs by a few levels, so grow more cautiously
    ok = (lum < backdrop + 9) if dark else (lum > 88)
    ok &= sat < 20
    step = 4 if dark else 6
    bg = np.zeros((h, w), bool)
    q = deque(p for p in [(0, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)] if ok[p])
    for p in q:
        bg[p] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and ok[ny, nx] \
                    and np.abs(a[ny, nx] - a[y, x]).max() < step:
                bg[ny, nx] = True
                q.append((ny, nx))
    mask = Image.fromarray((~bg * 255).astype(np.uint8))
    # close the gaps the backdrop leaks into between strands of hair and beard; this
    # gives a solid but boxy outline
    coarse = mask.filter(ImageFilter.MaxFilter(35)).filter(ImageFilter.MinFilter(35))
    # well inside the outline everything is subject; near the edge keep only pixels that
    # actually differ from the backdrop, so frizzy hair keeps its real shape
    inner = np.asarray(coarse.filter(ImageFilter.MinFilter(31))) > 128
    differs = np.abs(lum - backdrop) > 7
    keep = inner | ((np.asarray(coarse) > 128) & differs)
    mask = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
    return mask.resize(img.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))


def floyd_steinberg(gray):
    """Serpentine Floyd-Steinberg on a 0..1 array; True = dot."""
    g = gray.copy()
    h, w = g.shape
    out = np.zeros_like(g, bool)
    for y in range(h):
        xs = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        d = 1 if y % 2 == 0 else -1
        for x in xs:
            old = g[y, x]
            new = old >= 0.5
            out[y, x] = new
            err = old - new
            if 0 <= x + d < w:
                g[y, x + d] += err * 7 / 16
            if y + 1 < h:
                if 0 <= x - d < w:
                    g[y + 1, x - d] += err * 3 / 16
                g[y + 1, x] += err * 5 / 16
                if 0 <= x + d < w:
                    g[y + 1, x + d] += err * 1 / 16
    return out


def crop_box(mask):
    """Head-and-shoulders box at the panel's aspect ratio, centred on the head."""
    m = np.asarray(mask) > 128
    rows = np.where(m.any(1))[0]
    top = rows[0]
    head = m[top: top + m.shape[0] // 4]               # top quarter of the subject
    cols = np.where(head.any(0))[0]
    cx, head_w = (cols[0] + cols[-1]) / 2, cols[-1] - cols[0]
    w = min(mask.width, head_w * 1.9)
    h = w * MAP_H / MAP_W
    x0 = int(np.clip(cx - w / 2, 0, mask.width - w))
    y0 = int(max(0, top - 0.06 * h))
    return x0, y0, int(x0 + w), int(min(mask.height, y0 + h))


def dither(photo):
    img = Image.open(photo).convert("RGB")
    mask = cut_out(img)
    box = crop_box(mask)
    rgb = img.crop(box).resize((COLS, ROWS_PX), Image.LANCZOS)
    alpha = mask.crop(box).resize((COLS, ROWS_PX), Image.LANCZOS)
    a = np.asarray(alpha).astype(float) / 255
    # a light backdrop leaves a bright fringe along the outline that would light up as a
    # halo on the dark panel, so the dark theme uses an outline pulled a few pixels in
    tight = mask.filter(ImageFilter.MinFilter(9)).crop(box).resize((COLS, ROWS_PX), Image.LANCZOS)
    a_dark = np.asarray(tight).astype(float) / 255
    subject = alpha.point(lambda v: 255 if v > 20 else 0)

    def prepare(gray, light):
        # equalize against the subject only, so the empty backdrop doesn't skew the histogram
        gray = ImageOps.equalize(gray, mask=subject)
        # ink on white loses more to the random thinning, so it gets extra contrast
        gray = ImageEnhance.Contrast(gray).enhance(1.6 if light else 1.35)
        gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=175, threshold=1))
        return np.asarray(gray).astype(float) / 255

    lum = np.asarray(rgb.convert("L")).astype(float)
    # dark theme: lit dots on a dark panel, backdrop blacked out
    lit = prepare(Image.fromarray(np.uint8(lum * a_dark)), light=False)
    dark_bits = floyd_steinberg(lit) & (a_dark > 0.5)
    # light theme: ink dots for shadows on a white panel, backdrop whited out
    paper = prepare(Image.fromarray(np.uint8(lum * a + 255 * (1 - a))), light=True)
    light_bits = ~floyd_steinberg(paper) & (a > 0.08)
    return {"dark": thin(dark_bits), "light": thin(light_bits)}


def thin(bits, seed=314159):
    """Keep a random MAX_PTS of the dots, for the even stipple grain."""
    ys, xs = np.nonzero(bits)
    if len(xs) > MAX_PTS:
        keep = np.random.default_rng(seed).choice(len(xs), MAX_PTS, replace=False)
        bits = np.zeros_like(bits)
        bits[ys[keep], xs[keep]] = True
    return bits


def dots_path(bits, x0, y0):
    """One-unit dots as horizontal stroke runs: M x y h len, merging neighbours."""
    d = []
    for y in range(bits.shape[0]):
        row = np.flatnonzero(np.diff(np.concatenate(([0], bits[y].astype(np.int8), [0]))))
        for start, stop in zip(row[::2], row[1::2]):
            d.append(f"M{x0 + start:g} {y0 + y + 0.5:g}h{stop - start}")
    return "".join(d)


def text(x, y, s, size, fill, anchor="start", weight=400, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{extra}>{escape(s)}</text>')


def render(bits, t, handle):
    n_pts = int(bits.sum())
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-label="profile.sh --live" font-family="{FONT}">',
         '<style>.row{animation:in .35s ease-out backwards}'
         '@keyframes in{from{opacity:0}}'
         '.blink{animation:blink 1.4s steps(1) infinite}@keyframes blink{50%{opacity:0}}'
         '@media (prefers-reduced-motion:reduce){.row,.blink{animation:none}}</style>',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{t["bg"]}" stroke="{t["line"]}"/>']
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        o.append(f'<circle cx="{26 + 20 * i}" cy="26" r="6" fill="{c}"/>')
    o.append(text(W / 2, 30, "profile.sh --live", 12, t["muted"], "middle"))

    # ---- VISUAL.MAP panel
    px, py, pw, ph = 30, 56, 380, 524
    o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="8" fill="{t["panel"]}" stroke="{t["line"]}"/>')
    o.append(text(px + 16, py + 24, "VISUAL.MAP", 12, t["chrome"], weight=700, extra=' letter-spacing="1"'))
    o.append(text(px + pw - 16, py + 24, f"{MAP_W}×{MAP_H} / 1-BIT", 10, t["muted"], "end"))
    o.append(f'<line x1="{px}" y1="{py + 38}" x2="{px + pw}" y2="{py + 38}" stroke="{t["line"]}"/>')
    ix, iy = px + (pw - MAP_W) / 2, py + 58 + (ph - 100 - MAP_H) / 2
    for cx, cy, sx, sy in ((px + 14, py + 52, 1, 1), (px + pw - 14, py + 52, -1, 1),
                           (px + 14, py + ph - 38, 1, -1), (px + pw - 14, py + ph - 38, -1, -1)):
        o.append(f'<path d="M{cx} {cy + 14 * sy}V{cy}H{cx + 14 * sx}" fill="none" stroke="{t["chrome"]}" stroke-width="1.2" opacity=".7"/>')
    # scanline reveal: the clip grows top to bottom once (full height if SMIL is off)
    o.append(f'<clipPath id="scan"><rect x="{ix}" y="{iy}" width="{MAP_W}" height="{MAP_H}">'
             f'<animate attributeName="height" from="0" to="{MAP_H}" dur="2.2s" fill="freeze" '
             'calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/></rect></clipPath>')
    o.append(f'<path d="{dots_path(bits, ix, iy)}" fill="none" stroke="{t["portrait"]}" stroke-width="1" '
             'clip-path="url(#scan)"/>')
    o.append(text(px + 16, py + ph - 14, f"PTS {n_pts} · FS/SERPENTINE", 10, t["muted"]))

    # ---- SYSTEM.INFO panel
    sx, sy, sw, sh = 430, 56, 720, 524
    o.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="8" fill="{t["panel"]}" stroke="{t["line"]}"/>')
    o.append(text(sx + 16, sy + 24, "SYSTEM.INFO", 12, t["chrome"], weight=700, extra=' letter-spacing="1"'))
    pill_w = len(handle) * 12 * CHAR + 36
    o.append(f'<rect x="{sx + sw - 16 - pill_w:.1f}" y="{sy + 10}" width="{pill_w:.1f}" height="22" rx="11" fill="{t["pill"]}"/>')
    o.append(text(sx + sw - 16 - pill_w / 2, sy + 25, handle, 12, t["chrome"], "middle", 700))
    live_x = sx + sw - 16 - pill_w - 20
    o.append(f'<circle class="blink" cx="{live_x - 38:.1f}" cy="{sy + 21}" r="3.5" fill="{t["live"]}"/>')
    o.append(text(live_x, sy + 25, "LIVE", 10, t["live"], "end", 700))
    o.append(f'<line x1="{sx}" y1="{sy + 38}" x2="{sx + sw}" y2="{sy + 38}" stroke="{t["line"]}"/>')

    left, right, size = sx + 16, sx + sw - 16, 13
    for i, (label, value) in enumerate(ROWS):
        y = sy + 72 + i * 27
        x1 = left + len(label) * size * CHAR + 10
        x2 = right - len(value) * size * CHAR - 10
        o.append(f'<g class="row" style="animation-delay:{0.6 + i * 0.12:.2f}s">')
        o.append(text(left, y, label, size, t["muted"]))
        o.append(f'<line x1="{x1:.1f}" y1="{y - 4}" x2="{x2:.1f}" y2="{y - 4}" stroke="{t["line"]}" stroke-dasharray="1 5"/>')
        o.append(text(right, y, value, size, t["text"], "end", 600))
        o.append("</g>")

    o.append(f'<line x1="{sx}" y1="{sy + sh - 34}" x2="{sx + sw}" y2="{sy + sh - 34}" stroke="{t["line"]}"/>')
    o.append(f'<circle cx="{sx + 20}" cy="{sy + sh - 17}" r="3.5" fill="{t["accent"]}"/>')
    o.append(text(sx + 30, sy + sh - 13, "ALL SYSTEMS NOMINAL", 10, t["accent"], weight=700))
    o.append(text(sx + sw - 16, sy + sh - 13, "UTC+5:30 · IN NODE", 10, t["muted"], "end"))
    o.append("</svg>")
    return "".join(o)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--photo", default=ROOT / "assets/source/me.png", type=Path)
    p.add_argument("--handle", default="@snehangshu2002")
    args = p.parse_args()
    bits = dither(args.photo)
    for name, theme in THEMES.items():
        path = ROOT / f"assets/banner-{name}.svg"
        path.write_text(render(bits[name], theme, args.handle))
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB  {int(bits[name].sum())} pts")


if __name__ == "__main__":
    main()
