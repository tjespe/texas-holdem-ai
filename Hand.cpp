#include "Hand.hpp"

std::vector<CardCollection> Hand::COMBINATIONS = Hand::generate_combinations();

std::vector<CardCollection> Hand::generate_combinations()
{
    std::vector<CardCollection> combinations;
    std::bitset<52> cards;
    for (int i = 0; i < 52; ++i)
    {
        cards.set(i);
        for (int j = i + 1; j < 52; ++j)
        {
            cards.set(j);
            combinations.push_back(cards);
            cards.reset(j);
        }
        cards.reset(i);
    }
    return combinations;
}

Hand::Hand()
{
}

Hand::Hand(int index)
{
    this->index = index;
}

CardCollection Hand::get_cards() const
{
    return COMBINATIONS[this->index];
}

int Hand::to_index() const
{
    return this->index;
}

std::string Hand::get_cli_repr() const
{
    return get_cards().get_cli_repr();
}

std::string Hand::str() const
{
    return get_cards().str();
}

bool Hand::operator==(const Hand &other) const
{
    return this->index == other.index;
}
