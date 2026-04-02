#!/usr/bin/env python3
"""
喜报 / 海报 Generator — v3
Generates festive celebration posters matching the Canva template style:
  - Golden/yellow background with red scalloped-wave border
  - Short, downward-bowing curved arrows
  - Arrow 1 → Application status "Granted"
  - Arrow 2 → Length of stay field

Usage:
  # Visa grant letter poster
  python generate_poster.py \
      --input  path/to/visa_letter.png \
      --output path/to/output.jpg \
      --annotation "五年多次往返" \
      --type visa --month "3月" --year "2026"

  # Chat screenshot poster
  python generate_poster.py \
      --input    path/to/chat.png \
      --output   path/to/output.jpg \
      --annotation "客户希望今天就下签！" \
      --type chat \
      --top-text "目前旅游签证审理严格…"

  # Optional: use a custom watermark image (PNG with transparency)
  python generate_poster.py ... --watermark-image path/to/logo.png
"""

import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFont

# ── Font paths ───────────────────────────────────────────────────────────────────
CHINESE_FONT = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
LATIN_FONT   = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# Badge + 祥云 band PNG assets (relative to this script's directory)
_SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
HE_BADGE_PNG     = os.path.join(_SCRIPT_DIR, "..", "assets", "he_badge.png")
XIANGUYUN_TOP    = os.path.join(_SCRIPT_DIR, "..", "assets", "xianguyun_top.png")
XIANGUYUN_BOT    = os.path.join(_SCRIPT_DIR, "..", "assets", "xianguyun_bot.png")
MEIHUA_PNG       = os.path.join(_SCRIPT_DIR, "..", "assets", "meihua.png")   # optional

# ── Brand colours ────────────────────────────────────────────────────────────────
BG_YELLOW   = (251, 205,   5)   # warm golden yellow (main background)
RED_BORDER  = (195,  20,  20)   # deep red for border and title text
RED_ARROW   = (200,  20,  20)   # red for arrows and annotation
GOLD        = (220, 170,   0)   # dark gold for inner border line
GOLD_LIGHT  = (255, 220,  50)   # lighter gold for badge accents
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
CREAM       = (255, 248, 220)
BG_RED_VISA = (185,  15,  15)   # deep red for new visa poster background
GOLD_BAND   = (218, 168,  12)   # warm gold for decorative wave bands

# ── Canvas ───────────────────────────────────────────────────────────────────────
CANVAS_W   = 1200
CANVAS_H   = 1800
OUTPUT_DPI = 80

# ── Border geometry ──────────────────────────────────────────────────────────────
BORDER_W   = 52   # width of the red border strip
SCALLOP_R  = 16   # radius of each scallop semicircle


# ═══════════════════════════════════════════════════════════════════════════════
# Font / text helpers
# ═══════════════════════════════════════════════════════════════════════════════

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def is_cjk(c):
    cp = ord(c)
    return (0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0xFE30 <= cp <= 0xFE4F or
            0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF)


def _pick_font(char, cjk_f, latin_f):
    return cjk_f if (is_cjk(char) or char in "！？。，、：；\u201c\u201d\u2018\u2019（）【】—·") else latin_f


def render_mixed(draw, text, x, y, size, fill, shadow_fill=None):
    cjk_f   = load_font(CHINESE_FONT, size)
    latin_f = load_font(LATIN_FONT,   size)
    for char in text:
        font = _pick_font(char, cjk_f, latin_f)
        if shadow_fill:
            draw.text((x + 3, y + 3), char, font=font, fill=shadow_fill)
        draw.text((x, y), char, font=font, fill=fill)
        bbox = draw.textbbox((x, y), char, font=font)
        x += bbox[2] - bbox[0]
    return x


def measure_mixed(draw, text, size):
    cjk_f   = load_font(CHINESE_FONT, size)
    latin_f = load_font(LATIN_FONT,   size)
    w = 0
    for char in text:
        bbox = draw.textbbox((0, 0), char, font=_pick_font(char, cjk_f, latin_f))
        w += bbox[2] - bbox[0]
    return w


def draw_centered(draw, text, y, size, fill, canvas_w=CANVAS_W, shadow=False):
    w = measure_mixed(draw, text, size)
    x = (canvas_w - w) // 2
    render_mixed(draw, text, x, y, size, fill,
                 shadow_fill=(100, 0, 0) if shadow else None)


# ═══════════════════════════════════════════════════════════════════════════════
# Border: red with scalloped / cloud-wave inner edge
# ═══════════════════════════════════════════════════════════════════════════════

def draw_wave_border(draw, canvas_w, canvas_h,
                     bg_color=BG_YELLOW,
                     border_fill=None,
                     scallop_fill=None,
                     inner_line_color=None):
    """
    Draws the scalloped wave border.

    Visa poster (default):  red border strip, yellow punch-out scallops, gold inner line
    Chat poster (reversed): yellow border strip, red punch-out scallops, gold inner line

    Args:
        bg_color:        canvas background colour (used as default scallop_fill)
        border_fill:     colour of the solid border strips (default: RED_BORDER)
        scallop_fill:    colour of the punch-out semicircles (default: bg_color)
        inner_line_color: colour of the thin inner rectangle (default: GOLD)
    """
    if border_fill     is None: border_fill      = RED_BORDER
    if scallop_fill    is None: scallop_fill      = bg_color
    if inner_line_color is None: inner_line_color = GOLD

    bw = BORDER_W
    sr = SCALLOP_R

    # ── Solid border strips ──────────────────────────────────────────────────
    draw.rectangle([0, 0, canvas_w - 1, bw - 1],                      fill=border_fill)
    draw.rectangle([0, canvas_h - bw, canvas_w - 1, canvas_h - 1],    fill=border_fill)
    draw.rectangle([0, 0, bw - 1, canvas_h - 1],                      fill=border_fill)
    draw.rectangle([canvas_w - bw, 0, canvas_w - 1, canvas_h - 1],    fill=border_fill)

    # ── Scalloped inner edges (punch-out semicircles) ────────────────────────
    for ix in range(bw, canvas_w - bw, sr * 2):
        draw.ellipse([ix, bw - sr, ix + sr * 2, bw + sr],                 fill=scallop_fill)
    for ix in range(bw, canvas_w - bw, sr * 2):
        cy2 = canvas_h - bw
        draw.ellipse([ix, cy2 - sr, ix + sr * 2, cy2 + sr],               fill=scallop_fill)
    for iy in range(bw, canvas_h - bw, sr * 2):
        draw.ellipse([bw - sr, iy, bw + sr, iy + sr * 2],                 fill=scallop_fill)
    for iy in range(bw, canvas_h - bw, sr * 2):
        cx2 = canvas_w - bw
        draw.ellipse([cx2 - sr, iy, cx2 + sr, iy + sr * 2],               fill=scallop_fill)

    # ── Thin inner line ──────────────────────────────────────────────────────
    margin = bw + sr + 4
    draw.rectangle([margin, margin, canvas_w - margin - 1, canvas_h - margin - 1],
                   outline=inner_line_color, width=3)


# ═══════════════════════════════════════════════════════════════════════════════
# 贺 badge  — red circle with gold starburst rays
# ═══════════════════════════════════════════════════════════════════════════════

def draw_he_badge(draw, canvas_w, badge_x=None, badge_y=None, size=130):
    """
    Ornate medallion-style 贺 badge matching the Canva template.
    Layers (back → front):
      1. Long + short alternating gold rays (24 rays)
      2. Outer gold disc
      3. Rope-like notched ring (small ellipses around edge)
      4. Red main disc
      5. Two concentric gold inner rings
      6. Gold '贺' text
    """
    cx = badge_x if badge_x is not None else canvas_w - 82
    cy = badge_y if badge_y is not None else 82
    r  = size // 2

    GOLD_DARK  = (190, 140,   0)
    GOLD_MID   = (220, 175,  10)
    GOLD_LITE  = (255, 225,  60)
    RED_DEEP   = (170,  10,  10)

    # ── 1. Alternating long / short rays ──────────────────────────────────────
    n_rays = 24
    for i in range(n_rays):
        angle     = 2 * math.pi * i / n_rays - math.pi / 2
        long_ray  = (i % 2 == 0)
        r_inner   = r + 7
        r_outer   = r + (38 if long_ray else 24)
        lw        = 4 if long_ray else 2
        x1 = cx + r_inner * math.cos(angle)
        y1 = cy + r_inner * math.sin(angle)
        x2 = cx + r_outer * math.cos(angle)
        y2 = cy + r_outer * math.sin(angle)
        draw.line([x1, y1, x2, y2], fill=GOLD_LITE, width=lw)

    # ── 2. Outer gold disc ────────────────────────────────────────────────────
    draw.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6],
                 fill=GOLD_MID)

    # ── 3. Rope ring: small circles evenly spaced around edge ─────────────────
    n_dots = 32
    for i in range(n_dots):
        angle = 2 * math.pi * i / n_dots
        dx2   = (r + 2) * math.cos(angle)
        dy2   = (r + 2) * math.sin(angle)
        rr    = 5
        draw.ellipse([cx + dx2 - rr, cy + dy2 - rr,
                      cx + dx2 + rr, cy + dy2 + rr],
                     fill=GOLD_LITE)

    # ── 4. Red main disc ──────────────────────────────────────────────────────
    draw.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2],
                 fill=RED_DEEP)

    # ── 5. Two concentric gold inner rings ────────────────────────────────────
    for offset, lw in [(10, 3), (16, 1)]:
        draw.ellipse([cx - r + offset, cy - r + offset,
                      cx + r - offset, cy + r - offset],
                     outline=GOLD_LITE, width=lw)

    # ── 6. '贺' in gold ───────────────────────────────────────────────────────
    font = load_font(CHINESE_FONT, r - 6)
    bbox = draw.textbbox((0, 0), "贺", font=font)
    bw2  = bbox[2] - bbox[0]
    bh2  = bbox[3] - bbox[1]
    # Shadow
    draw.text((cx - bw2 // 2 + 2, cy - bh2 // 2 + 1), "贺",
              font=font, fill=GOLD_DARK)
    # Main text
    draw.text((cx - bw2 // 2,     cy - bh2 // 2 - 2), "贺",
              font=font, fill=GOLD_LITE)


def paste_he_badge(canvas, badge_size=220, corner_x=None, corner_y=None):
    """
    Composites the 贺 badge PNG asset onto the canvas (top-right corner).
    Handles both RGBA (transparent) and RGB (white-background) source images.
    Falls back to programmatic badge if PNG asset is missing.
    badge_size: target width in pixels.
    """
    badge_path = HE_BADGE_PNG
    if not os.path.isfile(badge_path):
        draw_temp = ImageDraw.Draw(canvas)
        draw_he_badge(draw_temp, canvas.width,
                      badge_x=canvas.width - 82, badge_y=82)
        return canvas

    badge = Image.open(badge_path).convert("RGBA")

    # If the source was RGB (white background), make white pixels transparent
    r, g, b, a = badge.split()
    import numpy as np
    r_np = np.array(r)
    g_np = np.array(g)
    b_np = np.array(b)
    # Pixels where all channels > 230 are considered "white background"
    white_mask = (r_np > 230) & (g_np > 230) & (b_np > 230)
    a_np = np.array(a)
    a_np[white_mask] = 0
    # Also soften near-white edges (anti-aliasing)
    near_white = (r_np > 200) & (g_np > 200) & (b_np > 200) & ~white_mask
    a_np[near_white] = (a_np[near_white] * 0.4).astype(np.uint8)
    badge = Image.merge("RGBA", (r, g, b, Image.fromarray(a_np)))

    # Resize preserving aspect ratio
    bw_orig, bh_orig = badge.size
    bh_new = int(badge_size * bh_orig / bw_orig)
    badge  = badge.resize((badge_size, bh_new), Image.LANCZOS)

    # Top-right corner — badge hangs from corner, slightly outside border
    px = canvas.width - badge_size + 28
    py = -35

    if corner_x is not None: px = corner_x
    if corner_y is not None: py = corner_y

    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(badge, (px, py), badge)
    return canvas_rgba.convert("RGB")


# ═══════════════════════════════════════════════════════════════════════════════
# Curved Bézier arrow — short, bowing DOWNWARD
# ═══════════════════════════════════════════════════════════════════════════════

def _bezier(t, p0, p1, p2, p3):
    u = 1 - t
    return (u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1])


def draw_curved_arrow(draw, start, end,
                      color=RED_ARROW,
                      stroke=12,
                      bow_down_px=70,   # how many px the arc bows DOWNWARD
                      head_len=28,
                      head_spread=0.42):
    """
    Draws a short, thick, downward-bowing curved arrow.
    bow_down_px > 0 always bows the curve toward the bottom of the image,
    regardless of whether the arrow goes left→right or right→left.

    Control-point design guarantees arrowhead points DOWNWARD toward target:
      p1 — 30% along the horizontal axis, pushed DOWN by 1.5 × bow  (arc belly)
      p2 — 80% along the horizontal axis, placed ABOVE endpoint by 0.5 × bow
    Tangent at t=1: 3*(p3-p2) = 3*(dx*0.2, +bow*0.5) → always points in the
    direction of travel AND downward, so the arrowhead faces toward the target. ✓
    """
    sx, sy = float(start[0]), float(start[1])
    ex, ey = float(end[0]),   float(end[1])

    dx = ex - sx   # may be negative (arrow going left)
    dy = ey - sy

    p0 = (sx, sy)
    p1 = (sx + dx * 0.30,  sy + bow_down_px * 1.5)   # belly — bows downward from tail
    p2 = (sx + dx * 0.80,  ey - bow_down_px * 0.5)   # above endpoint → approach from above
    p3 = (ex, ey)

    steps = 80
    pts   = [_bezier(i / steps, p0, p1, p2, p3) for i in range(steps + 1)]

    # Draw thick polyline
    r = stroke // 2
    for i in range(len(pts) - 1):
        draw.line([int(pts[i][0]),   int(pts[i][1]),
                   int(pts[i+1][0]), int(pts[i+1][1])],
                  fill=color, width=stroke)
    # Round end-caps
    for px2, py2 in [(int(pts[0][0]), int(pts[0][1])),
                     (int(pts[-1][0]), int(pts[-1][1]))]:
        draw.ellipse([px2 - r, py2 - r, px2 + r, py2 + r], fill=color)

    # Filled arrowhead at the tip
    tx = pts[-1][0] - pts[-2][0]
    ty = pts[-1][1] - pts[-2][1]
    tl = math.hypot(tx, ty) or 1
    tx, ty = tx / tl, ty / tl
    bx = ex - tx * head_len
    by = ey - ty * head_len
    wing = head_len * math.tan(head_spread)
    draw.polygon([
        (int(ex), int(ey)),
        (int(bx + (-ty) * wing), int(by + tx * wing)),
        (int(bx - (-ty) * wing), int(by - tx * wing)),
    ], fill=color)


# ═══════════════════════════════════════════════════════════════════════════════
# Fireworks decoration
# ═══════════════════════════════════════════════════════════════════════════════

def draw_fireworks(draw, base_x, base_y, dark=False):
    random.seed(42)
    colours = ([(180, 0, 0), (200, 120, 0), (180, 80, 20), (160, 140, 0), (200, 60, 0)]
               if dark else
               [GOLD_LIGHT, (255, 140, 0), (255, 80, 80), (255, 255, 100), (255, 230, 30)])
    bursts  = [(base_x + 40,  base_y - 70,  55, 12),
               (base_x + 95,  base_y - 145, 45, 10),
               (base_x + 155, base_y - 90,  50, 11),
               (base_x + 205, base_y - 165, 40,  9)]
    for idx, (bx, by, radius, n_rays) in enumerate(bursts):
        col = colours[idx % len(colours)]
        for i in range(n_rays):
            angle = 2 * math.pi * i / n_rays
            draw.line([bx, by,
                       bx + int(radius * math.cos(angle)),
                       by + int(radius * math.sin(angle))],
                      fill=col, width=3)
        draw.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=col)
    for _ in range(35):
        bx2 = base_x + random.randint(0, 240)
        by2 = base_y + random.randint(-200, 0)
        r2  = random.randint(3, 8)
        draw.ellipse([bx2 - r2, by2 - r2, bx2 + r2, by2 + r2],
                     fill=colours[random.randint(0, len(colours) - 1)])


# ═══════════════════════════════════════════════════════════════════════════════
# Passport + suitcase icon
# ═══════════════════════════════════════════════════════════════════════════════

def draw_passport_icon(draw, base_x, base_y):
    # Passport book (dark blue)
    px, py, pw, ph = base_x, base_y - 115, 85, 115
    draw.rounded_rectangle([px, py, px + pw, py + ph],
                            radius=10, fill=(30, 50, 120), outline=GOLD, width=3)
    draw.ellipse([px + 22, py + 18, px + 62, py + 58],
                 fill=(30, 50, 120), outline=GOLD, width=3)
    draw.text((px + 31, py + 25), "★", font=load_font(CHINESE_FONT, 22), fill=GOLD)
    draw.text((px + 10, py + 72), "PASSPORT", font=load_font(LATIN_FONT, 13), fill=GOLD)
    # Airplane ticket
    tx, ty = base_x + 55, base_y - 135
    draw.rounded_rectangle([tx, ty, tx + 60, ty + 38],
                            radius=6, fill=(240, 180, 0), outline=GOLD, width=2)
    draw.text((tx + 5, ty + 5), "✈", font=load_font(CHINESE_FONT, 26), fill=WHITE)
    # Suitcase
    sx, sy, sw, sh = base_x + 100, base_y - 90, 70, 80
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh],
                            radius=8, fill=(220, 60, 40), outline=GOLD, width=3)
    draw.rounded_rectangle([sx + 18, sy - 18, sx + 52, sy],
                            radius=5, fill=None, outline=GOLD, width=3)
    draw.line([sx, sy + sh // 2, sx + sw, sy + sh // 2], fill=GOLD, width=3)
    for wx in [sx + 14, sx + sw - 14]:
        draw.ellipse([wx - 8, sy + sh - 8, wx + 8, sy + sh + 8],
                     fill=(30, 30, 30), outline=GOLD, width=2)


# ═══════════════════════════════════════════════════════════════════════════════
# Watermark helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_nl_logo(draw, cx, cy, size, fill):
    """
    Draws the New Legend geometric logo: two overlapping rotated squares
    (diamond shapes) forming the characteristic NL emblem.
    size = half-width of each diamond.
    """
    s = size
    # Outer diamond (rotated square)
    pts_outer = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    draw.polygon(pts_outer, outline=fill, width=max(2, size // 10))
    # Inner diamond (slightly smaller, rotated 45° further = axis-aligned square)
    si = int(s * 0.62)
    pts_inner = [(cx - si, cy - si), (cx + si, cy - si),
                 (cx + si, cy + si), (cx - si, cy + si)]
    draw.polygon(pts_inner, outline=fill, width=max(2, size // 10))
    # Center dot
    cd = max(2, size // 8)
    draw.ellipse([cx - cd, cy - cd, cx + cd, cy + cd], fill=fill)


def _make_watermark_tile(base_w):
    """
    Builds one repeating watermark tile matching the New Legend Canva template:
      Row 1:  [logo]  NEW LEGEND          (large)
      Row 2:          新传奇教育移民        (medium CJK)
      Row 3:  Choose New Legend  Start a legendary life  (small)
    Returns an RGBA Image tile at ~35% opacity, golden colour.
    """
    # --- sizes scale with the base image width ---------------------------------
    tile_w   = int(base_w * 0.52)
    sz_big   = max(22, int(tile_w * 0.115))   # "NEW LEGEND" font size
    sz_cjk   = max(18, int(tile_w * 0.085))   # Chinese font size
    sz_small = max(12, int(tile_w * 0.055))   # tagline font size
    logo_r   = max(10, int(sz_big * 0.55))    # logo diamond half-width
    pad      = max(6,  int(tile_w * 0.025))   # internal padding
    gap      = max(4,  int(tile_w * 0.018))   # row gap

    GOLD_WM  = (195, 140, 10, 255)            # golden colour, fully opaque here

    f_big   = load_font(LATIN_FONT,   sz_big)
    f_cjk   = load_font(CHINESE_FONT, sz_cjk)
    f_small = load_font(LATIN_FONT,   sz_small)

    # Measure text widths
    dummy = Image.new("RGBA", (1, 1))
    dd    = ImageDraw.Draw(dummy)

    def tw(text, font):
        bb = dd.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0], bb[3] - bb[1]

    big_w,   big_h   = tw("NEW LEGEND",              f_big)
    cjk_w,   cjk_h   = tw("新传奇教育移民",             f_cjk)
    tag1_w,  tag1_h  = tw("Choose New Legend",        f_small)
    tag2_w,  tag2_h  = tw("Start a legendary life",   f_small)

    # Row 1: logo + "NEW LEGEND"
    row1_w = logo_r * 2 + pad + big_w
    row1_h = max(logo_r * 2, big_h)

    # Row 2: Chinese text
    row2_h = cjk_h

    # Row 3: two tagline phrases side by side
    tag_gap = max(8, int(tile_w * 0.04))
    row3_w  = tag1_w + tag_gap + tag2_w
    row3_h  = max(tag1_h, tag2_h)

    total_w = max(row1_w, cjk_w, row3_w) + pad * 2
    total_h = row1_h + gap + row2_h + gap + row3_h + pad * 2

    tile = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    td   = ImageDraw.Draw(tile)

    # --- Row 1 ---------------------------------------------------------------
    r1_y  = pad + (row1_h - logo_r * 2) // 2
    logo_cx = pad + logo_r
    logo_cy = pad + row1_h // 2
    _draw_nl_logo(td, logo_cx, logo_cy, logo_r, GOLD_WM)

    txt_y = pad + (row1_h - big_h) // 2
    td.text((pad + logo_r * 2 + pad, txt_y), "NEW LEGEND", font=f_big, fill=GOLD_WM)

    # --- Row 2 ---------------------------------------------------------------
    r2_top = pad + row1_h + gap
    cjk_x  = (total_w - cjk_w) // 2
    td.text((cjk_x, r2_top), "新传奇教育移民", font=f_cjk, fill=GOLD_WM)

    # --- Row 3 ---------------------------------------------------------------
    r3_top  = r2_top + row2_h + gap
    tag_start = (total_w - row3_w) // 2
    td.text((tag_start,             r3_top), "Choose New Legend",      font=f_small, fill=GOLD_WM)
    td.text((tag_start + tag1_w + tag_gap, r3_top), "Start a legendary life", font=f_small, fill=GOLD_WM)

    # Apply global opacity (35%)
    r, g, b, a = tile.split()
    a = a.point(lambda p: int(p * 0.35))
    return Image.merge("RGBA", (r, g, b, a))


def apply_watermark(base_img_rgba, watermark_path=None):
    """
    Tile the New Legend 3-line golden watermark across the image.
    If watermark_path is provided and valid, use that PNG instead
    (legacy override — normally the built-in tile is used).
    """
    w, h = base_img_rgba.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    if watermark_path and os.path.isfile(watermark_path):
        # Custom PNG override (external logo file)
        wm = Image.open(watermark_path).convert("RGBA")
        scale = w * 0.35 / wm.width
        wm_w  = int(wm.width  * scale)
        wm_h  = int(wm.height * scale)
        wm_r  = wm.resize((wm_w, wm_h), Image.LANCZOS)
        r2, g2, b2, a2 = wm_r.split()
        a2 = a2.point(lambda p: int(p * 0.35))
        wm_r = Image.merge("RGBA", (r2, g2, b2, a2))
        for ty in range(-wm_h, h * 2, wm_h + 40):
            for tx in range(-wm_w, w * 2, wm_w + 40):
                layer.paste(wm_r, (tx, ty), wm_r)
    else:
        # Built-in 3-line New Legend tile
        tile   = _make_watermark_tile(w)
        tile_w = tile.width
        tile_h = tile.height
        # Slight diagonal offset per row for visual interest
        for row, ty in enumerate(range(0, h + tile_h, tile_h + 20)):
            offset_x = (row % 2) * (tile_w // 2)   # stagger every other row
            for tx in range(-tile_w + offset_x, w + tile_w, tile_w + 30):
                layer.paste(tile, (tx, ty), tile)

    return Image.alpha_composite(base_img_rgba, layer)


# ═══════════════════════════════════════════════════════════════════════════════
# Annotation auto-detect
# ═══════════════════════════════════════════════════════════════════════════════

def determine_annotation(length_of_stay, must_not_arrive, grant_date):
    import re
    stay  = length_of_stay.lower()
    must  = must_not_arrive.lower()
    grant = grant_date.lower()

    def yr(s):
        m = re.search(r'\b(20\d\d)\b', s)
        return int(m.group(1)) if m else None

    diff  = (yr(must) - yr(grant)) if (yr(must) and yr(grant)) else 0
    entry = "多次往返"

    if "12 month" in stay:
        return f"{'五' if diff >= 5 else diff}年{entry}"
    if "3 month" in stay:
        if diff >= 5: return f"五年{entry}"
        if diff >= 2: return f"{diff}年{entry}"
        if diff == 1: return f"一年{entry}"

    from datetime import datetime
    for fmt in ["%d %B %Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            days = (datetime.strptime(must.strip(), fmt) -
                    datetime.strptime(grant.strip(), fmt)).days
            if days <= 45:
                m = max(1, round(days / 30))
                return f"{'一' if m == 1 else str(m)}个月的旅游签"
            if days <= 400: return f"一年{entry}"
            return f"{diff}年{entry}"
        except Exception:
            pass
    return "旅游签下签"


# ═══════════════════════════════════════════════════════════════════════════════
# 祥云 decorative band — uses real PNG assets, falls back to programmatic
# ═══════════════════════════════════════════════════════════════════════════════

def _png_band_height(png_path, canvas_w):
    """Return the pixel height the BOTTOM HALF of the band would occupy when scaled to canvas_w."""
    if not os.path.isfile(png_path):
        return 90
    img = Image.open(png_path)
    half_h = img.height // 2          # we only use the bottom half
    return int(half_h * canvas_w / img.width)


def paste_xianguyun_band(canvas, png_path, y_top, canvas_w, scallop_down=True):
    """
    Paste only the BOTTOM HALF of the 祥云 wave-band PNG onto the canvas.

    Why bottom half?
    - xianguyun_top.png: top-half = tiny arches; bottom-half = full circles  → shows circles at poster top
    - xianguyun_bot.png: top-half = full circles; bottom-half = arches facing UP → shows upward arches at poster bottom

    White pixels are made transparent so the red background shows through.
    Falls back to a simple programmatic gold bar if the PNG is missing.
    Returns (modified_canvas, rendered_height_px).
    """
    import numpy as np

    if not os.path.isfile(png_path):
        draw = ImageDraw.Draw(canvas)
        h = 90
        draw.rectangle([0, y_top, canvas_w, y_top + h], fill=GOLD_BAND)
        return canvas, h

    band_full = Image.open(png_path).convert("RGBA")
    # ── Crop to bottom half only ─────────────────────────────────────────────
    bw, bh   = band_full.size
    band     = band_full.crop((0, bh // 2, bw, bh))   # bottom half

    # Make white / near-white background transparent
    r_ch, g_ch, b_ch, a_ch = band.split()
    r_np = np.array(r_ch, dtype=np.uint16)
    g_np = np.array(g_ch, dtype=np.uint16)
    b_np = np.array(b_ch, dtype=np.uint16)
    a_np = np.array(a_ch)
    white_mask = (r_np > 240) & (g_np > 240) & (b_np > 240)
    a_np[white_mask] = 0
    band = Image.merge("RGBA", (r_ch, g_ch, b_ch, Image.fromarray(a_np)))

    # Scale to canvas width (preserving aspect ratio of the cropped half)
    new_w = canvas_w
    new_h = int(band.height * canvas_w / band.width)
    band  = band.resize((new_w, new_h), Image.LANCZOS)

    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(band, (0, y_top), band)
    return canvas_rgba.convert("RGB"), new_h


def draw_gold_wave_band(draw, y_top, band_h, canvas_w,
                        gold=None, bg=None, scallop_down=True):
    """Fallback programmatic gold band (used by chat poster)."""
    if gold is None: gold = GOLD_BAND
    if bg   is None: bg   = BG_RED_VISA
    GOLD_LITE = (255, 215, 50)
    sr = 22
    draw.rectangle([0, y_top, canvas_w, y_top + band_h], fill=gold)
    draw.line([0, y_top + 8, canvas_w, y_top + 8], fill=GOLD_LITE, width=3)
    if scallop_down:
        edge_y = y_top + band_h
        draw.line([0, edge_y - sr*2 - 5, canvas_w, edge_y - sr*2 - 5], fill=GOLD_LITE, width=3)
        for ix in range(0, canvas_w, sr * 2):
            draw.ellipse([ix, edge_y - sr, ix + sr*2, edge_y + sr], fill=bg)
    else:
        edge_y = y_top
        draw.line([0, edge_y + sr*2 + 5, canvas_w, edge_y + sr*2 + 5], fill=GOLD_LITE, width=3)
        for ix in range(0, canvas_w, sr * 2):
            draw.ellipse([ix, edge_y - sr, ix + sr*2, edge_y + sr], fill=bg)


# ═══════════════════════════════════════════════════════════════════════════════
# 梅花 (plum blossom) decoration  — multi-layer 3D style matching Canva
# ═══════════════════════════════════════════════════════════════════════════════

def paste_meihua(canvas, cx, cy, radius=100):
    """
    Composite the 梅花 PNG (if available) or draw a multi-layer programmatic
    flower centred at (cx, cy) with the given radius.
    Uses MEIHUA_PNG asset if present; falls back to programmatic.
    """
    import numpy as np

    if os.path.isfile(MEIHUA_PNG):
        flower = Image.open(MEIHUA_PNG).convert("RGBA")
        # White → transparent
        r_ch, g_ch, b_ch, a_ch = flower.split()
        r_np = np.array(r_ch, dtype=np.uint16)
        g_np = np.array(g_ch, dtype=np.uint16)
        b_np = np.array(b_ch, dtype=np.uint16)
        a_np = np.array(a_ch)
        a_np[(r_np > 240) & (g_np > 240) & (b_np > 240)] = 0
        flower = Image.merge("RGBA", (r_ch, g_ch, b_ch, Image.fromarray(a_np)))
        size = radius * 2
        flower = flower.resize((size, size), Image.LANCZOS)
        canvas_rgba = canvas.convert("RGBA")
        canvas_rgba.paste(flower, (cx - radius, cy - radius), flower)
        return canvas_rgba.convert("RGB")

    # ── Programmatic multi-layer 3D flower ──────────────────────────────────
    draw = ImageDraw.Draw(canvas)
    RED_OUTER  = (210, 22, 22)
    WHITE_EDGE = (255, 255, 255)
    CREAM_PETAL= (245, 215, 155)
    CREAM_CTR  = (245, 220, 165)

    petal_r   = int(radius * 0.46)
    petal_off = int(radius * 0.55)
    border    = max(4, int(petal_r * 0.14))

    # Layer 1 — white border ring behind outer petals
    for i in range(5):
        angle = 2 * math.pi * i / 5 - math.pi / 2
        px = cx + int(petal_off * math.cos(angle))
        py = cy + int(petal_off * math.sin(angle))
        draw.ellipse([px - petal_r - border, py - petal_r - border,
                      px + petal_r + border, py + petal_r + border],
                     fill=WHITE_EDGE)

    # Layer 2 — red outer petals
    for i in range(5):
        angle = 2 * math.pi * i / 5 - math.pi / 2
        px = cx + int(petal_off * math.cos(angle))
        py = cy + int(petal_off * math.sin(angle))
        draw.ellipse([px - petal_r, py - petal_r,
                      px + petal_r, py + petal_r],
                     fill=RED_OUTER)

    # Center cap (covers petal intersections)
    cr = int(radius * 0.30)
    draw.ellipse([cx - cr - border, cy - cr - border,
                  cx + cr + border, cy + cr + border], fill=WHITE_EDGE)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=RED_OUTER)

    # Layer 3 — smaller cream inner petals
    inner_r   = int(radius * 0.27)
    inner_off = int(radius * 0.33)
    for i in range(5):
        angle = 2 * math.pi * i / 5 - math.pi / 2
        px = cx + int(inner_off * math.cos(angle))
        py = cy + int(inner_off * math.sin(angle))
        draw.ellipse([px - inner_r, py - inner_r,
                      px + inner_r, py + inner_r],
                     fill=CREAM_PETAL)

    # Center cream disc + tiny hole
    tiny = int(radius * 0.14)
    draw.ellipse([cx - tiny, cy - tiny, cx + tiny, cy + tiny], fill=CREAM_CTR)
    dot = max(3, int(radius * 0.06))
    draw.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=WHITE_EDGE)

    return canvas


# ═══════════════════════════════════════════════════════════════════════════════
# Diagonal text overlay
# ═══════════════════════════════════════════════════════════════════════════════

def draw_diagonal_text(canvas, text, center_x, center_y,
                       size=33, fill=(210, 20, 20),
                       angle=-15, max_chars_per_line=18):
    """
    Render `text` rotated by `angle` degrees, centered at (center_x, center_y).
    White stroke outline for legibility. Returns modified canvas (RGB).
    """
    cjk_f = load_font(CHINESE_FONT, size)
    dummy = Image.new("RGBA", (2, 2))
    dd    = ImageDraw.Draw(dummy)
    bb    = dd.textbbox((0, 0), "测", font=cjk_f)
    lh    = (bb[3] - bb[1]) + 8

    # Wrap text to max_chars_per_line
    lines, chunk = [], ""
    for char in text:
        chunk += char
        if len(chunk) >= max_chars_per_line or char in "！。；":
            lines.append(chunk.strip())
            chunk = ""
    if chunk.strip():
        lines.append(chunk.strip())

    if not lines:
        return canvas

    max_w = max(dd.textbbox((0, 0), ln, font=cjk_f)[2] for ln in lines)
    pad   = 18
    txt_w = max_w + pad * 2
    txt_h = lh * len(lines) + pad * 2

    txt_img  = Image.new("RGBA", (int(txt_w), int(txt_h)), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    y = pad
    for line in lines:
        lw = txt_draw.textbbox((0, 0), line, font=cjk_f)[2]
        x  = (txt_w - lw) // 2
        # White outline (8 directions)
        for ddx, ddy in [(-3,-3),(3,-3),(-3,3),(3,3),(-3,0),(3,0),(0,-3),(0,3)]:
            txt_draw.text((x + ddx, y + ddy), line, font=cjk_f,
                          fill=(255, 255, 255, 210))
        txt_draw.text((x, y), line, font=cjk_f,
                      fill=(*fill[:3], 255))
        y += lh

    rotated = txt_img.rotate(angle, expand=True, resample=Image.BICUBIC)

    rx = center_x - rotated.width  // 2
    ry = center_y - rotated.height // 2

    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(rotated, (rx, ry), rotated)
    return canvas_rgba.convert("RGB")


# ═══════════════════════════════════════════════════════════════════════════════
# VISA POSTER
# ═══════════════════════════════════════════════════════════════════════════════

def generate_visa_poster(
    input_path, output_path, annotation,
    month="", year="",
    title="澳洲新传奇恭喜客户\n旅游签下签！",
    description="",
    visa_number="",
    story_text="客户有他国旅行记录，找到新传奇帮忙递签，"
               "准备资料时新传奇突出客户稳定的收入以及"
               "多国良好旅行记录的优势，帮全家申请获得"
               "1年多次往返澳洲旅游签证！",
    watermark_path=None,
):
    """
    Generates the 下签喜报 poster matching the '下签喜报 (2)' template series.

    Layout (top → bottom):
      0   – 185:  Gold 祥云 wave band
      195 – 435:  White congratulatory title (3 lines, white on red)
      440 – 580:  Case description text + 梅花 decoration
      585 – 1615: Visa letter (旅游签N overlay, watermark, diagonal story)
      1620– 1800: Gold 祥云 wave band
    """
    W, H = CANVAS_W, CANVAS_H

    # ── Background: deep red ────────────────────────────────────────────────────
    canvas = Image.new("RGB", (W, H), BG_RED_VISA)
    draw   = ImageDraw.Draw(canvas)

    # ── Top 祥云 wave band (PNG-based) ─────────────────────────────────────────
    canvas, TOP_BAND_H = paste_xianguyun_band(canvas, XIANGUYUN_TOP, 0, W, scallop_down=True)
    draw = ImageDraw.Draw(canvas)

    # ── Bottom 祥云 wave band ──────────────────────────────────────────────────
    BOT_BAND_H = _png_band_height(XIANGUYUN_BOT, W)
    BOT_BAND_Y = H - BOT_BAND_H
    canvas, _  = paste_xianguyun_band(canvas, XIANGUYUN_BOT, BOT_BAND_Y, W, scallop_down=False)
    draw = ImageDraw.Draw(canvas)

    # ── White title text (no box, white on red) ────────────────────────────────
    TITLE_Y    = TOP_BAND_H + 14
    TITLE_SIZE = 66
    title_lines = [l.strip() for l in title.split("\\n") if l.strip()]
    if not title_lines:
        title_lines = [l.strip() for l in title.split("\n") if l.strip()]
    # Auto-wrap single long line
    if len(title_lines) == 1 and len(title_lines[0]) > 14:
        raw = title_lines[0]
        title_lines = [raw[i:i+14] for i in range(0, len(raw), 14)]

    cjk_big = load_font(CHINESE_FONT, TITLE_SIZE)
    bb_big  = draw.textbbox((0, 0), "测", font=cjk_big)
    lh_big  = bb_big[3] - bb_big[1] + 8

    TITLE_X = 65   # left-aligned to leave right side clear for 贺 badge
    ty = TITLE_Y
    for line in title_lines[:3]:
        # Dark shadow for depth
        render_mixed(draw, line, TITLE_X + 4, ty + 4, TITLE_SIZE, (100, 0, 0))
        render_mixed(draw, line, TITLE_X,     ty,     TITLE_SIZE, WHITE)
        ty += lh_big

    # ── Case description block ─────────────────────────────────────────────────
    DESC_Y    = ty + 10
    DESC_SIZE = 34
    CREAM_WM  = (255, 238, 185)   # warm cream text on red

    if description:
        desc_lines = [l.strip() for l in description.split("\\n") if l.strip()]
        if not desc_lines:
            desc_lines = [l.strip() for l in description.split("\n") if l.strip()]
    elif month or year:
        desc_lines = [f"（{year}年{month}旅游签下签喜报部分展示）"]
    else:
        desc_lines = []

    cjk_desc = load_font(CHINESE_FONT, DESC_SIZE)
    bb_desc  = draw.textbbox((0, 0), "测", font=cjk_desc)
    lh_desc  = bb_desc[3] - bb_desc[1] + 10

    desc_max_w = W - 80 - 80   # max text width (~1040px, full width minus margins

    def _wrap_desc(text, size, max_w):
        cjk_f = load_font(CHINESE_FONT, size)
        lat_f = load_font(LATIN_FONT,   size)
        lines, line, lw = [], "", 0
        for char in text:
            f  = _pick_font(char, cjk_f, lat_f)
            cw = draw.textbbox((0, 0), char, font=f)[2]
            if lw + cw > max_w and line:
                lines.append(line)
                line, lw = char, cw
            else:
                line += char
                lw   += cw
        if line:
            lines.append(line)
        return lines

    td = DESC_Y
    total_wrapped = 0
    for raw_line in desc_lines[:5]:
        for wrapped in _wrap_desc(raw_line, DESC_SIZE, desc_max_w):
            if total_wrapped >= 5:
                break
            render_mixed(draw, wrapped, 80, td, DESC_SIZE, CREAM_WM)
            td += lh_desc
            total_wrapped += 1

    # ── Visa letter zone ───────────────────────────────────────────────────────
    LETTER_Y1 = max(td + 20, DESC_Y + 100)
    LETTER_Y2 = BOT_BAND_Y - 8
    LETTER_X1 = 52
    LETTER_X2 = W - 52
    zw = LETTER_X2 - LETTER_X1
    zh = LETTER_Y2 - LETTER_Y1

    letter = Image.open(input_path).convert("RGB")
    ar     = letter.width / letter.height
    nw     = zw
    nh     = int(zw / ar)
    if nh > zh:
        nh = zh
        nw = int(zh * ar)
    if nw > zw:
        nw = zw
        nh = int(nw / ar)

    # Apply watermark to letter
    wm_letter = apply_watermark(
        letter.resize((nw, nh), Image.LANCZOS).convert("RGBA"),
        watermark_path=watermark_path,
    ).convert("RGB")

    lx = LETTER_X1 + (zw - nw) // 2
    ly = LETTER_Y1

    canvas.paste(wm_letter, (lx, ly))
    draw = ImageDraw.Draw(canvas)

    # Gold border around letter
    draw.rectangle([lx - 3, ly - 3, lx + nw + 3, ly + nh + 3],
                   outline=GOLD, width=3)

    # ── "旅游签 N" large red overlay on upper portion of letter ────────────────
    # annotation = the overlay label (e.g. "旅游签①", "旅游签2", or custom text)
    # If visa_number is provided, use "旅游签{visa_number}"; else use annotation directly
    if visa_number:
        overlay_text = f"旅游签{visa_number}"
    elif annotation:
        overlay_text = annotation
    else:
        overlay_text = ""

    if overlay_text:
        VN_SIZE = 92
        vnw = measure_mixed(draw, overlay_text, VN_SIZE)
        vnx = lx + (nw - vnw) // 2
        vny = ly + int(nh * 0.10)
        for ddx, ddy in [(-4,-4),(4,-4),(-4,4),(4,4),(-4,0),(4,0),(0,-4),(0,4)]:
            render_mixed(draw, overlay_text, vnx + ddx, vny + ddy, VN_SIZE, WHITE)
        render_mixed(draw, overlay_text, vnx, vny, VN_SIZE, (215, 20, 20))

    # ── Diagonal story text (lower 55–75% of letter) ──────────────────────────
    if story_text:
        story_cx = lx + nw // 2
        story_cy = ly + int(nh * 0.65)
        canvas = draw_diagonal_text(
            canvas, story_text,
            center_x=story_cx, center_y=story_cy,
            size=32, fill=(210, 20, 20),
            angle=-15, max_chars_per_line=18,
        )

    # ── 梅花 flower — overlapping top-right corner of visa letter ──────────────
    flower_r  = 95
    flower_cx = lx + nw - flower_r // 2 + 10    # right edge of letter
    flower_cy = ly + flower_r - 10               # just above/at letter top
    canvas = paste_meihua(canvas, flower_cx, flower_cy, radius=flower_r)

    # ── Fireworks decoration (lower-left of canvas, on bottom band) ────────────
    draw = ImageDraw.Draw(canvas)
    draw_fireworks(draw, 15, H - 15, dark=True)

    # ── 贺 badge — in the right side of the red area (below top wave band) ─────
    badge_size = 320
    badge_cx = W - badge_size + 35          # slightly off right edge (natural overflow)
    badge_cy = TOP_BAND_H - 45              # overlaps bottom 45px of wave band
    canvas = paste_he_badge(canvas, badge_size=badge_size,
                            corner_x=badge_cx, corner_y=badge_cy)

    canvas.save(output_path, "JPEG", quality=88, dpi=(OUTPUT_DPI, OUTPUT_DPI))
    print(f"✅  Visa poster → {output_path}  ({W}×{H} @ {OUTPUT_DPI} DPI)")


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT POSTER  — red background, yellow scallop border (Canva template style)
# ═══════════════════════════════════════════════════════════════════════════════

BG_RED = (185, 18, 18)   # deep red background for chat poster


def _draw_cartoon_figure(draw, bx, by, size=160):
    """
    Draws a simple cartoon traveller (circle head, body, luggage) in warm tones
    to approximate the Canva illustration.  bx, by = bottom-left anchor.
    """
    s = size
    # ── Suitcase ──────────────────────────────────────────────────────────────
    sw, sh = int(s * 0.38), int(s * 0.42)
    sx, sy = bx + int(s * 0.54), by - sh
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh],
                            radius=7, fill=(230, 190, 60), outline=WHITE, width=2)
    draw.line([sx, sy + sh // 2, sx + sw, sy + sh // 2], fill=WHITE, width=2)
    draw.rounded_rectangle([sx + sw // 2 - 8, sy - 12, sx + sw // 2 + 8, sy],
                            radius=4, fill=None, outline=WHITE, width=2)
    for wx in [sx + 10, sx + sw - 10]:
        draw.ellipse([wx - 5, sy + sh - 4, wx + 5, sy + sh + 6],
                     fill=(60, 60, 60), outline=WHITE, width=1)
    # ── Body ──────────────────────────────────────────────────────────────────
    bdy_x, bdy_y = bx + int(s * 0.12), by - int(s * 0.72)
    bdy_w, bdy_h = int(s * 0.32), int(s * 0.38)
    draw.rounded_rectangle([bdy_x, bdy_y, bdy_x + bdy_w, bdy_y + bdy_h],
                            radius=10, fill=(255, 160, 80), outline=WHITE, width=2)
    # ── Head ──────────────────────────────────────────────────────────────────
    hcx = bdy_x + bdy_w // 2
    hcy = bdy_y - int(s * 0.14)
    hr  = int(s * 0.13)
    draw.ellipse([hcx - hr, hcy - hr, hcx + hr, hcy + hr],
                 fill=(255, 210, 160), outline=WHITE, width=2)
    # simple eyes + smile
    draw.ellipse([hcx - 6, hcy - 4, hcx - 2, hcy],     fill=(60, 40, 20))
    draw.ellipse([hcx + 2, hcy - 4, hcx + 6, hcy],     fill=(60, 40, 20))
    draw.arc([hcx - 6, hcy + 1, hcx + 6, hcy + 9],     start=10, end=170,
             fill=(180, 80, 40), width=2)
    # ── Arm holding suitcase ──────────────────────────────────────────────────
    draw.line([bdy_x + bdy_w - 4, bdy_y + int(bdy_h * 0.3),
               sx + 4,            sy + 8],
              fill=(255, 160, 80), width=6)


def generate_chat_poster(
    input_path, output_path, annotation,
    top_text="", month="", year="",
    watermark_path=None,
):
    # ── Canvas: RED background ───────────────────────────────────────────────────
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_RED)
    draw   = ImageDraw.Draw(canvas)

    # Reversed border: YELLOW fill strips, RED punch-out scallops, GOLD inner line
    # (no white lines — inner line colour is GOLD not WHITE)
    draw_wave_border(draw, CANVAS_W, CANVAS_H,
                     bg_color=BG_RED,
                     border_fill=BG_YELLOW,
                     scallop_fill=BG_RED,
                     inner_line_color=GOLD)

    inner_margin = BORDER_W + SCALLOP_R + 10   # 78 px

    # ── Top advisory text block (cream box, bold & large) ────────────────────────
    FONT_SIZE = 54          # larger — matches template prominence
    LINE_GAP  = 14
    PAD_X, PAD_Y = 32, 22
    # Text wraps to ~17 chars wide (leaves room for cartoon figure on right)
    avail_text_w = int((CANVAS_W - inner_margin * 2) * 0.72) - PAD_X * 2

    cjk_f    = load_font(CHINESE_FONT, FONT_SIZE)
    latin_f  = load_font(LATIN_FONT,   FONT_SIZE)
    bbox_ref = draw.textbbox((0, 0), "测", font=cjk_f)
    line_h   = bbox_ref[3] - bbox_ref[1]

    lines, current, current_w = [], "", 0
    for char in top_text:
        f  = _pick_font(char, cjk_f, latin_f)
        cw = draw.textbbox((0, 0), char, font=f)[2]
        if current_w + cw > avail_text_w and current:
            lines.append(current)
            current, current_w = char, cw
        else:
            current += char
            current_w += cw
    if current:
        lines.append(current)
    lines = lines[:5]

    box_h = len(lines) * line_h + (len(lines) - 1) * LINE_GAP + PAD_Y * 2
    # Ensure box is tall enough for the cartoon figure overlap
    box_h = max(box_h, 220)

    tb_x1 = inner_margin
    tb_y1 = inner_margin + 8
    tb_x2 = CANVAS_W - inner_margin
    tb_y2 = tb_y1 + box_h

    draw.rounded_rectangle([tb_x1, tb_y1, tb_x2, tb_y2],
                            radius=16, fill=BG_YELLOW, outline=WHITE, width=3)
    ty = tb_y1 + PAD_Y
    for line in lines:
        render_mixed(draw, line, tb_x1 + PAD_X, ty, FONT_SIZE, BLACK)
        ty += line_h + LINE_GAP

    # ── Cartoon figure in top-right of yellow box ────────────────────────────────
    fig_size = 200
    fig_bx   = tb_x2 - fig_size - 5
    fig_by   = tb_y2 - 10
    _draw_cartoon_figure(draw, fig_bx, fig_by, size=fig_size)

    # ── Chat screenshot — fills most of the remaining height ─────────────────────
    CHAT_GAP = 14
    chat_y1  = tb_y2 + CHAT_GAP
    chat_y2  = CANVAS_H - inner_margin - 100   # leave just enough room for fireworks
    zw       = CANVAS_W - inner_margin * 2
    zh       = chat_y2 - chat_y1

    chat = Image.open(input_path).convert("RGB")
    ar   = chat.width / chat.height
    nw   = zw
    nh   = int(zw / ar)
    if nh > zh:
        nh = zh
        nw = int(zh * ar)
    if nw > zw:
        nw = zw
        nh = int(zw / ar)

    cx = inner_margin + (zw - nw) // 2
    cy = chat_y1

    # Apply watermark to chat screenshot
    wm_chat = apply_watermark(
        chat.resize((nw, nh), Image.LANCZOS).convert("RGBA"),
        watermark_path=watermark_path,
    ).convert("RGB")
    canvas.paste(wm_chat, (cx, cy))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([cx - 3, cy - 3, cx + nw + 3, cy + nh + 3],
                   outline=GOLD, width=3)

    # ── Annotation text: OVERLAID on the chat screenshot ────────────────────────
    # Matches reference: large RED text in middle portion of chat image
    anno_size  = 58
    avail_anno = nw - 30

    anno_lines, remaining = [], annotation
    while remaining:
        for cut in range(len(remaining), 0, -1):
            if measure_mixed(draw, remaining[:cut], anno_size) <= avail_anno:
                anno_lines.append(remaining[:cut])
                remaining = remaining[cut:]
                break
        else:
            anno_lines.append(remaining[0])
            remaining = remaining[1:]
    anno_lines = anno_lines[:3]

    cjk_fa = load_font(CHINESE_FONT, anno_size)
    bb_a   = draw.textbbox((0, 0), "测", font=cjk_fa)
    lh_a   = bb_a[3] - bb_a[1] + 8

    # Place at ~42% from top of the chat screenshot
    ay = cy + int(nh * 0.42) - (len(anno_lines) * lh_a) // 2
    ax = cx + 15

    for line in anno_lines:
        # Bold white stroke outline (4 directions) for legibility over chat
        for ddx, ddy in [(-3, -3), (3, -3), (-3, 3), (3, 3),
                          (-3, 0), (3, 0), (0, -3), (0, 3)]:
            render_mixed(draw, line, ax + ddx, ay + ddy, anno_size, WHITE)
        render_mixed(draw, line, ax, ay, anno_size, RED_ARROW)
        ay += lh_a

    # ── Two arrows: from annotation area pointing DOWN to PDF attachment ─────────
    # PDF attachments typically appear in the lower ~65-75% of a WeChat chat
    pdf_y = cy + int(nh * 0.72)
    pdf_x = cx + int(nw * 0.62)

    anno_bottom_y = cy + int(nh * 0.42) + len(anno_lines) * lh_a // 2 + 20

    draw_curved_arrow(draw,
                      start=(cx + int(nw * 0.38), anno_bottom_y),
                      end  =(pdf_x - int(nw * 0.08), pdf_y),
                      color=RED_ARROW, stroke=11, bow_down_px=55)

    draw_curved_arrow(draw,
                      start=(cx + int(nw * 0.58), anno_bottom_y),
                      end  =(pdf_x + int(nw * 0.05), pdf_y - int(nh * 0.04)),
                      color=RED_ARROW, stroke=11, bow_down_px=45)

    # ── Decorations ──────────────────────────────────────────────────────────────
    draw_fireworks(draw, inner_margin, CANVAS_H - 45, dark=False)
    # Paste 贺 badge PNG over the top-right corner
    canvas = paste_he_badge(canvas, badge_size=210)

    canvas.save(output_path, "JPEG", quality=88, dpi=(OUTPUT_DPI, OUTPUT_DPI))
    print(f"✅  Chat poster → {output_path}  ({CANVAS_W}×{CANVAS_H} @ {OUTPUT_DPI} DPI)")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Generate 喜报 / 海报 poster")
    p.add_argument("--input",            required=True)
    p.add_argument("--output",           required=True)
    p.add_argument("--annotation",       default="",
                   help="Visa poster: overlay text (e.g. '旅游签①'); Chat: quote annotation")
    p.add_argument("--type",             choices=["visa", "chat"], default="visa")
    p.add_argument("--month",            default="")
    p.add_argument("--year",             default="")
    p.add_argument("--title",
                   default="澳洲新传奇恭喜客户\\n旅游签下签！",
                   help="Visa poster title lines (use \\\\n to separate lines)")
    p.add_argument("--description",      default="",
                   help="Visa poster case details (use \\\\n between lines)")
    p.add_argument("--visa-number",      default="",
                   help="Visa poster: family member number shown as '旅游签N' (e.g. '①')")
    p.add_argument("--story-text",
                   default="客户有他国旅行记录，找到新传奇帮忙递签，"
                           "准备资料时新传奇突出客户稳定的收入以及"
                           "多国良好旅行记录的优势，帮全家申请获得"
                           "1年多次往返澳洲旅游签证！",
                   help="Visa poster: diagonal story text overlaid on letter")
    p.add_argument("--top-text",         default="")
    p.add_argument("--watermark-image",  default=None,
                   help="Path to a PNG logo (with transparency) to use as watermark")
    a = p.parse_args()

    if not os.path.isfile(a.input):
        print(f"❌  Input not found: {a.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)

    if a.type == "visa":
        generate_visa_poster(
            a.input, a.output, a.annotation,
            month=a.month, year=a.year,
            title=a.title,
            description=a.description,
            visa_number=a.visa_number,
            story_text=a.story_text,
            watermark_path=a.watermark_image,
        )
    else:
        generate_chat_poster(
            a.input, a.output, a.annotation,
            top_text=a.top_text, month=a.month, year=a.year,
            watermark_path=a.watermark_image,
        )


if __name__ == "__main__":
    main()