"""
A collection of comms_ml "aggregation functions" - functions that return a
post-processing function. This post-processing converts a list of pre-processed
values such as packet timestamp in milliseconds into a fixed-length feature
such as the mean.
"""

import numpy as np


def count():
    """
    Returns an aggregator for the number of occurrences
    """
    return lambda arr: len(arr)


def count_if(condition):
    """
    Returns an aggregator for the number of occurrences that match the given
    condition
    """
    return lambda arr: len([val for val in arr if condition(val)])


def downsample(factor):
    """
    Returns an aggregator for the first valid element of the samples,
    downsampled with the given factor.
    """
    return lambda arr: arr[::factor]


def head(n_elems):
    """
    Returns an aggregator for the first n_elems elements of the first sample
    """
    return lambda arr: arr[0][:n_elems] if len(arr) >= 0 else None


def tail(n_elems):
    """
    Returns an aggregator for the last n_elems elements of the first sample
    """
    return lambda arr: arr[0][-n_elems:] if len(arr) >= 0 else None


def n_unique():
    """
    Returns the number of unique elements
    """
    return lambda arr: len(set(arr))


# Mappers, TODO: move to separate module
def keep_if(condition):
    """
    Returns a property map that keeps only the first element
    """
    def ret_func(prop_recs):
        for prop, record in prop_recs:
            if condition(record):
                return [prop]
        return []
    return ret_func


def iat():
    """
    Returns a property map that contains the inter-arrival times of the given
    packets
    """
    def ret_func(arr):
        n_elems = len(arr)
        if n_elems <= 1:
            return [0] * n_elems
        return [np.NaN] + [float(arr[i+1][0]) - float(arr[i][0]) for i in range(n_elems - 1)]
    return ret_func
