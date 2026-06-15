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

"""The catalogue of charts.

Each chart is a thin wrapper that builds a :class:`~trends.render.ChartSpec`
and delegates to :func:`~trends.render.render_chart`. Adding a single-metric
chart is one wrapper plus one :data:`CHARTS` entry.

Most charts overlay one metric across all configurations. The two combined
charts (``regr-flaky`` and ``regr-flaky-pct``) plot *two* metrics, so they fall
back to Release-only overlays where color encodes the port and the line style
(solid/dashed) encodes the metric -- otherwise there'd be no free visual channel
to tell the two metrics apart from the Debug-dashed configs.
"""

import pandas as pd

from .data import interrupted_bool
from .render import ChartSpec, render_chart

# ---------------------------------------------------------------------------
# Single-metric charts: one metric, all configurations overlaid.
# ---------------------------------------------------------------------------


def chart_passing(df, **kw):
    return render_chart(df, ChartSpec(
        "passing", ["num_passes"], "Passing tests", "Number of tests"), **kw)


def chart_skipped(df, **kw):
    return render_chart(df, ChartSpec(
        "skipped", ["skipped"], "Skipped tests", "Number of tests"), **kw)


def chart_fixable(df, **kw):
    return render_chart(df, ChartSpec(
        "fixable", ["fixable"], "Known failures (fixable)", "Number of tests"), **kw)


def chart_errors(df, **kw):
    return render_chart(df, ChartSpec(
        "errors", ["unexpected_ERROR"], "Unexpected crashes + timeouts",
        "Number of tests", kind="spike", threshold=50), **kw)


def chart_crash(df, **kw):
    return render_chart(df, ChartSpec(
        "crash", ["unexpected_CRASH"], "Unexpected crashes", "Number of tests",
        kind="spike"), **kw)


def chart_timeout(df, **kw):
    return render_chart(df, ChartSpec(
        "timeout", ["unexpected_TIMEOUT"], "Unexpected timeouts", "Number of tests",
        kind="spike"), **kw)


def chart_failures(df, **kw):
    return render_chart(df, ChartSpec(
        "failures", ["unexpected_FAIL"], "Unexpected image + text failures",
        "Number of tests"), **kw)


def chart_text(df, **kw):
    return render_chart(df, ChartSpec(
        "text", ["unexpected_TEXT"], "Unexpected text failures", "Number of tests"), **kw)


def chart_image(df, **kw):
    return render_chart(df, ChartSpec(
        "image", ["unexpected_IMAGE"], "Unexpected image failures", "Number of tests"), **kw)


# ---------------------------------------------------------------------------
# Combined two-metric charts: Release-only; metric -> line style.
# ---------------------------------------------------------------------------


def chart_regr_flaky(df, **kw):
    return render_chart(df, ChartSpec(
        "regr-flaky", ["num_regressions", "num_flaky"],
        "Regressions and flakies", "Number of tests",
        style_by="metric", release_only=True,
        metric_labels={"num_regressions": "regressions", "num_flaky": "flaky"}), **kw)


def chart_regr_flaky_pct(df, **kw):
    return render_chart(df, ChartSpec(
        "regr-flaky-pct", ["pct_regressions", "pct_flaky"],
        "Regressions and flakies (% of run)", "% of tests run",
        style_by="metric", release_only=True,
        metric_labels={"pct_regressions": "regressions", "pct_flaky": "flaky"}), **kw)


# ---------------------------------------------------------------------------
# Interrupted-runs ratio: a per-day count ratio, not a smoothed metric column.
# ---------------------------------------------------------------------------


def interrupted_ratio_wide(df, freq="D", window="7D"):
    """Wide (date x config) fraction of runs that were interrupted.

    Per config: count total runs and interrupted runs per ``freq`` bin, take a
    rolling sum over ``window``, and divide. NaN where the window has no runs.
    Reproduces plot_wkcm2025's daily_run_count / daily_frac_sm. Expects ``df``
    to still contain interrupted rows.
    """
    total_by_cfg = {}
    interrupted_by_cfg = {}
    for cfg, g in df.groupby("configuration", sort=False):
        gi = g.sort_values("date").assign(_interrupted=interrupted_bool(g))
        gi = gi.set_index("date")
        total_by_cfg[cfg] = gi.resample(freq).size()
        interrupted_by_cfg[cfg] = gi["_interrupted"].resample(freq).sum()

    daily_total = pd.DataFrame(total_by_cfg)
    daily_interrupted = pd.DataFrame(interrupted_by_cfg)

    num = daily_interrupted.rolling(window, min_periods=1).sum()
    den = daily_total.rolling(window, min_periods=1).sum()
    return (num / den).where(den > 0)


def chart_interrupted_ratio(df, *, window, smoothing, directory, include_raw=False):
    wide = interrupted_ratio_wide(df)
    spec = ChartSpec(
        "interrupted-ratio", [], "Ratio of interrupted runs (7-day)", "Ratio",
        kind="ratio")
    return render_chart(df, spec, window=window, smoothing=smoothing,
                        directory=directory, precomputed=wide)


# ---------------------------------------------------------------------------
# Registry. interrupted-ratio needs the pre-interrupted-drop frame (see CLI).
# ---------------------------------------------------------------------------

CHARTS = {
    "passing": chart_passing,
    "skipped": chart_skipped,
    "fixable": chart_fixable,
    "errors": chart_errors,
    "crash": chart_crash,
    "timeout": chart_timeout,
    "failures": chart_failures,
    "text": chart_text,
    "image": chart_image,
    "regr-flaky": chart_regr_flaky,
    "regr-flaky-pct": chart_regr_flaky_pct,
    "interrupted-ratio": chart_interrupted_ratio,
}

# Charts that must receive the frame *before* interrupted rows are dropped.
NEEDS_INTERRUPTED = frozenset({"interrupted-ratio"})
