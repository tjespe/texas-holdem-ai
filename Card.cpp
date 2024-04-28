#include "Card.hpp"
#include <sstream>
#include <iomanip>
#include <algorithm>

const std::vector<std::string> Card::SUITS = {"♥", "♦", "♣", "♠"};
const std::vector<std::string> Card::VALUES = {"2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"};

Card::Card() : rank(0), suit(0) {}

Card::Card(int rank, int suit) : rank(rank), suit(suit) {}

Card::Card(std::string rank, std::string suit)
{
    this->rank = std::distance(VALUES.begin(), std::find(VALUES.begin(), VALUES.end(), rank));
    this->suit = std::distance(SUITS.begin(), std::find(SUITS.begin(), SUITS.end(), suit));
}

Card::Card(int index)
{
    this->rank = index % 13;
    this->suit = index / 13;
}

int Card::to_index() const
{
    return suit * 13 + rank;
}

std::string Card::term_color() const
{
    return (suit == 0 || suit == 1) ? TerminalColors::RED : TerminalColors::BLUE;
}

std::string Card::get_cli_repr() const
{
    std::stringstream ss;
    ss << "┌───────┐\n";
    ss << "│" << term_color() << std::left << std::setw(2) << VALUES[rank] << TerminalColors::DEFAULT << "     │\n";
    ss << "│       │\n";
    ss << "│   " << term_color() << SUITS[suit] << TerminalColors::DEFAULT << "   │\n";
    ss << "│       │\n";
    ss << "│     " << term_color() << std::right << std::setw(2) << VALUES[rank] << TerminalColors::DEFAULT << "│\n";
    ss << "└───────┘";
    return ss.str();
}

std::string Card::get_cli_repr_for_cards(const std::vector<Card> &cards)
{
    std::vector<std::vector<std::string>> lines(cards.size(), std::vector<std::string>(7));
    for (size_t i = 0; i < cards.size(); ++i)
    {
        std::stringstream ss(cards[i].get_cli_repr());
        std::string line;
        size_t line_no = 0;
        while (std::getline(ss, line))
        {
            lines[i][line_no++] = line;
        }
    }

    std::string combined;
    for (size_t i = 0; i < 7; ++i)
    { // 7 lines per card
        for (const auto &line_vec : lines)
        {
            combined += line_vec[i] + " ";
        }
        combined += "\n";
    }
    return combined;
}

std::string Card::get_cli_repr_for_cards(const std::vector<int> &cards)
{
    std::vector<Card> card_objs;
    for (int card : cards)
    {
        card_objs.push_back(Card(card));
    }
    return get_cli_repr_for_cards(card_objs);
}

int Card::get_rank(const std::string &rank)
{
    return std::distance(VALUES.begin(), std::find(VALUES.begin(), VALUES.end(), rank));
}

std::string Card::str() const
{
    return SUITS[suit] + " " + VALUES[rank];
}

bool Card::operator<(const Card &other) const
{
    if (rank != other.rank)
        return rank < other.rank;
    return suit < other.suit;
}

bool Card::operator>(const Card &other) const
{
    if (rank != other.rank)
        return rank > other.rank;
    return suit > other.suit;
}

bool Card::operator==(const Card &other) const
{
    return rank == other.rank && suit == other.suit;
}
