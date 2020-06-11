from copy import deepcopy
from .main import EVRouting
from .helper import break_point
from .helper import break_points_list


class FloydWarshallProfile(EVRouting):
    """Floyd-Warshall profile"""

    def __init__(self, area, M, n=None, testing=False):
        """
        Initializing FloydWarshallProfile class
        by calling EVRouting initializer

        :param area:
        :param M: Maximum battery capacity
        :param n: Number of nodes to be considered
            (if None, it includes all nodes within the area)
        """
        EVRouting.__init__(self, area, testing=testing)

        self.matrix = []
        self.M = M

        n = n if n else len(self.v)

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append([
                        break_point.new(0, 0, 1),
                        break_point.new(M, M, 0),
                    ])
                else:
                    e = self.map.connected(self.vid[i], self.vid[j])
                    if e:
                        row.append(break_point.init(e, M))
                    else:
                        row.append([
                            break_point.new(0, float('-inf'), 0),
                            break_point.new(M, float('-inf'), 0),
                        ])

            self.matrix.append(row)

    def run(self):
        """
        Args:
        """
        # New set of break points after linking two paths
        l_new = []
        n = len(self.matrix)

        for k in range(n):
            for i in range(n):
                l_ik = self.matrix[i][k]

                for j in range(n):
                    l_kj = self.matrix[k][j]

                    l_new = break_points_list.link(l_ik, l_kj)
                    l_new = break_points_list.sort(l_new)

                    self.matrix[i][j] = break_points_list.merge(
                        self.matrix[i][j], l_new, self.M)

    def run_with_history(self):
        """
        Running Floyd-Warshall profile and storing its history
        """
        n = len(self.matrix)

        history = []
        matrix = deepcopy(self.matrix)
        history.append(matrix)

        for k in range(n):
            matrix = deepcopy(self.matrix)
            history.append(matrix)

            for i in range(n):
                l_ik = history[k][i][k]

                for j in range(n):
                    l_kj = history[k][k][j]

                    l_new = break_points_list.link(l_ik, l_kj)
                    l_new = break_points_list.sort(l_new)

                    history[k+1][i][j] = break_points_list.merge(
                        history[k][i][j], l_new, self.M)

        return history

