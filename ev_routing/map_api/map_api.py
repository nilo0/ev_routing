import overpy
from math import *
import numpy as np


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

    NODES_DTYPE = [
        ('id', np.int64),
        ('lat', np.float64),
        ('lon', np.float64)
    ]

    EDGES_DTYPE = [
        ('n1', np.int64),
        ('n2', np.int64),
        ('cost', np.float64)
    ]


    def __init__ ( self, area=[] ):
        """
        Initializing OpenStreetMapAPI object

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)


        Example
        >>> map = MapAPI( [ 52.50, 13.37, 52.53, 13.40 ] )
        """

        self.scope = {
            'bottom_left': ( area[0], area[1] ),
            'top_right':  ( area[2], area[3] ),
            'center': ( (area[2] - area[0]) / 2, (area[3] - area[1]) / 2 )
        }


        filters = '["highway"~"^(' + '|'.join(self.OSM_STREET_TAGS) + ')$"]'
        query = 'node(' + ','.join([str(i) for i in area]) + ');way' + filters + '(bn);( ._; >; );out;'
        self.response = api.query(query)


        # Nodes
        self.nodes = np.array( [
            (n.id, float(n.lat), float(n.lon)) for n in self.response.nodes
        ], dtype=self.NODES_DTYPE) # It's already sorted


        # Edges
        n_edges = sum([ len(w.nodes) - 1 for w in self.response.ways ])
        self.edges = np.zeros( (n_edges), dtype=self.EDGES_DTYPE)

        i = 0
        for w in self.response.ways:
            if ( len( w.nodes ) < 2 ): continue

            for n1, n2 in zip( w.nodes[:-1], w.nodes[1:] ):
                id1 = np.searchsorted(self.nodes['id'], n1.id)
                id2 = np.searchsorted(self.nodes['id'], n2.id)
                cost = self._cost((float(n1.lat), float(n1.lon)), (float(n2.lat), float(n2.lon)))

                self.edges[i] = (id1, id2, cost)
                i += 1


    def _cost (self, p1, p2):
        """
        Calculating the cost of each edge

        Keyword arguments:
        p1 -- 1st point tuple (lat, lon)
        p2 -- 2nd point tuple (lat, lon)
        """

        dlat = p2[0] - p1[0]
        dlon = p2[1] - p1[1]

        a = (sin(dlat / 2))**2 + cos(p1[0]) * cos(p1[0]) * (sin(dlon / 2))**2

        return 6.378e6 * 2 * atan2( sqrt(a), sqrt(1-a) )
