import os
import pathlib
import glob
import multiprocessing
import functools

import astropy.units as u
import numpy as np

from magnetogram import MagnetogramFactory
from solar_library import get_gong_map


output_dir = pathlib.Path('/Volumes/Media/open_fline_results')

nr = 50
rss = 2
nlon = 180
nlat = 90

dtime_fmt = '%Y%m%d_%H%M%S'


def process_single_magnetogram(source, path):
    """
    Process a single magnetogram and save outputs.
    """
    print(f'Processing {path}')
    m = MagnetogramFactory(path, nr, rss, nlon, nlat, source)
    feet = m.fline_feet
    b_feet = m.b_at_feet

    lats = feet.lat.to_value(u.deg)
    lons = feet.lon.to_value(u.deg)
    b_feet = b_feet
    b_all = m.data.ravel()

    date_str = m.date.strftime(dtime_fmt)
    fname = output_dir / source / f'{date_str}.npz'
    np.savez(fname, lats=lats, lons=lons, b_feet=b_feet, b_all=b_all)


if __name__ == '__main__':
    source = 'solis'
    fnames = glob.glob(f'/Volumes/Media/Data/{source}/*.fits.gz')
    fnames.sort()
    func = functools.partial(process_single_magnetogram, source)
    for fname in fnames[:1]:
        with multiprocessing.Pool(1) as p:
            p.map(func, [fname])
