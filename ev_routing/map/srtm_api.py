import os
import requests
from zipfile import ZipFile


class SRTMAPI:

    STRM3_URL = 'https://dds.cr.usgs.gov/srtm/version2_1/SRTM3'

    SRTMAPI_DIR = os.environ['HOME'] + '/.srtm_api'

    STRM3_REGIONS = [
        # TODO: Complete this list
        {'lon': (-15, 180), 'lat': (35, 61), 'code': 'Eurasia' },
        {'lon': (60, 180), 'lat': (-10, 35), 'code': 'Eurasia' },
        {'lon': (-26, 60), 'lat': (-35, 35), 'code': 'Africa' },
    ]


    def __init__(self, area=[]):
        """
        Downloading SRTM data from usgs.gov and creating a mesh

        Parameter
        area: (bl_lat, bl_on, tr_lat, tr_lon), bl: bottom left, tr: top right
        """

        # Create map_api config directory
        if not 'HOME' in os.environ:
            return

        if not os.path.exists(self.SRTMAPI_DIR):
            os.makedirs(self.SRTMAPI_DIR)

        self.region = {
            'bottom_left': {'lat': area[0], 'lon': area[1]},
            'top_right': {'lat': area[2], 'lon': area[3]}
        }

        self._download_are()


    def _download_are(self):
        """
        Downloadin STRM3 hgt files
        """

        bl_lat = int(self.region['bottom_left']['lat'])
        bl_lon = int(self.region['bottom_left']['lon'])
        tr_lat = int(self.region['top_right']['lat'])
        tr_lon = int(self.region['top_right']['lon'])

        for lon in range(bl_lon, tr_lon + 1):
            for lat in range(bl_lat, tr_lat + 1):
                regionname = self._get_region_code(lon, lat)

                dirname = self.SRTMAPI_DIR + '/' + regionname
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                lon_tag = "%s%03d" % ('E' if lon > 0 else 'W', abs(lon))
                lat_tag = "%s%02d" % ('N' if lat > 0 else 'S', abs(lat))

                filename = lat_tag + lon_tag + '.hgt'
                filepath = dirname + '/' + filename

                if os.path.exists(filepath):
                    continue

                url = self.STRM3_URL + '/' + regionname + '/' + filename + '.zip'
                hgt = requests.get(url)

                zipfile = dirname + '/' + filename + '.zip'
                open(zipfile, 'wb').write(hgt.content)

                hgtzip = ZipFile(zipfile, 'r')
                hgtzip.extractall(dirname)
                hgtzip.close()


    def _get_region_code(self, lon, lat):
        """
        Getting the region name based on (lon, lat)
        """
        for region in self.STRM3_REGIONS:
            if lon >= region['lon'][0] and lon <= region['lon'][1]:
                if lat >= region['lat'][0] and lat <= region['lat'][1]:
                    return region['code']

        raise RuntimeError('Region not found!', lon, lat)
