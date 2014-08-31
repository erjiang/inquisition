A static type system and checker for Python.

Requirements: python3

Usage: `inquisition.py somefile.py`

Run test cases: `./run_cases.sh`


Anticipated Questions
=====================

1. Is this type system sound?  
Improbable.

2. Is it faithful to Python's type system?  
No.

3. Can it account for all the subtleties inherent in Python's de facto
standard (CPython)?  
Given the previous answer, no.

4. What kind of code can it handle?  
Check out the examples in `./cases/` that also serve as the test suite.

5. Is this a static analysis tool (AKA linter)?  
Only so far as you consider static type checking to be "static analysis".

6. Does this infer types?  
Yes, it certainly tries to. For example, it will attempt to guess the type
signature of a function if you didn't write one in.

7. Why does this require Python 3?  
Python 3 is the wave of the future. Also, for some ill-advised reason, Py3k has
built-in support for function type signatures.
