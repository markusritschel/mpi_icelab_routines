#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   06/03/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import division, print_function, absolute_import

import pandas
import unittest

from ctds import read_ctd, read_seabird, read_rbr

SBE_TESTFILE = '../examples/sbe37sm-example-data.cnv'
RBR_TESTFILE = '../examples/rbr-example-data.dat'


class TestSeabird(unittest.TestCase):
    def setUp(self):
        self.fixture = read_seabird(SBE_TESTFILE)

    def test_read_seabird_output(self):
        self.assertIsInstance(self.fixture, pandas.DataFrame)
        self.assertEqual(self.fixture.shape[1], 6)
        for var in ['Conductivity', 'Density', 'Potential_Temperature', 'Pressure', 'Salinity_Practical', 'Temperature']:
            self.assertTrue(var in self.fixture.columns)


class TestRBR(unittest.TestCase):
    def setUp(self):
        self.fixture = read_rbr(RBR_TESTFILE)

    def test_read_rbr_output(self):
        self.assertIsInstance(self.fixture, pandas.DataFrame)
        self.assertEqual(self.fixture.shape[1], 5)
        for var in ['Conductivity', 'Density_Anomaly', 'Pressure', 'Salinity', 'Temperature']:
            self.assertTrue(var in self.fixture.columns)


class TestCTD(unittest.TestCase):
    def test_seabird(self):
        data = read_ctd(SBE_TESTFILE)
        self.assertIsInstance(data, pandas.DataFrame)
        self.assertEqual(data.shape[1], 6)

    def test_rbr(self):
        data = read_ctd(RBR_TESTFILE)
        self.assertIsInstance(data, pandas.DataFrame)
        self.assertEqual(data.shape[1], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
