def foo():
    def bar() -> int:
        return 42
    return bar

foo()

foo()()
