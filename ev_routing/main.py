import numpy as np

from .map_api.map_api import MapAPI


class EVRouting:
    """Electrical Vehicles (EV) Routing Class"""

    def __init__( self, area ):
        """
        Initializing EVRouting by:
        - loading nodes and edges based on a given region
        - finding incoming and outgoing edges

        Keyword arguments:
        area -- Array of 4 Numbers (bottom left lat/lon, upper right lat/lon)

        Example
        >>> from ev_routing import EVRouting
        >>> evr = EVRouting([ 52.50, 13.37, 52.53, 13.40 ])
        """

        map = MapAPI( area )
        self.v = map.nodes
        self.e = map.edges

        self.map_center = map.scope['center']

        self.outgoing = [ [] for _ in range(len(self.v)) ]
        self.incoming  = [ [] for _ in range(len(self.v)) ]

        for e in self.e:
            self.outgoing[e['u']].append(e)
            self.incoming[e['v']].append(e)


    def dijkstra( self, sid, tid, bs, M=float('inf') ):
        """
        EV Dijkstra Algorithm

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        bs -- charging level at start node
        M -- maximum charging level
        """

        Q_DTYPE = [
            ('vid', np.int64),
            ('bv', np.float64)
        ]

        b = float('-inf') * np.ones( len(self.v) )
        b[sid] = bs

        Q = np.array( [ (sid, b[sid]) ], dtype=Q_DTYPE)

        def f ( bu, c ):
            bv = bu - c
            if bv < 0: return float('-inf')
            if bv > M: return M
            return bv

        while len(Q) > 0:
            qid = np.argmax( Q['bv'] )
            uid = Q[qid]['vid']

            for e in self.outgoing[uid]:
                vid = e['v']
                bv = f( b[uid], e['cost'] )

                if bv > b[vid]: b[vid] = bv

                if b[vid] > 0:
                    Q = np.append( Q, np.array([(vid, b[vid])], dtype=Q_DTYPE) )

                if vid is tid: return b[tid]

            Q = np.delete( Q, qid )

        return b[tid]
