def foo() -> int:
    return 42

if True:
    y = foo() + 'a'  ##ERROR can't add int and str
