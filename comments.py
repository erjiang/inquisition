#!/bin/env python

import re

find_sig = re.compile('#::\s*(.*?)$') #:: re.pattern

def grab_types(f):
    lines = f.readlines()
    types = {} #::Map(int, str)

    for lineno, line in enumerate(lines):
        match = find_sig.search(line)
        if match:
            types[lineno] = match.groups()[0]

    return types
