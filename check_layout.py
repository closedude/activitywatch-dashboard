"""Layout check of a generated dashboard.html.

Runs a headless browser (Chrome or Edge, whichever is installed) at
several window widths and measures the real geometry of the page.
Installs nothing: the browser is already there, no other dependencies.

What is checked:
  * equal gaps between cards horizontally and vertically;
  * in every pair of columns the bottom edges match (no empty space below);
  * nothing sticks out of its container;
  * the page does not scroll sideways.

    python check_layout.py                       check dashboard.html
    python check_layout.py dashboard-demo.html   check another report file
    python check_layout.py --keep                keep the temporary files

Exit code 1 if at least one check fails.
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
# Three working widths plus a narrow one: that is where the banner's left
# block starts crowding the coverage bar, and that is where to catch it.
WIDTHS = (1920, 1440, 1100, 820)
HEIGHT = 1200
TOLERANCE = 1.0          # pixels things may be off by
MARKER = "AW-LAYOUT-CHECK"

BROWSERS = [
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for name in ("chrome", "msedge", "chromium"):
        found = shutil.which(name)
        if found:
            return found
    for raw in BROWSERS:
        path = Path(os.path.expandvars(raw))
        if path.is_file():
            return str(path)
    return None


# Runs inside the page and builds a report about the geometry.
PROBE = r"""
(function () {
  var TOL = %(tol)s;
  var problems = [];
  var facts = {};
  function round(v) { return Math.round(v * 10) / 10; }
  function rect(el) { return el.getBoundingClientRect(); }

  // --- 1. Gaps between cards ---------------------------------------------
  // Card groups must share one step. List rows (.rows) live inside a card
  // and have their own, smaller step.
  var cardGroups = ['.kpis', '.tiles', '.cols', '.col-stack'];
  var cardGaps = {};
  cardGroups.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (group) {
      var cs = getComputedStyle(group);
      var row = parseFloat(cs.rowGap), col = parseFloat(cs.columnGap);
      if (!isNaN(row) && !isNaN(col) && Math.abs(row - col) > TOL) {
        problems.push('Different gaps per axis in ' + sel +
          ': vertical ' + row + 'px, horizontal ' + col + 'px');
      }
      if (!isNaN(row)) cardGaps[sel] = row;
    });
  });
  var distinct = [];
  Object.keys(cardGaps).forEach(function (k) {
    if (distinct.indexOf(cardGaps[k]) === -1) distinct.push(cardGaps[k]);
  });
  facts.cardGaps = cardGaps;
  if (distinct.length > 1) {
    problems.push('Card groups use different gaps: ' +
      JSON.stringify(cardGaps));
  }

  // The distance between top-level sections must equal the same step.
  var step = distinct.length ? distinct[0] : null;
  var sections = Array.prototype.slice.call(
    document.querySelectorAll('.wrap > .panel, .wrap > .cols, .wrap > .banner, .wrap > .kpis'));
  var sectionGaps = [];
  for (var i = 0; i < sections.length - 1; i++) {
    var g = round(rect(sections[i + 1]).top - rect(sections[i]).bottom);
    sectionGaps.push(g);
    if (step !== null && Math.abs(g - step) > TOL) {
      var title = sections[i].querySelector('h2, .bstat .k');
      problems.push('Gap after section "' +
        (title ? title.textContent.trim().slice(0, 32) : sections[i].className) +
        '" is ' + g + 'px instead of ' + step + 'px');
    }
  }
  facts.sectionGaps = sectionGaps;

  // Gaps inside each card group — between neighbours in one row.
  cardGroups.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (group) {
      var kids = Array.prototype.slice.call(group.children);
      for (var i = 0; i < kids.length - 1; i++) {
        var a = rect(kids[i]), b = rect(kids[i + 1]);
        var gap = (Math.abs(a.top - b.top) < TOL)
          ? round(b.left - a.right)   // neighbours in a row
          : round(b.top - a.bottom);  // neighbours in a column
        if (step !== null && gap >= 0 && Math.abs(gap - step) > TOL) {
          problems.push('Gap between cards in ' + sel + ' is ' +
            gap + 'px instead of ' + step + 'px');
        }
      }
    });
  });

  // --- 2. Bottom edges of columns ----------------------------------------
  var pairs = [];
  document.querySelectorAll('.cols').forEach(function (row) {
    var kids = Array.prototype.slice.call(row.children);
    if (kids.length < 2) return;
    // When the columns have stacked, there is nothing to align.
    var sideBySide = Math.abs(rect(kids[0]).top - rect(kids[1]).top) < TOL;
    if (!sideBySide) return;
    var bottoms = kids.map(function (k) { return round(rect(k).bottom); });
    var spread = Math.max.apply(null, bottoms) - Math.min.apply(null, bottoms);
    var name = (row.querySelector('h2') || {}).textContent || row.className;
    pairs.push({row: name.trim().slice(0, 32), bottoms: bottoms, spread: round(spread)});
    if (spread > TOL) {
      problems.push('Columns of row "' + name.trim().slice(0, 32) +
        '" end at different heights: ' + round(spread) + 'px apart');
    }
  });
  facts.columnPairs = pairs;

  // --- 3. Content sticking out of containers -----------------------------
  var containers = document.querySelectorAll('.panel, .kpi, .banner, .bstat, .row-card');
  var escaped = 0;
  containers.forEach(function (box) {
    var cs = getComputedStyle(box);
    var pad = {
      l: parseFloat(cs.paddingLeft), r: parseFloat(cs.paddingRight),
      t: parseFloat(cs.paddingTop), b: parseFloat(cs.paddingBottom)
    };
    var br = rect(box);
    var inner = {
      left: br.left + pad.l, right: br.right - pad.r,
      top: br.top + pad.t, bottom: br.bottom - pad.b
    };
    Array.prototype.slice.call(box.children).forEach(function (child) {
      // Elements with their own scrolling may be wider.
      if (child.classList.contains('tscroll')) return;
      var cr = rect(child);
      if (cr.width === 0 && cr.height === 0) return;
      var over = Math.max(inner.left - cr.left, cr.right - inner.right);
      if (over > TOL + 0.5) {
        escaped++;
        if (escaped <= 5) {
          problems.push('Content sticks out of ' +
            (box.className.split(' ')[0]) + ' by ' + round(over) + 'px (' +
            (child.className || child.tagName) + ')');
        }
      }
    });
  });
  facts.escapedChildren = escaped;

  // Tables scroll on their own on narrow screens, but at the checked
  // widths the scrolling must not kick in: a scrollbar under a table has
  // already appeared once, when the row highlight went past the edge
  // (screenshots with --hide-scrollbars did not show it).
  document.querySelectorAll('.tscroll').forEach(function (box) {
    if (box.scrollWidth > box.clientWidth + TOL) {
      var head = box.closest('.panel') && box.closest('.panel').querySelector('h2');
      problems.push('Horizontal scrolling in table "' +
        (head ? head.textContent.trim() : '?') + '": content ' +
        box.scrollWidth + 'px at width ' + box.clientWidth + 'px');
    }
  });

  // Scrolling where there should be none.
  document.querySelectorAll('.panel, .kpi, .banner').forEach(function (box) {
    if (box.scrollWidth > box.clientWidth + TOL) {
      problems.push('Horizontal scrolling inside ' +
        box.className.split(' ')[0] + ': content ' + box.scrollWidth +
        'px at width ' + box.clientWidth + 'px');
    }
  });

  // --- 4. Banner: coverage bar -------------------------------------------
  var banner = document.querySelector('.banner');
  if (banner) {
    var cs = getComputedStyle(banner);
    var main = banner.querySelector('.banner-main');
    var cov = banner.querySelector('.coverage');
    var bar = banner.querySelector('.coverage-bar');
    var fill = bar ? bar.querySelector('i') : null;
    var inner = {
      left: rect(banner).left + parseFloat(cs.paddingLeft),
      right: rect(banner).right - parseFloat(cs.paddingRight)
    };
    facts.banner = {};

    if (bar) {
      var br = rect(bar);
      facts.banner.barRight = round(br.right);
      facts.banner.bannerInnerRight = round(inner.right);
      facts.banner.barWidth = round(br.width);
      // The bar must reach the right edge of the banner content.
      if (Math.abs(br.right - inner.right) > TOL) {
        problems.push('Banner bar does not reach the edge: ends at ' +
          round(br.right) + 'px, content edge ' + round(inner.right) + 'px');
      }
      if (br.left < inner.left - TOL || br.right > inner.right + TOL) {
        problems.push('Banner bar sticks out of the banner');
      }
      // Summary bar of the shared bar design (--bar-sum in report.py).
      if (round(br.height) !== 12) {
        problems.push('Banner bar height is ' + round(br.height) +
          'px instead of 12px');
      }
      if (fill && rect(fill).width > br.width + TOL) {
        problems.push('Bar fill is wider than the bar itself');
      }
    }

    if (main && cov) {
      var mr = rect(main), cr = rect(cov);
      var sameLine = Math.abs(mr.bottom - cr.bottom) < 40;
      facts.banner.sameLine = sameLine;
      facts.banner.bottoms = [round(mr.bottom), round(cr.bottom)];
      if (sameLine) {
        // Aligned on the bottom line.
        if (Math.abs(mr.bottom - cr.bottom) > TOL) {
          problems.push('Banner blocks are not aligned at the bottom: ' +
            round(mr.bottom) + ' vs ' + round(cr.bottom));
        }
        // The left block does not overlap the bar.
        if (mr.right > cr.left + TOL) {
          problems.push('Banner left block overlaps the coverage bar by ' +
            round(mr.right - cr.left) + 'px');
        }
      }
    }
  }

  // --- 5. The page does not scroll sideways ------------------------------
  var doc = document.documentElement;
  facts.pageScrollWidth = doc.scrollWidth;
  facts.pageClientWidth = doc.clientWidth;
  if (doc.scrollWidth > doc.clientWidth + TOL) {
    problems.push('The page scrolls sideways: ' + doc.scrollWidth +
      'px in a ' + doc.clientWidth + 'px window');
  }

  // --dump-dom returns HTML, so quotes in JSON would turn into &quot;.
  // base64 passes through intact.
  var payload = JSON.stringify(
    {width: window.innerWidth, problems: problems, facts: facts});
  var out = document.createElement('pre');
  out.id = 'aw-layout-check';
  out.textContent = '%(marker)s' +
    btoa(unescape(encodeURIComponent(payload))) + '%(marker)s';
  document.body.appendChild(out);
})();
"""


def build_probe_page(source, destination, tolerance):
    html = source.read_text(encoding="utf-8")
    script = PROBE % {"tol": tolerance, "marker": MARKER}
    html = html.replace("</body>", f"<script>{script}</script></body>")
    destination.write_text(html, encoding="utf-8")


def run_browser(browser, page, width):
    command = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={width},{HEIGHT}",
        "--virtual-time-budget=4000",
        "--dump-dom",
        page.as_uri(),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=120,
    )
    found = re.search(f"{MARKER}([A-Za-z0-9+/=\\s]*){MARKER}", result.stdout, re.S)
    if not found:
        raise RuntimeError(
            f"the browser returned no result for width {width}. "
            f"stderr: {result.stderr.strip()[:300]}"
        )
    raw = base64.b64decode("".join(found.group(1).split()))
    return json.loads(raw.decode("utf-8"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keep = "--keep" in sys.argv
    report = Path(args[0]).resolve() if args else BASE / config.OUTPUT_FILE
    if not report.is_file():
        print(f"{report.name} not found. Run first: python report.py")
        return 1

    browser = find_browser()
    if not browser:
        print("Neither Chrome nor Edge found — nothing to measure the layout with.")
        print("Install either of them or add its path to BROWSERS.")
        return 1

    workdir = Path(tempfile.mkdtemp(prefix="aw-layout-"))
    page = workdir / "probe.html"
    build_probe_page(report, page, TOLERANCE)

    print(f"Browser: {browser}")
    print(f"File:    {report}\n")

    total = 0
    for width in WIDTHS:
        try:
            data = run_browser(browser, page, width)
        except Exception as error:  # noqa: BLE001 — shown to the user as is
            print(f"[{width}px] could not check: {error}")
            total += 1
            continue

        problems = data["problems"]
        facts = data["facts"]
        total += len(problems)

        head = "all clean" if not problems else f"problems: {len(problems)}"
        print(f"[{width}px] {head}")
        print(f"    gap step:        {facts.get('cardGaps')}")
        print(f"    between sections: {facts.get('sectionGaps')}")
        for pair in facts.get("columnPairs", []):
            print(f"    columns \"{pair['row']}\": bottoms {pair['bottoms']}, "
                  f"spread {pair['spread']}px")
        banner = facts.get("banner")
        if banner:
            print(f"    banner: bar {banner.get('barWidth')}px, ends at "
                  f"{banner.get('barRight')}, content edge "
                  f"{banner.get('bannerInnerRight')}, "
                  f"{'one line' if banner.get('sameLine') else 'wrapped'}, "
                  f"bottoms {banner.get('bottoms')}")
        print(f"    page width: {facts.get('pageScrollWidth')} "
              f"in a {facts.get('pageClientWidth')} window")
        for problem in problems:
            print(f"    ✗ {problem}")
        print()

    if keep:
        print(f"Temporary page: {page}")
    else:
        shutil.rmtree(workdir, ignore_errors=True)

    if total:
        print(f"TOTAL: {total} problems — the layout needs fixing.")
        return 1
    widths = ", ".join(str(w) for w in WIDTHS)
    print(f"TOTAL: all checks passed at widths {widths}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
