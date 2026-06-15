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

"""Reusable building blocks for the WebKit test-results trend charts.

The same functions back both the ``plot_trends.py`` CLI and interactive
notebooks, e.g.::

    from trends import load_configs, slice_window, smooth, Window
    df = load_configs()
    win = Window("2025", "2025-01-01", "2025-12-31")
    wide = smooth(slice_window(df, win)[["date", "configuration", "num_passes"]],
                  "num_passes", "rolling7d")
    wide.plot()
"""

from .charts import CHARTS, NEEDS_INTERRUPTED, interrupted_ratio_wide
from .data import (
    STANDARD_CSVS,
    add_derived_metrics,
    apply_interrupted_policy,
    interrupted_bool,
    load_configs,
    read_csv,
)
from .render import ChartSpec, render_chart
from .smoothing import smooth, winsorize
from .style import RELEASE_PALETTE, color_for, linestyle_for
from .windows import Window, resolve_windows, slice_window

__all__ = [
    "CHARTS",
    "NEEDS_INTERRUPTED",
    "interrupted_ratio_wide",
    "STANDARD_CSVS",
    "add_derived_metrics",
    "apply_interrupted_policy",
    "interrupted_bool",
    "load_configs",
    "read_csv",
    "ChartSpec",
    "render_chart",
    "smooth",
    "winsorize",
    "RELEASE_PALETTE",
    "color_for",
    "linestyle_for",
    "Window",
    "resolve_windows",
    "slice_window",
]
