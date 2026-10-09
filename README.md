# aw-dashboard

[Українською](README.uk.md)

An offline report for [ActivityWatch](https://activitywatch.net/) data.
It reads events from the local ActivityWatch API, computes statistics and
writes **one self-contained HTML file**. The file opens with a double
click and works without a network connection: CSS, charts, icons and
script are all inside, with no CDN or external requests.

![Dashboard with demo data](docs/screenshot.png)

*The screenshot uses made-up demo data (`python report.py --demo`).*

## What's in the report

- **Active days.** Days with activity out of all calendar days since
  the first event.
- **Totals.** Active time, average per day and time in games.
- **Last 30 days.** Activity per day.
- **Top applications and categories.** Categories come from your own
  `categories.json`.
- **Computer-on time.** Split into active time, other time at the
  computer, and AFK.
- **Games.** Recent launches, session counts, the longest session, and
  games that are installed but have not been launched.
- **Heatmap.** Weekday × hour, with a quantile scale.
- **Attention fragmentation.** Switches per hour, the share of time in
  deep blocks (over 25 minutes) and the average block.
- **Daily rhythm.** Median start and end of the day, week by week, and
  time after midnight.
- **Longest sessions and a per-month table.**
- **Ten color themes.** Three dark, three light, three monochrome, plus
  Midnight. They switch without JavaScript.

All numbers are computed in `aw_data.py`. `report.py` only lays them
out.

## Requirements

- Python 3.10 or newer.
- [`requests`](https://pypi.org/project/requests/).
- ActivityWatch running at `http://localhost:5600`, with
  `aw-watcher-window` and, ideally, `aw-watcher-afk`. Without the AFK
  watcher, time is counted without the away filter and the report says
  so.
- Optional: Chrome or Edge, for the layout check in `check_layout.py`.

Report generation works on any OS. The desktop shortcut
(`launch.pyw`, `make_shortcut.ps1`) and the default game library paths
in `scan_games.py` are Windows-specific.

## Installation

```bash
git clone <this repository>
cd aw-dashboard
pip install requests
```

## Running

```bash
python report.py                  # build dashboard.html from your data
python report.py --lang en        # same, with the interface in English
python report.py --demo           # made-up data → dashboard-demo.html
python report.py --demo --lang en
```

`report.py` prints the path of the report. It does not open a browser.

Other tools:

```bash
python aw_data.py         # plain-text summary in the terminal, no HTML
python scan_games.py      # find installed games and add them to categories.json
python theme.py           # contrast audit of all themes (WCAG 4.5:1 / 3:1)
python check_layout.py    # layout check in headless Chrome/Edge at 4 widths
python make_icon.py       # redraw dashboard.ico
```

### Desktop shortcut (Windows)

```bash
powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
```

This creates a shortcut that runs `launch.pyw` with `pythonw.exe`. The
report is rebuilt and opened in your browser with no console window.
Errors are shown in a message box. To name the shortcut yourself, add
`-Name "My report"`.

### Archive

Every real run (but not `--demo`) also saves
`archive/dashboard-YYYY-MM-DD.html`. Running again on the same day
overwrites that day's copy. Only the newest `ARCHIVE_KEEP` (30) copies
are kept. Set `ARCHIVE_KEEP = 0` to turn the archive off; the existing
copies are not deleted.

## Configuration

### `config.py`

| Setting | Default | Meaning |
|---|---|---|
| `LANGUAGE` | `"uk"` | Interface language: `"uk"` or `"en"`. Also sets the duration and date formats. `--lang` overrides it for one run. |
| `DEFAULT_THEME` | `"midnight"` | Theme shown first. The choice made in the menu is remembered in the browser. |
| `API` | `http://localhost:5600/api/0` | ActivityWatch API. |
| `GAME_CATEGORY` | `"Ігри"` | Name of the category in `categories.json` that holds games. |
| `SYSTEM_PROCESSES` | — | Shell processes left out of the statistics completely. |
| `AFK_LENIENT_CAP_SECONDS` | 30 min | Maximum AFK credited to a `lenient` category from each AFK stretch. |
| `SESSION_GAP_SECONDS` | 120 | A pause longer than this ends a session or focus block. |
| `GAME_SESSION_GAP_SECONDS` | 600 | Same, for games (loading screens, matchmaking). |
| `FOCUS_MIN_DWELL_SECONDS` | 10 | Focus shorter than this is a pass-through, not a switch. |
| `FOCUS_DEEP_SECONDS` | 25 min | Blocks longer than this count as deep. |
| `DAY_START_SECONDS` | 06:00 | When the logical day starts in the daily rhythm. |
| `ICON_SHAPE` | `"rounded_square"` | Icon plates: `circle`, `rounded_square`, `squircle` or `hexagon`. |
| `EMBED_FONT` | `False` | Embed Roboto from `fonts/` as base64. Otherwise the system font is used. |
| `ARCHIVE_KEEP` | 30 | Number of daily copies to keep; `0` turns the archive off. |
| `DEMO` | `False` | Always use demo data, as with `--demo`. |

Each threshold in `config.py` has a comment explaining why it has that
value.

Themes: `midnight`, `indigo-teal`, `deep-purple-amber`, `blue-grey-cyan`,
`indigo-pink`, `teal-deep-orange`, `brown-light-green`, `blue-mono`,
`red-mono`, `blue-red`.

### `categories.json`

This file maps applications to categories. It is created from a starter
set on the first run, and from then on you edit it by hand:

```json
{
  "Ігри": {
    "afk_policy": "strict",
    "processes": ["eldenring", "factorio"],
    "patterns": []
  },
  "Спілкування": {
    "afk_policy": "lenient",
    "processes": ["discord", "zoom", "telegram"],
    "patterns": []
  }
}
```

- **`processes`** are exact process names. Matching ignores case, and
  `.exe` is optional.
- **`patterns`** are substrings of the process name. An exact name
  always wins over a pattern. If patterns from several categories
  match, the category listed first wins, and the conflict is shown in
  the report.
- **`afk_policy`** can be `strict` or `lenient`.
  - `strict` (the default) counts only time when you are using the
    keyboard and mouse.
  - `lenient` also counts AFK time while the category's window is in
    focus, up to `AFK_LENIENT_CAP_SECONDS` per AFK stretch. It is meant
    for calls and videos, where you listen without touching anything.
- **Colors.** Category colors follow the order of the file: the first
  six categories get the theme's six category colors. Categories under
  3% of the time are merged into "Other".
- **Names.** Category names are your own data and appear in the report
  as written. The starter set uses Ukrainian names. To use other names,
  rename the keys, and if you rename the games category, also set
  `GAME_CATEGORY` in `config.py`.

`aw-watcher-window` reports only the process name, not the path. That
means a rule like "everything under `steamapps\common` is a game" can't
be applied to events. `scan_games.py` applies it on disk instead: it
scans your Steam, GOG and Epic libraries (`STEAM_ROOTS`,
`GAME_LIBRARY_ROOTS`) and adds the exact executable names to the games
category. Use `--dry-run` to preview the changes.

### Application names

Display names instead of exe names (`"code.exe": "VS Code"`) live in
`app_names.local.json`, which is kept out of git. To start, copy the
example:

```bash
cp app_names.example.json app_names.local.json
```

While there is no local file, `app_names.example.json` is used. Keys are
case-insensitive, and several executables may map to one name; their
time adds up. Names of Windows system programs (Task Manager, File
Explorer, Command Prompt and so on) come from the `app_names` section of
`locales/*.json`, so they follow the interface language. Your file
overrides them.

### Adding a language

1. Copy `locales/en.json` to `locales/<code>.json` and translate the
   values. Keep the `{placeholders}`, and keep the HTML tags such as
   `<b>` and `<code>`.
   This includes the `app_names` section with names of system programs.
2. If the language has more than two plural forms, add a rule to
   `PLURAL_RULES` in `i18n.py`, as is done for Ukrainian.
3. Set `LANGUAGE = "<code>"` or run `python report.py --lang <code>`.

## Demo mode

`python report.py --demo` doesn't read ActivityWatch and doesn't touch
`categories.json`:

- **Data.** `demo.py` generates about ten weeks of window and AFK
  events ending today, using a fixed seed. The data includes days with
  the computer off, calls, late nights and games.
- **Pipeline.** The events go through the same `aw_data.collect_stats`
  as real data, so every section is computed for real. Only the input
  is made up.
- **Output.** The result is written to `dashboard-demo.html` and is
  never archived. The report footer marks it as demo data.
- **Language.** Category names follow the active language.

Use demo mode for screenshots, or to try the report without
ActivityWatch.

## Project layout

| File | Responsibility |
|---|---|
| `aw_data.py` | ActivityWatch API requests and all calculations. |
| `report.py` | HTML rendering only: layout, SVG charts, inline script. |
| `i18n.py`, `locales/` | Interface strings, plural forms, duration and date formats. |
| `demo.py` | Synthetic data for demo mode. |
| `config.py` | Settings and thresholds. |
| `app_names.py`, `app_names.example.json` | Display names for executables. |
| `categories.py`, `categories.json` | Category storage, matching and conflict detection. |
| `theme.py` | Palettes (Material Design 2014), elevation, typography, contrast audit. |
| `icons.py`, `assets/icons/` | Phosphor duotone icons, inlined into the HTML. |
| `fonts.py` | Optional Roboto embedding. |
| `archive.py` | Daily report copies and their rotation. |
| `check_layout.py` | Layout geometry checks in a headless browser. |
| `scan_games.py` | Steam, GOG and Epic library scanner. |
| `launch.pyw`, `make_shortcut.ps1`, `make_icon.py` | Desktop shortcut and its icon. |

## Privacy

Everything stays on your computer. The report is a local file built
from your local ActivityWatch database, and it makes no network
requests when opened. The generated reports, `archive/`,
`categories.json` and `app_names.local.json` describe your habits, so
they are all in `.gitignore`. Think before sharing them.

## License

[MIT](LICENSE) © 2026 closedude.

## Credits

- Icons: [Phosphor Icons](https://phosphoricons.com/), MIT license. See
  [`licenses/phosphor.txt`](licenses/phosphor.txt).
- Colors: Material Design 2014 palettes.
