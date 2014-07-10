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
    def __str__(self):
        return "?"


unknown = AnyType()


class SomeType():
    """Annoy PL nerds who talk about Sum types."""
    options = []
    def __init__(self, *args):
        self.options = args


class Heresy(Exception):
    ast_obj = None
    message = None
    def __init__(self, message, ast_obj):
        self.message = message 
        self.ast_obj = ast_obj

    def __repr__(self):
        return "<TypeError %s %s>" % (repr(self.message), self.ast_obj)

    def __str__(self):
        return str(self.ast_obj.lineno) + ": " + self.message
