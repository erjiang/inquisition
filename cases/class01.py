class Foo():

    y = 0

    def __init__(self, a: int):
        self.y = a

f = Foo('str')  ##ERROR class initializer expects an int
