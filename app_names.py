"""Display names instead of executable names.

Three sources, later ones win:
  1. locales/<language>.json, section "app_names" — Windows system
     programs (Task Manager, File Explorer...), so their names follow the
     interface language;
  2. app_names.local.json — your own names; kept out of git;
  3. app_names.example.json — used instead of the local file when there
     is none, so a fresh checkout still has a few sensible names.

Keys are exe names as aw-watcher-window reports them ("code.exe") and
are compared case-insensitively. Several executables may map to one name
(steam.exe and steamwebhelper.exe -> "Steam"); their time adds up. Keys
starting with "_" are notes and are skipped.
"""

import json
from pathlib import Path

import config
import i18n

BASE = Path(__file__).resolve().parent

_user = None    # the user mapping, read once
_merged = {}    # language -> merged mapping


def _read(path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"{path.name} cannot be read: {e}") from e
    return {k.lower(): v for k, v in raw.items() if not k.startswith("_")}


def user_names():
    """Names from app_names.local.json, or from the example if it is missing."""
    global _user
    if _user is None:
        local = BASE / config.APP_NAMES_FILE
        example = BASE / config.APP_NAMES_EXAMPLE_FILE
        if local.is_file():
            _user = _read(local)
        elif example.is_file():
            _user = _read(example)
        else:
            _user = {}
    return _user


def use(names):
    """Replace the user names for the rest of the run (demo mode)."""
    global _user
    _user = {k.lower(): v for k, v in names.items()}
    _merged.clear()


def mapping():
    """{exe name in lower case: display name} for the active language."""
    language = i18n.language()
    if language not in _merged:
        system = {k.lower(): v for k, v in i18n.system_app_names().items()}
        _merged[language] = {**system, **user_names()}
    return _merged[language]
