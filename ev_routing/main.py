from .map.map_api import MapAPI
from copy import deepcopy
from helper import break_point


class EVRouting:
    """Electrical Vehicles (EV) Routing Class"""

    def __init__(self, area):
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

        self.map = MapAPI(area)
        self.v = self.map.v
        self.e = self.map.e

        self.map_center = self.map.scope['center']

    def d_profile(self, s, t, M=float('inf')):
        """
        EV Dijkstra Profile Search

        maps every possible initial state of charges at s
        to the optimal state of charge at target t.

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        M -- maximum charge level
        """

        f = {}
        Q = {}
        potential = self.potential()

        for vid in self.v:
            f[vid] = [(0, float('-inf'), 0), (M, float('-inf'), 0)]

        f[s] = [(0, 0, 1), (M, M, 0)]
        Q[s] = 0 + potential[s]

        while len(Q) > 0:
            u = min(Q, key=lambda k: Q[k])
            _ = Q.pop(u)

            for eid in self.v[u]['outgoing']:
                e = self.e[eid]
                v = e['v']
                l = []

                # if self.target_prune(v, f[v], t, f[t], M):
                #     print('target_prune', v, f[v], t, f[t])
                #     continue

                # linking SoC function of fu and fuv break point f_u
                f_e = break_point.init(e, M)

                l.extend(self.link_step1(f[u], f_e))
                l.extend(self.link_step2(f_e, f[u]))

                # Removing duplicated elements from l_new
                l = break_points_list.sort(l)

                ifmerge = False

                for bp in l:
                    if bp[1] > self._f(f[v], bp[0]):
                        ifmerge = True
                        break

                # Merge break points of fu and fuv and update the key
                if ifmerge:
                    f_v_new = []
                    f_v = deepcopy(f[v])
                    f[v] = self._soc_merge(f[v], l, M)
                    for bp in f[v]:
                        if bp not in f_v:
                            f_v_new.append(bp)

                    min_list = []
                    for bp in list(f_v):
                        min_list.append(bp[0] - bp[1])

                    minkey = min(min_list)
                    print('minkey', minkey)
                    Q[v] = potential[v] + minkey
                    print('Q[v]', Q[v])

        return f[t]

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

        c_v = [M]
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
                alpha_e[eid] = e['cost'] / \
                        (self.v[v]['elev'] - self.v[u]['elev'])
                if self.v[v]['elev'] - self.v[u]['elev'] > 0:
                    q_up.append(alpha_e[eid])
                elif self.v[v]['elev'] - self.v[u]['elev'] < 0:
                    q_down.append(alpha_e[eid])

        alpha_max = int(max(q_up))
        alpha_min = int(min(q_down))

        if alpha_min <= 1 <= alpha_max:
            return 1
        else:
            return 2

    def check_alpha_true(self):
        num_edges = 0
        num_pos_cost = 0
        num_neg_cost = 0
        h_c_pos = 0
        h_c_neg = 0
        for eid in self.e:
            num_edges += 1
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
