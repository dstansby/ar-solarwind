import numpy as np
from sunpy.net import attrs as a
from sunpy.net import Fido


for year in range(1990, 1996):
    tstart = f'{year}/01/01 00:00:00'
    tend = f'{year+1}/01/01 00:00:00'

    print(f'Searching for {year}')
    result = Fido.search(a.Time(tstart, tend),
                         a.hek.EventType('AR'),
                         a.hek.FRM.Name == 'NOAA SWPC Observer')
    try:
        df = result['hek'][['event_starttime', 'hgc_x', 'hgc_y']].to_pandas()
    except KeyError:
        print(f'No data available for {year}')
        continue
    df = df.set_index('event_starttime')
    df.to_csv(f'ar_data_{year}.txt')
