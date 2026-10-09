"""Report settings. Edit them here — the other modules hard-code nothing."""

# --- Connection ----------------------------------------------------------

API = "http://localhost:5600/api/0"
TIMEOUT = 30

# --- Language ------------------------------------------------------------

# Interface language: a file name in locales/ without .json ("uk", "en").
# It also decides plural forms, the duration format and date formats.
# Can be overridden for one run with: python report.py --lang en
LANGUAGE = "uk"

# --- Output --------------------------------------------------------------

OUTPUT_FILE = "dashboard.html"

# Archive: on every build a copy of the report goes here as
# dashboard-YYYY-MM-DD.html, named by the build date. Building again on
# the same day overwrites that copy. The folder is in .gitignore; if you
# rename it here, change it there too.
ARCHIVE_DIR = "archive"

# How many daily copies to keep. The oldest ones beyond the limit are
# deleted. A copy is about 200 KB, so 30 is a month of history and ~6 MB.
# 0 turns the archive off: nothing is written and nothing is deleted.
ARCHIVE_KEEP = 30

# --- Demo ----------------------------------------------------------------

# Demo mode builds the report from made-up data (demo.py) instead of
# ActivityWatch — for screenshots that should not show real activity.
# Usually turned on per run: python report.py --demo
DEMO = False

# The demo report goes to its own file and is never archived.
DEMO_OUTPUT_FILE = "dashboard-demo.html"

# --- Appearance ----------------------------------------------------------

# Default theme. See theme.py for the available ids:
#   dark:        midnight, indigo-teal, deep-purple-amber, blue-grey-cyan
#   light:       indigo-pink, teal-deep-orange, brown-light-green
#   monochrome:  blue-mono, red-mono, blue-red
# If the browser allows localStorage, the theme picked in the menu
# overrides this value the next time the report is opened.
DEFAULT_THEME = "midnight"

# Shape of the plate under icons:
#   circle, rounded_square, squircle, hexagon
ICON_SHAPE = "rounded_square"

# --- Font ----------------------------------------------------------------

# Roboto is used if installed in the system; otherwise the system fallback.
FONT_STACK = "'Roboto', 'Segoe UI', system-ui, sans-serif"

# Embed the font into the HTML via @font-face with base64. Makes the report
# independent of whether Roboto is installed, but a few hundred KB heavier.
EMBED_FONT = False

# Where to look for font files to embed. Order matters.
# Supported: .woff2 (the lightest), .woff and .ttf.
FONT_DIR = "fonts"

# Which faces to embed: (weight, base file name without extension).
FONT_FACES = (
    (300, "Roboto-Light"),
    (400, "Roboto-Regular"),
    (500, "Roboto-Medium"),
)

# How many applications the top list shows.
TOP_N = 30

# How many top-list rows are visible at once; the rest go into a
# collapsible block.
APPS_VISIBLE = 8

# The same for the games list.
GAMES_VISIBLE = 6
# Share of the densest non-empty heatmap cells that goes to the top "peak"
# level. The rest is split into 4 equal levels.
HEAT_PEAK_SHARE = 0.05

# How many recent days the activity chart shows.
RECENT_DAYS = 30

# --- Noise filters -------------------------------------------------------

# Applications with less total time than this are not shown (seconds).
MIN_APP_SECONDS = 60

# A day counts as active if at least this much time was collected (seconds).
MIN_DAY_SECONDS = 60

# A pause that does NOT break a continuous session (seconds).
# A short switch to another window or a pause within this time counts as
# part of the same session.
SESSION_GAP_SECONDS = 120

# Sessions shorter than this are not shown (seconds).
MIN_SESSION_SECONDS = 300

# A separate session-break threshold for games (seconds).
#
# It is deliberately larger than SESSION_GAP_SECONDS, because games
# regularly have stretches when the game window is not focused or the
# keyboard and mouse are silent while the game goes on: cutscenes, loading
# screens, a matchmaking queue, a break between rounds, a switch to the
# browser for a guide. With a two-minute threshold one evening of play
# would fall apart into a dozen "sessions". Ten minutes is closer to what
# a person calls one sitting.
GAME_SESSION_GAP_SECONDS = 600

# --- AFK policy ----------------------------------------------------------

# The cap for categories with "afk_policy": "lenient" in categories.json
# (seconds).
#
# For such categories AFK time is credited too while their window is
# focused: on a call or watching a video a person listens and presses
# nothing. But only the first this-many seconds of each continuous AFK
# stretch; the rest of the stretch is dropped. Any touch of the keyboard
# or mouse closes the stretch and the next one starts from zero, so on a
# normal call, where you unmute or reply in chat now and then, the cap
# rarely kicks in.
#
# Why 30 minutes. In call and video windows most AFK stretches are short
# listening pauses of up to 20–25 minutes, and they are credited in full.
# Longer stretches are a mix of real calls and an abandoned computer that
# the events alone cannot tell apart. A cap bounds the cost of a mistake:
# a messenger left open overnight adds at most 30 minutes, not 8 hours.
# The price: a long passive call is undercounted after the 30th minute of
# silence (an untouched two-hour webinar is credited as 30 minutes).
AFK_LENIENT_CAP_SECONDS = 30 * 60

# --- Attention fragmentation ---------------------------------------------

# Minimum stay in an application (seconds). Focus shorter than this is a
# pass-through, not a stay: it does not count as a switch, and its seconds
# go to the ongoing block.
#
# Why 10 seconds. Very short focus runs fall mostly on the shell and
# desktop widgets (the taskbar, alt-tab, tray utilities): focus lands
# there on the way, not because anything is done there. Their share drops
# steadily for longer runs, so around 10 s is where the technical noise
# ends. Without the threshold the switch rate is several times higher and
# mostly measures alt-tab. The price: a very short reply in a messenger
# is not a switch either.
FOCUS_MIN_DWELL_SECONDS = 10

# A block longer than this counts as focused work (seconds).
FOCUS_DEEP_SECONDS = 25 * 60

# --- Daily rhythm --------------------------------------------------------

# Logical day offset (seconds after midnight). A day runs from this time to
# the same time the next day, so a sitting that ended at 02:33 belongs to
# yesterday instead of becoming the start of today.
#
# Why 06:00, not 04:00 or midnight. The boundary should fall where nobody
# sits at the computer, otherwise a late sitting is cut in two and its
# tail becomes "the day started at 04:00". For a night owl the quiet
# window is usually early morning; adjust this if your nights run later
# or your mornings start earlier.
DAY_START_SECONDS = 6 * 60 * 60

# The category the "Games" section is built from. It must match a category
# name in categories.json.
GAME_CATEGORY = "Ігри"

# Games list order: "time" — by total time, "last" — by the date of the
# last launch.
GAMES_SORT = "time"

# How many longest sessions to show.
TOP_SESSIONS = 5

# Windows system processes that get caught for fractions of a second.
# Compared case-insensitively and without the .exe extension — write
# them however is convenient. These processes are filtered out before
# any counting and never reach a category.
SYSTEM_PROCESSES = {
    "searchhost",
    "shellhost",
    "startmenuexperiencehost",
    "pickerhost",
    "applicationframehost",
    "credentialuibroker",
    "lockapp",
    "systemsettings",
    "textinputhost",
    "shellexperiencehost",
    "searchapp",
    "dwm",
    "sihost",
    "runtimebroker",
    "peopleexperiencehost",
    "widgets",
    "widgetboard",
    "appinstaller",
    "rundll32",
    "pcaui",
    "openwith",
}

# Display names instead of exe names (see app_names.py). Your own names go
# into APP_NAMES_FILE, which is kept out of git; while it does not exist,
# the example file is used. Names of Windows system programs come from
# the locale ("app_names" in locales/*.json) and follow the language.
APP_NAMES_FILE = "app_names.local.json"
APP_NAMES_EXAMPLE_FILE = "app_names.example.json"

# Internal key for events without an application name. Shown in the
# report as the localized app.unknown label.
UNKNOWN_APP = "(unknown)"

# --- Categories ----------------------------------------------------------

# The categories themselves live in this file next to the scripts and are
# edited by hand. If it is missing, categories.py creates it from the
# starter set.
CATEGORIES_FILE = "categories.json"

# Internal keys for time outside any category and for small categories
# merged together. They never collide with a name in categories.json and
# are shown in the report as localized labels (category.uncategorized,
# category.other).
UNCATEGORIZED = "__uncategorized__"
CATEGORY_OTHER = "__other__"

# In the "Categories" block, categories with a share of active time below
# this merge into one "Other" row (a share from 0 to 1). "Uncategorized"
# is not subject to the rule: it is always a separate last row.
CATEGORY_OTHER_SHARE = 0.03

# Until uncategorized time reaches this, the hint listing what to add to
# categories.json is not shown. Sorting out three minutes of noise is not
# worth it (seconds).
UNCATEGORIZED_SHOW_SECONDS = 600

# --- Game scanner (scan_games.py) ----------------------------------------

# Steam libraries are found automatically from libraryfolders.vdf.
# Here — where to look for Steam itself.
STEAM_ROOTS = [
    r"C:\Program Files (x86)\Steam",
    r"C:\Steam",
    r"D:\Steam",
]

# Extra library folders: every subfolder counts as a separate game.
# GOG, Epic and anything of your own go here.
GAME_LIBRARY_ROOTS = [
    r"C:\GOG Games",
    r"C:\Program Files (x86)\GOG Galaxy\Games",
    r"C:\Program Files\Epic Games",
    r"D:\Epic Games",
]

# Folders inside a game that contain no game executables.
GAME_SCAN_IGNORE_DIRS = {
    "_commonredist",
    "commonredist",
    "redist",
    "redistributable",
    "redistributables",
    "directx",
    "dotnet",
    "dotnetfx",
    "vcredist",
    "openal",
    "prerequisites",
    "installers",
    "support",
    "tools",
    "sdk",
    "docs",
    "soundtrack",
    "extras",
    "engine",
    "steamworks shared",
    "steam controller configs",
    "steamvr",
}

# Substrings in an exe name that mean "this is not a game".
GAME_SCAN_IGNORE_PATTERNS = (
    "unins",
    "setup",
    "install",
    "redist",
    "vcredist",
    "dxsetup",
    "dxwebsetup",
    "directx",
    "dotnetfx",
    "crashhandler",
    "crashreport",
    "crashpad",
    "errorreport",
    "bugreport",
    "updater",
    "patcher",
    "activation",
    "config",
    "settings",
    "benchmark",
    "server",
    "editor",
    "dedicated",
    "touchup",
    "cleanup",
    "helper",
    "eac",
    "easyanticheat",
    "battleye",
    "vc_",
    "ue4prereq",
    "ue5prereq",
    "epicwebhelper",
    "anticheat",
    "worldbuilder",
    "vbsp",
    "vvis",
    "vrad",
    "hammer",
)

# Names that are too generic: correct for a game, but in categories.json
# they become a trap — any unrelated launcher.exe would land in the games
# category forever. The scanner lists them separately and does not add
# them without --include-generic.
GAME_SCAN_GENERIC_NAMES = {
    "launcher",
    "game",
    "start",
    "play",
    "client",
    "main",
    "app",
    "engine",
    "dosbox",
    "bin",
}

# Small executables are almost always helper utilities, not the game.
MIN_GAME_EXE_BYTES = 400 * 1024
