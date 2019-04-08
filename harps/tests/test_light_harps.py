#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   22/03/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import division, print_function, absolute_import
import unittest

from harps.light_harps import read_harp_file

TESTFILE = '../examples/light_harps_test_data.txt'


class TestReadFile(unittest.TestCase):
    def setUp(self):
        self.fixture = read_harp_file(file=TESTFILE)

    def tearDown(self):
        del self.fixture

    def test_format(self):
        print(self.fixture)


if __name__ == '__main__':
    unittest.main(verbosity=2)
