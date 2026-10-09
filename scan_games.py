"""Scans game libraries on disk and adds the found exe names to categories.json.

Needed because aw-watcher-window reports only the process name, without a
path. A rule like "everything under steamapps\\common is a game" cannot be
applied to events, but it can be applied to the disk: here we take the
paths, extract the exe names and store them as exact entries of the games
category (config.GAME_CATEGORY).

Usage:
    python scan_games.py            review and confirm
    python scan_games.py --dry-run  only show, write nothing
    python scan_games.py --yes      do not ask (for scripts)
"""

import argparse
import re
import sys
from pathlib import Path

import categories
import config

STEAM_COMMON = Path("steamapps") / "common"
LIBRARY_PATH_RE = re.compile(r'"path"\s+"([^"]+)"', re.IGNORECASE)


def steam_libraries():
    """steamapps/common folders of all libraries, including those listed in the vdf."""
    roots, seen = [], set()

    def add(path):
        common = Path(path) / STEAM_COMMON
        key = str(common).lower()
        if key not in seen and common.is_dir():
            seen.add(key)
            roots.append(common)

    for steam_root in config.STEAM_ROOTS:
        root = Path(steam_root)
        if not root.is_dir():
            continue
        add(root)

        vdf = root / "steamapps" / "libraryfolders.vdf"
        if vdf.is_file():
            try:
                text = vdf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in LIBRARY_PATH_RE.findall(text):
                add(match.replace("\\\\", "\\"))

    return roots


def extra_libraries():
    return [Path(p) for p in config.GAME_LIBRARY_ROOTS if Path(p).is_dir()]


def is_noise(exe):
    name = exe.stem.lower()
    if any(bad in name for bad in config.GAME_SCAN_IGNORE_PATTERNS):
        return True
    try:
        if exe.stat().st_size < config.MIN_GAME_EXE_BYTES:
            return True
    except OSError:
        return True
    return False


def scan_game_dir(game_dir):
    """Game executables inside the folder of one game."""
    found = []
    for exe in game_dir.rglob("*.exe"):
        parts = {p.lower() for p in exe.relative_to(game_dir).parts[:-1]}
        if parts & config.GAME_SCAN_IGNORE_DIRS:
            continue
        if is_noise(exe):
            continue
        found.append(exe)
    return found


def scan(libraries):
    """{process: (game name, path)} over all libraries."""
    result = {}
    for library in libraries:
        for game_dir in sorted(library.iterdir()):
            if not game_dir.is_dir():
                continue
            if game_dir.name.lower() in config.GAME_SCAN_IGNORE_DIRS:
                continue
            for exe in scan_game_dir(game_dir):
                key = categories.normalize(exe.name)
                result.setdefault(key, (game_dir.name, exe))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="write nothing")
    parser.add_argument(
        "--include-generic",
        action="store_true",
        help="also add overly generic names (launcher, game, client)",
    )
    args = parser.parse_args()
    target = config.GAME_CATEGORY

    libraries = steam_libraries() + extra_libraries()
    if not libraries:
        print("No game libraries found.")
        print("Set the paths in STEAM_ROOTS or GAME_LIBRARY_ROOTS in config.py.")
        return 1

    print("Libraries:")
    for library in libraries:
        print(f"  {library}")

    found = scan(libraries)
    print(f"\nGame executables found: {len(found)}")
    if not found:
        return 0

    data, created, errors = categories.load_categories()
    if created:
        print(f"Created {config.CATEGORIES_FILE} from the starter set.")
    for error in errors:
        print(f"  ! {error}")

    index = categories.build_index(data)

    new, existing, generic = {}, [], {}
    for process, (game, exe) in sorted(found.items()):
        if process in index.exact:
            existing.append((process, index.exact[process]))
        elif process in config.GAME_SCAN_GENERIC_NAMES and not args.include_generic:
            generic[process] = (game, exe)
        else:
            new[process] = (game, exe)

    if existing:
        print(f"Already in categories.json: {len(existing)} — left as is.")

    if generic:
        print(f"\nSkipped as overly generic names ({len(generic)}):")
        for process, (game, _) in sorted(generic.items()):
            print(f"  {process:<34} {game}")
        print("  Such an entry would catch any unrelated program with the same")
        print("  name. To add them anyway: --include-generic")

    if not new:
        print("\nNothing new to add.")
        return 0

    print(f"\nWill be added to {target!r} ({len(new)}):")
    for process, (game, exe) in sorted(new.items(), key=lambda kv: kv[1][0].lower()):
        print(f"  {process:<34} {game}")
        print(f"  {'':<34} {exe}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    if not args.yes:
        if not sys.stdin.isatty():
            print("\nNot an interactive run. Run it in a terminal "
                  "or add --yes.")
            return 1
        answer = input(f"\nAdd {len(new)} entries to {target!r}? [y/N] ").strip().lower()
        if answer not in ("y", "yes", "т", "так"):  # Ukrainian "yes" too
            print("Cancelled.")
            return 0

    added, skipped = categories.add_processes(target, new.keys())
    print(f"\nAdded: {len(added)}")
    if skipped:
        print(f"Skipped (already present): {len(skipped)}")
    print(f"File: {categories.CATEGORIES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
