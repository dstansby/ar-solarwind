from datetime import datetime, timedelta
from pathlib import Path
import glob

import numpy as np
import pandas as pd
import xarray as xr


# Location of the processed data files
data_dir = Path('/Volumes/Work/new_fline_results')

dtime_fmt = '%Y%m%d_%H%M%S'

# Cutoff for AR detection in G for each source
thresholds = {'gong': 30, 'solis': 40, 'kpvt': 35, 'mdi': 100}


bad_dates = {'20060921': 'gong', '20061018': 'gong', '20061114': 'gong', '20061212': 'gong', '20210317': 'gong', '20210414': 'gong', '20210511': 'gong', '19980607': 'mdi', '19981118': 'mdi', '19981215': 'mdi', '19990208': 'mdi', '19991107': 'mdi', '19991205': 'mdi', '20020203': 'mdi', '20030609': 'mdi', '20030706': 'mdi', '20031217': 'mdi', '20040404': 'mdi', '20070108': 'mdi', '20090723': 'mdi', '20030906': 'solis', '20040604': 'solis', '20040702': 'solis', '20040826': 'solis', '20050912': 'solis', '20060213': 'solis', '20070822': 'solis', '20071205': 'solis', '20091127': 'solis', '20100111': 'solis', '20140703': 'solis', '20141022': 'solis', '20150529': 'solis', '20150716': 'solis', '20150915': 'solis', '20170727': 'solis', '20171021': 'solis'}


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
        if bad_dates.get(f.stem[:8], '') == f.parts[-3]:
            # Skip if a bad date - this still keeps the datetime
            # index as all nans in the dataframe
            continue
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
    df[df['dt'] > timedelta(days=25)] = np.nan
    df[(df.index > datetime(1998, 6, 24)) &
       (df.index < datetime(1999, 2, 1))] = np.nan
    df[(df.index < datetime(1996, 2, 1))] = np.nan
    return df


def get_ar_lats(stime, etime):
    files = glob.glob('data/ar/ar_data_*.txt')
    df = pd.concat([pd.read_csv(f, index_col='event_starttime',
                                parse_dates=['event_starttime']) for f in files])
    df = df.loc[df.index > stime]
    df = df.loc[df.index < etime]
    return df['hgc_y']


if __name__ == '__main__':
    df = load_lasco_downtime()
    print(df)
