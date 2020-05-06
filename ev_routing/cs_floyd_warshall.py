import random
import time
from .floyd_warshall_profile import FloydWarshallProfile
from .helper import break_points_list as bp_list
from .helper import matrix as matrix_helper


class CSFloydWarshall(FloydWarshallProfile):
    """Floyd-Warshall algorithm with Charging Station"""

    def __init__(self, area, M, n_nodes=None, n_stations=None):
        """
        Initializing CSFloydWarshall

        :param area:
        :param M: Maximum battery capacity
        :param n_nodes: Number of nodes to be considered
            (if None, it includes all nodes within the area)
        """
        FloydWarshallProfile.__init__(self, area, M, n=n_nodes)

        start_time = time.time()
        self.run()  # Result will be set in self.matrix
        self.dt_FW = time.time() - start_time

        self.M = M
        self.n_nodes = n_nodes if n_nodes else len(self.v)
        self.n_stations = n_stations if n_stations else int(.1 * self.n_nodes)

        random.seed(123)
        self.station_vid = list(set([
            random.choice(self.vid[:self.n_nodes]) for _ in range(self.n_stations)
        ]))
        self.n_stations = len(self.station_vid)

        self.stations = []
        start_time = time.time()
        self._stations_graph()
        self.dt_stations_graph = time.time() - start_time

    def _stations_graph(self):
        def fill_min_costs(i, j):
            if bp_list.reachable(self.matrix[i][j]):
                bp_id = bp_list.search_range(self.matrix[i][j], 0)
                return self.matrix[i][j][bp_id][0]
            else:
                return float('inf')

        min_costs = matrix_helper.init(self.n_stations, self.n_stations, fill_min_costs)
        helper = matrix_helper.zeros(self.n_stations, self.n_stations, by=None)

        for k in range(self.n_stations):
            for i in range(self.n_stations):
                for j in range(self.n_stations):
                    ikj_cost = min_costs[i][k] + min_costs[k][j]
                    if min_costs[i][j] > ikj_cost:
                        min_costs[i][j] = ikj_cost
                        helper[i][j] = k

        def get_path(i, j):
            if helper[i][j]:
                path_ik = get_path(i, helper[i][j])
                path_kj = get_path(helper[i][j], j)
                return path_ik + path_kj
            else:
                if float('inf') > min_costs[i][j] > 0:
                    return [(i, j, min_costs[i][j])]
                else:
                    return []

        self.stations = matrix_helper.init(self.n_stations, self.n_stations, get_path)











