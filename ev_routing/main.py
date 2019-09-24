import numpy as np
import time
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


    def dijkstra( self, s, t, bs, M=float('inf') ):
        """
        EV Dijkstra Algorithm

        Keyword arguments:
        s -- id of the start node
        t -- id of the target node
        bs -- charging level at start node
        M -- maximum charge level
        """

        # TODO: check s and t are within the valid range

        start_time = time.time()

        # Data types
        B_DTYPE = [ ('bv', np.float64), ('prev', np.int64) ]
        Q_DTYPE = [ ('v', np.int), ('bv', np.float) ]

        # Initializing b array with -inf
        b = np.array(
            [ (float('-inf'), -1) for _ in range(len(self.v)) ],
            dtype=B_DTYPE
        )

        b[s]['bv'] = bs

        # Initializing Q with only one member
        Q = np.array([ (s, b[s]['bv']) ], dtype=Q_DTYPE )

        # Final cost function
        def f ( e ):
            bv = b[e['u']]['bv'] - e['cost']
            if bv < 0: return float('-inf')
            if bv > M: return M
            return bv

        while len(Q) > 0:
            # Finding the maximum b[v] in Q
            qid = np.argmax( Q['bv'] )
            uid = Q[qid]['v']

            # Removing maximum b[v] from Q
            Q = np.delete( Q, qid )

            target_reached = False

            for e in self.outgoing[uid]:
                v = e['v']
                bv = f(e)

                if v is t:
                    target_reached = True

                if bv < b[v]['bv']:
                    continue

                b[v]['bv'] = bv
                b[v]['prev'] = uid

                if v in Q['v']:
                    idx = np.where( Q['v'] == v )[0][0]
                    Q[idx] = (v, b[v]['bv'])
                else:
                    if b[v]['bv'] > 0:
                        Q = np.append( Q, np.array([ (v, b[v]['bv']) ], dtype=Q_DTYPE) )

            if target_reached:
                break

        print("Dijkstra running time ", (time.time() - start_time) )

        trace_back = np.array( [], dtype=self.e.dtype )

        if b[t]['bv'] > 0:
            v = t
            while v is not s:
                if v is -1:
                    break

                pv = b[v]['prev']
                e = [ edge for edge in self.outgoing[pv] if edge['v'] == v ]

                if not e:
                    break

                trace_back = np.append( trace_back, np.array( e[0], dtype=self.e.dtype ) )
                v = e[0]['u']

        return b[t]['bv'], trace_back



    def dijkstra_dict( self, s, t, bs, M=float('inf') ):
        """
        Implementing Dijkstra algorithm on python dictionary
        """

        E = {}
        V = {}

        for i, v in enumerate( self.v ):
            V[i] = {
                'lat': v['lat'], 'lon': v['lon'], 'incoming': [], 'outgoing': []
            }

        for i, e in enumerate( self.e ):
            E[i] = { 'u': e['u'], 'v': e['v'], 'cost': e['cost'] }
            V[e['u']]['outgoing'].append( i )
            V[e['v']]['incoming'].append( i )

        SoC = {}
        for i, v in enumerate(V.values()):
            SoC[i] = {'b':float('-inf'), 'prev': -1}


        start_time = time.time()

        def f_e ( bu, c):
            bv = bu - c
            if bv < 0: return float('-inf')
            if bv > M: return M
            return bv

        SoC[s]['b'] = bs

        Q = { s:bs }

        #retrive the node with maximum key
        while len(Q) > 0:
            bu = max(Q.values())

            for q in list(Q):
                if Q[q] == bu:
                    u = q

            SoC[u]['b'] = Q.pop( u )

            for key_e in V[u]['outgoing']:
                e = E[key_e]
                v = e['v']
                c = e['cost']
                bv = SoC[v]['b']
                bv_new = f_e(bu, c)

                if bv_new > bv:
                    Q[v] = bv_new
                    SoC[v]['b'] = bv_new
                    SoC[v]['prev'] = u

                if v == t:
                    print("Dijkstra_dict running time before trace back", (time.time() - start_time) )


        trace = [t]
        v = t
        while v != s:
            trace.insert(0, SoC[v]['prev'])
            v = SoC[v]['prev']

        print("s-t path is", trace)

        print("Dijkstra_dict running time is ", (time.time() - start_time) )
        return SoC[t], SoC
