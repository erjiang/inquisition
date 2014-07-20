# empty list should satisfy any kind of list


def foo(x: [int]) -> int:
    if len(x) > 0:
        return x[0]
    else:
        return 42


foo([])
