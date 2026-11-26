#!/usr/bin/env python3
"""Draw the 26 November 2026 world-news front page as a 1024x1024 PNG.

Editorial infographic: a masthead naming the day, then four story panels in a
2x2 grid. Every panel has a hand-drawn pictogram, a headline and a one-line
caption, all rendered with PIL and the DejaVu fonts, so no letter is ever
garbled. The program takes no input, uses no network and no clock: running it
twice writes identical bytes.

Stories (all happened or first reported on Thursday 26 November 2026):
  1. Kim Jong Un orders a wider tactical-nuclear deployment (KCNA, Thursday).
  2. Taiwan says it will keep its agreed 15% US tariff rate (Reuters, Thursday).
  3. Thanksgiving Day in the United States.
  4. World Chess Championship game 3 in Geneva, match level 1-1.

Usage: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Output: <MAKEFUN_OUTPUT_DIR>/entry.png (or ./entry.png when unset).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 243, 234)
INK = (17, 24, 39)
RED = (178, 34, 34)
NAVY = (15, 27, 45)
GOLD = (184, 134, 11)
GREY = (90, 96, 108)
CARD = (255, 255, 255)
LINE = (205, 200, 188)
BROWN = (139, 90, 43)
ORANGE = (232, 126, 32)
GREEN = (46, 110, 60)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def rotated_ellipse_points(cx, cy, rx, ry, deg, steps=24):
    """Points of an ellipse centred on (cx, cy), rotated by deg degrees."""
    rad = math.radians(deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        pts.append((cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a))
    return pts


def starburst(draw, cx, cy, r, color):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def icon_missile(draw, x, y, s):
    """A missile climbing past a burst, on a navy sky panel."""
    draw.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=NAVY)
    for dx, dy in [(0.18, 0.16), (0.82, 0.22), (0.35, 0.1), (0.68, 0.34)]:
        draw.ellipse([x + dx * s - 2, y + dy * s - 2, x + dx * s + 2, y + dy * s + 2],
                     fill=(250, 220, 140))
    bx = x + s * 0.5
    # flame
    draw.polygon([(bx - s * 0.07, y + s * 0.82), (bx + s * 0.07, y + s * 0.82),
                  (bx, y + s * 0.98)], fill=ORANGE)
    # body
    draw.rounded_rectangle([bx - s * 0.09, y + s * 0.3, bx + s * 0.09, y + s * 0.82],
                           radius=6, fill=(240, 240, 235))
    draw.polygon([(bx - s * 0.09, y + s * 0.3), (bx + s * 0.09, y + s * 0.3),
                  (bx, y + s * 0.14)], fill=RED)
    draw.rectangle([bx - s * 0.09, y + s * 0.58, bx + s * 0.09, y + s * 0.64],
                   fill=RED)
    # fins
    draw.polygon([(bx - s * 0.09, y + s * 0.7), (bx - s * 0.22, y + s * 0.86),
                  (bx - s * 0.09, y + s * 0.84)], fill=RED)
    draw.polygon([(bx + s * 0.09, y + s * 0.7), (bx + s * 0.22, y + s * 0.86),
                  (bx + s * 0.09, y + s * 0.84)], fill=RED)
    starburst(draw, x + s * 0.78, y + s * 0.2, s * 0.13, GOLD)


def icon_tariff(draw, x, y, s):
    """Rising bars with a red 15% badge."""
    draw.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=(245, 240, 230))
    draw.line([(x + s * 0.1, y + s * 0.9), (x + s * 0.1, y + s * 0.12)],
              fill=GREY, width=3)
    draw.line([(x + s * 0.1, y + s * 0.9), (x + s * 0.92, y + s * 0.9)],
              fill=GREY, width=3)
    bars = [(0.18, 0.38, NAVY), (0.4, 0.52, GOLD), (0.62, 0.66, RED)]
    for bx, bh, col in bars:
        draw.rectangle([x + bx * s, y + (0.9 - bh) * s, x + (bx + 0.15) * s,
                        y + s * 0.9], fill=col)
    draw.ellipse([x + s * 0.56, y + s * 0.02, x + s * 1.0, y + s * 0.46],
                 fill=RED, outline=(255, 255, 255), width=3)
    draw.text((x + s * 0.78, y + s * 0.24), "15%", font=font(FB, 22),
              fill=(255, 255, 255), anchor="mm")


def icon_turkey(draw, x, y, s):
    """A stylised turkey: fanned tail feathers behind a brown body."""
    draw.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=(245, 240, 230))
    cx, cy = x + s * 0.5, y + s * 0.62
    for deg, col in [(-55, BROWN), (-28, (166, 110, 52)), (0, GOLD),
                     (28, (166, 110, 52)), (55, BROWN)]:
        pts = rotated_ellipse_points(cx, cy - s * 0.16, s * 0.075, s * 0.26, deg)
        draw.polygon(pts, fill=col, outline=(120, 76, 34))
    draw.ellipse([cx - s * 0.2, cy - s * 0.16, cx + s * 0.2, cy + s * 0.24],
                 fill=BROWN, outline=(90, 58, 26), width=2)
    # wing
    draw.ellipse([cx - s * 0.14, cy - s * 0.06, cx + s * 0.02, cy + s * 0.16],
                 fill=(120, 76, 34))
    # head and beak
    hx, hy = cx + s * 0.14, cy - s * 0.2
    draw.ellipse([hx - s * 0.07, hy - s * 0.07, hx + s * 0.07, hy + s * 0.07],
                 fill=BROWN)
    draw.polygon([(hx + s * 0.05, hy - s * 0.01), (hx + s * 0.14, hy + s * 0.02),
                  (hx + s * 0.05, hy + s * 0.05)], fill=ORANGE)
    draw.ellipse([hx + s * 0.015, hy + s * 0.02, hx + s * 0.05, hy + s * 0.1],
                 fill=RED)
    draw.ellipse([hx + s * 0.02, hy - s * 0.03, hx + s * 0.045, hy - s * 0.005],
                 fill=INK)


def icon_chess(draw, x, y, s):
    """A 4x4 board with a gold king standing on it."""
    draw.rounded_rectangle([x, y, x + s, y + s], radius=8, fill=(245, 240, 230))
    cell = s * 0.17
    ox, oy = x + s * 0.16, y + s * 0.3
    for r in range(4):
        for c in range(4):
            col = NAVY if (r + c) % 2 == 0 else (255, 255, 255)
            draw.rectangle([ox + c * cell, oy + r * cell,
                            ox + (c + 1) * cell, oy + (r + 1) * cell],
                           fill=col, outline=LINE)
    # king on the second row, third column
    kx = ox + 2 * cell + cell / 2
    ky = oy + 1 * cell + cell / 2
    draw.line([(kx, ky - cell * 0.42), (kx, ky + cell * 0.42)], fill=GOLD, width=4)
    draw.line([(kx - cell * 0.2, ky - cell * 0.32),
               (kx + cell * 0.2, ky - cell * 0.32)], fill=GOLD, width=4)
    draw.polygon([(kx - cell * 0.3, ky - cell * 0.18),
                  (kx + cell * 0.3, ky - cell * 0.18),
                  (kx + cell * 0.18, ky + cell * 0.28),
                  (kx - cell * 0.18, ky + cell * 0.28)], fill=GOLD,
                 outline=INK)
    draw.rectangle([kx - cell * 0.34, ky + cell * 0.28, kx + cell * 0.34,
                    ky + cell * 0.42], fill=GOLD, outline=INK)
    draw.text((x + s * 0.5, y + s * 0.06), "1 - 1", font=font(FB, 24),
              fill=INK, anchor="ma")


PANELS = [
    dict(kicker="PYONGYANG  •  SECURITY", color=RED,
         head="KIM ORDERS NUCLEAR BUILD-UP",
         cap="Kim Jong Un orders North Korea to spread tactical nuclear arms.",
         src="Sources: Reuters, KCNA",
         icon=icon_missile),
    dict(kicker="TAIPEI  •  TRADE", color=NAVY,
         head="TAIWAN HOLDS ITS 15% TARIFF",
         cap="Taipei says its US deal survives Trump's tariff salvo.",
         src="Sources: Reuters",
         icon=icon_tariff),
    dict(kicker="UNITED STATES  •  THANKSGIVING", color=(139, 90, 43),
         head="AMERICA MARKS THANKSGIVING",
         cap="Families gather for the holiday as markets close for the day.",
         src="Sources: Reuters",
         icon=icon_turkey),
    dict(kicker="GENEVA  •  CHESS", color=GREEN,
         head="TITLE FIGHT RESUMES",
         cap="Gukesh and Sindarov level 1-1 as game 3 begins in Geneva.",
         src="Sources: FIDE, Reuters",
         icon=icon_chess),
]


def draw_card(draw, x, y, pw, ph, p):
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=10, fill=CARD,
                           outline=LINE, width=2)
    draw.rounded_rectangle([x, y, x + pw, y + 10], radius=5, fill=p["color"])
    draw.rectangle([x, y + 5, x + pw, y + 10], fill=p["color"])
    draw.text((x + 20, y + 26), p["kicker"], font=font(FB, 21), fill=p["color"])
    lines = wrap_text(draw, p["head"], font(FB, 38), pw - 40)
    ty = y + 60
    for ln in lines[:2]:
        draw.text((x + 20, ty), ln, font=font(FB, 38), fill=INK)
        ty += 45
    p["icon"](draw, x + 20, y + 158, 118)
    cap_lines = wrap_text(draw, p["cap"], font(FR, 24), pw - 168)
    cy = y + 168
    for ln in cap_lines[:3]:
        draw.text((x + 158, cy), ln, font=font(FR, 24), fill=(52, 58, 70))
        cy += 31
    draw.line([(x + 20, y + ph - 44), (x + pw - 20, y + ph - 44)], fill=LINE, width=2)
    draw.text((x + 20, y + ph - 34), p["src"], font=font(FR, 19), fill=GREY)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    # masthead
    draw.text((36, 34), "T H E   W O R L D   I N   O N E   D A Y",
              font=font(FB, 26), fill=RED)
    draw.text((36, 66), "26 NOVEMBER 2026", font=font(FB, 78), fill=INK)
    draw.text((36, 156), "Thursday  •  Four stories that defined the day",
              font=font(FR, 27), fill=GREY)
    draw.line([(36, 196), (988, 196)], fill=INK, width=3)
    # grid
    gx, gy, gap = 36, 214, 20
    pw, ph = (W - 2 * gx - gap) // 2, 356
    for i, p in enumerate(PANELS):
        x = gx + (i % 2) * (pw + gap)
        y = gy + (i // 2) * (ph + gap)
        draw_card(draw, x, y, pw, ph, p)
    # footer
    draw.line([(36, 966), (988, 966)], fill=LINE, width=2)
    draw.text((512, 976), "make.fun  •  one day, one picture  •  26 November 2026",
              font=font(FR, 22), fill=GREY, anchor="ma")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img.save(out_path, optimize=True)
    print("saved", out_path, img.size)


if __name__ == "__main__":
    main()
