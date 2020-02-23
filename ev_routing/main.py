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

        self.map_center = self.map.scope['center']


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





    def fw_profile(self, stations, M):
        """
        Args:
        stations: list of charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        l = self._soc_initialise(stations, M)

        # New set of break points after linking two paths
        l_new = []

        def f(break_points, ic):
            """
            Args:
            break_points: List of break points and their final charges
            ic: Inital charge
            """
            I = [bp['point'][0] for bp in break_points] # Initial charge
            F = [bp['point'][1] for bp in break_points] # Final charge
            S = [bp['slope'] for bp in break_points] # Right-side slope

            for i in range(len(I) - 1):
                if I[i] <= ic < I[i+1]:
                    if S[i] == 0:
                        return F[i]
                    else:
                        return ic - I[i] + F[i]


        n = len(stations)

        for k in range(n):
            for i in range(n):
                l_ik = l[i][k]

                ik_maps = []
                for ik in l_ik:
                    ik_maps.append({
                        'domain': (ik['point'][0], ik['point'][0] + ik['xlength']),
                        'range': (ik['point'][1], ik['point'][1] + ik['slope'] * ik['xlength']),
                    })

                for j in range(n):
                    l_kj = l[k][j]

                    for ik in l_ik:
                        l_new.append(
                            self._soc_segment((ik['point'][0], f(l_kj, ik['point'][1])), None, None)
                        )

                    for kj in l_kj:
                        for ik_map in ik_maps:
                            if ik_map['range'][0] <= kj['point'][0] < ik_map['range'][1]:
                                l_new.append(
                                    self._soc_segment((ik_map['domain'][0] , kj['point'][1]), None, None)
                                )
                                break

                    # Removing duplicated element from l_new
                    l_new = self._soc_remove_unnecessary_break_points(l_new)


    def _soc_remove_unnecessary_break_points(self, l):
        """
        Removeing break points with the same x but different ys

        Args:
        l: List of break points after linking
        """
        l_ikj = [l[0]]

        for bp in l[1:]:
            found = False

            for i in range(len(l_ikj)):
                ikj = l_ikj[i]
                if ikj['point'][0] == bp['point'][0]:
                    found = True
                    if bp['point'][1] > ikj['point'][1]:
                        l_ikj[i] = bp
            if not found:
                l_ikj.append(bp)

        return l_ikj


    def _soc_initialise(self, stations, M):
        """
        Args:
        stations: list of charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        n = len(stations)
        l = []

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append([
                        self._soc_segment((0, 0), 1, 0),
                        self._soc_segment((M, M), 0, 0),
                    ])
                else:
                    e = self.map.is_connected(stations[i], stations[j])
                    if e:
                        row.append(self._set_of_break_points(e, M))
                    else:
                        row.append([
                            self._soc_segment((0, float('-inf')), 0, 0),
                            self._soc_segment((M, float('-inf')), 0, 0),
                        ])

            l.append(row)

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
            return [
                self._soc_segment((0, -c), 1, M + c),
                self._soc_segment((M + c, M), 0, -c),
                self._soc_segment((M, M), 0, 0),
            ]
        else:
            return [
                self._soc_segment((c, 0), 1, M-c),
                self._soc_segment((M, M - c), 1, 0),
            ]

    def _soc_segment(self, point, slope, xlength):
        """
        Args:
        point: Starting point of the segment
        slope: Slope of the segment
        xlength: Projected length of the segment on x-axis (initial charge axis)
        """
        return {
            'point': point,
            'slope': slope,
            'xlength': xlength,
        }
