#!/usr/bin/env python3

import ast
import sys
from env import Env
import pypes
from pypes import Heresy


class LazyError(Exception):
    ast_obj = None
    message = None
    def __init__(self, message, ast_obj=None):
        self.message = message
        self.ast_obj = ast_obj

    def __repr__(self):
        return "<LazyError %s %s>" % (repr(self.message), self.ast_obj)

    def __str__(self):
        return self.message


def main(f):
    contents = open(f, 'r').read()
    code = ast.parse(contents, filename=f)

    env = Env()

    run_through(code.body, env, top_level=True)


def run_through(exprs: list, env, top_level=False):

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
            else:
                get_type(val, env)
        except Heresy as e:
            print(str(e))
        except LazyError as e:
            print("Unimplemented: " + e.message)

    for val in exprs:
        try:
            if isinstance(val, ast.FunctionDef):
                env.add(val.name, get_func_type_for_real(val, env))
        except Heresy as e:
            print(str(e))
        except LazyError as e:
            print("Unimplemented: " + e.message)

    if top_level:
        for k, v in env.values.items():
            print("%s :: %s" % (k, v))


def get_type(val, env):
    if isinstance(val, ast.FunctionDef):
        return get_func_type(val, env)
    elif isinstance(val, ast.Assign):
        raise LazyError("run_through should handle ast.Assign, not get_type")
    elif isinstance(val, ast.Expr):
        get_expr_type(val, env)
    elif isinstance(val, ast.Str):
        return "str"
    elif isinstance(val, ast.Num):
        if isinstance(val.n, int):
            return 'int'
        elif isinstance(val.n, float):
            return 'float'
        else:
            raise LazyError("Don't understand " + repr(val.n))
    else:
        raise LazyError("Don't understand " + repr(val))


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
    print("Diving into %s" % func.name)
    apparent_type = get_func_body_type(func.body, env.extend())
    return declared_type


def get_func_body_type(exprs, env):
    """Given a list of exprs, get the type of what the list returns. E.g., look
    for a return statement."""
    run_through(exprs, env)

def get_arg_type(ast_arg, env):
    if ast_arg.annotation:
        return ast_arg.annotation.id
    else:
        return pypes.unknown


def get_expr_type(expr, env):
    if isinstance(expr.value, ast.Call):
        return get_call_type(expr.value, env)
    else:
        raise LazyError("Don't understand " + repr(expr))


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
        print(env)
        if len(call.args) != len(func_t.args):
            raise Heresy("Function %s expects %d arguments, %d provided" %
                            (call.func.id, len(call.args), len(func_t.args)),
                            call)
        for idx, args in enumerate(zip(call.args, func_t.args)):
            arg, arg_t = args
            call_arg_t = get_type(arg, env)
            if call_arg_t != arg_t:
                raise Heresy("Argument %d of call to %s should be %s, not %s" %
                                (idx, call.func.id, arg_t, call_arg_t))
        return func_t.ret
    else:
        raise Heresy("Tried calling %s which doesn't seem to exist" %
                     (call.func.id),
                     call)


if __name__ == "__main__":
    main(sys.argv[1])
