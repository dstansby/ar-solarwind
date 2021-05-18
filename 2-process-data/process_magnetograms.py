import argparse
import functools
import glob
import multiprocessing
import pathlib

import astropy.units as u
import matplotlib
matplotlib.use('Agg')
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
import numpy as np

from magnetogram import MagnetogramFactory

# Directory with magnetograms
magnetogram_dir = pathlib.Path('/Volumes/Work/synoptic_data')
# Directory to output traced field line data to
output_dir = pathlib.Path('/Volumes/Work/new_fline_results')

# Configurable PFSS model resolution. Set to 50 for the paper
nr = 50
# Size of fieldline grid to trace. Set to 360, 180 for the paper.
nlon = 360
nlat = 180
# Configurable source surface radius
# In the paper this is set at 2.0 throughout, apart from appendix 1
# where it is varied as [1.5, 2.0, 2.5, 3.0].
rss = 2.0


parser = argparse.ArgumentParser(description='Process magnetograms.')
parser.add_argument('data_source', type=str, help='Data source',
                    choices=['gong', 'kpvt', 'solis', 'mdi'])
args = parser.parse_args()
source = args.data_source


def save_to_png(m, fname):
    fig = plt.figure()
    m.m.plot_settings['cmap'] = 'RdBu'
    m.m.plot_settings['norm'] = Normalize(vmin=-100, vmax=100)
    m.m.plot()
    fig.savefig(fname)
    plt.close('all')


def process_single_magnetogram(source, path):
    """
    Process a single magnetogram and save outputs.

    Parameters
    ----------
    source: str
        Source name.
    path: pathlib.Path
        Path to magnetogram file.
    """
    print(f'Processing {path}')
    m = MagnetogramFactory(path, nr, rss, nlon, nlat, source)
    if np.any(~np.isfinite(m.data)):
        nonfin = np.sum(~np.isfinite(m.data))
        print(f'Skipping {path}, has {nonfin} non-finite data points')
        return

    rss_str = str(int(rss * 10))
    (output_dir / source / 'png').mkdir(parents=True, exist_ok=True)
    (output_dir / source / rss_str).mkdir(parents=True, exist_ok=True)
    dtime_fmt = '%Y%m%d_%H%M%S'
    date_str = m.date.strftime(dtime_fmt)

    fname = output_dir / source / 'png' / f'{source}_{date_str}.png'
    if not fname.exists():
        print('Saving png...')
        save_to_png(m, fname)

    print('Tracing field lines in...')
    feet = m.fline_feet_coords
    b_feet = m.b_at_feet

    lats = np.ones(nlon * nlat) * np.nan
    lats[m.is_open_fline] = feet.lat.to_value(u.deg)

    lons = np.ones(nlon * nlat) * np.nan
    lons[m.is_open_fline] = feet.lon.to_value(u.deg)

    b_feet = np.ones(nlon * nlat) * np.nan
    b_feet[m.is_open_fline] = m.b_at_feet

    b_all = m.data.ravel()
    b_ss = np.ones(nlon * nlat) * np.nan
    b_ss[m.is_open_fline] = m.b_at_ss
    # Sampling on the solar surface can be a bit erronous, so label field line
    # polarity using source surface magnetic field
    b_feet = np.abs(b_feet) * np.sign(b_ss)

    fname = output_dir / source / rss_str / f'{date_str}.npz'
    np.savez(fname, lats=lats, lons=lons, b_feet=b_feet, b_all=b_all, b_ss=b_ss)
    print(f'✅ Processed {path}')


def get_fnames(directory):
    """
    Get all .fits.gz or .fits files in ``directory``.

    Parameters
    ----------
    directory : str
    """
    fnames = glob.glob(f'{directory}/*.fits.gz')
    if len(fnames) == 0:
        fnames = glob.glob(f'{directory}/*.fits')
    fnames.sort()
    return fnames


if __name__ == '__main__':
    directory = f'{magnetogram_dir}/{source}'
    fnames = get_fnames(directory)[::-1]
    print(f"Found {len(fnames)} files in {directory}")
    func = functools.partial(process_single_magnetogram, source)
    for fname in fnames:
        # Using mutliprocessing here is an embarassingly awful method of
        # avoiding memory leaks by running each magnetogram in its own
        # thread which is then deleted along with its memory.
        with multiprocessing.Pool(1) as p:
            p.map(func, [fname])
