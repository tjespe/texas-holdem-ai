#include "HandRank.hpp"
#include <stdexcept>

const int HandRank::ROYAL_FLUSH;
const int HandRank::STRAIGHT_FLUSH;
const int HandRank::FOUR_OF_A_KIND;
const int HandRank::FULL_HOUSE;
const int HandRank::FLUSH;
const int HandRank::STRAIGHT;
const int HandRank::THREE_OF_A_KIND;
const int HandRank::TWO_PAIR;
const int HandRank::ONE_PAIR;
const int HandRank::HIGH_CARD;

HandRank::HandRank(int rank, const std::array<int, 5> tiebreakers) : rank(rank), tiebreakers(tiebreakers) {}

HandRank::HandRank(int rank, const std::vector<int> tiebreakers) : rank(rank) {
    if (tiebreakers.size() > 5) throw std::runtime_error("Too many tiebreakers");
    std::copy(tiebreakers.begin(), tiebreakers.end(), this->tiebreakers.begin());
}

std::string HandRank::get_rank_name() const
{
    std::string rank_str;
    switch (this->rank)
    {
    case ROYAL_FLUSH:
        rank_str = "Royal Flush";
        break;
    case STRAIGHT_FLUSH:
        rank_str = "Straight Flush";
        break;
    case FOUR_OF_A_KIND:
        rank_str = "Four of a Kind";
        break;
    case FULL_HOUSE:
        rank_str = "Full House";
        break;
    case FLUSH:
        rank_str = "Flush";
        break;
    case STRAIGHT:
        rank_str = "Straight";
        break;
    case THREE_OF_A_KIND:
        rank_str = "Three of a Kind";
        break;
    case TWO_PAIR:
        rank_str = "Two Pairs";
        break;
    case ONE_PAIR:
        rank_str = "One Pair";
        break;
    case HIGH_CARD:
        rank_str = "High Card";
        break;
    default:
        rank_str = "Unknown";
        break;
    }
    return rank_str;
}

std::string HandRank::str() const
{
    auto rank_str = get_rank_name();
    std::string tiebreakers_str = "[";
    for (int i = 0; i < 5; i++)
    {
        tiebreakers_str += std::to_string(this->tiebreakers[i]);
        if (i < 4)
        {
            tiebreakers_str += ", ";
        }
    }
    tiebreakers_str += "]";
    return rank_str + " " + tiebreakers_str;
}

int HandRank::get_rank() const {
    return this->rank;
}

std::array<int, 5> HandRank::get_tiebreakers() const {
    return this->tiebreakers;
}

bool HandRank::operator<(const HandRank &other) const {
    if (this->rank != other.rank) {
        return this->rank < other.rank;
    }
    return this->tiebreakers < other.tiebreakers;
}

bool HandRank::operator==(const HandRank &other) const
{
    return this->rank == other.rank && this->tiebreakers == other.tiebreakers;
}

bool HandRank::operator>(const HandRank &other) const
{
    return !(*this < other) && !(*this == other);
}

int HandRank::beats(const HandRank &other) const
{
    if (*this > other)
    {
        return 1;
    }
    if (*this == other)
    {
        return 0;
    }
    return -1;
}
