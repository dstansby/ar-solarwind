from datetime import datetime, timedelta
import pathlib
import urllib.request

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


def get_solis_maps():
    # dl = parfive.Downloader(max_conn=2, headers={'user': 'anonymous'})
    to_dl = []
    local_dir = pathlib.Path('/Volumes/Media/Data/solis')

    with FTP('solis.nso.edu', user='anonymous') as ftp:
        print('Getting file list...')
        ftp.cwd('/integral/kbv7g')
        files = ftp.nlst()
        for fname in files:
            if fname[-2:] == 'gz':
                local_file = local_dir / fname
                with open(local_file, "wb") as file:
                    print(fname)
                    # use FTP's RETR command to download the file
                    ftp.retrbinary(f"RETR {fname}", file.write)


def get_hmi_maps():
    from sunpy.net import Fido, attrs as a
    import sunpy.map

    series = a.jsoc.Series('hmi.mrsynop_small_720s')
    time = a.Time('2010/01/01', '2010/01/01')

    result = Fido.search(time, series, a.jsoc.Notify("d.stansby@ucl.ac.uk"))

    Fido.fetch(result)
    print(result)


if __name__ == '__main__':
    get_hmi_maps()
    # for i in range(2007, 2010):
    #     get_gong_maps(i)
