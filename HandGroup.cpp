// HandGroup.cpp

#include "HandGroup.hpp"
#include <stdexcept>
#include <iostream>

// Initialize static variables
std::vector<std::pair<int, int>> HandGroup::UNSUITED_COMBINATIONS = []()
{
    std::vector<std::pair<int, int>> combinations;

    for (int h = 12; h >= 0; --h)
    {
        for (int l = h; l >= 0; --l)
        {
            std::pair<int, int> group = std::make_pair(h, l);
            combinations.push_back(group);
        }
    }

    return combinations;
}();

std::vector<HandGroup> HandGroup::ALL_COMBINATIONS = []()
{
    std::vector<HandGroup> combinations;

    // Pairs first
    for (int r = 12; r >= 0; --r)
    {
        HandGroup hg;
        hg.high_rank = r;
        hg.low_rank = r;
        hg.suited = false; // Suitedness doesn't matter for pairs
        combinations.push_back(hg);
    }

    // Non-pairs
    for (int h = 12; h >= 0; --h)
    {
        for (int l = h - 1; l >= 0; --l)
        {
            // Suited
            HandGroup hg_suited;
            hg_suited.high_rank = h;
            hg_suited.low_rank = l;
            hg_suited.suited = true;
            combinations.push_back(hg_suited);

            // Offsuit
            HandGroup hg_offsuit;
            hg_offsuit.high_rank = h;
            hg_offsuit.low_rank = l;
            hg_offsuit.suited = false;
            combinations.push_back(hg_offsuit);
        }
    }

    return combinations;
}();

// Default constructor
HandGroup::HandGroup() : high_rank(0), low_rank(0), suited(false) {}

// Constructor from index
HandGroup::HandGroup(int index)
{
    if (index < 0 || index >= static_cast<int>(ALL_COMBINATIONS.size()))
    {
        throw std::out_of_range("Index out of range for HandGroup.");
    }
    *this = ALL_COMBINATIONS[index];
}

HandGroup::HandGroup(int unsuited_index, bool suited)
{
    if (unsuited_index < 0 || unsuited_index >= static_cast<int>(UNSUITED_COMBINATIONS.size()))
    {
        throw std::out_of_range("Index out of range for HandGroup.");
    }

    std::pair<int, int> ranks = UNSUITED_COMBINATIONS[unsuited_index];
    high_rank = ranks.first;
    low_rank = ranks.second;
    this->suited = suited;
}

// Constructor from CardCollection
HandGroup::HandGroup(CardCollection cards)
{
    std::vector<Card> card_vector = cards.to_vector();

    if (card_vector.size() != 2)
    {
        throw std::invalid_argument("CardCollection must contain exactly two cards.");
    }

    int rank1 = card_vector[0].rank;
    int rank2 = card_vector[1].rank;

    if (rank1 > rank2)
    {
        high_rank = rank1;
        low_rank = rank2;
    }
    else
    {
        high_rank = rank2;
        low_rank = rank1;
    }

    suited = (card_vector[0].suit == card_vector[1].suit);
}

// Constructor from card indices
HandGroup::HandGroup(int card1, int card2, bool suited)
{
    Card c1(card1);
    Card c2(card2);

    int rank1 = c1.rank;
    int rank2 = c2.rank;

    if (rank1 > rank2)
    {
        high_rank = rank1;
        low_rank = rank2;
    }
    else
    {
        high_rank = rank2;
        low_rank = rank1;
    }

    this->suited = suited;
}

// Constructor from Cards
HandGroup::HandGroup(Card card1, Card card2, bool suited)
{
    int rank1 = card1.rank;
    int rank2 = card2.rank;

    if (rank1 > rank2)
    {
        high_rank = rank1;
        low_rank = rank2;
    }
    else
    {
        high_rank = rank2;
        low_rank = rank1;
    }

    this->suited = suited;
}

// Convert HandGroup to index using COMBINATIONS
int HandGroup::to_index() const
{
    auto it = std::find(ALL_COMBINATIONS.begin(), ALL_COMBINATIONS.end(), *this);
    if (it != ALL_COMBINATIONS.end())
    {
        return static_cast<int>(std::distance(ALL_COMBINATIONS.begin(), it));
    }
    else
    {
        throw std::out_of_range("HandGroup not found in ALL_COMBINATIONS.");
    }
}

int HandGroup::to_unsuited_index() const
{
    std::pair<int, int> ranks = std::make_pair(high_rank, low_rank);
    auto it = std::find(UNSUITED_COMBINATIONS.begin(), UNSUITED_COMBINATIONS.end(), ranks);
    if (it != UNSUITED_COMBINATIONS.end())
    {
        return static_cast<int>(std::distance(UNSUITED_COMBINATIONS.begin(), it));
    }
    else
    {
        throw std::out_of_range("HandGroup not found in UNSUITED_COMBINATIONS.");
    }
}

// String representation
std::string HandGroup::str() const
{
    const std::string ranks[] = {"2", "3", "4", "5", "6", "7", "8",
                                 "9", "T", "J", "Q", "K", "A"};
    std::string s;
    s += ranks[high_rank];
    s += ranks[low_rank];
    if (high_rank != low_rank)
    {
        s += suited ? "s" : "o";
    }
    return s;
}

// Suitedness getter
bool HandGroup::is_suited() const
{
    return suited;
}

// Equality operator
bool HandGroup::operator==(const HandGroup &other) const
{
    return high_rank == other.high_rank && low_rank == other.low_rank && suited == other.suited;
}
