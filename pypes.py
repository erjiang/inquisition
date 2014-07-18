class Type():
    def accepts(self, T):
        """
        Returns true if this the type T is equal to this type or is a subset of
        this type.
        """
        return T == self

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__str__())


class FuncType(Type):
    args = []
    kwargs = []
    ret = None
    def __init__(self, args, rv, kwargs=None):
        self.args = args
        self.ret = rv
        if kwargs is not None:
            self.kwargs = kwargs

    def accepts_args(self, given_args):
        if len(self.args) != len(given_args):
            return False

        for idx, args in enumerate(zip(self.args, given_args)):
            my_arg, call_arg = args
            if not type_fits(call_arg, my_arg):
                return False
        return True

    def accepts(self, T):
        if not isinstance(T, FuncType):
            return False
        if len(T.args) != len(self.args):
            return False
        if not type_fits(T.ret, self.ret):
            return False
        # check that all the args match
        # TODO: kwargs
        return all([type_fits(A, B) for A, B in zip(self.args, T.args)])

    def __repr__(self):
        return "<FuncType %s>" % self.__str__()

    def __str__(self):
        kwargs = ["%s=%s" % (k, v) for k, v in self.kwargs]
        args = ", ".join(list(map(str, self.args)) + self.kwargs)
        return "(%s) -> %s" % (args, str(self.ret))


class AnyType(Type):
    def __init__(self, magic_words=None):
        if magic_words != "nuh-uh-uh":
            raise Exception("Shouldn't instantiate AnyType")
    def __str__(self):
        return "?"

    def accepts(self, T):
        """
        AnyType can be anything!
        """
        return True


unknown = AnyType("nuh-uh-uh")


# need to pattern match on function args
class Overload(set): # :: set(FuncType)
    def for_args(self, ls):
        possibilities = SomeType()
        for overload in self:
            if len(overload.args) != len(ls):
                continue
            if all([type_fits(A, B) for A, B in zip(ls, overload.args)]):
                possibilities.add(overload.ret)
        if len(possibilities) == 1:
            return possibilities.pop()
        if not possibilities:
            raise ValueError("Can't fit %s to %s", (ls, self))
        return possibilities

    def accepts_args(self, ls):
        """
        Just check to see if there are any possible return types. If we get the
        empty set, it means it couldn't match on any of the overloads.
        """
        return self.for_args(ls)

    def accepts(self, T):
        return any([type_fits(T, X) for X in self])


class ListType(Type):
    # using a string here should be ok because other strings shouldn't find
    # their way into the type system
    inner = "emptylist"
    
    def __init__(self, inner_t="emptylist"):
        self.inner = inner_t

    def accepts(self, T):
        if isinstance(T, ListType):
            # The empty list fits all lists
            if self.inner == "emptylist":
                return True
            return type_fits(T.inner, self.inner)
        return False

    def __repr__(self):
        return "<ListType %s>" % self.inner

    def __str__(self):
        return "[%s]" % self.inner


class DictType(Type):
    k = "emptydict"
    v = "emptydict"

    def __init__(self, k_t="emptydict", v_t="emptydict"):
        if v_t == "emptydict" and k_t != v_t:
            raise ValueError("DictType requires both key and value type.")
        self.k = k_t
        self.v = v_t

    def accepts(self, T):
        if isinstance(T, DictType):
            if self.k == "emptydict"
            return type_fits(T.k, self.k) and type_fits(T.v, self.v)
        return False


def type_fits(A, B):
    """
    Check whether type A is a valid B.
    A can be a valid B if any of the following are true:
      * A==B
      * B is AnyType
      * B is SomeType and A is in B
      * B is Maybe(X) and A is None or X
    """
    import inquisition
    if inquisition.DEBUG_LEVEL > 2:
        print("checking type_fits(%s, %s)?" % (A, B))
    if A == B:  # if B is a str or A==B
        return True
    elif isinstance(B, str):
        return False # by this point we know that A != B
    elif B == unknown:
        return True
    else:  # assume that B is a Type sub-class
        return B.accepts(A)


class Maybe(Type):
    """
    Represents a Nunnable type - a type that can be either the concrete type,
    or None. For example, Maybe(int) may be int or may be None.
    """
    concrete = None
    def __init__(self, concrete):
        if concrete is None:
            raise ValueError("Can't have Maybe(None) - doesn't make sense")
        self.concrete = concrete

    def accepts(self, T):
        return T is None or type_fits(T, self.concrete)


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
