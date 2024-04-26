# cpp_poker

This is the build directory for the part of the project written using C++.

### Building

0. Make sure that `CMakeLists.txt` in the source directory includes all relevant C++ source files
1. `cd` into this directory
2. `cmake ..`
3. `make`

### Importing from Python

```python
from cpp_poker.cpp_poker import Card, Oracle, TerminalColors
```