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

"""Smoothing strategies.

Every smoother takes and returns a *wide* DataFrame (a DatetimeIndex of dates,
one column per configuration) so the renderer never has to branch on the mode.
:func:`smooth` is the single entry point used by the charts.

Modes:

* ``rolling7d`` (default): time-based 7-day rolling mean. Gaps stay NaN (no
  forward-fill), no outlier clipping -- spikes and idle periods stay honest.
* ``legacy``: faithful reproduction of plot_wkcm2025's chain
  (24h median -> winsorize 5/95 -> ffill -> centered 7-bin mean). Kept for
  A/B comparison. NB: winsorize here is computed *within the supplied window*
  rather than over the full history (a deliberate improvement over the old
  script, which is left untouched).
* ``raw``: no smoothing, plot values as-is.
"""

import pandas as pd


def winsorize(s, q_low=0.05, q_high=0.95):
    """Clip a series to its own [q_low, q_high] quantiles (NaN-safe)."""
    if s.dropna().empty:
        return s
    lo, hi = s.quantile(q_low), s.quantile(q_high)
    return s.clip(lo, hi)


def _to_wide(df_long, metric):
    """Pivot a long frame (date, configuration, <metric>) to wide (date x config)."""
    wide = df_long.pivot_table(
        index="date", columns="configuration", values=metric, aggfunc="mean"
    )
    return wide.sort_index()


def smooth_rolling7d(wide):
    """Time-based 7-day rolling mean; gaps wider than the window stay NaN."""
    return wide.rolling("7D").mean()


def smooth_legacy(wide):
    """plot_wkcm2025's chain: 24h median -> winsorize -> ffill -> centered 7-mean."""
    resampled = wide.resample("24h").median()
    clipped = resampled.apply(winsorize)
    filled = clipped.ffill()
    return filled.rolling(7, center=True).mean()


def smooth_raw(wide):
    """Identity -- plot the values as-is."""
    return wide


SMOOTHERS = {
    "rolling7d": smooth_rolling7d,
    "legacy": smooth_legacy,
    "raw": smooth_raw,
}

# Human-readable descriptions for chart titles.
SMOOTHING_LABELS = {
    "rolling7d": "rolling 7 day window",
    "legacy": "legacy smoothing",
    "raw": "raw data",
}


def smooth(df_long, metric, mode):
    """Pivot ``df_long`` to wide and apply the named smoothing ``mode``."""
    if mode not in SMOOTHERS:
        raise ValueError(f"Unknown smoothing mode {mode!r}; "
                         f"choose from {sorted(SMOOTHERS)}")
    return SMOOTHERS[mode](_to_wide(df_long, metric))
