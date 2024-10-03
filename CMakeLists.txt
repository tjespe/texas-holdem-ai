cmake_minimum_required(VERSION 3.12)
project(cpp_poker)
find_package(Python 3.9.6 EXACT COMPONENTS Interpreter Development)

add_subdirectory(pybind11)
set(CMAKE_CXX_STANDARD 17)
pybind11_add_module(cpp_poker cpp_poker_module.cpp Card.cpp Card.hpp CardCollection.cpp CardCollection.hpp Hand.cpp Hand.hpp HandRank.cpp HandRank.hpp TerminalColors.cpp TerminalColors.hpp CheatSheet.cpp CheatSheet.hpp Oracle.cpp Oracle.hpp HandGroup.hpp HandGroup.cpp)
set_target_properties(cpp_poker PROPERTIES 
    PREFIX ""
    OUTPUT_NAME "cpp_poker" 
    SUFFIX ".so"
)
