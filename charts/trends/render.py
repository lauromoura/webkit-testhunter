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

"""The single shared rendering primitive.

All matplotlib boilerplate (figure setup, smoothing call, styling, threshold
lines, axis formatting, saving) lives here. Per-chart functions in
:mod:`trends.charts` are thin wrappers that build a :class:`ChartSpec` and
delegate to :func:`render_chart`.
"""

import os
import sys
from dataclasses import dataclass, field

import matplotlib.pyplot as plt

from .smoothing import SMOOTHING_LABELS, smooth
from .style import color_for, linestyle_for, use_style, variant_label

# Line styles cycled by metric index when style_by="metric".
_METRIC_LINESTYLES = ["-", "--", ":", "-."]


@dataclass
class ChartSpec:
    """Declarative description of a chart (consumed by :func:`render_chart`)."""

    key: str                       # filename stem
    metrics: list                  # one or more column names to plot
    title: str
    ylabel: str
    kind: str = "trend"            # "trend" | "spike" | "ratio"
    threshold: float | None = None
    threshold_color: str = "red"
    style_by: str = "config"       # "config": color=config; "metric": solid/dashed per metric
    release_only: bool = False     # drop Debug configs (used by combined charts)
    metric_labels: dict = field(default_factory=dict)


def _select_configs(df_window, spec):
    """Configurations present in the window, optionally Release-only, sorted."""
    configs = sorted(df_window["configuration"].unique())
    if spec.release_only:
        configs = [c for c in configs if not c.endswith("-Debug")]
    return configs


def _line_label(spec, cfg, metric):
    """Legend label for one series."""
    if spec.style_by == "metric":
        return f"{variant_label(cfg)} {spec.metric_labels.get(metric, metric)}"
    return cfg


def _line_style(spec, cfg, metric_index):
    """(color, linestyle) for one series given the spec's styling mode."""
    if spec.style_by == "metric":
        ls = _METRIC_LINESTYLES[metric_index % len(_METRIC_LINESTYLES)]
        return color_for(cfg), ls
    return color_for(cfg), linestyle_for(cfg)


def _save(fig, spec, window, smoothing, directory):
    fname = f"{spec.key}-{window.slug()}-{smoothing}.png"
    path = os.path.join(directory, fname)
    fig.savefig(path, transparent=True, bbox_inches="tight")
    plt.close(fig)
    return path


def render_chart(df_window, spec, *, window, smoothing, directory,
                 include_raw=False, precomputed=None):
    """Render one chart to a PNG and return its path (or None if nothing to plot).

    ``df_window`` is the already-windowed long frame. For ``kind == "ratio"`` the
    caller supplies a ``precomputed`` wide frame (date x config) and smoothing is
    bypassed; otherwise each metric is pivoted+smoothed via :func:`smooth`.
    """
    use_style()
    fig, ax = plt.subplots(figsize=(10, 5))

    plotted_any = False

    if spec.kind == "ratio":
        wide = precomputed
        for cfg in wide.columns:
            series = wide[cfg]
            if series.notna().any():
                series.plot(ax=ax, color=color_for(cfg),
                            linestyle=linestyle_for(cfg), label=cfg, linewidth=1.6)
                plotted_any = True
    else:
        configs = _select_configs(df_window, spec)
        sub = df_window[df_window["configuration"].isin(configs)]
        for i, metric in enumerate(spec.metrics):
            long = sub[["date", "configuration", metric]]
            wide = smooth(long, metric, smoothing)
            raw = smooth(long, metric, "raw") if include_raw else None
            for cfg in wide.columns:
                color, ls = _line_style(spec, cfg, i)
                if include_raw and cfg in raw.columns and raw[cfg].notna().any():
                    raw[cfg].plot(ax=ax, color=color, alpha=0.3, linewidth=1.0,
                                  label="_nolegend_")
                series = wide[cfg]
                if series.notna().any():
                    series.plot(ax=ax, color=color, linestyle=ls,
                                label=_line_label(spec, cfg, metric), linewidth=1.6)
                    plotted_any = True

    if not plotted_any:
        plt.close(fig)
        print(f"Warning: no data for chart '{spec.key}' in window "
              f"'{window.name}'; skipping", file=sys.stderr)
        return None

    if spec.threshold is not None:
        ax.axhline(spec.threshold, color=spec.threshold_color, linestyle="dotted")

    # e.g. "Passing tests (last 12 months, rolling 7 day window)". The ratio
    # chart's smoothing is fixed (and noted in its own title), so it only shows
    # the window to avoid an inaccurate smoothing label.
    if spec.kind == "ratio":
        suffix = window.display
    else:
        suffix = f"{window.display}, {SMOOTHING_LABELS.get(smoothing, smoothing)}"
    ax.set_title(f"{spec.title} ({suffix})")
    ax.set_xlabel("Date")
    ax.set_ylabel(spec.ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend(title="Configuration")
    if window.start is not None or window.end is not None:
        ax.set_xlim(window.start, window.end)

    return _save(fig, spec, window, smoothing, directory)
