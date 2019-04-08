#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   03/04/2019
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import division, print_function, absolute_import

import re
import pandas as pd

from cachetools import cached, TTLCache
licor_cache = TTLCache(maxsize=1, ttl=600)


def read_licor(file):
    if licor_cache.currsize > 0:
        print('get LiCOR data from cache')
    return read_licor_serial_log(file)


@cached(cache=licor_cache)
def read_licor_serial_log(file):
    print('read LiCOR file now... ', end='')

    # default values for header and units
    # col_names = ['TIMESTAMP', 'Licor_T', 'Licor_P', 'Licor_CO2', 'Licor_H2O', 'Licor_DewPt', 'Licor_Batt']
    col_names = ["TIMESTAMP", "RECORD", "Licor_T", "Licor_P", "Licor_CO2", "Licor_H2O", "Licor_DewPt", "Licor_Batt", "LoggerBatt", "LoggerTemp", "PAR", "SoilT107"]
    units = ["TS", "RN", "°CC", "kPa", "ppm", "ppt", "°C", "Volt", "Volt", "°C", "µmol/m^2/s", "°C"]

    skiprows = 0
    # read header and units if available
    with open(file, 'r') as f:
        line = f.readline().rstrip()
        while not re.match(r'^\"?\d+', line):
            if line.startswith('"TIMESTAMP",'):
                col_names = [x.strip('"') for x in line.split(',')]
            if line.startswith('"TS",'):
                units = [x.strip('"') for x in line.split(',')]
            skiprows += 1
            line = f.readline().rstrip()

    col_names = [re.sub("Licor_", "", x) for x in col_names]
    units_dict = {k: re.sub(r"[Dd]eg.*C", "°C", v)
                  for (k, v) in zip(col_names, units)}

    # read data into pandas.DataFrame
    # if header is present, skip respective amount of rows
    df = pd.read_csv(file, names=col_names,
                     sep=',', engine='python',
                     error_bad_lines=False, skiprows=skiprows)

    df = df.dropna(subset=['TIMESTAMP'])                                # drop rows with non datetime objects
    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')  # 'coerce' errors yields NA for non datetime strings
    df['TIMESTAMP'] = df.TIMESTAMP.dt.tz_localize(None)                 # remove timezone info
    df.set_index(['TIMESTAMP'], inplace=True)
    df.index.name = df.index.name.lower()

    units_dict.pop("TIMESTAMP", None)
    units_dict.pop("RECORD", None)

    # ensure all column dtypes are numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    print('done')

    ds = df.to_xarray()

    ds.attrs = units_dict

    return ds


if __name__ == '__main__':
    file = '/home/mpim/m300660/Masterarbeit/Data/IceLab/LiCOR/2019-03-28_exp.dat'
    d = read_licor_serial_log(file)
    print(d.info())
