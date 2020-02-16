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

        self.map = MapAPI( area )
        self.v = self.map.v
        self.e = self.map.e

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


    def _soc_initialise(self, stations, M):
        """
        Args:
        stations: list of charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        n = len(stations)
        l = [[[]]*n]*n

        for i in stations:
            for j in stations:
                e = self.map.is_connected(i, j)
                if e:
                    l[i][j] = self._set_of_break_points(e, M)
                else:
                    l[i][j] = [(0, float('-inf')), (M, float('-inf'))]

        for i in range(n):
            l[i][i] = [(0, 0), (2, 2)]

        return l


    def _set_of_break_points(self, e, M):
        """
        Calculated set of break points for a given edge and charge state

        Arguments:
        e -- a given edge (u, v, c)
        M -- Battery charge capacity
        """
        break_points = []

        c = e['cost']

        if c < 0:
            return [(0, c), (M + c, M), (M, M)]
        else:
            return [(c, 0), (M, M - c )]
