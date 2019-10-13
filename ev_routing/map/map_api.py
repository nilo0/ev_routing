from .srtm3_api import SRTM3API

import overpy

from math import *
import pickle
import os


api = overpy.Overpass()


class MapAPI:
    OSM_STREET_TAGS = [
        'motorway', 'motorway_link', 'motorway_junction',
        'trunk', 'trunk_link',
        'primary', 'primary_link',
        'secondary', 'secondary_link',
        'tertiary', 'tertiary_link',
        'unclassified',
        'residential',
        'living_street',
        'service',
        'road'
    ]


    MAPAPI_DIR = os.environ['HOME'] + '/.map_api'


    def __init__(self, area=[]):
        """
        Initializing OpenStreetMapAPI object

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)


        Example
        >>> map = MapAPI( [ 52.50, 13.37, 52.53, 13.40 ] )
        """

        # Create map_api config directory
        if not 'HOME' in os.environ:
            return

        if not os.path.exists(self.MAPAPI_DIR):
            os.makedirs(self.MAPAPI_DIR)


        # Info about the scope of the map
        self.scope = {
            'area': area,
            'bottom_left': (area[0], area[1]),
            'top_right':  (area[2], area[3]),
            'center': ((area[2] + area[0]) / 2, (area[3] + area[1]) / 2)
        }


        # Loading/downloadin elevations
        SRTM = SRTM3API(area)


        # Check if we have already downloaded the map
        if self._load_vertices_and_edges_from_disk(): return

        # OpenStreetMap Query
        self.response = api.query(self._osm_query_string())

        self.v = {}
        self.e = {}

        i = 0
        for w in self.response.ways:
            if len( w.nodes ) < 2: continue

            for u, v in zip(w.nodes[:-1], w.nodes[1:]):
                if u.id not in self.v:
                    self.v[ u.id ] = self._new_vertex(u.id, u.lat, u.lon)
                    self.v[ u.id ]['elev'] = SRTM.elevation(u.lon, u.lat)

                if v.id not in self.v:
                    self.v[ v.id ] = self._new_vertex(v.id, v.lat, v.lon)
                    self.v[ v.id ]['elev'] = SRTM.elevation(u.lon, u.lat)

                self.e[i] = self._new_edge(i, u.id, v.id)

                self.v[u.id]['outgoing'].append(i)
                self.v[v.id]['incoming'].append(i)

                if 'oneway' in w.tags and w.tags['oneway'] is 'yes':
                    i += 1
                else:
                    self.e[i+1] = self._new_edge(i+1, v.id, u.id)
                    self.v[v.id]['outgoing'].append(i+1)
                    self.v[u.id]['incoming'].append(i+1)
                    i += 2


        # Save data on disk
        self._save_vertices_and_edges_to_disk()

        del SRTM



    def _new_vertex(self, id, lat, lon):
        """Generating and returning a new vertex object"""
        return {
            'id': id,
            'lat': float(lat),
            'lon': float(lon),
            'elev': 0.0, # Not safe
            'incoming': [],
            'outgoing': []
        }



    def _new_edge(self, id, uid, vid):
        """Generating and returning a new edge object"""
        return {
            'id': id,
            'u': uid,
            'v': vid,
            'cost': self._cost(
                (self.v[uid]['lat'], self.v[uid]['lon']),
                (self.v[vid]['lat'], self.v[vid]['lon'])
            )
        }



    def _cost(self, p1, p2):
        """
        Calculating the cost of each edge

        Keyword arguments:
        p1 -- 1st point tuple (lat, lon)
        p2 -- 2nd point tuple (lat, lon)
        """

        dlat = p2[0] - p1[0]
        dlon = p2[1] - p1[1]

        a = (sin(dlat / 2))**2 + cos(p1[0]) * cos(p1[0]) * (sin(dlon / 2))**2

        return 6.378e6 * 2 * atan2(sqrt(a), sqrt(1-a))



    def _osm_query_string(self):
        """
        Create OpenStreetMap query to retreive all vertices and edges within
        the given area

        Return:
        query -- string including filters
        """

        way_types = '["highway"~"^(' + '|'.join(self.OSM_STREET_TAGS) + ')$"]'

        query = 'node(' + ','.join([str(i) for i in self.scope['area']]) + ');'
        query += 'way' + way_types + '(bn);( ._; >; );'
        query += 'out;'

        return query



    def _load_vertices_and_edges_from_disk(self):
        """
        Load vertices and edges if they have already downloaded on disk

        Return:
        success -- boolean
        """

        vertices_file, edges_file = self._vertices_and_edges_filenames()

        if os.path.isfile(vertices_file) and os.path.isfile(edges_file):
            print('Loading...')

            with open(vertices_file, 'rb') as handle:
                self.v = pickle.load(handle)

            with open(edges_file, 'rb') as handle:
                self.e = pickle.load(handle)

            return True

        return False


    def _save_vertices_and_edges_to_disk(self):
        """
        Saving downloaded vertices and edges under this path: ~/.ev_routing
        """

        vertices_file, edges_file = self._vertices_and_edges_filenames()

        with open(vertices_file, 'wb') as handle:
            pickle.dump(self.v, handle, pickle.HIGHEST_PROTOCOL)

        with open(edges_file, 'wb') as handle:
            pickle.dump(self.e, handle, pickle.HIGHEST_PROTOCOL)



    def _vertices_and_edges_filenames(self):
        """
        Crreating filename for vertices and edges to be read or saved on disk

        Return:
        vertices_filename --
        edges_filename --
        """

        basename = '-'.join([ str(a) for a in self.scope['area'] ]).replace('.', '_')
        vertices_filename = self.MAPAPI_DIR + '/' + basename + '-vertices_v1.pickle'
        edges_filename = self.MAPAPI_DIR + '/' + basename + '-edges_v1.pickle'

        return vertices_filename, edges_filename
