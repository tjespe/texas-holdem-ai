#include <pybind11/pybind11.h>
#include <pybind11/stl.h>       // Needed for bindings of STL containers
#include <pybind11/operators.h> // Needed for binding of comparison operators
#include "Card.hpp"
#include "Oracle.hpp"
#include "TerminalColors.hpp"
#include "Hand.hpp"

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
        .def_static("get_rank", &Card::get_rank)
        .def("__str__", &Card::str)
        .def("__repr__", &Card::str)
        .def("__hash__", &Card::to_index)
        .def("__eq__", [](const Card &a, const Card &b)
             { return a == b; })
        .def("__lt__", [](const Card &a, const Card &b)
             { return a < b; })
        .def("__gt__", [](const Card &a, const Card &b)
             { return a > b; });

    py::class_<CardCollection::Iterator>(m, "Iterator")
        .def("__iter__", [](CardCollection::Iterator &it) -> CardCollection::Iterator &
             { return it; })
        .def("__next__", [](CardCollection::Iterator &it)
             {
            if (it != it.collection.end()) {
                Card result = *it;
                ++it;
                return result;
            } else {
                throw py::stop_iteration();
            } });

    py::class_<CardCollection>(m, "CardCollection")
        .def(py::init<>())
        .def(py::init<std::vector<int>>(), py::arg("card_indices"))
        .def(py::init<std::set<int>>(), py::arg("card_indices"))
        .def(py::init<std::vector<Card>>(), py::arg("cards"))
        .def(py::init<std::set<Card>>(), py::arg("cards"))
        .def(py::init<std::bitset<52>>(), py::arg("cards"))
        .def("__eq__", &CardCollection::operator==)
        .def("add_card", &CardCollection::add_card)
        .def("add_cards", &CardCollection::add_cards)
        .def("remove_card", &CardCollection::remove_card)
        .def("remove_cards", &CardCollection::remove_cards)
        .def("__add__", &CardCollection::operator+)
        .def("__sub__", &CardCollection::operator-)
        .def("has", &CardCollection::has)
        .def("is_superset", &CardCollection::is_superset)
        .def("is_subset", &CardCollection::is_subset)
        .def("intersects", &CardCollection::intersects)
        .def("check_for_royal_flush", &CardCollection::check_for_royal_flush)
        .def("check_for_straight_flush", &CardCollection::check_for_straight_flush)
        .def("check_for_four_of_a_kind", &CardCollection::check_for_four_of_a_kind)
        .def("check_for_full_house", &CardCollection::check_for_full_house)
        .def("check_for_flush", &CardCollection::check_for_flush)
        .def("check_for_straight", &CardCollection::check_for_straight)
        .def("check_for_three_of_a_kind", &CardCollection::check_for_three_of_a_kind)
        .def("check_for_two_pair", &CardCollection::check_for_two_pair)
        .def("check_for_one_pair", &CardCollection::check_for_one_pair)
        .def("get_n_high_cards", &CardCollection::get_n_high_cards)
        .def("get_n_high_ranks", &CardCollection::get_n_high_ranks)
        .def("get_n_high_ranks_except", &CardCollection::get_n_high_ranks_except)
        .def("rank_hand", &CardCollection::rank_hand)
        .def("beats", &CardCollection::beats)
        .def("str", &CardCollection::str)
        .def("get_cli_repr", &CardCollection::get_cli_repr)
        .def("size", &CardCollection::size)
        .def("to_vector", &CardCollection::to_vector)
        .def("__iter__", [](const CardCollection &c)
             { return c.begin(); }, py::keep_alive<0, 1>());

    py::class_<Hand>(m, "Hand")
        .def(py::init<>())
        .def(py::init<int>(), py::arg("index"))
        .def("get_cards", &Hand::get_cards)
        .def("to_index", &Hand::to_index)
        .def("get_cli_repr", &Hand::get_cli_repr)
        .def("str", &Hand::str)
        .def("__eq__", &Hand::operator==)
        .def_readonly_static("COMBINATIONS", &Hand::COMBINATIONS);

    py::class_<HandRank>(m, "HandRank")
        .def_readonly_static("ROYAL_FLUSH", &HandRank::ROYAL_FLUSH)
        .def_readonly_static("STRAIGHT_FLUSH", &HandRank::STRAIGHT_FLUSH)
        .def_readonly_static("FOUR_OF_A_KIND", &HandRank::FOUR_OF_A_KIND)
        .def_readonly_static("FULL_HOUSE", &HandRank::FULL_HOUSE)
        .def_readonly_static("FLUSH", &HandRank::FLUSH)
        .def_readonly_static("STRAIGHT", &HandRank::STRAIGHT)
        .def_readonly_static("THREE_OF_A_KIND", &HandRank::THREE_OF_A_KIND)
        .def_readonly_static("TWO_PAIR", &HandRank::TWO_PAIR)
        .def_readonly_static("ONE_PAIR", &HandRank::ONE_PAIR)
        .def_readonly_static("HIGH_CARD", &HandRank::HIGH_CARD)
        .def(py::init<int, std::vector<int>>(), py::arg("rank"), py::arg("tiebreakers"))
        .def("get_rank", &HandRank::get_rank)
        .def("get_tiebreakers", &HandRank::get_tiebreakers)
        .def("__lt__", &HandRank::operator<)
        .def("__eq__", &HandRank::operator==)
        .def("__gt__", &HandRank::operator>)
        .def("beats", &HandRank::beats)
        .def("__str__", &HandRank::str)
        .def("__repr__", &HandRank::str)
        .def("get_rank_name", &HandRank::get_rank_name);

    py::class_<TerminalColors>(m, "TerminalColors")
        .def_readonly_static("RED", &TerminalColors::RED)
        .def_readonly_static("BLUE", &TerminalColors::BLUE)
        .def_readonly_static("DEFAULT", &TerminalColors::DEFAULT)
        .def_readonly_static("FOLDED", &TerminalColors::FOLDED);

    py::class_<Oracle>(m, "Oracle")
        .def_static("find_winner", &Oracle::find_winner)
        .def_static("get_max_bet_allowed", &Oracle::get_max_bet_allowed)
        .def_static("get_winning_probability", &Oracle::get_winning_probability,
                    py::arg("hand"), py::arg("table"), py::arg("num_players"),
                    "Get the winning probability of a hand given a table and number of players\n"
                    ":param hand: A set of integers representing the hand\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param num_players: An integer representing the number of players\n"
                    ":return: A float representing the winning probability")
        .def_static("get_winning_probability_n_simulations", &Oracle::get_winning_probability_n_simulations,
                    py::arg("hand"), py::arg("table"), py::arg("num_players"), py::arg("num_simulations"),
                    "Get the winning probability of a hand given a table and number of players\n"
                    ":param hand: A set of integers representing the hand\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param num_players: An integer representing the number of players\n"
                    ":param num_simulations: An integer representing the number of simulations to run\n"
                    ":return: A float representing the winning probability")
        .def_static("generate_utility_matrix",
                    py::overload_cast<const CardCollection &, const std::vector<bool> &, int>(&Oracle::generate_utility_matrix),
                    py::arg("table"), py::arg("player_is_active"), py::arg("perspective"),
                    "Generate a utility matrix for the given table and player states\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param player_is_active: A list of booleans representing whether each player is active\n"
                    ":return: A 2D list of floats representing the utility matrix")
        .def_static("generate_utility_matrix",
                    py::overload_cast<const CardCollection &, const std::vector<bool> &, int, const CardCollection &>(&Oracle::generate_utility_matrix),
                    py::arg("table"), py::arg("player_is_active"), py::arg("perspective"), py::arg("deck"),
                    "Generate a utility matrix for the given table, player states, and deck\n"
                    ":param table: A list of integers representing the table cards\n"
                    ":param player_is_active: A list of booleans representing whether each player is active\n"
                    ":param deck: A set of integers representing the deck\n"
                    ":return: A 2D list of floats representing the utility matrix");
}
