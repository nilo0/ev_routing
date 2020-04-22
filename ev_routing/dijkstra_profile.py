from .main import EVRouting
from .helper import break_point
from .helper import break_points_list


class DijkstraProfile(EVRouting):
    """Dijkstra profile """

    def __init__(self, area, M):
        """
        Initializing DijkstraProfile class
        by calling EVRouting initializer

        Args:
        area:
        M: Maximum battery capacity
        """
        EVRouting.__init__(self, area)

        self.M = M

    def run(self, s, t):
        """
        EV Dijkstra profile search

        Map every possible initial state of charges (SoCs) at source node
        to its optimal SoC at target node

        Args:
        s: id of the source node
        t: id of the target node
        """
        Q, f = {}, {}
        potential = self._potential()

        for vid in self.v:
            f[vid] = [
                break_point.new(0, float('-inf'), 0),
                break_point.new(self.M, float('-inf'), 0),
            ]

        f[s] = [
            break_point.new(0, 0, 1),
            break_point.new(self.M, self.M, 0),
        ]

        Q[s] = 0 + potential[s]

        while len(Q) > 0:
            uid = Q.pop(min(Q, key=lambda k: Q[k]))
            u = self.v[uid]

            for eid in u['outgoing']:
                e = self.e[eid]
                v = e['v']
                l = []

                f_u = f[uid]
                f_e = break_point.init(e, self.M)

                l = break_points_list.link(f_u, f_e)
                l = break_points_list.sort(l)

                # TODO: Port d_profile from main to here

    def _alpha(self):
        """
        Evaluating the consistency of potential
        by comparing the elevation of the two ends of edges
        """
        alpha_e = {}
        q_up, q_down = [], []

        for eid in self.e:
            e = self.e[eid]
            uid, vid = e['u'], e['v']
            u, v = self.v[uid], self.v[vid]

            if u['elev'] - v['elev'] != 0:
                alpha_e[eid] = e['cost'] / (v['elev'] - u['elev'])

                if v['elev'] > u['elev']:
                    q_up.append(alpha_e[eid])
                else:
                    q_down.append(alpha_e[eid])

        alpha_max = int(max(q_up))
        alpha_min = int(min(q_down))

        return 1 if alpha_min <= 1 <= alpha_max else 2

    def _potential(self):
        """
        Assing a consistent potential to all nodes
        """
        pot = {}

        alpha = self.alpha()

        for uid in self.v:
            pot[uid] = alpha * self.v[uid]['elev']

        return pot
