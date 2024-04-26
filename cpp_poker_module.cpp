#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Needed for bindings of STL containers
#include <pybind11/operators.h> // Needed for binding of comparison operators
#include "Card.hpp"
#include "Oracle.hpp"
#include "TerminalColors.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_poker, m)
{
    py::class_<Card>(m, "Card")
        .def(py::init<int>(), py::arg("index"))
        .def(py::init<int, int>(), py::arg("rank"), py::arg("suit"))
        .def(py::init<std::string, std::string>(), py::arg("rank"), py::arg("suit"))
        .def("to_index", &Card::to_index)
        .def("get_cli_repr", &Card::get_cli_repr)
        .def_static("get_cli_repr_for_cards", py::overload_cast<const std::vector<Card> &>(&Card::get_cli_repr_for_cards))
        .def_static("get_cli_repr_for_cards", py::overload_cast<const std::vector<int> &>(&Card::get_cli_repr_for_cards))
        .def("__str__", &Card::str)
        .def("__repr__", &Card::str)
        .def("__hash__", &Card::to_index)
        .def("__eq__", [](const Card &a, const Card &b)
             { return a == b; })
        .def("__lt__", [](const Card &a, const Card &b)
             { return a < b; })
        .def("__gt__", [](const Card &a, const Card &b)
             { return a > b; });

    py::class_<TerminalColors>(m, "TerminalColors")
        .def_readonly_static("RED", &TerminalColors::RED)
        .def_readonly_static("BLUE", &TerminalColors::BLUE)
        .def_readonly_static("DEFAULT", &TerminalColors::DEFAULT)
        .def_readonly_static("FOLDED", &TerminalColors::FOLDED);

    py::class_<Oracle>(m, "Oracle")
        .def_static("check_for_royal_flush", &Oracle::check_for_royal_flush)
        .def_static("check_for_straight_flush", &Oracle::check_for_straight_flush)
        .def_static("check_for_four_of_a_kind", &Oracle::check_for_four_of_a_kind)
        .def_static("check_for_full_house", &Oracle::check_for_full_house)
        .def_static("check_for_flush", &Oracle::check_for_flush)
        .def_static("check_for_straight", &Oracle::check_for_straight)
        .def_static("check_for_three_of_a_kind", &Oracle::check_for_three_of_a_kind)
        .def_static("check_for_two_pair", &Oracle::check_for_two_pair)
        .def_static("check_for_one_pair", &Oracle::check_for_one_pair)
        .def_static("get_n_high_cards", &Oracle::get_n_high_cards)
        .def_static("get_n_high_ranks", &Oracle::get_n_high_ranks)
        .def_static("rank_hand", &Oracle::rank_hand)
        .def_static("compare_hands", &Oracle::compare_hands)
        .def_static("find_winner", &Oracle::find_winner)
        .def_static("get_max_bet_allowed", &Oracle::get_max_bet_allowed)
        .def_static("get_winning_probability", &Oracle::get_winning_probability)
        .def_static("generate_utility_matrix",
                    py::overload_cast<const std::vector<int> &, const std::vector<bool> &>(&Oracle::generate_utility_matrix),
                    py::arg("table"), py::arg("player_is_active"),
                    "Generate a utility matrix for the given table and player states\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param player_is_active: A list of booleans representing whether each player is active\n"
                    ":return: A 2D list of floats representing the utility matrix")
        .def_static("generate_utility_matrix",
                    py::overload_cast<const std::vector<int> &, const std::vector<bool> &, const std::set<int> &>(&Oracle::generate_utility_matrix),
                    py::arg("table"), py::arg("player_is_active"), py::arg("deck"),
                    "Generate a utility matrix for the given table, player states, and deck\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param player_is_active: A list of booleans representing whether each player is active\n"
                    ":param deck: A set of integers representing the deck\n"
                    ":return: A 2D list of floats representing the utility matrix");
}
