from ..cs_floyd_warshall import CSFloydWarshall


def test_csfw():
    bl = {'lat': 52.51, 'lon': 13.373}  # Bottom left corner coordinate
    tr = {'lat': 52.52, 'lon': 13.401}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    M = 5

    csfw = CSFloydWarshall(area, M, n_stations=2, testing=True, station_id=[4, 8])
    csfw._stations_graph()
    csfw.final()

    return




