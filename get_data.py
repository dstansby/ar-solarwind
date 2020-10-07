from datetime import datetime, timedelta
import pathlib

import numpy as np
from ftplib import FTP
import parfive
from sunpy.coordinates.sun import (carrington_rotation_number,
                                   carrington_rotation_time)


local_dir = pathlib.Path('/Volumes/Media/Data/gong')


def get_crots(year):
    """
    Get all Carrington rotations that start within the given year.
    """
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)

    crot_start = carrington_rotation_number(year_start)
    crot_end = carrington_rotation_number(year_end)

    crot_start = int(np.ceil(crot_start))
    crot_end = int(np.floor(crot_end))

    return list(range(crot_start, crot_end + 1))


def get_gong_maps(year):
    """
    Get GONG maps closest to the start of each Carrington rotation in year.
    """
    crots = get_crots(year)
    crot_dates = [carrington_rotation_time(crot) for crot in crots]
    crot_dates = [d for d in crot_dates if d < datetime.now()]
    crot_strs = [d.isot for d in crot_dates]
    print(f'Dates for {year}: {crot_strs}')

    dl = parfive.Downloader(max_conn=2)
    ftp = FTP('gong2.nso.edu')
    ftp.login()
    print('Getting file list...')
    for d in crot_dates:
        date_dir = d.strftime('%Y%m/mrzqs%y%m%d')
        gong_dir = f"/oQR/zqs/{date_dir}"
        ftp.cwd(gong_dir)
        files = ftp.nlst()
        fname = files[0]
        if not (local_dir / fname).exists():
            dl.enqueue_file(f"ftp://gong2.nso.edu{gong_dir}/{fname}",
                            local_dir, fname)

    ftp.quit()
    res = dl.download()
    if len(res.errors):
        print(res.errors)


if __name__ == '__main__':
    for i in range(2007, 2010):
        get_gong_maps(i)
