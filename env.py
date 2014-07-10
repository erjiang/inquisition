# maps variable names to their types
class Env():
    parent = None
    values = {}

    def __init__(self, values=None, parent=None):
        self.parent = parent
        if isinstance(values, dict):
            self.values = values

    def lookup(self, name):
        if name in self.values:
            return self.values[name]
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return None

    def __getitem__(self, name):
        return self.lookup(name)

    def shallow_lookup(self, name):
        if name in self.values:
            return self.values[name]
        else:
            return None

    def __contains__(self, x):
        if x in self.values:
            return True
        elif self.parent is not None:
            return x in self.parent
        else:
            return False

    def add(self, k, v):
        self.values[k] = v

    def extend(self):
        return Env(parent=self)

    def __repr__(self):
        if self.parent is None:
            return "(" + " ".join(["%s:%s" % (k, v) for (k, v) in self.values.items()]) + ")"
        else:
            return "(" + " ".join(["%s:%s" % (k, v) for (k, v) in self.values.items()]) + " " + self.parent.__repr__() + ")"
