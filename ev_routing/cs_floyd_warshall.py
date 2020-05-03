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

        # TODO: Randomly specify CS in self.v

    def run(self):
        """
        Performing the algorithm
        :return:
        """
        pass