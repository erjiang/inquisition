#!/usr/bin/env python3

import ast
import os
import sys


from env import Env
import pypes
from pypes import Heresy, Suspicion
from typiary import builtins

DEBUG_LEVEL = 0


# map ast binop objects to python methods
BINOPS = {
    "Add": "__add__",
    "Mult": "__mul__"
}

class LazyError(Exception):
    ast_obj = None
    message = None
    def __init__(self, message, ast_obj=None):
        self.message = message
        self.ast_obj = ast_obj

    def __repr__(self):
        return "<LazyError %s %s>" % (repr(self.message), self.ast_obj)

    def __str__(self):
        return str(self.ast_obj.lineno) + ": " + self.message


def main(f):
    contents = open(f, 'r').read()
    code = ast.parse(contents, filename=f)

    env = Env()

    run_through(code.body, env, top_level=True)


def run_through(exprs: list, env, top_level=False):

    return_type = None

    errors = set()

    for val in exprs:
        try:
            if isinstance(val, ast.FunctionDef):
                env.add(val.name, get_func_type(val, env))
            elif isinstance(val, ast.Assign):
                if not isinstance(val.targets[0], ast.Name):
                    raise LazyError("Don't know how to deal with tuple assignment", val)
                if len(val.targets) > 1:
                    raise LazyError("Don't know how to deal with multiple targets.", val)
                env.add(val.targets[0].id, get_type(val.value, env))
            elif isinstance(val, ast.Return):
                return_type = get_type(val.value, env)
            else:
                get_type(val, env)
        except Heresy as e:
            if top_level:
                errors.add(e)
            else:
                raise e
        except LazyError as e:
            if DEBUG_LEVEL > 0:
                print("Unimplemented: " + str(e))

    for val in exprs:
        try:
            if isinstance(val, ast.FunctionDef):
                env.add(val.name, get_func_type_for_real(val, env))
        except Heresy as e:
            if top_level:
                errors.add(e)
            else:
                raise e
        except LazyError as e:
            if DEBUG_LEVEL > 0:
                print("Unimplemented: " + e.message)

    for e in sorted(errors, key=lambda e: e.ast_obj.lineno):
        print(str(e))

    if top_level and DEBUG_LEVEL > 0:
        for k, v in env.values.items():
            print("%s :: %s" % (k, v))

    return return_type

def get_type(val, env):
    if isinstance(val, ast.FunctionDef):
        return get_func_type(val, env)
    elif isinstance(val, ast.Name):
        if val.id in env:
            return env[val.id]
        else:
            raise Heresy("Tried using var '%s' but it wasn't defined." % val.id, val)
    elif isinstance(val, ast.Assign):
        raise LazyError("run_through should handle ast.Assign, not get_type", val)
    elif isinstance(val, ast.Expr):
        get_expr_type(val, env)
    elif isinstance(val, ast.Str):
        return "str"
    elif isinstance(val, ast.Num):
        if isinstance(val.n, int):
            return 'int'
        elif isinstance(val.n, float):
            return 'float'
        elif isinstance(val.n, complex):
            return 'complex'
        else:
            raise LazyError("Don't understand Num " + repr(val.n), val)
    elif isinstance(val, ast.BinOp):
        return get_binop_type(val, env)
    else:
        raise LazyError("Don't understand val " + repr(val), val)


def get_func_type(ast_func, env):
    """Only looks at the declared type in the signature. Does not examine
    body."""
    params = [get_arg_type(arg, env) for arg in ast_func.args.args]
    if ast_func.returns is not None:
        rv = ast_func.returns.id
    else:
        rv = pypes.unknown
    return pypes.FuncType(params, rv)


def get_func_type_for_real(func, env):
    """Uses both the declared type and the inferred type."""
    declared_type = get_func_type(func, env)
    # create a new scope!!
    if DEBUG_LEVEL > 1:
        print("Diving into %s" % func.name)

    body_env = env.extend()

    for arg in func.args.args:
        body_env.add(arg.arg, get_arg_type(arg, env))

    apparent_return_type = get_func_body_type(func.body, env.extend())
    if not pypes.type_fits(apparent_return_type, declared_type.ret):
        raise Heresy("Return type of '%s' declared as '%s' but seems to be '%s'" %
                     (func.name, declared_type.ret, apparent_return_type),
                     func)
    declared_type.ret = apparent_return_type
    return declared_type


def get_func_body_type(exprs, env):
    """Given a list of exprs, get the type of what the list returns. E.g., look
    for a return statement."""
    return run_through(exprs, env)

def get_arg_type(ast_arg, env):
    if ast_arg.annotation:
        return ast_arg.annotation.id
    else:
        return pypes.unknown


def get_expr_type(expr, env):
    if isinstance(expr.value, ast.Call):
        return get_call_type(expr.value, env)
    else:
        raise LazyError("Don't understand expr " + repr(expr), val)


def get_assign_type(expr, env):
    return get_type(expr.value)


def is_callable(t):
    if isinstance(t, pypes.FuncType):
        return True
    else:
        return False


def get_call_type(call, env):
    if call.func.id in env:
        func_t = env[call.func.id]
        if len(call.args) != len(func_t.args):
            raise Heresy("Function %s expects %d arguments, %d provided" %
                            (call.func.id, len(func_t.args), len(call.args)),
                            call)
        for idx, args in enumerate(zip(call.args, func_t.args)):
            arg, arg_t = args
            call_arg_t = get_type(arg, env)
            if call_arg_t != arg_t:
                raise Heresy("Argument %d of call to %s should be %s, not %s" %
                             (idx, call.func.id, arg_t, call_arg_t),
                             call)
        return func_t.ret
    else:
        raise Heresy("Tried calling %s which doesn't seem to exist" %
                     (call.func.id),
                     call)


def get_binop_type(expr, env):
    """
    expr should be an ast.BinOp, and this needs to convert the binop to the
    corresponding method on the left type.
    Only builtin types supported right now :(
    TODO: add support for custom types
    """
    left_t = get_type(expr.left, env)
    right_t = get_type(expr.right, env)

    # lookup which method goes with this binop
    # can't directly do BINOPS[expr.op], unfortunately
    binop_method = BINOPS[expr.op.__class__.__name__]

    if left_t not in builtins.builtins:
        if DEBUG_LEVEL > 0:
            print("Type %s is not recognized. Can't typecheck this binop." % left_t)
        return pypes.unknown

    binop_t = builtins.builtins[left_t][binop_method]
    # should be a FuncType

    try:
        return binop_t.for_args([left_t, right_t])
    except ValueError:
        raise Heresy("Tried doing (%s %s %s) which doesn't match type %s" %
                     (left_t, expr.op.__class__.__name__, right_t, binop_t),
                     expr)


if __name__ == "__main__":
    if 'DEBUG' in os.environ:
        DEBUG_LEVEL = int(os.environ['DEBUG'])
    main(sys.argv[1])
