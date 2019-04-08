#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   05/04/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import division, print_function, absolute_import
import pandas as pd
import re


def read_arduino(file, **kwargs):
    """Read in Arduino log file and return a xarray.Dataset including units.
    The routine checks the first lines until it finds the header based on a regular expression.
    Subsequent data then get read into a pandas.DataFrame object.
    After some data postprocessing return a xarray.Dataset
    """
    verbose = kwargs.get('verbose', False)
    csv_separator = kwargs.pop('sep', ',')
    frequency = kwargs.pop('freq', '10S')
    interpolation = kwargs.pop('interpolate', False)

    print('read Arduino file now... ', end='')

    # find header
    with open(file, 'r') as f:
        skip = 0
        while True:
            line = f.readline().strip()
            skip += 1
            if re.match(r'^# [a-z]+{}'.format(csv_separator), line):
                col_names = line.strip('# ').split(csv_separator)
                col_names = [col.strip() for col in col_names]
                break
            elif not line:
                raise ValueError('No header found!')

    # read csv file into pandas.DataFrame
    df = pd.read_csv(file, names=col_names,
                     skiprows=skip, comment='#', sep=csv_separator,
                     engine='python', error_bad_lines=False)

    # generate time index
    df = df.dropna(subset=['timestamp'])  # drop rows with non datetime objects
    df = df[df['timestamp'].str.contains(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ', regex=True)]
    df['timestamp'] = pd.to_datetime(df['timestamp'],
                                     errors='coerce')  # 'coerce' errors yields NA for non datetime strings
    df['timestamp'] = df.timestamp.dt.tz_localize(None)  # remove timezone info
    df = df.set_index('timestamp')

    # remove rows with equal index/timestamp
    df = df[~df.index.duplicated(keep='first')]

    # remove redundant columns
    df = df.drop(['millis'], axis=1, errors='ignore')  # drop 'millis' column if existent
    # rename columns in old datasets
    df = df.rename(columns={'CO2_value': 'pCO2_air',
                            'pH_value_1': 'pH_china',
                            'pH_value_2': 'pH_GMH',
                            'pH_value': 'pH',
                            'T_value': 'T_air',
                            'CO2_state': 'CO2_flag'})

    # ensure all entries are numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    df = df.reindex(pd.date_range(start=df.index.min(),
                                  end=df.index.max(),
                                  freq=frequency))

    df = df.resample(frequency).median()

    if interpolation:
        df.interpolate(method='time', inplace=True)

    if verbose:
        print("Time span:")
        print("    Start: {}".format(df.index[0]))
        print("      End: {}".format(df.index[-1]))

    ds = df.to_xarray()

    units = {'CO2_air': 'ppm',
             'Temp (GMH 3700)': '°C',
             'Temp (BME280)': '°C',
             'RelHumidity (BME280)': '%',
             'Pressure (BME280)': 'hPa'}

    ds.attrs = units

    print('done')

    return ds
