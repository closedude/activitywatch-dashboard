"""Icons: Phosphor Icons, duotone weight, embedded inline in the HTML.

The files live in assets/icons/ — only the ones actually used, copied
from the phosphor-icons/core set (assets/duotone/). MIT licence —
licenses/phosphor.txt. While the report is built the SVG is read from
disk and inserted into the HTML as is, so the report stays self-contained.

An icon is a plate (span.plate) with a glyph inside:
  • glyph: outline in the category colour at full strength, the second
    duotone layer in the same colour with DUOTONE_ALPHA transparency;
  • plate: the card glass effect in miniature (edge, highlight, shading
    — styles in report.py) and a background faintly tinted with the
    category colour (--tint, TINT_ALPHA transparency).

Line weight. In Phosphor the outline is filled shapes on a 256 grid,
not a stroke, so the line scales together with the icon and never gets
thicker on its own: 16 units of 256, i.e. 1/16 of the glyph size. The
glyph takes GLYPH_SCALE of the plate: a 20px plate has a 16px glyph and
a 1.0px line, a 30px plate a 1.5px line. No stroke or vector-effect is
added anywhere.

Colour is set via style, not the fill attribute: var() in a
presentation attribute does not work in every engine, in CSS it does.
"""

import re
from pathlib import Path

import config

ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"

# Category -> Phosphor file (without the -duotone.svg suffix). Category
# names are user data from categories.json, so both the Ukrainian starter
# set and the English demo names are listed; any other name gets FALLBACK.
CATEGORY_ICONS = {
    "Ігри": "game-controller",
    "Браузер": "globe",
    "Робота/Розробка": "code",
    "Спілкування": "chat-circle-dots",
    "Розваги": "play-circle",
    "Системні": "sliders-horizontal",
    "Games": "game-controller",
    "Browser": "globe",
    "Work/Dev": "code",
    "Communication": "chat-circle-dots",
    "Entertainment": "play-circle",
    "System": "sliders-horizontal",
    config.CATEGORY_OTHER: "stack",
    config.UNCATEGORIZED: "dots-three-circle",
}

# For hand-added categories that have no icon yet.
FALLBACK = "tag"

# Layout icons: section headings, KPI cards, the header.
UI_ICONS = {
    "chart": "chart-bar",          # logo, "Top applications"
    "trend": "trend-up",           # "Activity over the last 30 days", "Average per day"
    "layers": "chart-pie-slice",   # "Categories" (stack is already "Other")
    "games": "game-controller",    # "Games"
    "grid": "squares-four",        # "When you are active"
    "focus": "target",             # "Attention fragmentation"
    "moon": "moon",                # "Daily rhythm"
    "stopwatch": "timer",          # "Longest sessions"
    "calendar": "calendar-blank",  # "By month"
    "clock": "clock",              # "Active time"
    "idle": "power",               # "Computer-on time"
}

DUOTONE_ALPHA = 0.3   # second duotone layer
TINT_ALPHA = 0.10     # plate tint in the category colour (see the contrast note in CLAUDE.md)
GLYPH_SCALE = 0.8     # share of the plate taken by the glyph

# Plate shape (config.ICON_SHAPE). The rounded_square radius matches the
# former backing rect rx=7 of 24, i.e. 29%. A hexagon cannot be repeated
# by a border radius — it is cut with clip-path.
SHAPE_RADIUS = {"circle": "50%", "rounded_square": "29%", "squircle": "38%"}
HEXAGON_CLIP = "polygon(50% 0, 96% 25%, 96% 75%, 50% 100%, 4% 75%, 4% 25%)"


_cache = {}


def _glyph(name):
    """Inside of a Phosphor SVG: the paths, with the second layer's opacity."""
    if name not in _cache:
        svg = (ICON_DIR / f"{name}-duotone.svg").read_text(encoding="utf-8")
        inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
        _cache[name] = re.sub(r'opacity="0\.2"', f'opacity="{DUOTONE_ALPHA}"', inner)
    return _cache[name]


def used_files():
    """File names referenced by the mappings — for checks."""
    return sorted({*CATEGORY_ICONS.values(), *UI_ICONS.values(), FALLBACK})


def glyph_svg(name, color, size):
    """A bare glyph without a plate — for places that need no plate."""
    # Size both in attributes and in style: the report's global
    # svg { width: 100% } would otherwise stretch the glyph, and the line
    # with it.
    return (
        f'<svg class="glyph" viewBox="0 0 256 256" width="{size:g}" '
        f'height="{size:g}" aria-hidden="true" focusable="false" '
        f'style="fill:{color};width:{size:g}px;height:{size:g}px">'
        f'{_glyph(name)}</svg>'
    )


def _plate(name, color, size):
    glyph = round(size * GLYPH_SCALE, 1)
    shape = (f"clip-path:{HEXAGON_CLIP};" if config.ICON_SHAPE == "hexagon" else "")
    return (
        f'<span class="plate cat-icon" style="--tint:{color};width:{size}px;'
        f'height:{size}px;{shape}">{glyph_svg(name, color, glyph)}</span>'
    )


def icon(category, color, size=20):
    """Category icon in a plate. color is usually var(--cat-N)."""
    return _plate(CATEGORY_ICONS.get(category, FALLBACK), color, size)


def ui_icon(name, color, size=18, backing=True):
    """Layout icon: in a plate or, with backing=False, a bare glyph."""
    file = UI_ICONS.get(name, FALLBACK)
    if not backing:
        return glyph_svg(file, color, size)
    return _plate(file, color, size)


def plate_radius():
    return SHAPE_RADIUS.get(config.ICON_SHAPE, "0")


def available_shapes():
    return (*SHAPE_RADIUS, "hexagon")
