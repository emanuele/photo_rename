import numpy as np


def joint_argsort(value1, value2):
    """Argsort an iteable accordin gto the value in value1 and, when there
    are ties, ise the corresponding value in value2.
    """
    order1 = []
    for uv1 in np.unique(value1):
        idx_uv1 = np.where(value1 == uv1)[0]
        order_of_ties_v1 = idx_uv1[np.argsort(value2[idx_uv1])]
        order1 += order_of_ties_v1.tolist()

    return np.array(order1)


if __name__ == '__main__':
    n = 10
    value2 = np.random.uniform(size=n)
    value1 = np.floor(value2 * 10.0) / 10.0
    print("value1: %s" % value1)
    print("value2: %s" % value2)
    print("")
    order1 = joint_argsort(value1, value2)
    print("sorted value1: %s" % value1[order1])
    print("sorted value2: %s" % value2[order1])
