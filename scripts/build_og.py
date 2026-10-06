#!/usr/bin/env python3
"""Generate og.png, the 1200x630 social preview image, with the stdlib only.

The design is geometric: a linked-nodes motif (the same idea as the favicon)
beside the title in a 5x7 pixel font, in the site's dark palette. It is an
8-bit palette PNG. Anti-aliased shapes use a 16-step ramp from background to
accent, so the edges are smooth.

Deterministic on every platform: the PNG is written with a hand-rolled
deflate stream (fixed Huffman codes, runs of the previous byte only, rows
filtered "Up") instead of zlib.compress, whose output can differ between zlib
builds. Only zlib.adler32 and zlib.crc32 are used, and those are specified.

    python3 scripts/build_og.py
"""
import io, math, os, struct, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from site_common import DARK

W, H = 1200, 630


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (1, 3, 5))


BG, ACCENT = rgb(DARK["paper"]), rgb(DARK["accent"])
RAMP = 16                      # indices 0..15: BG -> ACCENT
INK, SOFT, GOLD, FAINT = 16, 17, 18, 19
PALETTE = ([tuple(round(BG[c] + (ACCENT[c] - BG[c]) * i / (RAMP - 1)) for c in range(3))
            for i in range(RAMP)]
           + [rgb(DARK["ink"]), rgb(DARK["soft"]), rgb(DARK["num"]), rgb(DARK["faint"])])

# 5x7 pixel font; only the characters the card uses.
_GLYPHS = """
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I ##### ..#.. ..#.. ..#.. ..#.. ..#.. #####
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# ##..# #.#.# #..## #...# #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
W #...# #...# #...# #.#.# #.#.# ##.## #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
- ..... ..... ..... ##### ..... ..... .....
[ ###.. #.... #.... #.... #.... #.... ###..
] ..### ....# ....# ....# ....# ....# ..###
. ..... ..... ..... ..... ..... .##.. .##..
"""
FONT = {}
for _line in _GLYPHS.strip().split("\n"):
    _ch, *_rows = _line.split()
    assert len(_rows) == 7 and all(len(r) == 5 for r in _rows), _line
    FONT[_ch] = "".join(_rows)


def new_canvas():
    return [bytearray(W) for _ in range(H)]


def clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = clamp01(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))
    ex, ey = px - ax - t * dx, py - ay - t * dy
    return math.sqrt(ex * ex + ey * ey)


def line(cv, a, b, width):
    hw = width / 2
    x0, x1 = int(min(a[0], b[0]) - width - 2), int(max(a[0], b[0]) + width + 2)
    y0, y1 = int(min(a[1], b[1]) - width - 2), int(max(a[1], b[1]) + width + 2)
    for y in range(max(0, y0), min(H, y1)):
        row = cv[y]
        for x in range(max(0, x0), min(W, x1)):
            c = clamp01(hw + 0.5 - seg_dist(x + .5, y + .5, a[0], a[1], b[0], b[1]))
            v = round(c * (RAMP - 1))
            if v > row[x] and row[x] < RAMP:
                row[x] = v


def node(cv, cx, cy, r, ring=4, filled=False):
    for y in range(max(0, int(cy - r - 2)), min(H, int(cy + r + 3))):
        row = cv[y]
        for x in range(max(0, int(cx - r - 2)), min(W, int(cx + r + 3))):
            ex, ey = x + .5 - cx, y + .5 - cy
            d = math.sqrt(ex * ex + ey * ey)
            disk = clamp01(r + .5 - d)
            if disk <= 0:
                continue
            if filled:
                row[x] = max(round(row[x] * (1 - disk)), round(disk * (RAMP - 1)))
            else:
                row[x] = round(row[x] * (1 - disk))
                ringc = clamp01(ring / 2 + .5 - abs(d - (r - ring / 2)))
                row[x] = max(row[x], round(ringc * (RAMP - 1)))


def rect(cv, x, y, w, h, color):
    for yy in range(y, y + h):
        cv[yy][x:x + w] = bytes([color]) * w


def text(cv, x, y, s, string, color):
    for ch in string:
        g = FONT.get(ch)
        if g:
            for r in range(7):
                for c in range(5):
                    if g[r * 5 + c] == "#":
                        rect(cv, x + c * s, y + r * s, s, s, color)
        x += 6 * s


def draw():
    cv = new_canvas()
    for y in range(20, H, 40):                       # faint dot grid
        for x in range(20, W, 40):
            rect(cv, x, y, 2, 2, 2)
    pts = {"a": (800, 470), "b": (905, 262), "c": (1040, 392), "d": (1100, 176),
           "e": (790, 196), "f": (1104, 528), "g": (930, 548)}
    for p, q in ("ab", "bc", "bd", "eb", "ae", "cf", "ag", "gc", "ed"):
        line(cv, pts[p], pts[q], 3)
    for k, r in (("a", 36), ("b", 36), ("c", 36), ("e", 26), ("f", 26), ("g", 22)):
        node(cv, pts[k][0], pts[k][1], r)
    node(cv, pts["d"][0], pts["d"][1], 20, filled=True)
    rect(cv, 72, 84, 96, 8, RAMP - 1)
    text(cv, 72, 112, 4, "[[ GUIDE - COURSE - HANDBOOKS ]]", GOLD)
    text(cv, 72, 190, 13, "SECOND", INK)
    text(cv, 72, 300, 13, "BRAIN OS", INK)
    text(cv, 72, 436, 4, "A KNOWLEDGE BASE YOUR", SOFT)
    text(cv, 72, 472, 4, "AGENT MAINTAINS.", SOFT)
    text(cv, 72, 560, 3, "PLAIN MARKDOWN YOU OWN", FAINT)
    return cv


# ---- PNG with a hand-written, platform-independent deflate stream
LEN_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51,
            59, 67, 83, 99, 115, 131, 163, 195, 227, 258]
LEN_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4,
             4, 5, 5, 5, 5, 0]


class Bits:
    def __init__(self):
        self.out, self.acc, self.n = bytearray(), 0, 0

    def put(self, value, nbits):                      # LSB first (extra bits)
        self.acc |= value << self.n
        self.n += nbits
        while self.n >= 8:
            self.out.append(self.acc & 255)
            self.acc >>= 8
            self.n -= 8

    def huff(self, code, nbits):                      # Huffman codes go MSB first
        self.put(int(format(code, f"0{nbits}b")[::-1], 2), nbits)

    def finish(self):
        if self.n:
            self.out.append(self.acc & 255)
        return bytes(self.out)


def lit_code(b):
    return (0x30 + b, 8) if b < 144 else (0x190 + b - 144, 9)


def deflate_fixed(data):
    bw = Bits()
    bw.put(1, 1)
    bw.put(1, 2)                                       # final block, fixed Huffman
    i, n = 0, len(data)
    while i < n:
        j = i
        if i and data[i] == data[i - 1]:
            while j < n and j - i < 258 and data[j] == data[i - 1]:
                j += 1
        run = j - i
        if run >= 3:
            k = max(x for x in range(len(LEN_BASE)) if LEN_BASE[x] <= run)
            sym = 257 + k
            bw.huff(sym - 256, 7) if sym < 280 else bw.huff(0xC0 + sym - 280, 8)
            if LEN_EXTRA[k]:
                bw.put(run - LEN_BASE[k], LEN_EXTRA[k])
            bw.huff(0, 5)                              # distance 1
            i += run
        else:
            bw.huff(*lit_code(data[i]))
            i += 1
    bw.huff(0, 7)                                      # end of block
    return bw.finish()


def png_chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


def encode(cv):
    raw, prev = bytearray(), bytes(W)
    for row in cv:
        raw.append(2)                                  # filter "Up"
        raw += bytes((a - b) & 255 for a, b in zip(row, prev))
        prev = bytes(row)
    z = (b"\x78\x01" + deflate_fixed(bytes(raw))
         + struct.pack(">I", zlib.adler32(bytes(raw)) & 0xFFFFFFFF))
    pal = b"".join(bytes(c) for c in PALETTE)
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 3, 0, 0, 0))
            + png_chunk(b"PLTE", pal) + png_chunk(b"IDAT", z) + png_chunk(b"IEND", b""))


if __name__ == "__main__":
    data = encode(draw())
    with io.open(os.path.join(ROOT, "og.png"), "wb") as fh:
        fh.write(data)
    print(f"og.png {len(data)//1024} KB")
