def init(e, M):
    """
    Calculated set of break points for a given edge and battery capacity

    Arguments:
    e -- a given edge (u, v, c)
    M -- Battery charge capacity
    """
    c = e['cost']

    if c < 0:
        return [
            new(0, -c, 1),
            new(M + c, M, 0),
            new(M, M, 0),
        ]
    else:
        return [
            new(0, float('-inf'), 0),
            new(c, 0, 1),
            new(M, M - c, 0),
        ]


def new(ic, fc, slope):
    """
    Args:
    ic: Initial charge
    fc: Final charge
    slope: Slope of the segment
    """
    return (ic, fc, slope)


def domain_overlap(bp1, xlen1, bp2, xlen2):
    """
    Find if two break points overlap on their domains

    Args:
    bp1: First break point
    xlen1: Length of the first break poin on its domain
    bp2: Second break point
    xlen2: Length of the second break poin on its domain

    Returns:
    None: If break points do not overlap
    [x1, x2]: Overlap range
    """
    x1 = max(bp1[0], bp2[0])
    x2 = min(bp1[0] + xlen1, bp2[0] + xlen2)

    if x1 > x2:
        return None
    else:
        return [x1, x2]


def range_overlap(bp1, xlen1, bp2, xlen2):
    """
    Find if two break points overlap on their range

    Args:
    bp1: First break point
    xlen1: Length of the first break poin on its domain
    bp2: Second break point
    xlen2: Length of the second break poin on its domain

    Returns:
    None: If break points do not overlap
    [y1, y2]: Overlap range in case y1 == y2: [y1]
    """
    y1 = max(bp1[1], bp2[1])
    y2 = min(bp1[1] + bp1[2] * xlen1, bp2[1] + bp2[2] * xlen2)

    if y1 > y2:
        return None
    if y1 < y2:
        return [y1, y2]
    else:
        return [y1]


def overlap(bp1, xlen1, bp2, xlen2):
    """
    Find if two break points overlap on their domain and range

    Args:
    bp1: First break point
    xlen1: Length of the first break poin on its domain
    bp2: Second break point
    xlen2: Length of the second break poin on its domain

    Returns:
    A dictionary with range and domain keys
    """

    return {
            'domain': domain_overlap(bp1, xlen1, bp2, xlen2),
            'range': range_overlap(bp1, xlen1, bp2, xlen2)
            }
