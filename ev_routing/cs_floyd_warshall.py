import random
import time
from .floyd_warshall_profile import FloydWarshallProfile


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
        print("Floyd-Warshall finished in: %s s" % (time.time() - start_time))

        self.M = M
        self.n_nodes = n_nodes if n_nodes else len(self.v)
        self.n_stations = n_stations if n_stations else int(.1 * len(self.n_nodes))

        self.station_keys = list(set([
            random.choice(list(self.vid[:self.n_nodes])) for _ in range(self.n_stations)
        ]))