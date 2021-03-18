"""
A class for working with a single magnetogram.
"""
import pathlib
from functools import cached_property
import numpy as np
import warnings

from astropy.coordinates import SkyCoord
import astropy.constants as const
import astropy.units as u
import sunpy.map
import sunpy.coordinates.sun
from sunpy.time import parse_time
from astropy.time import Time
import pfsspy
import pfsspy.tracing
import pfsspy.utils

import map


class MagnetogramFactory:
    def __new__(self, filepath, nr, rss, nlon, nlat, source):
        try:
            return sources[source](filepath, nr, rss, nlon, nlat)
        except KeyError:
            raise RuntimeError(f"No magnetogram source registered for {source}")


class Magnetogram:
    def __init__(self, filepath, nr, rss, nlon, nlat):
        """
        Parameters
        ----------
        filepath :
            Path to the magnetogram file
        nr : int
            Number of radial grid points to use in PFSS solution.
        rss : float
            Source surface radius to use in PFSS solution.
        nlon : int
            Number of points in longitude for tracing seeds.
        nlat : int
            Number of points in lattitude for tracing seeds.
        """
        if isinstance(filepath, sunpy.map.GenericMap):
            self.m = filepath
        else:
            self.m = sunpy.map.Map(filepath)
        self.nr = nr
        self.rss = rss
        self.nlon = nlon
        self.nlat = nlat

        # Set some helpful methods from the map
        self.peek = self.m.peek

    @property
    def data(self):
        return self.m.data

    @property
    def date(self):
        return self.m.date

    @cached_property
    def pfss_input(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return pfsspy.Input(self.m, self.nr, self.rss)

    @cached_property
    def pfss_output(self):
        return pfsspy.pfss(self.pfss_input)

    def fline_seeds(self, radius):
        """
        Create a grid of field line seeds, equally spaced on a CEA projection.

        Parameters
        ----------
        nlon : int
            Number of points in longitude.
        nlat : int
            Number of points in lattitude.
        """
        lat = (np.arccos(np.linspace(-1, 1, self.nlat + 1, endpoint=True)) - np.pi / 2) * u.rad
        lat = (lat[1:] + lat[:-1]) / 2
        lon = np.linspace(0, 360, self.nlon + 1, endpoint=True) * u.deg
        lon = (lon[1:] + lon[:-1]) / 2
        lon, lat = np.meshgrid(lon, lat, indexing='ij')
        self.source_surf_seeds = SkyCoord(radius=radius, lon=lon.ravel(),
                                          lat=lat.ravel(),
                                          frame=self.m.coordinate_frame)
        return self.source_surf_seeds

    @cached_property
    def flines(self):
        tracer = pfsspy.tracing.FortranTracer(max_steps=1000)
        radius = self.rss * const.R_sun
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            traced = tracer.trace(self.fline_seeds(radius), self.pfss_output)
        return traced

    @cached_property
    def fline_feet_coords(self):
        """
        Solar endpoints of traced field line seeds.
        """
        open_flines = self.flines.open_field_lines
        return open_flines.solar_feet

    @cached_property
    def b_at_feet(self):
        """
        Magnetic field values at solar feet.
        """
        return sunpy.map.sample_at_coords(self.m, self.fline_feet_coords)

    @cached_property
    def b_at_ss(self):
        """
        Magnetic field values at the source surface.
        """
        all_b = sunpy.map.sample_at_coords(self.pfss_output.source_surface_br,
                                           self.source_surf_seeds)
        # Only want to save source surface values of open field lines
        return all_b[self.is_open_fline]

    @cached_property
    def is_open_fline(self):
        """
        1 if open, 0 if closed field line.
        """
        return self.flines.connectivities.astype(bool)

    @cached_property
    def open_field_solar_surface_coords(self):
        """
        Trace a regular grid of seeds from the solar surface, and return the
        seed coordinates of the open field lines.
        """
        seeds = self.fline_seeds(1 * const.R_sun)
        tracer = pfsspy.tracing.FortranTracer(max_steps=2000)
        flines = tracer.trace(seeds, self.pfss_output)
        open_flines = flines.open_field_lines
        return open_flines.solar_feet

    @cached_property
    def open_field_solar_surface_b(self):
        return sunpy.map.sample_at_coords(
            self.m, self.open_field_solar_surface_coords)


class HMIMagnetogram(Magnetogram):
    def __init__(self, filepath, nr, rss, nlon, nlat):
        super().__init__(filepath, nr, rss, nlon, nlat)
        self.m.meta['cunit1'] = 'deg'
        self.m.meta['cunit2'] = 'deg'
        # Since, this map uses the cylindrical equal-area (CEA) projection,
        # the spacing should be modified to 180/pi times the original value
        # Reference: Section 5.5, Thompson 2006
        self.m.meta['cdelt2'] = 180 / np.pi * self.m.meta['cdelt2']
        self.m.meta['cdelt1'] = np.abs(self.m.meta['cdelt1'])
        self.m.meta.pop('CRDER1')
        self.m.meta.pop('CRDER2')
        self.m.meta['date-obs'] = Time.strptime(self.m.meta['t_start'], '%Y.%m.%d_%H:%M:%S_TAI').isot
        self.m = self.m.resample([360, 180] * u.pix)


class GONGMagnetogram(Magnetogram):
    def __init__(self, filepath, nr, rss, nlon, nlat):
        super().__init__(filepath, nr, rss, nlon, nlat)
        self.m._data = br = np.roll(self.m.data, self.m.meta['CRVAL1'] + 180, axis=1)
        self.m.meta['CRVAL1'] = 180


class KPVTMagnetogram(Magnetogram):
    def __init__(self, filepath, nr, rss, nlon, nlat):
        data, header = sunpy.io.fits.read(filepath)[0]
        crot = int(pathlib.Path(filepath).name[1:5])
        date = sunpy.coordinates.sun.carrington_rotation_time(crot)
        header = pfsspy.utils.carr_cea_wcs_header(date.isot, data.shape[::-1])
        m = sunpy.map.Map(data, header)
        super().__init__(m, nr, rss, nlon, nlat)


class MDIMagnetogram(Magnetogram):
    def __init__(self, filepath, nr, rss, nlon, nlat):
        super().__init__(filepath, nr, rss, nlon, nlat)
        self.m.meta['CTYPE1'] = 'CRLN-CEA'
        self.m.meta['CTYPE2'] = 'CRLT-CEA'
        self.m.meta['CDELT1'] = np.abs(self.m.meta['CDELT1'])
        self.m.meta['CDELT2'] = 180 / np.pi * self.m.meta['CDELT2']
        self.m.meta['CRVAL1'] = 0.0
        self.m.meta['CUNIT1'] = 'deg'
        self.m.meta['CUNIT2'] = 'deg'
        self.m.meta['date-obs'] = parse_time(self.m.meta['t_start']).isot
        self.m = self.m.resample([360, 180] * u.pix)


sources = {'gong': GONGMagnetogram,
           'solis': Magnetogram,
           'hmi': HMIMagnetogram,
           'kpvt': KPVTMagnetogram,
           'mdi': MDIMagnetogram}
