x = 4
def foo() -> int:
    return 42

if x < 0:
    y = foo() + 'a'  ##ERROR can't add int and str
else:
    y = foo() + 'b'  ##ERROR can't add int and str
