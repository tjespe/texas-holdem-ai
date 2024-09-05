#pragma once
#include <string>
#include <vector>
#include "TerminalColors.hpp"

class Card
{
public:
    static const std::vector<std::string> SUITS;
    static const std::vector<std::string> VALUES;
    int rank;
    int suit;

    Card(); // Default constructor used by containers
    Card(int rank, int suit);
    Card(std::string rank, std::string suit);
    Card(int index);
    int to_index() const;
    std::string term_color() const;
    std::string get_cli_repr() const;
    static std::string get_cli_repr_for_cards(const std::vector<Card> &cards);
    static std::string get_cli_repr_for_cards(const std::vector<int> &cards);
    static int get_rank(const std::string &rank);
    std::string str() const;

    /** Comparators for sorting based on rank (cards with the same rank are arbitrarily distringuished based on suit) */
    bool operator<(const Card &other) const;
    bool operator>(const Card &other) const;
    bool operator==(const Card &other) const;
};

