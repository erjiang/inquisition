Test cases
==========

All of these test cases should be small Python programs that exercise one
particular part of the type system.

Test cases may simply have `##ERROR some message` at the end of some lines.
This declares that a type error is expected at that line. The test runner will
complain if there is no error at that line, and will not print anything
otherwise.

For false positives, the test runner will complain if an error is thrown for a
line that does not have an `##ERROR` annotation on it.

Some test cases do not have an `##ERROR` annotations, which means that there
should be no type errors, and any type errors thrown are bugs in the type
checker.
