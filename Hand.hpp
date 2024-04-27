#pragma once
#include <utility>
#include "Card.hpp"
#include "CardCollection.hpp"

class Hand
{
public:
    static std::vector<CardCollection> COMBINATIONS;

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
