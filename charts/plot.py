#!/usr/bin/env python3
# coding: utf-8
#
#  Copyright 2020 Igalia S.L.
#  Lauro Moura <lmoura@igalia.com>
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

"""Plot Layout tests results over time"""

import os
import sys
import argparse
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator
from pandas.plotting import register_matplotlib_converters

SMALL_SIZE = 12
MEDIUM_SIZE = 16
BIGGER_SIZE = 8

plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title


register_matplotlib_converters()

def parse_date(date_str):
    """Helper to get a date object from a YYYY-MM-DD string"""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")

def parse_args():
    """Parse command line args"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        default="Unknown",
        choices=("GTK", "WPE"),
        help="Name of the port being processed",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="Unknown",
        choices=("Release", "Debug"),
        help="Configuration of the port being processed",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=os.getcwd(),
        help="Output directory. Defaults to the current one",
    )

    parser.add_argument(
        "--since",
        default="2023-01-01",
        type=parse_date,
        help="Start date to generate the report, as YYYY-MM-DD")

    parser.add_argument("filename", help="File to be processed.")

    args = parser.parse_args()
    filename = args.filename.lower()

    if args.port == "Unknown" and args.config == "Unknown":
        try:
            basename, _ = os.path.splitext(filename)
            port, config = basename.split("-")
            args.port = port.upper()
            args.config = config.capitalize()
            print(
                "Guessed port '%s' and configuration '%s' from filename"
                % (args.port, args.config)
            )
        except ValueError:  # No '-' in the name, for example
            print("Could not guess port and config")

    return args


def port_str(port, config):
    """Standard identifier for a port/config pair"""
    return "%s-%s" % (port, config)


MONTHS = (1, 4, 7, 10)

def get_date_ticks(data):
    """Gets a list of ticks covering the data from the given dataframe.

    It assumes the date is stored as the dataframe index."""
    current_year = datetime.date.today().year

    max_date = data.index.max()
    min_date = data.index.min()

    print(f"Min date: {min_date}")
    print(f"Max date: {max_date}")

    starting_year = min_date.year
    end_year = max_date.year if max_date.month < 10 else max_date.year + 1

    starting_month = min_date.month
    end_month = max_date.month if max_date.month < 10 else 1
    print(f"Starting block: {starting_year}-{starting_month}")
    print(f"Ending year: {end_year}-{end_month}")

    acc = []
    for year in range(starting_year, end_year+1):
        for month in MONTHS:
            # In the first year we don't need H1...
            if year == starting_year:
                # ..if we started logging in H2
                if starting_month >= 7 and month == 1:
                    continue
            # In the last year we don't need H2
            elif year == end_year:
                # if we ended logging in H1
                if end_month >= 7 and month == 7:
                    break
            acc.append(f"{year}-{month}")

    return acc

def generate_quarterly_ticks(df):
    # Get the minimum and maximum dates from the 'date' column
    start_date = df.index.min()
    end_date = df.index.max()

    # Get the quarter of the start date
    start_quarter = start_date - pd.DateOffset(days=start_date.day - 1) - pd.DateOffset(months=(start_date.month-1)%3)
    end_quarter = end_date + pd.DateOffset(days=end_date.day + 1) + pd.DateOffset(months=(end_date.month-1)%3)
    end_quarter = end_quarter.replace(day=1)

    # Generate quarterly ticks from the quarter immediately before the start date
    quarterly_ticks = pd.date_range(start=start_quarter, end=end_quarter, freq='QS').tolist()

    print(quarterly_ticks)

    return quarterly_ticks

def read_df(filename, since):
    """Read the initial data for the given port and config"""
    df = pd.read_csv(filename, parse_dates=["date"])
    df = df[df["date"] > since]
    df.set_index("date", inplace=True)
    return df


def main():
    """Main script routine"""

    args = parse_args()

    df = read_df(args.filename, since=args.since)

    if not os.path.exists(args.directory):
        os.makedirs(args.directory)
    elif not os.path.isdir(args.directory):
        print("Output directory is not a directory", file=sys.stderr)
        sys.exit(1)

    df["fixable"] = df["fixable"] - df["skipped"]

    plot_expected(df, args.port, args.config, args.directory)
    plot_unexpected(df, args.port, args.config, args.directory)


def plot_unexpected(df, port, config, directory):
    """Plot the unexpected results

    The unexpected results are grouped in regressions (failures, timeouts,
    crashes) not yet gardened, and in Flakies (tests that fails on the first run
    and passes on a retry).
    """
    # This fig size generates an image with height of 767 pixels
    # The width varies due to the ax.lengends call below to move the
    # legend bots to outside the chart
    fig, ax = plt.subplots(facecolor="white", figsize=(5, 5), dpi=160)
    df[["num_regressions", "num_flaky"]].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Regressions and flakies" % port_str(port, config))
    plt.xlabel("Date")
    plt.ylabel("Number of tests")
    # FIXME Parametrize these ticks
    # ax.set_xticks(generate_quarterly_ticks(df))
    locator = MonthLocator(bymonthday=1, interval=1)
    ax.xaxis.set_major_locator(locator)
    ax.legend(["Regressions", "Flakies"], loc="center right", bbox_to_anchor=(1.5, 0.5))
    ax.grid(True, linestyle="-.")
    fig = ax.get_figure()
    fig.savefig(
        os.path.join(directory, ("%s-unexpected-regr-flaky.png" % port_str(port, config))),
        transparent=True,
        bbox_inches="tight",
    )


def plot_expected(df, port, config, directory):
    """Plot the expected results

    The expected results are grouped in passes, skips and known failures. The last
    are crashes, flakies, timeouts and failures already gardened.
    """
    fig, ax = plt.subplots(facecolor="white", figsize=(5, 5), dpi=160)
    # df[["fixable", "skipped", "num_passes"]].rolling(50).mean().plot(ax=ax)
    df[["fixable", "skipped"]].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Expected skips and known failures" % port_str(port, config))
    plt.xlabel("Date")
    plt.ylabel("Number of tests")
    # FIXME Parametrize these ticks
    locator = MonthLocator(bymonthday=1, interval=1)
    ax.xaxis.set_major_locator(locator)
    ax.legend(
        ["Fixable", "Skipped"], loc="center right", bbox_to_anchor=(1.5, 0.5)
    )
    ax.grid(True, linestyle="-.")
    fig = ax.get_figure()
    fig.savefig(
        os.path.join(directory, ("%s-expected-results.png" % port_str(port, config))),
        transparent=True,
        bbox_inches="tight",
    )


if __name__ == "__main__":
    main()
