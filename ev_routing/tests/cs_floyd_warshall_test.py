from ..cs_floyd_warshall import CSFloydWarshall


def test_csfloydwarshall():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate
    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    M = 8

    csfw = CSFloydWarshall(area, M, n_nodes=32, n_stations=32)
    for i in csfw.station_vid:
        assert i in csfw.v


def test_csfw_final():
    bl = {'lat': 52.51, 'lon': 13.373}  # Bottom left corner coordinate
    tr = {'lat': 52.52, 'lon': 13.401}  # Top right corner coordinate

    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    M = 5

    csfw = CSFloydWarshall(area, M, n_stations=2, testing=True, station_id=[3, 6])
    csfw.final()

    print('khodafez')


