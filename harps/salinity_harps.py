#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   24/01/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""This script reads harp data from a text file which contains the data in the following format:

x:y: datetime r6 i6 r10 i10 temperature something

    x           : Module ID (0-2)
    y           : Wire pair (usually going from 0 to 7)
    datetime    : Time stamp in ISO8601 format
    r6          : Resistance at 6 kHz [Ohm]
    i6          : some index
    r10         : Resistance at 10kHz [Ohm]
    i10         : some index
    temperature : Temperature [°C]
    ?           : ?

Data will be organized in an xarray.Dataset. Modules and parameters can be directly approached from the script (see options).


Usage:
    harp_eval.py FILE --parameter=<VALUE> --module=<ID> [--wire=<ID>] [options]
    harp_eval.py FILE --parameter=<VALUE> --wire=<ID> [--module=<ID>] [options]
    harp_eval.py (-h | --help)
    harp_eval.py --version

Options:
    -p, --parameter=<VALUE>  The parameter to be evaluated (must be one of 'temperature', 'r6' or 'r10').
    -m, --module=<ID>        The module/harps to be evaluated (can be single value or comma separated list).
    -w, --wire=<ID>          The wire pair to be evaluated (can be single value or comma separated list).

    -s, --stat               Show statistics.
    -v, --verbose            Print more text.
    -h, --help               Show this screen.
    --version                Show version.

"""
import inspect
import re

import docopt
import pandas as pd

VERBOSE = False


def read_harp_file(file, **kwargs):
    """Read-out routine for log files of the salinity harps developed by Leif Riemenschneider.
    Non-valid characters get eliminated such that only numeric values remain.
    A xarray.Dataset is created with `time`, `module` and `wire_pair` as coordinates.

    Return
    ------
    ds : xarray.Dataset
        Converted DataFrame to xarray Dataset. Similar to netCDF structure.
    """

    # specify column names for entries of the data file
    col_names = ['device', 'time', 'r6', 'i6', 'r10', 'i10', 'temperature', 't_case']

    # read csv file into Pandas DataFrame
    df = pd.read_csv(file, names=col_names, index_col=False,
                     skiprows=0, comment='#', sep=' ',
                     engine='python', error_bad_lines=False)

    # split first column into harp-module number and wire-pair number and remove the origin column
    df = df.join(df['device'].str.split(':', 2, expand=True).iloc[:, :2].rename(columns={0: 'module', 1: 'wire_pair'}))
    df.drop(['device'], inplace=True, axis=1, errors='ignore')

    # convert content of 'time' column to datetime objects
    df['time'] = pd.to_datetime(df['time'], errors='coerce')  # 'coerce' errors yields NA for non datetime strings
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

    # make 'module' and 'wire_pair' column additional index
    df.set_index(['module', 'wire_pair'], append=True, inplace=True)

    df.sort_index(inplace=True)

    if VERBOSE:
        print()
        print('-' * 50)
        print(inspect.getdoc(read_harp_file))

    if kwargs.get('stat'):
        print()
        print(df.describe())

    # convert multi index to multi column
    df = df.unstack(level=1).unstack(level=1)
    lastcol_idx = df.iloc[:, 0].dropna().index
    # ... and fill NANs in all columns backwards such that in each row with `lastcol_idx` are
    # all values of one block
    df.fillna(method='bfill', inplace=True)

    # now limit data frame to those respective rows
    df = df.loc[lastcol_idx][:-1]  # last row has only one single value in column 1

    # convert back to multi index
    df = df.stack(level=1).stack()
    ds = df.to_xarray()

    ds.attrs = {'Temperature': '°C',
                'Resistance' : 'Ohm'}

    # ensure time coordinate is datetime object
    ds.coords['time'] = pd.to_datetime(ds.coords['time'])

    return ds


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='1.0')

    file = args.pop('FILE')
    kwargs = {re.sub('^--', '', a): v for a, v in args.items()}
