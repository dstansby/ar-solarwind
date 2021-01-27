import os
import pathlib
import glob
import multiprocessing
import functools

import astropy.units as u
import numpy as np

from magnetogram import MagnetogramFactory
from solar_library import get_gong_map


output_dir = pathlib.Path('/Volumes/Work/open_fline_results')

nr = 50
rss = 2.0
nlon = 360
nlat = 180

dtime_fmt = '%Y%m%d_%H%M%S'


def process_single_magnetogram(source, path):
    """
    Process a single magnetogram and save outputs.
    """
    print(f'Processing {path}')
    m = MagnetogramFactory(path, nr, rss, nlon, nlat, source)
    if np.any(~np.isfinite(m.data)):
        nonfin = np.sum(~np.isfinite(m.data))
        print(f'Skipping {path}, has {nonfin} non-finite data points')
        return
    print('Tracing field lines in...')
    feet = m.fline_feet_coords
    b_feet = m.b_at_feet

    lats = feet.lat.to_value(u.deg)
    lons = feet.lon.to_value(u.deg)
    b_feet = b_feet
    b_all = m.data.ravel()
    b_ss = m.b_at_ss.ravel()

    date_str = m.date.strftime(dtime_fmt)
    rss_str = str(int(rss * 10))
    fname = output_dir / source / rss_str / f'{date_str}.npz'
    np.savez(fname, lats=lats, lons=lons, b_feet=b_feet, b_all=b_all, b_ss=b_ss)


def get_fnames(folder):
    fnames = glob.glob(f'{folder}/*.fits.gz')
    if len(fnames) == 0:
        fnames = glob.glob(f'{folder}/*.fits')
    fnames.sort()
    return fnames


if __name__ == '__main__':
    source = 'gong'
    folder = f'/Volumes/Work/Data/{source}'
    fnames = get_fnames(folder)
    print(f"Found {len(fnames)} files in {folder}")
    func = functools.partial(process_single_magnetogram, source)
    for fname in fnames:
        with multiprocessing.Pool(1) as p:
            p.map(func, [fname])
