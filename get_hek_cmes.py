import numpy as np
from sunpy.net import attrs as a
from sunpy.net import Fido


for year in range(1996, 2021):
    tstart = f'{year}/01/01 00:00:00'
    tend = f'{year+1}/01/01 00:00:00'
    event_type = 'CE'

    print(f'Searching for {year}')
    result = Fido.search(a.Time(tstart, tend), a.hek.EventType(event_type))
    starttime = result['hek']['event_starttime']
    np.savetxt(f'CME_data/{year}.txt', starttime.data, fmt='%s')
