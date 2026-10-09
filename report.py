"""Builds a self-contained HTML report from ActivityWatch data.

One file with everything inside: CSS, charts (inline SVG), icons (inline
SVG) and a small script. No CDNs and no outside requests, so the report
opens offline and keeps working years from now.

Design is Material Design 2: palettes, elevation, typography and gradient
tokens live in theme.py, icons in icons.py, the font in fonts.py, and
every piece of interface text in locales/ (see i18n.py).

There is no counting here: aw_data.py stays the single source of
statistics. The exceptions are presentation-only reshaping of numbers
that are already computed (grouping categories for the legend, heatmap
level bounds, week-over-week deltas from stats.by_day).

Usage:
    python report.py              # build dashboard.html from ActivityWatch
    python report.py --lang en    # interface language for this run
    python report.py --demo       # made-up data, for screenshots
"""

import argparse
import html
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import archive
import aw_data
import config
import fonts
import i18n
import icons
import theme
from aw_data import ActivityWatchError
from i18n import category_label, counted, fmt_duration, tr


def t(name):
    """CSS declarations for a step of the Material type scale."""
    return theme.type_css(name)


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------


def build_css():
    return f"""
*, *::before, *::after {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ background: {theme.default_theme()['background']}; }}

.theme-radio {{
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap;
}}

.page {{
  /* One spacing step between cards for the whole report. */
  --gap-card: 16px;
  --gap-row: 8px;
  /* Hover transitions: appear fast, fade a little slower. Never longer
     than 150 ms; only transform, opacity and background-color animate. */
  --t-in: 80ms;
  --t-out: 150ms;
  /* Bars follow one design code with two roles. A summary bar is the
     main visual of a card (banner, categories, computer-on time); a row
     bar sits in a table row. The shape is the same: see "Bars" below. */
  --bar-sum: 12px;
  --bar-row: 8px;
  --bar-gap: 3px;
  /* Icon plate radius follows the backing shape (config.ICON_SHAPE). */
  --plate-radius: {icons.plate_radius()};
  min-height: 100vh;
  /* Layered background: large soft spots over a base colour.
     fixed — so the background does not scroll with the content. */
  background: var(--page-bg);
  background-attachment: fixed;
  color: var(--text);
  font-family: {config.FONT_STACK};
  {t('body2')}
  -webkit-font-smoothing: antialiased;
}}
.wrap {{ max-width: 1180px; margin: 0 auto; padding: 22px 22px 56px; }}

/* --- Typography ------------------------------------------------------- */
h1 {{ {t('h5')} font-weight: 500; margin: 0; }}
h2 {{
  {t('subtitle2')} text-transform: uppercase;
  color: var(--muted); margin: 0;
}}
.overline {{ {t('overline')} text-transform: uppercase; color: var(--muted); }}
.sub {{ {t('caption')} color: var(--muted); margin: 2px 0 0; }}
code {{ font-family: Consolas, "SF Mono", Menlo, monospace; font-size: .75rem; }}

/* --- Elevation and glass ---------------------------------------------- */
/* A level is glass veil density plus a shadow. The elevation steps are
   still there: the higher, the denser the glass. The top edge of the
   border is lighter than the rest so light reads as coming from above. */
.elev-2, .elev-6, .elev-12, .elev-24 {{
  border: 1px solid var(--glass-border);
  border-top-color: var(--glass-border-top);
}}
.elev-2  {{ background: var(--glass-2);  box-shadow: var(--elev-2); }}
.elev-6  {{ background: var(--glass-6);  box-shadow: var(--elev-6); }}
.elev-12 {{ background: var(--glass-12); box-shadow: var(--elev-12); }}
.elev-24 {{ background: var(--glass-24); box-shadow: var(--elev-24); }}

/* Blur only on large cards. Top-list rows, category rows and heatmap
   cells stay merely translucent: backdrop-filter on a couple dozen rows
   makes scrolling heavy. */
.panel, .kpi, .thememenu .menu, .thememenu > summary {{
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  background-image: var(--glass-sheen);
  box-shadow: var(--glass-shadow);
}}
/* Tiles inside a glass card (games, fragmentation, rhythm) sit on glass
   that is already blurred: their own blur adds nothing visible but costs
   one more blurred layer repainted together with the card. So blur is
   only on top-level cards. */
.panel .kpi {{ backdrop-filter: none; -webkit-backdrop-filter: none; }}

/* --- Card volume -------------------------------------------------------- */
/* The card looks convex: a barely visible vertical background gradient
   (--glass-sheen, lighter at the top), a white highlight at the top and
   shading at the bottom inside, a soft layered shadow outside. All from
   theme tokens; the effect values come from a Google Stitch reference,
   see theme.py. */
.panel, .kpi {{
  position: relative;
  box-shadow: var(--card-shadow), var(--glass-highlight), var(--glass-shade);
  /* Without mask support the edge is drawn by a plain border in the
     same tokens. */
  border-color: var(--glass-edge-bottom);
  border-top-color: var(--glass-edge-top);
}}
/* The light line along the edge is a 1px gradient border: a pseudo-element
   over the whole border box with the inside cut out by mask. A regular
   border cannot be a gradient. The card's own border stays 1px and
   transparent, so sizes and layout do not change. ::after is the same
   line for hover: it fades in on top and makes the edge a bit brighter.
   black in the mask is not a colour, only mask opacity. */
@supports (mask-composite: exclude) or (-webkit-mask-composite: xor) {{
  .panel, .kpi {{ border-color: transparent; }}
  .panel::before, .kpi::before, .panel::after, .kpi::after, .plate::before {{
    content: ""; position: absolute; inset: -1px; padding: 1px;
    border-radius: inherit; pointer-events: none;
    background: linear-gradient(180deg, var(--glass-edge-top), var(--glass-edge-bottom));
    -webkit-mask: linear-gradient(black 0 0) content-box, linear-gradient(black 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(black 0 0) content-box exclude, linear-gradient(black 0 0);
  }}
  .plate::before {{ inset: 0; }}
  .panel::after, .kpi::after {{
    opacity: 0; transition: opacity var(--t-out) ease-out;
  }}
  .panel:hover::after, .kpi:hover::after {{
    opacity: .8; transition-duration: var(--t-in);
  }}
}}
/* The plate under every icon (icons.py) is the card glass in miniature:
   a vertical background sheen, the edge (::before above), light at the
   top and shading at the bottom. The background is faintly tinted with
   the category colour: the icon sets --tint, ::after lays it under the
   glyph with transparency (isolation keeps it inside the plate).
   No backdrop-filter — that is for cards only. The radius follows
   config.ICON_SHAPE. */
.plate {{
  position: relative; isolation: isolate; flex: none; line-height: 0;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--plate-radius);
  background-image: var(--glass-sheen);
  box-shadow: var(--glass-highlight), var(--glass-shade-sm);
}}
.plate::after {{
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  border-radius: inherit; background: var(--tint); opacity: {icons.TINT_ALPHA};
}}
.plate > svg {{ display: block; }}

/* --- List rows ---------------------------------------------------------- */
/* A hovered row is highlighted (--row-hover) and its value gets brighter.
   Only the overlay opacity and background-color animate: box-shadow and
   filter repaint every frame, and under a glass card that also re-blurs
   the whole card layer — that is where the lag came from.
   Duration: appear --t-in (80 ms), fade --t-out (150 ms) — the shorter
   one sits on :hover, the longer one in the base state. */

/* Tables: every cell has a ::before overlay over its whole area; in the
   edge cells it reaches 8px past the text so the highlight does not stick
   to the letters, and the table layout does not change. z-index: 0 makes
   the cell its own layer, so the overlay goes under the text, not under
   the card. */
.tscroll tr:not(.axis-row) > td {{ position: relative; z-index: 0; }}
.tscroll tr:not(.axis-row) > td::before {{
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: var(--row-hover); opacity: 0;
  transition: opacity var(--t-out) ease-out;
}}
.tscroll tr:not(.axis-row) > td:first-child::before {{ left: -8px; border-radius: 8px 0 0 8px; }}
.tscroll tr:not(.axis-row) > td:last-child::before {{ right: -8px; border-radius: 0 8px 8px 0; }}
.tscroll tr:not(.axis-row):hover > td::before {{ opacity: 1; transition-duration: var(--t-in); }}

/* A row card already has its own 2dp background — the highlight is an
   overlay. */
.row-card {{ position: relative; }}
.row-card::after {{
  content: ""; position: absolute; inset: 0; border-radius: inherit;
  pointer-events: none; background: var(--row-hover); opacity: 0;
  transition: opacity var(--t-out) ease-out;
}}
.row-card:hover::after {{ opacity: 1; transition-duration: var(--t-in); }}

/* The category legend is transparent, so background-color is enough. */
.cat-row {{ transition: background-color var(--t-out) ease-out; }}
.cat-row:hover {{ background-color: var(--row-hover); transition-duration: var(--t-in); }}

/* Values change instantly, with no transition: color and filter are not
   among the properties allowed to animate. Coloured values brighten with
   a filter, muted ones switch to the full text colour (a brightness
   filter does nothing to white text). */
.row-card:hover .rc-value, .cat-row:hover .cat-time,
.tscroll tr:hover td.num {{ filter: var(--value-hover); }}
.cat-row:hover .cat-pct, .tscroll tr:hover td.pct, .tscroll tr:hover td.muted {{
  color: var(--text);
}}

/* Without backdrop-filter a card must stay readable — fall back to the
   solid surface of the same level. */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {{
  .elev-2  {{ background-color: var(--surface-2);  background-image: none; }}
  .elev-6  {{ background-color: var(--surface-6);  background-image: none; }}
  .elev-12 {{ background-color: var(--surface-12); background-image: none; }}
  .elev-24 {{ background-color: var(--surface-24); background-image: none; }}
}}

/* --- Header ----------------------------------------------------------- */
/* Title on the left, theme switcher on the right. Both are identical
   cards in shape, height and padding; only the fill differs: the title
   uses the banner gradient, the switcher uses glass. Content is centred
   inside each tile on both axes. */
.topbar {{
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 14px; margin-bottom: 18px;
}}
.brand, .thememenu > summary {{
  min-height: 44px; padding: 0 17px; border-radius: 11px;
  display: inline-flex; align-items: center; justify-content: center;
  gap: 10px; text-align: center;
  border: 1px solid var(--glass-border);
  border-top-color: var(--glass-border-top);
  box-shadow: var(--elev-2);
}}
.brand {{
  background: var(--gradient-banner); color: var(--on-banner);
}}
.brand svg {{ display: block; margin: 0; }}
.brand h1 {{ {t('subtitle1')} font-weight: 500; white-space: nowrap; }}

/* --- Banner ----------------------------------------------------------- */
/* Banner: active days on the left, the coverage bar across the rest.
   Both blocks are aligned on the bottom line. Bar colours derive from
   --on-banner, which is white or black depending on the gradient. */
.banner {{
  background: var(--gradient-banner); color: var(--on-banner);
  border-radius: 14px; padding: 22px 26px; margin-bottom: var(--gap-card);
  display: flex; flex-wrap: wrap; align-items: flex-end; gap: 20px 44px;
  box-shadow: var(--elev-6);
}}
.banner-main {{ flex: 0 0 auto; }}
.banner-main .k {{
  {t('overline')} text-transform: uppercase;
  color: var(--on-banner-soft); display: block;
}}
.banner-main .v {{
  display: flex; align-items: baseline; gap: 10px; margin-top: 7px;
}}
.banner-main .v b {{ {t('h4')} font-weight: 500; }}
.banner-main .v .of {{ {t('h6')} color: var(--on-banner-soft); }}

/* flex-grow with a basis: the bar takes all the width left between the
   left block and the banner edge. min-width makes the block wrap to its
   own line before it would start overlapping the number. */
.coverage {{
  flex: 1 1 280px; min-width: 260px;
  display: flex; flex-direction: column; gap: 9px;
}}
.coverage-top {{
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 16px;
}}
.coverage-from {{ {t('body2')} color: var(--on-banner-soft); }}
.coverage-pct {{ {t('subtitle2')} white-space: nowrap; }}
/* The banner bar is a summary .segbar of two segments: active and
   inactive days. The active segment has the banner text colour, so its
   contrast against the background is covered by the "banner text" check.
   The inactive one is the track, quieter on purpose: its value is
   repeated by the caption under the bar. */
.coverage-bar > .on {{ background: var(--banner-fill); }}
.coverage-bar > .off {{ background: var(--banner-track); }}
.coverage-legend {{
  display: flex; justify-content: space-between; gap: 16px;
  {t('body2')} color: var(--on-banner-soft);
}}

/* --- KPI cards -------------------------------------------------------- */
/* Explicit column counts, not auto-fit: with auto-fit the cards became
   3 + 1 at medium widths and the last one hung on its own row. */
/* All card groups share one --gap-card step so horizontal and vertical
   spacing match across the report. .rows are not cards but list rows
   inside a card, so they have their own, smaller step. */
.kpis {{
  display: grid; gap: var(--gap-card); margin-bottom: var(--gap-card);
  grid-template-columns: 1fr;
}}
/* Three cards: straight from 1 to 3 columns, no two-column step —
   otherwise the third would hang on its own row. */
@media (min-width: 720px) {{ .kpis {{ grid-template-columns: repeat(3, 1fr); }} }}
.tiles {{
  display: grid; gap: var(--gap-card); margin-bottom: var(--gap-card);
  grid-template-columns: 1fr;
}}
@media (min-width: 720px) {{ .tiles {{ grid-template-columns: repeat(3, 1fr); }} }}
.kpi {{ border-radius: 12px; padding: 15px 16px; }}
/* Icon left of the label — same as in section headings, so the whole
   report keeps one order. */
.kpi-top {{ display: flex; align-items: center; gap: 9px; margin-bottom: 14px; }}
.kpi-label {{ {t('overline')} text-transform: uppercase; color: var(--muted); }}
.kpi-icon {{ flex: none; line-height: 0; }}
/* Headline 5, not 4: values like "114 h 12 min" at 34px do not fit
   a card when there are four in a row. */
.kpi-value {{ {t('h5')} }}
.kpi-delta {{ {t('caption')} color: var(--muted); margin-top: 6px; }}
/* Green only for positive values. */
.kpi-delta.up {{ color: var(--positive); }}

/* --- Sections --------------------------------------------------------- */
.panel {{ border-radius: 12px; padding: 18px 20px; margin-bottom: var(--gap-card); }}
.panel-head {{
  display: flex; align-items: center; gap: 9px; margin-bottom: 14px;
}}
/* The gap to the next section is carried by the row itself: the cards
   inside have no margin of their own, otherwise it would enter the row
   height and break the alignment of the bottom edges. */
.cols {{ display: grid; gap: var(--gap-card); grid-template-columns: 1fr; margin-bottom: var(--gap-card); }}
@media (min-width: 1000px) {{
  /* stretch by default: both column rows must end on the same level.
     With align-items:start the bottom row was off by 216px — the shorter
     card left empty space under itself. */
  .cols {{ grid-template-columns: 1.45fr 1fr; align-items: stretch; }}
  /* Equal columns — for the paired rows. */
  .cols.even {{ grid-template-columns: 1fr 1fr; }}
}}
/* A card's own margin would enter the row height and stretch the
   neighbouring column 16px lower. The gap comes from the grid itself. */
.cols.even > .panel, .cols.stretch > .panel {{ margin-bottom: 0; }}

/* A stack of cards in a column: free space is shared between them, so
   the bottom of the stack lands level with the neighbouring column.
   In a narrow window, when the columns stack, there is no row height —
   flex-grow has nothing to act on and the cards keep their content
   height. */
.col-stack {{
  display: flex; flex-direction: column; gap: var(--gap-card); height: 100%;
}}
.col-stack > .panel {{ margin-bottom: 0; flex: 1 1 auto; }}
.cols > * {{ min-width: 0; }}

/* --- Row cards -------------------------------------------------------- */
.rows {{ display: flex; flex-direction: column; gap: var(--gap-row); }}
.row-card {{
  display: flex; align-items: center; gap: 12px;
  border-radius: 10px; padding: 10px 14px;
}}
.row-card .pos {{
  {t('subtitle2')} color: var(--muted); width: 22px; flex: none;
  font-variant-numeric: tabular-nums;
}}
.row-card .ricon {{ flex: none; line-height: 0; }}
.rc-main {{ min-width: 0; flex: 1; }}
.rc-title {{
  {t('subtitle1')} overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}}
.rc-sub {{ {t('caption')} color: var(--muted); margin-top: 1px; }}
.rc-value {{
  {t('subtitle1')} color: var(--primary); flex: none;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}}
.rc-value.plain {{ color: var(--text); }}

/* --- Tables ----------------------------------------------------------- */
/* The row highlight reaches 8px past the edge cells (see "List rows").
   For an overflow-x: auto container that is overflowing content — a
   scrollbar used to appear under every table. So the container has 8px
   of padding on the sides and the same negative margin: the table stays
   where it was, at the same width, and the highlight falls into the
   padding without crossing the container edge. */
.tscroll {{ overflow-x: auto; margin: 0 -8px; padding: 0 8px; }}
/* Widths are chosen so a table fits even the narrow right column of the
   two-column layout (about 415px there). */
table {{
  width: 100%; border-collapse: collapse; table-layout: fixed; min-width: 340px;
}}
td {{ padding: 5px 0; vertical-align: middle; }}
td.name {{
  width: 150px; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; padding-right: 10px;
}}
/* 104px, not 84: "54 h 18 min" in 84px overflowed the cell and ran into
   the percentage column. */
td.num {{
  width: 104px; text-align: right; font-variant-numeric: tabular-nums;
  padding-left: 10px; white-space: nowrap;
}}
td.pct {{
  width: 48px; text-align: right; color: var(--muted);
  font-variant-numeric: tabular-nums;
}}
/* For values like "2 h 31 min/day" that the usual 84px is too narrow for. */
td.num.wide {{ width: 112px; }}
/* --- Categories --------------------------------------------------------- */
/* The category bar is a summary .segbar; the segment width comes from
   flex-grow in the markup (category seconds). Only spacing here. */
.seg-bar {{ margin: 2px 0 12px; }}
/* The legend is a grid in every row: icon, name, time, percentage. The
   percentage has a fixed width, so the right edges of the times line up,
   and aligned_duration puts hours under hours. Row step as in tables. */
/* A negative margin and the same padding: the content stays where it
   was, and the hover highlight reaches 8px past the text. */
.cat-row {{
  display: grid; grid-template-columns: 20px minmax(0, 1fr) auto 3em;
  align-items: center; column-gap: 10px; padding: 5px 8px; margin: 0 -8px;
  border-radius: 8px;
}}
.cat-row .ricon {{ line-height: 0; }}
.cat-name {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.cat-time {{
  text-align: right; white-space: nowrap; font-weight: 500;
  font-variant-numeric: tabular-nums;
}}
.cat-pct {{ text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }}
/* The categories card keeps its content height; the free column height
   goes to the neighbouring computer-on card so the column bottoms stay
   level. */
.col-stack > .panel.natural {{ flex: 0 0 auto; }}

/* Minutes in a fixed-width field: in a right-aligned column hours line
   up under hours and minutes under minutes (aligned_duration). Two-digit
   minutes are 2.54em in Segoe UI; 2.6em leaves a little room for Roboto,
   otherwise an extra gap appeared between hours and minutes. */
.dur-m {{ display: inline-block; min-width: 2.6em; margin-left: .25em; text-align: right; }}
/* Margin only where the icon sits inside a line of text. In flex contexts
   (header, section headings, KPI cards, row cards) the gap does it, and
   an extra margin pushed the icon off centre — that is what made the
   header icon drift. */
.cat-icon {{ flex: none; }}
td .cat-icon {{ vertical-align: -5px; margin-right: 8px; }}
/* --- Bars ------------------------------------------------------------- */
/* One design code for every bar in the report. There used to be four
   shapes: radius 3, 4 and "outer ends only", gaps 0, 2 and 6px, heights
   8 and 14px. The rules are shared now, while each bar keeps its colours
   and gradients:
   • full rounding (pill) on the track, the fill and every segment;
   • segments are separate pills with a --bar-gap gap, width is flex-grow
     in the markup (the value itself, no conversion to percent);
   • the smallest segment is never narrower than its own height, so even
     a few minutes show as a dot, not a hairline;
   • height by role: --bar-sum for summary bars, --bar-row for row bars. */
.segbar {{ display: flex; gap: var(--bar-gap); height: var(--bar-sum); }}
.segbar > i {{
  display: block; flex: 1 1 0; min-width: var(--bar-sum); border-radius: 999px;
}}
.bar {{
  background: var(--track); border-radius: 999px; height: var(--bar-row);
  overflow: hidden;
}}
.bar > i {{ display: block; height: 100%; border-radius: 999px; background: var(--accent-fill); }}

/* --- Active time and AFK ---------------------------------------------- */
/* The total above the bar shows that the three parts under it add up. */
.split-total {{ margin-bottom: 10px; }}
.split-total .k {{
  {t('overline')} text-transform: uppercase; color: var(--muted); display: block;
}}
.split-total .v {{ {t('h5')} margin-top: 4px; display: block; }}
.slegend {{ display: flex; flex-wrap: wrap; gap: 22px; margin-top: 14px; }}
.slegend .k {{ {t('overline')} text-transform: uppercase; color: var(--muted); }}
.slegend .v {{ {t('subtitle2')} margin-top: 3px; }}
.note-block {{
  {t('caption')} color: var(--muted); margin-top: 14px;
  border-top: 1px solid var(--divider); padding-top: 12px; line-height: 1.6;
}}
.note-block p {{ margin: 6px 0; }}

/* --- Heatmap ---------------------------------------------------------- */
/* The grid spans the card width but no wider than max-width, otherwise
   cells become absurdly large on a wide screen. Height follows the width
   through aspect-ratio on the cells, so the proportion holds at any
   window width. */
/* .heat-box is the anchor for the tooltip (position: relative); the grid
   itself is unchanged in the flow. */
.heat-box {{ position: relative; max-width: 940px; margin: 0 auto; }}
.heat {{ display: grid; grid-template-columns: 28px repeat(24, 1fr); gap: 4px; }}
.heat div {{ border-radius: 3px; }}
.heat .lbl {{ {t('caption')} color: var(--muted); display: flex; align-items: center; }}
.heat .hour {{
  {t('overline')} color: var(--muted); text-align: center;
  font-variant-numeric: tabular-nums;
}}
/* Every hour label is in the markup, but only every third one is visible;
   the rest appear when their hour is under the cursor. */
.heat .hour.minor {{ color: transparent; }}
.heat .lbl.hl, .heat .hour.hl {{ color: var(--text); }}
/* An empty cell and five levels: the bounds are quantiles of the non-empty
   cells (report.heat_bounds), the peak is the brightest step of the same
   hue (theme.heat_scale). */
.heat .cell {{
  aspect-ratio: 1; min-width: 0; position: relative;
  background: var(--heat-empty); transition: transform var(--t-out) ease-out;
}}
/* transform only: the neighbours' layout is not recalculated. */
.heat .cell:hover {{ transform: scale(1.2); z-index: 2; transition-duration: var(--t-in); }}
.heat .h1, .legend .h1 {{ background: var(--heat-1); }}
.heat .h2, .legend .h2 {{ background: var(--heat-2); }}
.heat .h3, .legend .h3 {{ background: var(--heat-3); }}
.heat .h4, .legend .h4 {{ background: var(--heat-4); }}
.heat .hp, .legend .hp {{ background: var(--heat-peak); }}
.heat-tip {{
  position: absolute; left: 0; top: 0; z-index: 5; pointer-events: none;
  opacity: 0; transition: opacity var(--t-out) ease-out;
  padding: 6px 10px; border-radius: 8px; white-space: nowrap;
  {t('caption')} color: var(--text); font-variant-numeric: tabular-nums;
}}
/* The tooltip is always in the DOM: shown via opacity, placed via transform. */
.heat-tip.on {{ opacity: 1; transition-duration: var(--t-in); }}
.legend {{
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 12px;
  {t('caption')} color: var(--muted);
}}
.legend span {{ width: 15px; height: 9px; border-radius: 2px; background: var(--heat-empty); }}
.legend .sep {{ width: auto; height: auto; background: none; margin: 0 4px; }}

/* All transitions are off when the system asks for reduced motion. */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
}}

/* --- Attention fragmentation and daily rhythm ------------------------- */
/* The same tiles, tables and tokens the report already has: there are no
   new colour pairs left unchecked by the audit. */
/* A caption under the number in a tile: where it comes from. */
.kpi-sub {{ {t('caption')} color: var(--muted); margin-top: 4px; }}
/* Report tables have no headers, so one line above says what the columns are. */
.table-cap {{ {t('caption')} color: var(--muted); margin: 0 0 6px; }}
/* A week is one Monday date: fixed width and muted colour, so the eye
   goes to the bar and the hours, not to the dates. */
td.week {{
  width: 56px; white-space: nowrap; color: var(--muted);
  font-variant-numeric: tabular-nums;
}}
td.muted {{ color: var(--muted); }}
/* Paired cards of equal height: the cards are flex columns, a spacer takes
   the free space, and "How this is calculated" sits near the bottom of
   both, on one line. Outside a flex context the spacer is zero. */
.panel.fill {{ display: flex; flex-direction: column; }}
.panel.fill > .push {{ flex: 1 0 0; }}
/* A week on the logical-day track is an ordinary .bar whose fill is
   shifted: margin-left and width in percent of a day are set inline. */
.ticks {{
  display: flex; justify-content: space-between;
  {t('caption')} color: var(--muted); font-variant-numeric: tabular-nums;
}}

/* --- Theme switcher --------------------------------------------------- */
/* margin: 0 cancels the global details margin — because of it the menu's
   outer box was 10px taller than the card and the pair was off centre. */
.thememenu {{ position: relative; flex: none; margin: 0; }}
.thememenu > summary {{
  {t('button')} display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 15px; border-radius: 10px; cursor: pointer;
  border: 1px solid var(--glass-border); border-top-color: var(--glass-border-top);
  color: var(--text); text-transform: none; background-color: var(--glass-2);
}}
.thememenu > summary:hover {{ border-color: var(--primary); }}
.thememenu .current {{ display: none; align-items: center; gap: 7px; }}
.thememenu .menu {{
  position: absolute; z-index: 30; top: calc(100% + 8px); right: 0;
  display: flex; flex-direction: column; gap: 4px;
  padding: 10px; border-radius: 12px; min-width: 250px;
}}
.thememenu .menu .overline {{ margin: 2px 0 4px 4px; }}
.thememenu label {{
  {t('button')} display: flex; align-items: center; gap: 9px;
  padding: 7px 10px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; color: var(--muted);
  text-transform: none; user-select: none;
}}
.thememenu label:hover {{ background: var(--track); color: var(--text); }}
.sw {{ display: inline-flex; gap: 2px; flex: none; }}
.sw i {{ width: 9px; height: 14px; border-radius: 2px; }}

/* --- Small things ----------------------------------------------------- */
.empty {{ color: var(--muted); font-style: italic; padding: 8px 0; }}
.tiny {{
  {t('caption')} color: var(--muted); margin-top: 12px;
  border-top: 1px solid var(--divider); padding-top: 10px;
}}
details {{ margin-top: 10px; }}
details summary {{
  {t('button')} text-transform: none; cursor: pointer; color: var(--primary);
  list-style: none; display: inline-block; user-select: none;
}}
details summary::-webkit-details-marker {{ display: none; }}
details summary::before {{ content: "\\25B8  "; }}
details[open] summary::before {{ content: "\\25BE  "; }}
.thememenu > summary::before {{ content: none; }}
pre.copy {{
  background: var(--sunken); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 12px; margin: 10px 0 0; overflow-x: auto;
  font-family: Consolas, "SF Mono", Menlo, monospace; font-size: .75rem;
  color: var(--text); line-height: 1.5;
}}
.warn {{
  border-radius: 10px; padding: 11px 15px; margin-bottom: 16px;
  {t('body2')} color: var(--on-error); background: var(--error);
}}
.warn ul {{ margin: 6px 0 0; padding-left: 20px; }}
.warn code {{ color: inherit; }}
footer {{ {t('caption')} color: var(--muted); margin-top: 24px; }}
footer p {{ margin: 6px 0; }}
svg {{ display: block; width: 100%; height: auto; }}
svg.cat-icon {{ display: inline-block; width: auto; }}
.axis {{ fill: var(--muted); font-size: .625rem; font-family: inherit; }}
.grid {{ stroke: var(--divider); stroke-width: 1; stroke-dasharray: 3 5; }}
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def esc(text):
    return html.escape(str(text))


def table(rows, style=""):
    attr = f" style='{style}'" if style else ""
    return f"<div class='tscroll'><table{attr}>{rows}</table></div>"


def category_vars(order):
    """Category -> CSS variable with its colour in the active theme.

    The colour follows the position in categories.json (--cat-1..6, then
    round again); "Other" and "Uncategorized" have their own neutral
    theme tokens.
    """
    colors = {}
    known = [name for name in order if name != config.UNCATEGORIZED]
    for i, name in enumerate(known):
        colors[name] = f"var(--cat-{i % 6 + 1})"
    colors[config.CATEGORY_OTHER] = "var(--cat-other)"
    colors[config.UNCATEGORIZED] = "var(--cat-uncategorized)"
    return colors


def color_of(category, colors):
    return colors.get(category, "var(--cat-uncategorized)")


def percents_to_100(values):
    """Whole percentages that add up to exactly 100 (largest remainder).

    Plain rounding of 39.8 + 19.7 + 16.2 + … easily gives 99 or 101.
    Here everyone gets the integer part, and the units left until 100 go
    to those with the largest fractional part.
    """
    total = sum(values)
    if total <= 0:
        return [0] * len(values)
    exact = [v / total * 100 for v in values]
    result = [int(x) for x in exact]
    by_remainder = sorted(range(len(values)), key=lambda i: exact[i] - result[i],
                          reverse=True)
    for i in by_remainder[:100 - sum(result)]:
        result[i] += 1
    return result


def pct(part, whole):
    return part / whole * 100 if whole else 0.0


def ago(moment, today):
    days = (today - moment.date()).days
    if days <= 0:
        return tr("games.today")
    if days == 1:
        return tr("games.yesterday")
    return tr("games.ago", days=counted(days, "day"))


def window_sum(by_day, end, span):
    """Sum over span days ending with the day end, inclusive."""
    start = end - timedelta(days=span - 1)
    return sum(v for day, v in by_day.items() if start <= day <= end)


def window_days(by_day, end, span):
    start = end - timedelta(days=span - 1)
    return sum(
        1 for day, v in by_day.items()
        if start <= day <= end and v >= config.MIN_DAY_SECONDS
    )


def week_delta(by_day, anchor, span=7):
    """Percent change of the last week against the one before, or None.

    Computed from the ready-made stats.by_day — no new counting over raw
    events happens here.
    """
    if not by_day or anchor is None:
        return None
    current = window_sum(by_day, anchor, span)
    previous = window_sum(by_day, anchor - timedelta(days=span), span)
    if previous <= 0:
        return None
    return (current - previous) / previous * 100


def delta_markup(value, suffix=None):
    """Zero is written in words: "▲ 0%" next to "▲ 206%" reads like a glitch."""
    suffix = tr("delta.suffix") if suffix is None else suffix
    if value is None:
        return f"<div class='kpi-delta'>{tr('delta.none')}</div>"
    if round(abs(value)) == 0:
        return f"<div class='kpi-delta'>{tr('delta.same')}</div>"
    arrow = "▲" if value > 0 else "▼"
    klass = "kpi-delta up" if value > 0 else "kpi-delta"
    return f"<div class='{klass}'>{arrow} {abs(value):.0f}% {esc(suffix)}</div>"


def aligned_duration(seconds, suffix=""):
    """A duration for a numeric column: hours under hours, minutes under minutes.

    The column is right-aligned, so "41 h 8 min" under "12 h 35 min" would
    be shifted by the width of a digit. Minutes go into a fixed-width
    field here and the units line up. The text is the same fmt_duration.
    """
    hours, minutes = i18n.duration_parts(seconds)
    return (f"{esc(hours)}<span class='dur-m'>{esc(minutes)}</span>"
            f"{esc(suffix)}")


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------


def swatches(item):
    return "".join(
        f'<i style="background:{item[key]}"></i>'
        for key in ("primary", "secondary")
    )


def render_topbar(stats):
    labels, current = [], []
    for item in theme.THEMES:
        kind = tr("theme.dark") if item["mode"] == "dark" else tr("theme.light")
        labels.append(
            f'<label for="th-{item["id"]}" title="{esc(item["name"])} · {kind}">'
            f'<span class="sw">{swatches(item)}</span>{esc(item["name"])}</label>'
        )
        current.append(
            f'<span class="current current-{item["id"]}">'
            f'<span class="sw">{swatches(item)}</span>{esc(item["name"])}</span>'
        )

    # The bucket name and event count were removed from the header:
    # technical details that added nothing. They are still in Stats.
    mark = icons.ui_icon("chart", "var(--on-banner)", 22, backing=False)
    return f"""<header class="topbar">
  <div class="brand">
    {mark}
    <h1>{tr('brand')}</h1>
  </div>
  <details class="thememenu" id="thememenu">
    <summary>{tr('theme.label')} {''.join(current)}</summary>
    <div class="menu elev-24" role="group" aria-label="{tr('theme.aria')}">
      <span class="overline">{tr('theme.menu_title')}</span>
      {''.join(labels)}
    </div>
  </details>
</header>"""


def missing_label(days):
    """«26–27 і 29 липня; 17–27 серпня» — days without data grouped by month."""
    runs = []
    for day in days:
        if (runs and day - runs[-1][1] == timedelta(days=1)
                and day.month == runs[-1][1].month):
            runs[-1][1] = day
        else:
            runs.append([day, day])

    months = []
    for start, end in runs:
        text = f"{start.day}" if start == end else f"{start.day}–{end.day}"
        if months and months[-1][0] == (start.year, start.month):
            months[-1][1].append(text)
        else:
            months.append(((start.year, start.month), [text]))

    parts = [tr("by_month.group", days=i18n.join_and(items),
                month=i18n.month_genitive(month))
             for (_, month), items in months]
    return "; ".join(parts)


def render_banner(stats):
    """The banner carries one figure: how many calendar days were active.

    Layout from the mockup: "Active days" and "12 of 30" on the left; the
    start date and the percentage above the bar on the right; a bar of two
    segments (active and inactive) with the counts under it. No other
    metrics: total time, daily average and event count live in the cards.

    The denominator is calendar days from the first event to today,
    inclusive. Days without any event are not singled out: ActivityWatch
    starts with the system, so these are days the computer was off —
    inactive.
    """
    if not (stats.period_start and stats.calendar_days):
        return ""

    total = stats.calendar_days
    active = len(stats.active_days)
    inactive = stats.inactive_days
    share = round(pct(active, total))

    # The number of days itself sets the segment width (flex-grow). An
    # empty segment is not drawn, otherwise the gap would have no partner.
    bar = "".join(
        f'<i class="{klass}" style="flex-grow:{count}"></i>'
        for klass, count in (("on", active), ("off", inactive)) if count
    )

    return f"""<section class="banner">
  <div class="banner-main">
    <span class="k">{tr('banner.active_days')}</span>
    <span class="v"><b>{active}</b><span class="of">{tr('banner.of', total=total)}</span></span>
  </div>
  <div class="coverage">
    <div class="coverage-top">
      <span class="coverage-from">{tr('banner.since', date=esc(i18n.date_long(stats.period_start)))}</span>
      <span class="coverage-pct">{tr('banner.share', share=share)}</span>
    </div>
    <div class="segbar coverage-bar">{bar}</div>
    <div class="coverage-legend">
      <span>{counted(active, 'active')}</span>
      <span>{counted(inactive, 'inactive')}</span>
    </div>
  </div>
</section>"""


def render_kpis(stats):
    """Label, icon, number — and nothing else.

    The week-over-week comparison was removed from the cards: next to the
    number itself it read as noise. The calculation stays in place
    (week_delta, window_days, delta_markup) so the line can come back with
    one call.
    """
    # Active days were removed from here: they are the banner's content now.
    colors = ["var(--cat-1)", "var(--cat-2)", "var(--cat-3)"]
    cards = [
        (tr("kpi.active"), "clock", fmt_duration(stats.total_seconds)),
        (tr("kpi.average"), "trend", fmt_duration(stats.avg_per_day)),
        (tr("kpi.games"), "games", fmt_duration(stats.games_total)),
    ]

    out = ["<div class='kpis'>"]
    for i, (label, glyph, value) in enumerate(cards):
        icon = (icons.icon(config.GAME_CATEGORY, colors[i], 30) if glyph == "games"
                else icons.ui_icon(glyph, colors[i], 30))
        out.append(
            "<div class='kpi elev-2'>"
            f"<div class='kpi-top'><span class='kpi-icon'>{icon}</span>"
            f"<span class='kpi-label'>{esc(label)}</span></div>"
            f"<div class='kpi-value'>{esc(value)}</div></div>"
        )
    out.append("</div>")
    return "".join(out)


def render_split(stats):
    if not stats.afk_filtered or stats.powered_seconds <= 0:
        return ""

    # AFK credited to lenient categories is already inside active time, so
    # only the uncredited remainder is shown here — otherwise it would count
    # twice.
    parts = [
        (tr("split.active"), stats.total_seconds, "var(--accent-fill)"),
        (tr("split.other"), stats.other_seconds, "var(--track)"),
        (tr("split.afk"), stats.afk_uncounted_seconds, "var(--fill-idle)"),
    ]
    # The total is the sum of exactly all three parts. Active plus AFK would
    # be several hours less and would not match 100% on the bar.
    whole = sum(value for _, value, _ in parts)

    lenient = ""
    if stats.lenient_categories:
        names = [i18n.quoted(esc(c)) for c in stats.lenient_categories]
        lenient = "<p>" + tr(
            "split.lenient_note",
            where=i18n.plural(len(names), "category_in"),
            listed=i18n.join_and(names),
            cap=counted(config.AFK_LENIENT_CAP_SECONDS // 60, "minute"),
            counted=esc(fmt_duration(stats.afk_counted_seconds)),
        ) + "</p>"

    bar = "".join(
        f"<i style='flex-grow:{value:.0f};background:{color}' "
        f"title='{esc(label)} — {esc(fmt_duration(value))}'></i>"
        for label, value, color in parts if value > 0
    )
    legend = "".join(
        f"<div><div class='k'>{esc(label)}</div>"
        f"<div class='v'>{esc(fmt_duration(value))} · {pct(value, whole):.1f}%</div></div>"
        for label, value, _ in parts
    )
    head = icons.ui_icon("idle", "var(--primary)", 20)
    afk_note = tr("split.afk_note",
                  minutes=counted(config.SESSION_GAP_SECONDS // 60, "minute"))
    other_note = tr("split.other_note", system=esc(fmt_duration(stats.system_seconds)))
    return f"""
  <div class="panel fill elev-6">
    <div class="panel-head">{head}<h2>{tr('split.title')}</h2></div>
    <div class="split-total">
      <span class="k">{tr('split.total')}</span>
      <span class="v">{esc(fmt_duration(whole))}</span>
    </div>
    <div class="segbar split">{bar}</div>
    <div class="slegend">{legend}</div>
    <div class="push"></div>
    <div class="note-block">
      <details id="d-afk">
        <summary>{tr('common.how')}</summary>
        <p>{afk_note}</p>
        <p>{other_note}</p>{lenient}
      </details>
    </div>
  </div>"""


def category_parts(stats):
    """Rows of the categories block: [(name, seconds, hint)].

    Takes the ready-made sums of stats.by_category — this only groups them
    for display. Sorted by time descending; categories with a share under
    CATEGORY_OTHER_SHARE merge into "Other" after them; "Uncategorized"
    is separate and last, even when it is under the threshold.
    """
    total = stats.total_seconds
    known = [(c, s) for c, s in stats.by_category if c != config.UNCATEGORIZED]
    known.sort(key=lambda kv: kv[1], reverse=True)

    big = [(c, s) for c, s in known if total and s / total >= config.CATEGORY_OTHER_SHARE]
    small = [(c, s) for c, s in known if (c, s) not in big and s > 0]

    parts = [(c, s, "") for c, s in big]
    if small:
        merged = ", ".join(
            tr("categories.merged_item", name=category_label(c), duration=fmt_duration(s))
            for c, s in small
        )
        parts.append((config.CATEGORY_OTHER, sum(s for _, s in small),
                      tr("categories.merged",
                         share=f"{config.CATEGORY_OTHER_SHARE * 100:g}", list=merged)))
    unsorted = dict(stats.by_category).get(config.UNCATEGORIZED, 0.0)
    if unsorted > 0:
        parts.append((config.UNCATEGORIZED, unsorted, ""))
    return parts


def render_categories(stats):
    """Categories: a full-width segmented bar with the legend under it.

    The segment width is flex-grow equal to the category seconds, so the
    proportion is exact without conversion. Legend percentages are whole
    and add up to 100.
    """
    parts = category_parts(stats)
    if not parts:
        return f"<div class='empty'>{tr('common.no_data')}</div>"

    colors = category_vars(stats.category_order)
    shares = percents_to_100([s for _, s, _ in parts])

    segments, rows = [], []
    for (category, seconds, hint), share in zip(parts, shares):
        color = color_of(category, colors)
        name = category_label(category)
        title = tr("categories.segment", name=name, duration=fmt_duration(seconds),
                   share=share)
        if hint:
            title += f". {hint}"
        segments.append(
            f"<i style='flex-grow:{seconds:.0f};background:{color}' "
            f"title='{esc(title)}'></i>"
        )
        rows.append(
            f"<div class='cat-row' title='{esc(title)}'>"
            f"<span class='ricon'>{icons.icon(category, color)}</span>"
            f"<span class='cat-name'>{esc(name)}</span>"
            f"<span class='cat-time'>{aligned_duration(seconds)}</span>"
            f"<span class='cat-pct'>{share}%</span></div>"
        )

    return (f"<div class='segbar seg-bar'>{''.join(segments)}</div>"
            f"<div class='cat-legend'>{''.join(rows)}</div>"
            f"{render_uncategorized(stats)}")


def render_uncategorized(stats):
    """A hint on what to add to categories.json — when there is something to sort.

    The short "Uncategorized: N apps, X min" line was removed: the same
    time already sits in the last row of the category legend.
    """
    apps = stats.uncategorized_apps
    total = sum(seconds for _, _, seconds in apps)
    if not apps or total < config.UNCATEGORIZED_SHOW_SECONDS:
        return ""

    rows, lines = [], []
    for app, processes, seconds in apps:
        for process in processes:
            lines.append(f'    "{process}",')
        rows.append(
            f"<tr><td class='name'>{esc(i18n.app_label(app))}</td>"
            f"<td class='num'>{esc(fmt_duration(seconds))}</td>"
            f"<td style='padding-left:16px'><code>{esc(', '.join(processes))}</code></td>"
            "</tr>"
        )
    note = tr("categories.uncategorized_note",
              label=tr("category.uncategorized"), apps=counted(len(apps), "app"),
              duration=esc(fmt_duration(total)), file=esc(config.CATEGORIES_FILE))
    return f"""<div class='note-block'>
      {note}
      {table("".join(rows), "margin:10px 0")}
      <details id="d-uncat">
        <summary>{tr('categories.uncategorized_lines', file=esc(config.CATEGORIES_FILE))}</summary>
        <pre class='copy'>{esc(chr(10).join(lines))}</pre>
      </details>
    </div>"""


def collapse_rows(rows, visible, block_id, label):
    """Show the first visible rows, hide the rest in a collapsible block."""
    head = f"<div class='rows'>{''.join(rows[:visible])}</div>"
    rest = rows[visible:]
    if not rest:
        return head
    return (
        f"{head}<details id='{block_id}'>"
        f"<summary>{esc(label)} ({len(rest)})</summary>"
        f"<div class='rows' style='margin-top:8px'>{''.join(rest)}</div>"
        "</details>"
    )


def render_apps(stats):
    """Top applications as row cards: position, icon, name, time on the right."""
    if not stats.by_app:
        return f"<div class='empty'>{tr('apps.none')}</div>"

    colors = category_vars(stats.category_order)
    rows = []
    for i, (app, seconds) in enumerate(stats.by_app, 1):
        category = stats.app_categories.get(app, config.UNCATEGORIZED)
        color = color_of(category, colors)
        sub = tr("apps.sub", category=category_label(category),
                 share=f"{pct(seconds, stats.total_seconds):.1f}")
        rows.append(
            "<div class='row-card elev-2'>"
            f"<span class='pos'>{i}</span>"
            f"<span class='ricon'>{icons.icon(category, color, 26)}</span>"
            f"<div class='rc-main'><div class='rc-title'>{esc(i18n.app_label(app))}</div>"
            f"<div class='rc-sub'>{esc(sub)}</div></div>"
            f"<span class='rc-value'>{esc(fmt_duration(seconds))}</span></div>"
        )

    body = collapse_rows(
        rows, config.APPS_VISIBLE, "d-apps-rest", tr("common.show_all")
    )
    note = ""
    if stats.hidden_apps:
        note = (
            "<div class='tiny'>"
            + tr("apps.hidden", apps=counted(stats.hidden_apps, "app"),
                 duration=fmt_duration(config.MIN_APP_SECONDS))
            + "</div>"
        )
    return body + note


def monotone_path(points, y_min, y_max):
    """Monotone cubic interpolation (Fritsch–Carlson).

    Catmull-Rom overshoots past neighbouring values on sharp drops, and
    the curve on days falling from several hours to zero dipped below the
    zero line. The monotone scheme tames the tangents at the knots so that
    on every segment the curve stays between the values at its ends — it
    cannot fall below zero by construction.

    y_min / y_max are the plot area bounds; control points are also
    clamped to them as insurance against rounding errors.
    """
    count = len(points)
    if count < 2:
        return ""

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    widths = [xs[i + 1] - xs[i] for i in range(count - 1)]
    slopes = [
        (ys[i + 1] - ys[i]) / widths[i] if widths[i] else 0.0
        for i in range(count - 1)
    ]

    # Tangents at the knots: zero at extremes, a weighted mean inside.
    tangents = [0.0] * count
    tangents[0] = slopes[0]
    tangents[-1] = slopes[-1]
    for i in range(1, count - 1):
        if slopes[i - 1] * slopes[i] <= 0:
            tangents[i] = 0.0
        else:
            w1 = 2 * widths[i] + widths[i - 1]
            w2 = widths[i] + 2 * widths[i - 1]
            tangents[i] = (w1 + w2) / (w1 / slopes[i - 1] + w2 / slopes[i])

    # Fritsch–Carlson limiter: keeps each segment monotone.
    for i in range(count - 1):
        if slopes[i] == 0:
            tangents[i] = tangents[i + 1] = 0.0
            continue
        a = tangents[i] / slopes[i]
        b = tangents[i + 1] / slopes[i]
        total = a * a + b * b
        if total > 9:
            scale = 3.0 / total ** 0.5
            tangents[i] = scale * a * slopes[i]
            tangents[i + 1] = scale * b * slopes[i]

    def clamp(value):
        return max(y_min, min(y_max, value))

    parts = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(count - 1):
        third = widths[i] / 3.0
        c1y = clamp(ys[i] + tangents[i] * third)
        c2y = clamp(ys[i + 1] - tangents[i + 1] * third)
        parts.append(
            f"C{xs[i] + third:.1f},{c1y:.1f} "
            f"{xs[i + 1] - third:.1f},{c2y:.1f} "
            f"{xs[i + 1]:.1f},{ys[i + 1]:.1f}"
        )
    return " ".join(parts)


def render_days(stats):
    days = aw_data.recent_days(stats)
    peak = max((s for _, s in days), default=0.0)
    if peak <= 0:
        return (f"<div class='empty'>"
                f"{tr('days.none', days=counted(config.RECENT_DAYS, 'day'))}</div>")

    width, height = 960, 230
    pad_left, pad_bottom, pad_top = 64, 28, 14
    plot_w = width - pad_left - 12
    plot_h = height - pad_bottom - pad_top
    step = plot_w / max(1, len(days) - 1)

    def y_of(seconds):
        return pad_top + plot_h - (seconds / peak) * plot_h

    points = [(pad_left + i * step, y_of(seconds))
              for i, (_, seconds) in enumerate(days)]

    grid, labels = [], []
    for value in nice_ticks(peak):
        y = y_of(value)
        grid.append(
            f"<line class='grid' x1='{pad_left}' y1='{y:.1f}' "
            f"x2='{width - 12}' y2='{y:.1f}'/>"
            f"<text class='axis' x='{pad_left - 10}' y='{y + 3:.1f}' "
            f"text-anchor='end'>{esc(fmt_duration(value)) if value else '0'}</text>"
        )
    for i, (day, _) in enumerate(days):
        if i % 5 == 0 or i == len(days) - 1:
            grid.append(
                f"<line class='grid' x1='{points[i][0]:.1f}' y1='{pad_top}' "
                f"x2='{points[i][0]:.1f}' y2='{pad_top + plot_h}'/>"
            )
            labels.append(
                f"<text class='axis' x='{points[i][0]:.1f}' "
                f"y='{height - 9}' text-anchor='middle'>{i18n.date_short(day)}</text>"
            )

    # The lower bound is pinned to zero: the curve may not go below the axis.
    baseline = pad_top + plot_h
    curve = monotone_path(points, pad_top, baseline)
    area = (f"{curve} L{points[-1][0]:.1f},{baseline:.1f} "
            f"L{points[0][0]:.1f},{baseline:.1f} Z")

    # A day without any event is labelled "no data", not "0 s": it is a
    # missing observation, not zero activity.
    missing = set(stats.missing_days)
    dots = "".join(
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4.6' "
        f"style='fill:var(--primary);stroke:var(--background);stroke-width:2'>"
        "<title>"
        + tr("days.point", date=i18n.date_numeric(day),
             weekday=i18n.weekday_short(day.weekday()),
             value=tr("days.no_data") if day in missing else esc(fmt_duration(seconds)))
        + "</title></circle>"
        for (x, y), (day, seconds) in zip(points, days)
    )

    return (
        f"<svg viewBox='0 0 {width} {height}' role='img' "
        f"aria-label='{tr('days.aria', days=counted(len(days), 'day'))}'>"
        f"{''.join(grid)}"
        f"<path d='{area}' style='fill:var(--primary);opacity:.10'/>"
        f"<path d='{curve}' style='fill:none;stroke:var(--primary);"
        "stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round'/>"
        f"{dots}{''.join(labels)}</svg>"
    )


def nice_ticks(peak):
    steps = [60, 300, 600, 900, 1800, 3600, 7200, 10800, 14400, 21600, 43200]
    step = steps[-1]
    for candidate in steps:
        if peak / candidate <= 4:
            step = candidate
            break
    ticks, value = [], 0
    while value <= peak:
        ticks.append(value)
        value += step
    return ticks


def render_months(stats):
    if not stats.by_month:
        return f"<div class='empty'>{tr('common.no_data')}</div>"

    months = sorted(stats.by_month.items())
    peak = max(s for _, s in months)
    # The same rule as the daily average in the cards: the denominator is
    # days with data; days without any event are left out of it.
    days_by_month = stats.observed_by_month

    rows = []
    for (year, month), seconds in months:
        days = days_by_month.get((year, month), 0)
        avg = seconds / days if days else 0
        rows.append(
            f"<tr><td class='name'>{tr('by_month.row', month=i18n.month_name(month), year=year)}</td>"
            f"<td><div class='bar'><i style='width:{pct(seconds, peak):.2f}%'></i></div></td>"
            f"<td class='num'>{aligned_duration(seconds)}</td>"
            f"<td class='pct'>{tr('by_month.days', n=days)}</td>"
            f"<td class='num wide'>{aligned_duration(avg, tr('by_month.per_day'))}</td></tr>"
        )

    # Days without any event are listed here, not in the banner: the table
    # is about days per month anyway, and these days explain why a month
    # has fewer "d" than calendar days.
    gaps = ""
    if stats.missing_days:
        gaps = (
            "<div class='tiny'>"
            + tr("by_month.gaps", days=counted(len(stats.missing_days), "day"),
                 list=esc(missing_label(stats.missing_days)))
            + "</div>"
        )
    return table("".join(rows)) + gaps


def heat_bounds(grid):
    """Upper bounds of heatmap levels 1–4; anything above the fourth is the peak.

    The bounds are quantiles of the non-empty cells, not fractions of the
    maximum: on a linear scale one dense cell would take the whole top
    level and the rest would clump in the lower ones. Here levels 1–4
    split the lower (1 − HEAT_PEAK_SHARE) of the cells evenly, and the
    peak is roughly the top 5%. This only lays out the ready-made
    stats.heatmap matrix for display.
    """
    values = sorted(v for row in grid for v in row if v > 0)
    if not values:
        return []

    def quantile(share):
        rank = max(1, math.ceil(share * len(values)))
        return values[min(rank, len(values)) - 1]

    base = 1 - config.HEAT_PEAK_SHARE
    return [quantile(base * k / 4) for k in (1, 2, 3, 4)]


def heat_level(seconds, bounds):
    """0 — empty cell, 1–4 — levels, 5 — peak."""
    if seconds <= 0:
        return 0
    for level, bound in enumerate(bounds, 1):
        if seconds <= bound:
            return level
    return 5


HEAT_CLASSES = ("", "h1", "h2", "h3", "h4", "hp")


def render_heatmap(stats):
    peak = max((max(row) for row in stats.heatmap), default=0.0)
    if peak <= 0:
        return f"<div class='empty'>{tr('common.no_data')}</div>"

    bounds = heat_bounds(stats.heatmap)

    # Labels for every hour are in the markup: the invisible "minor" ones
    # show up when their hour is hovered. data-d / data-h tie a cell to its
    # labels for highlighting, data-t is the text of our own tooltip (no
    # title, so the system tooltip does not appear as well).
    cells = ["<div class='heat-box'><div class='heat'><div></div>"]
    for hour in range(24):
        minor = "" if hour % 3 == 0 else " minor"
        cells.append(f"<div class='hour{minor}' data-h='{hour}'>{hour}</div>")

    for weekday in range(7):
        day = i18n.weekday_short(weekday)
        cells.append(f"<div class='lbl' data-d='{weekday}'>{day}</div>")
        for hour in range(24):
            seconds = stats.heatmap[weekday][hour]
            value = fmt_duration(seconds) if seconds else tr("heat.empty")
            text = tr("heat.tip", day=day, start=f"{hour:02d}:00",
                      end=f"{(hour + 1) % 24:02d}:00", value=value)
            klass = HEAT_CLASSES[heat_level(seconds, bounds)]
            cells.append(
                f"<div class='cell {klass}' data-d='{weekday}' data-h='{hour}' "
                f"data-t='{esc(text)}' aria-label='{esc(text)}'></div>"
            )
    cells.append("</div><div class='heat-tip elev-12' role='tooltip' hidden></div></div>")

    # Legend for the scale: empty, four levels with their bounds in the
    # tooltips, and the peak separately — it has a different colour, so it
    # is worth naming in words.
    lower = [0.0] + bounds[:3]
    steps = "".join(
        f"<span class='h{i}' title='"
        + esc(tr("heat.range", low=fmt_duration(lo), high=fmt_duration(hi)))
        + "'></span>"
        for i, (lo, hi) in enumerate(zip(lower, bounds), 1)
    )
    share = f"{config.HEAT_PEAK_SHARE * 100:g}%"
    cells.append(
        f"<div class='legend'>{tr('heat.less')}<span title='{tr('heat.empty')}'></span>{steps}"
        f"{tr('heat.more')}<span class='sep'>·</span><span class='hp'></span>"
        + tr("heat.peak", share=share, duration=esc(fmt_duration(bounds[3])))
        + "<span class='sep'>·</span>"
        + tr("heat.densest", duration=esc(fmt_duration(peak)))
        + "</div>"
    )
    return "".join(cells)


def stat_tile(label, value, sub, title=""):
    """A stat tile: label, number and a line on where it comes from."""
    attr = f" title='{esc(title)}'" if title else ""
    return (
        f"<div class='kpi elev-2'{attr}><div class='kpi-top'>"
        f"<span class='kpi-label'>{esc(label)}</span></div>"
        f"<div class='kpi-value' style='{t('h6')}'>{esc(value)}</div>"
        f"<div class='kpi-sub'>{esc(sub)}</div></div>"
    )


def render_focus(stats):
    """Attention fragmentation: how long the stretches of work are.

    The numbers come ready from aw_data.focus_stats; only layout here.
    """
    focus = stats.focus
    if not focus.blocks:
        return f"<div class='empty'>{tr('common.no_data')}</div>"

    deep = fmt_duration(config.FOCUS_DEEP_SECONDS)
    tiles = "".join([
        stat_tile(tr("focus.switches"),
                  tr("focus.per_hour", value=f"{focus.switches_per_hour:.1f}"),
                  tr("focus.switches_sub", n=focus.switches)),
        stat_tile(tr("focus.deep"), f"{focus.deep_share * 100:.0f}%",
                  tr("focus.deep_sub", duration=deep),
                  tr("focus.deep_title", deep=fmt_duration(focus.deep_seconds),
                     duration=deep, total=fmt_duration(focus.seconds))),
        stat_tile(tr("focus.average"), fmt_duration(focus.avg_block),
                  counted(focus.blocks, "block")),
    ])

    colors = category_vars(stats.category_order)
    rows = []
    for c in focus.by_category:
        color = color_of(c.category, colors)
        name = category_label(c.category)
        title = tr("focus.row_title", category=name, blocks=counted(c.blocks, "block"),
                   rate=f"{c.switches_per_hour:.1f}")
        rows.append(
            f"<tr title='{esc(title)}'>"
            f"<td class='name'>{icons.icon(c.category, color)}{esc(name)}</td>"
            f"<td><div class='bar'><i style='width:{c.deep_share * 100:.2f}%;"
            f"background:{color}'></i></div></td>"
            f"<td class='pct'>{c.deep_share * 100:.0f}%</td>"
            f"<td class='num'>{esc(fmt_duration(c.avg_block))}</td></tr>"
        )

    return f"""<div class='tiles'>{tiles}</div>
    <div class='table-cap'>{tr('focus.caption', duration=deep)}</div>
    {table("".join(rows))}
    <div class='push'></div>
    <div class="note-block">
      <details id="d-focus">
        <summary>{tr('common.how')}</summary>
        <p>{tr('focus.note_block', dwell=esc(fmt_duration(config.FOCUS_MIN_DWELL_SECONDS)))}</p>
        <p>{tr('focus.note_pause', gap=esc(fmt_duration(config.SESSION_GAP_SECONDS)))}</p>
        <p>{tr('focus.note_deep', duration=esc(deep))}</p>
      </details>
    </div>"""


def rhythm_weeks_visible(stats, total):
    """How many weeks to show so "Daily rhythm" ends level with the
    neighbouring "Attention fragmentation".

    On the left under the tiles is the category table, on the right the
    weeks. The axis row and the "Earlier weeks" row take the place of two
    categories, so two fewer weeks are visible than there are categories.
    If only one week would have to be hidden, all are shown: the
    collapsible row would take as much room as the week itself.
    """
    visible = max(3, len(stats.focus.by_category) - 2)
    return total if total <= visible + 1 else visible


def render_rhythm(stats):
    """Daily rhythm: when activity usually starts and ends.

    Bounds are seconds from the start of the logical day
    (config.DAY_START_SECONDS), so the track runs from that hour to the
    same hour the next day, and an end at 01:40 sits to the right of
    23:00, not at the left edge.
    """
    rhythm = stats.rhythm
    if not rhythm.days or rhythm.typical_start is None or rhythm.typical_end is None:
        return f"<div class='empty'>{tr('common.no_data')}</div>"

    day = 24 * 60 * 60
    share = pct(rhythm.after_midnight_seconds, stats.total_seconds)
    tiles = "".join([
        stat_tile(tr("rhythm.start"), aw_data.fmt_clock(rhythm.typical_start),
                  tr("rhythm.median", days=counted(rhythm.start_days, "day"))),
        stat_tile(tr("rhythm.end"), aw_data.fmt_clock(rhythm.typical_end),
                  tr("rhythm.median", days=counted(rhythm.end_days, "day"))),
        stat_tile(tr("rhythm.after"), f"{share:.0f}%",
                  fmt_duration(rhythm.after_midnight_seconds),
                  tr("rhythm.after_title",
                     duration=fmt_duration(rhythm.after_midnight_seconds),
                     days=counted(rhythm.after_midnight_days, "day"))),
    ])

    # A week is labelled by its Monday in a fixed short format: equal
    # width, no ranges of varying length. The full range, number of days
    # and time after midnight are in the row tooltip. The newest week is
    # on top; earlier ones are hidden first.
    rows = []
    for week in reversed(rhythm.weeks):
        label = f"<td class='week'>{i18n.date_short(week.monday)}</td>"
        sunday = week.monday + timedelta(days=6)
        period = tr("rhythm.week", start=i18n.date_short(week.monday),
                    end=i18n.date_short(sunday))
        if week.start is None or week.end is None:
            reason = tr("rhythm.no_data") if not week.days else tr("rhythm.unknown")
            title = tr("rhythm.week_missing", period=period, reason=reason)
            rows.append(f"<tr title='{esc(title)}'>{label}"
                        "<td><div class='bar'></div></td>"
                        "<td class='num muted'>—</td></tr>")
            continue
        span = (f"{aw_data.fmt_clock(week.start)}–"
                f"{aw_data.fmt_clock(week.end)}")
        title = tr("rhythm.week_title", period=period, span=span,
                   days=counted(week.days, "day"),
                   duration=fmt_duration(week.after_midnight))
        rows.append(
            f"<tr title='{esc(title)}'>{label}"
            f"<td><div class='bar'><i style='margin-left:{pct(week.start, day):.2f}%;"
            f"width:{pct(max(week.end - week.start, 0), day):.2f}%'></i></div></td>"
            f"<td class='num'>{span}</td></tr>"
        )

    # Axis ticks every 6 hours from the start of the logical day. The axis
    # row comes first: with table-layout: fixed it is the one that sets
    # the column widths.
    ticks = "".join(
        f"<span>{aw_data.fmt_clock(h * 3600)[:2]}</span>" for h in range(0, 25, 6)
    )
    axis = (f"<tr class='axis-row'><td class='week'></td><td><div class='ticks'>{ticks}</div></td>"
            "<td class='num'></td></tr>")

    visible = rhythm_weeks_visible(stats, len(rows))
    weeks = table(axis + "".join(rows[:visible]))
    older = rows[visible:]
    if older:
        weeks += (
            f"<details id='d-rhythm-weeks'><summary>{tr('rhythm.older', n=len(older))}"
            f"</summary>{table(''.join(older))}</details>"
        )

    start = aw_data.fmt_clock(0)
    return f"""<div class='tiles'>{tiles}</div>
    <div class='table-cap'>{tr('rhythm.caption')}</div>
    {weeks}
    <div class='push'></div>
    <div class="note-block">
      <details id="d-rhythm">
        <summary>{tr('common.how')}</summary>
        <p>{tr('rhythm.note_day', start=start)}</p>
        <p>{tr('rhythm.note_bounds')}</p>
        <p>{tr('rhythm.note_after', start=start)}</p>
      </details>
    </div>"""


def render_games(stats):
    """Games as a list of recent sessions: game, how long ago, duration."""
    today = datetime.now().astimezone().date()
    if not stats.games:
        return (
            "<div class='empty'>"
            + tr("games.none", category=i18n.quoted(esc(config.GAME_CATEGORY)))
            + "</div>" + render_unplayed_games(stats)
        )

    best = stats.games_best_day
    summary = "".join(
        f"<div class='kpi elev-2'><div class='kpi-top'>"
        f"<span class='kpi-label'>{esc(label)}</span></div>"
        f"<div class='kpi-value' style='{t('h6')}'>{esc(value)}</div></div>"
        for label, value in [
            (tr("games.total"), fmt_duration(stats.games_total)),
            (tr("games.distinct"), str(len(stats.games))),
            (tr("games.best_day"),
             tr("games.best_value", date=i18n.date_numeric(best[0]),
                duration=fmt_duration(best[1])) if best else "—"),
        ]
    )

    # The list is sorted by recency: whatever was played last comes first.
    recent = sorted(stats.games, key=lambda g: g.last_played, reverse=True)
    rows = []
    for game in recent:
        sub = tr("games.sub", ago=ago(game.last_played, today),
                 sessions=counted(game.session_count, "session"),
                 duration=fmt_duration(game.longest_session))
        rows.append(
            "<div class='row-card elev-2'>"
            f"<span class='ricon'>{icons.icon(config.GAME_CATEGORY, 'var(--cat-1)', 28)}</span>"
            f"<div class='rc-main'><div class='rc-title'>{esc(game.app)}</div>"
            f"<div class='rc-sub'>{esc(sub)}</div></div>"
            f"<span class='rc-value'>{esc(fmt_duration(game.total_seconds))}</span>"
            "</div>"
        )

    return (
        f"<div class='tiles'>{summary}</div>"
        f"{collapse_rows(rows, config.GAMES_VISIBLE, 'd-games-rest', tr('common.show_all'))}"
        "<div class='tiny'>"
        + tr("games.order", duration=esc(fmt_duration(config.GAME_SESSION_GAP_SECONDS)))
        + "</div>"
        + render_unplayed_games(stats)
    )


def render_unplayed_games(stats):
    if not stats.games_unplayed:
        return ""
    items = "".join(
        f"<li>{esc(name)} <code>{esc(', '.join(processes))}</code></li>"
        for name, processes in stats.games_unplayed
    )
    return f"""<details id="d-unplayed">
      <summary>{tr('games.unplayed', n=len(stats.games_unplayed))}</summary>
      <ul class='unplayed'>{items}</ul>
    </details>"""


def render_sessions(stats):
    if not stats.sessions:
        return ("<div class='empty'>"
                + tr("sessions.none", duration=fmt_duration(config.MIN_SESSION_SECONDS))
                + "</div>")

    rows = []
    for i, s in enumerate(stats.sessions, 1):
        when = tr("sessions.when", date=i18n.date_numeric(s.start),
                  start=f"{s.start:%H:%M}", end=f"{s.end:%H:%M}")
        rows.append(
            "<div class='row-card elev-2'>"
            f"<span class='pos'>{i}</span>"
            f"<div class='rc-main'><div class='rc-title'>{esc(i18n.app_label(s.app))}</div>"
            f"<div class='rc-sub'>{when}</div></div>"
            f"<span class='rc-value'>{esc(fmt_duration(s.active_seconds))}</span>"
            "</div>"
        )
    return f"<div class='rows'>{''.join(rows)}</div>"


# --------------------------------------------------------------------------
# Script
# --------------------------------------------------------------------------

SCRIPT = """
(function () {
  "use strict";
  var KEY = "aw-dashboard-ui";

  // A file opened from disk has the origin "null", and some browsers throw
  // on localStorage access then. In that case we simply work without
  // saving: the theme comes from config, and the console stays quiet.
  var store = (function () {
    try {
      var probe = "__aw__";
      window.localStorage.setItem(probe, "1");
      window.localStorage.removeItem(probe);
      return window.localStorage;
    } catch (e) {
      return null;
    }
  })();

  function load() {
    if (!store) return {};
    try { return JSON.parse(store.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save(state) {
    if (!store) return;
    try { store.setItem(KEY, JSON.stringify(state)); } catch (e) { /* quietly */ }
  }

  var state = load();
  var menu = document.getElementById("thememenu");

  // --- Theme --------------------------------------------------------------
  var radios = document.querySelectorAll(".theme-radio");
  if (state.theme) {
    var saved = document.getElementById("th-" + state.theme);
    if (saved) saved.checked = true;
  }
  Array.prototype.forEach.call(radios, function (radio) {
    radio.addEventListener("change", function () {
      if (!radio.checked) return;
      state.theme = radio.id.slice(3);
      save(state);
      if (menu) menu.open = false;          // close after choosing
    });
  });

  // --- Menu ---------------------------------------------------------------
  if (menu) {
    document.addEventListener("click", function (event) {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape" || !menu.open) return;
      menu.open = false;
      var summary = menu.querySelector("summary");
      if (summary) summary.focus();
    });
  }

  // --- Heatmap ------------------------------------------------------------
  // One handler for the whole grid (delegation). The event only remembers
  // the cell; all work happens once per frame in requestAnimationFrame.
  // The text and the label highlight change only when moving to another
  // cell; the tooltip is always in the DOM, shown by a class (opacity) and
  // placed with transform, so the page layout is not recalculated. Without
  // the script the map still works, just without the tooltip.
  var heatBox = document.querySelector(".heat-box");
  if (heatBox) {
    var tip = heatBox.querySelector(".heat-tip");
    tip.hidden = false;
    var labels = {d: {}, h: {}};
    Array.prototype.forEach.call(heatBox.querySelectorAll(".lbl[data-d]"),
      function (el) { labels.d[el.dataset.d] = el; });
    Array.prototype.forEach.call(heatBox.querySelectorAll(".hour[data-h]"),
      function (el) { labels.h[el.dataset.h] = el; });
    var shown = null, wanted = null, frame = 0;

    var render = function () {
      frame = 0;
      if (wanted === shown) return;
      if (shown) {
        labels.d[shown.dataset.d].classList.remove("hl");
        labels.h[shown.dataset.h].classList.remove("hl");
      }
      shown = wanted;
      if (!shown) { tip.classList.remove("on"); return; }
      labels.d[shown.dataset.d].classList.add("hl");
      labels.h[shown.dataset.h].classList.add("hl");
      tip.textContent = shown.dataset.t;
      // Geometry: the cell without its scale (offset*), the tooltip read
      // once after the text change, and only once per frame.
      var cx = shown.offsetLeft + shown.offsetWidth / 2;
      var w = tip.offsetWidth, h = tip.offsetHeight;
      var x = Math.max(0, Math.min(cx - w / 2, heatBox.clientWidth - w));
      var y = shown.offsetTop - h - 8;
      if (y < 0) y = shown.offsetTop + shown.offsetHeight + 8;
      tip.style.transform = "translate(" + Math.round(x) + "px," + Math.round(y) + "px)";
      tip.classList.add("on");
    };
    var schedule = function (cell) {
      wanted = cell;
      if (!frame) frame = requestAnimationFrame(render);
    };
    heatBox.addEventListener("mouseover", function (event) {
      var cell = event.target.closest(".cell");
      if (cell) schedule(cell);
    });
    heatBox.addEventListener("mouseleave", function () { schedule(null); });
  }

  // --- Expanded blocks ----------------------------------------------------
  // The only part of the layout that can be changed from the page itself,
  // so that is what we remember.
  state.open = state.open || {};
  var blocks = document.querySelectorAll("details[id]");
  Array.prototype.forEach.call(blocks, function (block) {
    if (block === menu) return;
    if (state.open[block.id]) block.open = true;
    block.addEventListener("toggle", function () {
      state.open[block.id] = block.open;
      save(state);
    });
  });
})();
"""


# --------------------------------------------------------------------------


def render(stats, font_css="", font_warnings=(), demo=False):
    warn = ""
    if not stats.afk_filtered:
        warn += f"<div class='warn'>{tr('warn.no_afk')}</div>"
    if stats.categories_created:
        warn += (f"<div class='warn'>"
                 f"{tr('warn.created', file=esc(config.CATEGORIES_FILE))}</div>")
    messages = list(stats.category_warnings) + list(font_warnings)
    if messages:
        items = "".join(f"<li>{esc(m)}</li>" for m in messages)
        warn += f"<div class='warn'>{tr('common.warnings')}<ul>{items}</ul></div>"

    radios = "".join(
        f'<input class="theme-radio" type="radio" name="theme" id="th-{item["id"]}"'
        f'{" checked" if item["id"] == theme.default_theme()["id"] else ""}>'
        for item in theme.THEMES
    )
    generated = datetime.now().astimezone()
    # In demo mode the report says so in the footer, quietly: a warning
    # box would end up on every screenshot.
    demo_note = f"<p>{tr('warn.demo')}</p>" if demo else ""

    def head(glyph, title):
        return (f"<div class='panel-head'>"
                f"{icons.ui_icon(glyph, 'var(--primary)', 20)}"
                f"<h2>{esc(title)}</h2></div>")

    return f"""<!DOCTYPE html>
<html lang="{tr('lang')}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tr('title')}</title>
<style>
{font_css}
{build_css()}
{theme.theme_css()}
</style>
</head>
<body>
{radios}
<div class="page">
<div class="wrap">
  {render_topbar(stats)}
  {warn}
  {render_banner(stats)}
  {render_kpis(stats)}

  <div class="panel elev-6">
    {head("trend", tr("days.title", days=counted(config.RECENT_DAYS, "day")))}
    {render_days(stats)}
  </div>

  <div class="cols stretch">
    <div class="panel elev-6">
      {head("chart", tr("apps.title"))}
      {render_apps(stats)}
    </div>
    <div class="col-stack">
      <div class="panel natural elev-6">
        {head("layers", tr("categories.title"))}
        {render_categories(stats)}
      </div>
      {render_split(stats)}
    </div>
  </div>

  <div class="panel elev-6">
    {head("games", tr("games.title"))}
    {render_games(stats)}
  </div>

  <div class="panel elev-6">
    {head("grid", tr("heat.title"))}
    {render_heatmap(stats)}
  </div>

  <div class="cols even">
    <div class="panel fill elev-6">
      {head("focus", tr("focus.title"))}
      {render_focus(stats)}
    </div>
    <div class="panel fill elev-6">
      {head("moon", tr("rhythm.title"))}
      {render_rhythm(stats)}
    </div>
  </div>

  <div class="cols even">
    <div class="panel elev-6">
      {head("stopwatch", tr("sessions.title"))}
      {render_sessions(stats)}
    </div>
    <div class="panel elev-6">
      {head("calendar", tr("by_month.title"))}
      {render_months(stats)}
    </div>
  </div>

  <footer>
    <details id="d-about">
      <summary>{tr('footer.about')}</summary>
      <p>{tr('footer.generated', date=i18n.date_numeric(generated), time=f"{generated:%H:%M}")}</p>
      <p>{tr('footer.sessions', duration=fmt_duration(config.SESSION_GAP_SECONDS))}</p>
      <p>{tr('footer.design')}</p>{demo_note}
    </details>
  </footer>
</div>
</div>
<script>{SCRIPT}</script>
</body>
</html>
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build the ActivityWatch HTML report.")
    parser.add_argument("--lang", help="interface language (a file in locales/), "
                        "overrides config.LANGUAGE")
    parser.add_argument("--demo", action="store_true",
                        help="use made-up data instead of ActivityWatch, for screenshots")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.lang:
        i18n.set_language(args.lang)
    demo_mode = args.demo or config.DEMO

    try:
        if demo_mode:
            import demo
            stats = demo.collect_stats()
        else:
            stats = aw_data.collect_stats()
    except ActivityWatchError as e:
        print(e)
        sys.exit(1)

    font_css, font_warnings, font_bytes = fonts.face_css()
    for warning in font_warnings:
        print(f"  ! {warning}")

    page = render(stats, font_css, font_warnings, demo=demo_mode)
    name = config.DEMO_OUTPUT_FILE if demo_mode else config.OUTPUT_FILE
    output = Path(__file__).resolve().parent / name
    output.write_text(page, encoding="utf-8")

    size = output.stat().st_size
    print(tr("cli.saved", path=output))
    print(tr("cli.size", kb=f"{size / 1024:.1f}"), end="")
    if font_bytes:
        print(tr("cli.font_size", kb=f"{font_bytes / 1024:.1f}"))
    else:
        print(tr("cli.no_font"))

    if demo_mode:
        # Made-up data does not belong in the archive of real reports.
        print(tr("cli.demo"))
    else:
        # An archive failure does not cancel the report: the main file is
        # already written.
        try:
            copy, removed = archive.save_copy(page)
        except OSError as e:
            print(tr("cli.archive_failed", error=e))
        else:
            if copy:
                print(tr("cli.archived", path=copy.relative_to(output.parent)))
            if removed:
                print(tr("cli.pruned", n=len(removed), limit=config.ARCHIVE_KEEP))

    failures = [row for row in theme.audit() if not row[4]]
    if failures:
        print("\n" + tr("cli.contrast", n=len(failures)))
        for item, label, ratio, threshold, _ in failures:
            print(f"  {item['name']}: {label} — {ratio:.2f}:1 < {threshold}")


if __name__ == "__main__":
    main()
