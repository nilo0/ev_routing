from ..dijkstra_profile import DijkstraProfile
from ..helper import break_point as break_point


def test_if_main_works():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    dp = DijkstraProfile(area, 3000)
    node_ids = [v['id'] for v in dp.v.values()]
    dp.run(node_ids[3], node_ids[-1])


def test_target_prune():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]
    M = 5

    dp = DijkstraProfile(area, M)

    f_tid = [
        break_point.new(0, float('-inf'), 0),
        break_point.new(2, 0, 1),
        break_point.new(3, 1, 0),
        break_point.new(4, 1, 1),
        break_point.new(5, 2, 0)
    ]

    f_vid = [
        break_point.new(0, float('-inf'), 0),
        break_point.new(3, 0, 1),
        break_point.new(4, 1, 0),
        break_point.new(5, 1, 0)
    ]

    value = dp._target_prune(f_vid, f_tid)

    assert value is True
