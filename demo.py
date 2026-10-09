"""Demo mode: made-up activity for screenshots and trying the report out.

    python report.py --demo            (or DEMO = True in config.py)
    python report.py --demo --lang en

Nothing is read from ActivityWatch and categories.json is not touched.
Instead this module generates window and AFK events for about ten weeks
ending today and feeds them through the very same pipeline
(aw_data.collect_stats with replaced data sources). So every section of
the report is computed exactly as for real data — only the input is
synthetic.

The generator is seeded, so the same day gives the same report. The
schedule is relative to today, which keeps the "last 30 days" chart and
the banner populated whenever the demo is run.

Demo categories take their names from the active locale
(demo.categories), so an English demo shows English category names.
The user's app names (app_names.local.json) and config.GAME_CATEGORY are
replaced for the rest of the run: the demo has its own applications and
games category. Windows system programs keep their localized names.
"""

import random
from datetime import datetime, time, timedelta, timezone

import app_names
import aw_data
import categories
import config
from i18n import tr

SEED = 7
DAYS = 75

WINDOW_BUCKET = "aw-watcher-window_demo"
AFK_BUCKET = "aw-watcher-afk_demo"

# Process -> display name. Made-up games, everyday applications. Explorer
# and Task Manager are named by the locale, like for real data.
APPS = {
    "firefox.exe": "Firefox",
    "chrome.exe": "Chrome",
    "code.exe": "VS Code",
    "windowsterminal.exe": "Terminal",
    "obsidian.exe": "Obsidian",
    "figma.exe": "Figma",
    "discord.exe": "Discord",
    "telegram.exe": "Telegram",
    "zoom.exe": "Zoom",
    "vlc.exe": "VLC",
    "spotify.exe": "Spotify",
    "mspaint.exe": "Paint",
    "calc.exe": "Calculator",
    "starfall.exe": "Starfall Tactics",
    "neondrift.exe": "Neon Drift",
    "deepmines.exe": "Deep Mines",
    "orbitracer.exe": "Orbit Racer",
    "kingdom.exe": "Kingdom Builder",
}

# Category key (locale demo.categories.<key>) -> (policy, processes).
# Kingdom Builder is "installed" but never launched, so the games section
# shows its unplayed list too. Paint and Calculator are left
# uncategorized on purpose.
CATEGORY_SPEC = {
    "games": (categories.AFK_STRICT,
              ["starfall", "neondrift", "deepmines", "orbitracer", "kingdom"]),
    "browser": (categories.AFK_STRICT, ["firefox", "chrome"]),
    "work": (categories.AFK_STRICT, ["code", "windowsterminal", "obsidian", "figma"]),
    "chat": (categories.AFK_LENIENT, ["discord", "telegram", "zoom"]),
    "media": (categories.AFK_LENIENT, ["vlc", "spotify"]),
    "system": (categories.AFK_STRICT, ["explorer", "taskmgr"]),
}

# Activities: main applications with weights, typical block length in
# minutes, and the applications a short glance goes to.
ACTIVITIES = {
    "work": ({"code.exe": 6, "windowsterminal.exe": 3, "obsidian.exe": 2,
              "figma.exe": 1}, 35),
    "browse": ({"firefox.exe": 5, "chrome.exe": 2}, 18),
    "chat": ({"discord.exe": 4, "telegram.exe": 2}, 8),
    "call": ({"zoom.exe": 1, "discord.exe": 2}, 20),
    "media": ({"vlc.exe": 1, "spotify.exe": 1}, 26),
    "game": ({"starfall.exe": 5, "neondrift.exe": 3, "deepmines.exe": 2,
              "orbitracer.exe": 1}, 70),
    "misc": ({"explorer.exe": 4, "taskmgr.exe": 1, "mspaint.exe": 1,
              "calc.exe": 1}, 4),
}
GLANCES = ["firefox.exe", "discord.exe", "telegram.exe", "explorer.exe"]


def _category_names():
    return {key: tr(f"demo.categories.{key}") for key in CATEGORY_SPEC}


def _categories():
    names = _category_names()
    data = {
        names[key]: {"afk_policy": policy, "processes": list(processes),
                     "patterns": []}
        for key, (policy, processes) in CATEGORY_SPEC.items()
    }
    return data, False, []


def _pick(rng, weights):
    items = list(weights)
    return rng.choices(items, weights=[weights[i] for i in items])[0]


def _activity_weights(moment, weekend):
    """What a block is likely to be at a given hour."""
    hour = moment.hour
    if weekend:
        if hour < 12:
            return {"browse": 4, "chat": 2, "media": 2, "misc": 1}
        if hour < 18:
            return {"game": 4, "browse": 3, "chat": 2, "media": 1, "misc": 1}
        return {"game": 6, "browse": 2, "chat": 2, "call": 1, "misc": 1}
    if hour < 18:
        return {"work": 7, "browse": 3, "chat": 2, "call": 1, "misc": 1}
    if hour < 21:
        return {"browse": 3, "game": 3, "work": 2, "chat": 2, "media": 2}
    return {"game": 4, "browse": 3, "media": 2, "chat": 2, "work": 1}


class _Recorder:
    def __init__(self):
        self.window = []
        self.afk = []

    def window_event(self, app, start, end, title=""):
        self.window.append(_event(start, end, {"app": app, "title": title}))

    def afk_event(self, status, start, end):
        self.afk.append(_event(start, end, {"status": status}))


def _event(start, end, data):
    return {
        "timestamp": start.astimezone(timezone.utc).isoformat(),
        "duration": (end - start).total_seconds(),
        "data": data,
    }


def _focus(rng, rec, app, start, end, glances):
    """Window events of one application, with an occasional short glance away."""
    cursor = start
    while cursor < end:
        piece = min(end, cursor + timedelta(seconds=rng.uniform(30, 240)))
        rec.window_event(app, cursor, piece)
        cursor = piece
        if glances and cursor < end and rng.random() < 0.18:
            glance = min(end, cursor + timedelta(seconds=rng.uniform(3, 40)))
            rec.window_event(rng.choice(GLANCES), cursor, glance)
            cursor = glance


def _sitting(rng, rec, start, end, weekend):
    """One continuous stretch with the computer on: blocks and AFK breaks."""
    cursor = start
    active_from = start
    last_app = "explorer.exe"
    while cursor < end:
        kind = _pick(rng, _activity_weights(cursor, weekend))
        apps, typical = ACTIVITIES[kind]
        app = _pick(rng, apps)
        minutes = max(1.5, rng.lognormvariate(0, 0.6) * typical)
        block_end = min(end, cursor + timedelta(minutes=minutes))
        _focus(rng, rec, app, cursor, block_end, glances=kind not in ("call", "media", "game"))
        cursor = block_end
        last_app = app

        # Now and then the user is at the computer with no window in
        # focus: the desktop, a closed window — "other at the computer".
        if cursor < end and rng.random() < 0.12:
            cursor = min(end, cursor + timedelta(seconds=rng.uniform(40, 240)))

        # A break: the window stays focused while the user is away. Calls
        # and media keep going without touching the keyboard, which is
        # what the lenient AFK policy credits.
        if cursor < end and rng.random() < (0.35 if kind in ("call", "media") else 0.22):
            away = timedelta(minutes=rng.choice((4, 6, 9, 14, 22, 35, 50)))
            away_end = min(end, cursor + away)
            rec.afk_event("not-afk", active_from, cursor)
            rec.afk_event("afk", cursor, away_end)
            rec.window_event(last_app, cursor, away_end)
            cursor = away_end
            active_from = cursor
    if active_from < end:
        rec.afk_event("not-afk", active_from, end)


def generate(now=None):
    """(buckets, {bucket: events}) — ActivityWatch-shaped demo data."""
    now = now or datetime.now().astimezone()
    rng = random.Random(SEED)
    rec = _Recorder()
    tz = now.tzinfo
    first = now.date() - timedelta(days=DAYS - 1)

    # A week-long trip and a few scattered days with the computer off.
    trip = {first + timedelta(days=d) for d in range(38, 44)}

    for offset in range(DAYS):
        day = first + timedelta(days=offset)
        if day in trip or (offset > 2 and rng.random() < 0.08):
            continue
        weekend = day.weekday() >= 5
        quiet = rng.random() < 0.05   # switched on, barely used

        if weekend:
            start_hour = rng.uniform(11.0, 14.0)
        else:
            start_hour = rng.uniform(9.5, 11.5)
        if quiet:
            length = rng.uniform(0.3, 0.9)
        else:
            late = rng.random() < (0.45 if weekend or day.weekday() == 4 else 0.25)
            end_hour = rng.uniform(24.2, 26.0) if late else rng.uniform(20.5, 23.8)
            length = end_hour - start_hour

        start = datetime.combine(day, time.min, tzinfo=tz) + timedelta(hours=start_hour)
        end = min(now, start + timedelta(hours=length))
        if end <= start:
            continue

        # Meals, errands and evenings out split the day into sittings.
        cuts = sorted(rng.uniform(0.15, 0.9) for _ in range(rng.choice((2, 3, 3, 4))))
        bounds = [start] + [start + (end - start) * c for c in cuts] + [end]
        for i in range(len(bounds) - 1):
            sit_start = bounds[i] + (timedelta(minutes=rng.uniform(30, 110)) if i else timedelta())
            if sit_start < bounds[i + 1]:
                _sitting(rng, rec, sit_start, bounds[i + 1], weekend)

    # ActivityWatch returns events newest first.
    window = sorted(rec.window, key=lambda e: e["timestamp"], reverse=True)
    afk = sorted(rec.afk, key=lambda e: e["timestamp"], reverse=True)
    buckets = {
        WINDOW_BUCKET: {"type": "currentwindow"},
        AFK_BUCKET: {"type": "afkstatus"},
    }
    return buckets, {WINDOW_BUCKET: window, AFK_BUCKET: afk}


def apply_config():
    """Demo applications and games category for the rest of the run."""
    app_names.use(APPS)
    config.GAME_CATEGORY = _category_names()["games"]


def collect_stats(now=None):
    """Stats for the demo data, computed by aw_data like real ones."""
    apply_config()
    buckets, events = generate(now)
    return aw_data.collect_stats(
        fetch_buckets=lambda: buckets,
        fetch_events=lambda bucket: events[bucket],
        load_categories=_categories,
    )


if __name__ == "__main__":
    stats = collect_stats()
    label = __import__("i18n").category_label
    print(f"Window events: {stats.event_count}")
    print(f"Active: {aw_data.fmt_duration(stats.total_seconds)}, "
          f"{len(stats.active_days)} active of {stats.calendar_days} days")
    for category, seconds in stats.by_category:
        print(f"  {label(category):<18} {aw_data.fmt_duration(seconds)}")
