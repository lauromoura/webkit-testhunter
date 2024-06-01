#!/usr/bin/env python3
# coding: utf-8
#
#  Copyright 2023 Igalia S.L.
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

"""Inspect values from the generate report"""

import argparse

import pandas as pd

def parse_args():
    """Parse command line args"""
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="File to be processed.")

    args = parser.parse_args()
    return args

def main():

    args = parse_args()

    df = pd.read_csv(args.filename, parse_dates=["date"])
    df.set_index("date", inplace=True)

    print(df)

    print(df.index.is_monotonic)

    break_index = df.index[df.index.to_series().diff().fillna(pd.Timedelta(seconds=1)).dt.total_seconds() < 0].min()

    print(break_index)

if __name__ == "__main__":
    main()

