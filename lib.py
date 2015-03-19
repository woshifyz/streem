import functools
import os

def eq(x, y):
    return x == y

def neq(x, y):
    return x != y

def gt(x, y):
    return x > y

def lt(x, y):
    return x < y

def gte(x, y):
    return x >= y

def lte(x, y):
    return x <= y

def echo(x):
    print x

def split(s, sep=None):
    if sep is None:
        return s.split()
    else:
        return s.split(sep)

def join(s, sep=','):
    return sep.join(s)

def strip(s, v=None):
    if v is None:
        return s.strip()
    else:
        return s.strip(v)

def readfile(filename, count=None, strip=True):
    if count is None:
        with open(filename, 'r') as fp:
            if strip:
                return [v.strip() for v in list(fp.readlines())]
            else:
                return list(fp.readlines())
    else:
        with open(filename, 'r') as fp:
            res = []
            for i in range(count):
                if strip:
                    res.append(fp.readline().strip())
                else:
                    res.append(fp.readline())
        return res

def nth(s, idx=0):
    return s[idx]

def fileexist(f):
    return os.path.exists(f)

nth_1 = functools.partial(nth, idx=1)
nth_2 = functools.partial(nth, idx=2)
nth_3 = functools.partial(nth, idx=3)
nth_4 = functools.partial(nth, idx=4)
nth_5 = functools.partial(nth, idx=5)
nth_6 = functools.partial(nth, idx=6)
nth_7 = functools.partial(nth, idx=7)
nth_8 = functools.partial(nth, idx=8)
nth_9 = functools.partial(nth, idx=9)

if __name__ == '__main__':
    print readfile("./streem", 10)
    print readfile("./test")
