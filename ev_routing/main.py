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


        n = len(stations)

        for k in range(n):
            for i in range(n):
                l_ik = l[i][k]

                for j in range(n):
                    l_kj = l[k][j]

                    # Linking
                    for ik in l_ik:
                        f_ikj = self._f(l_kj, ik[1])
                        if f_ikj is not None and f_ikj >= 0:
                            l_new.append(self._soc_segment(ik[0], f_ikj, ik[2]))

                    for kj in l_kj:
                        for ik1, ik2 in zip(l_ik[:-1], l_ik[1:]):
                            xlength = ik2[0] - ik1[0]
                            if ik1[1] <= kj[0] < ik1[1] + ik1[2] * xlength:
                                l_new.append(self._soc_segment(
                                    ik1[0] + (kj[0] - ik1[1]) * ik1[2], kj[1], kj[2]
                                ))

                        if kj[0] == l_id[-1][1]:
                            l_new.append(self._soc_segment(l_id[-1][0], kj[1], kj[2]))

                    # Removing duplicated element from l_new
                    l_new = self._soc_remove_repeated_break_points_sort(l_new)

                    self._soc_merge(l[i][j], l_new)


    def _soc_merge(self, l_ij, l_new, M):
        """
        Updating l_ij
        """
        do_merge = True

        # TODO: fix the condition
        # for bp in l_new:
        #     if self._f(l_ij, bp[0]) is not None and bp[1] > self._f(l_ij, bp[0]):
        #         do_merge = True

        # if not do_merge:
        #     return l_ij

        merged = [l for l in l_ij]
        for l in l_new:
            i = -1
            for mi in range(len(merged) - 1):
                if merged[mi][0] <= l[0] < merged[mi+1][0]:
                    i = mi
                    break

            if i < 0:
                break

            dx = merged[i+1][0] - merged[i][0]
            dlx = merged[i+1][0] - l[0]

            l_ij_at_l0 = self._f(l_ij, l[0])
            l_new_at_end = l[1] + l[2] * dlx
            l_ij_at_end = merged[i][1] + merged[i][2] * dx

            if l[1] <= l_ij_at_l0 and l_new_at_end <= l_ij_at_end:
                continue
            elif l[1] > l_ij_at_l0 and l_new_at_end > l_ij_at_end:
                if l[0] == merged[i][0]:
                    merged[i] = l
                    if l[1] + l[2] * dlx > M:
                        x_intersect = l[0] + l[2] * (M - l[1])
                        merged.insert(i+1, (x_intersect, M, 0))
                else:
                    merged.insert(i+1, l)
                    if l[1] + l[2] * dlx > M:
                        x_intersect = l[0] + l[2] * (M - l[1])
                        merged.insert(i+2, (x_intersect, M, 0))
            elif l[1] < l_ij_at_l0 and l_new_at_end > l_ij_at_end:
                x_intersect = l[0] + l_ij_at_l0 - l[1]
                if x_intersect == merged[i][0]:
                    del(merged[i])
                    merged.insert(i, (merged[i][0], merged[i][1], l[2]))
                else:
                    merged.insert(i+1, (x_intersect, merged[i][1], l[2]))
            else:
                print('Something\'s wrong! I should not be here!')

        return merged


    def _f(self, break_points, ic):
        """
        Args:
        break_points:
        ic:
        """
        I = [bp[0] for bp in break_points] # Initial charge
        F = [bp[1] for bp in break_points] # Final charge
        S = [bp[2] for bp in break_points] # Right-side slope

        for i1, i2, f, s in zip(I[:-1], I[1:], F[:-1], S[:-1]):
            if i1 <= ic < i2:
                if s == 0:
                    return f
                else:
                    return ic - i1 + f

        if ic == I[-1]:
            return F[-1]

        return None


    def _soc_remove_repeated_break_points_and_sort(self, l):
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
                if ikj[0] == bp[0]:
                    found = True
                    if bp[1] > ikj[1]:
                        l_ikj[i] = bp
            if not found:
                l_ikj.append(bp)

        return sorted(l_ikj, key=lambda t: t[0])


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
                        self._soc_segment(0, 0, 1),
                        self._soc_segment(M, M, 0),
                    ])
                else:
                    e = self.map.is_connected(stations[i], stations[j])
                    if e:
                        row.append(self._set_of_break_points(e, M))
                    else:
                        row.append([
                            self._soc_segment(0, float('-inf'), 0),
                            self._soc_segment(M, float('-inf'), 0),
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
                self._soc_segment(0, -c, 1),
                self._soc_segment(M + c, M, 0),
                self._soc_segment(M, M, 0),
            ]
        else:
            return [
                self._soc_segment(c, 0, 1),
                self._soc_segment(M, M - c, 0),
            ]

    def _soc_segment(self, ic, fc, slope):
        """
        Args:
        ic: Initial charge
        fc: Final charge
        slope: Slope of the segment
        """
        return (ic, fc, slope)
