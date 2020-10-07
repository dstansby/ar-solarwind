"""
Custom `sunpy.map.GenericMap` sub-classes for different magnetogram sources.
"""
from astropy.time import Time
import astropy.units as u
import numpy as np
import sunpy.map


class SOLISSynopticMap(sunpy.map.GenericMap):
    def __init__(self, data, header, **kwargs):
        # Fix coordinate system stuff
        if 'cunit2' in header and header['cunit2'] == 'sinlat':
            header['cunit2'] = 'deg'
            header['cdelt2'] = header['cdelt2'] * 180 / np.pi
        if 'cunit1' in header and header['cunit1'] == 'degree':
            header['cunit1'] = 'deg'
        if 'hglt_obs' not in header:
            header.update(_earth_obs_coord_meta(header['date-obs']))
        header.pop('CROTA1A', None)
        super().__init__(data, header, **kwargs)

    @classmethod
    def is_datasource_for(cls, data, header, **kwargs):
        """Determines if header corresponds to a SOLIS map."""
        return str(header.get('TELESCOP', '')).endswith('SOLIS')


def _observer_coord_meta(observer_coord):
    """
    Convert an observer coordinate into FITS metadata.
    """
    new_obs_frame = sunpy.coordinates.HeliographicStonyhurst(
        obstime=observer_coord.obstime)
    observer_coord = observer_coord.transform_to(new_obs_frame)

    new_meta = {}
    new_meta['hglt_obs'] = observer_coord.lat.to_value(u.deg)
    new_meta['hgln_obs'] = observer_coord.lon.to_value(u.deg)
    new_meta['dsun_obs'] = observer_coord.radius.to_value(u.m)
    return new_meta


def _earth_obs_coord_meta(obstime):
    """
    Return metadata for an Earth obeserver coordinate.
    """
    return _observer_coord_meta(sunpy.coordinates.get_earth(obstime))
