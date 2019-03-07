#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   07/03/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import division, print_function, absolute_import

import numpy as np
import pandas as pd
import re


def read_seabird(file, nan_flag=-9.990e-29, **kwargs):
    """Read SeaBird CTD file."""
    row_no = 0
    with open(file, 'r') as f:
        var_names = []
        units = []
        while True:
            line = next(f, None)
            row_no += 1
            if line.startswith('*END*'):    # end of header
                break

            # get names and units
            rx = re.match('^# name \d = (?P<variable>.+?): (?P<name>.+?) \[(?P<unit>.+?)\].*$', line)
            if rx:
                var_names.append(rx.group('name'))
                units.append(rx.group('unit'))

            # get logging interval
            rx = re.match('^# interval = (?P<unit>\w+?): (?P<value>\d+)', line)
            if rx:
                interval = pd.Timedelta('{} {}'.format(rx.group('value'), rx.group('unit')))

            # get start time
            rx = re.match('^# start_time = (.+) \[.+\]', line)
            if rx:
                start_time = pd.to_datetime(rx.group(1))

        # modify names such that there are no blank spaces in between elements
        var_names[:] = [re.sub("[,]*\s+", "_", var) for var in var_names]

        # read rest of the file into a pandas DataFrame
        df = pd.read_fwf(file, skiprows=row_no, names=var_names,
                         usecols=range(len(var_names)))  # usecols omits `flag` column

    # remove 'time' column
    df = df.drop([i for i in var_names if 'time' in i.lower()], axis=1, errors='ignore')

    # ensure all column dtypes are numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    # generate time series and set as index
    time_idx = pd.date_range(start=start_time, periods=len(df), freq=interval)
    df.index = time_idx
    df.index = df.index.round(interval)

    df = df.reindex(sorted(df.columns), axis=1)

    # set nan_flag as NAN
    df[df == nan_flag] = np.nan

    if 'verbose' in kwargs:
        print('{:<11}:'.format('Start time'), start_time)
        print('{:<11}:'.format('End time  '), time_idx[-1])
        print('{:<11}:'.format('Interval'), interval)
        print('Variables and units:')
        for var, unit in list(zip(var_names, units))[1:]:
            print('\t{:<22} : {}'.format(var, unit))
        print()

    return df
