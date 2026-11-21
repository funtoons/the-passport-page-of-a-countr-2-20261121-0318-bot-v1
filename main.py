#!/usr/bin/env python3
"""Kavarra Passport Spread v1.

Builds one image: the open passport spread of the invented
Republic of Kavarra. Pure standard library, fully deterministic:
no network, no randomness, no clock, no files outside the repo.
Writes entry.png (1024x1024, under 1 MiB) to
$MAKEFUN_OUTPUT_DIR (or ./output when unset).
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
DESK_TOP = (27, 50, 71)
DESK_BOT = (13, 26, 38)
PAGE_L = (246, 239, 221)
PAGE_R = (242, 231, 205)
PAGE_EDGE = (214, 196, 158)
INK = (31, 58, 95)
INK_SOFT = (74, 96, 128)
GOLD = (176, 141, 62)
GOLD_LT = (201, 162, 39)
GOLD_DK = (122, 94, 38)
TEAL = (15, 118, 110)
TEAL_DK = (10, 84, 78)
BURG = (127, 29, 46)
VIOLET = (91, 74, 138)
GREEN = (47, 107, 58)
CREAM_LINE = (232, 219, 186)
PHOTO_BG = (168, 188, 205)
PHOTO_BG2 = (140, 165, 188)
SILH = (38, 64, 96)
SILH2 = (24, 46, 74)
MRZ_BG = (233, 222, 190)
FAINT_GOLD = (216, 196, 150)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '#' = on.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}

BLANK = ("00000",) * 7


def text_width(s, scale, spacing=1):
    return len(s) * (5 * scale + spacing) - spacing


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def blend_set(self, x, y, c, a):
        """Blend colour c over the pixel with alpha a (0..1)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1 - a) + c[k] * a)

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.w, x1); y1 = min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def vgrad_rect(self, x0, y0, x1, y1, top, bot):
        for y in range(max(0, y0), min(self.h, y1)):
            t = (y - y0) / max(1, (y1 - y0 - 1))
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.fill_rect(x0, y, x1, y + 1, c)

    def hline(self, x0, x1, y, c, th=1):
        for t in range(th):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set(x, y + t, c)

    def vline(self, x, y0, y1, c, th=1):
        for t in range(th):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                self.set(x + t, y, c)

    def line(self, x0, y0, x1, y1, c, th=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for a in range(th):
                for b in range(th):
                    self.set(x + a, y + b, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; x += sx
            if e2 < dx:
                err += dx; y += sy

    def rect(self, x0, y0, x1, y1, c, th=1):
        self.hline(x0, x1, y0, c, th)
        self.hline(x0, x1, y1 - th + 1, c, th)
        self.vline(x0, y0, y1, c, th)
        self.vline(x1 - th + 1, y0, y1, c, th)

    def circle(self, cx, cy, r, c, th=1, fill=False):
        if fill:
            for y in range(cy - r, cy + r + 1):
                dx = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
                self.hline(cx - dx, cx + dx, y, c)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                           (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                for a in range(th):
                    for b in range(th):
                        self.set(px + a, py + b, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10; y -= 1
            x += 1

    def ellipse_fill(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1 - t * t)))
            self.hline(cx - dx, cx + dx, y, c)

    def poly(self, pts, c, th=1):
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            self.line(x0, y0, x1, y1, c, th)

    def poly_fill(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(xs[k]), int(xs[k + 1]), y, c)

    def star(self, cx, cy, r_out, r_in, points, c, rot=-math.pi / 2, fill=True):
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = rot + i * math.pi / points
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        if fill:
            self.poly_fill(pts, c)
        else:
            self.poly(pts, c)

    def rosette(self, cx, cy, r, c, waves=12, amp=5, th=1):
        prev = None
        steps = 240
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            rr = r + amp * math.sin(waves * a)
            p = (int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, th)
            prev = p

    def text(self, s, x, y, scale, c, spacing=1):
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, BLANK)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       cx + col * scale + scale,
                                       y + row * scale + scale, c)
            cx += 5 * scale + spacing
        return cx

    def text_center(self, s, cx, y, scale, c, spacing=1):
        w = text_width(s, scale, spacing)
        return self.text(s, cx - w // 2, y, scale, c, spacing)

    def dotted_row(self, x0, x1, y, step, c, r=2):
        for x in range(x0, x1, step):
            self.circle(x, y, r, c, fill=True)


# ---------------------------------------------------------------- PNG out
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack('>I', len(data)) + typ + data
        out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', comp)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- drawing
def flag(cv, x, y, w, h):
    """Tricolour of Kavarra: teal / cream / burgundy, gold star."""
    third = h // 3
    cv.fill_rect(x, y, x + w, y + third, TEAL)
    cv.fill_rect(x, y + third, x + w, y + 2 * third, (240, 232, 205))
    cv.fill_rect(x, y + 2 * third, x + w, y + h, BURG)
    cv.star(x + w // 2, y + h // 2, 9, 4, 5, GOLD_LT)
    cv.rect(x, y, x + w, y + h, GOLD_DK, 1)


def portrait(cv, x0, y0, x1, y1):
    """Stylised passport portrait: duotone silhouette bust."""
    cv.vgrad_rect(x0, y0, x1, y1, PHOTO_BG, PHOTO_BG2)
    # faint guilloche arcs behind the head
    for r in (52, 66, 80):
        cv.circle((x0 + x1) // 2, y0 + 78, r, (150, 172, 194), th=1)
    cx = (x0 + x1) // 2
    # shoulders / jacket (kept inside the photo box)
    cv.poly_fill([(x0 + 6, y1), (cx - 42, y1 - 48), (cx + 42, y1 - 48),
                  (x1 - 6, y1)], SILH)
    # shirt + tie
    cv.poly_fill([(cx - 16, y1 - 44), (cx + 16, y1 - 44), (cx, y1 - 8)], (238, 234, 222))
    cv.poly_fill([(cx - 6, y1 - 40), (cx + 6, y1 - 40), (cx + 4, y1 - 14),
                  (cx, y1 - 8), (cx - 4, y1 - 14)], (90, 30, 40))
    # neck + head
    cv.fill_rect(cx - 12, y0 + 96, cx + 12, y0 + 128, (196, 158, 128))
    cv.circle(cx, y0 + 66, 40, (196, 158, 128), fill=True)
    # hair: cap over the top of the head
    cv.ellipse_fill(cx, y0 + 44, 40, 26, SILH2)
    cv.poly_fill([(cx - 40, y0 + 52), (cx + 40, y0 + 52), (cx + 34, y0 + 26),
                  (cx - 34, y0 + 26)], SILH2)
    # simple glasses hint
    cv.circle(cx - 16, y0 + 66, 11, SILH2, th=2)
    cv.circle(cx + 16, y0 + 66, 11, SILH2, th=2)
    cv.hline(cx - 5, cx + 5, y0 + 66, SILH2, 2)
    # smile hint
    cv.line(cx - 8, y0 + 88, cx + 8, y0 + 88, (120, 70, 60), 2)


def coat_of_arms(cv, cx, cy):
    """Shield: three peaks over waves, eight-point star above, motto banner."""
    # star above shield
    cv.star(cx, cy - 108, 20, 8, 8, GOLD_LT)
    # shield outline
    shield = [(cx - 78, cy - 78), (cx + 78, cy - 78), (cx + 78, cy + 18),
              (cx, cy + 84), (cx - 78, cy + 18)]
    cv.poly_fill(shield, (250, 244, 224))
    cv.poly(shield, GOLD_DK, 3)
    # sky + mountains + waves inside shield (clipped by drawing inside)
    cv.poly_fill([(cx - 62, cy - 20), (cx - 26, cy - 62), (cx + 6, cy - 20)], TEAL_DK)
    cv.poly_fill([(cx - 8, cy - 20), (cx + 28, cy - 66), (cx + 62, cy - 20)], TEAL)
    cv.poly_fill([(cx - 26, cy - 62), (cx - 14, cy - 50), (cx - 30, cy - 48)], (250, 244, 224))
    cv.poly_fill([(cx + 28, cy - 66), (cx + 40, cy - 52), (cx + 20, cy - 50)], (250, 244, 224))
    for k, yy in enumerate((cy + 6, cy + 22, cy + 38)):
        y = yy
        prev = None
        for x in range(cx - 66, cx + 67, 4):
            p = (x, y + int(5 * math.sin((x - cx) / 14.0 + k)))
            if prev is not None:
                cv.line(prev[0], prev[1], p[0], p[1], (31, 58, 95) if k < 2 else BURG, 2)
            prev = p
    # banner with motto
    bx0, bx1 = cx - 96, cx + 96
    by = cy + 92
    cv.poly_fill([(bx0, by), (bx1, by), (bx1 + 12, by + 12), (bx1, by + 24),
                  (bx0, by + 24), (bx0 - 12, by + 12)], GOLD)
    cv.poly([(bx0, by), (bx1, by), (bx1 + 12, by + 12), (bx1, by + 24),
             (bx0, by + 24), (bx0 - 12, by + 12)], GOLD_DK, 2)
    cv.text_center("MARE ET MONTES LIBERI", cx, by + 5, 1, (255, 250, 230), spacing=1)


def stamp_rect(cv, x0, y0, x1, y1, c, title, lines):
    cv.rect(x0, y0, x1, y1, c, 3)
    cv.rect(x0 + 6, y0 + 6, x1 - 6, y1 - 6, c, 1)
    cv.text_center(title, (x0 + x1) // 2, y0 + 12, 2, c, spacing=1)
    cv.hline(x0 + 12, x1 - 12, y0 + 34, c, 2)
    yy = y0 + 44
    for ln in lines:
        cv.text_center(ln, (x0 + x1) // 2, yy, 1, c, spacing=1)
        yy += 13


def build():
    cv = Canvas(W, H)
    cv.vgrad_rect(0, 0, W, H, DESK_TOP, DESK_BOT)
    # faint dotted world-map hint on the desk
    for gx in range(40, 1000, 46):
        for gy in range(36, 130, 34):
            if (gx * 7 + gy * 13) % 5 < 3:
                cv.circle(gx, gy, 2, (52, 84, 110), fill=True)
    for gx in range(40, 1000, 46):
        for gy in range(920, 1000, 34):
            if (gx * 7 + gy * 13) % 5 < 3:
                cv.circle(gx, gy, 2, (52, 84, 110), fill=True)

    # soft shadow under the spread
    cv.fill_rect(64, 196, 984, 842, (8, 16, 26))
    # spread pages
    SX0, SY0, SX1, SY1 = 52, 170, 972, 830
    MX = (SX0 + SX1) // 2
    cv.fill_rect(SX0, SY0, MX, SY1, PAGE_L)
    cv.fill_rect(MX, SY0, SX1, SY1, PAGE_R)
    # gutter shadow
    for i, w in enumerate((2, 5, 9, 14)):
        shade = (206, 188, 150 - i * 6)
        cv.fill_rect(MX - w, SY0, MX - w + 2, SY1, shade)
        cv.fill_rect(MX + w - 2, SY0, MX + w, SY1, shade)
    cv.vline(MX, SY0, SY1, (160, 138, 100), 2)
    # outer gold frame
    cv.rect(SX0, SY0, SX1, SY1, GOLD_DK, 3)
    cv.rect(SX0 + 10, SY0 + 10, SX1 - 10, SY1 - 10, GOLD, 1)
    cv.rect(MX - 2, SY0 + 10, MX + 2, SY1 - 10, GOLD, 1)
    # perforated passport number along the top of each page
    cv.dotted_row(SX0 + 30, MX - 30, SY0 + 22, 9, (120, 100, 70), r=2)
    cv.dotted_row(MX + 30, SX1 - 30, SY0 + 22, 9, (120, 100, 70), r=2)

    # ================= LEFT PAGE: data page =================
    # faint rosette watermark behind the data
    cv.rosette(300, 470, 150, FAINT_GOLD, waves=10, amp=4, th=1)
    cv.rosette(300, 470, 110, FAINT_GOLD, waves=10, amp=4, th=1)
    # header
    flag(cv, 82, 196, 52, 30)
    cv.text("REPUBLIC OF KAVARRA", 148, 198, 3, INK, spacing=1)
    cv.text("PASSEPORT  -  PASSPORT", 148, 226, 2, GOLD_DK, spacing=1)
    cv.hline(82, 482, 258, GOLD, 2)
    # photo
    cv.rect(78, 280, 222, 474, INK, 3)
    cv.rect(82, 284, 218, 470, GOLD, 1)
    portrait(cv, 84, 286, 216, 468)
    cv.text("PHOTO", 84, 478, 1, INK_SOFT, spacing=1)
    # data fields
    fields = [
        ("SURNAME", "VOSS"),
        ("GIVEN NAMES", "ELARA MIREN"),
        ("NATIONALITY", "KAVARRAN"),
        ("DATE OF BIRTH", "14 MAR 1998"),
        ("PLACE OF BIRTH", "PORT SELENE"),
        ("SEX / HEIGHT", "F  /  172 CM"),
        ("DATE OF ISSUE", "02 JUN 2026"),
        ("DATE OF EXPIRY", "01 JUN 2036"),
        ("AUTHORITY", "MINISTRY OF INTERIOR"),
    ]
    fy = 282
    for label, value in fields:
        cv.text(label, 238, fy, 1, INK_SOFT, spacing=1)
        cv.text(value, 238, fy + 11, 2, INK, spacing=1)
        fy += 32
    cv.text("PASSPORT No", 238, fy + 2, 1, INK_SOFT, spacing=1)
    cv.text("KV 482 913", 238, fy + 13, 3, BURG, spacing=1)
    # biometric chip
    cv.fill_rect(238, 636, 292, 676, GOLD_LT)
    cv.rect(238, 636, 292, 676, GOLD_DK, 2)
    for yy in (646, 656, 666):
        cv.hline(244, 286, yy, GOLD_DK, 1)
    cv.vline(265, 640, 672, GOLD_DK, 1)
    cv.text("CHIP", 296, 648, 1, INK_SOFT, spacing=1)
    # signature squiggle
    cv.text("HOLDER'S SIGNATURE", 320, 636, 1, INK_SOFT, spacing=1)
    pts = [(322, 668), (336, 652), (350, 670), (364, 650), (378, 668),
           (392, 654), (406, 670), (420, 656), (434, 668), (448, 660),
           (462, 670), (476, 662)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], INK, 2)
    cv.hline(320, 482, 678, INK_SOFT, 1)
    # MRZ zone
    cv.fill_rect(72, 706, 492, 800, MRZ_BG)
    cv.rect(72, 706, 492, 800, (190, 170, 120), 1)
    cv.text("P<KAVVOSS<<ELARA<MIREN<<<<<<<<<<<<<<<<<<<<", 84, 718, 1, INK, spacing=3)
    cv.text("KV4829130KAV9803147F3606015<<<<<<<<<<<<08", 84, 738, 1, INK, spacing=3)
    cv.text("TYPE P   CODE KAV   No KV482913", 84, 766, 1, INK_SOFT, spacing=1)
    cv.text("10", 466, 806, 2, INK_SOFT, spacing=1)

    # ================= RIGHT PAGE: visas & stamps =================
    cv.text_center("VISAS", 742, 196, 3, INK, spacing=2)
    cv.text_center("VISA  -  STAMPS  -  ENDORSEMENTS", 742, 226, 1, GOLD_DK, spacing=1)
    cv.hline(542, 942, 258, GOLD, 2)
    coat_of_arms(cv, 742, 392)
    # entry / departure stamps
    stamp_rect(cv, 542, 540, 736, 640, BURG, "PORT SELENE",
               ["DEPARTURE", "02 JUN 2026", "No 1187"])
    stamp_rect(cv, 748, 540, 942, 640, TEAL_DK, "AURELIA",
               ["ENTRY", "19 JUN 2026", "No 0442"])
    # visa sticker
    cv.fill_rect(542, 656, 788, 792, (16, 96, 90))
    cv.vgrad_rect(542, 656, 788, 792, (20, 110, 102), (12, 78, 74))
    cv.rect(542, 656, 788, 792, GOLD_LT, 3)
    cv.rect(548, 662, 782, 786, GOLD, 1)
    flag(cv, 556, 672, 40, 22)
    cv.text("VISA", 606, 672, 3, (250, 240, 200), spacing=2)
    cv.text("KINGDOM OF AURELIA", 556, 706, 2, (250, 240, 200), spacing=1)
    cv.hline(556, 774, 730, GOLD_LT, 1)
    cv.text("No AU-77120", 556, 742, 1, (220, 210, 170), spacing=1)
    cv.text("VALID 90 DAYS", 556, 758, 1, (220, 210, 170), spacing=1)
    cv.text("SINGLE ENTRY", 680, 742, 1, (220, 210, 170), spacing=1)
    cv.text("19 JUN-16 SEP 26", 680, 758, 1, (220, 210, 170), spacing=1)
    # circular date stamp, bottom right, clear of the sticker
    cv.circle(871, 724, 58, VIOLET, th=3)
    cv.circle(871, 724, 48, VIOLET, th=1)
    cv.text_center("PORT", 871, 694, 1, VIOLET, spacing=1)
    cv.text_center("SELENE", 871, 708, 1, VIOLET, spacing=1)
    cv.text_center("11 AUG", 871, 722, 2, VIOLET, spacing=1)
    cv.text_center("2026", 871, 742, 2, VIOLET, spacing=1)
    cv.text_center("RETURN", 871, 760, 1, VIOLET, spacing=1)
    cv.text("THIS PASSPORT CONTAINS 32 PAGES", 542, 806, 1, INK_SOFT, spacing=1)
    cv.text("11", 926, 806, 2, INK_SOFT, spacing=1)

    # caption under the spread
    cv.text_center("THE PASSPORT OF KAVARRA  -  AN INVENTED COUNTRY",
                   512, 872, 2, GOLD_LT, spacing=1)
    cv.text_center("SPECIMEN  No 001  -  NOT A TRAVEL DOCUMENT",
                   512, 900, 1, (120, 140, 160), spacing=1)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    cv = build()
    size = write_png(cv, path)
    print(f"wrote {path} {cv.w}x{cv.h} {size} bytes")


if __name__ == "__main__":
    main()
