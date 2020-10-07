import os
import pathlib
import glob
import multiprocessing

import astropy.units as u
import numpy as np

from magnetogram import Magnetogram
from solar_library import get_gong_map


output_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'data'

nr = 50
rss = 2
nlon = 180
nlat = 90

dtime_fmt = '%Y%m%d_%H%M%S'


def process_single_magnetogram(path):
    """
    Process a single magnetogram and save outputs.
    """
    print(f'Processing {path}')
    m = Magnetogram(path, nr, rss, nlon, nlat)
    feet = m.fline_feet
    b_feet = m.b_at_feet

    lats = feet.lat.to_value(u.deg)
    lons = feet.lon.to_value(u.deg)
    b_feet = b_feet
    b_all = m.data.ravel()

    date_str = m.date.strftime(dtime_fmt)
    fname = output_dir / f'{date_str}.npz'
    np.savez(fname, lats=lats, lons=lons, b_feet=b_feet, b_all=b_all)


if __name__ == '__main__':
    fnames = glob.glob('/Volumes/Media/Data/gong/*.fits.gz')
    fnames.sort()
    for fname in fnames:
        with multiprocessing.Pool(1) as p:
            p.map(process_single_magnetogram, [fname])
