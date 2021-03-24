from datetime import datetime
import glob

from parfive import Downloader
import pandas as pd


def dl_lasco_downtime():
    dl = Downloader()
    base_url = 'https://cdaw.gsfc.nasa.gov/CME_list/UNIVERSAL/downtime'
    for y in range(1995, 2021):
        for m in range(1, 13):
            dl.enqueue_file(f'{base_url}/c2dt_{y}{m:02}.txt',
                            path='lasco_downtime/')

    dl.download()
