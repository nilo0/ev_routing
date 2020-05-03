from .map.map_api import MapAPI


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