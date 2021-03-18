from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

dtime_fmt = '%Y%m%d_%H%M%S'

# Cutoff for AR detection in G for each source
thresholds = {'gong': 30, 'solis': 40, 'kpvt': 30, 'hmi': 150, 'mdi': 100}


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


