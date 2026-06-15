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

"""Generate long-term test-results trend charts from report.py CSVs.

Thin CLI over the :mod:`trends` package. Examples::

    ./plot_trends.py --year 2025
    ./plot_trends.py --last 12m --smoothing legacy
    ./plot_trends.py --windows 2024,2025,2024-25,2022-25
    ./plot_trends.py WPE-Release.csv GTK-Release.csv --charts passing,errors
"""

import argparse
import os
import sys

import pandas as pd

from trends import (
    CHARTS,
    NEEDS_INTERRUPTED,
    apply_interrupted_policy,
    load_configs,
    resolve_windows,
    slice_window,
)


def parse_date(value):
    """argparse type: a YYYY-MM-DD string -> pandas Timestamp."""
    try:
        return pd.Timestamp(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}: {exc}") from exc


def split_list(value):
    """Comma-separated string -> list of non-empty trimmed items (None -> None)."""
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "csvs", nargs="*",
        help="Per-config CSV paths. Default: the standard bot CSVs "
             "(WPE/GTK Release+Debug and WPE-ARM64-Release).")

    group = parser.add_argument_group("time range (union of all given; none -> all-time)")
    group.add_argument("--since", type=parse_date, help="Start date YYYY-MM-DD")
    group.add_argument("--until", type=parse_date, help="End date YYYY-MM-DD")
    group.add_argument("--year", type=int, help="A single calendar year, e.g. 2025")
    group.add_argument("--last", help="Trailing window, e.g. 90d, 12m, 2y")
    group.add_argument("--windows",
                       help="Comma list, e.g. 2024,2025,2024-25,2022-25")

    parser.add_argument("--smoothing", choices=["rolling7d", "legacy", "raw"],
                        default="rolling7d",
                        help="Smoothing strategy (default: rolling7d)")
    parser.add_argument("--charts",
                        help=f"Comma list of chart keys (default: all). "
                             f"Available: {', '.join(CHARTS)}")
    parser.add_argument("--include-interrupted", action="store_true",
                        help="Keep interrupted runs (default: exclude them)")
    parser.add_argument("--include-raw", action="store_true",
                        help="Overlay faint raw points behind the smoothed line")
    parser.add_argument("-d", "--directory", default=os.getcwd(),
                        help="Output directory (default: cwd; *.png are gitignored)")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    chart_keys = split_list(args.charts) or list(CHARTS)
    unknown = [k for k in chart_keys if k not in CHARTS]
    if unknown:
        print(f"Unknown chart key(s): {', '.join(unknown)}. "
              f"Available: {', '.join(CHARTS)}", file=sys.stderr)
        return 2

    df = load_configs(args.csvs or None)
    today = pd.Timestamp.today().normalize()
    windows = resolve_windows(
        windows=split_list(args.windows), year=args.year, last=args.last,
        since=args.since, until=args.until, today=today)

    os.makedirs(args.directory, exist_ok=True)

    for window in windows:
        wdf_full = slice_window(df, window)
        wdf = apply_interrupted_policy(wdf_full, args.include_interrupted)
        for key in chart_keys:
            data = wdf_full if key in NEEDS_INTERRUPTED else wdf
            path = CHARTS[key](
                data, window=window, smoothing=args.smoothing,
                directory=args.directory, include_raw=args.include_raw)
            if path:
                print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
