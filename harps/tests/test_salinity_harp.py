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
import unittest

import numpy
import xarray

from harps.salinity_harps import read_harp_file, calc_reference_resistance, read_harp_data, calc_brine_salinity

TESTFILE = '../examples/test_data.dat'


class TestReadFile(unittest.TestCase):
    def setUp(self):
        self.fixture = read_harp_file(file=TESTFILE)

    def tearDown(self):
        del self.fixture

    def test_instance(self):
        self.assertIsInstance(self.fixture, xarray.Dataset)

    def test_time_coordinate(self):
        self.assertIsInstance(self.fixture.coords['time'], xarray.DataArray)
        self.assertEqual(self.fixture.coords['time'].dtype, "datetime64[ns]")


class TestReadData(unittest.TestCase):
    def setUp(self):
        self.fixture = read_harp_data(file=TESTFILE, module=0)

    def tearDown(self):
        del self.fixture

    def test_calc_reference_R(self):
        for method in ['median', 'butterworth', 'savgol']:
            r0s = calc_reference_resistance(self.fixture, 'r10', kind=method, tolerance=(1e-4, 5e-4))
            self.assertIsInstance(r0s, xarray.DataArray)
            self.assertEqual(len(r0s.values), len(self.fixture.coords['wire_pair']))

    def test_calc_brine_Salinity(self):
        T = numpy.random.random(10)
        S_brine = calc_brine_salinity(T, method='Assur')
        self.assertIsInstance(S_brine, numpy.ndarray)
        self.assertEqual(len(T), len(S_brine))

    def test_data_format(self):
        self.assertIsInstance(self.fixture, xarray.Dataset)

    def test_variables(self):
        for var in ['brine salinity', 'solid fraction', 'liquid fraction', 'bulk salinity']:
            self.assertTrue(var in self.fixture.data_vars)


if __name__ == '__main__':
    unittest.main(verbosity=2)
