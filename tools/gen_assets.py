#!/usr/bin/env python3
"""Generator aset pixel-art orisinal untuk WIRA NUSA.

Semua sprite dibuat programatik dari palet + bentuk dasar, jadi tidak ada
aset pihak ketiga sama sekali. Jalankan ulang kapan saja:

    python3 tools/gen_assets.py --out assets

Sistem paperdoll: karakter dirakit saat runtime dari lapisan terpisah
(kaki, badan, kepala, rambut, topi, sayap, senjata). Tiap lapisan punya
jumlah frame yang sama supaya index frame bisa dipakai bersama.
"""

import argparse
import os
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- konstanta

CELL_W = 24
CELL_H = 32

# urutan animasi dipakai client dan server (SERVER hanya butuh jumlah frame)
ANIM = [
    ("idle", 2),
    ("walk", 4),
    ("atk", 3),
    ("hurt", 1),
    ("die", 2),
]
TOTAL_FRAMES = sum(n for _, n in ANIM)  # 12

# offset badan per frame: (dx, dy) supaya jalan terasa memantul
BOB = [
    (0, 0), (0, -1),                 # idle
    (0, 0), (0, -1), (0, 0), (0, -1),  # walk
    (1, 0), (3, -1), (2, 0),         # atk
    (-1, 1),                          # hurt
    (0, 2), (0, 4),                   # die
]

JOBS = ["pedang", "sepasang", "dukun", "senapan"]

PALETTE = {
    "pedang":   {"main": (168, 62, 54), "trim": (222, 128, 96), "dark": (96, 30, 30)},
    "sepasang": {"main": (58, 108, 168), "trim": (120, 186, 232), "dark": (28, 56, 100)},
    "dukun":    {"main": (120, 74, 168), "trim": (188, 148, 232), "dark": (66, 36, 100)},
    "senapan":  {"main": (54, 138, 96), "trim": (128, 210, 154), "dark": (26, 76, 52)},
}

SKIN = [(232, 190, 152), (206, 158, 118), (168, 120, 84), (128, 88, 62)]
HAIR = [(38, 30, 28), (86, 54, 32), (172, 132, 56), (200, 200, 208)]

TRANSPARENT = (0, 0, 0, 0)


def new_sheet(frames):
    return Image.new("RGBA", (CELL_W * frames, CELL_H), TRANSPARENT)


def px(d, x, y, color):
    d.point((x, y), fill=color)


def box(d, x0, y0, x1, y1, fill, outline=None):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)


# ---------------------------------------------------------------- lapisan

def draw_leg(sheet, frame, i, color, dark):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    base_y = 30 + (by // 2)
    # dua kaki, langkahnya bergantian pada frame walk
    swing = 0
    if 2 <= frame <= 5:
        swing = [2, 0, -2, 0][frame - 2]
    if frame >= 10:  # die: kaki rebah
        box(d, ox + 6, base_y - 2, ox + 18, base_y, fill=color)
        return
    box(d, ox + 9 + swing, base_y - 6, ox + 11 + swing, base_y, fill=color)
    box(d, ox + 13 - swing, base_y - 6, ox + 15 - swing, base_y, fill=color)
    box(d, ox + 8 + swing, base_y, ox + 12 + swing, base_y, fill=dark)
    box(d, ox + 12 - swing, base_y, ox + 16 - swing, base_y, fill=dark)


def draw_body(sheet, frame, i, main, trim, dark):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    top = 14 + by
    if frame >= 10:  # die
        box(d, ox + 5, 26, ox + 19, 30, fill=main, outline=dark)
        return
    lean = 1 if 6 <= frame <= 8 else 0  # condong saat menyerang
    box(d, ox + 8 + lean, top, ox + 16 + lean, top + 10, fill=main, outline=dark)
    # sabuk + aksen dada
    box(d, ox + 8 + lean, top + 8, ox + 16 + lean, top + 9, fill=dark)
    box(d, ox + 11 + lean, top + 2, ox + 13 + lean, top + 6, fill=trim)
    # lengan
    arm_y = top + 2
    if 6 <= frame <= 8:  # ayunan serang
        reach = [1, 4, 2][frame - 6]
        box(d, ox + 16 + lean, arm_y - reach // 2, ox + 17 + reach + lean,
            arm_y + 2 - reach // 2, fill=main, outline=dark)
        box(d, ox + 6 + lean, arm_y, ox + 8 + lean, arm_y + 4, fill=main)
    else:
        sw = 1 if 2 <= frame <= 5 and frame % 2 == 0 else 0
        box(d, ox + 16, arm_y + sw, ox + 17, arm_y + 5 + sw, fill=main, outline=dark)
        box(d, ox + 7, arm_y - sw, ox + 8, arm_y + 5 - sw, fill=main, outline=dark)


def draw_head(sheet, frame, i, skin):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    if frame >= 10:
        box(d, ox + 3, 24, ox + 8, 29, fill=skin, outline=(0, 0, 0))
        return
    top = 5 + by
    box(d, ox + 8, top, ox + 16, top + 8, fill=skin, outline=(48, 32, 24))
    # mata menghadap kanan
    px(d, ox + 14, top + 4, (32, 24, 20))
    px(d, ox + 12, top + 4, (32, 24, 20))


def draw_hair(sheet, frame, i, color, style):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    if frame >= 10:
        box(d, ox + 3, 23, ox + 8, 25, fill=color)
        return
    top = 5 + by
    box(d, ox + 7, top - 1, ox + 16, top + 2, fill=color)
    if style == 0:      # cepak
        pass
    elif style == 1:    # poni
        box(d, ox + 13, top + 2, ox + 16, top + 3, fill=color)
    elif style == 2:    # ekor kuda
        box(d, ox + 5, top + 1, ox + 7, top + 7, fill=color)
    else:               # gondrong
        box(d, ox + 6, top + 1, ox + 8, top + 9, fill=color)
        box(d, ox + 16, top + 1, ox + 17, top + 6, fill=color)


def draw_hat(sheet, frame, i, main, trim, kind):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    if frame >= 10:
        return
    top = 5 + by
    if kind == 0:      # ikat kepala
        box(d, ox + 7, top, ox + 16, top + 1, fill=main)
        box(d, ox + 5, top, ox + 7, top + 3, fill=trim)
    elif kind == 1:    # caping
        box(d, ox + 4, top - 1, ox + 19, top, fill=main)
        box(d, ox + 8, top - 4, ox + 15, top - 1, fill=trim)
    else:              # helm
        box(d, ox + 7, top - 3, ox + 16, top + 2, fill=main, outline=(24, 24, 24))
        box(d, ox + 11, top - 5, ox + 12, top - 3, fill=trim)


def draw_wing(sheet, frame, i, main, trim):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    if frame >= 10:
        return
    top = 14 + by
    flap = [0, 1, 0, 1, 2, 1, 0, 1, 2, 0][frame] if frame < 10 else 0
    box(d, ox + 2 + flap, top - 2, ox + 8, top + 6 - flap, fill=main)
    box(d, ox + 3 + flap, top, ox + 6, top + 4 - flap, fill=trim)


def draw_weapon(sheet, frame, i, job, tier):
    d = ImageDraw.Draw(sheet)
    ox = i * CELL_W
    bx, by = BOB[frame]
    if frame >= 10:
        return
    pal = PALETTE[job]
    glow = (255, 236, 160) if tier >= 2 else pal["trim"]
    steel = (198, 202, 214) if tier == 0 else (232, 226, 190)
    arm_y = 16 + by
    swing = 0
    if 6 <= frame <= 8:
        swing = [2, 6, 4][frame - 6]
    hx = 17 + swing
    if job == "pedang":
        box(d, ox + hx, arm_y - 8, ox + hx + 1, arm_y + 2, fill=steel)
        box(d, ox + hx - 1, arm_y + 2, ox + hx + 2, arm_y + 3, fill=pal["dark"])
        if tier >= 1:
            box(d, ox + hx, arm_y - 9, ox + hx + 1, arm_y - 8, fill=glow)
    elif job == "sepasang":
        box(d, ox + hx, arm_y - 5, ox + hx + 1, arm_y + 1, fill=steel)
        box(d, ox + 5 - swing // 2, arm_y - 3, ox + 6 - swing // 2, arm_y + 3, fill=steel)
        if tier >= 1:
            box(d, ox + hx, arm_y - 6, ox + hx + 1, arm_y - 5, fill=glow)
    elif job == "dukun":
        box(d, ox + hx, arm_y - 10, ox + hx + 1, arm_y + 4, fill=(120, 84, 50))
        box(d, ox + hx - 1, arm_y - 13, ox + hx + 2, arm_y - 10, fill=glow)
        if tier >= 1:
            box(d, ox + hx - 2, arm_y - 14, ox + hx + 3, arm_y - 13, fill=pal["trim"])
    else:  # senapan
        box(d, ox + hx - 2, arm_y - 1, ox + hx + 6, arm_y + 1, fill=(72, 72, 84))
        box(d, ox + hx - 3, arm_y, ox + hx, arm_y + 3, fill=(120, 84, 50))
        if tier >= 1:
            box(d, ox + hx + 6, arm_y - 1, ox + hx + 7, arm_y + 1, fill=glow)


# ---------------------------------------------------------------- mob

MOBS = [
    ("celeng", (110, 82, 62), (60, 44, 34), 20, 16),
    ("kunti", (226, 226, 236), (150, 150, 170), 18, 26),
    ("genderuwo", (86, 66, 54), (40, 30, 24), 26, 28),
    ("buto", (108, 132, 74), (52, 64, 36), 30, 30),
    ("naga", (78, 140, 128), (34, 74, 68), 40, 32),
]
MOB_FRAMES = 6  # idle 2, walk 2, atk 2


def gen_mob(name, main, dark, w, h):
    img = Image.new("RGBA", (w * MOB_FRAMES, h), TRANSPARENT)
    d = ImageDraw.Draw(img)
    for f in range(MOB_FRAMES):
        ox = f * w
        bob = [0, 1, 0, 2, 0, -1][f]
        lunge = 2 if f >= 4 else 0
        box(d, ox + 2 + lunge, h - 14 + bob, ox + w - 4, h - 3 + bob,
            fill=main, outline=dark)
        # kepala
        box(d, ox + w - 9 + lunge, h - 20 + bob, ox + w - 2, h - 13 + bob,
            fill=main, outline=dark)
        px(d, ox + w - 4, h - 17 + bob, (240, 60, 50))
        # kaki
        step = 1 if f % 2 else 0
        box(d, ox + 4 + step, h - 3 + bob, ox + 6 + step, h - 1 + bob, fill=dark)
        box(d, ox + w - 8 - step, h - 3 + bob, ox + w - 6 - step, h - 1 + bob, fill=dark)
        if name == "naga":
            box(d, ox, h - 22 + bob, ox + 6, h - 16 + bob, fill=dark)  # sayap
        if name == "kunti":
            box(d, ox + 3, h - 6 + bob, ox + w - 5, h - 1 + bob, fill=(255, 255, 255, 120))
    return img


# ---------------------------------------------------------------- latar & tile

def gen_bg_layer(w, h, top, bottom, hills, seed):
    import random
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y * 255 // max(h - 1, 1)
        col = tuple(top[i] + (bottom[i] - top[i]) * t // 255 for i in range(3))
        d.line([(0, y), (w, y)], fill=col + (255,))
    if hills:
        base = h - 6
        prev = base - rng.randint(6, 18)
        for x in range(0, w + 8, 8):
            nxt = max(8, min(h - 8, prev + rng.randint(-6, 6)))
            d.polygon([(x, base), (x, prev), (x + 8, nxt), (x + 8, base)],
                      fill=tuple(max(0, c - 28) for c in bottom) + (255,))
            prev = nxt
    return img


TILES = [
    ("tanah", (118, 92, 58), (86, 64, 40), (74, 132, 62)),
    ("batu", (128, 128, 138), (86, 86, 96), (150, 150, 158)),
    ("pasir", (214, 190, 132), (176, 150, 96), (226, 208, 158)),
    ("lava", (92, 48, 40), (60, 28, 24), (220, 96, 40)),
]
TILE = 16


def gen_tileset(name, body, dark, top):
    img = Image.new("RGBA", (TILE * 3, TILE), TRANSPARENT)
    d = ImageDraw.Draw(img)
    for i in range(3):
        ox = i * TILE
        box(d, ox, 0, ox + TILE - 1, TILE - 1, fill=body)
        if i == 0:  # tile permukaan
            box(d, ox, 0, ox + TILE - 1, 2, fill=top)
        if i == 2:  # tile hancur / tepi
            box(d, ox, 0, ox + 3, TILE - 1, fill=dark)
        for y in range(4, TILE, 5):
            d.line([(ox, y), (ox + TILE - 1, y)], fill=dark)
    return img


# ---------------------------------------------------------------- antarmuka

def gen_ui():
    out = {}
    # bar hp/mp: 3 potong (kiri, isi, kanan)
    for name, col in (("hp", (206, 62, 54)), ("mp", (58, 112, 196)),
                      ("exp", (226, 178, 52))):
        img = Image.new("RGBA", (12, 6), TRANSPARENT)
        d = ImageDraw.Draw(img)
        box(d, 0, 0, 11, 5, fill=(28, 28, 34), outline=(70, 70, 80))
        box(d, 1, 1, 10, 4, fill=col)
        out["bar_" + name] = img
    # tombol aksi bulat
    for name, col in (("atk", (206, 92, 54)), ("skill", (120, 92, 200)),
                      ("item", (72, 160, 96))):
        img = Image.new("RGBA", (20, 20), TRANSPARENT)
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, 19, 19], fill=col, outline=(24, 24, 28))
        d.ellipse([4, 3, 15, 10], fill=tuple(min(255, c + 46) for c in col))
        out["btn_" + name] = img
    # ikon item 12x12
    icons = {
        "potion_hp": (206, 62, 54), "potion_mp": (58, 112, 196),
        "batu_upgrade": (226, 178, 52), "kristal": (150, 96, 220),
        "kayu": (120, 84, 50), "besi": (150, 152, 162),
    }
    for name, col in icons.items():
        img = Image.new("RGBA", (12, 12), TRANSPARENT)
        d = ImageDraw.Draw(img)
        box(d, 1, 1, 10, 10, fill=col, outline=(24, 24, 28))
        box(d, 3, 3, 5, 5, fill=tuple(min(255, c + 60) for c in col))
        out["ikon_" + name] = img
    return out


def gen_icon():
    img = Image.new("RGBA", (48, 48), (18, 20, 28, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 47, 47], outline=(226, 178, 52))
    # pedang menyilang
    d.line([(10, 38), (34, 12)], fill=(214, 216, 226), width=3)
    d.line([(38, 38), (14, 12)], fill=(214, 216, 226), width=3)
    d.line([(8, 34), (16, 42)], fill=(168, 62, 54), width=3)
    d.line([(40, 34), (32, 42)], fill=(58, 108, 168), width=3)
    d.rectangle([20, 4, 27, 11], fill=(226, 178, 52))
    return img


# ---------------------------------------------------------------- main

def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()
    out = args.out
    total = 0
    count = 0

    # ---- paperdoll
    for job_i, job in enumerate(JOBS):
        pal = PALETTE[job]
        sheet = new_sheet(TOTAL_FRAMES)
        for f in range(TOTAL_FRAMES):
            draw_body(sheet, f, f, pal["main"], pal["trim"], pal["dark"])
        total += save(sheet, "%s/c/body/b%d.png" % (out, job_i)); count += 1

    for i, skin in enumerate(SKIN):
        sheet = new_sheet(TOTAL_FRAMES)
        for f in range(TOTAL_FRAMES):
            draw_head(sheet, f, f, skin)
        total += save(sheet, "%s/c/head/h%d.png" % (out, i)); count += 1

    for i, col in enumerate(HAIR):
        for style in range(4):
            sheet = new_sheet(TOTAL_FRAMES)
            for f in range(TOTAL_FRAMES):
                draw_hair(sheet, f, f, col, style)
            total += save(sheet, "%s/c/hair/r%d_%d.png" % (out, i, style)); count += 1

    for job_i, job in enumerate(JOBS):
        pal = PALETTE[job]
        for kind in range(3):
            sheet = new_sheet(TOTAL_FRAMES)
            for f in range(TOTAL_FRAMES):
                draw_hat(sheet, f, f, pal["main"], pal["trim"], kind)
            total += save(sheet, "%s/c/hat/t%d_%d.png" % (out, job_i, kind)); count += 1

        sheet = new_sheet(TOTAL_FRAMES)
        for f in range(TOTAL_FRAMES):
            draw_leg(sheet, f, f, pal["dark"], (32, 28, 30))
        total += save(sheet, "%s/c/leg/k%d.png" % (out, job_i)); count += 1

        for tier in range(3):
            sheet = new_sheet(TOTAL_FRAMES)
            for f in range(TOTAL_FRAMES):
                draw_weapon(sheet, f, f, job, tier)
            total += save(sheet, "%s/weapon/%s/w%d.png" % (out, job, tier)); count += 1

    for i, (main_c, trim_c) in enumerate([
            ((226, 226, 240), (255, 255, 255)),
            ((240, 168, 72), (255, 222, 150)),
            ((150, 96, 220), (206, 170, 255))]):
        sheet = new_sheet(TOTAL_FRAMES)
        for f in range(TOTAL_FRAMES):
            draw_wing(sheet, f, f, main_c, trim_c)
        total += save(sheet, "%s/c/wing/s%d.png" % (out, i)); count += 1

    # ---- mob
    for name, main_c, dark_c, w, h in MOBS:
        total += save(gen_mob(name, main_c, dark_c, w, h),
                      "%s/mob/%s.png" % (out, name)); count += 1

    # ---- latar parallax (3 lapis x 4 tema)
    themes = [
        ("desa", (128, 186, 232), (206, 228, 246)),
        ("hutan", (72, 128, 96), (150, 196, 140)),
        ("gurun", (232, 196, 128), (246, 226, 176)),
        ("kawah", (72, 40, 48), (176, 88, 56)),
    ]
    for name, top, bottom in themes:
        for layer in range(3):
            w = 128 + layer * 32
            h = 64 + layer * 16
            img = gen_bg_layer(w, h, top, bottom, layer > 0, hash(name) + layer)
            total += save(img, "%s/bg/%s_%d.png" % (out, name, layer)); count += 1

    # ---- tile
    for name, body, dark, top in TILES:
        total += save(gen_tileset(name, body, dark, top),
                      "%s/tile/%s.png" % (out, name)); count += 1

    # ---- antarmuka
    for name, img in gen_ui().items():
        total += save(img, "%s/ui/%s.png" % (out, name)); count += 1
    total += save(gen_icon(), "%s/icon.png" % out); count += 1

    # ---- manifest supaya client tahu apa yang ada tanpa listing direktori
    lines = ["# dihasilkan gen_assets.py", "frames=%d" % TOTAL_FRAMES,
             "cell=%dx%d" % (CELL_W, CELL_H)]
    for label, n in ANIM:
        lines.append("anim.%s=%d" % (label, n))
    lines.append("jobs=" + ",".join(JOBS))
    lines.append("mobs=" + ",".join(m[0] for m in MOBS))
    lines.append("tiles=" + ",".join(t[0] for t in TILES))
    lines.append("themes=" + ",".join(t[0] for t in themes))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "manifest.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print("file   : %d" % count)
    print("ukuran : %.1f KB" % (total / 1024.0))
    print("frame  : %d per lapisan paperdoll" % TOTAL_FRAMES)
    if count < 60 or total > 900 * 1024:
        print("ASSET_FAIL")
        raise SystemExit(1)
    print("ASSET_OK")


if __name__ == "__main__":
    main()
