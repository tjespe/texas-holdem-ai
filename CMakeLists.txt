cmake_minimum_required(VERSION 3.12)
project(cpp_poker)

add_subdirectory(pybind11)
set(CMAKE_CXX_STANDARD 17)
pybind11_add_module(cpp_poker cpp_poker_module.cpp Card.cpp Card.hpp TerminalColors.cpp TerminalColors.hpp Oracle.cpp Oracle.hpp)