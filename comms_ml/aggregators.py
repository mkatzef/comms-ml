

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
    def ret_func(prop_rec):
        prop, record = prop_rec
        if condition(record):
            return prop
    return ret_func
