from ...helper import break_points_list as bp_list
from ...helper import break_point as bp


def test_sort():
    lst = [bp.new(0, 0, 1),
           bp.new(600, 600, 0),
           bp.new(300, 200, 1),
           bp.new(1000, 1000, 0),
           bp.new(100, 100, 0),
           bp.new(1000, 1000, 0)]

    sorted_lst = bp_list.sort(lst)

    assert len(sorted_lst) == 5

    for i in range(len(sorted_lst) - 1):
        assert sorted_lst[i][0] < sorted_lst[i + 1][0]


def test_remove_redundant_break_points():
    lst = [bp.new(0, 0, 1),
           bp.new(12.34, 12.34, 1),
           bp.new(23.45, 23.45, 1),
           bp.new(34.56, 34.56, 1),
           bp.new(45.67, 45.67, 1),
           bp.new(56.78, 56.78, 1),
           bp.new(100, 100, 0)]

    bp_list._remove_redundant_break_points(lst)

    assert lst == [bp.new(0, 0, 1), (100, 100, 0)]


def test_reachable():
    lst = [
        bp.new(0, float('-inf'), 0),
        bp.new(100, float('-inf'), 0),
    ]

    assert bp_list.reachable(lst) is False

    lst = [
        bp.new(0, float('-inf'), 0),
        bp.new(10, 0, 1),
        bp.new(100, 90, 0),
    ]
    assert bp_list.reachable(lst) is True


def test_final_merge():
    l1 = [(0, float('-inf'), 0), (5, 0, 1), (10, 6, 1), (12, 9, 1), (15, 12, 0)]
    c1 = 36
    l2 = [(0, float('-inf'), 0), (4, 0, 1), (7, 9, 1), (13, 15, 0), (15, 15, 0)]
    c2 = 46
    D = 15

    merged = bp_list.disconnected_merge(l1, c1, l2, c2, D)

    assert merged[0] == (0, float('-inf'), 0)
    assert merged[1] == (4, -46, 1)
    assert merged[2] == (5, -36, 1)
    assert merged[3] == (10, -30, 1)
    assert merged[4] == (12, -27, 1)
    assert merged[5] == (15, -24, 0)
