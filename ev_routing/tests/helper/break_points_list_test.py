from ...helper import break_points_list as bp_list
from ...helper import break_point as bp


def test_if_sort_works():
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
