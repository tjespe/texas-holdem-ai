#pragma once
#include <utility>
#include "Card.hpp"
#include "CardCollection.hpp"
#include <map>

class Hand
{
public:
    // All possible combinations of 2 cards from a deck of 52 cards
    static std::vector<CardCollection> COMBINATIONS;

    // Maps every card in the deck to a list of hands (indices) that contain that card
    static std::map<int, std::vector<int>> HANDS_WITH_CARD;

    Hand(); // Default constructor used by containers
    Hand(int index);
    CardCollection get_cards() const;
    int to_index() const;
    std::string get_cli_repr() const;
    std::string str() const;
    bool operator==(const Hand& other) const;

private:
    int index;
    static std::vector<CardCollection> generate_combinations();
};
