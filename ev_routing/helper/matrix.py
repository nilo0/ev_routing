def zeros(len_x, len_y, by=0):
    """
    Initializing a matrix
    :param len_x: x-axis length
    :param len_y: y-axis length
    :param by: Element to be places in the matrix
    :return:
    """
    matrix = []
    for i in range(len_x):
        row = []
        for j in range(len_y):
            row.append(by)
        matrix.append(row)

    return matrix


def init(len_x, len_y, func):
    """

    Initializing a matrix by a given elemental function
    :param len_x: x-axis length
    :param len_y: y-axis length
    :param func: A given elemental function
    :return:
    """
    matrix = []
    for i in range(len_x):
        row = []
        for j in range(len_y):
            row.append(func(i, j))
        matrix.append(row)

    return matrix
