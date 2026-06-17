"""
Gera a capa/title-card do projeto SENTINELA ORBITAL (1920x1080).

Visual "mission control" alinhado ao dashboard: fundo espacial escuro,
glows teal/violeta, starfield, limbo da Terra com atmosfera, satelite em
orbita, focos de queimada reais (laranja) e o titulo do projeto.

Saida: assets/capa_sentinela_orbital.png

Executar:
    python scripts/gerar_capa.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "capa_sentinela_orbital.png"

W, H = 1920, 1080

# paleta do dashboard
BG = (6, 9, 18)
TXT = (234, 241, 251)
TXT2 = (126, 139, 163)
ACCENT = (56, 225, 217)     # teal
VIOLET = (124, 140, 255)
FIRE = (251, 146, 60)


# ---------------------------------------------------------------------------
# fontes (Windows) com fallback
# ---------------------------------------------------------------------------
def load_font(names, size):
    fdir = Path("C:/Windows/Fonts")
    for n in names:
        p = fdir / n
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()


F_TITLE = load_font(["bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf"], 168)
F_SUB = load_font(["segoeui.ttf", "arial.ttf"], 40)
F_KICK = load_font(["consola.ttf", "cour.ttf"], 26)
F_FOOT = load_font(["consola.ttf", "cour.ttf"], 26)


# ---------------------------------------------------------------------------
# fundo (numpy): glows radiais + starfield + limbo da Terra
# ---------------------------------------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(float)
arr = np.zeros((H, W, 3), float)
arr[:] = BG


def add_glow(cx, cy, rad, color, strength):
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    a = np.clip(1 - d / rad, 0, 1) ** 2 * strength
    for i, c in enumerate(color):
        arr[..., i] += a * c


add_glow(W * 0.08, -H * 0.08, 1250, ACCENT, 0.16)
add_glow(W * 1.04, H * 1.12, 1400, VIOLET, 0.15)
add_glow(W * 0.5, H * 1.55, 900, ACCENT, 0.10)

# starfield
rng = np.random.default_rng(7)
n = 560
sx = rng.integers(0, W, n)
sy = rng.integers(0, int(H * 0.92), n)
sb = rng.random(n) ** 2.2
for i in range(n):
    b = 90 + sb[i] * 165
    arr[sy[i], sx[i]] += (b, b, b)

# limbo da Terra: esfera grande quase toda abaixo do quadro
gcx, gcy, gr = W * 0.5, H * 1.98, H * 1.33
d = np.sqrt((xx - gcx) ** 2 + (yy - gcy) ** 2)
surf = d < gr
atmo = (d >= gr) & (d < gr + 90)

# textura de continentes (ruido low-freq)
noise = np.array(
    Image.fromarray((rng.random((54, 96)) * 255).astype("uint8")).resize((W, H), Image.BICUBIC)
) / 255.0
ocean = np.array((10, 24, 40), float)
land = np.array((22, 74, 58), float)
shade = np.clip((gcy - yy) / (gr * 0.6), 0, 1)[..., None]  # mais claro perto do topo
landmask = surf & (noise > 0.56)
arr[surf] = (ocean * (0.45 + 0.55 * shade))[surf]
arr[landmask] = (land * (0.5 + 0.5 * shade))[landmask]

# atmosfera (rim teal) acima da superficie
rim = np.exp(-((d - gr) / 46.0) ** 2)
for i, c in enumerate(ACCENT):
    arr[..., i] += np.where(atmo | (np.abs(d - gr) < 70), rim * c * 0.9, 0)

arr = np.clip(arr, 0, 255).astype("uint8")
img = Image.fromarray(arr, "RGB")

# grade de meridianos/paralelos sutil sobre o globo
glayer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glayer)
for k in range(-4, 5):
    rr = gr + k * 95
    gd.ellipse([gcx - rr, gcy - rr, gcx + rr, gcy + rr], outline=(56, 225, 217, 26), width=2)
for ang in range(0, 180, 15):
    a = math.radians(ang)
    gd.line([gcx - math.cos(a) * gr * 1.4, gcy - math.sin(a) * gr * 1.4,
             gcx + math.cos(a) * gr * 1.4, gcy + math.sin(a) * gr * 1.4],
            fill=(56, 225, 217, 14), width=2)
gmask = Image.fromarray((surf * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1))
img.paste(Image.alpha_composite(img.convert("RGBA"), glayer).convert("RGB"), (0, 0), gmask)


# ---------------------------------------------------------------------------
# overlay vetorial: orbita + satelite + focos + textos + molduras
# ---------------------------------------------------------------------------
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dr = ImageDraw.Draw(ov)


def tracked_width(text, font, tracking):
    return sum(font.getlength(c) for c in text) + tracking * (len(text) - 1)


def draw_tracked(draw, x, y, text, font, fill, tracking, stroke_width=0, stroke_fill=None):
    cx = x
    for c in text:
        draw.text((cx, y), c, font=font, fill=fill,
                  stroke_width=stroke_width, stroke_fill=stroke_fill)
        cx += font.getlength(c) + tracking


# orbita eliptica tracejada
ob = [W * 0.16, H * 0.06, W * 0.84, H * 0.78]
ocx, ocy = (ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2
oa, obb = (ob[2] - ob[0]) / 2, (ob[3] - ob[1]) / 2
seg = 240
prev = None
for i in range(seg + 1):
    t = i / seg * 2 * math.pi
    px = ocx + math.cos(t) * oa
    py = ocy + math.sin(t) * obb
    if prev and i % 2 == 0:
        dr.line([prev, (px, py)], fill=(56, 225, 217, 55), width=2)
    prev = (px, py)

# satelite sobre a orbita (canto superior direito)
st_t = math.radians(-32)
stx = ocx + math.cos(st_t) * oa
sty = ocy + math.sin(st_t) * obb


def satelite(draw, cx, cy, s, col):
    # paineis solares
    draw.rectangle([cx - 4.2 * s, cy - 1.5 * s, cx - 1.4 * s, cy + 1.5 * s], outline=col, width=3)
    draw.rectangle([cx + 1.4 * s, cy - 1.5 * s, cx + 4.2 * s, cy + 1.5 * s], outline=col, width=3)
    for g in range(1, 3):
        gx1 = cx - 4.2 * s + (2.8 * s) * g / 3
        draw.line([gx1, cy - 1.5 * s, gx1, cy + 1.5 * s], fill=col, width=2)
        gx2 = cx + 1.4 * s + (2.8 * s) * g / 3
        draw.line([gx2, cy - 1.5 * s, gx2, cy + 1.5 * s], fill=col, width=2)
    draw.line([cx - 1.4 * s, cy, cx + 1.4 * s, cy], fill=col, width=3)
    # corpo
    draw.rectangle([cx - 1.3 * s, cy - 1.0 * s, cx + 1.3 * s, cy + 1.0 * s],
                   fill=(15, 22, 38, 255), outline=col, width=3)
    # antena
    draw.line([cx, cy - 1.0 * s, cx, cy - 2.4 * s], fill=col, width=2)
    draw.ellipse([cx - 0.35 * s, cy - 2.8 * s, cx + 0.35 * s, cy - 2.1 * s], outline=col, width=2)


# glow do satelite
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
satelite(ImageDraw.Draw(glow), stx, sty, 22, (56, 225, 217, 255))
ov = Image.alpha_composite(ov, glow.filter(ImageFilter.GaussianBlur(9)))
dr = ImageDraw.Draw(ov)
satelite(dr, stx, sty, 22, (210, 245, 243, 255))

# feixe de sensoriamento ate a Terra
dr.line([stx, sty + 30, gcx + 120, gcy - gr + 60], fill=(56, 225, 217, 40), width=2)
dr.line([stx, sty + 30, gcx - 60, gcy - gr + 30], fill=(56, 225, 217, 40), width=2)

# focos de queimada reais (laranja) sobre o globo visivel
fires = [(0.28, 0.84), (0.43, 0.90), (0.56, 0.83), (0.67, 0.89), (0.76, 0.86), (0.36, 0.94)]
fglow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fdr = ImageDraw.Draw(fglow)
for fxf, fyf in fires:
    px, py = W * fxf, H * fyf
    if py < H - 12:
        fdr.ellipse([px - 13, py - 13, px + 13, py + 13], fill=(251, 146, 60, 235))
ov = Image.alpha_composite(ov, fglow.filter(ImageFilter.GaussianBlur(9)))
dr = ImageDraw.Draw(ov)
for fxf, fyf in fires:
    px, py = W * fxf, H * fyf
    if py < H - 12:
        dr.ellipse([px - 4.5, py - 4.5, px + 4.5, py + 4.5], fill=(255, 224, 188, 255))

# molduras de canto (estilo cards do dashboard)
m, ln = 54, 46
for (ax, ay, dx, dy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
    dr.line([ax, ay, ax + dx * ln, ay], fill=(56, 225, 217, 150), width=3)
    dr.line([ax, ay, ax, ay + dy * ln], fill=(56, 225, 217, 150), width=3)

# kicker topo
kick = "FIAP  ·  SUB GLOBAL SOLUTION 2026.1  ·  INTELIGENCIA ARTIFICIAL"
kw = tracked_width(kick, F_KICK, 6)
draw_tracked(dr, (W - kw) / 2, 120, kick, F_KICK, (56, 225, 217, 235), 6)

# titulo com glow — auto-fit p/ caber na largura com margem
title = "SENTINELA ORBITAL"
target_w = W * 0.84
t_size, trk = 168, None
while t_size > 80:
    F_TITLE = load_font(["bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf"], t_size)
    trk = t_size * 0.155
    tw = tracked_width(title, F_TITLE, trk)
    if tw <= target_w:
        break
    t_size -= 2
tx, ty = (W - tw) / 2, H * 0.30
tlayer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_tracked(ImageDraw.Draw(tlayer), tx, ty, title, F_TITLE, (56, 225, 217, 255), trk)
ov = Image.alpha_composite(ov, tlayer.filter(ImageFilter.GaussianBlur(22)))
dr = ImageDraw.Draw(ov)
draw_tracked(dr, tx, ty, title, F_TITLE, (234, 241, 251, 255), trk)

# linha + subtitulo
ly = ty + t_size * 1.22
dr.line([W * 0.30, ly, W * 0.70, ly], fill=(56, 225, 217, 120), width=2)
dr.ellipse([W * 0.5 - 6, ly - 6, W * 0.5 + 6, ly + 6], fill=(56, 225, 217, 255))
sub = "Monitoramento de desmatamento e queimadas por fusao de satelite e IA"
sw = F_SUB.getlength(sub)
dr.text(((W - sw) / 2, ly + 26), sub, font=F_SUB, fill=(176, 190, 214, 255))

# tags fontes
tags = "VISAO COMPUTACIONAL  /  NASA EONET + GIBS  /  IoT ESP32  /  AWS"
tgw = tracked_width(tags, F_KICK, 5)
draw_tracked(dr, (W - tgw) / 2, ly + 84, tags, F_KICK, (150, 165, 190, 255), 5, 3, (4, 8, 16, 220))

# rodape autor
foot = "Bruno de Souza Leite  ·  RM567213"
fw = tracked_width(foot, F_FOOT, 4)
draw_tracked(dr, (W - fw) / 2, H - 96, foot, F_FOOT, (205, 218, 238, 255), 4, 4, (3, 7, 14, 235))

# selo AO VIVO canto inferior esquerdo
live = "● AO VIVO"
dr.text((m + 6, H - 96), live, font=F_KICK, fill=(56, 225, 217, 255),
        stroke_width=4, stroke_fill=(3, 7, 14, 235))

# ---------------------------------------------------------------------------
final = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
OUT.parent.mkdir(parents=True, exist_ok=True)
final.save(OUT, "PNG")
print(f"OK -> {OUT}  ({final.size[0]}x{final.size[1]})")
