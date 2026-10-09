"""Report archive: a daily copy of dashboard.html and rotation of old copies.

The copy goes to config.ARCHIVE_DIR as dashboard-YYYY-MM-DD.html by the
generation date. Generating again on the same day overwrites the copy, so
each day keeps one, the latest. Beyond config.ARCHIVE_KEEP copies the
oldest are deleted.

Only files with exactly this name pattern are touched. Everything else in
the folder (notes, copies renamed by hand) is left alone.
"""

import re
from datetime import date
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent

# The prefix comes from the main report name: dashboard.html -> dashboard-...
STEM = Path(config.OUTPUT_FILE).stem
PATTERN = re.compile(rf"^{re.escape(STEM)}-\d{{4}}-\d{{2}}-\d{{2}}\.html$")


def save_copy(html, day=None, directory=None, keep=None):
    """Saves the report copy for the day and removes the oldest over the limit.

    Returns (copy_path, [removed_paths]). With keep <= 0 the archive is off:
    nothing is written and nothing is deleted.
    """
    keep = config.ARCHIVE_KEEP if keep is None else keep
    if keep <= 0:
        return None, []
    directory = BASE / config.ARCHIVE_DIR if directory is None else Path(directory)
    day = day or date.today()

    directory.mkdir(parents=True, exist_ok=True)
    copy = directory / f"{STEM}-{day:%Y-%m-%d}.html"
    copy.write_text(html, encoding="utf-8")

    # The date in the name is ISO, so alphabetical order is chronological.
    # File modification time will not do: the copy may have been rewritten.
    copies = sorted(
        path for path in directory.iterdir()
        if path.is_file() and PATTERN.match(path.name)
    )
    removed = copies[:-keep]
    for path in removed:
        path.unlink()
    return copy, removed
