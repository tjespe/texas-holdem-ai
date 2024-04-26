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
    std::string str() const;

    bool operator<(const Card &other) const;
    bool operator>(const Card &other) const;
    bool operator==(const Card &other) const;
};

/**
 * Comparator providing a strict ordering of cards (as opposed to the < and > operators which only compare ranks)
 */
struct CardSortingComparator
{
    bool operator()(const Card &a, const Card &b) const
    {
        if (a.rank != b.rank)
            return a.rank < b.rank;
        return a.suit < b.suit;
    }
};
