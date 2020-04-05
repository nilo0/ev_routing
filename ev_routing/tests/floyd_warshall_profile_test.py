from ..floyd_warshall_profile import FloydWarshallProfile

BL = {'lat': 52.514e0, 'lon': 13.385e0}  # Bottom left corner coordinate
TR = {'lat': 52.516e0, 'lon': 13.387e0}  # Top right corner coordinate

AREA = [BL['lat'], BL['lon'], TR['lat'], TR['lon']]
M = 300


def test_init():
    fw = FloydWarshallProfile(AREA, M, n=16)

    assert isinstance(fw.v, dict)
    assert isinstance(fw.e, dict)


def test_run():
    fw = FloydWarshallProfile(AREA, M)
    fw.run()

    for i in range(len(fw.matrix)):
        for j in range(len(fw.matrix)):
            print(i, j, fw.matrix[i][j])


def test_run_with_history():
    fw = FloydWarshallProfile(AREA, M, n=16)
    history = fw.run_with_history()

    assert len(history) == len(fw.matrix) + 1

    for k in range(len(fw.matrix)):
        assert len(history[k]) == len(fw.matrix)

        for j in range(len(fw.matrix)):
            assert len(history[k][j]) == len(fw.matrix)

    #  for k in range(len(fw.matrix)):
    #     for i in range(len(fw.matrix)):
    #         assert history[k][i][i] == [(0, 0, 1), (M, M, 0)]
