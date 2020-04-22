import os
import requests
from zipfile import ZipFile
import numpy as np
from scipy.interpolate import interp2d


class SRTM3API:

    SRTM3_URL = 'https://dds.cr.usgs.gov/srtm/version2_1/SRTM3'
    SRTM3API_DIR = os.environ['HOME'] + '/.srtm_api'
    SRTM3_RES = 1201
    SRTM3_REGIONS = [
        # TODO: Complete this list
        {'lon': (-15, 180), 'lat': (35, 61), 'code': 'Eurasia'},
        {'lon': (60, 180), 'lat': (-10, 35), 'code': 'Eurasia'},
        {'lon': (-26, 60), 'lat': (-35, 35), 'code': 'Africa'},
    ]

    def __init__(self, area=[]):
        """
        Downloading SRTM3 data from usgs.gov and creating a mesh

        Parameter
        area: (bl_lat, bl_on, tr_lat, tr_lon), bl: bottom left, tr: top right
        """

        # Create srtm_api config directory
        if 'HOME' not in os.environ:
            return

        if not os.path.exists(self.SRTM3API_DIR):
            os.makedirs(self.SRTM3API_DIR)

        # Create region directories inside srtm_api directory
        for region in self.SRTM3_REGIONS:
            dirname = self.SRTM3API_DIR + '/' + region['code']
            if not os.path.exists(dirname):
                os.makedirs(dirname)

        xpixels = (int(area[3] - area[1]) + 1) * self.SRTM3_RES
        ypixels = (int(area[2] - area[0]) + 1) * self.SRTM3_RES

        self.data = {
            'bl': {'lat': int(area[0]), 'lon': int(area[1])},
            'tr': {'lat': int(area[2]) + 1, 'lon': int(area[3]) + 1},
            'resolution': (xpixels, ypixels),
            'mesh': np.zeros((xpixels, ypixels), dtype=np.dtype('>i2'))
        }

        self._download_area()
        self._load_hgt_data()

    def elevation(self, lon, lat, interpolate=True):
        """
        Return the elevation of a given (lon, lat) by interpolating STRM3 data

        Parameter
        lon: longitude
        lat: latitude
        interpolate: If True, uses interpolation to find the elevation
        """

        dlon = float(lon) - self.data['bl']['lon']
        dlat = float(lat) - self.data['bl']['lat']

        x = dlon * self.SRTM3_RES
        y = dlat * self.SRTM3_RES

        i = int(x)
        j = int(y)

        max_i = self.data['resolution'][0]
        max_j = self.data['resolution'][1]

        if interpolate:
            if i - 1.5 < 0 or i + 3.5 > max_i or j - 1.5 < 0 or j + 3.5 > max_j:
                raise RuntimeError('Out of range!', lon, lat)

            xi, yi = np.meshgrid(
                np.arange(i - 1.5, i + 3.5, 1.0),
                np.arange(j - 1.5, j + 3.5, 1.0))
            f = interp2d(
                xi, yi, self.data['mesh'][i-2:i+3, j-2:j+3], kind='cubic')

            return f(x, y)[0]
        else:
            if not 0 <= i < max_i or not 0 <= j < max_j:
                raise RuntimeError('Out of range!', lon, lat)

            return self.data['mesh'][i, j]

    def _download_area(self):
        """
        Downloading SRTM3 hgt files
        """
        for lon in range(self.data['bl']['lon'], self.data['tr']['lon']):
            for lat in range(self.data['bl']['lat'], self.data['tr']['lat']):
                mdata = self._get_metadata(lon, lat)

                if os.path.exists(mdata['file']['path']):
                    continue

                hgt = requests.get(mdata['url'])
                open(mdata['zip']['path'], 'wb').write(hgt.content)

                hgtzip = ZipFile(mdata['zip']['path'], 'r')
                hgtzip.extractall(mdata['directory']['path'])
                hgtzip.close()

    def _get_region_code(self, lon, lat):
        """
        Getting the region name based on (lon, lat)
        """
        for region in self.SRTM3_REGIONS:
            if lon >= region['lon'][0] and lon <= region['lon'][1]:
                if lat >= region['lat'][0] and lat <= region['lat'][1]:
                    return region['code']

        raise RuntimeError('Region not found!', lon, lat)

    def _get_metadata(self, lon, lat):
        regionname = self._get_region_code(lon, lat)

        dirpath = self.SRTM3API_DIR + '/' + regionname

        lon_tag = "%s%03d" % ('E' if int(lon) > 0 else 'W', abs(int(lon)))
        lat_tag = "%s%02d" % ('N' if int(lat) > 0 else 'S', abs(int(lat)))
        filename = lat_tag + lon_tag + '.hgt'

        return {
            'region': regionname,
            'directory': {
                'name': regionname,
                'path': dirpath
            },
            'file': {
                'name': filename,
                'path': dirpath + '/' + filename,
            },
            'zip': {
                'name': filename + '.zip',
                'path': dirpath + '/' + filename + '.zip',
            },
            'url': self.SRTM3_URL + '/' + regionname + '/' + filename + '.zip',
        }

    def _load_hgt_data(self):
        """
        Loading downloaded .hgt files into self.data
        """
        for lon in range(self.data['bl']['lon'], self.data['tr']['lon']):
            for lat in range(self.data['bl']['lat'], self.data['tr']['lat']):
                mdata = self._get_metadata(lon, lat)

                i = (lon - self.data['bl']['lon']) * self.SRTM3_RES
                i_end = i + self.SRTM3_RES

                j = (lat - self.data['bl']['lat']) * self.SRTM3_RES
                j_end = j + self.SRTM3_RES

                # We need to flip the hgt matrix along y-dir since it is
                # arranged from west to east and then **north to south**
                self.data['mesh'][i:i_end, j:j_end] = np.flip(
                    np.fromfile(
                        mdata['file']['path'],
                        np.dtype('>i2'),
                        self.SRTM3_RES*self.SRTM3_RES
                    ).reshape((self.SRTM3_RES, self.SRTM3_RES)), 1  # y-dir
                )
