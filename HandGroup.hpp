#pragma once
#include <utility>
#include "Card.hpp"
#include "CardCollection.hpp"
#include <map>

/** Class representing the 13x13 possible combinations of ranks and suited/not suited */
class HandGroup
{
public:
    // The 13x13 possible combinations of ranks
    static std::vector<std::pair<int, int>> UNSUITED_COMBINATIONS;

    // All 13x13 possible combinations of ranks and suited/not suited
    static std::vector<HandGroup> ALL_COMBINATIONS;

    HandGroup(); // Default constructor used by containers
    HandGroup(int index);
    HandGroup(int unsuited_index, bool suited);
    HandGroup(CardCollection cards);
    HandGroup(int card1, int card2, bool suited);
    HandGroup(Card card1, Card card2, bool suited);
    int to_index() const;
    int to_unsuited_index() const;
    std::string str() const;
    bool is_suited() const;
    bool operator==(const HandGroup &other) const;

private:
    int high_rank;
    int low_rank;
    bool suited;
};
