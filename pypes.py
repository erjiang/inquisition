class FuncType():
    args = []
    kwargs = []
    ret = None
    def __init__(self, args, rv, kwargs=None):
        self.args = args
        self.ret = rv
        if kwargs is not None:
            self.kwargs = kwargs

    def __str__(self):
        kwargs = ["%s=%s" % (k, v) for k, v in self.kwargs]
        args = ", ".join(list(map(str, self.args)) + self.kwargs)
        return "(%s) -> %s" % (args, str(self.ret))


class AnyType():
    def __init__(self, magic_words=None):
        if magic_words != "nuh-uh-uh":
            raise Exception("Shouldn't instantiate AnyType")
    def __str__(self):
        return "?"


unknown = AnyType("nuh-uh-uh")


# need to pattern match on function args
class Overload(set): # :: set(FuncType)
    def for_args(self, ls):
        for overload in self:
            if overload.args == ls:
                return overload.ret
        raise Heresy("No.")


def type_fits(A, B):
    """
    Check whether type A is a valid B.
    A can be a valid B if any of the following are true:
      * A==B
      * B is AnyType
      * B is SomeType and A is in B
      * B is Maybe(X) and A is None or X
    """
    if A == B:
        return True
    elif B == unknown:
        return True
    elif isinstance(B, SomeType):
        return A in B
    elif isinstance(B, Maybe):
        return A is None or type_fits(A, B.concrete)
    else:
        return False


class Maybe():
    """
    Represents a Nunnable type - a type that can be either the concrete type,
    or None. For example, Maybe(int) may be int or may be None.
    """
    concrete = None
    def __init__(self, concrete):
        if concrete is None:
            raise ValueError("Can't have Maybe(None) - doesn't make sense")
        self.concrete = concrete


SomeType = set


Num = set(['int', 'float'])


class Heresy(Exception):
    ast_obj = None
    message = None
    def __init__(self, message, ast_obj):
        self.message = message 
        self.ast_obj = ast_obj

    def __repr__(self):
        return "<Heresy %s %s>" % (repr(self.message), self.ast_obj)

    def __str__(self):
        return str(self.ast_obj.lineno) + ": " + self.message


class Suspicion(Heresy):
    def __repr__(self):
        return "<Suspicion %s %s>" % (repr(self.message), self.ast_obj)
