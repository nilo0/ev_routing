from ..dijkstra_profile import DijkstraProfile


def test_if_main_works():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    dp = DijkstraProfile(area, 3000)
    node_ids = [v['id'] for v in dp.v.values()]
    dp.run(node_ids[3], node_ids[-1])