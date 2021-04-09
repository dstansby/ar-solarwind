from datetime import datetime
from pathlib import Path
import glob

import numpy as np
import pandas as pd
import xarray as xr

dtime_fmt = '%Y%m%d_%H%M%S'

# Cutoff for AR detection in G for each source
thresholds = {'gong': 30, 'solis': 40, 'kpvt': 35, 'mdi': 100}


def load_data(files):
    # Number of data points for each variable and time
    npoints = 360 * 180
    # Variable names
    variables = ['lons', 'lats', 'b_all', 'b_feet', 'b_ss']

    # Empty array to store data
    all_data = np.zeros((len(variables), len(files), npoints)) * np.nan

    dtimes = []
    for j, f in enumerate(files):
        f = Path(f)
        dtimes.append(datetime.strptime(f.stem, dtime_fmt))
        d = np.load(f)
        for i, var in enumerate(variables):
            # Pad data to have the same length
            data = d[var]
            all_data[i, j, :data.size] = data

    all_data = xr.DataArray(all_data,
                            dims=('variable', 'time', 'points'),
                            coords={'variable': variables, 'time': dtimes, 'points': np.arange(npoints)})
    return all_data


def all_flux(data):
    b_ss = np.abs(data.loc['b_ss'])
    allflux = np.sum(b_ss, axis=1)
    return allflux


def ar_flux(data, threshold):
    b_feet = np.abs(data.loc['b_feet'])
    b_ss = np.abs(data.loc['b_ss'])
    # Calculate flux
    ar_flux = np.sum((b_feet > threshold) * b_ss, axis=1)
    return ar_flux


def load_ssn():
    df = pd.read_csv('data/ssn/SN_d_tot_V2.0.csv', delimiter=';',
                     names=['Year', 'Month', 'Day', 'Fractional year', 'SSN', 'SSN st dev',
                            'nobs', 'Definitive indicator'],
                     parse_dates={'Date': [0, 1, 2]},
                     na_values=['-1'])
    df = df.loc[df['Date'] > datetime(1975, 1, 1)]
    df = df.set_index('Date')
    return df


def load_cme_rate():
    df = pd.read_csv('data/cme/CME_obs.csv', names=['Date', 'n'],
                     parse_dates=['Date'])
    df = df.set_index('Date')
    df = df.resample('25D', origin=datetime(1995, 10, 1)).sum()
    return df


def load_lasco_downtime():
    files = glob.glob('data/cme/lasco_downtime/*.txt')
    dfs = [pd.read_csv(f, sep='-',
                       names=['Start', 'End'],
                       parse_dates=['Start', 'End'],
                       comment='#') for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df = df.set_index('Start')
    df = df.sort_index()
    df = df.drop_duplicates()
    df['dt'] = df['End'] - df.index
    df = df.drop('End', axis=1)
    df = df.resample('25D', origin=datetime(1995, 10, 1)).sum()
    return df


def get_ar_lats(stime, etime):
    files = glob.glob('data/ar/ar_data_*.txt')
    df = pd.concat([pd.read_csv(f, index_col='event_starttime',
                                parse_dates=['event_starttime']) for f in files])
    df = df.loc[df.index > stime]
    df = df.loc[df.index < etime]
    return df['hgc_y']


if __name__ == '__main__':
    get_ar_lats()
