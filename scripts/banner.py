"""Generate the animated `profile.sh --live` terminal banner for the README.

A photo is cut out from its background, dithered to 1-bit with serpentine
Floyd-Steinberg, and drawn as a dot map next to a SYSTEM.INFO panel. After a
short hold the portrait dissolves and 1200 of its dots fly into Python, PyTorch
and Hugging Face silhouettes, then back into the face, on a 14.2 s SMIL loop.
Writes assets/banner-dark.svg and assets/banner-light.svg.

    python scripts/banner.py [--photo assets/source/me.png]

Needs numpy, pillow and scipy.
"""
import argparse
import math
import re
from collections import deque
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

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
    "dark": dict(bg="#0A101F", panel="#0D1628", panel2="#101B30", line="#25344C", muted="#8291A8",
                 text="#DDE7F5", portrait="#AA9BEF", chrome="#22D3EE", accent="#10B981",
                 live="#FF4D5A", shadow="#02050B"),
    "light": dict(bg="#F6F8FA", panel="#FFFFFF", panel2="#EDF3F7", line="#CBD7E1", muted="#64748B",
                  text="#172033", portrait="#4A3D7A", chrome="#0891B2", accent="#10B981",
                  live="#CF222E", shadow="#AAB7C4"),
}

# Silhouettes the portrait morphs through, in order. 24x24 path data from Simple Icons (CC0).
LOGOS = {
    "python": "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
    "pytorch": "M12.005 0L4.952 7.053a9.865 9.865 0 000 14.022 9.866 9.866 0 0014.022 0c3.984-3.9 3.986-10.205.085-14.023l-1.744 1.743c2.904 2.905 2.904 7.634 0 10.538s-7.634 2.904-10.538 0-2.904-7.634 0-10.538l4.647-4.646.582-.665zm3.568 3.899a1.327 1.327 0 00-1.327 1.327 1.327 1.327 0 001.327 1.328A1.327 1.327 0 0016.9 5.226 1.327 1.327 0 0015.573 3.9z",
    "huggingface": "M12.025 1.13c-5.77 0-10.449 4.647-10.449 10.378 0 1.112.178 2.181.503 3.185.064-.222.203-.444.416-.577a.96.96 0 0 1 .524-.15c.293 0 .584.124.84.284.278.173.48.408.71.694.226.282.458.611.684.951v-.014c.017-.324.106-.622.264-.874s.403-.487.762-.543c.3-.047.596.06.787.203s.31.313.4.467c.15.257.212.468.233.542.01.026.653 1.552 1.657 2.54.616.605 1.01 1.223 1.082 1.912.055.537-.096 1.059-.38 1.572.637.121 1.294.187 1.967.187.657 0 1.298-.063 1.921-.178-.287-.517-.44-1.041-.384-1.581.07-.69.465-1.307 1.081-1.913 1.004-.987 1.647-2.513 1.657-2.539.021-.074.083-.285.233-.542.09-.154.208-.323.4-.467a1.08 1.08 0 0 1 .787-.203c.359.056.604.29.762.543s.247.55.265.874v.015c.225-.34.457-.67.683-.952.23-.286.432-.52.71-.694.257-.16.547-.284.84-.285a.97.97 0 0 1 .524.151c.228.143.373.388.43.625l.006.04a10.3 10.3 0 0 0 .534-3.273c0-5.731-4.678-10.378-10.449-10.378M8.327 6.583a1.5 1.5 0 0 1 .713.174 1.487 1.487 0 0 1 .617 2.013c-.183.343-.762-.214-1.102-.094-.38.134-.532.914-.917.71a1.487 1.487 0 0 1 .69-2.803m7.486 0a1.487 1.487 0 0 1 .689 2.803c-.385.204-.536-.576-.916-.71-.34-.12-.92.437-1.103.094a1.487 1.487 0 0 1 .617-2.013 1.5 1.5 0 0 1 .713-.174m-10.68 1.55a.96.96 0 1 1 0 1.921.96.96 0 0 1 0-1.92m13.838 0a.96.96 0 1 1 0 1.92.96.96 0 0 1 0-1.92M8.489 11.458c.588.01 1.965 1.157 3.572 1.164 1.607-.007 2.984-1.155 3.572-1.164.196-.003.305.12.305.454 0 .886-.424 2.328-1.563 3.202-.22-.756-1.396-1.366-1.63-1.32q-.011.001-.02.006l-.044.026-.01.008-.03.024q-.018.017-.035.036l-.032.04a1 1 0 0 0-.058.09l-.014.025q-.049.088-.11.19a1 1 0 0 1-.083.116 1.2 1.2 0 0 1-.173.18q-.035.029-.075.058a1.3 1.3 0 0 1-.251-.243 1 1 0 0 1-.076-.107c-.124-.193-.177-.363-.337-.444-.034-.016-.104-.008-.2.022q-.094.03-.216.087-.06.028-.125.063l-.13.074q-.067.04-.136.086a3 3 0 0 0-.135.096 3 3 0 0 0-.26.219 2 2 0 0 0-.12.121 2 2 0 0 0-.106.128l-.002.002a2 2 0 0 0-.09.132l-.001.001a1.2 1.2 0 0 0-.105.212q-.013.036-.024.073c-1.139-.875-1.563-2.317-1.563-3.203 0-.334.109-.457.305-.454m.836 10.354c.824-1.19.766-2.082-.365-3.194-1.13-1.112-1.789-2.738-1.789-2.738s-.246-.945-.806-.858-.97 1.499.202 2.362c1.173.864-.233 1.45-.685.64-.45-.812-1.683-2.896-2.322-3.295s-1.089-.175-.938.647 2.822 2.813 2.562 3.244-1.176-.506-1.176-.506-2.866-2.567-3.49-1.898.473 1.23 2.037 2.16c1.564.932 1.686 1.178 1.464 1.53s-3.675-2.511-4-1.297c-.323 1.214 3.524 1.567 3.287 2.405-.238.839-2.71-1.587-3.216-.642-.506.946 3.49 2.056 3.522 2.064 1.29.33 4.568 1.028 5.713-.624m5.349 0c-.824-1.19-.766-2.082.365-3.194 1.13-1.112 1.789-2.738 1.789-2.738s.246-.945.806-.858.97 1.499-.202 2.362c-1.173.864.233 1.45.685.64.451-.812 1.683-2.896 2.322-3.295s1.089-.175.938.647-2.822 2.813-2.562 3.244 1.176-.506 1.176-.506 2.866-2.567 3.49-1.898-.473 1.23-2.037 2.16c-1.564.932-1.686 1.178-1.464 1.53s3.675-2.511 4-1.297c.323 1.214-3.524 1.567-3.287 2.405.238.839 2.71-1.587 3.216-.642.506.946-3.49 2.056-3.522 2.064-1.29.33-4.568 1.028-5.713-.624",
}

W, H = 1180, 610
MAP_W, MAP_H = 300, 340        # dither grid, one dot per SVG unit
MAP_X, MAP_Y = 74, 154         # where the grid sits inside VISUAL.MAP
CLIP = (49, 124, 390, 414)     # VISUAL.MAP drawing area: x, y, w, h
LOGO_BOX = (89, 188, 270)      # silhouettes fill this centred square: x, y, size
MAX_PTS = 18000                # dots kept, sampled at random: an even grain, not a solid block
TRAVELLERS = 1200              # portrait dots that fly into the logos
BANDS = 94                     # portrait chunks that drift apart as it dissolves
INTRO = 3.2                    # seconds before the loop starts
# portrait 3.0 s, each logo held 2.0 s, four 1.3 s morphs = 14.2 s
TIMES = [0, 3.0, 4.3, 6.3, 7.6, 9.6, 10.9, 12.9, 14.2]
LOOP = TIMES[-1]
SEED = 314159
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace"
CHAR = 0.605                   # monospace advance per unit of font size


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
    rgb = img.crop(box).resize((MAP_W, MAP_H), Image.LANCZOS)
    alpha = mask.crop(box).resize((MAP_W, MAP_H), Image.LANCZOS)
    a = np.asarray(alpha).astype(float) / 255
    # a light backdrop leaves a bright fringe along the outline that would light up as a
    # halo on the dark panel, so the dark theme uses an outline pulled a few pixels in
    tight = mask.filter(ImageFilter.MinFilter(9)).crop(box).resize((MAP_W, MAP_H), Image.LANCZOS)
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


def thin(bits, seed=SEED):
    """Keep a random MAX_PTS of the dots, for the even stipple grain."""
    ys, xs = np.nonzero(bits)
    if len(xs) > MAX_PTS:
        keep = np.random.default_rng(seed).choice(len(xs), MAX_PTS, replace=False)
        bits = np.zeros_like(bits)
        bits[ys[keep], xs[keep]] = True
    return bits


# ---- logo silhouettes: SVG path data -> filled mask -> evenly spread points

NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def arc(p0, rx, ry, phi, large, sweep, p1, n=24):
    """Points along an SVG elliptical arc (endpoint parameterisation, SVG spec F.6.5)."""
    (x1, y1), (x2, y2) = p0, p1
    if (x1, y1) == (x2, y2):
        return []
    rx, ry = abs(rx), abs(ry)
    if not rx or not ry:
        return [p1]
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    xp, yp = c * dx + s * dy, -s * dx + c * dy
    scale = xp ** 2 / rx ** 2 + yp ** 2 / ry ** 2
    if scale > 1:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    num = rx * rx * ry * ry - rx * rx * yp * yp - ry * ry * xp * xp
    k = math.sqrt(max(0.0, num / (rx * rx * yp * yp + ry * ry * xp * xp)))
    k = -k if large == sweep else k
    cxp, cyp = k * rx * yp / ry, -k * ry * xp / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2
    t1 = math.atan2((yp - cyp) / ry, (xp - cxp) / rx)
    dt = math.atan2((-yp - cyp) / ry, (-xp - cxp) / rx) - t1
    if sweep and dt < 0:
        dt += math.tau
    elif not sweep and dt > 0:
        dt -= math.tau
    out = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        out.append((c * ex - s * ey + cx, s * ex + c * ey + cy))
    return out


def flatten(d, n=12):
    """Parse SVG path data into closed polygons (lists of points)."""
    pos, polys = 0, []
    cur, start, ctrl, cmd, poly = (0.0, 0.0), (0.0, 0.0), None, None, []

    def skip():
        nonlocal pos
        while pos < len(d) and d[pos] in " ,\t\n":
            pos += 1

    def number():
        nonlocal pos
        skip()
        m = NUMBER.match(d, pos)
        pos = m.end()
        return float(m.group())

    def flag():  # arc flags may be packed with no separator: "a1 1 0 00-1 1"
        nonlocal pos
        skip()
        pos += 1
        return d[pos - 1] == "1"

    def bezier(pts):
        t = np.linspace(0, 1, n + 1)[1:, None]
        k = len(pts) - 1
        return [tuple(p) for p in sum(math.comb(k, i) * (1 - t) ** (k - i) * t ** i * np.array(p)
                                      for i, p in enumerate(pts))]

    while True:
        skip()
        if pos >= len(d):
            break
        if d[pos].isalpha():
            cmd = d[pos]
            pos += 1
        elif cmd in "Mm":                              # extra pairs after a move are lines
            cmd = "L" if cmd == "M" else "l"
        rel = cmd.islower()
        ox, oy = cur if rel else (0.0, 0.0)
        op = cmd.upper()
        if op == "Z":
            if poly:
                polys.append(poly)
            poly, cur, ctrl = [], start, None
            continue
        if op == "M":
            if poly:
                polys.append(poly)
            cur = start = (ox + number(), oy + number())
            poly, ctrl = [cur], None
            continue
        if op == "L":
            new = [(ox + number(), oy + number())]
        elif op == "H":
            new = [(ox + number(), cur[1])]
        elif op == "V":
            new = [(cur[0], oy + number())]
        elif op in "CS":
            c1 = (2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if op == "S" and ctrl and ctrl[2] == "C" else cur
            if op == "C":
                c1 = (ox + number(), oy + number())
            c2, end = (ox + number(), oy + number()), (ox + number(), oy + number())
            new = bezier([cur, c1[:2], c2, end])
            ctrl = (*c2, "C")
        elif op in "QT":
            if op == "Q":
                c1 = (ox + number(), oy + number())
            else:
                c1 = (2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if ctrl and ctrl[2] == "Q" else cur
            end = (ox + number(), oy + number())
            new = bezier([cur, c1[:2], end])
            ctrl = (*c1[:2], "Q")
        elif op == "A":
            rx, ry, phi = number(), number(), number()
            large, sweep = flag(), flag()
            end = (ox + number(), oy + number())
            new = arc(cur, rx, ry, phi, large, sweep, end) or [end]
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
        if op not in "CSQT":
            ctrl = None
        poly.extend(new)
        cur = new[-1]
    if poly:
        polys.append(poly)
    return polys


def fill(polys, size, scale, offset):
    """Rasterise polygons with the nonzero winding rule (how browsers fill a path)."""
    wind = np.zeros((size, size + 1))
    rows = np.arange(size) + 0.5
    for poly in polys:
        p = np.asarray(poly) * scale + offset
        for (x0, y0), (x1, y1) in zip(p, np.roll(p, -1, axis=0)):
            if y0 == y1:
                continue
            hit = np.nonzero((rows >= min(y0, y1)) & (rows < max(y0, y1)))[0]
            xs = x0 + (rows[hit] - y0) * (x1 - x0) / (y1 - y0)
            cols = np.clip(np.ceil(xs - 0.5).astype(int), 0, size)
            np.add.at(wind, (hit, cols), 1 if y1 > y0 else -1)
    return np.cumsum(wind, axis=1)[:, :size] != 0


def spread(ys, xs, rng, count):
    """`count` of the given pixels, spread evenly: one random pixel per grid cell."""
    cell = math.sqrt(len(xs) / count)
    while True:                                        # shrink the grid until every point has a cell
        key = (ys // cell).astype(int) * 10000 + (xs // cell).astype(int)
        if len(np.unique(key)) >= count:
            break
        cell *= 0.97
    order = rng.permutation(len(xs))
    _, first = np.unique(key[order], return_index=True)
    picked = order[first][rng.permutation(len(first))[:count]]
    return np.column_stack((xs[picked], ys[picked]))


def logo_points(d, rng, count, outline=0.45):
    """`count` points over a silhouette. A share of them trace its outline: 900 dots spread
    evenly are too sparse to show thin gaps and holes (Python's split, the eyes)."""
    x0, y0, size = LOGO_BOX
    shape = fill(flatten(d), size, (size - 16) / 24, 8)
    img = Image.fromarray(np.uint8(shape * 255))
    inner = np.asarray(img.filter(ImageFilter.MinFilter(5))) > 0
    edge = shape & ~inner
    n_edge = int(count * outline)
    pts = np.vstack((spread(*np.nonzero(edge), rng, n_edge), spread(*np.nonzero(inner), rng, count - n_edge)))
    return pts.astype(float) + (x0, y0)


def transport(source, target):
    """Reorder target so each source point travels to its nearest free slot (min total distance)."""
    rows, cols = linear_sum_assignment(cdist(source, target, "sqeuclidean"))
    out = np.empty_like(target)
    out[rows] = target[cols]
    return out


# ---- SVG

def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".") if v % 1 else f"{v:.0f}"


def dots_path(bits, x0, y0):
    """One-unit dots as horizontal stroke runs: M x y h len, merging neighbours."""
    d = []
    for y in range(bits.shape[0]):
        row = np.flatnonzero(np.diff(np.concatenate(([0], bits[y].astype(np.int8), [0]))))
        for start, stop in zip(row[::2], row[1::2]):
            d.append(f"M{x0 + start} {y0 + y}h{stop - start}")
    return "".join(d)


def text(x, y, s, size, fill, anchor="start", weight=400, extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    w = f' font-weight="{weight}"' if weight != 400 else ""
    return f'<text x="{num(x)}" y="{num(y)}" font-size="{size}" fill="{fill}"{a}{w}{extra}>{escape(s)}</text>'


def render(bits, t, handle, rng):
    ys, xs = np.nonzero(bits)
    portrait = np.column_stack((MAP_X + xs, MAP_Y + ys)).astype(float)

    # travellers: portrait dots that become each logo in turn, matched by optimal transport
    # so every morph moves dots the shortest total distance
    source = portrait[rng.choice(len(portrait), TRAVELLERS, replace=False)]
    stops = [source]
    for d in LOGOS.values():
        stops.append(transport(stops[-1], logo_points(d, rng, TRAVELLERS)))
    first_logo = stops[1]
    # hold, morph, hold, ... and home to the exact start dot so the loop has no seam
    frames = [source, source, stops[1], stops[1], stops[2], stops[2], stops[3], stops[3], source]

    loop = (f'begin="{INTRO}s" dur="{LOOP}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="{";".join(f"{v / LOOP:.4f}".rstrip("0") for v in TIMES)}" '
            f'keySplines="{";".join(["0.45 0 0.25 1"] * (len(TIMES) - 1))}"')

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-labelledby="title desc" font-family="{FONT}">',
         "<title id=\"title\">Snehangshu's live system profile</title>",
         '<desc id="desc">Animated terminal profile: a dithered portrait whose dots fly into '
         'Python, PyTorch and Hugging Face silhouettes and back.</desc>',
         "<defs>",
         '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
         f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".28"/></filter>',
         '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
         f'<feGaussianBlur stdDeviation="3" result="b"/><feFlood flood-color="{t["chrome"]}" flood-opacity=".35"/>'
         '<feComposite in2="b" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
         # scanline reveal: the clip grows top to bottom once (full height if SMIL is off)
         f'<clipPath id="scan"><rect x="{CLIP[0]}" y="{CLIP[1]}" width="{CLIP[2]}" height="{CLIP[3]}" rx="3">'
         f'<animate attributeName="height" from="0" to="{CLIP[3]}" dur="2.2s" fill="freeze" '
         'calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/></rect></clipPath>',
         "</defs>",
         f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
         f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" filter="url(#shadow)"/>',
         f'<path d="M13 62H1167" stroke="{t["line"]}"/>']
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        o.append(f'<circle cx="{38 + 21 * i}" cy="38" r="6" fill="{c}"/>')
    o.append(text(590, 43, "profile.sh --live", 13, t["muted"], "middle", extra=' letter-spacing=".4"'))

    # ---- VISUAL.MAP panel
    o.append(f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>')
    o.append(f'<path d="M35 124H453" stroke="{t["line"]}"/>')
    o.append(text(49, 111, "VISUAL.MAP", 13, t["chrome"], weight=700, extra=' letter-spacing="1.2"'))
    o.append(text(438, 111, f"{MAP_W}×{MAP_H} / 1-BIT", 11, t["muted"], "end"))
    o.append('<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12M439 539h-12M439 539v-12" '
             f'fill="none" stroke="{t["chrome"]}" opacity=".55"/>')
    o.append('<g clip-path="url(#scan)" shape-rendering="crispEdges">')

    # the portrait, cut into bands that drift toward the first logo as they fade out
    o.append(f'<g opacity=".94"><animate attributeName="opacity" {loop} values=".94;.94;0;0;0;0;0;0;.94"/>')
    band = rng.integers(0, BANDS, len(portrait))
    noise = rng.normal(0, 4, (BANDS, 2))
    target = first_logo.mean(0)
    for b in range(BANDS):
        pts = portrait[band == b]
        if not len(pts):
            continue
        dx, dy = (target - pts.mean(0)) * 0.18 + noise[b]
        part = np.zeros_like(bits)
        part[pts[:, 1].astype(int) - MAP_Y, pts[:, 0].astype(int) - MAP_X] = True
        drift = f"{num(dx)} {num(dy)}"
        o.append(f'<path d="{dots_path(part, MAP_X, MAP_Y)}" fill="none" stroke="{t["portrait"]}">'
                 f'<animateTransform attributeName="transform" type="translate" {loop} '
                 f'values="0 0;0 0;{drift};{drift};0 0;0 0;0 0;0 0;0 0"/></path>')
    o.append("</g>")

    # the travellers, hidden until the portrait starts to dissolve
    o.append(f'<g opacity="0" fill="{t["portrait"]}"><animate attributeName="opacity" {loop} values="0;0;1;1;1;1;1;1;0"/>')
    for i in range(TRAVELLERS):
        values = ";".join(f"{num(f[i, 0])} {num(f[i, 1])}" for f in frames)
        o.append(f'<path d="M-.65-.65h1.3v1.3h-1.3z"><animateTransform attributeName="transform" '
                 f'type="translate" {loop} values="{values}"/></path>')
    o.append("</g></g>")
    o.append(text(58, 551, f"PTS {len(portrait):05d} · FS/SERPENTINE", 10, t["muted"]))

    # ---- SYSTEM.INFO panel
    o.append(f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>')
    o.append(f'<path d="M474 124H1146" stroke="{t["line"]}"/>')
    o.append(text(490, 111, "SYSTEM.INFO", 13, t["chrome"], weight=700, extra=' letter-spacing="1.2"'))
    pill_w = len(handle) * 14 * CHAR + 26
    pill_x = 1128 - pill_w
    o.append(f'<rect x="{num(pill_x)}" y="94" width="{num(pill_w)}" height="24" rx="12" fill="{t["chrome"]}" '
             f'fill-opacity=".16" stroke="{t["chrome"]}"/>')
    o.append(text(pill_x + pill_w / 2, 111, handle, 14, t["chrome"], "middle", 700))
    o.append(text(pill_x - 16, 111, "LIVE", 12, t["live"], "end", 700))
    o.append(f'<g filter="url(#glow)"><circle cx="{num(pill_x - 16 - 4 * 12 * CHAR - 12)}" cy="106" r="4" fill="{t["live"]}">'
             '<animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle></g>')

    left, right, size = 491, 1127, 14
    for i, (label, value) in enumerate(ROWS):
        y = 153 + i * 23
        x1 = left + len(label) * size * CHAR + 12
        x2 = right - len(value) * size * CHAR - 12
        leader = "".join(f"M{num(x)} {y - 4}h1" for x in np.arange(x1, x2, 5.0))
        o.append(text(left, y, label, size, t["muted"]))
        o.append(f'<path d="{leader}" fill="none" stroke="{t["line"]}" shape-rendering="crispEdges"/>')
        o.append(text(right, y, value, size, t["text"], "end",
                      extra=f' textLength="{num(len(value) * size * CHAR)}" lengthAdjust="spacingAndGlyphs"'))

    o.append(f'<path d="M490 530H1130" stroke="{t["line"]}"/>')
    o.append(text(491, 548, "● ALL SYSTEMS NOMINAL", 11, t["accent"]))
    o.append(text(1128, 548, "UTC+5:30 · IN NODE", 11, t["muted"], "end"))
    o.append("</svg>")
    return "".join(o)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--photo", default=ROOT / "assets/source/me.png", type=Path)
    p.add_argument("--handle", default="@snehangshu2002")
    args = p.parse_args()
    bits = dither(args.photo)
    for i, (name, theme) in enumerate(THEMES.items()):
        path = ROOT / f"assets/banner-{name}.svg"
        path.write_text(render(bits[name], theme, args.handle, np.random.default_rng(SEED + i)))
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB  {int(bits[name].sum())} pts")


if __name__ == "__main__":
    main()
