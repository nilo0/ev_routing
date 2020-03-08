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



    def d_profile(self, s, t, M=float('inf')):

        """
        EV Dijkstra Profile Search

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        M -- maximum charge level
        maps the every possible initial state of charge at s to the optimal state
        of charge at target t.
        """

        f = {}
        Q = {}
        potential = self.potential()

        for vid in self.v:
            f[vid] = [(0, float('-inf'), 0 ), (M, float('-inf'), 0)]

        f[s] = [(0, 0, 1), (M, M, 0)]
        Q[s] = 0 + potential[s]

        while len(Q) > 0:
            u = min(Q, key=lambda k:Q[k])
            _ = Q.pop(u)

            for eid in self.v[u]['outgoing']:
                e = self.e[eid]
                v = e['v']
                l = []
                print('e   :', e)
                print('f[u]:', f[u])

                # if self.target_prune(v, f[v], t, f[t], M):
                #     print('target_prune', v, f[v], t, f[t])
                #     continue

                #linking SoC function of fu and fuv   break point f_u
                f_e = self._set_of_break_points(e, M)
                print('f_e :', f_e)

                for bp in f[u]:
                    f_e_at_bp = self._f(f_e, bp[1])
                    if f_e_at_bp:
                        l.append(self._soc_segment(bp[0], f_e_at_bp, bp[2]))
                print('l', l)

                for bp in f_e:
                    for b1, b2 in zip(f[u][:-1], f[u][1:]):
                        xlength = b2[0] - b1[0]
                        if b1[1] <= bp[0] < b1[1] + b1[2] * xlength:
                            # The minimum charge in f(u) for which f(f(u)) = bp[1]
                            l.append(self._soc_segment(
                                b1[0] + (bp[1] - b1[1]) * b1[2], bp[1], bp[2]
                            ))
                        if bp[0] == f[u][-1][1]:
                            l.append(self._soc_segment(f[u][-1][0], bp[1], bp[2]))
                print('l', l)
        #         # Removing duplicated element from l_new
        #         l = self._soc_remove_repeated_break_points_and_sort(l)
        #
        #         ifmerge = False
        #
        #         for bp in l:
        #             if bp[1] > self._f(f[v], bp[0]):
        #                 ifmerge = True
        #
        #         #merge break points of fu and fuv and update the key
        #         if ifmerge:
        #             f[v] = self._soc_merge(f[v], l, M)
        #             f_v = set(l).difference(set(f[v]))
        #
        #             min_list = []
        #             for bp in list(f_v):
        #                 min_list.append(bp[0] - bp[1])
        #
        #             minkey = min(min_list)
        #             Q[v] = potential[v] + minkey
        #
        return f[t]




    def target_prune(self, v, f_v, t, f_t, M):
        """
        target pruning step
        t : target
        l : f[v]
        Q : the priority queue after changing the key value of node v
        M : battery capacity
        """
        f_v.sort(key=lambda tup: tup[0])
        f_t.sort(key=lambda tup: tup[0])

        c_t = [0]
        for bp in f_t:
            consumption = bp[0] - bp[1]
            if consumption <= M:
                c_t.append(consumption)
        c_t_max = max(c_t)

        c_v  = [M]
        for bp in f_v:
            consumption = bp[0] - bp[1]
            if consumption >= 0:
                c_v.append(consumption)
        c_v_min = min(c_v)

        b_t_min = self.find_minimum_bv(f_t)
        b_v_min = self.find_minimum_bv(f_v)

        if b_v_min >= b_t_min and c_v_min >= c_t_max:
            return True

        return False



    def find_minimum_bv(self, l):
        """
        returns the min initial charge level for which f_t is not -infty
        l : f[t], list of break points of SoC function f_t b, f(b), slope_at_b)
        """
        for bp in l:
            if bp[1] >= 0:
                return bp[0]

        return 0



    def alpha(self):
        """
        alpha function returns a scalar which is used to evaluate a consistent
        potential, using elevation difference of head and tail of edges.
        """
        q_up = []
        q_down = []
        alpha_e = {}
        for eid in self.e:
            e = self.e[eid]
            u = e['u']
            v = e['v']
            if self.v[v]['elev'] - self.v[u]['elev'] != 0:
                alpha_e[eid] = e['cost'] / (self.v[v]['elev'] - self.v[u]['elev'])
                if self.v[v]['elev'] - self.v[u]['elev'] > 0:
                    q_up.append(alpha_e[eid])
                if self.v[v]['elev'] - self.v[u]['elev'] < 0:
                    q_down.append(alpha_e[eid])

        alpha_max = int(max(q_up))
        alpha_min =int(min(q_down))

        if alpha_min <= 1 <= alpha_max:
            return 1
        else:
            return 2 # TODO



    def check_alpha_true(self):
        num_edges = 0
        num_pos_cost = 0
        num_neg_cost = 0
        h_c_pos = 0
        h_c_neg = 0
        for eid in self.e:
            num_edges +=1
            e = self.e[eid]
            u = e['u']
            v = e['v']
            c = e['cost']
            h = self.v[v]['elev'] - self.v[u]['elev']
            if c > 0:
                num_pos_cost += 1
                if h == 0:
                    h_c_pos += 1
            if c < 0:
                num_neg_cost += 1
                if h == 0:
                    h_c_neg += 1
        return num_edges, num_neg_cost, num_pos_cost, h_c_pos, h_c_neg



    def potential(self):
        """
        To all nodes it assigns a consistent potential
        """
        pot = {}

        alpha = self.alpha()
        for uid in self.v:
            pot[uid] = alpha * self.v[uid]['elev']

        return pot





    def fw_profile(self, nodes, M):
        """
        Args:
        nodes: list of nodes and charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        l = self._soc_initialise(nodes, M)

        # New set of break points after linking two paths
        l_new = []


        n = len(nodes)

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

                        if kj[0] == l_id[-1][1]:   #check what this line does!!! and what is l_id
                            l_new.append(self._soc_segment(l_id[-1][0], kj[1], kj[2]))

                    # Removing duplicated element from l_new
                    l_new = self._soc_remove_repeated_break_points_and_sort(l_new)

                    ifmerge = False

                    for bp in l_new:
                        if bp[1] > self._f(l[i][j], bp[0]):
                            ifmerge = True

                    if ifmerge:
                        l[i][j] = self._soc_merge(l[i][j], l_new, M)


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
                continue

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

        # update last break point

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
        l_ikj = [l[0]]      #is it really a list of list? like [[a, b, c, ... ,z]] where l[0] is [a, b, ...,z]

        for bp in l[1:]:
            found = False

            for i in range(len(l_ikj)):   #then the len(l_ikj) should be 1!!!
                ikj = l_ikj[i]
                if ikj[0] == bp[0]:
                    found = True
                    if bp[1] > ikj[1]:
                        l_ikj[i] = bp
            if not found:
                l_ikj.append(bp)

        return sorted(l_ikj, key=lambda t: t[0])


    def _soc_initialise(self, nodes, M):
        """
        Args:
        nodess: list of nodes and charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        n = len(nodes)
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
                    e = self.map.is_connected(nodes[i], nodes[j])
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
        Calculated set of break points for a given edge and battery capacity

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
