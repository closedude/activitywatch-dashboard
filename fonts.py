"""Optional embedding of Roboto into the HTML via @font-face with base64.

Off by default: if Roboto is installed in Windows, font-family picks it up
on its own and the report stays light. With EMBED_FONT the report no
longer depends on the system, but grows by a few hundred kilobytes.

If the files are missing we do not fail: a warning is returned and the
report falls back to the system font.
"""

import base64
from pathlib import Path

import config
from i18n import tr

BASE = Path(__file__).resolve().parent

# Order matters: woff2 compresses best.
EXTENSIONS = (
    (".woff2", "woff2"),
    (".woff", "woff"),
    (".ttf", "truetype"),
)


def font_dir():
    path = Path(config.FONT_DIR)
    return path if path.is_absolute() else BASE / path


def find_font_file(stem):
    directory = font_dir()
    if not directory.is_dir():
        return None, None
    for suffix, fmt in EXTENSIONS:
        candidate = directory / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate, fmt
    return None, None


def face_css():
    """(css, warnings, embedded_bytes)."""
    if not config.EMBED_FONT:
        return "", [], 0

    directory = font_dir()
    if not directory.is_dir():
        return "", [tr("font_warnings.no_dir", directory=directory)], 0

    blocks, warnings, total = [], [], 0
    for weight, stem in config.FONT_FACES:
        path, fmt = find_font_file(stem)
        if path is None:
            warnings.append(tr(
                "font_warnings.missing_face",
                stem=stem, directory=directory, weight=weight,
            ))
            continue
        data = path.read_bytes()
        total += len(data)
        encoded = base64.b64encode(data).decode("ascii")
        blocks.append(
            "@font-face{font-family:'Roboto';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/{fmt};base64,{encoded}) format('{fmt}');}}"
        )

    if not blocks:
        warnings.append(tr("font_warnings.none_embedded"))
    return "\n".join(blocks), warnings, total
