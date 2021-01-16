import numpy as np

def CDF(data):
    """
    Return the cumulative distribution function of a dataset.
    """
    data = data.ravel()
    data = data[np.isfinite(data)]
    p = np.arange(data.size) / (data.size - 1)
    return np.sort(data), p
