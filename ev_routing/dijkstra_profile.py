from .main import EVRouting


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


    def find(self, s, t):
        """
        EV Dijkstra profile search

        Map every possible initial state of charges (SoCs) at source node
        to its optimal SoC at target node

        Args:
        s: id of the source node
        t: id of the target node
        """
        Q, f = {}, {}

    def _alpha(self):
        """
        Calculate a scalar for thej evaluation of the consistency of potential
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

        if alpha_min <= 1 <= alpha_max:
            return 1
        else:
            return 2

