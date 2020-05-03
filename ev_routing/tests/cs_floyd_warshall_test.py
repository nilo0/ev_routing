from ..cs_floyd_warshall import CSFloydWarshall


def test_csfloydwarshall():
    bl = {'lat': 52.50e0, 'lon': 13.34e0}  # Bottom left corner coordinate
    tr = {'lat': 52.53e0, 'lon': 13.43e0}  # Top right corner coordinate
    area = [bl['lat'], bl['lon'], tr['lat'], tr['lon']]

    M = 3000

    csfw = CSFloydWarshall(area, M)
    csfw.run()