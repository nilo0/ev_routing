from .map_api.map_api import MapAPI


class EVRouting:
    """Electrical Vehicles (EV) Routing Class"""

    def __init__( self, area ):
        """
        Initializing EVRouting by:
        - loading nodes and edges based on a given region
        - finding incoming and outcoming edges

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)

        Example
        >>> from ev_routing import EVRouting
        >>> evr = EVRouting([ 52.50, 13.37, 52.53, 13.40 ])
        """

        map = MapAPI( area )
        self.v = map.nodes
        self.e = map.edges


        self.outcoming = [ [] for _ in range(len(self.v)) ]
        self.incoming  = [ [] for _ in range(len(self.v)) ]

        for i, e in enumerate( self.e ):
            self.outcoming[e['n1']].append(i)
            self.incoming[e['n2']].append(i)
