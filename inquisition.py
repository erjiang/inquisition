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

# map these constants to their types so that we don't interpret them as vars
# we'll just yell at you if you try to redefine them
CONSTANTS = {
    "None": "None",
    "True": "bool",
    "False": "bool"
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

    results = run_through(code.body, env, top_level=True, catch_errors=True)

    for e in sorted(results['errors'], key=lambda e: e.ast_obj.lineno):
        print(str(e))


def run_through(exprs, env, top_level=False, catch_errors=False, expected_return_type=pypes.unknown):
    """
    Runs through a list of expressions, e.g. a module top-level or a function body.
    Returns a dict of errors, values, and the return type (of a function).
    """

    return_type = "noreturn"

    errors = set()

    # first get all top-level declared types without going into functions
    for expr in exprs:
        try:
            if isinstance(expr, ast.FunctionDef):
                env.add(expr.name, get_func_type(expr, env))
        except Heresy as e:
            if catch_errors:
                errors.add(e)
            else:
                raise e
        except LazyError as e:
            if DEBUG_LEVEL > 0:
                print("Unimplemented: " + str(e))


    for expr in exprs:
        try:
            if isinstance(expr, ast.FunctionDef):
                env.add(expr.name, get_func_type_for_real(expr, env))
            elif isinstance(expr, ast.Assign):
                if not isinstance(expr.targets[0], ast.Name):
                    raise LazyError("Don't know how to deal with tuple assignment", expr)
                if len(expr.targets) > 1:
                    raise LazyError("Don't know how to deal with multiple targets.", expr)
                if expr.targets[0].id in CONSTANTS:
                    raise Heresy("Tried to redefine built-in '%s'" % expr.targets[0].id, expr)
                env.add(expr.targets[0].id, get_type(expr.value, env))
            elif isinstance(expr, ast.If):
                run_if(expr, env, expected_return_type)
            elif isinstance(expr, ast.Return):
                if top_level:
                    raise Heresy("Can't 'return' outside of function", expr)
                return_type = get_type(expr.value, env)
                if DEBUG_LEVEL > 2:
                    print("checking if %s fits expected return %s" %
                          (return_type, expected_return_type))
                if not pypes.type_fits(return_type, expected_return_type):
                    raise Heresy("Trying to return '%s' but should return '%s'" %
                                 (return_type, expected_return_type),
                                 expr)

            else:
                get_type(expr, env)
        except Heresy as e:
            if catch_errors:
                errors.add(e)
            else:
                raise e
        except LazyError as e:
            if DEBUG_LEVEL > 0:
                print("Unimplemented: " + str(e))

    if top_level and DEBUG_LEVEL > 0:
        for k, v in env.values.items():
            print("%s :: %s" % (k, v))

    return {
        "errors": errors,
        "returns": return_type,
        "values": env.values
    }


def run_if(expr, env, expected_return_type):
    """
    TODO: support elif
    """

    if DEBUG_LEVEL > 2:
        print("Exploring if statement expecting to return %s" % expected_return_type)

    all_branches_return = True

    possible_returns = set()
    if_env = env.extend()
    if_body = run_through(expr.body, if_env, expected_return_type=expected_return_type)
    if if_body['returns'] != "noreturn":
        possible_returns = pypes.merge_types(possible_returns, if_body['returns'])
    else:
        all_branches_return = False
    if expr.orelse:  # if there are else clauses
        else_env = env.extend()
        else_body = run_through(expr.orelse, else_env, expected_return_type=expected_return_type)
        if else_body['returns'] != "noreturn":
            possible_returns = pypes.merge_types(possible_returns, else_body['returns'])
        else:
            all_branches_return = True

    if len(possible_returns) == 1:
        possible_returns = possible_returns.pop()

    return {
        "returns": possible_returns,
        "all_branches_return": all_branches_return
    }

def get_type(expr, env):
    if DEBUG_LEVEL > 2:
        print("Getting type of %s" % expr)
    if isinstance(expr, ast.FunctionDef):
        return get_func_type(expr, env)
    elif isinstance(expr, ast.Call):
        return get_call_type(expr, env)
    elif isinstance(expr, ast.Name):
        return get_name_type(expr, env)
    elif isinstance(expr, ast.Assign):
        raise LazyError("run_through should handle ast.Assign, not get_type", expr)
    elif isinstance(expr, ast.Expr):
        get_expr_type(expr, env)
    elif isinstance(expr, ast.Str):
        return "str"
    elif isinstance(expr, ast.Num):
        if isinstance(expr.n, int):
            return 'int'
        elif isinstance(expr.n, float):
            return 'float'
        elif isinstance(expr.n, complex):
            return 'complex'
        else:
            raise LazyError("Don't understand Num " + repr(expr.n), expr)
    elif isinstance(expr, ast.BinOp):
        if DEBUG_LEVEL > 2:
            print("Type of binop at line %d is %s" % (expr.lineno, get_binop_type(expr, env)))
        return get_binop_type(expr, env)
    elif isinstance(expr, ast.List):
        return get_list_type(expr, env)
    elif isinstance(expr, ast.Dict):
        return get_dict_type(expr, env)   
    elif isinstance(expr, ast.If):
        raise Heresy("if statement found outside module/function body")
    elif isinstance(expr, ast.Pass):
        return None
    else:
        raise LazyError("Don't understand expr " + repr(expr), expr)


def type_annotation2type(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    elif isinstance(expr, ast.List):
        # TODO: create separate errors for invalid type annotations
        if not expr.elts:
            raise Heresy("Cannot type empty list. Try [Any] instead.", expr)
        elif len(expr.elts) > 1:
            raise Heresy("Cannot have multiple types in list.", expr)
        else:
            return pypes.ListType(type_annotation2type(expr.elts[0]))
    elif isinstance(expr, ast.Dict):
        if not expr.keys:
            return Heresy("Cannot type empty dict. Try {Any: Any} instead.", expr)
        elif len(expr.keys) > 1:
            raise Heresy("Cannot have multiple key/value types in dict.", expr)
        else:
            return pypes.DictType(
                type_annotation2type(expr.keys[0]),
                type_annotation2type(expr.values[0]))
    else:
        raise LazyError("Don't understand annotation %s" % expr, expr)


def get_name_type(expr, env):
    if expr.id in CONSTANTS:
        return CONSTANTS[expr.id]
    if expr.id in env:
        return env[expr.id]
    else:
        raise Heresy("Tried using var '%s' but it wasn't defined." % expr.id, expr)


def get_func_type(expr, env):
    """Only looks at the declared type in the signature. Does not examine
    body."""
    params = [get_arg_type(arg, env) for arg in expr.args.args]
    if expr.returns is not None:
        rv = type_annotation2type(expr.returns)
    else:
        rv = pypes.unknown
    return pypes.FuncType(params, rv)


def get_func_type_for_real(expr, env):
    """Uses both the declared type and the inferred type."""
    declared_type = get_func_type(expr, env)
    # create a new scope!!
    if DEBUG_LEVEL > 1:
        print("Diving into %s" % expr.name)

    body_env = env.extend()

    for arg in expr.args.args:
        body_env.add(arg.arg, get_arg_type(arg, env))

    apparent_return_type = get_func_body_type(expr.body, env.extend(), declared_type.ret)
    if not pypes.type_fits(apparent_return_type, declared_type.ret):
        raise Heresy("Return type of '%s' declared as '%s' but seems to be '%s'" %
                     (expr.name, declared_type.ret, apparent_return_type),
                     expr)
    declared_type.ret = apparent_return_type
    return declared_type


def get_func_body_type(exprs, env, expected_return_type):
    """Given a list of exprs, get the type of what the list returns. E.g., look
    for a return statement."""
    run = run_through(exprs, env, expected_return_type=expected_return_type)
    return run['returns']

def get_arg_type(ast_arg, env):
    if ast_arg.annotation:
        return ast_arg.annotation.id
    else:
        return pypes.unknown


def get_expr_type(expr, env):
    """
    This takes an ast.Expr, not to be confused with any old 'expr'.
    """
    return get_type(expr.value, env)


def get_assign_type(expr, env):
    return get_type(expr.value, env)


def is_callable(t):
    if isinstance(t, pypes.FuncType):
        return True
    else:
        return False


def get_call_type(call, env):
    if isinstance(call.func, ast.Attribute):
        raise LazyError("Don't know how to do method calls.", call)
    # TODO: check if func is expr, maybe use get_type instead?
    func_t = get_type(call.func, env)
    if DEBUG_LEVEL > 2:
        print("call to %s" % func_t)
    if not isinstance(func_t, (pypes.FuncType, pypes.ClassType)):
        raise Heresy("'%s' is not callable." % func_t, call)
    if len(call.args) != len(func_t.args):
        raise Heresy("Function %s expects %d arguments, %d provided" %
                        (call.func.id, len(func_t.args), len(call.args)),
                        call)
    for idx, args in enumerate(zip(call.args, func_t.args)):
        arg, arg_t = args
        call_arg_t = get_type(arg, env)
        if not pypes.type_fits(call_arg_t, arg_t):
            raise Heresy("Argument %d of call to %s should be %s, not %s" %
                         (idx, call.func.id, arg_t, call_arg_t),
                         call)
    return func_t.ret


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


def get_list_type(expr, env):
    """
    Right now, we only look at the first element in the list and assume that
    all the other elements in the list are the same.
    """
    if not expr.elts:  # it's just an empty list
        return pypes.ListType()
    else:
        return pypes.ListType(get_type(expr.elts[0], env))


def get_dict_type(expr, env):
    """
    Right now, we only look at the first element in the list and assume that
    all the other elements in the list are the same.
    """
    if not expr.values:  # it's just an empty list
        return pypes.DictType()
    else:
        return pypes.DictType(
            get_type(expr.keys[0], env),
            get_type(expr.values[0], env))


if __name__ == "__main__":
    if 'DEBUG' in os.environ:
        DEBUG_LEVEL = int(os.environ['DEBUG'])
    main(sys.argv[1])
