from datetime import datetime, timedelta
from ftplib import FTP
import pathlib

import numpy as np
import parfive
from sunpy.coordinates.sun import (carrington_rotation_number,
                                   carrington_rotation_time)


# Set this to the directory you want to download files to
local_dir = pathlib.Path('/Volumes/Work/Data')
# Set this to your JSOC username
# See http://jsoc.stanford.edu/ajax/register_email.html to register
jsoc_user = "d.stansby@ucl.ac.uk"


def get_crots(year):
    """
    Get all Carrington rotations that start within the given year.

    Parameters
    ----------
    year : int
    """
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)

    crot_start = carrington_rotation_number(year_start)
    crot_end = carrington_rotation_number(year_end)

    crot_start = int(np.ceil(crot_start))
    crot_end = int(np.floor(crot_end))

    return list(range(crot_start, crot_end + 1))


def get_mdi_maps():
    """
    Get all available MDI Carrington rotation synoptic maps.
    """
    base_url = 'http://soi.stanford.edu/magnetic/synoptic/carrot/M_Corr'
    dl = parfive.Downloader(max_conn=1)
    for i in range(1911, 2105):
        fname = f'{base_url}/synop_Mr_0.polfil.{i}.fits'
        dl.enqueue_file(fname, local_dir / 'mdi')

    res = dl.download()
    if len(res.errors):
        print(res.errors)


def get_kpvt_maps():
    """
    Get all available KPVT Carrington rotation synoptic maps.
    """
    base_url = 'ftp://nispdata.nso.edu/kpvt/synoptic/mag'
    dl = parfive.Downloader(max_conn=1)
    for i in range(1625, 2008):
        fname = f'{base_url}/m{i}f.fits'
        dl.enqueue_file(fname, local_dir / 'kpvt')

    res = dl.download()
    if len(res.errors):
        print(res.errors)


def get_gong_maps(year):
    """
    Get GONG maps closest to the start of each Carrington rotation in the given year.

    Parameters
    ----------
    year : int
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
    local_gong_dir = local_dir / 'gong'
    for d in crot_dates:
        date_dir = d.strftime('%Y%m/mrzqs%y%m%d')
        gong_dir = f"/oQR/zqs/{date_dir}"
        try:
            ftp.cwd(gong_dir)
        except Exception as e:
            print(f'❌ Could not change to directory {gong_dir}')
            continue
        files = ftp.nlst()
        fname = files[0]
        if not (local_gong_dir / fname).exists():
            dl.enqueue_file(f"ftp://gong2.nso.edu{gong_dir}/{fname}",
                            local_gong_dir, fname)

    ftp.quit()
    res = dl.download()
    if len(res.errors):
        print(res.errors)


def get_solis_maps():
    """
    Get all available SOLIS Carrington rotation synoptic maps.
    """
    to_dl = []
    solis_dir = local_dir / 'solis'

    with FTP('solis.nso.edu', user='anonymous') as ftp:
        print('Getting file list...')
        ftp.cwd('/integral/kbv7g')
        files = ftp.nlst()
        for fname in files:
            if fname[-2:] == 'gz':
                local_file = solis_dir / fname
                if not local_file.exists():
                    with open(local_file, "wb") as file:
                        print(fname)
                        # use FTP's RETR command to download the file
                        ftp.retrbinary(f"RETR {fname}", file.write)


def get_hmi_maps():
    from sunpy.net import Fido, attrs as a
    import sunpy.map

    series = a.jsoc.Series('hmi.synoptic_mr_polfil_720s')
    # Time doesn't matter in the search, but have to provide it to sunpy for
    # some reason
    time = a.Time('2010/01/01', '2010/01/01')

    result = Fido.search(time, series, a.jsoc.Notify(jsoc_user))
    print(result)

    result = Fido.fetch(result, path=local_dir / 'hmi', max_conn=1)
    for error in result.errors:
        print(error[1], error[2])


if __name__ == '__main__':
    # print('Getting HMI maps')
    # get_hmi_maps()
    print('Getting GONG maps')
    get_gong_maps(2021)
    # for i in range(2020, 2022):
    #     get_gong_maps(i)

    # print('Getting mdi maps')
    # get_mdi_maps()
