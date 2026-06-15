#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Consolidate json test run stats into a single csv file"""

import argparse
import multiprocessing
from functools import partial
from collections import OrderedDict
import json
import csv
import os
import sys
import pandas as pd


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-o", "--output", type=str, default="out.csv", help="Output file"
    )
    parser.add_argument(
        "filenames", type=str, nargs="+", help="Files or directory to process"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print progress information"
    )
    parser.add_argument(
        "-f",
        "--full-parse",
        action="store_true",
        help="Parse the entire json file, without trying to skip the tests",
    )
    parser.add_argument(
        "-c",
        "--extra-column",
        action="append",
        default = [],
        help="Extra key=value constant value to be added as a new column in the exported data"
    )

    parser.add_argument(
        "-d",
        "--delete-column",
        action="append",
        default = [],
        help="Delete the given columns from the parsed data, if present"
    )

    return parser.parse_args()

def collect_unexpected_results(data, unexpected_results_acc):
    """Process the tests data, counting unexpected results"""
    for entry_name, entry in data.items():
        # Process subfolders, if any
        if "expected" not in entry and "actual" not in entry:
            collect_unexpected_results(entry, unexpected_results_acc)
            continue

        expected = entry["expected"]
        actual = entry["actual"]

        if actual not in expected:
            if entry.get("report", "") == "FLAKY":
                actual = "FLAKY"
            elif entry.get("report", "") == "REGRESSION":
                actual = actual.split()[0]  # 'TEXT IMAGE+TEXT'
            elif ("FAIL" in expected) and (actual in ("TEXT", "IMAGE")):
                continue
            try:
                unexpected_results_acc[actual] += 1
            except KeyError:
                print(f"Unexpected result: {actual} in {entry_name}")
                sys.exit(1)


def collect_jsons(sources):
    """Collect all json files in a directory"""
    for source in sources:
        if os.path.isdir(source):
            for root, _, files in os.walk(source):
                for filename in sorted(files):
                    if filename.endswith("json"):
                        yield os.path.join(root, filename)
        else:
            yield source


def parse_single_file(filename, full_parse):
    """Parse a single json file

    The json files are wrapped in "ADD_RESULTS[<json payload>]", thus we
    can't use json.load directly.

    If full_parse is false, it'll try to skip the huge "tests" field with
    the individual results, jumping straight to the test run totals. This
    has the side effect of not being able to count unexpected results
    details.
    """
    # print(f"parsing {filename}")

    with open(filename, encoding="utf-8") as handle:
        raw_data = handle.read()[len("ADD_RESULTS[") : -len("];")]
        # We have 2 versions of results files:
        # - Version 3: Starts directly with "tests" key
        # - Version 4: Added 'other_crashes' field, used by integration and
        #   moves a few keys before the big "tests" one.
        test_start = raw_data.find('"tests"')
        prologue = raw_data[:test_start]

        if not full_parse:
            if 'version":4' in prologue:
                epilogue_idx = raw_data.find('"num_passes"')
            else:
                epilogue_idx = raw_data.find('"skipped"')
            raw_data = prologue + raw_data[epilogue_idx:]
        try:
            data = json.loads(raw_data)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            raise
        if "date" in data:
            # FIXME Looks like date in results_full.json is in PDT (bot time)
            parsed = pd.to_datetime(data['date'])
            data['date'] = parsed

        if "tests" in data:
            # Nested dictionaries for each folder
            unexpected_results_acc = {
                "IMAGE": 0,
                "FLAKY": 0,
                "PASS": 0,
                "CRASH": 0,
                "TIMEOUT": 0,
                "TEXT": 0,
                "MISSING": 0,
            }
            all_tests = data["tests"]
            collect_unexpected_results(all_tests, unexpected_results_acc)
            for (
                unexpected_outcome,
                unexpected_count,
            ) in unexpected_results_acc.items():
                data[f"unexpected_{unexpected_outcome}"] = unexpected_count
            del data["tests"]
        return data


def parse_data(sources, full_parse):
    """Parses all json files in the given sources, returning a generator of parsed data

    If full_parse is false, it'll try to skip the huge "tests" field, jumping
    straight to the test run totals.

    If a `sources` element is a directory, it'll recursively search for json files.
    """
    with multiprocessing.Pool(os.cpu_count() // 2) as pool:
        parse_func = partial(parse_single_file, full_parse=full_parse)
        yield from pool.map(parse_func, collect_jsons(sources))


def main():
    """Main script function"""
    args = parse_args()

    with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
        files = list(parse_data(args.filenames, args.full_parse))

        fieldnames_set = set()

        for row in files:
            fieldnames_set |= row.keys()
        fieldnames_set.add("date")

        extra_cols = {}

        if args.extra_column:
            for extra_col in args.extra_column:
                extra_key, extra_value = extra_col.split("=")
                assert not extra_key in fieldnames_set
                fieldnames_set.add(extra_key)
                extra_cols[extra_key] = extra_value

        for col_to_remove in args.delete_column:
            fieldnames_set.discard(col_to_remove)
            extra_cols.pop(col_to_remove, None)

        writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames_set))

        writer.writeheader()
        # if "date" in first:
        #     for extra_col, extra_value in extra_cols.items():
        #         first[extra_col] = extra_value

        #     for col_to_remove in args.delete_column:
        #         first.pop(col_to_remove, None)

        #     writer.writerow(first)

        for entry in files:
            if "date" not in entry:
                print(f"Skipping entry {entry['revision']} as it's missing date")
                continue

            for col_to_remove in args.delete_column:
                entry.pop(col_to_remove, None)

            entry_keys = set(entry.keys())

            not_present_keys = entry_keys - fieldnames_set
            for key in not_present_keys:
                if args.verbose:
                    print(
                        f"Ignoring key {key} with value {entry[key]} from current revision"
                    )
                del entry[key]
            missing_keys = fieldnames_set - entry_keys
            for key in missing_keys:
                if args.verbose:
                    print(f"Adding placeholder 0 to key {key} for current revision")
                entry[key] = 0
            for extra_col, extra_value in extra_cols.items():
                entry[extra_col] = extra_value
            if args.verbose:
                print("Saving revision", entry["revision"])
            writer.writerow(entry)


if __name__ == "__main__":
    main()
