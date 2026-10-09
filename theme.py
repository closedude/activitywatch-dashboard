"""Themes, elevation and typography after Material Design 2.

Where the values come from:

* Palettes — "The color system", pp. 21–30: the exact hex values of the
  2014 palettes. No color here is made up; all are taken from those tables.
* Baseline colors — same article, pp. 8–9: background and surface #FFFFFF,
  error #B00020, the default "on" values #FFFFFF and #000000.
* Shadows — "Light and shadows": a shadow has two sources, key light and
  ambient light, and on the web it is offset along the Y axis only. The
  numbers for 2/6/12/24dp are given in the PDF only as pictures, so they
  are taken from the reference implementation, Material Components for
  Web, which describes exactly this model (umbra + penumbra + ambient).
* Surface lighting in dark themes — the same article says outright that
  shadows are less visible on dark surfaces. The white overlay percentages
  per level are taken from the Material Dark theme spec.
* Type scale — "The type system": the PDF text shows Headline 1 (Light
  300, 96px, letter spacing −1.5px), the list of weights
  Light/Regular/Medium and the rule for converting to rem (size/16). The
  remaining rows of the scale are images in the PDF, so they are filled in
  with the canonical Material 2 values.
"""

import colorsys

import config

# --------------------------------------------------------------------------
# 2014 palettes ("The color system", pp. 21–30)
# --------------------------------------------------------------------------

PALETTES = {
    "red": {50: "#FFEBEE", 100: "#FFCDD2", 200: "#EF9A9A", 300: "#E57373",
            400: "#EF5350", 500: "#F44336", 600: "#E53935", 700: "#D32F2F",
            800: "#C62828", 900: "#B71C1C"},
    "pink": {50: "#FCE4EC", 100: "#F8BBD0", 200: "#F48FB1", 300: "#F06292",
             400: "#EC407A", 500: "#E91E63", 600: "#D81B60", 700: "#C2185B",
             800: "#AD1457", 900: "#880E4F"},
    "purple": {50: "#F3E5F5", 100: "#E1BEE7", 200: "#CE93D8", 300: "#BA68C8",
               400: "#AB47BC", 500: "#9C27B0", 600: "#8E24AA", 700: "#7B1FA2",
               800: "#6A1B9A", 900: "#4A148C"},
    "deep_purple": {50: "#EDE7F6", 100: "#D1C4E9", 200: "#B39DDB",
                    300: "#9575CD", 400: "#7E57C2", 500: "#673AB7",
                    600: "#5E35B1", 700: "#512DA8", 800: "#4527A0",
                    900: "#311B92"},
    "indigo": {50: "#E8EAF6", 100: "#C5CAE9", 200: "#9FA8DA", 300: "#7986CB",
               400: "#5C6BC0", 500: "#3F51B5", 600: "#3949AB", 700: "#303F9F",
               800: "#283593", 900: "#1A237E"},
    "blue": {50: "#E3F2FD", 100: "#BBDEFB", 200: "#90CAF9", 300: "#64B5F6",
             400: "#42A5F5", 500: "#2196F3", 600: "#1E88E5", 700: "#1976D2",
             800: "#1565C0", 900: "#0D47A1"},
    "light_blue": {50: "#E1F5FE", 100: "#B3E5FC", 200: "#81D4FA",
                   300: "#4FC3F7", 400: "#29B6F6", 500: "#03A9F4",
                   600: "#039BE5", 700: "#0288D1", 800: "#0277BD",
                   900: "#01579B"},
    "cyan": {50: "#E0F7FA", 100: "#B2EBF2", 200: "#80DEEA", 300: "#4DD0E1",
             400: "#26C6DA", 500: "#00BCD4", 600: "#00ACC1", 700: "#0097A7",
             800: "#00838F", 900: "#006064"},
    "teal": {50: "#E0F2F1", 100: "#B2DFDB", 200: "#80CBC4", 300: "#4DB6AC",
             400: "#26A69A", 500: "#009688", 600: "#00897B", 700: "#00796B",
             800: "#00695C", 900: "#004D40"},
    "green": {50: "#E8F5E9", 100: "#C8E6C9", 200: "#A5D6A7", 300: "#81C784",
              400: "#66BB6A", 500: "#4CAF50", 600: "#43A047", 700: "#388E3C",
              800: "#2E7D32", 900: "#1B5E20"},
    "light_green": {50: "#F1F8E9", 100: "#DCEDC8", 200: "#C5E1A5",
                    300: "#AED581", 400: "#9CCC65", 500: "#8BC34A",
                    600: "#7CB342", 700: "#689F38", 800: "#558B2F",
                    900: "#33691E"},
    "yellow": {50: "#FFFDE7", 100: "#FFF9C4", 200: "#FFF59D", 300: "#FFF176",
               400: "#FFEE58", 500: "#FFEB3B", 600: "#FDD835", 700: "#FBC02D",
               800: "#F9A825", 900: "#F57F17"},
    "amber": {50: "#FFF8E1", 100: "#FFECB3", 200: "#FFE082", 300: "#FFD54F",
              400: "#FFCA28", 500: "#FFC107", 600: "#FFB300", 700: "#FFA000",
              800: "#FF8F00", 900: "#FF6F00"},
    "orange": {50: "#FFF3E0", 100: "#FFE0B2", 200: "#FFCC80", 300: "#FFB74D",
               400: "#FFA726", 500: "#FF9800", 600: "#FB8C00", 700: "#F57C00",
               800: "#EF6C00", 900: "#E65100"},
    "deep_orange": {50: "#FBE9E7", 100: "#FFCCBC", 200: "#FFAB91",
                    300: "#FF8A65", 400: "#FF7043", 500: "#FF5722",
                    600: "#F4511E", 700: "#E64A19", 800: "#D84315",
                    900: "#BF360C"},
    "brown": {50: "#EFEBE9", 100: "#D7CCC8", 200: "#BCAAA4", 300: "#A1887F",
              400: "#8D6E63", 500: "#795548", 600: "#6D4C41", 700: "#5D4037",
              800: "#4E342E", 900: "#3E2723"},
    "gray": {50: "#FAFAFA", 100: "#F5F5F5", 200: "#EEEEEE", 300: "#E0E0E0",
             400: "#BDBDBD", 500: "#9E9E9E", 600: "#757575", 700: "#616161",
             800: "#424242", 900: "#212121"},
    "blue_gray": {50: "#ECEFF1", 100: "#CFD8DC", 200: "#B0BEC5",
                  300: "#90A4AE", 400: "#78909C", 500: "#607D8B",
                  600: "#546E7A", 700: "#455A64", 800: "#37474F",
                  900: "#263238"},
}

WHITE = "#FFFFFF"
BLACK = "#000000"
BASELINE_ERROR = "#B00020"          # p. 8 of the PDF


def tone(palette, level):
    return PALETTES[palette][level]


# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------
#
# In dark themes primary comes from the light tones (200–300), as Material
# Dark theme prescribes: a saturated 500 on a dark background loses its
# lightness and gives no text contrast. For the same reason on-primary is
# black there.
#
# The background of dark themes is the neutral 900 tones of the Gray and
# Blue Grey palettes. Themes with the same background differ in accents and
# in the tint of raised surfaces: each level mixes in the primary color.

THEMES = [
    {
        "id": "indigo-teal",
        "name": "Indigo + Teal",
        "mode": "dark",
        "primary": tone("indigo", 200),
        "primary_variant": tone("indigo", 400),
        "secondary": tone("teal", 200),
        "secondary_variant": tone("teal", 400),
        "background": tone("gray", 900),
        "surface": tone("gray", 900),
        "error": tone("red", 200),
        "categories": [
            tone("indigo", 200), tone("teal", 200), tone("amber", 300),
            tone("pink", 300), tone("light_blue", 300), tone("light_green", 300),
        ],
        "cat_other": tone("gray", 300),
        "cat_uncategorized": tone("gray", 500),
    },
    {
        "id": "deep-purple-amber",
        "name": "Deep Purple + Amber",
        "mode": "dark",
        "primary": tone("deep_purple", 200),
        "primary_variant": tone("deep_purple", 400),
        "secondary": tone("amber", 300),
        "secondary_variant": tone("amber", 600),
        "background": tone("gray", 900),
        "surface": tone("gray", 900),
        "error": tone("red", 200),
        "categories": [
            tone("deep_purple", 200), tone("amber", 300), tone("cyan", 300),
            tone("pink", 300), tone("light_green", 300), tone("red", 300),
        ],
        "cat_other": tone("gray", 300),
        "cat_uncategorized": tone("gray", 500),
    },
    {
        "id": "blue-grey-cyan",
        "name": "Blue Grey + Cyan",
        "mode": "dark",
        "primary": tone("blue_gray", 200),
        "primary_variant": tone("blue_gray", 400),
        "secondary": tone("cyan", 300),
        "secondary_variant": tone("cyan", 600),
        "background": tone("blue_gray", 900),
        "surface": tone("blue_gray", 900),
        # This theme has the lightest surfaces of the dark ones, so error is
        # lighter too: Red 200 gave only 3.92:1 here.
        "error": tone("red", 100),
        # The cards here are the lightest of the dark themes, and the empty
        # heatmap cell is itself bluish grey: the first level of the shared
        # scale was only ΔE 6.1 away from it. A darker and slightly more
        # saturated level gives 13.1 / 11.2 (light / dark zone) and stays
        # darker and less saturated than level 2, so the scale holds.
        "heat_first": (-9, 0.30, 0.20),
        "categories": [
            tone("blue_gray", 200), tone("cyan", 300), tone("amber", 300),
            tone("purple", 200), tone("light_green", 300), tone("deep_orange", 300),
        ],
        "cat_other": tone("gray", 300),
        "cat_uncategorized": tone("gray", 500),
    },
    {
        "id": "indigo-pink",
        "name": "Indigo + Pink",
        "mode": "light",
        "primary": tone("indigo", 500),
        "primary_variant": tone("indigo", 700),
        "secondary": tone("pink", 600),
        "secondary_variant": tone("pink", 800),
        "background": tone("gray", 50),
        "surface": WHITE,
        "error": BASELINE_ERROR,
        "categories": [
            # Amber 800 gives only 2.29:1 on white, so the warm slot is Orange 900.
            tone("indigo", 600), tone("pink", 600), tone("teal", 700),
            tone("orange", 900), tone("purple", 600), tone("light_green", 800),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 700),
    },
    {
        "id": "teal-deep-orange",
        "name": "Teal + Deep Orange",
        "mode": "light",
        "primary": tone("teal", 500),
        "primary_variant": tone("teal", 700),
        "secondary": tone("deep_orange", 600),
        "secondary_variant": tone("deep_orange", 800),
        "background": tone("gray", 50),
        "surface": WHITE,
        "error": BASELINE_ERROR,
        "categories": [
            # Here the warm slot is taken by Deep Orange, so Brown 500 is used
            # instead of yellow — otherwise two oranges would merge.
            tone("teal", 700), tone("deep_orange", 700), tone("indigo", 600),
            tone("brown", 500), tone("purple", 600), tone("light_blue", 700),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 700),
    },
    {
        "id": "brown-light-green",
        "name": "Brown + Light Green",
        "mode": "light",
        # This theme's background was already at the right level, so the
        # shared darkening of light themes does not apply. With the shift,
        # Light Green as an accent gave 3.00:1 at a 3.0 threshold — exactly
        # on the edge.
        "page_lift": 0.0,
        "primary": tone("brown", 500),
        "primary_variant": tone("brown", 700),
        "secondary": tone("light_green", 700),
        "secondary_variant": tone("light_green", 900),
        "background": tone("brown", 50),
        "surface": WHITE,
        "error": BASELINE_ERROR,
        "categories": [
            tone("brown", 600), tone("light_green", 800), tone("deep_orange", 700),
            tone("indigo", 600), tone("teal", 700), tone("purple", 600),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 700),
    },
]

# Monochrome themes: white background, one hue within a range of tones,
# no gradients. The flat flag turns gradient fills off — bars, columns and
# sparklines become solid.
#
# A monochrome scheme lacks tones for all the category slots: in Blue the
# 500–900 range gives only five values, in Red 400–900 six. The remaining
# slots are covered by neutral greys, which belong to a monochrome palette
# and bring in no foreign hue. Repeating the same blue twice would be
# worse: two categories would merge into one in the legend.

THEMES += [
    {
        "id": "blue-mono",
        "name": "Blue Mono",
        "mode": "light",
        "flat": True,
        "primary": tone("blue", 700),
        "primary_variant": tone("blue", 900),
        "secondary": tone("blue", 500),
        "secondary_variant": tone("blue", 800),
        "background": WHITE,
        "surface": WHITE,
        "error": BASELINE_ERROR,
        "categories": [
            tone("blue", 900), tone("blue", 500), tone("blue", 700),
            tone("blue", 600), tone("blue", 800),
            # Gray 500 gives only 2.68:1 on white, so the neutrals are darker.
            tone("gray", 800),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 600),
    },
    {
        "id": "red-mono",
        "name": "Red Mono",
        "mode": "light",
        "flat": True,
        "primary": tone("red", 700),
        "primary_variant": tone("red", 900),
        "secondary": tone("red", 500),
        "secondary_variant": tone("red", 800),
        "background": WHITE,
        "surface": WHITE,
        "error": BASELINE_ERROR,
        "categories": [
            tone("red", 900), tone("red", 500), tone("red", 700),
            tone("red", 400), tone("red", 800),
            # Gray 500 gives only 2.68:1 on white, so the neutrals are darker.
            tone("gray", 800),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 600),
    },
    {
        "id": "blue-red",
        "name": "Blue + Red",
        "mode": "light",
        "flat": True,
        "primary": tone("blue", 800),
        "primary_variant": tone("blue", 900),
        "secondary": tone("red", 700),
        "secondary_variant": tone("red", 900),
        "background": WHITE,
        "surface": WHITE,
        "error": BASELINE_ERROR,
        # The two hues alternate: neighbouring categories never share a color.
        "categories": [
            tone("blue", 800), tone("red", 600), tone("blue", 500),
            tone("red", 900), tone("blue", 600), tone("red", 400),
        ],
        "cat_other": tone("blue_gray", 400),
        "cat_uncategorized": tone("gray", 700),
    },
]

# Theme after a reference screenshot. The background is a dark, low
# saturation grey-blue (Blue Grey 900), not black. The only strong accent
# is violet; secondary is deliberately neutral so that the accent stays
# single. Surface overlays are smaller than usual: with them 60% white for
# secondary text still passes AA, with the usual ones it does not.
THEMES.append({
    "id": "midnight",
    "name": "Midnight",
    "mode": "dark",
    # Deep Purple 300 as an accent gave only 2.77:1 on the surface — too
    # little even for graphics, hence 200. The saturated 500 stays in the
    # banner.
    "primary": tone("deep_purple", 200),
    "primary_variant": tone("deep_purple", 500),
    "secondary": tone("blue_gray", 200),
    "secondary_variant": tone("blue_gray", 400),
    "background": tone("blue_gray", 900),
    "surface": tone("blue_gray", 900),
    "error": tone("red", 200),
    "emphasis": {"high": 0.87, "medium": 0.60, "divider": 0.10},
    "overlay": {2: 0.040, 6: 0.060, 12: 0.075, 24: 0.085},
    "tint": {2: 0.025, 6: 0.035, 12: 0.045, 24: 0.050},

    # --- Special background after the reference ------------------------
    # The scheme is inverted relative to the other themes: the background
    # is lighter than the cards. The numbers were picked with an eyedropper
    # from the reference screenshot, not chosen by eye:
    #   dark corner, top left     #090D18  H 224  S 46  L  6.5
    #   light zone, bottom left   #7D7B89  H 249  S  6  L 51.0
    #   bright zone, right        #CBC2D4  H 270  S 17  L 79.6
    # (width, height, x%, y%, hue, saturation, lightness, alpha, stop%)
    "ambient_base": (240, 0.075, 0.44),
    "ambient_zones": [
        (1700, 1200, 94, 6, 270, 0.17, 0.80, 0.95, 64),
        (1200, 1000, 4, 94, 249, 0.07, 0.52, 0.88, 62),
        (1400, 1100, 2, 2, 224, 0.46, 0.065, 0.96, 60),
    ],
    # No vignette: the dark corner of the reference already plays its role.
    "ambient_vignette": None,
    # The lightness budget does not apply here — the wide range is intended.
    "ambient_budget": None,

    # A card is dense dark glass, not a see-through film: the blurred light
    # zone shows through, but the text lies on a dark surface. The density
    # is chosen so that the audit passes even where a card covers the
    # brightest zone of the background.
    "glass_veil": "#12131C",
    "glass_alpha": {2: 0.90, 6: 0.915, 12: 0.93, 24: 0.945},
    # The heatmap scale is set by hand; HEAT_LADDER for the other themes
    # was derived from it. Levels 1–5 and the peak.
    "heat": ["#3B3552", "#4C3F7E", "#6650B4", "#8668DE", "#A98BF2", "#EFE6FF"],
    "categories": [
        tone("deep_purple", 200), tone("blue_gray", 200), tone("amber", 300),
        tone("pink", 300), tone("cyan", 300), tone("light_green", 300),
    ],
    # Gray 600 gave exactly 3.00:1 here — no margin, hence 500 (5.16:1).
    "cat_other": tone("gray", 300),
    "cat_uncategorized": tone("gray", 500),
})

THEME_BY_ID = {t["id"]: t for t in THEMES}


# --------------------------------------------------------------------------
# Elevation
# --------------------------------------------------------------------------
#
# Shadow = umbra + penumbra + ambient, offset along Y only ("Light and shadows").
ELEVATION_SHADOWS = {
    2: ("0 3px 1px -2px rgba(0,0,0,.20), 0 2px 2px 0 rgba(0,0,0,.14), "
        "0 1px 5px 0 rgba(0,0,0,.12)"),
    6: ("0 3px 5px -1px rgba(0,0,0,.20), 0 6px 10px 0 rgba(0,0,0,.14), "
        "0 1px 18px 0 rgba(0,0,0,.12)"),
    12: ("0 7px 8px -4px rgba(0,0,0,.20), 0 12px 17px 2px rgba(0,0,0,.14), "
         "0 5px 22px 4px rgba(0,0,0,.12)"),
    24: ("0 11px 15px -7px rgba(0,0,0,.20), 0 24px 38px 3px rgba(0,0,0,.14), "
         "0 9px 46px 8px rgba(0,0,0,.12)"),
}

# How much white is mixed into the surface at each level in a dark theme.
DARK_OVERLAY = {2: 0.07, 6: 0.11, 12: 0.14, 24: 0.16}

# How much primary is mixed in on top — so that themes with the same
# background differ on raised surfaces.
DARK_TINT = {2: 0.03, 6: 0.05, 12: 0.06, 24: 0.07}

ELEVATIONS = (2, 6, 12, 24)


def to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(c))) for c in rgb))


def blend(base, over, amount):
    """Mixes base with over in proportion amount (0..1)."""
    a, b = to_rgb(base), to_rgb(over)
    return to_hex(tuple(x + (y - x) * amount for x, y in zip(a, b)))


def to_hsl(color):
    """(hue 0..360, saturation 0..1, lightness 0..1)."""
    r, g, b = (c / 255 for c in to_rgb(color))
    high, low = max(r, g, b), min(r, g, b)
    lightness = (high + low) / 2
    if high == low:
        return 0.0, 0.0, lightness

    span = high - low
    saturation = (
        span / (2 - high - low) if lightness > 0.5 else span / (high + low)
    )
    if high == r:
        hue = ((g - b) / span) % 6
    elif high == g:
        hue = (b - r) / span + 2
    else:
        hue = (r - g) / span + 4
    return hue * 60, saturation, lightness


def from_hsl(hue, saturation, lightness):
    hue = hue % 360
    saturation = max(0.0, min(1.0, saturation))
    lightness = max(0.0, min(1.0, lightness))

    chroma = (1 - abs(2 * lightness - 1)) * saturation
    second = chroma * (1 - abs((hue / 60) % 2 - 1))
    offset = lightness - chroma / 2

    sector = int(hue // 60) % 6
    table = [
        (chroma, second, 0), (second, chroma, 0), (0, chroma, second),
        (0, second, chroma), (second, 0, chroma), (chroma, 0, second),
    ]
    r, g, b = table[sector]
    return to_hex(((r + offset) * 255, (g + offset) * 255, (b + offset) * 255))


def lightness_of(color):
    return to_hsl(color)[2]


def surface_at(theme, elevation):
    """Surface at a given elevation.

    Dark theme: the higher the level, the lighter the surface — a shadow on
    a dark background barely reads, so lighting carries the depth.
    Light theme: the surface stays white, the shadow carries the depth.

    A theme may set its own overlay/tint if the usual steps make surfaces
    too light for its text opacity levels.
    """
    if theme["mode"] == "light":
        return theme["surface"]
    overlay = theme.get("overlay", DARK_OVERLAY)[elevation]
    tint = theme.get("tint", DARK_TINT)[elevation]
    lifted = blend(theme["surface"], WHITE, overlay)
    return blend(lifted, theme["primary"], tint)


def fit_contrast(color, ink, target=4.5, steps=60, alpha=1.0):
    """Darkens or lightens color until text in ink on it passes target.

    Used for the banner: the gradient is derived from the theme palette,
    but its ends are adjusted so that text stays readable at any point.
    Otherwise light palettes would give a banner the text drowns in.

    alpha is the opacity the text actually has on the background. Fit to
    the weakest level: if secondary text passes, full text passes all
    the more.
    """
    toward = BLACK if luminance(ink) > 0.5 else WHITE
    result = color
    for _ in range(steps):
        if contrast(over(ink, result, alpha), result) >= target:
            break
        result = blend(result, toward, 0.04)
    return result


# Opacity of the banner's secondary text and of the coverage bar track.
# Both derive from on-banner, so they work on light gradients too, where
# on-banner is black.
BANNER_SOFT = 0.82
# Lower than feels intuitive: the track must stay close to the banner
# background, otherwise it merges with the fill and the bar does not read.
BANNER_TRACK = 0.20


def banner_endpoints(theme):
    """(start, end, text color) of the banner, fitted for contrast.

    The only place where the banner ends are computed. The same logic once
    lived both here and in gradient_stops, the two drifted apart, and the
    audit checked colors other than the ones drawn.
    """
    if theme.get("flat"):
        # Monochrome themes stay without a transition: both ends are equal.
        base = theme["primary"]
        ink = on_color(base)
        fitted = fit_contrast(base, ink, alpha=BANNER_SOFT)
        return fitted, fitted, ink

    start, end = theme["primary_variant"], theme["secondary_variant"]
    ink = on_color(blend(start, end, 0.5))
    # Fit to the secondary text: it is the weakest on the banner.
    return (fit_contrast(start, ink, alpha=BANNER_SOFT),
            fit_contrast(end, ink, alpha=BANNER_SOFT), ink)


def gradients(theme):
    """Gradient tokens derived from the theme's primary and secondary.

    Returns (page background, banner, banner text color). For flat themes
    the gradient degenerates into a solid color — they are deliberately
    without transitions.
    """
    background = theme["background"]
    start, end, ink = banner_endpoints(theme)

    if theme.get("flat"):
        return background, start, ink

    # Background: a barely visible tint of the accents so the plane is not
    # dead. Deliberately weak — text reads across the whole area.
    strength = 0.14 if theme["mode"] == "dark" else 0.07
    corner_a = blend(background, theme["primary"], strength)
    corner_b = blend(background, theme["secondary"], strength * 0.6)
    page = (
        f"linear-gradient(160deg, {corner_a} 0%, {background} 45%, "
        f"{corner_b} 100%)"
    )

    banner = f"linear-gradient(120deg, {start} 0%, {end} 100%)"
    return page, banner, ink


# --------------------------------------------------------------------------
# Background spots and glass
# --------------------------------------------------------------------------
#
# Large-radius spots create light and dark zones along the page edges. In
# dark themes the light spots are white, in light themes dark: white
# highlights do not read on a light background at all.
#
# Each spot is tinted with the theme's primary or secondary, so every
# palette gets its own set rather than one for all.
#
# The zones are placed for the real report layout. The content is a
# 1180px-wide column in the centre, so the empty places are the strip
# behind the header at the top and the outer margins left and right of the
# column. That is where the zones aim; none falls under the dense text in
# the centre.
#
# (width, height, x%, y%, hue role, lightness shift, saturation, alpha, stop%)
AMBIENT_ZONES = {
    "dark": [
        # Behind the header, full width.
        (1500, 680, 50, -8, "primary", +0.022, 0.34, 0.85, 64),
        # Left outer margin.
        (820, 1100, -6, 34, "secondary", +0.016, 0.26, 0.75, 60),
        # Right outer margin, lower than the left one.
        (880, 1050, 106, 66, "primary", +0.012, 0.30, 0.70, 60),
    ],
    "light": [
        # In light themes the cards are almost white and the background a
        # little darker and tinted: the darkening is colored, in the
        # palette's hue.
        (1500, 680, 50, -8, "primary", -0.030, 0.26, 0.80, 64),
        (820, 1100, -6, 34, "secondary", -0.022, 0.22, 0.70, 60),
        (880, 1050, 106, 66, "primary", -0.018, 0.24, 0.65, 60),
    ],
}

# Vignette: transparent in the centre, darkening towards the edges and
# corners. The hue comes from primary, so the darkening is colored, not grey.
# (lightness shift, saturation, alpha, edge of the transparent core %)
VIGNETTE = {
    "dark": (-0.034, 0.24, 0.92, 46),
    "light": (-0.028, 0.14, 0.80, 52),
}

# Monochrome themes: the same principle, but weaker and without a second
# hue — otherwise they would stop being monochrome.
FLAT_AMBIENT_SCALE = 0.60

# Lightness shift of the page base relative to the theme background color.
# Dark themes were too dark and light ones too light, so the cards did not
# read as raised. The --background token is left alone: only what is
# actually drawn under the content is shifted.
PAGE_LIFT = {"dark": 0.055, "light": -0.038}

# Glass opacity at each elevation level. The gradation is kept: the higher
# the level, the denser the glass, so the depth step has not gone anywhere
# — it is expressed by density instead of a solid color.
#
# IMPORTANT about the veil color in dark themes. The canonical glass recipe
# is white at a few percent. It works while it is evenly dark under the
# card. As soon as a light background spot gets under it, the white lights
# the card up even more and the text sinks: in Midnight muted text gave
# 3.44:1 at a 4.5 threshold. Raising the white opacity only makes it worse,
# so "raise the opacity instead of removing the gradient" cannot work in
# that form.
#
# Hence in dark themes the veil is the theme's own background color, and
# only a thin highlight at the top stays white. The glass still lets the
# blurred background through, but brings light zones back to a workable
# brightness, and raising the opacity now really raises the contrast.
GLASS_ALPHA = {
    "dark": {2: 0.52, 6: 0.60, 12: 0.68, 24: 0.78},
    "light": {2: 0.58, 6: 0.66, 12: 0.74, 24: 0.84},
}

# White sheen over the veil: stronger at the top, fading downwards.
GLASS_SHEEN = {"dark": (0.075, 0.020), "light": (0.45, 0.10)}

# Card volume. The effect values are taken from a Google Stitch reference:
# edge white 0.16–0.18 at the top and 0.08 at the bottom, highlight
# inset 0 1px 1px white 0.35, shadow 0 16px 36px -10px black 0.45 plus
# 0 1px 2px black 0.2. The reference was made for a single dark theme, so
# for light themes the edge is semi-transparent dark (a white line does not
# show on a light background), while the top highlight stays white.
GLASS_EDGE = {           # (top, bottom): color and alpha
    "dark": ((WHITE, 0.18), (WHITE, 0.05)),
    "light": ((BLACK, 0.12), (BLACK, 0.05)),
}
GLASS_HIGHLIGHT = {"dark": 0.30, "light": 0.90}   # white alpha of the highlight
CARD_SHADE = {"dark": 0.30, "light": 0.05}        # black alpha of the bottom shade
CARD_SHADOW = {
    "dark": ("0 16px 36px -10px rgba(0,0,0,.45), "
             "0 4px 10px -4px rgba(0,0,0,.25), 0 1px 2px 0 rgba(0,0,0,.20)"),
    "light": ("0 14px 30px -12px rgba(0,0,0,.16), "
              "0 4px 10px -6px rgba(0,0,0,.10), 0 1px 2px 0 rgba(0,0,0,.06)"),
}
# Row highlight under the cursor: in the reference the background grows
# from white 0.045 to 0.075; here +0.05, because our cards are denser and
# +0.03 got lost. In light themes the background gets darker, not lighter.
ROW_HOVER = {"dark": (WHITE, 0.05), "light": (BLACK, 0.04)}
# The value in the hovered row gets brighter: lighter in dark themes,
# deeper in light ones (lightening there would eat the contrast).
VALUE_HOVER = {"dark": "brightness(1.25)", "light": "brightness(.8) saturate(1.15)"}

# Heatmap scale: --heat-1..5 and --heat-peak, one hue from the theme
# accent. The level bounds are computed by report.py from quantiles of the
# non-empty cells; only the colors are here.
#
# The anchor is the Midnight scale, set by hand (theme["heat"]). Broken
# down into HSL it gives the rule the other themes are built by:
#   hue        — the primary hue; dark levels slightly shifted (down to −9°);
#   saturation — grows from level to level: 0.22 → 1.00;
#   lightness  — grows: 0.27 → 0.95, the peak is the lightest.
# In light themes the logic is reversed: the empty cell is light, the levels
# darken and saturate, the peak is the darkest and most saturated.
# Empty heatmap cell. It used to be the shared --track (10%), and in
# Midnight its brightness almost matched the first level (1.07:1). Dark
# themes: white 20% — contrast to level 1 in Midnight 1.33:1; light themes:
# black 5% instead of 10% — lighter, further from level 1. A lighter empty
# cell inevitably matches one of levels 2–3 in brightness, so it differs in
# color too: neutral grey against saturated levels, ΔE ≥ 10 to levels 1–3
# in all themes (Midnight ≥ 17).
HEAT_EMPTY = {"dark": (WHITE, 0.20), "light": (BLACK, 0.05)}

HEAT_LADDER = {
    #          hue shift, saturation, lightness — for levels 1..5 and the peak
    "dark": ((-9, 0.215, 0.265), (-9, 0.333, 0.371), (-8, 0.400, 0.510),
             (-6, 0.641, 0.639), (-4, 0.798, 0.747), (0, 1.000, 0.951)),
    "light": ((-4, 0.450, 0.860), (-3, 0.520, 0.740), (-2, 0.580, 0.610),
              (-1, 0.650, 0.480), (0, 0.720, 0.370), (0, 0.880, 0.250)),
}

GLASS_BLUR = "blur(16px) saturate(120%)"


def rgba(color, alpha):
    r, g, b = to_rgb(color)
    return f"rgba({r},{g},{b},{alpha:.3f})"


def page_base(theme):
    """Base color of the page plane.

    Not the same as the --background token: that one stays the theme color
    and is used, for example, to outline chart points. This is what
    actually lies under the content, with the lightness shift.
    """
    if "ambient_base" in theme:
        return from_hsl(*theme["ambient_base"])
    hue, saturation, lightness = to_hsl(theme["background"])
    lift = theme.get("page_lift", PAGE_LIFT[theme["mode"]])
    return from_hsl(hue, saturation, lightness + lift)


def _zone_color(theme, role, shift, saturation):
    """Zone color: the role's hue, lightness almost as the background's.

    This is where the main principle lives: zones differ in hue and
    saturation, not brightness. Lightness comes from the theme background
    and shifts by a hair, so the contrast of text on top does not drift.
    """
    base_hue, base_saturation, base_lightness = to_hsl(page_base(theme))
    hue = to_hsl(theme[role])[0]
    if theme.get("flat"):
        # Monochrome theme: its own background hue, no foreign one.
        hue = to_hsl(theme["primary"])[0]
        saturation *= 0.7

    # If the zone hue is close to the background hue, the zone does not read:
    # lightness cannot be raised (budget), so saturation is boosted. This is
    # exactly the Blue Grey + Cyan case, where palette and background share
    # a hue.
    if base_saturation > 0.02:
        distance = abs(hue - base_hue)
        distance = min(distance, 360 - distance)
        if distance < 60:
            saturation *= 1 + (1 - distance / 60) * 1.2

    return from_hsl(hue, min(saturation, 0.72), base_lightness + shift)


def _zones(theme):
    """Background zones of a theme.

    A theme may set ambient_zones with absolute HSL — that is the case for
    Midnight, whose background was picked from a reference and is not
    derived from the palette by the general rule.
    """
    if "ambient_zones" in theme:
        return [
            (w, h, x, y, from_hsl(hue, saturation, lightness), alpha, stop)
            for w, h, x, y, hue, saturation, lightness, alpha, stop
            in theme["ambient_zones"]
        ]

    scale = FLAT_AMBIENT_SCALE if theme.get("flat") else 1.0
    out = []
    for w, h, x, y, role, shift, saturation, alpha, stop in AMBIENT_ZONES[theme["mode"]]:
        color = _zone_color(theme, role, shift * scale, saturation)
        out.append((w, h, x, y, color, alpha, stop))
    return out


def _vignette(theme):
    if "ambient_vignette" in theme:
        return theme["ambient_vignette"]

    shift, saturation, alpha, inner = VIGNETTE[theme["mode"]]
    scale = FLAT_AMBIENT_SCALE if theme.get("flat") else 1.0
    lightness = lightness_of(page_base(theme))
    # Hue from primary: the darkening is colored, not neutral grey.
    hue = to_hsl(theme["primary"])[0]
    color = from_hsl(hue, saturation, lightness + shift * scale)
    return color, alpha, inner


def noise_layer(opacity=0.042, size=160):
    """Noise over the background: removes banding on smooth gradients.

    Inline SVG in a data URI — no external request.

    opacity is multiplied by the turbulence's own alpha channel (about 0.5
    on average), so 0.042 gives roughly the 2% needed: the grain breaks up
    the steps but does not read by itself.
    """
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>"
        "<filter id='n' x='0' y='0' width='100%' height='100%'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.82' "
        "numOctaves='3' stitchTiles='stitch'/>"
        "<feColorMatrix type='saturate' values='0'/>"
        "</filter>"
        f"<rect width='100%' height='100%' filter='url(%23n)' "
        f"opacity='{opacity}'/></svg>"
    )
    encoded = (
        svg.replace("<", "%3C").replace(">", "%3E")
        .replace("#", "%23").replace('"', "'")
    )
    return f"url(\"data:image/svg+xml,{encoded}\")"


def ambient_css(theme):
    """The composed background: noise, zones, vignette, base color."""
    layers = [noise_layer()]
    layers += [
        f"radial-gradient({w}px {h}px at {x}% {y}%, "
        f"{rgba(color, alpha)}, transparent {stop}%)"
        for w, h, x, y, color, alpha, stop in _zones(theme)
    ]
    vignette = _vignette(theme)
    if vignette:
        color, alpha, inner = vignette
        layers.append(
            f"radial-gradient(farthest-side at 50% 42%, transparent {inner}%, "
            f"{rgba(color, alpha)} 100%)"
        )
    layers.append(page_base(theme))
    return ", ".join(layers)


def ambient_extremes(theme):
    """(lightest background point, darkest) — for contrast checks.

    The zones lie in different places and do not overlap at full strength,
    so the strongest single zone in each direction is taken.
    """
    base = page_base(theme)
    candidates = [blend(base, c, a) for _, _, _, _, c, a, _ in _zones(theme)]
    vignette = _vignette(theme)
    if vignette:
        color, alpha, _ = vignette
        candidates.append(blend(base, color, alpha))
    candidates.append(base)
    return (max(candidates, key=luminance), min(candidates, key=luminance))


def ambient_lightness_spread(theme):
    """How far the background lightness varies between extremes, in percent."""
    lightest, darkest = ambient_extremes(theme)
    return (lightness_of(lightest) - lightness_of(darkest)) * 100


def glass_veil(theme):
    """Glass veil color.

    A theme may set its own: in Midnight the background is lighter than
    the cards, so the veil there is not the background color but
    noticeably darker.
    """
    if "glass_veil" in theme:
        return theme["glass_veil"]
    return theme["background"] if theme["mode"] == "dark" else WHITE


def glass_alpha(theme, elevation):
    if "glass_alpha" in theme:
        return theme["glass_alpha"][elevation]
    return GLASS_ALPHA[theme["mode"]][elevation]


def glass_over(theme, page_color, elevation=6):
    """Actual card color: veil plus sheen over the background."""
    veiled = blend(page_color, glass_veil(theme), glass_alpha(theme, elevation))
    top, bottom = GLASS_SHEEN[theme["mode"]]
    # Take the middle of the sheen — text is spread over the whole card.
    return blend(veiled, WHITE, (top + bottom) / 2)


def heat_scale(theme):
    """Heatmap colors: levels 1–5 and the peak, one hue from primary.

    A theme may set the scale by hand (Midnight); otherwise it is built by
    HEAT_LADDER from the theme's primary hue.
    """
    if "heat" in theme:
        return list(theme["heat"])
    r, g, b = (c / 255 for c in to_rgb(theme["primary"]))
    hue, _, _ = colorsys.rgb_to_hls(r, g, b)
    ladder = list(HEAT_LADDER[theme["mode"]])
    if "heat_first" in theme:
        ladder[0] = theme["heat_first"]
    scale = []
    for shift, saturation, lightness in ladder:
        rgb = colorsys.hls_to_rgb((hue + shift / 360) % 1.0, lightness, saturation)
        scale.append("#" + "".join(f"{round(c * 255):02X}" for c in rgb))
    return scale


def gradient_stops(theme):
    """End colors of the gradients — for contrast checks.

    The banner ends come from banner_endpoints instead of being computed
    again: duplicated logic once drifted apart, and the audit checked
    colors other than the ones actually drawn.
    """
    background = theme["background"]
    start, end, _ = banner_endpoints(theme)

    if theme.get("flat"):
        return [page_base(theme)], [start]

    strength = 0.14 if theme["mode"] == "dark" else 0.07
    page = [
        blend(background, theme["primary"], strength),
        background,
        blend(background, theme["secondary"], strength * 0.6),
    ]
    return page, [start, end]


# --------------------------------------------------------------------------
# Contrast ("Accessible colors", pp. 10–11)
# --------------------------------------------------------------------------


def _channel(value):
    value /= 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(color):
    r, g, b = (_channel(c) for c in to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    lo, hi = sorted((la, lb))
    return (hi + 0.05) / (lo + 0.05)


def over(color, background, alpha):
    """A color with transparency laid over a background — for contrast checks."""
    return blend(background, color, alpha)


# --------------------------------------------------------------------------
# Theme roles
# --------------------------------------------------------------------------


def on_color(background):
    """Black or white over a color — whichever gives more contrast.

    This is what the PDF shows with check marks: a white mark means white
    text reads on that swatch, a black one means black.
    """
    return BLACK if contrast(background, BLACK) >= contrast(background, WHITE) else WHITE


# Material text emphasis levels: high and medium.
# medium in dark themes is raised from 0.70 to 0.75: on the lightest 24dp
# surface seventy percent white gave 4.45:1, just short of the AA threshold
# for normal text.
EMPHASIS = {
    "dark": {"high": 1.00, "medium": 0.75, "divider": 0.12},
    "light": {"high": 0.87, "medium": 0.60, "divider": 0.12},
}


# Green 300 gives only 4.19:1 on the lightest dark surfaces, hence 200.
POSITIVE = {"dark": ("green", 200), "light": ("green", 800)}


def roles(theme):
    """The full set of theme roles as {css variable: value}."""
    mode = theme["mode"]
    ink = WHITE if mode == "dark" else BLACK
    emphasis = theme.get("emphasis", EMPHASIS[mode])

    values = {
        "primary": theme["primary"],
        "primary-variant": theme["primary_variant"],
        "secondary": theme["secondary"],
        "secondary-variant": theme["secondary_variant"],
        "background": theme["background"],
        "surface": theme["surface"],
        "error": theme["error"],
        "on-primary": on_color(theme["primary"]),
        "on-secondary": on_color(theme["secondary"]),
        "on-background": on_color(theme["background"]),
        "on-surface": on_color(theme["surface"]),
        "on-error": on_color(theme["error"]),
    }

    # Green only for positive values — not for decoration.
    values["positive"] = tone(*POSITIVE[mode])

    page, banner, banner_ink = gradients(theme)
    values["gradient-page"] = page
    values["gradient-banner"] = banner
    values["on-banner"] = banner_ink
    # The banner's secondary text and the coverage bar derive from on-banner
    # too, since it can be white or black depending on gradient brightness.
    values["on-banner-soft"] = rgba(banner_ink, BANNER_SOFT)
    values["banner-track"] = rgba(banner_ink, BANNER_TRACK)
    values["banner-fill"] = banner_ink

    rgb = ",".join(str(c) for c in to_rgb(ink))
    values["text"] = f"rgba({rgb},{emphasis['high']})"
    values["muted"] = f"rgba({rgb},{emphasis['medium']})"
    values["divider"] = f"rgba({rgb},{emphasis['divider']})"
    # A helper border: half as strong as the divider, just a hint of an edge.
    values["border"] = f"rgba({rgb},{emphasis['divider'] / 2:.3f})"
    values["track"] = f"rgba({rgb},0.10)"
    # Sunken surface: a code block inside a card. Darker than the card, so it
    # derives from black regardless of the theme mode.
    values["sunken"] = "rgba(0,0,0,0.22)" if mode == "dark" else "rgba(0,0,0,0.05)"
    # Neutral fill for AFK: more visible than the track, but not an accent.
    values["fill-idle"] = f"rgba({rgb},0.32)"

    # Accent fill. In flat themes the gradient degenerates into a solid
    # color: both SVG gradient stops are equal and the CSS fill is just a
    # color, so no transition is visible.
    if theme.get("flat"):
        values["accent-fill"] = theme["primary"]
        values["grad-a"] = theme["primary"]
        values["grad-b"] = theme["primary"]
    else:
        values["accent-fill"] = (
            "linear-gradient(90deg, var(--primary), var(--secondary))"
        )
        values["grad-a"] = theme["primary_variant"]
        values["grad-b"] = theme["primary"]

    for level in ELEVATIONS:
        values[f"surface-{level}"] = surface_at(theme, level)
        values[f"elev-{level}"] = ELEVATION_SHADOWS[level]
        # The glass counterpart of the same level.
        values[f"glass-{level}"] = rgba(glass_veil(theme), glass_alpha(theme, level))

    values["page-bg"] = ambient_css(theme)
    values["glass-blur"] = GLASS_BLUR
    sheen_top, sheen_bottom = GLASS_SHEEN[mode]
    values["glass-sheen"] = (
        f"linear-gradient(180deg, {rgba(WHITE, sheen_top)}, "
        f"{rgba(WHITE, sheen_bottom)})"
    )
    values["glass-shadow"] = (
        "0 8px 24px rgba(0,0,0,.35)" if mode == "dark"
        else "0 8px 24px rgba(0,0,0,.12)"
    )
    # The top border edge is lighter than the rest — light reads as from above.
    if mode == "dark":
        values["glass-border"] = rgba(WHITE, 0.08)
        values["glass-border-top"] = rgba(WHITE, 0.14)
    else:
        values["glass-border"] = rgba(BLACK, 0.09)
        values["glass-border-top"] = rgba(BLACK, 0.04)

    # Card volume: gradient edge, top highlight, bottom shade, layered
    # shadow. The miniature variants are for icon plates.
    (top_ink, top_a), (bottom_ink, bottom_a) = GLASS_EDGE[mode]
    values["glass-edge-top"] = rgba(top_ink, top_a)
    values["glass-edge-bottom"] = rgba(bottom_ink, bottom_a)
    values["glass-highlight"] = f"inset 0 1px 1px 0 {rgba(WHITE, GLASS_HIGHLIGHT[mode])}"
    shade = rgba(BLACK, CARD_SHADE[mode])
    values["glass-shade"] = f"inset 0 -16px 22px -18px {shade}"
    values["glass-shade-sm"] = f"inset 0 -4px 6px -4px {shade}"
    values["card-shadow"] = CARD_SHADOW[mode]
    hover_ink, hover_a = ROW_HOVER[mode]
    values["row-hover"] = rgba(hover_ink, hover_a)
    values["value-hover"] = VALUE_HOVER[mode]

    scale = heat_scale(theme)
    for i, color in enumerate(scale[:5], 1):
        values[f"heat-{i}"] = color
    values["heat-peak"] = scale[5]
    empty_ink, empty_alpha = HEAT_EMPTY[mode]
    values["heat-empty"] = rgba(empty_ink, empty_alpha)

    # Six slots by position in categories.json, then "Other" (merged small
    # categories) and "Uncategorized". Both are Material 2014 neutrals
    # chosen for the theme palette: the largest color distance (ΔE) to the
    # six category colors and to each other, at contrast ≥ 3:1 on the card
    # glass.
    for i, color in enumerate(theme["categories"], 1):
        values[f"cat-{i}"] = color
    values["cat-other"] = theme["cat_other"]
    values["cat-uncategorized"] = theme["cat_uncategorized"]

    return values


# --------------------------------------------------------------------------
# Typography ("The type system")
# --------------------------------------------------------------------------
#
# (size in px, weight, letter-spacing in px). Conversion to rem is size/16,
# as described in the PDF on pp. 3–4.
TYPE_SCALE = {
    "h1": (96, 300, -1.5),
    "h2": (60, 300, -0.5),
    "h3": (48, 400, 0.0),
    "h4": (34, 400, 0.25),
    "h5": (24, 400, 0.0),
    "h6": (20, 500, 0.15),
    "subtitle1": (16, 400, 0.15),
    "subtitle2": (14, 500, 0.1),
    "body1": (16, 400, 0.5),
    "body2": (14, 400, 0.25),
    "button": (14, 500, 1.25),
    "caption": (12, 400, 0.4),
    "overline": (10, 400, 1.5),
}

# Medium 500 for subtitles, buttons and overline was a design request —
# for overline that departs from the scale (400 there), kept deliberately.
WEIGHT_OVERRIDES = {"overline": 500, "subtitle1": 500}


def type_css(name):
    size, weight, spacing = TYPE_SCALE[name]
    weight = WEIGHT_OVERRIDES.get(name, weight)
    return (
        f"font-size:{size / 16:.4f}rem;"
        f"font-weight:{weight};"
        f"letter-spacing:{spacing / 16:.4f}rem;"
    )


# --------------------------------------------------------------------------
# CSS generation
# --------------------------------------------------------------------------


def theme_css():
    """Variable blocks for every theme, switching without JS.

    The radio inputs sit before .page, so the variables hang on the sibling
    combinator. Plus a :has() rule for the page background; older browsers
    simply skip it and keep the .page background.
    """
    blocks = []
    for theme in THEMES:
        declarations = "".join(
            f"--{key}:{value};" for key, value in roles(theme).items()
        )
        blocks.append(f"#th-{theme['id']}:checked ~ .page{{{declarations}}}")
        # The same composed background on body too: otherwise the area past
        # the scroll extent would show the bare base color.
        blocks.append(
            f"body:has(#th-{theme['id']}:checked)"
            f"{{background:{ambient_css(theme)};"
            "background-attachment:fixed;}"
        )
        blocks.append(
            f"#th-{theme['id']}:checked ~ .page label[for=th-{theme['id']}]"
            "{border-color:var(--primary);color:var(--text);}"
        )
        # Name of the active theme in the menu button.
        blocks.append(
            f"#th-{theme['id']}:checked ~ .page .current-{theme['id']}"
            "{display:inline-flex;}"
        )
    return "\n".join(blocks)


def default_theme():
    return THEME_BY_ID.get(config.DEFAULT_THEME, THEMES[0])


# --------------------------------------------------------------------------
# Accessibility check
# --------------------------------------------------------------------------

AA_NORMAL = 4.5     # normal text
AA_LARGE = 3.0      # large text and graphical elements


def audit():
    """Contrast of all text pairs in every theme.

    Returns [(theme, pair, ratio, threshold, passed)].
    """
    results = []
    for theme in THEMES:
        values = roles(theme)
        mode = theme["mode"]
        ink = WHITE if mode == "dark" else BLACK
        emphasis = theme.get("emphasis", EMPHASIS[mode])

        checks = []
        # The background is a gradient, so text is checked at each of its
        # stops, not only on the base color.
        page_stops, banner_stops = gradient_stops(theme)
        for i, stop in enumerate(page_stops, 1):
            checks.append(
                (f"text on background, stop {i}",
                 over(ink, stop, emphasis["high"]), stop, AA_NORMAL)
            )
            checks.append(
                (f"muted on background, stop {i}",
                 over(ink, stop, emphasis["medium"]), stop, AA_NORMAL)
            )
        # The banner carries text of two levels and the coverage bar. All of
        # it is checked at both gradient ends: each theme has its own color
        # under it.
        for i, stop in enumerate(banner_stops, 1):
            checks.append(
                (f"banner text, stop {i}", values["on-banner"], stop, AA_NORMAL)
            )
            checks.append(
                (f"banner secondary text, stop {i}",
                 over(values["on-banner"], stop, BANNER_SOFT), stop, AA_NORMAL)
            )
            # On the bar the value is carried by fill against track, not track
            # against background: the track is just the edge of the groove.
            checks.append(
                (f"bar fill against track, stop {i}",
                 values["banner-fill"],
                 over(values["on-banner"], stop, BANNER_TRACK), AA_LARGE)
            )
        # Cards are glass, so text lies not on a solid surface but on glass
        # over the background. Both extreme background points are checked:
        # the lightest spot and the darkest.
        lightest, darkest = ambient_extremes(theme)
        for level in ELEVATIONS:
            for spot_name, spot in (("light zone", lightest),
                                    ("dark zone", darkest)):
                card = glass_over(theme, spot, level)
                checks.append(
                    (f"text on glass {level}dp, {spot_name}",
                     over(ink, card, emphasis["high"]), card, AA_NORMAL)
                )
                checks.append(
                    (f"muted on glass {level}dp, {spot_name}",
                     over(ink, card, emphasis["medium"]), card, AA_NORMAL)
                )
            # The worst points of the card for muted text: the top of the sheen
            # (lighter), the shaded bottom and the hovered row (--row-hover).
            # The middle is covered by the check above.
            sheen_top, sheen_bottom = GLASS_SHEEN[theme["mode"]]
            hover_ink, hover_alpha = ROW_HOVER[theme["mode"]]
            for spot_name, spot in (("light zone", lightest),
                                    ("dark zone", darkest)):
                veiled = blend(spot, glass_veil(theme), glass_alpha(theme, level))
                variants = (
                    ("top", blend(veiled, WHITE, sheen_top)),
                    ("bottom", blend(blend(veiled, WHITE, sheen_bottom), BLACK,
                                  CARD_SHADE[theme["mode"]])),
                    ("hovered row",
                     blend(glass_over(theme, spot, level), hover_ink, hover_alpha)),
                )
                for where, card in variants:
                    checks.append(
                        (f"muted {level}dp, {where}, {spot_name}",
                         over(ink, card, emphasis["medium"]), card, AA_NORMAL)
                    )
            # Opaque fallback when backdrop-filter is unavailable.
            surface = values[f"surface-{level}"]
            checks.append(
                (f"text on fallback {level}dp",
                 over(ink, surface, emphasis["high"]), surface, AA_NORMAL)
            )
            checks.append(
                (f"muted on fallback {level}dp",
                 over(ink, surface, emphasis["medium"]), surface, AA_NORMAL)
            )

        # Accents and categories are checked on the lightest glass card:
        # that is where they have it hardest.
        base = glass_over(theme, ambient_extremes(theme)[0], 6)
        checks += [
            ("on-primary on primary", values["on-primary"], theme["primary"],
             AA_NORMAL),
            ("on-secondary on secondary", values["on-secondary"],
             theme["secondary"], AA_NORMAL),
            ("primary as accent on surface", theme["primary"], base, AA_LARGE),
            ("secondary as accent on surface", theme["secondary"], base,
             AA_LARGE),
            ("error on surface", theme["error"], base, AA_NORMAL),
            ("positive on surface", values["positive"], base, AA_NORMAL),
        ]
        for i, color in enumerate(theme["categories"], 1):
            checks.append((f"category {i} on surface", color, base, AA_LARGE))
        checks += [
            ('"Other" on surface', theme["cat_other"], base, AA_LARGE),
            ('"Uncategorized" on surface', theme["cat_uncategorized"], base,
             AA_LARGE),
            ("heatmap peak on surface", heat_scale(theme)[5], base, AA_LARGE),
        ]

        for label, fg, bg, threshold in checks:
            ratio = contrast(fg, bg)
            results.append((theme, label, ratio, threshold, ratio >= threshold))
    return results


# Background lightness spread budget, in percentage points.
LIGHTNESS_BUDGET = 6.0


if __name__ == "__main__":
    print(f"{'theme':<22}{'check':<34}{'ratio':>7}  threshold")
    failures = 0
    for theme, label, ratio, threshold, ok in audit():
        if not ok:
            failures += 1
            print(f"{theme['name']:<22}{label:<34}{ratio:>6.2f}:1  "
                  f"< {threshold}  ✗")
    print(f"\nfailing: {failures}")

    print(f"\nBackground lightness spread (budget {LIGHTNESS_BUDGET:.0f}%):")
    for theme in THEMES:
        spread = ambient_lightness_spread(theme)
        if "ambient_budget" in theme and theme["ambient_budget"] is None:
            mark = "budget does not apply (reference background)"
        else:
            mark = "OK" if spread <= LIGHTNESS_BUDGET else "EXCEEDED"
        print(f"  {theme['name']:<22}{spread:5.2f}%   {mark}")

    print("\nLightness: background vs card at 6dp")
    for theme in THEMES:
        lightest, darkest = ambient_extremes(theme)
        card_light = lightness_of(glass_over(theme, lightest, 6)) * 100
        card_dark = lightness_of(glass_over(theme, darkest, 6)) * 100
        print(f"  {theme['name']:<22}"
              f"background {lightness_of(darkest)*100:5.1f}–{lightness_of(lightest)*100:5.1f}%   "
              f"card {card_dark:5.1f}–{card_light:5.1f}%")
