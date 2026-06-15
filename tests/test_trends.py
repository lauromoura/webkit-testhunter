#!/usr/bin/env python3
# coding: utf-8
"""Unit tests for the pure helpers of the trends charting package."""

import os
import sys

import pandas as pd

# Make the charts/ dir importable so `import trends` works.
_CHARTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "charts")
sys.path.insert(0, _CHARTS)

from trends import add_derived_metrics, resolve_windows, smooth  # noqa: E402
from trends.style import color_for, variant_label  # noqa: E402
from trends.windows import Window, parse_window_token  # noqa: E402


# --- windows -------------------------------------------------------------

def test_parse_window_token_single_year():
    w = parse_window_token("2025")
    assert w.start == pd.Timestamp("2025-01-01")
    assert w.end == pd.Timestamp("2025-12-31 23:59:59")


def test_parse_window_token_year_span_two_digit_end():
    w = parse_window_token("2024-25")
    assert w.start == pd.Timestamp("2024-01-01")
    assert w.end == pd.Timestamp("2025-12-31 23:59:59")
    assert w.display == "2024-2025"


def test_resolve_windows_year_and_last():
    today = pd.Timestamp("2026-06-14")
    (wy,) = resolve_windows(year=2025, today=today)
    assert wy.name == "2025"

    (wl,) = resolve_windows(last="12m", today=today)
    assert wl.name == "last-12m"
    assert wl.display == "last 12 months"
    assert wl.end == today


def test_window_display_falls_back_to_name():
    assert Window("all", None, None, label="all time").display == "all time"
    assert Window("2025", None, None).display == "2025"


def test_resolve_windows_default_is_open_all():
    (w,) = resolve_windows(today=pd.Timestamp("2026-06-14"))
    assert w.name == "all" and w.start is None and w.end is None


# --- data: derived metrics ----------------------------------------------

def _row(**kw):
    base = dict(
        date=pd.Timestamp("2025-01-01"), configuration="WPE-Release",
        unexpected_CRASH=0, unexpected_TIMEOUT=0, unexpected_IMAGE=0,
        unexpected_TEXT=0, fixable=0, skipped=0, num_passes=0, num_flaky=0,
        num_regressions=0,
    )
    base.update(kw)
    return base


def test_add_derived_metrics():
    df = pd.DataFrame([_row(
        unexpected_CRASH=3, unexpected_TIMEOUT=4, unexpected_IMAGE=5,
        unexpected_TEXT=6, fixable=100, skipped=30, num_passes=90,
        num_flaky=5, num_regressions=5,
    )])
    out = add_derived_metrics(df).iloc[0]
    assert out["unexpected_ERROR"] == 7        # 3 + 4
    assert out["unexpected_FAIL"] == 11        # 5 + 6
    assert out["fixable"] == 70                 # 100 - 30
    assert out["num_run"] == 100               # 90 + 5 + 5
    assert out["pct_regressions"] == 5.0       # 5 / 100 * 100
    assert out["pct_flaky"] == 5.0


def test_pct_is_nan_when_no_runs():
    df = pd.DataFrame([_row(num_passes=0, num_flaky=0, num_regressions=0)])
    out = add_derived_metrics(df).iloc[0]
    assert pd.isna(out["pct_regressions"])


# --- smoothing: raw is identity -----------------------------------------

def test_smooth_raw_is_identity():
    long = pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
        "configuration": ["WPE-Release"] * 3,
        "num_passes": [10.0, 20.0, 30.0],
    })
    wide = smooth(long, "num_passes", "raw")
    assert list(wide.columns) == ["WPE-Release"]
    assert list(wide["WPE-Release"]) == [10.0, 20.0, 30.0]


# --- style ---------------------------------------------------------------

def test_color_for_exact_match_and_port_fallback():
    assert color_for("WPE-ARM64-Release") == "#9467bd"   # exact entry wins
    assert color_for("WPE-Release") == "#d62728"
    assert color_for("WPE-Debug") == color_for("WPE-Release")  # debug shares port hue


def test_variant_label_strips_release_suffix():
    assert variant_label("WPE-Release") == "WPE"
    assert variant_label("WPE-ARM64-Release") == "WPE-ARM64"
    assert variant_label("GTK-Release") == "GTK"
