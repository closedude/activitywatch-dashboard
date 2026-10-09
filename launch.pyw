"""Entry point for the desktop shortcut: builds the report and opens it.

The .pyw extension and running through pythonw.exe mean no console window
flashes. Errors are not lost — they are shown in a message box through
ctypes, so tkinter is not needed.

report.py itself does not open a browser and should not: opening is a
separate action you start by clicking the shortcut.
"""

import ctypes
import os
import sys
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

MB_ICONERROR = 0x10
# Used only if the modules (and so the locale) failed to load.
FALLBACK_TITLE = "ActivityWatch report"


def alert(text, title=FALLBACK_TITLE):
    ctypes.windll.user32.MessageBoxW(0, text, title, MB_ICONERROR)


def main():
    try:
        import archive
        import aw_data
        import config
        import report
        from i18n import tr
    except Exception:
        alert("Could not load the report modules:\n\n" + traceback.format_exc())
        return 1

    title = tr("launch.title")

    try:
        if config.DEMO:
            import demo
            stats = demo.collect_stats()
        else:
            stats = aw_data.collect_stats()
    except aw_data.ActivityWatchError as e:
        alert(str(e), title)
        return 1
    except Exception:
        alert(tr("launch.collect") + "\n\n" + traceback.format_exc(), title)
        return 1

    try:
        page = report.render(stats, demo=config.DEMO)
        name = config.DEMO_OUTPUT_FILE if config.DEMO else config.OUTPUT_FILE
        output = BASE / name
        output.write_text(page, encoding="utf-8")
        os.startfile(output)
    except Exception:
        alert(tr("launch.render") + "\n\n" + traceback.format_exc(), title)
        return 1

    # Made-up data does not belong in the archive of real reports.
    if config.DEMO:
        return 0

    # Archive after opening: its failure must not delay the report itself.
    try:
        archive.save_copy(page)
    except OSError as e:
        alert(f"{tr('launch.archive')}\n\n{e}", title)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
