from .map.map_api import MapAPI
from copy import deepcopy


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

        self.vid = [v['id'] for v in self.v.values()]

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
