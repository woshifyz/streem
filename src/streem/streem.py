#!/usr/bin/env python
# coding: utf8

#=======================================================================================================
#============================================= STREEM CODE =============================================
#=======================================================================================================

from pyparsing import *
import string
import sys
import os, os.path
import inspect
import imp
import uuid
import re

class Streem(object):
    ITEM_SYMBOL = "_"
    VAR_SYMBOL = "@"
    STDIN_SYMBOL = "INPUT"

    TAG_MAP = 1
    TAG_REDUCE = 2
    TAG_FILTER = 4
    TAG_INPUT = 8

    _ENABLE_DEBUG = False
    _ENABLE_STRICT_MODE = False

    @classmethod
    def filter_func(cls, f):
        def wrapper(*args, **kw):
            return f(*args, **kw)
        wrapper.__tag__ = cls.TAG_FILTER
        return wrapper

    @classmethod
    def reduce_func(cls, f):
        def wrapper(*args, **kw):
            return f(*args, **kw)
        wrapper.__tag__ = cls.TAG_REDUCE
        return wrapper

    @classmethod
    def add_load_dir(cls, path):
        FuncLoader._DEFAULT_LOAD_ORDER.insert(0, args.include)

    @classmethod
    def is_debug(cls, d):
        cls._ENABLE_DEBUG = d

    @classmethod
    def is_strict_mode(cls, m):
        cls._ENABLE_STRICT_MODE = m

    @classmethod
    def parse(cls, content):

        addop = Literal('+') | Literal('-')
        multop = Literal("*") | Literal("/") | Literal("%")
        point = Literal('.')

        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        assign = Literal( "=" ).suppress()

        number = Word(nums)
        integer = Combine( Optional(addop) + number ).setParseAction(lambda t: int(t[0]))
        floatnumber = Combine( integer + Optional( point + number ) ).setParseAction(lambda t: float(t[0]))
        constant = (integer | floatnumber | quotedString.setParseAction(lambda t: t[0][1:-1])).setParseAction(lambda t : Constant(t[0]))

        normalVariable = Word(string.ascii_uppercase, alphanums + '_').setParseAction(lambda t: Variable(t[0]))
        specialKeyword = ( Literal(cls.ITEM_SYMBOL) | Literal(cls.VAR_SYMBOL) | Literal(cls.STDIN_SYMBOL) ).setParseAction(lambda t: KVariable(t[0]))
        conKeywords = (Literal("True") | Literal("False") | Literal("None")).setParseAction(lambda t: ConKeyword(t[0]))
        variable = (conKeywords | specialKeyword | normalVariable)

        funcName = Word(string.ascii_lowercase, alphanums + '_')

        expr = Forward()
        funcCall = Forward()
        atom = (constant | funcCall | variable | ( lpar + expr + rpar )).setParseAction(lambda t: Atom(t[0]))
        term = Group(atom.setResultsName("left") + ZeroOrMore(( Group(multop.setResultsName("op") + atom.setResultsName("atom")))).setResultsName("right")).setParseAction(lambda t: Term(t[0]))
        expr << Group(term.setResultsName("left") + ZeroOrMore( ( Group(addop.setResultsName("op") + term.setResultsName("term")))).setResultsName("right")).setParseAction(lambda t: Expr(t[0]))

        judgeExpr = Group(expr.setResultsName("check") + Literal("?") + expr.setResultsName("success") + Literal(":") + expr.setResultsName("failure")).setParseAction(lambda t: JudgeExpr(t[0]))
        complexExpr = (judgeExpr | expr)

        funcCall << Group(funcName.setResultsName("name") + lpar + delimitedList(complexExpr).setResultsName("params") + rpar).setParseAction(lambda t: FuncCall(t[0]))


        assignStmt = Group(variable.setResultsName("key") + assign + complexExpr.setResultsName("value")).setParseAction(lambda t: AssignStmt(t[0]))
        simpleStmt = ( assignStmt | complexExpr )
        complexFunc = Group(delimitedList(variable).setResultsName("args") + Suppress("->") + delimitedList(simpleStmt, ';').setResultsName("stmts")).setParseAction(lambda t: Func(t[0]))

        func = ( complexFunc | complexExpr | funcName.setParseAction(lambda t: FuncCall.fromFuncName(t[0])) )

        funcSep = ( Literal('|') | Literal('&') )

        codeContent = Group(func.setResultsName("left") + ZeroOrMore(Group(funcSep.setResultsName("op") + func.setResultsName("func"))).setResultsName("right")).setParseAction(lambda t: CodeContent(t[0]))
        return codeContent.parseString(content)

class Helper(object):

    @classmethod
    def debug(cls, *args):
        if Streem._ENABLE_DEBUG:
            print args

    @staticmethod
    def isIter(v):
        return hasattr(v, '__iter__')

    @staticmethod
    def cal(op, left, right):
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        elif op == '%':
            return left % right
        raise Exception("not support op " + op)

class Context(object):
    kvs = {}

    @classmethod
    def init(cls, value=None, item=None):
        cls.kvs = {Streem.ITEM_SYMBOL: item, Streem.VAR_SYMBOL: value}

    @classmethod
    def set(cls, key, value):
        cls.kvs[key] = value

    @classmethod
    def get(cls, key):
        if not cls.kvs.has_key(key):
            raise Exception("cannot find key in this ctx")
        return cls.kvs.get(key)

    @classmethod
    def getSymbol(cls):
        return cls.kvs.get(Streem.ITEM_SYMBOL)

    @classmethod
    def getVar(cls):
        return cls.kvs.get(Streem.VAR_SYMBOL)

def getFuncsOfModule(module):
    members = inspect.getmembers(module)
    funcs = []
    for m in members:
        if callable(m[1]):
            funcs.append(m)
    return funcs

def getFuncByName(name):
    return FuncLoader.instance().getFunc(name)

def realPath(p):
    return os.path.abspath(os.path.expanduser(p))

class StreemFunc(object):

    def __init__(self, name, func, location=None, tag=None):
        self.func = func
        self.location = location
        self.tag = tag
        self.name = name

    def __call__(self, *args, **kw):
        return self.func(*args, **kw)

    def __str__(self):
        return 'func\t%s\t%s' % (self.name, self.location)
    __repr__ = __str__

class FuncLoader(object):
    _DEFAULT_LOAD_ORDER = ['/usr/local/lib/streem', '/usr/lib']
    _ENV_PATH_KEY = 'STREEM_LIB_PATH'
    _MAX_NO_USE_FILE_NUM_IN_ONE_DIR = 500
    _EXCLUDE_PATTERN = (re.compile(r'.*pyparsing.py'),re.compile(r'.*setup.py'))

    _INSTANCE = None

    @classmethod
    def instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def __init__(self, include=None):
        if os.environ.has_key(self._ENV_PATH_KEY):
            self._DEFAULT_LOAD_ORDER.insert(0, os.environ.get(self._ENV_PATH_KEY))

        self.funcStore = {}
        self.initBuildinFuncs()
        self.loadStandardLib()

        self.loadLib()

    def loadStandardLib(self):
        slib = os.path.join(realPath(os.path.dirname(__file__)), "./lib.py")
        self.loadOneFile(slib)

    def initBuildinFuncs(self):
        r_funcs = ('sorted', 'range', 'min', 'max', 'set', 'list', 'sum', 'len')
        m_funcs = ('str', 'int', 'float', 'abs')
        for f in r_funcs:
            self.addFunc(f, eval(f), 'buildin', tag=Streem.TAG_REDUCE)
        for f in m_funcs:
            self.addFunc(f, eval(f), 'buildin', tag=Streem.TAG_MAP)

    def loadLib(self):
        for directory in self._DEFAULT_LOAD_ORDER:
            self.loadOneDir(directory)

    def loadOneDir(self, directory):
        files = self.listPyFiles(directory)
        for f in files:
            self.loadOneFile(f)

    def loadOneFile(self, f):
        module = imp.load_source(str(uuid.uuid4()), f)
        funcs = getFuncsOfModule(module)
        for func in funcs:
            self.addFunc(func[0], func[1], f)

    def addFunc(self, name, func, filename, tag=Streem.TAG_MAP):
        if name in self.funcStore:
            return
        if hasattr(func, '__tag__'):
            tag = func.__tag__
        self.funcStore[name] = StreemFunc(name, func, location=filename, tag=tag)

    def getFunc(self, name):
        if not self.funcStore.has_key(name):
            raise Exception("can not find func %s" % name)
        return self.funcStore.get(name)

    def listPyFiles(self, dir):
        files = set()
        nonLibFileCount = 0
        for root, dirs, fs in os.walk(realPath(dir)):
            if not fs:
                continue
            root = realPath(root)
            for f in fs:
                if f.endswith('.py') and (not self.matchExclude(f)):
                    files.add(os.path.join(root, f))
                else:
                    nonLibFileCount += 1
                    if nonLibFileCount > self._MAX_NO_USE_FILE_NUM_IN_ONE_DIR:
                        raise Exception("too many no use file in lib dir, please check your location")
        return files

    def matchExclude(self, f):
        for pattern in self._EXCLUDE_PATTERN:
            if pattern.match(f):
                return True
        return False

    def listAll(self):
        for name, func in self.funcStore.iteritems():
            print func

class Constant(object):
    def __init__(self, result):
        Helper.debug('fyz constant', result)
        self.value = result

    def eval(self):
        return self.value

    def tag(self):
        return Streem.TAG_MAP

    def __str__(self):
        return str(self.value)
    __repr__ = __str__

class Variable(object):
    def __init__(self, result):
        Helper.debug('fyz variable', result)
        self.name = result

    def eval(self):
        return Context.get(self.name)

    def tag(self):
        return Streem.TAG_MAP

    def __str__(self):
        return self.name
    __repr__ = __str__

class KVariable(object):
    def __init__(self, result):
        Helper.debug('fyz KVariable', result)
        self.name = result

    def eval(self):
        if self.name == Streem.ITEM_SYMBOL:
            return Context.getSymbol()
        elif self.name == Streem.VAR_SYMBOL:
            return Context.getVar()
        elif self.name == Streem.STDIN_SYMBOL:
            return sys.stdin

    def tag(self):
        return Streem.TAG_MAP

    def __str__(self):
        return "<KV>"
    __repr__ = __str__

class ConKeyword(object):
    def __init__(self, result):
        self.name = result.name

    def eval(self):
        return eval(self.name)

    def tag(self):
        if self.name == "True" or self.name == "False":
            return Streem.TAG_FILTER
        return Streem.TAG_MAP

    def __str__(self):
        return self.name
    __repr__ = __str__

class Atom(object):
    def __init__(self, result):
        Helper.debug('fyz atom', result)
        self.value = result

    def eval(self):
        return self.value.eval()

    def tag(self):
        return self.value.tag()

    def __str__(self):
        return str(self.value)
    __repr__ = __str__

class Term(object):
    def __init__(self, result):
        Helper.debug('fyz term', result)
        self.left = result.left
        self.right = result.right or []

    def eval(self):
        result = self.left.eval()
        for op, atom in self.right:
            result = Helper.cal(op, result, atom.eval())
        return result

    def tag(self):
        if self.right:
            return Streem.TAG_MAP
        return self.left.tag()

    def __str__(self):
        result = str(self.left)
        for op, atom in self.right:
            result = '%s %s %s' % (result, op, str(atom))
        return result
    __repr__ = __str__

class Expr(object):
    def __init__(self, result):
        Helper.debug('fyz expr', result)
        self.left = result.left
        self.right = result.right or []

    def eval(self):
        result = self.left.eval()
        for op, term in self.right:
            result = Helper.cal(op, result, term.eval())
        return result

    def tag(self):
        if self.right:
            return Streem.TAG_MAP
        return self.left.tag()

    def __str__(self):
        result = str(self.left)
        for op, term in self.right:
            result = '%s %s %s' % (result, op, str(term))
        return result
    __repr__ = __str__

class FuncCall(object):
    def __init__(self, result=None):
        Helper.debug('fyz funccall', result)
        if result:
            self.name = result.name
            self.params = result.params

    @classmethod
    def fromFuncName(cls, funcName):
        fc = cls()
        fc.name = funcName
        fc.params = (KVariable(Streem.ITEM_SYMBOL),)
        return fc

    def eval(self):
        f = getFuncByName(self.name)
        args = [p.eval() for p in self.params]
        return f(*tuple(args))

    def tag(self):
        f = getFuncByName(self.name)
        return f.tag

    def __str__(self):
        return '<Func>%s(%s)' % (self.name, ','.join([str(v) for v in self.params]))
    __repr__ = __str__

class Func(object):
    def __init__(self, result):
        Helper.debug('fyz func', result)
        self.args = result.args
        self.stmts = result.stmts

        if not (self.args and self.stmts):
            raise Exception("func def error")

    def eval(self):
        if len(self.args) == 1:
            arg = self.args[0]
            Context.set(arg.name, Context.getSymbol())
        else:
            if not Helper.isIter(Context.getSymbol()):
                raise Exception("args num is error, cannot package to it")
            ipt = Context.getSymbol()
            for i, arg in enumerate(self.args):
                if i < len(ipt):
                    Context.set(arg.name, Context.getSymbol()[i])
                else:
                    Context.set(arg.name, None)

        for i, stmt in enumerate(self.stmts):
            res = stmt.eval()
            if i == len(self.stmts) - 1:
                return res

    def tag(self):
        return self.stmts[-1].tag()

class JudgeExpr(object):
    def __init__(self, result):
        Helper.debug('fyz judge', result)
        self.check = result.check[0]
        self.success = result.success[0]
        self.failure = result.failure[0]

    def eval(self):
        if self.check.eval():
            return self.success.eval()
        else:
            return self.failure.eval()

    def tag(self):
        return self.succuss.tag()

class AssignStmt(object):
    def __init__(self, result):
        Helper.debug('fyz assign', result)
        self.key = result.key
        self.value = result.value[0]

    def eval(self):
        Context.set(self.key.name, self.value.eval())
        return None

    def tag(self):
        return Streem.TAG_MAP

    def __str__(self):
        return '%s = %s' % (self.key, self.value)
    __repr__ = __str__

class CodeContent(object):
    def __init__(self, result):
        Helper.debug('fyz block', result)
        self.left = result.left
        self.right = result.right or []

    def eval(self):
        Context.init()
        out = self.left.eval()
        for op, block in self.right:
            if op == '|':   # smart mode
                if not Helper.isIter(out):
                    Context.init(out, out)
                    out = block.eval()
                elif block.tag() == Streem.TAG_FILTER:
                    new_out = []
                    for v in out:
                        Context.init(out, v)
                        try:
                            _res = block.eval()
                            if _res is not None and _res is not False:
                                new_out.append(v)
                        except:
                            if Streem._ENABLE_STRICT_MODE:
                                raise Exception("error in run eval with    %s" % v)
                            else:
                                Helper.debug("error in run eval with    %s" % v)
                                continue
                    out = new_out
                elif block.tag() == Streem.TAG_REDUCE:
                    Context.init(out, out)
                    out = block.eval()
                elif block.tag() == Streem.TAG_MAP:
                    new_out = []
                    for v in out:
                        Context.init(out, v)
                        try:
                            _res = block.eval()
                            new_out.append(_res)
                        except:
                            if Streem._ENABLE_STRICT_MODE:
                                raise Exception("error in run eval with    %s" % v)
                            else:
                                Helper.debug("error in run eval with    %s" % v)
                                continue
                    out = new_out
            elif op == '&':  # force reduce
                Context.init(out, out)
                out = block.eval()
            elif op == '~':  # force map
                if not Helper.isIter(out):
                    Context.init(out, out)
                    out = block.eval()
                else:
                    new_out = []
                    for v in out:
                        Context.init(out, v)
                        try:
                            _res = block.eval()
                            new_out.append(_res)
                        except:
                            if Streem._ENABLE_STRICT_MODE:
                                raise Exception("error in run eval with    %s" % v)
                            else:
                                Helper.debug("error in run eval with    %s" % v)
                                continue
                    out = new_out
            else:
                raise Exception("eval command not support, only support | and & and ~ now")

    def __str__(self):
        result = str(self.left)
        for op, block in self.right:
            result = '%s %s %s' % (result, op, str(block))
        return result
    __repr__ = __str__

#if __name__ == '__main__':
    #import argparse
    #parser = argparse.ArgumentParser()
    #parser.add_argument("content", help="content to eval", default=None)
    #parser.add_argument("-i", "--include", help="add lib dir")
    #parser.add_argument("--debug", help="debug sign", action="store_true")
    #parser.add_argument("--strict", help="turn no strict mode", action="store_true")
    #args = parser.parse_args()

    #if args.include:
        #Streem.add_load_dir(args.include)

    #content = args.content
    #Streem.is_debug(args.debug)
    #Streem.is_strict_mode(args.strict)

    #Streem.parse(content)[0].eval()
