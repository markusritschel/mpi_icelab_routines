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

i:k: datetime r2 d2 r16 d16 temperature logger_temp

    i           : Module ID (index starting at 0)
    k           : Wire pair (index starting at 0)
    datetime    : Time stamp in ISO8601 format
    r2          : Resistance of the respective wire_pair at 2 kHz [Ohm]
    d2          : Debugging value
    r16         : Resistance of the respective wire_pair at 16kHz [Ohm]
    d16         : Debugging value
    temperature : Temperature at the respective wire_pair [°C]
    logger_temp : Temperature of the controller [°C]

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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from .helpers import median, grad, savgol, butterworth

VERBOSE = False


__all__ = ['read_harp_file', 'read_harp_data', 'calc_brine_salinity', 'calc_reference_resistance', 'read']


def read_harp_file(file, debug=False, **kwargs):
    """Read-out routine for log files of the salinity harps developed by Leif Riemenschneider.
    Non-valid characters get eliminated such that only numeric values remain.
    A xarray.Dataset is created with `time`, `module` and `wire_pair` as coordinates.

    Return
    ------
    ds : xarray.Dataset
        Converted DataFrame to xarray Dataset. Similar to netCDF structure.
    """

    # specify column names for entries of the data file
    col_names = ['device', 'time', 'r2', 'd2', 'r16', 'd16', 'temperature', 'logger_temp']

    print('read salinity harp now... ', end='')

    # read csv file into Pandas DataFrame
    df = pd.read_csv(file, names=col_names, index_col=False,
                     skiprows=0, comment='#', sep=' ',
                     engine='python', error_bad_lines=False)

    # split first column into harp-module number and wire-pair number and remove the origin column
    df = df.join(df['device'].str.split(':', 2, expand=True).iloc[:, :2].rename(columns={0: 'module', 1: 'wire_pair'}))

    # remove redundant columns
    df.drop(['device'], inplace=True, axis=1, errors='ignore')

    # filter data by debugging numbers
#    if not debug:
#        df = df.where((df.d2==2) & (df.d16==2))
#        df.drop(['d2', 'd16'], inplace=True, axis=1, errors='ignore')

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
    df = df.loc[lastcol_idx]#[:-1]  # last row has only one single value in column 1

    # convert back to multi index
    df = df.stack(level=1).stack()
    ds = df.to_xarray()

    ds.attrs = {'Temperature': '°C',
                'Resistance' : 'Ohm'}

    # ensure time coordinate is datetime object
    ds.coords['time'] = pd.to_datetime(ds.coords['time'])

    print('done')

    return ds


def read_harp_data(file, module=0):
    """Read harp data from a file using the `read_harp_file` function and select a module.
    Certain variables will be calculated:
    - brine salinity
    - bulk salinity
    - solid fraction
    - liquid fraction"""
    data = read_harp_file(file)
    data = data.sel(module=module)

    resistance_channel = 'r16'

    # compute reference resistance
    r0s = calc_reference_resistance(data, resistance_channel, kind='butterworth', tolerance=(1e-4, 3e-4))

    T_freeze = data['temperature'].sel(time=r0s.coords['time'])
    T = data['temperature'].where(data['temperature'] < T_freeze)

    S_brine = calc_brine_salinity(T, method='Vancoppenolle')

    # liquid fraction calculated as written in [TODO: Reference]
    liquid_frac = r0s / data[resistance_channel]
    liquid_frac = liquid_frac.where(liquid_frac <= 1).transpose()
    solid_frac = 1 - liquid_frac
    S_bulk = liquid_frac * S_brine

    data = data.assign({'brine salinity': S_brine,
                        'solid fraction': solid_frac,
                        'liquid fraction': liquid_frac,
                        'bulk salinity': S_bulk})

    return data


def calc_brine_salinity(T, method='Assur', print_formula=False):
    """Calculate the brine salinity by a given temperature according to one of the following methods:
    - 'Assur'
        year: 1958
        S = -1.20 - 21.8*T - 0.919*T**2 - 0.0178*T**3

    - 'Vancoppenolle'
        year: 2019
        doi: 10.1029/2018JC014611
        S = -18.7*T - 0.519*T**2 - 0.00535*T**3
    """
    # TODO: add validity range and mask T/S accordingly
    if method == 'Assur':
        a = -1.20
        b = -21.8
        c = -0.919
        d = -0.0178

    elif method == 'N&W09':
        a = 0
        b = -21.4
        c = -0.886
        d = -0.0170

    elif method == 'Vancoppenolle':
        a = 0
        b = -18.7
        c = -0.519
        d = -0.00535

    else:
        raise KeyError("Method unknown!")

    S_brine = a + b*T +c*T**2 +d*T**3

    if print_formula:
        print('-'*60)
        print('For {}, the S_brine gets calculated according to'.format(method))
        print('\tS_brine = a + b*T +c*T**2 +d*T**3')
        print('with: ')
        print('\ta = {}'.format(a))
        print('\tb = {}'.format(b))
        print('\tc = {}'.format(c))
        print('\td = {}'.format(d))
        print()

    return S_brine


def calc_reference_resistance(data, resistance_channel='r10', kind='median', tolerance=(1e-4, 3e-4)):
    """Compute the reference resistance R0 for a given module.
    """
    if not isinstance(tolerance, tuple):
        raise KeyError("Parameter `tolerance` must be a tuple containing two floats.")
    tolerance = np.sort(tolerance)

    data = data[resistance_channel]
    data_smooth = eval(kind)(data)
    data_gradient = median(grad(data_smooth, 20))

    # data_gradient.to_pandas().squeeze().plot()
    # find values that are in a certain tolerance range and mask others
    grad_tol = np.where(np.logical_and(data_gradient > tolerance[0], data_gradient < tolerance[1]),
                        data_gradient, np.nan)
    # set all those values to common value
    grad_tol[~np.isnan(grad_tol)] = 1

    # now find the first occurrence in that array which is not NAN
    freezing_starts = np.nanargmin(grad_tol, axis=0).squeeze()
    freezing_sel = xr.DataArray(freezing_starts, dims=['wire_pair'])
    r0s = data[freezing_sel]

    return r0s


# alias
read = read_harp_data


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='1.0')

    file = args.pop('FILE')
    kwargs = {re.sub('^--', '', a): v for a, v in args.items()}
