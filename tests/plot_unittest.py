#!/usr/bin/env python3
# coding: utf-8
#
#  Copyright 2022 Igalia S.L.
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

import unittest
import pandas as pd
import os
import inspect

import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from charts.plot import get_date_ticks


class TestDateTicks(unittest.TestCase):
    def test_h1_h1(self):
        start = pd.Timestamp(year=2017, month=2, day=1)
        end = pd.Timestamp(year=2018, month=4, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(get_date_ticks(df), ["2017-1", "2017-7", "2018-1", "2018-7"])

    def test_h1_h2(self):
        start = pd.Timestamp(year=2017, month=2, day=1)
        end = pd.Timestamp(year=2018, month=8, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(
            get_date_ticks(df), ["2017-1", "2017-7", "2018-1", "2018-7", "2019-1"]
        )

    def test_h1_same_year(self):
        start = pd.Timestamp(year=2017, month=2, day=1)
        end = pd.Timestamp(year=2017, month=5, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(get_date_ticks(df), ["2017-1", "2017-7"])

    def test_h2_same_year(self):
        start = pd.Timestamp(year=2017, month=8, day=1)
        end = pd.Timestamp(year=2017, month=10, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(get_date_ticks(df), ["2017-7", "2018-1"])

    def test_boundary_h1(self):
        start = pd.Timestamp(year=2017, month=1, day=1)
        end = pd.Timestamp(year=2017, month=7, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(get_date_ticks(df), ["2017-1", "2017-7", "2018-1"])

    def test_boundary_h2(self):
        start = pd.Timestamp(year=2017, month=7, day=1)
        end = pd.Timestamp(year=2017, month=12, day=1)
        df = pd.DataFrame(index=(start, end), data={"col_a": (1, 2)})

        self.assertEqual(get_date_ticks(df), ["2017-7", "2018-1"])


if __name__ == "__main__":
    unittest.main()
