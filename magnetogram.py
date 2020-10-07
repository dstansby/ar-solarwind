"""
A class for working with a single magnetogram.
"""
from functools import cached_property
import numpy as np

from astropy.coordinates import SkyCoord
import astropy.constants as const
import astropy.units as u
import sunpy.map
import pfsspy
import pfsspy.tracing

import map


class MagnetogramFactory:
    def __new__(self, filepath, nr, rss, nlon, nlat, source):
        return sources[source](filepath, nr, rss, nlon, nlat)


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
        self.filepath = filepath
        self.m = sunpy.map.Map(filepath)
        # Roll to get in Carrington frame
        self.m._data = br = np.roll(self.m.data, self.m.meta['CRVAL1'] + 180, axis=1)
        self.m.meta['CRVAL1'] = 180
        self.nr = nr
        self.rss = rss
        self.nlon = nlon
        self.nlat = nlat

        # Set some helpful methods from the map
        self.peek = self.m.peek
        self.date = self.m.date
        self.data = self.m.data

    @cached_property
    def pfss_input(self):
        return pfsspy.Input(self.m, self.nr, self.rss)

    @cached_property
    def pfss_output(self):
        return pfsspy.pfss(self.pfss_input)

    @cached_property
    def fline_seeds(self):
        """
        Create a grid of field line seeds on the source surface, equally spaced
        on a CEA projection.

        Parameters
        ----------
        nlon : int
            Number of points in longitude.
        nlat : int
            Number of points in lattitude.
        """
        lat = (np.arccos(np.linspace(-1, 1, self.nlat)) - np.pi / 2) * u.rad
        lon = np.linspace(0, 360, self.nlon, endpoint=False) * u.deg
        lat, lon = np.meshgrid(lat, lon)
        r = self.rss * const.R_sun
        source_surf_seeds = SkyCoord(radius=r, lon=lon.ravel(),
                                     lat=lat.ravel(),
                                     frame=self.m.coordinate_frame)
        return source_surf_seeds

    @cached_property
    def fline_feet(self):
        """
        Solar endpoints of traced field line seeds.
        """
        tracer = pfsspy.tracing.FortranTracer(max_steps=2000)
        flines = tracer.trace(self.fline_seeds, self.pfss_output)
        open_flines = flines.open_field_lines
        return open_flines.solar_feet

    @cached_property
    def b_at_feet(self):
        """
        Magnetic field values at solar feet.
        """
        return sunpy.map.sample_at_coords(self.m, self.fline_feet)


class GONGMagnetogram(Magnetogram):
    def __init__(self, filepath, nr, rss, nlon, nlat):
        super().__init__(filepath, nr, rss, nlon, nlat)
        self.m._data = br = np.roll(self.m.data, self.m.meta['CRVAL1'] + 180, axis=1)
        self.m.meta['CRVAL1'] = 180


sources = {'gong': GONGMagnetogram,
           'solis': Magnetogram}
