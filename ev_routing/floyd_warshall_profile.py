from .main import EVRouting
from .helper import break_point
from .helper import break_points_list


class FloydWarshallProfile(EVRouting):
    """Floyd-Warshall profile"""

    def __init__(self, area, M, n=None):
        """
        Initializing FloydWarshallProfile class
        by calling EVRouting initializer

        Args:
        area:
        M: Maximum battery capacity
        """
        EVRouting.__init__(self, area)

        self.matrix = []

        n = len(self.v) if n is None else n

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
        M: Battery charge capacity
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
                        self.matrix[i][j], l_new)
