import time
from .map.map_api import MapAPI
from copy import deepcopy

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

                l.extend(self.link_step1(f[u], f_e))
                l.extend(self.link_step2(f_e, f[u]))



                #Removing duplicated element from l_new
                l = self._soc_remove_repeated_break_points_and_sort(l)
                print('l', l)

                ifmerge = False

                for bp in l:
                    if bp[1] > self._f(f[v], bp[0]):
                        ifmerge = True
                        break

                #merge break points of fu and fuv and update the key
                if ifmerge:
                    f_v_new = []
                    f_v = deepcopy(f[v])
                    f[v] = self._soc_merge(f[v], l, M)
                    print('f[v]' , f[v])
                    for bp in f[v]:
                        if bp not in f_v:
                            f_v_new.append(bp)

                    print('f_v_new', f_v_new)


                    min_list = []
                    for bp in list(f_v):
                        min_list.append(bp[0] - bp[1])

                    minkey = min(min_list)
                    print('minkey', minkey)
                    Q[v] = potential[v] + minkey
                    print('Q[v]', Q[v])

        return f[t]






    def link_step1(self, f_u, f_e):
        l_local = []
        for bp in f_u:
            f_e_at_bp = self._f(f_e, bp[1])
            print('f_e_at_bp', f_e_at_bp)
            if bp[1] >= 0 and f_e_at_bp:
                b = f_e[-1]
                for b1, b2 in zip(f_e[:-1], f_e[1:]):
                    if b1[0] <= bp[0] < b2[0]:
                        b = b1
                        break
                if bp[2] == 1 and b[2] == 1:
                    l_local.append(self._soc_segment(bp[0], f_e_at_bp, 1))
                    print('l_local', l_local)
                else:
                    l_local.append(self._soc_segment(bp[0], f_e_at_bp, 0))
                    print('l_local', l_local)

        return l_local

    def link_step2(self, f_e, f_u):
        l_local = []
        for be in f_e:
            for bu1, bu2 in zip(f_u[:-1], f_u[1:]):
                xlength = bu2[0] - bu1[0]

                if bu1[2] == 0: #projection of the segment is a point
                    if bu1[1] == be[0]: #be>=0
                        if be[2] == 1 or be[2]==0:
                            l_local.append(self._soc_segment(bu1[0], be[1], 0))
                        else:
                            print('I should not be here!')

                elif bu1[2] == 1:
                    if bu1[1] <= be[0] < bu1[1] + bu1[2] * xlength:

                        if be[2] == 0 and bu1[1] >=0: #TODO put some checks to prevent the first element becomes -inf
                            l_local.append(self._soc_segment(bu1[0] + be[0] - bu1[1], be[1], 0))
                            print(1, 'bu1 =', bu1, 'be[0] =', be[0])
                        elif be[2] == 1 and bu1[1] >=0:
                            l_local.append(self._soc_segment(bu1[0] + be[0] - bu1[1], be[1], 1))
                            print(2, 'bu1 =', bu1, 'be[0] = ', be[0])
                        else:
                            print('I should not be here!')
                else:
                    print('I should not be here!')
            if f_u[-1][1] == be[0]:
                l_local.append(self._soc_segment(f_u[-1][1], be[1], 0))

        return l_local

    def check_in_range(self, bp, l1):
        for b1, b2 in zip(l1[:-1], l1[1:]):
            if b1[1] != b2[1]:
                if b1[1] <= bp[0] < b2[1]:
                    return b1
            if b1[1] == b2[1] and bp[0] == b1[1]:
                return b1
        if bp[0] == l1[-1][1]:
            return l1[-1]







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
                elif self.v[v]['elev'] - self.v[u]['elev'] < 0:
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


    # def my_merge(self, l_1, l_2):
    #     l = self._soc_remove_repeated_break_points_and_sort(l_1)
    #     ll = self._soc_remove_repeated_break_points_and_sort(l_2)
    #     my = []
    #
    #     l_first = l.pop(0)
    #     ll_first = ll.pop(0)
    #
    #     if ll_first[0] > l_first[0]:
    #         my.append(l_first)
    #         ll.insert(0, ll_first)
    #     elif ll_first[0] == l_first[0]:
    #         if l_first[1] > ll_first[1]:
    #             my.append(l_first)
    #             ll.insert(0, ll_first)
    #         else:
    #             my.append(ll_first)
    #             l.insert(0, l_first)
    #     else:
    #         my.append(ll_first)
    #         l.insert(0, l_first)
    #
    #     while len(l) > 0 or len(ll) > 0:
    #
    #         l1 = l.pop(0)
    #         l2 = ll.pop(0)
    #
    #         if l1[0] < l2[0]:
    #
    #             if l1[1] > l_first[1]:
    #                 l3 = l[0]
    #                 if l3[0] > l2[0]:
    #                     my.append(l1)
    #                     if l1[2] == 0:
    #                         if l2[2] == 1:
    #                             if l2[1] < l1[1]:
    #                                 l_potentially = self._soc_segment(l2[0] + l1[0] - l2[1], l1[1], 1)
    #                                 if l_potentially[0] < l3[0]:
    #                                     my.append(l_potentially)
    #
    #                             elif l2[1] == l1[1]:
    #                                 my.append(l2)
    #
    #                             elif l2[1] > l1[1]:
    #                                 my.append(l2)
    #
    #                     elif l1[2] == 1:
    #                         if l2[1] == l1[1] and l3[2] == 0:
    #                             y = self._f(ll, l3[0])
    #                             if y == l3[1]:
    #                                 my.append(l2)
    #
    #                         elif l2[1] > l1[1]:
    #                             my.append(l2)
    #
    #                 elif l3[0] <= l2[0]:
    #                     my.append(l1)
    #                     ll.insert(0, l2)
    #
    #
    #             elif l1[1] == l_first[1]:
    #                 my.append(l1)
    #
    #             else:
    #                 continue
    #
    #         elif l1[0] > l2[0]:
    #             if l2[1] > l_first[1]:
    #                 l3 = ll[0]
    #                 if l3[0] > l1[0]:
    #                     my.append(l2)
    #                     if l2[2] == 0:
    #                         if l1[2] == 1:
    #                             if l1[1] < l2[1]:
    #                                 l_potentially = self._soc_segment(l1[0] + l2[0] - l1[1], l2[1], 1)
    #                                 if l_potentially[0] < l3[0]:
    #                                     my.append(l_potentially)
    #
    #                             elif l1[1] == l2[1]:
    #                                 my.append(l1)
    #
    #                             elif l1[1] > l2[1]:
    #                                 my.append(l1)
    #
    #                     elif l2[2] == 1:
    #                         if l1[1] == l2[1] and l3[2] == 0:
    #                             y = self._f(l, l3[0])
    #                             if y == l3[1]:
    #                                 my.append(l1)
    #
    #                         elif l1[1] > l2[1]:
    #                             my.append(l1)
    #
    #                 elif l3[0] <= l1[0]:
    #                     my.append(l2)
    #                     l.insert(0, l1)
    #
    #
    #             elif l2[1] == l_first[1]:
    #                 my.append(l2)
    #
    #         elif l1[0] == l2[0]:
    #             if l1[2] == 1:
    #                 my.append(l1)
    #             elif l2[2] == 1:
    #                 my.append(l2)
    #             else:
    #                 my.append(l1)
    #
    #         l_first = my[-1]
    #
    #     return my

















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

            if l_ij_at_l0 is None:
                continue

            l_new_at_end = l[1] + l[2] * dlx
            l_ij_at_end = merged[i][1] + merged[i][2] * dx

            if l[1] <= l_ij_at_l0 and l_new_at_end <= l_ij_at_end: # l_new completely under l_ij
                print('1', l, l_ij_at_l0, l_new_at_end, l_ij_at_end)
                continue
            elif l[1] > l_ij_at_l0 and l_new_at_end > l_ij_at_end: # l_new crosses l_ij from below
                print('2', l, l_ij_at_l0, l_new_at_end, l_ij_at_end)
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
            elif l[1] < l_ij_at_l0 and l_new_at_end > l_ij_at_end: # l_ij crosses l_new from below
                print('3', l, l_ij_at_l0, l_new_at_end, l_ij_at_end)
                x_intersect = l[0] + l_ij_at_l0 - l[1]
                if x_intersect == merged[i][0]:
                    del(merged[i])
                    merged.insert(i, (merged[i][0], merged[i][1], l[2]))
                else:
                    merged.insert(i+1, (x_intersect, merged[i][1], l[2]))
            elif l[1] > l_ij_at_l0 and l_new_at_end < l_ij_at_end: # l_new crosses l_ij from above
                print('4', l, l_ij_at_l0, l_new_at_end, l_ij_at_end)
                x_intersect = l[0] + merged[i][2] * (l[1] - l_ij_at_l0)
                old_bp = merged[i]
                print(old_bp)
                merged.insert(i+1, (x_intersect, old_bp[1] + old_bp[2] * (x_intersect - old_bp[0]), old_bp[2]))
                merged.insert(i+1, (l[0], l[1], l[2]))
            else:
                print('5', l, l_ij_at_l0, l_new_at_end, l_ij_at_end)
                print('Something\'s wrong! I should not be here!')

        # update last break point
        if l_ij[-1][0] == l_new[-1][0]:
            if merged[-1][0] == l_ij[-1][0]:
                last_point = merged.pop()
                merged.append(self._soc_segment(last_point[0], max(l_ij[-1][1], l_new[-1][1]), last_point[2]))
            else:
                print('I should not be here!')

        return merged


    def _f(self, break_points, ic): #TODO check if the last breakpoint always happens at M
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

    def _f_(self, break_points, ic):
        """
        Returns the final state of charge for every possible initial charge
        """

        I = [bp[0] for bp in break_points] # Initial charge
        F = [bp[1] for bp in break_points] # Final charge
        S = [bp[2] for bp in break_points] # Right-side slope

        for i1, i2, f1, f2, s in zip(I[:-1], I[1:], F[:-1], F[1:], S[:-1]):
            if ic < i1:
                return float('-inf')
            elif i1 <= ic < i2:
                if s == 0:
                    return f1
                else:
                    ic - i1 + f
            elif ic > i2:
                return f2








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
                        l_ikj[i] = bp    #TODO but if there are two break points for
            if not found:                #which the first two elements are similar but
                l_ikj.append(bp)         #the slopes differ, what should we do? which one should we chose?

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


    def _set_of_break_points(self, e, M): #TODO if i add a new break point (0, float('-inf'), 0 ) do i still need to add None in _f?
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
                self._soc_segment(0, float('-inf'), 0),
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
