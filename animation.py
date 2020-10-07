from datetime import datetime
import glob
from pathlib import Path

import numpy as np
import matplotlib.animation as anim
import matplotlib.pyplot as plt
import matplotlib.colors as mcolor
import matplotlib.ticker as mticker
import xarray as xr

dtime_fmt = '%Y%m%d_%H%M%S'


def load_data():
    # Variable names
    variables = ['lons', 'lats', 'b_all', 'b_feet']
    # List of filenames
    files = sorted(glob.glob('data/*.npz'))
    # Number of data poitns for each variable and time
    npoints = 360 * 180

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
                            coords={'variable': variables,
                                    'time': dtimes,
                                    'points': np.arange(npoints)})

    all_data.loc['lats', ...] = np.sin(np.deg2rad(all_data.loc['lats', ...]))
    return all_data


def histogram(data, bins, ax=None, mask=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))

    dtimes = data.coords['time'].values
    data = data.values
    finite = np.isfinite(data)
    if mask is not None:
        finite = mask & finite

    data = np.ma.array(data, mask=finite)
    for row, dtime in zip(data, dtimes):
        row = row.data[row.mask]
        hist, bin_edges = np.histogram(row, bins=bins, density=False)

        corner_x = [dtime, dtime + np.timedelta64(27, 'D')]
        corner_y = bin_edges
        X, Y = np.meshgrid(corner_x, corner_y)
        hist = hist.reshape(hist.size, 1)

        ax.pcolormesh(X, Y, hist, cmap='Blues', norm=mcolor.LogNorm(),
                      rasterized=True)

    ax.set_xlabel('Year')
    return ax


def setup_figure(data):
    fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(8, 4),
                            tight_layout=True)

    ax = axs[0, 1]
    histogram(data.loc['lats', ...],
              np.linspace(-1, 1, 101), ax)
    ax.set_ylabel('sin(lat)')

    ax = axs[1, 1]
    histogram(data.loc['lons', ...],
              np.linspace(0, 360, 181), ax)
    ax.set_ylabel('lon')
    return fig, axs


if __name__ == '__main__':
    data = load_data()
    fig, axs = setup_figure(data)

    frames = data.coords['time'].values

    l1 = axs[0, 1].axvline(frames[0], color='tab:red', linewidth=1)
    l2 = axs[1, 1].axvline(frames[0], color='tab:red', linewidth=1)
    lines = [l1, l2]

    norm = mcolor.SymLogNorm(linthresh=1, vmin=-1e3, vmax=1e3, base=10)
    cmap = plt.get_cmap('RdBu')
    footpoints = axs[0, 0].scatter(data.loc['lons', frames[0], :],
                                   data.loc['lats', frames[0], :],
                                   marker='o',
                                   s=1, alpha=0.5,
                                   c=norm(data.loc['b_feet', frames[0], :]),
                                   cmap='RdBu')
    axs[0, 0].set_xlim(0, 360)
    axs[0, 0].set_ylim(-1, 1)

    X, Y = np.meshgrid(np.linspace(0, 360, 361), np.linspace(-1, 1, 181))
    b_magnet = data.loc['b_all', frames[0], :].values.reshape(180, 360)
    magnet = axs[1, 0].pcolormesh(X, Y, b_magnet,
                                  cmap='RdBu', shading='flat', zorder=-10, norm=norm)

    gridlines = []
    for ax in axs[:, 0]:
        ax.xaxis.set_major_locator(mticker.FixedLocator(
            np.linspace(0, 360, 9)))
        gridlines += [ax.axvline(x, color='k', alpha=0.2, linewidth=1) for
                      x in np.linspace(0, 360, 9)]
        gridlines += [ax.axhline(y, color='k', alpha=0.2, linewidth=1) for
                      y in np.linspace(-1, 1, 5)]
    title = axs[0, 0].set_title(str(frames[0])[:10])

    def animate(dtime):
        print(dtime)
        for line in lines:
            line.set_xdata(dtime)

        footpoints.set_offsets(np.array([data.loc['lons', dtime, :],
                                         data.loc['lats', dtime, :]]).T)
        footpoints.set_facecolors(cmap(norm(data.loc['b_feet', dtime, :])))

        magnet.set_array(data.loc['b_all', dtime, :].values.reshape(180, 360))

        title.set_text(str(dtime)[:10])

        return lines + [footpoints] + [magnet] + gridlines + [title]

    ani = anim.FuncAnimation(fig, animate,
                             frames=frames, blit=True)
    ani.save('footoints.mp4', fps=12)
    # plt.show()
