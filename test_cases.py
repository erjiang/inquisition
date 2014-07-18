import ast
import re
import sys

import inquisition
from pypes import Heresy
from env import Env

VERBOSE = False

def test_file(filename):

    ALL_GOOD = True

    with open(filename, 'r') as f:
        f_ast = ast.parse(f.read())

    with open(filename, 'r') as f:
        f_lines = f.readlines()
        error_lines = collect_error_lines(f_lines)

    type_errors = {}
    env = Env()
    results = inquisition.run_through(f_ast.body, env, top_level=True, catch_errors=True)
    for e in results['errors']:
        type_errors[e.ast_obj.lineno] = str(e)

    for k, v in type_errors.items():
        if k not in error_lines:
            ALL_GOOD = False
            print("False alarm on line %d: %s" % (k, v))
        elif VERBOSE:
            print("Caught error on line %d: %s" % (k, v))

    for k, v in error_lines.items():
        if k not in type_errors:
            ALL_GOOD = False
            print("Didn't catch line %d: %s" % (k, v))

    return ALL_GOOD
 

def collect_error_lines(lines):
    error_pattern = re.compile('##ERROR\\s+(.*)$')
    error_lines = dict()
    for idx, line in enumerate(lines):
        match = error_pattern.search(line)
        if match:
            error_lines[idx+1] = match.groups()[0]

    return error_lines


if __name__ == "__main__":
    ALL_GOOD = True
    for f in sys.argv[1:]:
        if f == '-v':
            VERBOSE = True
            inquisition.DEBUG_LEVEL = 3
            continue
        print("---> " + f)
        ALL_GOOD = test_file(f) and ALL_GOOD
        print()
    sys.exit(not ALL_GOOD)
