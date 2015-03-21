import functools
import os
import re
from streem import Streem

def isstr(v):
    return isinstance(v, list) or isinstance(v, tuple)

#===========================================================
#================== Compare Funcs ==========================
#===========================================================

@Streem.reduce_func
def echo(x):
    print x

@Streem.filter_func
def eq(x, y):
    return x == y

@Streem.filter_func
def neq(x, y):
    return x != y

@Streem.filter_func
def gt(x, y):
    return x > y

@Streem.filter_func
def lt(x, y):
    return x < y

@Streem.filter_func
def gte(x, y):
    return x >= y

@Streem.filter_func
def lte(x, y):
    return x <= y

#===========================================================
#=================== String Funcs ==========================
#===========================================================

def capitalize(s):
    return s.capitalize()

@Streem.filter_func
def startswith(s, v):
    return s.startswith(v)

@Streem.filter_func
def endswith(s, v):
    return s.endswith(v)

@Streem.filter_func
def contains(s, v):
    if isinstance(s):
        return v in s
    else:
        return s.find(v) >= 0

def replace(s, ori, tgt):
    s.replace(ori, tgt)
    return s

def strip(s, v=None):
    if v is None:
        return s.strip()
    else:
        return s.strip(v)

def split(s, sep=None):
    if sep is None:
        return s.split()
    else:
        return s.split(sep)

#===========================================================
#=================== File Funcs ============================
#===========================================================

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

def fileexist(f):
    return os.path.exists(f)

#===========================================================
#=================== List Funcs ============================
#===========================================================

def append(l, v):
    l.append(v)
    return l

def sublist(l, start=0, end=None):
    if end is None:
        return l[start:]
    else:
        return l[start:end]

def nth(s, idx=0):
    return s[idx]

def join(s, sep=','):
    return sep.join(s)

nth_1 = functools.partial(nth, idx=1)
nth_2 = functools.partial(nth, idx=2)
nth_3 = functools.partial(nth, idx=3)
nth_4 = functools.partial(nth, idx=4)
nth_5 = functools.partial(nth, idx=5)
nth_6 = functools.partial(nth, idx=6)
nth_7 = functools.partial(nth, idx=7)
nth_8 = functools.partial(nth, idx=8)
nth_9 = functools.partial(nth, idx=9)

#===========================================================
#=================== Regular Expression Funcs ==============
#===========================================================

@Streem.filter_func
def reMatch(s, pattern):
    return re.match(pattern, s) is not None
