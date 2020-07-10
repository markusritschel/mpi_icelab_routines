import pandas as pd

def read_tsticks(file):
    col_names = ['id', 'seconds', 'time', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7']
    pd.read_csv(file, delim_whitespace=True, converters={}, parse_dates=[2], date_parser=None, error_bad_lines=False, names=col_names)
    
    # TODO: check salinity and light harp routines
