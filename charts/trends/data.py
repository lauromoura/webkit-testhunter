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

"""Loading and unifying the per-configuration CSVs produced by ``report.py``.

Each CSV holds one build per row, with a ``configuration`` column (e.g.
``WPE-Release``) added by ``report.py -c``. This module concatenates the
configurations into a single long DataFrame (a ``date`` column, not an index),
adds the derived metrics the charts need, and applies the interrupted-run
policy in one central place.
"""

import os
import sys

import numpy as np
import pandas as pd

# The standard set plotted when no CSV paths are given on the command line.
# (Apple-Release is intentionally excluded: its data is stale/partial. Pass it
# explicitly on the command line if you want it.)
STANDARD_CSVS = [
    "WPE-Release.csv",
    "WPE-Debug.csv",
    "WPE-ARM64-Release.csv",
    "GTK-Release.csv",
    "GTK-Debug.csv",
]


def read_csv(path):
    """Read one per-config CSV into a long DataFrame with a ``date`` column.

    Dates are parsed naively (bot-local, as stored). If the file lacks a
    ``configuration`` column (i.e. it wasn't stamped by ``report.py -c``), it is
    derived from the filename stem.
    """
    df = pd.read_csv(path, parse_dates=["date"])
    if "configuration" not in df.columns:
        df["configuration"] = os.path.splitext(os.path.basename(path))[0]
    return df


def interrupted_bool(df):
    """Return the ``interrupted`` column coerced to a clean boolean Series.

    Handles bool, numeric, and string ("True"/"False") encodings; NaN -> False.
    """
    col = df["interrupted"]
    if col.dtype == object:
        return col.astype(str).str.strip().str.lower().isin(("true", "1"))
    return col.fillna(False).astype(bool)


def add_derived_metrics(df):
    """Add the derived metric columns used by the charts (returns a copy).

    * ``unexpected_ERROR`` = crashes + timeouts (early-exit "errors")
    * ``unexpected_FAIL``  = image + text diffs
    * ``fixable``          = fixable - skipped (matches plot.py's adjustment)
    * ``num_run``          = passes + flaky + regressions (the % denominator)
    * ``pct_regressions`` / ``pct_flaky`` = share of run, in percent
    """
    df = df.copy()
    df["unexpected_ERROR"] = df["unexpected_CRASH"] + df["unexpected_TIMEOUT"]
    df["unexpected_FAIL"] = df["unexpected_IMAGE"] + df["unexpected_TEXT"]
    df["fixable"] = df["fixable"] - df["skipped"]
    df["num_run"] = df["num_passes"] + df["num_flaky"] + df["num_regressions"]
    denom = df["num_run"].replace(0, np.nan)
    df["pct_regressions"] = df["num_regressions"] / denom * 100
    df["pct_flaky"] = df["num_flaky"] / denom * 100
    return df


def load_configs(paths=None):
    """Load and unify configurations into one long DataFrame.

    ``paths=None`` loads :data:`STANDARD_CSVS` (a missing standard file is
    warned about and skipped). When paths are given explicitly, a missing file
    is a hard error -- we don't silently drop something the user named.
    """
    explicit = paths is not None
    paths = paths if explicit else STANDARD_CSVS

    frames = []
    for path in paths:
        if not os.path.exists(path):
            if explicit:
                raise FileNotFoundError(path)
            print(f"Warning: skipping missing standard CSV {path}", file=sys.stderr)
            continue
        frames.append(read_csv(path))

    if not frames:
        raise ValueError("No input CSVs could be loaded")

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["configuration", "date"]).reset_index(drop=True)
    return add_derived_metrics(df)


def apply_interrupted_policy(df, include_interrupted):
    """Drop interrupted builds unless ``include_interrupted`` is set.

    Dropping whole rows (rather than nulling a single metric) makes the gap
    real for every metric, which is what time-based smoothing needs to leave a
    genuine NaN gap instead of a fabricated flat line. Returns a copy.
    """
    if include_interrupted:
        return df.copy()
    return df[~interrupted_bool(df)].copy()
