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

import json
import argparse
import csv
import os


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

    return parser.parse_args()


def parse_files(files, verbose, full_parse):
    """Generator to parse each file individually

    If full_parse is false, it'll try to skip the huge "tests" field, jumping
    straight to the test run totals.
    """

    try:
        directory = files[0]
        entries = os.listdir(directory)
        files = map(lambda entry: os.path.join(directory, entry), entries)
    except (TypeError, IndexError, NotADirectoryError) as exception:
        if verbose:
            print("Silently ignoring the following exception:")
            print(exception)

    for filename in files:
        if not filename.endswith("json"):
            continue
        if verbose:
            print("Reading", filename)
        with open(filename, encoding="utf-8") as handle:
            # The json files are wrapped in "ADD_RESULTS[<json payload>]"
            raw_data = handle.read()[len("ADD_RESULTS[") : -len("];")]
            # We have 2 versions of results files:
            # - Version 3: Starts directly with "tests" key
            # - Version 4: Added 'other_crashes' field, used by integration and
            #   moves a few keys before the big "tests" one.
            test_start = raw_data.find("\"tests\"")
            prologue = raw_data[:test_start]
            if not full_parse:
                if "version\":4" in prologue:
                    epilogue_idx = raw_data.find('"num_passes"')
                else:
                    epilogue_idx = raw_data.find('"skipped"')
                raw_data = prologue + raw_data[epilogue_idx:]
            data = json.loads(raw_data)
            if "tests" in data:
                del data["tests"]
            yield data


def main():
    """Main script function"""
    args = parse_args()

    with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
        files = parse_files(args.filenames, args.verbose, args.full_parse)

        try:
            first = next(files)
        except StopIteration:
            if args.verbose:
                print("No entries found.")
            return

        fieldnames_set = set(first.keys())
        fieldnames_set.add('date')

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames_set)


        writer.writeheader()
        if 'date' in first:
            writer.writerow(first)

        for entry in files:
            if 'date' not in entry:
                print(f"Skipping entry {entry['revision']} as it's missing date")
                continue

            entry_keys = set(entry.keys())

            not_present_keys = entry_keys - fieldnames_set
            for key in not_present_keys:
                if args.verbose:
                    print(f"Ignoring key {key} with value {entry[key]} from current revision")
                del entry[key]
            missing_keys = fieldnames_set - entry_keys
            for key in missing_keys:
                if args.verbose:
                    print(f"Adding placeholder 0 to key {key} for current revision")
                entry[key] = 0
            if args.verbose:
                print("Saving revision", entry["revision"])
            writer.writerow(entry)


if __name__ == "__main__":
    main()
