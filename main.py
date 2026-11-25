#!/usr/bin/env python3
"""Draw a newspaper front page summing up Wednesday 25 November 2026.

Pure standard library: renders the page into an RGB buffer with a small
built-in 5x7 bitmap font, then encodes it as a PNG. No network, no files
read, no timestamps anywhere, so two runs produce identical bytes.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (22, 22, 22)
NAVY = (20, 38, 74)
GOLD = (198, 158, 40)
RED = (172, 32, 32)
TEAL = (18, 110, 105)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
RULE = (190, 182, 160)
MUTED = (90, 86, 76)

# ---------------------------------------------------------------- font ----
# Each glyph: 7 rows of 5 pixels, '#' on, '.' off. Uppercase + digits +
# the punctuation the page uses. All page text is set in capitals.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "..#..", ".#...", "#..##", "#..##", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (1px gap between glyphs)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d <= r * r:
                    self.set(xx, yy, color)
                elif not fill and abs(d - r * r) <= r:
                    self.set(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Scanline fill of a triangle.
        ys = sorted([y0, y1, y2])
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by) or y == ys[2]:
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                for x in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(x, y, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, y, s, scale, color):
        self.text((self.w - text_width(s, scale)) // 2, y, s, scale, color)


# -------------------------------------------------------------- icons -----
def draw_icon(cv, x, y, kind, color):
    """A small pictogram in a 56x56 box at (x, y)."""
    if kind == "mountain":  # Aden: ridges under a flag
        cv.triangle(x + 4, y + 48, x + 22, y + 16, x + 40, y + 48, color)
        cv.triangle(x + 20, y + 48, x + 38, y + 26, x + 52, y + 48, color)
        cv.vline(x + 50, y + 6, 22, color)
        cv.rect(x + 50, y + 6, 12, 8, RED)
    elif kind == "coin":  # Ukraine: a coin
        cv.circle(x + 28, y + 28, 22, color, fill=False)
        cv.circle(x + 28, y + 28, 17, color, fill=False)
        cv.hline(x + 18, y + 24, 20, color)
        cv.hline(x + 18, y + 32, 20, color)
        cv.rect(x + 26, y + 20, 4, 16, color)
    elif kind == "building":  # China: a tower block
        cv.rect(x + 14, y + 8, 28, 44, color)
        for wy in (16, 26, 36):
            for wx in (20, 28, 36):
                cv.rect(x + wx, y + wy, 5, 6, PAPER)
        cv.rect(x + 22, y + 44, 12, 8, color)
    elif kind == "flag":  # North Korea: a flag on a pole
        cv.vline(x + 10, y + 6, 46, color)
        cv.rect(x + 10, y + 8, 38, 22, color)
        cv.rect(x + 10, y + 8, 38, 4, RED)
        cv.circle(x + 29, y + 19, 5, WHITE, fill=True)
    elif kind == "factory":  # Bangladesh: a garment factory
        cv.rect(x + 6, y + 30, 44, 22, color)
        cv.rect(x + 6, y + 22, 12, 8, color)
        cv.rect(x + 20, y + 22, 12, 8, color)
        cv.rect(x + 34, y + 22, 12, 8, color)
        cv.rect(x + 42, y + 6, 6, 20, color)
        for wx in (12, 24, 36):
            cv.rect(x + wx, y + 38, 6, 7, PAPER)
    elif kind == "helmet":  # Indonesia: a miner's helmet
        cv.circle(x + 28, y + 30, 20, color, fill=True)
        cv.rect(x + 4, y + 30, 48, 6, color)
        cv.rect(x + 24, y + 8, 8, 8, GOLD)


# -------------------------------------------------------------- stories ----
# (kicker, headline, body, icon, accent, first-reported UTC)
STORIES = [
    ("YEMEN", "HOUTHIS ADVANCE ON ADEN",
     "Fighters encircle the temporary capital as residents and NGOs prepare to flee.",
     "mountain", RED, "00:00"),
    ("UKRAINE", "KYIV NEEDS 115BN EUROS",
     "Zelensky says 2027 will need EUR 115bn in outside help; EUR 90bn is secured.",
     "coin", TEAL, "01:19"),
    ("CHINA", "SHANGHAI CHIEF PROBED",
     "Party boss Chen Jining investigated for graft, the fourth politburo member since 2025.",
     "building", RED, "01:31"),
    ("NORTH KOREA", "SWISS OFFICE SHUT",
     "Pyongyang orders Switzerland's new office closed and expels its head in 48 hours.",
     "flag", NAVY, "04:50"),
    ("BANGLADESH", "GARMENT PAY UP 36%",
     "Minimum wage rises to 17,000 taka after weeks of protests; workers wanted 30,000.",
     "factory", TEAL, "06:01"),
    ("INDONESIA", "MINERS TRAPPED",
     "Dozens missing in a flooded gold mine in West Java after heavy rain swamped the shaft.",
     "helmet", NAVY, "08:08"),
]

ALSO = ("ALSO TODAY: COLOMBIA FREES ALL HOSTAGES IN CARTAGENA - SAUDI COALITION "
        "HITS HODEIDAH PORT - UK WARNS FIRMS OF RUSSIAN SABOTAGE - SIX DIE IN "
        "GULF OF MEXICO PLANE CRASH - PAKISTAN'S FIRST ASTRONAUT REACHES "
        "CHINA'S SPACE STATION")


def draw_card(cv, x, y, w, h, story):
    kicker, headline, body, icon, accent, reported = story
    cv.rect(x, y, w, h, CARD)
    cv.rect(x, y, w, 3, accent)
    # thin border
    cv.hline(x, y + h - 1, w, RULE)
    cv.vline(x, y, h, RULE)
    cv.vline(x + w - 1, y, h, RULE)
    cv.hline(x, y, w, RULE)
    # kicker + icon
    cv.text(x + 18, y + 16, kicker, 2, accent)
    draw_icon(cv, x + w - 74, y + 10, icon, accent)
    # headline, wrapped, up to 2 lines; kept clear of the icon
    lines = wrap(headline, w - 110, 3)
    hy = y + 44
    for line in lines[:2]:
        cv.text(x + 18, hy, line, 3, INK)
        hy += 26
    # body
    by = hy + 8
    for line in wrap(body, w - 36, 2)[:3]:
        cv.text(x + 18, by, line, 2, MUTED)
        by += 20
    # first-reported time
    cv.text(x + 18, by + 10, "FIRST REPORTED " + reported + " UTC", 2, accent)


def build():
    cv = Canvas(W, H, PAPER)
    # header band
    cv.rect(0, 0, W, 148, NAVY)
    cv.text_center(26, "THE WORLD IN ONE DAY", 6, WHITE)
    cv.hline(212, 96, 600, GOLD)
    cv.text_center(110, "WEDNESDAY 25 NOVEMBER 2026", 3, GOLD)
    # standfirst
    cv.text_center(164, "SIX STORIES FROM AROUND THE GLOBE, AS FIRST REPORTED TODAY",
                   2, INK)
    # cards: 2 columns x 3 rows
    cw, ch, gx, gy = 480, 244, 24, 196
    for i, story in enumerate(STORIES):
        cx = gx + (i % 2) * (cw + 16)
        cy = gy + (i // 2) * (ch + 12)
        draw_card(cv, cx, cy, cw, ch, story)
    # footer
    fy = 952
    cv.hline(24, fy, W - 48, NAVY)
    for line in wrap(ALSO, W - 48, 2):
        cv.text(24, fy + 10, line, 2, INK)
        fy += 20
    return cv


# -------------------------------------------------------------- png --------
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
