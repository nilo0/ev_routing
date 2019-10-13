import time
from .map.map_api import MapAPI


class EVRouting:
    """Electrical Vehicles (EV) Routing Class"""


    def __init__( self, area ):
        """
        Initializing EVRouting by:
        - loading nodes and edges based on a given region
        - finding incoming and outgoing edges

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)

        Example
        >>> from ev_routing import EVRouting
        >>> evr = EVRouting([ 52.50, 13.37, 52.53, 13.40 ])
        """

        map = MapAPI( area )
        self.v = map.v
        self.e = map.e

        self.map_center = map.scope['center']


    def dijkstra( self, s, t, bs, M=float('inf') ):
        """
        EV Dijkstra Algorithm

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        bs -- charging level at start node
        M -- maximum charge level
        """

        def f_e ( bu, c):
            bv = bu - c
            if bv < 0: return float('-inf')
            if bv > M: return M
            return bv

        def default_SoC ( b=float('-inf'), prev=-1 ):
            return { 'b': b, 'prev': prev }

        Q = { s: bs }

        SoC = {}
        SoC[s] = default_SoC( bs )

        target_reached = False

        while len(Q) > 0:
            u = max( Q, key=lambda k: Q[k] )
            bu = Q.pop(u)

            for eid in self.v[u]['outgoing']:
                e = self.e[eid]
                v = e['v']
                c = e['cost']
                bv = SoC[v]['b'] if v in SoC else float('-inf')
                bv_new = f_e(bu, c)

                if bv_new > bv:
                    Q[v] = bv_new
                    SoC[v] = default_SoC( bv_new, u )

                if v == t:
                    print( 'Target has reached!' )
                    target_reached = True
                    break

            if target_reached: break


        if target_reached:
            trace = [ t ]

            v = t
            while v != s and v != -1:
                trace.insert(0, SoC[v]['prev'])
                v = SoC[v]['prev']

            return SoC[t], SoC, trace
        else:
            return default_SoC(), SoC, []
