import numpy as np


def count():
    return lambda arr: len(arr)


def count_if(condition):
    return lambda arr: len([val for val in arr if condition(val)])


def downsample(factor):
    return lambda arr: arr[::factor]


def head(n_elems):
    return lambda arr: arr[0][:n_elems] if len(arr) >= 0 else None


def tail(n_elems):
    return lambda arr: arr[0][-n_elems:] if len(arr) >= 0 else None


def keep_if(condition):
    """ Returns a property map that keeps only the first element """
    def ret_func(prop_recs):
        for prop, record in prop_recs:
            if condition(record):
                return [prop]
        return []
    return ret_func


def iat():
    def ret_func(arr):
        n_elems = len(arr)
        if n_elems <= 1:
            return [0] * n_elems
        return [np.NaN] + [float(arr[i+1][0]) - float(arr[i][0]) for i in range(n_elems - 1)]
    return ret_func


def n_unique():
    return lambda arr: len(set(arr))
