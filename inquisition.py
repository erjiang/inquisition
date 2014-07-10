#!/usr/bin/env python3

import ast
import sys
from env import Env
import pypes
from pypes import Heresy

def main(f):
    contents = open(f, 'r').read()
    code = ast.parse(contents, filename=f)

    env = Env()

    for val in code.body:
        try:
            if isinstance(val, ast.FunctionDef):
                env.add(val.name, get_type(val, env))
            else:
                get_type(val, env)
        except Heresy as e:
            print(str(e))

    for k, v in env.values.items():
        print("%s :: %s" % (k, v))


def get_type(val, env):
    if isinstance(val, ast.FunctionDef):
        return get_function_type(val, env)
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
            raise ValueError("Don't understand " + repr(val.n))
    else:
        raise ValueError("Don't understand " + repr(val))


def get_function_type(ast_func, env):
    params = [get_arg_type(arg, env) for arg in ast_func.args.args]
    if ast_func.returns is not None:
        rv = ast_func.returns.id
    else:
        rv = pypes.unknown
    return pypes.FuncType(params, rv)

def get_arg_type(ast_arg, env):
    if ast_arg.annotation:
        return ast_arg.annotation.id
    else:
        return pypes.unknown

def get_expr_type(expr, env):
    if isinstance(expr.value, ast.Call):
        return get_call_type(expr.value, env)
    else:
        raise ValueError("Don't understand " + repr(expr))


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
                            (call.func.id, len(call.args), len(func_t.args)),
                            call)
        for idx, args in enumerate(zip(call.args, func_t.args)):
            arg, arg_t = args
            call_arg_t = get_type(arg, env)
            if call_arg_t != arg_t:
                raise Heresy("Argument %d of call to %s should be %s, not %s" %
                                (idx, call.func.id, arg_t, call_arg_t))


if __name__ == "__main__":
    main(sys.argv[1])
