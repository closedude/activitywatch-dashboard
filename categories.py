"""Application categories: storage in categories.json, matching, conflicts.

categories.json lives next to the scripts and is meant to be edited by
hand. If it is missing, it is created from the starter set below.

Matching has two levels:
  1. processes — the exact process name (case-insensitive, .exe optional);
  2. patterns  — a substring of the process name (case-insensitive).
An exact name always wins over a pattern. If a process matches patterns of
several categories, the first one in file order is used and the conflict
goes to warnings, which are shown in the report.

IMPORTANT: patterns are matched against the process name only.
aw-watcher-window does not report the path to the exe (only app and
title), so a rule like "steamapps\\common" cannot work here — that is what
scan_games.py is for: it takes paths from disk and adds exact names.

The AFK policy (afk_policy) is set per category:
  strict  — the default: only not-afk time is counted;
  lenient — AFK time is counted too while a window of the category is
            focused, but no more than config.AFK_LENIENT_CAP_SECONDS from
            the start of each continuous AFK stretch. For calls and video,
            where you listen without pressing anything.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import config
from i18n import tr

CATEGORIES_PATH = Path(__file__).resolve().parent / config.CATEGORIES_FILE

# Keys starting with "_" are not categories — a place for notes.
NOTE_KEY = "_note"

NOTE_TEXT = (
    "processes — exact process name, patterns — substring of the process "
    "name. An exact name wins. If patterns of several categories match, "
    "the category higher in this file wins. The path to the exe is not "
    "available (aw-watcher-window reports only the name), so patterns work "
    "on the process name only. afk_policy: strict (default) counts only "
    "time with the keyboard and mouse active; lenient also counts AFK "
    "while a window of the category is focused, but no longer than the "
    "cap from config.py from the start of each AFK stretch."
)

# AFK policies. An unknown value in categories.json gives a warning and
# behaves as strict.
AFK_STRICT = "strict"
AFK_LENIENT = "lenient"
AFK_POLICIES = (AFK_STRICT, AFK_LENIENT)

# Starter set, used only when categories.json is missing. Category names
# are user data and appear in the report as is — rename them freely.
# Games are best added by scan_games.py, which finds them on disk.
DEFAULT_CATEGORIES = {
    "Ігри": {
        "afk_policy": AFK_STRICT,
        "processes": [],
        "patterns": [],
    },
    "Браузер": {
        "afk_policy": AFK_STRICT,
        "processes": ["chrome", "firefox", "msedge", "opera", "brave", "vivaldi"],
        "patterns": [],
    },
    "Робота/Розробка": {
        "afk_policy": AFK_STRICT,
        "processes": ["code", "vscodium", "cmd", "mintty", "notepad", "notepad++"],
        "patterns": ["python", "pycharm", "powershell", "pwsh", "terminal"],
    },
    "Спілкування": {
        "afk_policy": AFK_LENIENT,
        "processes": ["discord", "zoom", "telegram", "slack", "teams"],
        "patterns": [],
    },
    "Розваги": {
        "afk_policy": AFK_LENIENT,
        "processes": ["photos", "vlc", "spotify"],
        "patterns": ["steam"],
    },
    "Системні": {
        "afk_policy": AFK_STRICT,
        "processes": ["explorer", "taskmgr", "mmc", "aw-qt"],
        "patterns": ["setup", "unins", "redist", "-runtime-", "installer"],
    },
}


def normalize(name):
    """Process name in canonical form: lower case, without .exe."""
    return (name or "").strip().lower().removesuffix(".exe")


@dataclass
class Index:
    exact: dict = field(default_factory=dict)         # {process: category}
    patterns: list = field(default_factory=list)      # [(pattern, category)]
    order: list = field(default_factory=list)         # category names in order
    policies: dict = field(default_factory=dict)      # {category: AFK policy}
    warnings: list = field(default_factory=list)


def _normalize_entry(entry):
    """A category is either {"processes": [...], "patterns": [...]} or a plain list."""
    if isinstance(entry, list):
        return {"afk_policy": AFK_STRICT, "processes": list(entry), "patterns": []}
    return {
        "afk_policy": entry.get("afk_policy", AFK_STRICT),
        "processes": list(entry.get("processes", [])),
        "patterns": list(entry.get("patterns", [])),
    }


def write_categories(data, path=CATEGORIES_PATH):
    payload = {NOTE_KEY: NOTE_TEXT}
    payload.update(data)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_categories(path=CATEGORIES_PATH):
    """Reads categories.json, creating it from the starter set if needed.

    Returns (categories, created, read_errors).
    """
    if not path.exists():
        write_categories(DEFAULT_CATEGORIES, path)
        return dict(DEFAULT_CATEGORIES), True, []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return dict(DEFAULT_CATEGORIES), False, [
            tr("category_warnings.unreadable", file=path.name, error=e)
        ]

    data = {
        name: _normalize_entry(entry)
        for name, entry in raw.items()
        if not name.startswith("_")
    }
    if not data:
        return dict(DEFAULT_CATEGORIES), False, [
            tr("category_warnings.empty", file=path.name)
        ]
    return data, False, []


def build_index(categories):
    """A flat index for matching, plus warnings about conflicts."""
    index = Index(order=list(categories))

    for category, entry in categories.items():
        policy = entry.get("afk_policy", AFK_STRICT)
        if policy not in AFK_POLICIES:
            index.warnings.append(tr(
                "category_warnings.unknown_policy",
                policy=policy, category=category, fallback=AFK_STRICT,
            ))
            policy = AFK_STRICT
        index.policies[category] = policy

    for category, entry in categories.items():
        for process in entry["processes"]:
            key = normalize(process)
            if not key:
                continue
            if key in index.exact and index.exact[key] != category:
                index.warnings.append(tr(
                    "category_warnings.duplicate_process",
                    process=key, first=index.exact[key], second=category,
                ))
                continue
            index.exact[key] = category

    seen = {}
    for category, entry in categories.items():
        for pattern in entry["patterns"]:
            key = normalize(pattern)
            if not key:
                continue
            if key in seen and seen[key] != category:
                index.warnings.append(tr(
                    "category_warnings.duplicate_pattern",
                    pattern=key, first=seen[key], second=category,
                ))
                continue
            seen[key] = category
            index.patterns.append((key, category))

    return index


def classify(process, index):
    """(category, warning). An exact name wins over a pattern."""
    key = normalize(process)
    if not key:
        return config.UNCATEGORIZED, None

    if key in index.exact:
        return index.exact[key], None

    hits = [(pattern, category) for pattern, category in index.patterns if pattern in key]
    if not hits:
        return config.UNCATEGORIZED, None

    winner = hits[0][1]
    rivals = {category for _, category in hits}
    if len(rivals) > 1:
        detail = ", ".join(f"{tr('quote', text=p)} → {c}" for p, c in hits)
        return winner, tr(
            "category_warnings.pattern_conflict",
            process=key, detail=detail, winner=winner,
        )
    return winner, None


def afk_policy(category, index):
    """AFK policy of a category. Uncategorized and unknown ones are strict."""
    return index.policies.get(category, AFK_STRICT)


def add_processes(category, processes, path=CATEGORIES_PATH):
    """Adds processes to a category without touching existing entries.

    Returns (added, skipped_as_already_present).
    """
    categories, _, _ = load_categories(path)
    index = build_index(categories)

    if category not in categories:
        categories[category] = {
            "afk_policy": AFK_STRICT, "processes": [], "patterns": [],
        }

    added, skipped = [], []
    for process in processes:
        key = normalize(process)
        if key in index.exact:
            skipped.append((key, index.exact[key]))
            continue
        if key in {normalize(p) for p in categories[category]["processes"]}:
            skipped.append((key, category))
            continue
        categories[category]["processes"].append(key)
        added.append(key)

    if added:
        categories[category]["processes"].sort()
        write_categories(categories, path)
    return added, skipped
