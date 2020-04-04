from .main import EVRouting
from .helper import break_point
from .helper import break_points_list


class FloydWarshallProfile(EVRouting):
    """Floyd-Warshall profile"""

    def __init__(self, area, M):
        """
        Initializing FloydWarshallProfile class
        by calling EVRouting initializer

        Args:
        area:
        M: Maximum battery capacity
        """
        EVRouting.__init__(self, area)

        self.l_ij = self.l_ij_init(self.v, M)

    def run(self, nodes, M):
        """
        Args:
        nodes: list of nodes and charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        #  l = self.l_ij_init(nodes, M)

        # New set of break points after linking two paths
        l_new = []

        n = len(nodes)

        for k in range(n):
            for i in range(n):
                l_ik = self.l_ij[i][k]

                for j in range(n):
                    l_kj = self.l_ij[k][j]

                    l_new = break_points_list.link(l_ik, l_kj)
                    l_new = break_points_list.sort(l_new)

                    ifmerge = False

                    for bp in l_new:
                        if bp[1] > self._f(self.l_ij[i][j], bp[0]):
                            ifmerge = True
                            break

                    if ifmerge:
                        self.l_ij[i][j] = self._soc_merge(
                                self.l_ij[i][j], l_new, M)

    def l_ij_init(self, nodes, M):
        """
        Args:
        nodess: list of nodes and charging stations ids, e.g. [1, 203, 453]
        M: Battery charge capacity
        """
        n = len(nodes)
        l = []

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append([
                        break_point.new(0, 0, 1),
                        break_point.new(M, M, 0),
                    ])
                else:
                    e = self.map.is_connected(nodes[i], nodes[j])
                    if e:
                        row.append(break_point.init(e, M))
                    else:
                        row.append([
                            break_point.new(0, float('-inf'), 0),
                            break_point.new(M, float('-inf'), 0),
                        ])

            l.append(row)

        return l
