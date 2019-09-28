import numpy as np
import time
from .map_api.map_api import MapAPI


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
        self.v = {}
        self.e = {}

        self.map_center = map.scope['center']

        # TODO: Move this to MapAPI
        for i, v in enumerate( map.nodes ):
            self.v[i] = {
                'lat': v['lat'], 'lon': v['lon'], 'incoming': [], 'outgoing': []
            }

        for i, e in enumerate( map.edges ):
            self.e[i] = { 'u': e['u'], 'v': e['v'], 'cost': e['cost'] }
            self.v[e['u']]['outgoing'].append( i )
            self.v[e['v']]['incoming'].append( i )


    def dijkstra( self, s, t, bs, M=float('inf') ):
        """
        EV Dijkstra Algorithm

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        bs -- charging level at start node
        M -- maximum charge level
        """

        SoC = {}
        for i, v in enumerate(self.v.values()):
            SoC[i] = {'b':float('-inf'), 'prev': -1}

        def f_e ( bu, c):
            bv = bu - c
            if bv < 0: return float('-inf')
            if bv > M: return M
            return bv

        SoC[s]['b'] = bs
        Q = { s:bs }

        target_reached = False

        while len(Q) > 0:
            bu = max(Q.values())

            for q in list(Q):
                if Q[q] == bu:
                    u = q

            SoC[u]['b'] = Q.pop( u )

            for key_e in self.v[u]['outgoing']:
                e = self.e[key_e]
                v = e['v']
                c = e['cost']
                bv = SoC[v]['b']
                bv_new = f_e(bu, c)

                if bv_new > bv:
                    Q[v] = bv_new
                    SoC[v]['b'] = bv_new
                    SoC[v]['prev'] = u

                if v == t:
                    target_reached = True
                    break

            if target_reached: break


        trace = [ t ]

        v = t
        while v != s:
            trace.insert(0, SoC[v]['prev'])
            v = SoC[v]['prev']

        return SoC[t], SoC, trace
