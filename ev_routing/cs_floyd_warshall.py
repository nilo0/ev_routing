import random
from .main import EVRouting


class CSFloydWarshall(EVRouting):
    """Floyd-Warshall algorithm with Charging Station"""

    def __init__(self, area, M):
        """
        Initializing CSFloydWarshall

        :param area:
        :param M: Maximum battery capacity
        """
        EVRouting.__init__(self, area)

        self.station_keys = list(set([
            random.choice(list(self.v)) for _ in range(30)
        ]))

    def run(self):
        """
        Performing the algorithm
        :return:
        """
        pass