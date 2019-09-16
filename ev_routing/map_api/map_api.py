import overpy
import numpy as np

from math import *
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

    NODES_DTYPE = [
        ('id', np.int64),
        ('lat', np.float64),
        ('lon', np.float64)
    ]

    EDGES_DTYPE = [
        ('u', np.int64),
        ('v', np.int64),
        ('cost', np.float64)
    ]

    MAPAPI_DIR = os.environ['HOME'] + '/.map_api'


    def __init__ ( self, area=[] ):
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

        if not os.path.exists( self.MAPAPI_DIR ):
            os.makedirs( self.MAPAPI_DIR)


        # Info about the scope of the map
        self.scope = {
            'area': area,
            'bottom_left': ( area[0], area[1] ),
            'top_right':  ( area[2], area[3] ),
            'center': ( (area[2] - area[0]) / 2, (area[3] - area[1]) / 2 )
        }


        # Check if we have already downloaded the map
        if self._load_nodes_and_edges_from_disk():
            return


        # OpenStreetMap Query
        osm_query = self._create_osm_query()
        self.response = api.query( osm_query )


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

            for u, v in zip( w.nodes[:-1], w.nodes[1:] ):
                id1 = np.searchsorted(self.nodes['id'], u.id)
                id2 = np.searchsorted(self.nodes['id'], v.id)
                cost = self._cost((float(u.lat), float(u.lon)), (float(v.lat), float(v.lon)))

                self.edges[i] = (id1, id2, cost)
                i += 1


        # Save data on disk
        self._save_nodes_and_edges_to_disk()



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



    def _create_osm_query ( self ):
        """
        Create OpenStreetMap query to retreive all nodes and edges within
        the given area

        Return:
        query -- string including filters
        """

        way_types = '["highway"~"^(' + '|'.join(self.OSM_STREET_TAGS) + ')$"]'

        query = 'node(' + ','.join([str(i) for i in self.scope['area']]) + ');'
        query += 'way' + way_types + '(bn);( ._; >; );'
        query += 'out;'

        return query



    def _load_nodes_and_edges_from_disk ( self ):
        """
        Load nodes and edges if they have already downloaded on disk

        Return:
        success -- boolean
        """

        nodes_file, edges_file = self._nodes_and_edges_filenames()

        if os.path.isfile( nodes_file ) and os.path.isfile( edges_file ):
            print('loading...')
            self.nodes = np.load( nodes_file )
            self.edges = np.load( edges_file )

            return True

        return False


    def _save_nodes_and_edges_to_disk ( self ):
        """
        Saving downloaded nodes and edges under this path: ~/.ev_routing
        """

        nodes_file, edges_file = self._nodes_and_edges_filenames()

        np.save( nodes_file, self.nodes )
        np.save( edges_file, self.edges )



    def _nodes_and_edges_filenames ( self ):
        """
        Crreating filename for nodes and edges to be read or saved on disk

        Return:
        nodes_filename --
        edges_filename --
        """

        basename = '-'.join([ str(a) for a in self.scope['area'] ]).replace('.', '_')
        nodes_filename = self.MAPAPI_DIR + '/' + basename + '-nodes.npy'
        edges_filename = self.MAPAPI_DIR + '/' + basename + '-edges.npy'

        return nodes_filename, edges_filename
