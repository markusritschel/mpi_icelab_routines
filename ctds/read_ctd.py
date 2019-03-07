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


def read_rbr(file, nan_flag=-1000., **kwargs):
    """Read RBR CTD file"""
    header = {'host_time': 'Host time',
              'log_time': 'Logger time',
              'log_start': 'Logging start',
              'log_end': 'Logging end',
              'sample_period': 'Sample period'}

    with open(file, 'r') as f:
        # read header info and find number of lines to skip
        row_no = 0
        file_header = ""
        while True:
            line = next(f, None)
            row_no += 1
            # break on first empty line (= end of header)
            if line == '\n':
                break
            else:
                file_header += line  # + '\n'

        for k, v in header.items():
            m = re.search('^{}\s+(\d.+)$'.format(v), file_header, re.MULTILINE)
            if m:
                time_str = m.group(1)
                if len(time_str.split('/')) > 1:
                    header[k] = pd.to_datetime(time_str, format='%y/%m/%d %H:%M:%S')
                else:
                    header[k] = pd.Timedelta(time_str)

        # read in the rest if the file into a pandas DataFrame
        df = pd.read_csv(file, skiprows=row_no, sep=r"\s+")

    # ensure all columns are numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    # generate time series and set as index
    time_idx = pd.date_range(start=header['log_start'], end=header['log_end'], freq=header['sample_period'])
    df.index = time_idx[:len(df)]
    df.index = df.index.round(header['sample_period'])

    # set nan_flag as NAN
    df[df == nan_flag] = np.nan

    df.rename(columns={'Cond': 'Conductivity',
                       'Temp': 'Temperature',
                       'Pres': 'Pressure',
                       'Sal': 'Salinity',
                       'DensAnom': 'Density_Anomaly'
                       }, inplace=True)

    df = df.reindex(sorted(df.columns), axis=1)

    if 'verbose' in kwargs:
        for k, v in header.items():
            print('{:<14}: {}'.format(k, v))
        print()

    return df
