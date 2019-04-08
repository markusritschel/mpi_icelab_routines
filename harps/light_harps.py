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
import pandas as pd


def read_harp_file(file):
    col_names = ['cnt', 'identifier', 'time', 'C', 'R', 'G', 'B', 'Temp']
    df = pd.read_csv(file, names=col_names, sep=r"\s+", comment='#',
                     engine='python', error_bad_lines=False)

    # find data blocks (counter starts at 1)
    # check lines where cnt == 1
    blocks_idx = df.index[df['cnt'] == 1]
    # take first cnt==1 index that is > 0
    block2_idx = blocks_idx[blocks_idx > 0][0]
    # => only consider lines up to 2nd data block
    df = df.iloc[:block2_idx, :]

    df.drop(['cnt'], axis=1, inplace=True)

    # split first column into harp-module number and wire-pair number and remove the origin column
    df = df.join(df['identifier'].str.split(':', 3, expand=True).iloc[:, :3].rename(
        columns={0: 'stick', 1: 'diode', 2: 'amplifier'}))
    df.drop(['identifier'], inplace=True, axis=1, errors='ignore')

    # convert content of 'time' column to datetime objects
    df['time'] = pd.to_datetime(df['time'], errors='coerce')  # 'coerce' errors yields NA for non datetime strings
    df['time'] = df.time.dt.tz_localize(None)  # remove timezone info
    # drop rows with non datetime objects
    df = df.dropna(subset=['time'])
    # set column 'time' as index
    df.set_index(['time'], inplace=True)

    # from now on only numeric columns should be left
    # filter non-valid characters
    df.replace(regex=True, to_replace=r"[^0-9.]", value="",
               inplace=True)  # replaces every character not matching '0-9' or '.' with empty string
    # make remaining columns numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    df.set_index(['stick', 'diode', 'amplifier'], append=True, inplace=True)

    _cols = df.columns

    df = df.unstack(level=[1, 2, 3])
    lastcol_idx = df.iloc[:, 0].dropna().index
    # ... and fill NANs in all columns backwards such that in each row with `lastcol_idx` are
    # all values of one block
    df.fillna(method='bfill', inplace=True)

    # now limit data frame to those respective rows
    df = df.loc[lastcol_idx][:-1]  # last row has only one single value in column 1

    # convert back to multi index
    df = df.stack(level=[1, 2, 3])

    # restore original order of the columns
    df = df[_cols]

    ds = df.to_xarray()

    ds.attrs = {'C': 'Clear channel',
                'R': 'Red channel',
                'G': 'Green channel',
                'B': 'Blue channel',
                'Temp': 'Temperature [°C]'
                }

    return ds
