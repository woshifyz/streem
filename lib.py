def echo(x):
    print x

def split(s, sep=','):
    return s.split(sep)

def join(s, sep=','):
    return sep.join(s)

def strip(s, v=None):
    if v is None:
        return s.strip()
    else:
        return s.strip(v)
