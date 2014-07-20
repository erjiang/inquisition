# Test that we can use inferred type of functions

def foo():
    def bar() -> int:
        return 42
    return bar

foo()() + 'a' ##ERROR can't add int to str
