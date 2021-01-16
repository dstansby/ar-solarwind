import os
import pathlib
import glob
import multiprocessingx
import functools

import astropy.units as u
import numpy as np

from magnetogram import MagnetogramFactory
from solar_library import get_gong_map


output_dir = pathlib.Path('/Volumes/Work/open_fline_results')

nr = 50
rss = 1.5
nlon = 180
nlat = 90

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
    feet = m.fline_feet
    b_feet = m.b_at_feet

    lats = feet.lat.to_value(u.deg)
    lons = feet.lon.to_value(u.deg)
    b_feet = b_feet
    b_all = m.data.ravel()

    date_str = m.date.strftime(dtime_fmt)
    fname = output_dir / source / f'{date_str}.npz'
    np.savez(fname, lats=lats, lons=lons, b_feet=b_feet, b_all=b_all)


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
