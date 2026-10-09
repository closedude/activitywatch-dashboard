"""Fetching data from ActivityWatch and all the counting.

The single source of truth is the list of Segment: pieces of window time
already clipped to not-afk intervals, with system processes filtered out,
names normalized and a category assigned. For categories with the lenient
AFK policy, pieces of credited AFK time are added to them (idle=True).
All statistics are computed from the segments, so the filters are applied
exactly once and never drift apart between sections.

Everything inside is counted in seconds. Formatting happens only on
output, through fmt_duration() (see i18n.py).
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from statistics import median

import requests

import app_names
import categories
import config
import i18n
from i18n import fmt_duration  # noqa: F401 — kept here for older imports
from i18n import tr


class ActivityWatchError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------


def fmt_clock(offset):
    """Seconds from the start of the logical day -> wall clock time: "01:50"."""
    minutes = round((config.DAY_START_SECONDS + offset) / 60) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------


def get_buckets():
    try:
        r = requests.get(f"{config.API}/buckets", timeout=config.TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ActivityWatchError(tr("errors.unreachable", api=config.API, error=e)) from e


def get_events(bucket_id):
    """All events of a bucket: limit=-1 means "no limit"."""
    try:
        r = requests.get(
            f"{config.API}/buckets/{bucket_id}/events",
            params={"limit": -1},
            timeout=config.TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ActivityWatchError(tr("errors.events", bucket=bucket_id, error=e)) from e


def find_bucket(buckets, bucket_type, name_prefix):
    for bucket_id, info in buckets.items():
        if info.get("type") == bucket_type:
            return bucket_id
    for bucket_id in buckets:
        if bucket_id.startswith(name_prefix):
            return bucket_id
    return None


# --------------------------------------------------------------------------
# Time
# --------------------------------------------------------------------------


def to_local(timestamp):
    """ISO string from the API (UTC) -> datetime in the system's local zone."""
    return datetime.fromisoformat(timestamp).astimezone()


def event_span(event):
    start = to_local(event["timestamp"])
    return start, start + timedelta(seconds=event.get("duration", 0.0))


def split_by_day(start, end):
    """Splits an interval into pieces by local calendar days."""
    cursor = start
    while cursor < end:
        midnight = datetime.combine(
            cursor.date() + timedelta(days=1), time.min, tzinfo=cursor.tzinfo
        )
        chunk_end = min(end, midnight)
        yield cursor.date(), (chunk_end - cursor).total_seconds()
        cursor = chunk_end


def split_by_hour(start, end):
    """Splits an interval into pieces at hour boundaries.

    An event 23:40 -> 00:20 gives two pieces: 20 min on Sunday at 23:00
    and 20 min on Monday at 00:00. It does not land in one hour whole.
    """
    cursor = start
    while cursor < end:
        next_hour = (cursor + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        chunk_end = min(end, next_hour)
        yield cursor, (chunk_end - cursor).total_seconds()
        cursor = chunk_end


def merge_spans(spans):
    """Merges intervals that overlap or touch."""
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(m) for m in merged]


def total_seconds(intervals):
    return sum((end - start).total_seconds() for start, end in intervals)


def subtract_spans(spans, cut):
    """Parts of spans that do not overlap cut.

    Both lists are sorted, and the intervals within each do not overlap
    (as after merge_spans).
    """
    result = []
    first = 0
    for start, end in spans:
        while first < len(cut) and cut[first][1] <= start:
            first += 1
        cursor = start
        i = first
        while i < len(cut) and cut[i][0] < end:
            if cut[i][0] > cursor:
                result.append((cursor, cut[i][0]))
            cursor = max(cursor, cut[i][1])
            i += 1
        if cursor < end:
            result.append((cursor, end))
    return result


def clip(start, end, intervals, cursor=0):
    """Pieces of [start, end) that lie inside intervals.

    intervals are sorted and do not overlap. Events are walked in order of
    increasing start, so intervals that ended before start are not needed
    by later events either: the advanced cursor is returned so they are
    not scanned every time.
    """
    while cursor < len(intervals) and intervals[cursor][1] <= start:
        cursor += 1
    pieces = []
    i = cursor
    while i < len(intervals) and intervals[i][0] < end:
        piece_start = max(start, intervals[i][0])
        piece_end = min(end, intervals[i][1])
        if piece_end > piece_start:
            pieces.append((piece_start, piece_end))
        i += 1
    return pieces, cursor


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------


def raw_app(event):
    return event.get("data", {}).get("app") or ""


def app_name(event):
    raw = raw_app(event) or config.UNKNOWN_APP
    return app_names.mapping().get(raw.lower(), raw)


def is_system(event):
    return categories.normalize(raw_app(event)) in config.SYSTEM_PROCESSES


# --------------------------------------------------------------------------
# Segments
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Segment:
    app: str        # display name (after app_names)
    process: str    # normalized process name — the key for categories.json
    category: str
    start: datetime
    end: datetime
    idle: bool = False  # AFK time credited under the lenient policy

    @property
    def seconds(self):
        return (self.end - self.start).total_seconds()


@dataclass
class Session:
    app: str
    start: datetime
    end: datetime
    active_seconds: float

    @property
    def span_seconds(self):
        return (self.end - self.start).total_seconds()


@dataclass
class Game:
    app: str
    processes: list
    total_seconds: float
    session_count: int
    avg_session: float
    longest_session: float
    longest_start: datetime | None
    first_played: datetime
    last_played: datetime
    by_day: dict          # {date: seconds}


@dataclass
class FocusBlock:
    """A continuous stay in one application."""
    app: str
    category: str
    start: datetime
    end: datetime
    seconds: float      # active time, including absorbed short focus runs


@dataclass
class CategoryFocus:
    category: str
    seconds: float
    blocks: int
    deep_share: float          # share of time in blocks longer than FOCUS_DEEP_SECONDS
    avg_block: float
    switches_per_hour: float   # switches away from this category per hour of its time


@dataclass
class Focus:
    seconds: float = 0.0
    blocks: int = 0
    switches: int = 0
    switches_per_hour: float = 0.0
    deep_seconds: float = 0.0
    deep_share: float = 0.0
    avg_block: float = 0.0
    by_category: list = field(default_factory=list)   # [CategoryFocus]


@dataclass
class DayRhythm:
    day: date                  # logical day
    seconds: float
    start: float | None        # seconds from the start of the logical day; None — bound unknown
    end: float | None
    after_midnight: float


@dataclass
class WeekRhythm:
    monday: date
    days: int                  # active logical days
    start: float | None        # median of starts
    end: float | None          # median of ends
    after_midnight: float


@dataclass
class Rhythm:
    days: list = field(default_factory=list)    # [DayRhythm] — active days only
    weeks: list = field(default_factory=list)   # [WeekRhythm] — every week of the period
    typical_start: float | None = None
    typical_end: float | None = None
    start_days: int = 0        # how many days gave the median start
    end_days: int = 0
    after_midnight_seconds: float = 0.0
    after_midnight_days: int = 0


@dataclass
class Stats:
    window_bucket: str = ""
    afk_bucket: str = ""
    event_count: int = 0
    afk_filtered: bool = True

    period_start: datetime | None = None
    period_end: datetime | None = None

    total_seconds: float = 0.0        # active time in windows
    afk_seconds: float = 0.0          # computer on, user away
    not_afk_seconds: float = 0.0      # computer on, user at it
    system_seconds: float = 0.0       # filtered-out system processes
    window_afk_discarded: float = 0.0  # window time cut by the AFK filter
    afk_counted_seconds: float = 0.0  # part of AFK credited to lenient categories

    by_app: list = field(default_factory=list)        # [(name, seconds)]
    app_categories: dict = field(default_factory=dict)  # {name: category}
    hidden_apps: int = 0
    by_category: list = field(default_factory=list)   # [(category, seconds)]
    uncategorized_apps: list = field(default_factory=list)  # [(name, [processes], sec)]
    category_warnings: list = field(default_factory=list)
    category_order: list = field(default_factory=list)  # order from categories.json
    lenient_categories: list = field(default_factory=list)  # with the lenient AFK policy
    categories_created: bool = False
    by_day: dict = field(default_factory=dict)        # {date: seconds}
    active_days: list = field(default_factory=list)
    observed_days: list = field(default_factory=list)  # days of the period with at least one event
    missing_days: list = field(default_factory=list)   # days of the period without any event
    calendar_days: int = 0     # calendar days from the first event to today, inclusive
    by_month: dict = field(default_factory=dict)      # {(year, month): seconds}
    heatmap: list = field(default_factory=list)       # [7][24] seconds
    sessions: list = field(default_factory=list)

    games: list = field(default_factory=list)          # [Game]
    games_unplayed: list = field(default_factory=list)  # [(name, [processes])]
    games_by_day: dict = field(default_factory=dict)    # {date: seconds}

    focus: Focus = field(default_factory=Focus)
    rhythm: Rhythm = field(default_factory=Rhythm)

    @property
    def games_total(self):
        return sum(g.total_seconds for g in self.games)

    @property
    def games_best_day(self):
        """(date, seconds) of the most active gaming day, or None."""
        if not self.games_by_day:
            return None
        return max(self.games_by_day.items(), key=lambda kv: kv[1])

    @property
    def avg_per_day(self):
        """Average per observed day.

        The denominator is days with at least one event, not only active
        days. A day when the computer was on but little got done is a
        real quiet day and should pull the average down. A day without
        any event is missing data, not zero, so it stays out of the
        denominator.
        """
        days = len(self.observed_days)
        return self.total_seconds / days if days else 0.0

    @property
    def inactive_days(self):
        """Calendar days without activity, for the banner.

        Days without any event are included: ActivityWatch starts with the
        system, so missing data means the computer was off. The banner's
        denominator (calendar_days) is deliberately different from the
        daily average's (observed_days).
        """
        return max(0, self.calendar_days - len(self.active_days))

    @property
    def observed_by_month(self):
        """{(year, month): days with data} — denominator of the monthly average."""
        counts = defaultdict(int)
        for day in self.observed_days:
            counts[(day.year, day.month)] += 1
        return dict(counts)

    @property
    def powered_seconds(self):
        """Computer-on time: not-afk + afk according to the AFK watcher."""
        return self.not_afk_seconds + self.afk_seconds

    @property
    def other_seconds(self):
        """Not-afk time with no window in focus, plus system processes.

        The difference between "at the computer" and "active in an
        application": switching desktops, untitled windows, filtered-out
        system processes. AFK credited under the lenient policy is not
        part of not-afk, so it is subtracted from active time before the
        comparison.
        """
        in_not_afk = self.total_seconds - self.afk_counted_seconds
        return max(0.0, self.not_afk_seconds - in_not_afk)

    @property
    def afk_uncounted_seconds(self):
        """AFK that was not credited to any application.

        Together with active and "other" it gives exactly powered_seconds:
        credited AFK already sits inside active time and is not shown a
        second time.
        """
        return max(0.0, self.afk_seconds - self.afk_counted_seconds)


def active_intervals(afk_events):
    """Merged intervals when the status is not-afk."""
    return merge_spans(
        event_span(e)
        for e in afk_events
        if e.get("data", {}).get("status") == "not-afk"
    )


def afk_intervals(afk_events):
    """Merged intervals when the status is afk (computer on, user away)."""
    return merge_spans(
        event_span(e) for e in afk_events if e.get("data", {}).get("status") == "afk"
    )


def lenient_intervals(afk_spans, active_spans, cap):
    """AFK time that may be credited to categories with the lenient policy.

    From each continuous AFK stretch only the first cap seconds are taken;
    the rest of the stretch is dropped, whatever window is in focus. The
    overlap with not-afk is cut out: the watcher sometimes writes both
    statuses for the same second, and without this it would count twice.
    """
    if cap <= 0:
        return []
    limit = timedelta(seconds=cap)
    capped = [(start, min(end, start + limit)) for start, end in afk_spans]
    return subtract_spans(capped, active_spans)


def build_segments(window_events, intervals, index=None, idle_intervals=()):
    """Window events clipped to the active intervals.

    Windows of categories with the lenient policy are also clipped to
    idle_intervals — the credited part of AFK stretches
    (lenient_intervals). Such pieces are marked idle=True. System
    processes and "uncategorized" are always strict.

    Returns (segments, seconds_cut_as_afk, system_seconds, warnings).
    """
    if index is None:
        index = categories.build_index(categories.load_categories()[0])

    spans = sorted((event_span(e), i) for i, e in enumerate(window_events))

    segments = []
    system_seconds = 0.0
    kept_seconds = 0.0
    raw_seconds = 0.0
    resolved = {}       # process -> (category, conflict), to classify only once
    warnings = {}       # process -> conflict text

    first = idle_first = 0
    for (ev_start, ev_end), event_index in spans:
        event = window_events[event_index]
        raw_seconds += (ev_end - ev_start).total_seconds()

        pieces, first = clip(ev_start, ev_end, intervals, first)

        if is_system(event):
            seconds = total_seconds(pieces)
            kept_seconds += seconds
            system_seconds += seconds
            continue

        process = categories.normalize(raw_app(event))
        if process not in resolved:
            resolved[process] = categories.classify(process, index)
        category, warning = resolved[process]

        pieces = [(start, end, False) for start, end in pieces]
        if (idle_intervals and categories.afk_policy(category, index)
                == categories.AFK_LENIENT):
            idle, idle_first = clip(ev_start, ev_end, idle_intervals, idle_first)
            pieces += [(start, end, True) for start, end in idle]

        for start, end, idle in pieces:
            kept_seconds += (end - start).total_seconds()
            segments.append(
                Segment(app_name(event), process, category, start, end, idle)
            )
        # A conflict is reported only if the process gave at least a second
        # to the statistics.
        if pieces and warning:
            warnings[process] = warning

    segments.sort(key=lambda s: s.start)
    return segments, raw_seconds - kept_seconds, system_seconds, list(warnings.values())


def observed_days(*event_lists):
    """Days with at least one event from any of the buckets.

    An event across midnight makes both days observed. A zero-length event
    counts too: the watcher was running that day.
    """
    days = set()
    for events in event_lists:
        for event in events:
            start, end = event_span(event)
            days.add(start.date())
            days.update(day for day, _ in split_by_day(start, end))
    return days


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------


def totals_by_app(segments):
    totals = defaultdict(float)
    for s in segments:
        totals[s.app] += s.seconds
    return totals


def totals_by_category(segments):
    totals = defaultdict(float)
    for s in segments:
        totals[s.category] += s.seconds
    return totals


def categories_of_apps(segments):
    """The category of each application.

    app_names can map several executables to one name, so the category in
    which the application spent the most time is taken.
    """
    pairs = defaultdict(float)
    for s in segments:
        pairs[(s.app, s.category)] += s.seconds

    best = {}
    for (app, category), seconds in sorted(pairs.items(), key=lambda kv: -kv[1]):
        best.setdefault(app, category)
    return best


def uncategorized(segments):
    """[(name, [processes], seconds)] for everything that landed in no category.

    The processes are exactly the strings to put into categories.json,
    not the display names.
    """
    seconds = defaultdict(float)
    processes = defaultdict(set)
    for s in segments:
        if s.category != config.UNCATEGORIZED:
            continue
        seconds[s.app] += s.seconds
        processes[s.app].add(s.process)

    return [
        (app, sorted(processes[app]), total)
        for app, total in sorted(seconds.items(), key=lambda kv: kv[1], reverse=True)
    ]


def totals_by_day(segments):
    totals = defaultdict(float)
    for s in segments:
        for day, seconds in split_by_day(s.start, s.end):
            totals[day] += seconds
    return dict(totals)


def totals_by_month(by_day):
    totals = defaultdict(float)
    for day, seconds in by_day.items():
        totals[(day.year, day.month)] += seconds
    return dict(totals)


def build_heatmap(segments):
    """A [weekday][hour] matrix in seconds.

    Intervals are cut at hour boundaries, so an event across midnight is
    spread over two hours and two different weekdays.
    """
    grid = [[0.0] * 24 for _ in range(7)]
    for s in segments:
        for moment, seconds in split_by_hour(s.start, s.end):
            grid[moment.weekday()][moment.hour] += seconds
    return grid


def find_sessions(segments, gap=None, min_seconds=None):
    """Continuous sessions in one application.

    The segments are already clipped to not-afk, so stepping away from the
    computer for longer than gap breaks a session. Shorter pauses
    (switching to another window, a minute for coffee) do not.

    Games are counted with their own GAME_SESSION_GAP_SECONDS threshold and
    no minimum duration, so a short launch counts as a session too.

    active_seconds is the time actually spent in the application, without
    pauses; span is from the start to the end of the session by the clock.
    """
    gap = config.SESSION_GAP_SECONDS if gap is None else gap
    min_seconds = config.MIN_SESSION_SECONDS if min_seconds is None else min_seconds

    sessions = []
    current = None

    for s in segments:
        if (
            current is not None
            and s.app == current.app
            and (s.start - current.end).total_seconds() <= gap
        ):
            current.end = max(current.end, s.end)
            current.active_seconds += s.seconds
        else:
            if current is not None:
                sessions.append(current)
            current = Session(s.app, s.start, s.end, s.seconds)

    if current is not None:
        sessions.append(current)

    sessions = [s for s in sessions if s.active_seconds >= min_seconds]
    sessions.sort(key=lambda s: s.active_seconds, reverse=True)
    return sessions


def display_name(process):
    """Display name for a normalized process name."""
    names = app_names.mapping()
    return names.get(f"{process}.exe", names.get(process, process))


def game_stats(segments):
    """Statistics for every game seen in the data.

    Sessions are counted separately for each game and only over its own
    segments: a couple of minutes in the browser must not break a game
    session if it fits into GAME_SESSION_GAP_SECONDS.
    """
    by_game = defaultdict(list)
    for s in segments:
        if s.category == config.GAME_CATEGORY:
            by_game[s.app].append(s)

    games = []
    for app, own in by_game.items():
        own.sort(key=lambda s: s.start)
        sessions = find_sessions(
            own, gap=config.GAME_SESSION_GAP_SECONDS, min_seconds=0
        )
        total = sum(s.seconds for s in own)
        longest = max(sessions, key=lambda s: s.active_seconds) if sessions else None

        day_totals = defaultdict(float)
        for segment in own:
            for day, seconds in split_by_day(segment.start, segment.end):
                day_totals[day] += seconds

        games.append(
            Game(
                app=app,
                processes=sorted({s.process for s in own}),
                total_seconds=total,
                session_count=len(sessions),
                avg_session=total / len(sessions) if sessions else 0.0,
                longest_session=longest.active_seconds if longest else 0.0,
                longest_start=longest.start if longest else None,
                first_played=own[0].start,
                last_played=max(s.end for s in own),
                by_day=dict(day_totals),
            )
        )

    if config.GAMES_SORT == "last":
        games.sort(key=lambda g: g.last_played, reverse=True)
    else:
        games.sort(key=lambda g: g.total_seconds, reverse=True)
    return games


def unplayed_games(category_data, games):
    """Games from categories.json that are absent from the data: [(name, [processes])].

    If several processes map to one name (game.exe and game_eac.exe), the game
    counts as launched when at least one of them was seen.
    """
    entry = category_data.get(config.GAME_CATEGORY, {})
    listed = [categories.normalize(p) for p in entry.get("processes", [])]

    played_names = {g.app for g in games}
    played_processes = {p for g in games for p in g.processes}

    grouped = defaultdict(list)
    for process in listed:
        if process in played_processes:
            continue
        grouped[display_name(process)].append(process)

    return sorted(
        (name, sorted(processes))
        for name, processes in grouped.items()
        if name not in played_names
    )


def sort_categories(totals):
    """By time descending, but "uncategorized" always last.

    The "uncategorized" row stays in the table even with zero time — so
    it is visible that the category exists and is empty right now.
    """
    known = sorted(
        ((c, s) for c, s in totals.items() if c != config.UNCATEGORIZED),
        key=lambda kv: kv[1],
        reverse=True,
    )
    known.append((config.UNCATEGORIZED, totals.get(config.UNCATEGORIZED, 0.0)))
    return known


# --------------------------------------------------------------------------
# Attention fragmentation
# --------------------------------------------------------------------------


def focus_blocks(segments, dwell=None, gap=None):
    """Blocks of staying in one application and the switches between them.

    1. Adjacent segments of one application with a pause no longer than
       gap merge into a run: a window title change is not a switch.
    2. A run shorter than dwell is not a stay but a pass-through: alt-tab,
       a taskbar click, a notification. It switches nothing, and its
       seconds go to the ongoing block. A pass-through at the start of a
       sitting goes to the first real block.
    3. A move between runs of dwell or longer in different applications is
       a switch. A pause longer than gap (stepping away from the computer)
       closes the block without a switch: coming back to a different
       application after a break is a fresh start, not a jump of attention.

    Every second of the segments lands in exactly one block, so the sum of
    the blocks equals active time. Returns (blocks, switches), where a
    switch is the category of the block that was left.
    """
    dwell = config.FOCUS_MIN_DWELL_SECONDS if dwell is None else dwell
    gap = config.SESSION_GAP_SECONDS if gap is None else gap

    runs = []   # [application, category, start, end, seconds]
    for s in segments:
        if (runs and runs[-1][0] == s.app
                and (s.start - runs[-1][3]).total_seconds() <= gap):
            runs[-1][3] = max(runs[-1][3], s.end)
            runs[-1][4] += s.seconds
        else:
            runs.append([s.app, s.category, s.start, s.end, s.seconds])

    blocks, switches = [], []
    current = None      # the ongoing FocusBlock
    pending = []        # pass-throughs at the start of a sitting, before the first block
    last_end = None

    def close_sitting():
        if current is not None:
            blocks.append(current)
        elif pending:
            # A sitting made only of pass-throughs: the time is not lost but
            # becomes a short block of the first application.
            app, category, start = pending[0][:3]
            end = max(run[3] for run in pending)
            blocks.append(FocusBlock(app, category, start, end,
                                     sum(run[4] for run in pending)))

    for run in runs:
        app, category, start, end, seconds = run
        if last_end is not None and (start - last_end).total_seconds() > gap:
            close_sitting()
            current, pending = None, []
        last_end = end if last_end is None else max(last_end, end)

        if seconds < dwell:
            if current is None:
                pending.append(run)
            else:
                current.end = max(current.end, end)
                current.seconds += seconds
            continue

        if current is not None and current.app == app:
            current.end = max(current.end, end)
            current.seconds += seconds
            continue

        if current is not None:
            blocks.append(current)
            switches.append(current.category)
        lead = sum(p[4] for p in pending)
        current = FocusBlock(app, category, pending[0][2] if pending else start,
                             end, seconds + lead)
        pending = []

    close_sitting()
    return blocks, switches


def focus_stats(segments):
    """Switches per hour, share of deep blocks, average block.

    Per category — the same within the category: where work goes in long
    blocks and where in bits and pieces. A block belongs to the category
    of its application.
    """
    blocks, switches = focus_blocks(segments)
    total = sum(b.seconds for b in blocks)
    if not blocks or total <= 0:
        return Focus()

    per = defaultdict(lambda: [0.0, 0, 0.0, 0])  # seconds, blocks, deep, switches
    for block in blocks:
        row = per[block.category]
        row[0] += block.seconds
        row[1] += 1
        if block.seconds > config.FOCUS_DEEP_SECONDS:
            row[2] += block.seconds
    for source in switches:
        per[source][3] += 1

    by_category = [
        CategoryFocus(
            category=category,
            seconds=seconds,
            blocks=count,
            deep_share=deep / seconds if seconds else 0.0,
            avg_block=seconds / count,
            switches_per_hour=left / (seconds / 3600) if seconds else 0.0,
        )
        for category, (seconds, count, deep, left) in per.items()
    ]
    by_category.sort(
        key=lambda c: (c.category == config.UNCATEGORIZED, -c.seconds)
    )

    deep_seconds = sum(row[2] for row in per.values())
    return Focus(
        seconds=total,
        blocks=len(blocks),
        switches=len(switches),
        switches_per_hour=len(switches) / (total / 3600),
        deep_seconds=deep_seconds,
        deep_share=deep_seconds / total,
        avg_block=total / len(blocks),
        by_category=by_category,
    )


# --------------------------------------------------------------------------
# Daily rhythm
# --------------------------------------------------------------------------


def logical_day(moment):
    """Logical day of a moment: before DAY_START_SECONDS it is still the previous day."""
    return (moment - timedelta(seconds=config.DAY_START_SECONDS)).date()


def logical_start(day, tzinfo):
    """The moment the logical day starts."""
    return (datetime.combine(day, time.min, tzinfo=tzinfo)
            + timedelta(seconds=config.DAY_START_SECONDS))


def split_by_logical_day(start, end):
    """Splits an interval at logical day boundaries: (day, start, end)."""
    cursor = start
    while cursor < end:
        day = logical_day(cursor)
        piece_end = min(end, logical_start(day + timedelta(days=1), cursor.tzinfo))
        yield day, cursor, piece_end
        cursor = piece_end


def rhythm_stats(segments, observed_from, now=None):
    """When the day starts and ends, and how that changes week to week.

    The day is logical: from DAY_START_SECONDS to the same time the next
    day, so a sitting until 02:33 is the end of yesterday, not the start
    of today. The bounds of a day are its first and last active moment;
    "usual" is the median over active days.

    Two bounds are deliberately not counted: the start of the first day is
    cut by the start of observation (observed_from), not by when you sat
    down at the computer, and the end of the current day (now) has not
    come yet.
    """
    now = now or datetime.now().astimezone()
    first_day = logical_day(observed_from)
    open_day = logical_day(now)

    spans = {}  # day -> [first moment, last moment, seconds, after midnight]
    for s in segments:
        for day, start, end in split_by_logical_day(s.start, s.end):
            row = spans.setdefault(day, [start, end, 0.0, 0.0])
            row[0] = min(row[0], start)
            row[1] = max(row[1], end)
            row[2] += (end - start).total_seconds()
            for calendar_day, seconds in split_by_day(start, end):
                if calendar_day > day:
                    row[3] += seconds

    days = []
    for day in sorted(spans):
        first, last, seconds, after_midnight = spans[day]
        if seconds < config.MIN_DAY_SECONDS:
            continue
        origin = logical_start(day, first.tzinfo)
        days.append(DayRhythm(
            day=day,
            seconds=seconds,
            start=None if day == first_day else (first - origin).total_seconds(),
            end=None if day == open_day else (last - origin).total_seconds(),
            after_midnight=after_midnight,
        ))

    def typical(values):
        values = [v for v in values if v is not None]
        return (median(values) if values else None), len(values)

    weeks = []
    if days:
        by_week = defaultdict(list)
        for row in days:
            by_week[row.day - timedelta(days=row.day.weekday())].append(row)
        monday = days[0].day - timedelta(days=days[0].day.weekday())
        while monday <= days[-1].day:
            rows = by_week.get(monday, [])
            weeks.append(WeekRhythm(
                monday=monday,
                days=len(rows),
                start=typical(r.start for r in rows)[0],
                end=typical(r.end for r in rows)[0],
                after_midnight=sum(r.after_midnight for r in rows),
            ))
            monday += timedelta(days=7)

    typical_start, start_days = typical(r.start for r in days)
    typical_end, end_days = typical(r.end for r in days)
    return Rhythm(
        days=days,
        weeks=weeks,
        typical_start=typical_start,
        typical_end=typical_end,
        start_days=start_days,
        end_days=end_days,
        after_midnight_seconds=sum(row[3] for row in spans.values()),
        after_midnight_days=sum(
            1 for row in days if row.after_midnight >= config.MIN_DAY_SECONDS
        ),
    )


# --------------------------------------------------------------------------


def collect_stats(fetch_buckets=None, fetch_events=None, load_categories=None):
    """Pulls the data from ActivityWatch and computes everything the report needs.

    The three optional arguments replace the data sources — the API and
    categories.json — and are used by demo mode (demo.py). Without them
    the module functions are looked up at call time.
    """
    fetch_buckets = fetch_buckets or get_buckets
    fetch_events = fetch_events or get_events
    load_categories = load_categories or categories.load_categories

    buckets = fetch_buckets()

    window_bucket = find_bucket(buckets, "currentwindow", "aw-watcher-window")
    if not window_bucket:
        raise ActivityWatchError(tr("errors.no_window_bucket"))

    window_events = fetch_events(window_bucket)
    if not window_events:
        raise ActivityWatchError(tr("errors.no_window_events"))

    afk_bucket = find_bucket(buckets, "afkstatus", "aw-watcher-afk")
    afk_events = []
    idle = []
    if afk_bucket:
        afk_events = fetch_events(afk_bucket)
        intervals = active_intervals(afk_events)
        afk_spans = afk_intervals(afk_events)
        idle = lenient_intervals(
            afk_spans, intervals, config.AFK_LENIENT_CAP_SECONDS
        )
        not_afk = total_seconds(intervals)
        afk = total_seconds(afk_spans)
        afk_filtered = True
    else:
        # Without an AFK bucket all window time is counted — better than
        # nothing, and the report says so honestly.
        earliest = to_local(window_events[-1]["timestamp"]) - timedelta(days=1)
        latest = to_local(window_events[0]["timestamp"]) + timedelta(days=1)
        intervals = [(earliest, latest)]
        not_afk = afk = 0.0
        afk_filtered = False

    category_data, created, load_errors = load_categories()
    index = categories.build_index(category_data)

    segments, discarded, system_seconds, conflicts = build_segments(
        window_events, intervals, index, idle
    )
    if not segments:
        raise ActivityWatchError(tr("errors.nothing_left"))

    # The period starts with the earliest event in the database, not the
    # first active segment: ActivityWatch starts with the system, so the
    # first event is the first day the computer was switched on.
    period_start = min(
        to_local(e["timestamp"]) for e in (*window_events, *afk_events)
    )
    period_end = max(s.end for s in segments)

    # Days of the period are split into those with at least one event and
    # those without any. The latter are days the computer was off. They do
    # not enter the daily average; in the banner they count as inactive
    # (calendar_days).
    seen = observed_days(window_events, afk_events)
    calendar = [
        period_start.date() + timedelta(days=i)
        for i in range((period_end.date() - period_start.date()).days + 1)
    ]
    today = datetime.now().astimezone().date()

    by_app = totals_by_app(segments)
    by_day = totals_by_day(segments)
    app_categories = categories_of_apps(segments)

    shown = sorted(
        ((app, s) for app, s in by_app.items() if s >= config.MIN_APP_SECONDS),
        key=lambda kv: kv[1],
        reverse=True,
    )

    active = sum(by_app.values())

    games = game_stats(segments)
    games_by_day = defaultdict(float)
    for game in games:
        for day, seconds in game.by_day.items():
            games_by_day[day] += seconds

    return Stats(
        window_bucket=window_bucket,
        afk_bucket=afk_bucket or "",
        event_count=len(window_events),
        afk_filtered=afk_filtered,
        period_start=period_start,
        period_end=period_end,
        total_seconds=active,
        afk_seconds=afk,
        not_afk_seconds=not_afk or active,
        system_seconds=system_seconds,
        window_afk_discarded=discarded,
        afk_counted_seconds=sum(s.seconds for s in segments if s.idle),
        by_app=shown[: config.TOP_N],
        app_categories=app_categories,
        hidden_apps=len(by_app) - len(shown),
        by_category=sort_categories(totals_by_category(segments)),
        uncategorized_apps=uncategorized(segments),
        category_warnings=load_errors + index.warnings + conflicts,
        category_order=list(category_data),
        lenient_categories=[
            c for c in category_data
            if categories.afk_policy(c, index) == categories.AFK_LENIENT
        ],
        categories_created=created,
        by_day=by_day,
        active_days=sorted(
            d for d, s in by_day.items() if s >= config.MIN_DAY_SECONDS
        ),
        observed_days=[d for d in calendar if d in seen],
        missing_days=[d for d in calendar if d not in seen],
        calendar_days=(today - period_start.date()).days + 1,
        by_month=totals_by_month(by_day),
        heatmap=build_heatmap(segments),
        sessions=find_sessions(segments)[: config.TOP_SESSIONS],
        games=games,
        games_unplayed=unplayed_games(category_data, games),
        games_by_day=dict(games_by_day),
        focus=focus_stats(segments),
        rhythm=rhythm_stats(segments, period_start),
    )


def recent_days(stats, count=None):
    """[(date, seconds)] for the last N days, including empty ones."""
    count = count or config.RECENT_DAYS
    last = max(stats.by_day) if stats.by_day else date.today()
    days = [last - timedelta(days=i) for i in range(count - 1, -1, -1)]
    return [(d, stats.by_day.get(d, 0.0)) for d in days]


if __name__ == "__main__":
    # A plain-text dump for checking the data without building the HTML.
    import sys

    try:
        stats = collect_stats()
    except ActivityWatchError as e:
        print(e)
        sys.exit(1)

    label = i18n.category_label
    print(f"Events: {stats.event_count}   bucket: {stats.window_bucket}")
    print(f"Period: {stats.period_start:%Y-%m-%d %H:%M} — {stats.period_end:%Y-%m-%d %H:%M}")
    print(f"Active time:        {fmt_duration(stats.total_seconds)}")
    print(f"AFK:                {fmt_duration(stats.afk_seconds)}")
    print(f"  credited of it:   {fmt_duration(stats.afk_counted_seconds)}"
          f"  (lenient, cap {config.AFK_LENIENT_CAP_SECONDS // 60} min)")
    print(f"Computer on:        {fmt_duration(stats.powered_seconds)}")
    print(f"Other (not-afk):    {fmt_duration(stats.other_seconds)}")
    print(f"Days with data:     {len(stats.observed_days)}")
    print(f"Active days:        {len(stats.active_days)} of {stats.calendar_days} "
          f"calendar days, inactive {stats.inactive_days}")
    print(f"Average per day:    {fmt_duration(stats.avg_per_day)}")
    if stats.missing_days:
        print(f"Days without data:  {len(stats.missing_days)}: "
              + ", ".join(f"{d:%d.%m}" for d in stats.missing_days))
    print()
    for category, seconds in stats.by_category:
        share = seconds / stats.total_seconds * 100 if stats.total_seconds else 0
        print(f"  {label(category):<18} {fmt_duration(seconds):>12}  {share:5.1f}%")

    focus = stats.focus
    print(f"\nFragmentation (threshold {config.FOCUS_MIN_DWELL_SECONDS} s, "
          f"deep block > {config.FOCUS_DEEP_SECONDS // 60} min):")
    print(f"  switches: {focus.switches}, {focus.switches_per_hour:.1f}/h;"
          f" blocks: {focus.blocks}, average {fmt_duration(focus.avg_block)};"
          f" in deep blocks {focus.deep_share * 100:.0f}%")
    for c in focus.by_category:
        print(f"  {label(c.category):<18} {c.deep_share * 100:4.0f}%  "
              f"avg {fmt_duration(c.avg_block):>10}  "
              f"{c.switches_per_hour:5.1f}/h  blocks {c.blocks}")

    rhythm = stats.rhythm
    if rhythm.days:
        print(f"\nRhythm (day from {fmt_clock(0)}): usually "
              f"{fmt_clock(rhythm.typical_start)}–{fmt_clock(rhythm.typical_end)}; "
              f"after midnight {fmt_duration(rhythm.after_midnight_seconds)} "
              f"on {rhythm.after_midnight_days} days")
        for week in rhythm.weeks:
            span = (f"{fmt_clock(week.start)}–{fmt_clock(week.end)}"
                    if week.start is not None and week.end is not None else "—")
            print(f"  week of {week.monday:%d.%m}: {week.days} d  {span}")
    if stats.category_warnings:
        print("\nCategory conflicts:")
        for warning in stats.category_warnings:
            print(f"  ! {warning}")

    if stats.uncategorized_apps:
        print("\nUncategorized:")
        for app, processes, seconds in stats.uncategorized_apps:
            print(f"  {i18n.app_label(app):<24} {fmt_duration(seconds):>10}   "
                  f"{', '.join(processes)}")
