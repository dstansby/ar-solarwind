import numpy as np
import pathlib

figdir = pathlib.Path('/Users/dstansby/Dropbox/Work/Papers/20arsources/figs')

def CDF(data):
    """
    Return the cumulative distribution function of a dataset.
    """
    data = data.ravel()
    data = data[np.isfinite(data)]
    p = np.arange(data.size) / (data.size - 1)
    return np.sort(data), p
