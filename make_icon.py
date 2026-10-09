"""Generates dashboard.ico — the shortcut's own icon.

No external dependencies: an ICO is a header plus frames in BMP format,
which are easy to assemble by hand with struct. We draw in normalized
[0,1] coordinates and render each size separately with supersampling, so
the edges are not jagged even at 16 pixels.

Same design as the dashboard: a dark rounded square and four bars going
from blue to teal.

    python make_icon.py
"""

import struct
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 128, 256)
SUPERSAMPLE = 4

BORDER = (0x2F, 0x35, 0x42)
PANEL = (0x17, 0x1A, 0x21)
ACCENT_A = (0x6A, 0xA6, 0xFF)   # blue
ACCENT_B = (0x4D, 0xE0, 0xC0)   # teal

# Bars: (left edge, width, height) as fractions of the side.
BARS = (
    (0.115, 0.155, 0.26),
    (0.305, 0.155, 0.42),
    (0.495, 0.155, 0.56),
    (0.685, 0.155, 0.72),
)
BASELINE = 0.845
BAR_RADIUS = 0.028


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def in_rrect(u, v, x0, y0, x1, y1, radius):
    """Whether a point lies inside a rectangle with rounded corners."""
    dx = max(x0 + radius - u, 0.0, u - (x1 - radius))
    dy = max(y0 + radius - v, 0.0, v - (y1 - radius))
    return dx * dx + dy * dy <= radius * radius


def color_at(u, v):
    """(r, g, b, alpha) at a point. alpha 0 means transparent."""
    if not in_rrect(u, v, 0.02, 0.02, 0.98, 0.98, 0.20):
        return (0, 0, 0, 0.0)

    for i, (x, width, height) in enumerate(BARS):
        top = BASELINE - height
        if in_rrect(u, v, x, top, x + width, BASELINE, BAR_RADIUS):
            across = i / (len(BARS) - 1)
            # Slight darkening towards the bottom so the bar is not flat.
            depth = (v - top) / max(height, 1e-6)
            return mix(mix(ACCENT_A, ACCENT_B, across), (0x2E, 0x5E, 0x9E),
                       depth * 0.35) + (1.0,)

    if not in_rrect(u, v, 0.055, 0.055, 0.945, 0.945, 0.165):
        return BORDER + (1.0,)
    return PANEL + (1.0,)


def render(size):
    """BGRA rows, top to bottom."""
    rows = []
    step = 1.0 / (size * SUPERSAMPLE)
    for y in range(size):
        row = bytearray()
        for x in range(size):
            r = g = b = a = 0.0
            for sy in range(SUPERSAMPLE):
                v = (y * SUPERSAMPLE + sy + 0.5) * step
                for sx in range(SUPERSAMPLE):
                    u = (x * SUPERSAMPLE + sx + 0.5) * step
                    cr, cg, cb, ca = color_at(u, v)
                    # Premultiply, otherwise a dark fringe shows up at the edges.
                    r += cr * ca
                    g += cg * ca
                    b += cb * ca
                    a += ca
            samples = SUPERSAMPLE * SUPERSAMPLE
            if a > 0:
                row += bytes((round(b / a), round(g / a), round(r / a),
                              round(255 * a / samples)))
            else:
                row += b"\0\0\0\0"
        rows.append(bytes(row))
    return rows


def bmp_frame(size, rows):
    """An ICO frame in BMP format: header, pixels bottom to top, mask."""
    header = struct.pack(
        "<IiiHHIIiiII",
        40,          # header size
        size,
        size * 2,    # doubled height: XOR image plus AND mask
        1,           # planes
        32,          # bits per pixel
        0,           # no compression
        size * size * 4,
        0, 0, 0, 0,
    )
    pixels = b"".join(reversed(rows))
    # A transparency mask is not needed at 32 bits, but must be present.
    mask_row = ((size + 31) // 32) * 4
    mask = b"\0" * (mask_row * size)
    return header + pixels + mask


def build(path):
    frames = [(size, bmp_frame(size, render(size))) for size in SIZES]

    out = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    offset = 6 + 16 * len(frames)
    for size, data in frames:
        out += struct.pack(
            "<BBBBHHII",
            size if size < 256 else 0,
            size if size < 256 else 0,
            0, 0, 1, 32,
            len(data),
            offset,
        )
        offset += len(data)
    for _, data in frames:
        out += data

    path.write_bytes(bytes(out))
    return path, len(out), [s for s, _ in frames]


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "dashboard.ico"
    path, size, sizes = build(target)
    print(f"Icon: {path}")
    print(f"Sizes: {', '.join(f'{s}x{s}' for s in sizes)}   {size / 1024:.1f} KB")
