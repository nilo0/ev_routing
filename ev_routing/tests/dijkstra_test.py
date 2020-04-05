from ..dijkstra import Dijkstra


def test_if_main_works():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]
    evr = Dijkstra(area)

    assert isinstance(evr.v, dict)
    assert isinstance(evr.e, dict)
