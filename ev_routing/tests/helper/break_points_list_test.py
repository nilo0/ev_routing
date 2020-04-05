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
        assert sorted_lst[i][0] < sorted_lst[i+1][0]


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
