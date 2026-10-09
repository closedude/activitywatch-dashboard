"""Interface strings and language-dependent formatting.

Every piece of text shown in the dashboard (and the messages of the
report / launcher entry points) lives in locales/<language>.json.
The language comes from config.LANGUAGE and can be overridden at run
time with set_language() (report.py --lang).

Besides plain strings, the language decides:
  * plural forms — Ukrainian has three (1 день, 2 дні, 5 днів),
    English two (1 day, 2 days);
  * duration format — "1 год 53 хв" vs "1h 53m";
  * date formats, weekday and month names, list conjunction, quotes.

Locale strings may contain HTML (<b>, <code>); values substituted into
them are escaped by the caller where they come from data.
"""

import json
from pathlib import Path

import config

LOCALE_DIR = Path(__file__).resolve().parent / "locales"

_language = None
_strings = {}


def _ukrainian_plural(count):
    """Index of the form: 0 — one (1, 21), 1 — few (2–4, 22–24), 2 — many (0, 5–20, 25…)."""
    count = abs(int(count))
    if 11 <= count % 100 <= 14:
        return 2
    last = count % 10
    if last == 1:
        return 0
    if 2 <= last <= 4:
        return 1
    return 2


def _english_plural(count):
    return 0 if abs(count) == 1 else 1


PLURAL_RULES = {"uk": _ukrainian_plural, "en": _english_plural}


def set_language(language):
    """Switch the active language; the locale file is read on first use."""
    global _language
    if not (LOCALE_DIR / f"{language}.json").exists():
        raise ValueError(f"No locale file for language '{language}' in {LOCALE_DIR}")
    _language = language


def language():
    return _language or config.LANGUAGE


def _locale():
    lang = language()
    if lang not in _strings:
        path = LOCALE_DIR / f"{lang}.json"
        _strings[lang] = json.loads(path.read_text(encoding="utf-8"))
    return _strings[lang]


def _lookup(key):
    node = _locale()
    for part in key.split("."):
        node = node[part]
    return node


def tr(key, **values):
    """Locale string by dotted key, with {placeholders} filled in."""
    template = _lookup(key)
    return template.format(**values) if values else template


def plural(count, key):
    """The form of plural.<key> that agrees with count."""
    forms = _lookup(f"plural.{key}")
    rule = PLURAL_RULES.get(language(), _english_plural)
    return forms[min(rule(count), len(forms) - 1)]


def counted(count, key):
    """«5 днів», "5 days" — a number with the agreeing word."""
    return f"{count} {plural(count, key)}"


# --------------------------------------------------------------------------
# Durations
# --------------------------------------------------------------------------


def duration_parts(seconds):
    """(hours part, minutes part) of a duration, either may be empty.

    The single duration format for the whole report: seconds under a
    minute, otherwise whole minutes, hours with minutes. The parts are
    separate so a right-aligned column can line up units under units.
    """
    seconds = round(seconds)
    if seconds < 60:
        return "", tr("duration.seconds", n=seconds)
    hours, minutes = divmod(round(seconds / 60), 60)
    if not hours:
        return "", tr("duration.minutes", n=minutes)
    if not minutes:
        return tr("duration.hours", n=hours), ""
    return tr("duration.hours", n=hours), tr("duration.minutes", n=minutes)


def fmt_duration(seconds):
    """"45 с" / "38 хв" / "1 год 53 хв" (or "45s" / "38m" / "1h 53m")."""
    return " ".join(part for part in duration_parts(seconds) if part)


# --------------------------------------------------------------------------
# Calendar
# --------------------------------------------------------------------------


def weekday_short(index):
    """Monday is 0, as in date.weekday()."""
    return _lookup("weekdays")[index]


def month_name(month):
    return _lookup("months")[month - 1]


def month_genitive(month):
    """Month form used after a day number: «5 березня»; same as name in English."""
    return _lookup("months_genitive")[month - 1]


def date_long(moment):
    """«5 березня 2026» / "March 5, 2026"."""
    return tr("date.long", day=moment.day, month=month_name(moment.month),
              month_gen=month_genitive(moment.month), year=moment.year)


def date_numeric(moment):
    """«05.03.2026» / "2026-03-05"."""
    return moment.strftime(tr("date.numeric"))


def date_short(moment):
    """Day and month without the year: «05.03» / "03/05"."""
    return moment.strftime(tr("date.short"))


def join_and(items):
    """«a, b і c» / "a, b and c"."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + tr("list_and") + items[-1]


def quoted(text):
    return tr("quote", text=text)


# --------------------------------------------------------------------------
# Labels for internal keys
# --------------------------------------------------------------------------


def category_label(name):
    """Display name of a category: internal keys get a localized label,
    real categories from categories.json are shown as they are."""
    if name == config.UNCATEGORIZED:
        return tr("category.uncategorized")
    if name == config.CATEGORY_OTHER:
        return tr("category.other")
    return name


def system_app_names():
    """Display names of Windows system programs in the active language."""
    return dict(_lookup("app_names"))


def app_label(name):
    """Display name of an application; the unknown-app key is localized."""
    return tr("app.unknown") if name == config.UNKNOWN_APP else name
