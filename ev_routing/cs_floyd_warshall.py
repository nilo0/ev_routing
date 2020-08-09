import random
import time
import sys
from copy import deepcopy
from .floyd_warshall_profile import FloydWarshallProfile
from .helper import break_points_list as bp_list
from .helper import matrix as matrix_helper
from .helper import break_point

class CSFloydWarshall(FloydWarshallProfile):
    """Floyd-Warshall algorithm with Charging Station"""

    def __init__(self, area, M, n_nodes=None, n_stations=None, testing=False, station_id=None):
        """
        Initializing CSFloydWarshall

        :param area:
        :param M: Maximum battery capacity
        :param n_nodes: Number of nodes to be considered
            (if None, it includes all nodes within the area)
        """
        FloydWarshallProfile.__init__(self, area, M, n=n_nodes, testing=testing)

        start_time = time.time()
        self.run()  # Result will be set in self.matrix
        self.dt_FW = time.time() - start_time

        self.M = M
        self.n_nodes = n_nodes if n_nodes else len(self.v)
        self.n_stations = n_stations if n_stations else int(.1 * self.n_nodes)

        if self.n_stations > 0:
            if station_id is None:
                random.seed(234)
                self.station_id = list(set([
                    random.choice(range(self.n_nodes)) for _ in range(self.n_stations)
                ]))
            else:
                self.station_id = station_id

            self.station_vid = [self.vid[i] for i in self.station_id]
            self.n_stations = len(self.station_id)

        self.stations = []
        self.min_costs = []
        start_time = time.time()
        self._stations_graph()
        self.dt_stations_graph = time.time() - start_time

    def _stations_graph(self):
        def fill_min_costs(i, j):
            if i == j:
                return 0
            e = self.map.connected(self.vid[i], self.vid[j])
            if e:
                return e['cost'] if e['cost'] <= self.M else float('inf')
            else:
                return float('inf')

        self.min_costs = matrix_helper.init(self.n_nodes, self.n_nodes, fill_min_costs)
        helper = matrix_helper.zeros(self.n_nodes, self.n_nodes, by=None)

        for k in range(self.n_nodes):
            for i in range(self.n_nodes):
                for j in range(self.n_nodes):
                    ik_cost = self.min_costs[i][k]
                    kj_cost = self.min_costs[k][j]
                    ikj_cost = ik_cost + kj_cost
                    ij_cost = self.min_costs[i][j]
                    if ikj_cost < ij_cost:
                        self.min_costs[i][j] = ikj_cost
                        helper[i][j] = k

        def get_path(i, j):
            if helper[i][j]:
                path_ik = get_path(i, helper[i][j])
                path_kj = get_path(helper[i][j], j)
                return path_ik + path_kj
            else:
                if float('inf') > self.min_costs[i][j] > 0:
                    return [(i, j, self.min_costs[i][j])]
                else:
                    return []

        self.stations = matrix_helper.zeros(self.n_nodes, self.n_nodes, by=[])
        for i in self.station_id:
            for j in self.station_id:
                self.stations[i][j] = get_path(i, j)

    def final(self):
        """
        Tozih
        :return:
        """
        def fill_final_min_costs(i, j):
            return bp_list.mim_reachable_charge(self.matrix[i][j])

        c_new = matrix_helper.init(self.n_nodes, self.n_nodes, fill_final_min_costs)

        for i in range(self.n_nodes):
            for j in range(self.n_nodes):

                if i == j:
                    continue

                final_soc = deepcopy(self.matrix[i][j])

                i_reaches_s = [bp_list.reachable(self.matrix[i][s]) for s in self.station_id]
                s_reaches_j = [bp_list.reachable(self.matrix[s][j]) for s in self.station_id]

                for si_id, si in enumerate(self.station_id):
                    if not i_reaches_s[si_id]:
                        continue
                    for sj_id, sj in enumerate(self.station_id):
                        if not s_reaches_j[sj_id]:
                            continue
                        # si: index of 1st station in self.matrix
                        # sj: index of 2nd station in self.matrix

                        bp_id = bp_list.search_range(self.matrix[sj][j], 0)
                        sj_j_cost = self.matrix[sj][j][bp_id][0]
                        si_sj_cost = self.min_costs[si_id][sj_id]

                        if si_sj_cost + sj_j_cost < c_new[si][j]:
                            c_new[si][j] = si_sj_cost + sj_j_cost

                    if c_new[si][j] < float('inf'):
                        final_soc = bp_list.disconnected_merge(self.matrix[i][si], c_new[si][j], final_soc, 0, self.M)

                self.matrix[i][j] = deepcopy(final_soc)
