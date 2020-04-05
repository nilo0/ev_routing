from ..floyd_warshall_profile import FloydWarshallProfile

BL = {'lat': 52.514e0, 'lon': 13.385e0}  # Bottom left corner coordinate
TR = {'lat': 52.516e0, 'lon': 13.387e0}  # Top right corner coordinate

AREA = [BL['lat'], BL['lon'], TR['lat'], TR['lon']]
M = 100


def test_init():
    fw = FloydWarshallProfile(AREA, M)

    assert isinstance(fw.v, dict)
    assert isinstance(fw.e, dict)


def test_run():
    fw = FloydWarshallProfile(AREA, M, n=3)
    fw.run()

    for i in range(len(fw.matrix)):
        for j in range(len(fw.matrix)):
            print(i, j, fw.matrix[i][j])
