#!/bin/env python
import ast
import re

find_sig = re.compile('#::\s*(.*?)$') #:: re.pattern

def grab_types(f):
    lines = f.readlines()
    types = {} #::Map(int, str)

    for lineno, line in enumerate(lines):
        match = find_sig.search(line)
        if match:
            annotation = match.groups()[0]
            types[lineno] = ast.parse(annotation).body[0].value

    return types
