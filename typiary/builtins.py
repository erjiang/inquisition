from pypes import FuncType, Overload

# int binops depend on the second type
int_binop_t = Overload([
    FuncType(['int', 'int'], 'int'),
    FuncType(['int', 'float'], 'float'),
    FuncType(['int', 'complex'], 'complex')
])

float_binop_t = FuncType(['float', 'float'], 'float')

builtins = {
    'int': {
        "__add__": int_binop_t,
        "__mul__": int_binop_t,
        "__sub__": int_binop_t
    },
    'float': {
        "__add__": float_binop_t,
        "__mul__": float_binop_t,
        "__sub__": float_binop_t
    }
}
