from .srtm3_api import SRTM3API

import overpy

from math import sin, cos, atan2, sqrt
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

    def __init__(self, area=[], testing=False):
        """
        Initializing OpenStreetMapAPI object

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)
        testing -- returns the test graph


        Example
        >>> map = MapAPI( [ 52.50, 13.37, 52.53, 13.40 ] )
        """
        self.v = {}
        self.e = {}

        if testing:
            area = [52.51, 13.373, 52.52, 13.401]

        # Create map_api config directory
        if 'HOME' not in os.environ:
            return

        if not os.path.exists(self.MAPAPI_DIR):
            os.makedirs(self.MAPAPI_DIR)

        # Info about the scope of the map
        self.scope = {
            'area': area,
            'bottom_left': (area[0], area[1]),
            'top_right': (area[2], area[3]),
            'center': ((area[2] + area[0]) / 2, (area[3] + area[1]) / 2)
        }

        if testing:
            self.v = self.testing_vertices(area)
            self.e = self.testing_edges()
            return

        # Loading/downloadin elevations
        SRTM = SRTM3API(area)

        # Check if we have already downloaded the map
        if self._load_vertices_and_edges_from_disk():
            return

        # OpenStreetMap Query
        self.response = api.query(self._osm_query_string())

        i = 0
        for w in self.response.ways:
            if len(w.nodes) < 2:
                continue

            for u, v in zip(w.nodes[:-1], w.nodes[1:]):
                if u.id not in self.v:
                    self.v[u.id] = self._new_vertex(u.id, u.lat, u.lon)
                    self.v[u.id]['elev'] = SRTM.elevation(u.lon, u.lat)

                if v.id not in self.v:
                    self.v[v.id] = self._new_vertex(v.id, v.lat, v.lon)
                    self.v[v.id]['elev'] = SRTM.elevation(u.lon, u.lat)

                self.e[i] = self._new_edge(i, u.id, v.id)

                self.v[u.id]['outgoing'].append(i)
                self.v[v.id]['incoming'].append(i)

                if 'oneway' in w.tags and w.tags['oneway'] == 'yes':
                    i += 1
                else:
                    self.e[i + 1] = self._new_edge(i + 1, v.id, u.id)
                    self.v[v.id]['outgoing'].append(i + 1)
                    self.v[u.id]['incoming'].append(i + 1)
                    i += 2

        # Save data on disk
        self._save_vertices_and_edges_to_disk()

        del SRTM

    def connected(self, i, j):
        """
        Check if two nodes with ids i and j are connected

        Args:
        i: Id of the first node
        j: Id of the second node

        Return:
        if found, it returns the edge connecting node i to node j
        if not, returns None
        """
        u = self.v[i]

        for eid in u['outgoing']:
            if self.e[eid]['v'] == j:
                return self.e[eid]

        return None

    def _new_vertex(self, id, lat, lon):
        """Generating and returning a new vertex object"""
        return {
            'id': id,
            'lat': float(lat),
            'lon': float(lon),
            'elev': 0.0,  # Not safe
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
                (self.v[uid]['lat'], self.v[uid]['lon'], self.v[uid]['elev']),
                (self.v[vid]['lat'], self.v[vid]['lon'], self.v[vid]['elev'])
            )
        }

    def _cost(self, p1, p2, kappa=0.02, lmbda=1, mu=0.25):
        """
        Calculating the cost of each edge

        Keyword arguments:
        p1 -- 1st point tuple (lat, lon, elev)
        p2 -- 2nd point tuple (lat, lon, elev)
        kappa -- (from Moritz Baum 2017, p38)
        lmbda -- (lambda) (from Moritz Baum 2017, p38)
        mu -- (from Moritz Baum 2017, p38)
        """
        dlat = p2[0] - p1[0]
        dlon = p2[1] - p1[1]
        a = (sin(dlat / 2)) ** 2 + cos(p1[0]) * cos(p1[0]) * (sin(dlon / 2)) ** 2
        l_e = 6.378e6 * 2 * atan2(sqrt(a), sqrt(1 - a))

        h_u = p1[2]
        h_v = p2[2]

        if h_v - h_u >= 0:
            c_e = (kappa * l_e) + lmbda * (h_v - h_u)
        else:
            c_e = (kappa * l_e) + mu * (h_v - h_u)

        return c_e

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

        base = '-'.join([str(a) for a in self.scope['area']]).replace('.', '_')
        vertices = self.MAPAPI_DIR + '/' + base + '-vertices_v1.pickle'
        edges = self.MAPAPI_DIR + '/' + base + '-edges_v1.pickle'

        return vertices, edges

    def testing_vertices(self, area):
        lat0 = area[0]
        dlat = (area[2] - area[0]) / 5

        lon0 = area[1]
        dlon = (area[3] - area[1]) /6

        v = {
            0: self._new_vertex(0, lat0 + 2 * dlat, lon0 + 2 * dlon),
            1: self._new_vertex(1, lat0 + 3 * dlat, lon0 + 1 * dlon),
            2: self._new_vertex(2, lat0 + 4 * dlat, lon0 + 3 * dlon),
            3: self._new_vertex(3, lat0 + 3 * dlat, lon0 + 2 * dlon),
            4: self._new_vertex(4, lat0 + 0 * dlat, lon0 + 1 * dlon),
            5: self._new_vertex(5, lat0 + 1 * dlat, lon0 + 5 * dlon),
            6: self._new_vertex(6, lat0 + 1 * dlat, lon0 + 2 * dlon),
            7: self._new_vertex(7, lat0 + 3 * dlat, lon0 + 5 * dlon),
            8: self._new_vertex(8, lat0 + 2 * dlat, lon0 + 4 * dlon),
            9: self._new_vertex(9, lat0 + 0 * dlat, lon0 + 0 * dlon),
        }

        v[0]['incoming'] = [8, 3, 1, 6]
        v[0]['outgoing'] = [8, 3, 6]
        v[1]['incoming'] = [3]
        v[1]['outgoing'] = [5, 2]
        v[2]['incoming'] = []
        v[2]['outgoing'] = [3]
        v[3]['incoming'] = [1, 2, 0]
        v[3]['outgoing'] = [0, 1]
        v[4]['incoming'] = [6, 9]
        v[4]['outgoing'] = [6, 9]
        v[5]['incoming'] = [8]
        v[5]['outgoing'] = [8]
        v[6]['incoming'] = [0, 4]
        v[6]['outgoing'] = [0, 4]
        v[7]['incoming'] = [8]
        v[7]['outgoing'] = [8]
        v[8]['incoming'] = [7, 5, 0]
        v[8]['outgoing'] = [7, 5, 0]
        v[9]['incoming'] = [4]
        v[9]['outgoing'] = [4]

        return v

    def testing_edges(self):
        e = {
            0: self._new_edge(0, 2, 3),
            1: self._new_edge(1, 1, 3),
            2: self._new_edge(2, 0, 3),
            3: self._new_edge(3, 3, 1),
            4: self._new_edge(4, 3, 0),
            5: self._new_edge(5, 1, 0),
            6: self._new_edge(6, 8, 0),
            7: self._new_edge(7, 0, 8),
            8: self._new_edge(8, 7, 8),
            9: self._new_edge(9, 8, 7),
            10: self._new_edge(10, 8, 5),
            11: self._new_edge(11, 5, 8),
            12: self._new_edge(12, 0, 6),
            13: self._new_edge(13, 6, 0),
            14: self._new_edge(14, 4, 6),
            15: self._new_edge(15, 6, 4),
            16: self._new_edge(16, 9, 4),
            17: self._new_edge(17, 4, 9),
        }

        e[0]['cost'] = 1
        e[1]['cost'] = 2
        e[2]['cost'] = 2
        e[3]['cost'] = 2
        e[4]['cost'] = 2
        e[5]['cost'] = 5
        e[6]['cost'] = 3
        e[7]['cost'] = 3
        e[8]['cost'] = 5
        e[9]['cost'] = 5
        e[10]['cost'] = 5
        e[11]['cost'] = 5
        e[12]['cost'] = 1
        e[13]['cost'] = 1
        e[14]['cost'] = 2
        e[15]['cost'] = 2
        e[16]['cost'] = 1
        e[17]['cost'] = 1

        return e
