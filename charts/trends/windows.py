#!/usr/bin/env python3
# coding: utf-8
#
#  Copyright 2025 Igalia S.L.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Time windows: a named (start, end) range, plus parsing of CLI presets.

A :class:`Window` carries a human name (used in output filenames) and an
inclusive ``[start, end]`` range; either bound may be ``None`` for open-ended.
Several CLI inputs resolve to windows:

* ``--year 2025``            -> a full calendar year
* ``--last 12m`` / ``90d``   -> a trailing range ending today
* ``--windows 2024,2024-25`` -> calendar years and ``START-END`` year spans
* ``--since`` / ``--until``  -> an explicit custom range
"""

import re
from dataclasses import dataclass

import pandas as pd

_SLUG_RE = re.compile(r"[^A-Za-z0-9_-]+")
_LAST_RE = re.compile(r"^(\d+)\s*([dwmy])$", re.IGNORECASE)

_OFFSETS = {
    "d": lambda n: pd.Timedelta(days=n),
    "w": lambda n: pd.Timedelta(weeks=n),
    "m": lambda n: pd.DateOffset(months=n),
    "y": lambda n: pd.DateOffset(years=n),
}

# Singular unit words for human-readable --last labels (pluralized as needed).
_UNIT_WORDS = {"d": "day", "w": "week", "m": "month", "y": "year"}


@dataclass(frozen=True)
class Window:
    """A named, inclusive date range. ``start``/``end`` may be ``None``.

    ``name`` is the terse, filesystem-safe identifier used in output filenames;
    ``label`` (when set) is the human-readable form shown in chart titles, e.g.
    name ``last-12m`` -> label ``last 12 months``. ``display`` returns the label
    if present, otherwise the name.
    """

    name: str
    start: pd.Timestamp | None
    end: pd.Timestamp | None
    label: str | None = None

    @property
    def display(self):
        """Human-readable form for titles (falls back to ``name``)."""
        return self.label or self.name

    def slug(self):
        """A filesystem-safe version of the name, for output filenames."""
        return _SLUG_RE.sub("-", self.name).strip("-") or "window"


def _year_bounds(year):
    """Inclusive (Jan 1 00:00:00, Dec 31 23:59:59) timestamps for a year."""
    start = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year, month=12, day=31, hour=23, minute=59, second=59)
    return start, end


def _full_year(two_or_four_digit, century_from):
    """Expand a 2-digit year to the century of ``century_from`` (e.g. 25 -> 2025)."""
    value = int(two_or_four_digit)
    if len(str(two_or_four_digit)) == 2:
        value += (century_from // 100) * 100
    return value


def parse_window_token(tok):
    """Parse one ``--windows`` token into a :class:`Window`.

    Accepted forms::

        2025                 single calendar year
        2024-25 / 2022-2025  span of calendar years (2-digit end shares century)
        2024-01-01..2025-06-30   explicit inclusive date range
    """
    tok = tok.strip()
    if ".." in tok:
        left, right = (part.strip() for part in tok.split("..", 1))
        start = pd.Timestamp(left)
        end = pd.Timestamp(right)
        return Window(f"{left}_{right}", start, end, label=f"{left} to {right}")

    parts = tok.split("-")
    if len(parts) == 1 and parts[0].isdigit():
        start, end = _year_bounds(int(parts[0]))
        return Window(tok, start, end)
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        start_year = int(parts[0])
        end_year = _full_year(parts[1], start_year)
        start, _ = _year_bounds(start_year)
        _, end = _year_bounds(end_year)
        return Window(f"{start_year}-{end_year % 100:02d}", start, end,
                      label=f"{start_year}-{end_year}")

    raise ValueError(
        f"Unrecognized window token {tok!r}; expected e.g. 2025, 2024-25, "
        "or 2024-01-01..2025-06-30"
    )


def _parse_last(spec, today):
    """Resolve ``--last`` (e.g. ``12m``, ``90d``, ``2y``) to a trailing window."""
    match = _LAST_RE.match(spec.strip())
    if not match:
        raise ValueError(
            f"Unrecognized --last value {spec!r}; expected e.g. 90d, 12m, 2y"
        )
    amount, unit = int(match.group(1)), match.group(2).lower()
    start = today - _OFFSETS[unit](amount)
    word = _UNIT_WORDS[unit] + ("s" if amount != 1 else "")
    label = f"last {amount} {word}"
    return Window(f"last-{amount}{unit}", pd.Timestamp(start), today, label=label)


def resolve_windows(*, windows=None, year=None, last=None, since=None,
                    until=None, today=None):
    """Build the list of windows requested via the CLI.

    Every provided source contributes a window (they are unioned, in order:
    ``--windows`` tokens, ``--year``, ``--last``, then ``--since/--until``). If
    nothing is provided, a single open-ended ``all`` window is returned.
    """
    if today is None:
        today = pd.Timestamp.today().normalize()

    resolved = []

    for tok in windows or []:
        if tok.strip():
            resolved.append(parse_window_token(tok))

    if year is not None:
        start, end = _year_bounds(int(year))
        resolved.append(Window(str(year), start, end))

    if last:
        resolved.append(_parse_last(last, today))

    if since is not None or until is not None:
        start = pd.Timestamp(since) if since is not None else None
        end = pd.Timestamp(until) if until is not None else None
        if start is not None and end is not None:
            name = f"{start:%Y%m%d}-{end:%Y%m%d}"
            label = f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
        elif start is not None:
            name = f"since-{start:%Y%m%d}"
            label = f"since {start:%Y-%m-%d}"
        else:
            name = f"until-{end:%Y%m%d}"
            label = f"until {end:%Y-%m-%d}"
        resolved.append(Window(name, start, end, label=label))

    if not resolved:
        resolved.append(Window("all", None, None, label="all time"))

    return resolved


def slice_window(df, window):
    """Return the rows of ``df`` whose ``date`` falls inside ``window``.

    Bounds are inclusive; an open (``None``) bound is not constrained. An empty
    result is allowed and handled by callers.
    """
    mask = pd.Series(True, index=df.index)
    if window.start is not None:
        mask &= df["date"] >= window.start
    if window.end is not None:
        mask &= df["date"] <= window.end
    return df[mask].copy()
