
def count():
    return lambda arr: len(arr)


def count_if(condition):
    return lambda arr: len([val for val in arr if condition(val)])


def downsample(factor):
    return lambda arr: arr[::factor]


def head(n_elems):
    return lambda arr: arr[:n_elems]
