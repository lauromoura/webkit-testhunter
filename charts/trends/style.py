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

"""Colors and line styles for the trend charts.

A configuration is named ``<Port>-<Config>`` (e.g. ``WPE-Release``,
``GTK-Debug``). Each *port* gets one color (taken from its Release entry in
``RELEASE_PALETTE``); the Debug variant of a port reuses that same color but is
drawn dashed, so a Release/Debug pair reads as one color with two line styles.

Exception: a configuration that needs its own color (a same-port variant that
would otherwise collide, e.g. ``WPE-ARM64-Release`` sharing WPE's red) can have
an explicit ``RELEASE_PALETTE`` entry, which ``color_for`` matches before the
port-derived lookup.
"""

import matplotlib.pyplot as plt

# Stable per-port colors, keyed by the Release configuration name. Debug
# configurations derive their color from the matching Release entry. Same-port
# variants that need a distinct color get their own exact-name entry.
RELEASE_PALETTE = {
    "Apple-Release": "#1f77b4",
    "GTK-Release": "#2ca02c",
    "WPE-Release": "#d62728",
    "WPE-ARM64-Release": "#9467bd",
}

_FALLBACK_COLOR = "gray"

# Built into matplotlib (>=3.6); avoids a hard seaborn dependency.
_STYLE = "seaborn-v0_8-colorblind"


def port_of(cfg):
    """Return the port part of a configuration name (``WPE-Debug`` -> ``WPE``)."""
    return cfg.split("-", 1)[0]


def is_debug(cfg):
    """Whether a configuration name denotes a Debug build."""
    return cfg.endswith("-Debug")


def color_for(cfg):
    """Color for a configuration.

    An exact entry in ``RELEASE_PALETTE`` wins (used for same-port variants like
    ``WPE-ARM64-Release`` that need their own color). Otherwise the config uses
    its port's Release color, so a Release/Debug pair shares a hue. Unknown
    ports fall back to gray.
    """
    if cfg in RELEASE_PALETTE:
        return RELEASE_PALETTE[cfg]
    release_cfg = f"{port_of(cfg)}-Release"
    return RELEASE_PALETTE.get(release_cfg, _FALLBACK_COLOR)


def variant_label(cfg):
    """Series label for metric-styled (combined) charts: the config without the
    trailing ``-Release`` (``WPE-Release`` -> ``WPE``,
    ``WPE-ARM64-Release`` -> ``WPE-ARM64``, ``GTK-Release`` -> ``GTK``).

    This keeps two same-port Release variants distinct in the legend, where
    ``port_of`` alone would label both just ``WPE``.
    """
    return cfg[: -len("-Release")] if cfg.endswith("-Release") else cfg


def linestyle_for(cfg):
    """Solid for Release, dashed for Debug."""
    return "--" if is_debug(cfg) else "-"


def use_style():
    """Apply the shared matplotlib style. Safe to call repeatedly."""
    plt.style.use(_STYLE)
