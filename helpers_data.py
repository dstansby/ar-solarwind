from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr

dtime_fmt = '%Y%m%d_%H%M%S'


def load_data(files):
    # Number of data points for each variable and time
    npoints = 360 * 180
    # Variable names
    variables = ['lons', 'lats', 'b_all', 'b_feet',
                 'open_b', 'open_lons', 'open_lats']

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


def source_fractions(data):
    """
    Calculate and return the fraction of different open field regions.
    """
    # Active region
    ar_thresh = 20
    n_ar_pix_min = np.sum(np.abs(data.loc['b_feet']) > 20, axis=1)
    n_ar_pix_max = np.sum(np.abs(data.loc['b_feet']) > ar_thresh, axis=1)
    # Coronal hole
    n_ch_pix = np.sum(np.abs(data.loc['b_feet']) < ar_thresh, axis=1)
    n_tot_pix = n_ar_pix_max + n_ch_pix

    # PCHs
    n_npch_pix = np.sum(data.loc['lats'] > np.rad2deg(np.arcsin(0.7)), axis=1)
    n_spch_pix = np.sum(data.loc['lats'] < -np.rad2deg(np.arcsin(0.7)), axis=1)

    dates = n_ar_pix_min.coords['time']

    frac_pch_n = n_npch_pix / n_tot_pix
    frac_pch_s = n_spch_pix / n_tot_pix
    frac_ch = n_ch_pix / n_tot_pix
    frac_ars_min = n_ar_pix_min / n_tot_pix
    frac_ars_max = n_ar_pix_max / n_tot_pix

    frac_ech = 1 - frac_pch_n - frac_pch_s - frac_ars_min

    ret = xr.DataArray([frac_pch_n, frac_pch_s, frac_ars_min, frac_ech, n_tot_pix], coords=(['n pch', 's pch', 'ar', 'ech', 'n tot'], dates))
    return ret
