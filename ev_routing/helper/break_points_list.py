import sys
from . import break_point


def sort(l):
    """
    Removeing break points with the same x but different ys

    Args:
    l: A given list of break points

    Returns:
    A new list of break points sorted and with no redundant element
    """
    if len(l) < 2:
        return l

    l_ikj = [l[0]]

    for bp in l[1:]:
        found = False

        for i in range(len(l_ikj)):
            ikj = l_ikj[i]

            if ikj[0] == bp[0]:
                found = True
                if bp[1] > ikj[1]:
                    l_ikj[i] = bp  # TODO but if there are two break points for

        if not found:  # which the first two elements are similar but
            # Slopes are different, which one should we chose?
            l_ikj.append(bp)

    return sorted(l_ikj, key=lambda t: t[0])


def link(l_ik, l_kj):
    """
    Linking two given list of break points

    Args:
    l_ik: List of break points between nodes i and k
    l_kj: List of break points between nodes k and j

    Returns:
    A new list of break points
    """
    l_local = []

    for ik in l_ik:
        charge_at_j = _f(l_kj, ik[1])

        if charge_at_j == float('-inf'):
            l_local.append(break_point.new(ik[0], charge_at_j, 0))
            continue

        if ik[1] >= 0:
            idx = search_domain(l_kj, ik[1])

            if idx is None:
                continue

            if ik[2] == 1 and l_kj[idx][2] == 1:
                l_local.append(break_point.new(ik[0], charge_at_j, 1))
            else:
                l_local.append(break_point.new(ik[0], charge_at_j, 0))

    for jk in l_kj:
        idx = search_range(l_ik, jk[0])

        if idx is None:
            continue

        if l_ik[idx][2] == 0:
            l_local.append(break_point.new(l_ik[idx][0], jk[1], 0))
        elif l_ik[idx][2] == 1:
            xnew = l_ik[idx][0] + (jk[0] - l_ik[idx][1])
            if 0 < xnew < l_ik[-1][0]:
                l_local.append(break_point.new(
                    xnew, jk[1], 0 if jk[2] == 0 else 1))

    return l_local


def merge(l1, l2, M):
    """
    Point-wise maximum of two functions (list of break points)

    Args:
    l1: Original set of break points
    l2: New set of break points
    M: Maximum battery capacity

    Returns:
    Point-wise maximum
    """
    merged = []
    i, j, di, dj = 0, 0, 0, 0

    df_old = 0.0
    x_old = 0.0
    f_old = 0.0
    s_old = 0.0

    while i < len(l1) or j < len(l2):
        if l1[i][0] < l2[j][0]:
            x = l1[i][0]
            f1, f2 = l1[i][1], _f(l2, x)
            s1, s2 = l1[i][2], _s(l2, x)
            di, dj = 1, 0

            if f1 != f2:
                merged.append(
                    l1[i] if f1 > f2
                    else break_point.new(x, f2, s2))
            else:
                merged.append(l1[i] if s1 > s2 else break_point.new(x, f2, s2))

        elif l2[j][0] < l1[i][0]:
            x = l2[j][0]
            f1, f2 = _f(l1, x), l2[j][1]
            s1, s2 = _s(l1, x), l2[j][2]
            di, dj = 0, 1

            if f1 != f2:
                merged.append(break_point.new(x, f1, s1) if f1 > f2 else l2[j])
            else:
                # Append break point with bigger slope
                merged.append(l2[j] if s2 > s1 else break_point.new(x, f1, s1))

        else:
            x = l1[i][0]
            f1, f2 = l1[i][1], l2[j][1]
            s1, s2 = l1[i][2], l2[j][2]
            di, dj = 1, 1

            if f1 != f2:
                merged.append(l1[i] if f1 > f2 else l2[j])
            else:
                # Append break point with bigger slope
                merged.append(l1[i] if l1[i][2] > l2[j][2] else l2[j])

        df = f2 - f1

        if df * df_old < 0:  # Found intersection
            xnew = x_old + df_old
            fnew = f_old + s_old * df_old

            if 0 < xnew < M and fnew < M:
                merged.insert(-1, break_point.new(xnew, fnew, s_old))

        i = i + di
        j = j + dj

        df_old = df
        x_old = merged[-1][0]
        f_old = merged[-1][1]
        s_old = merged[-1][2]

    return merged


def _remove_redundant_break_points(l, sig=3):
    """
    Combining adjacent break points if they're along the same line
    NB: In-place changes on l

    Args:
    l: A list of break points

    Returns:
    Nothing!
    """
    if len(l) <= 2:
        return

    i = 0

    while i < len(l) - 2:
        if l[i][2] != l[i+1][2]:
            i += 1
        elif round(l[i][1] + l[i][2] * (l[i+1][0] - l[i][0]), sig) == round(l[i+1][1], sig):
            del l[i+1]
        else:
            i += 1


def search_domain(l, charge):
    """
    Check if charge is in the domain of l

    Args:
    l: List of break points
    charge: a given charge

    Returns:
    The id of the break point with domain including the charge
    None: when charge is out of l domain (Note that l[-1][0] = M)
    """
    if charge < 0 or charge > l[-1][0]:
        return None

    for i in range(len(l) - 1):
        if l[i][0] <= charge < l[i+1][0]:
            return i

    # Checking the endpoint
    if charge == l[-1][0]:
        return len(l) - 1  # index of the last element of l


def search_range(l, charge):
    """
    Check if charge is in the range of l
    """

    if charge < 0:
        return None

    for i in range(len(l) - 1):
        if l[i][2] == 0:  # slope is zero
            if charge == l[i][1]:
                return i
        elif l[i][2] == 1:  # slope is one
            if l[i][1] <= charge < l[i][1] + (l[i+1][0] - l[i][0]):
                return i
        else:
            sys.exit()

    # Checking the endpoint
    if l[-1][1] == charge:
        return len(l) - 1  # index of the last element of l

    # If none of above conditions
    return None


def _f(l, charge):
    """
    Calculating the final state of charge for a given initial charge
    based on a given list of break points

    TODO: Make the search complexity log(N)

    Args:
    l: list of break points
    charge: a given charge

    Returns:
    Final state of charge
    """
    if charge == float('-inf'):
        return float('-inf')

    if charge < l[0][0]:
        return float('-inf')

    if charge < 0:
        print('_f: Charge is negative!')
        sys.exit()

    IC = [bp[0] for bp in l]
    FC = [bp[1] for bp in l]
    S = [bp[2] for bp in l]

    for i1, i2, f1, f2, s in zip(IC[:-1], IC[1:], FC[:-1], FC[1:], S[:-1]):
        if i1 <= charge < i2:
            if s == 0:
                return f1
            elif s == 1:
                return charge - i1 + f1
            else:
                sys.exit()

    if charge == IC[-1]:
        return FC[-1]
    elif charge > IC[-1]:
        print("_f: Charge is bigger than the domain of l!")
        sys.exit()
    else:
        print("_f: I should not be here")
        sys.exit()


def _s(l, charge):
    """
    Finding the slope of the l at a given charge

    TODO: Make the search complexity log(N)

    Args:
    l: list of break points
    charge: a given charge

    Returns:
    Slope of l at charge
    """

    if charge < l[0][0]:
        return 0

    IC = [bp[0] for bp in l]
    FC = [bp[1] for bp in l]
    S = [bp[2] for bp in l]

    if charge < 0:
        print('_s: Charge is negative!')
        sys.exit()

    for i1, i2, f1, f2, s in zip(IC[:-1], IC[1:], FC[:-1], FC[1:], S[:-1]):
        if i1 <= charge < i2:
            return s

    if charge == IC[-1]:
        return S[-1]
    elif charge > IC[-1]:
        print("_s: Charge is bigger than the domain of l!")
        sys.exit()
    else:
        print("_s: I should not be here")
        sys.exit()
