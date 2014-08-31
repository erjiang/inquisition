from pypes import DictType, FuncType, SomeType, Overload, unknown

# int binops depend on the second type
int_binop_t = Overload([
    FuncType(['int', 'int'], 'int'),
    FuncType(['int', 'float'], 'float'),
    FuncType(['int', 'complex'], 'complex')
])

float_binop_t = FuncType(['float', 'float'], 'float')

classes = {
#    'dict': {
#        "_": FuncType([SomeType([DictType,
    'float': {
        "_": Overload([FuncType([], 'float'), FuncType([unknown], 'float')]),
        "__add__": float_binop_t,
        "__mul__": float_binop_t,
        "__sub__": float_binop_t
    },
    'int': {
        "_": Overload([FuncType([], 'int'), FuncType([unknown], 'int')]),
        "__add__": int_binop_t,
        "__mul__": int_binop_t,
        "__sub__": int_binop_t
    },
}

funcs = {
    'print': FuncType([unknown], None)
}
