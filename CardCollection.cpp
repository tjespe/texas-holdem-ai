#include "CardCollection.hpp"
#include <algorithm> // For std::sort and std::unique
#include <stdexcept> // For runtime_error
#include <iterator>  // For std::next
#include <sstream>
#include <random>
#include "Hand.hpp"

CardCollection::CardCollection() : cards(0) {}

CardCollection::CardCollection(std::vector<int> card_indices) : cards(0)
{
    for (int index : card_indices)
    {
        this->cards.set(index);
    }
}

CardCollection::CardCollection(std::set<int> card_indices) : cards(0)
{
    for (int index : card_indices)
    {
        this->cards.set(index);
    }
}

CardCollection::CardCollection(std::vector<Card> cards) : cards(0)
{
    for (const Card &card : cards)
    {
        this->cards.set(card.to_index());
    }
}

CardCollection::CardCollection(std::set<Card> cards) : cards(0)
{
    for (const Card &card : cards)
    {
        this->cards.set(card.to_index());
    }
}

CardCollection::CardCollection(std::bitset<52> cards)
{
    this->cards = cards;
}

void CardCollection::add_card(const Card &card)
{
    this->cards.set(card.to_index());
}

void CardCollection::add_cards(const CardCollection &other)
{
    this->cards |= other.cards;
}

void CardCollection::remove_card(const Card &card)
{
    this->cards.reset(card.to_index());
}

void CardCollection::remove_cards(const CardCollection &other)
{
    this->cards &= ~other.cards;
}

Card CardCollection::draw_random_card()
{
    return Card(draw_random_cards(1).begin().index);
}

CardCollection CardCollection::draw_random_cards(int n)
{
    if (this->size() < n)
    {
        throw std::runtime_error("Cannot draw more cards than are in the collection");
    }
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> dist(0, this->size() - 1);
    CardCollection result;
    int n_remaining = n;
    while (n_remaining > 0)
    {
        int index = dist(gen);
        if (this->cards.test(index))
        {
            Card card(index);
            result.add_card(card);
            n_remaining--;
            this->remove_card(card);
        }
    }
    return result;
}

CardCollection CardCollection::operator+(const CardCollection &other) const
{
    CardCollection result(*this);
    result.cards |= other.cards;
    return result;
}


CardCollection CardCollection::operator-(const CardCollection &other) const
{
    CardCollection result(*this);
    result.cards &= ~other.cards;
    return result;
}

bool CardCollection::operator==(const CardCollection &other) const
{
    return this->cards == other.cards;
}

bool CardCollection::has(const Card &card) const
{
    return this->cards.test(card.to_index());
}

bool CardCollection::is_superset(const CardCollection &other) const
{
    return (this->cards & other.cards) == other.cards;
}

bool CardCollection::is_subset(const CardCollection &other) const
{
    return (this->cards & other.cards) == this->cards;
}

/**
 * Check if the two collections have any cards in common
 */
bool CardCollection::intersects(const CardCollection &other) const
{
    return (this->cards & other.cards).any();
}

std::optional<HandRank> CardCollection::check_for_royal_flush() const
{
    std::bitset<13> royal_bits(0b1111100000000);
    for (int suit = 0; suit < 4; ++suit)
    {
        // Extract the bits for the current suit from the cards bitstring using shifting
        std::bitset<13> suit_bits(this->cards.to_ulong() >> (suit * 13));
        // Check if the bits for the current suit match the royal flush bits
        if ((suit_bits & royal_bits) == royal_bits)
        {
            std::array<int, 5> tiebreakers{}; // No tiebreakers needed for royal flush
            return HandRank(HandRank::ROYAL_FLUSH, tiebreakers);
        }
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_straight_flush() const
{
    for (int suit = 0; suit < 4; ++suit)
    {
        // Extract the bits for the current suit from the cards bitstring using shifting
        std::bitset<13> suit_bits(this->cards.to_ulong() >> (suit * 13));
        // Check if the bits for the current suit contain a straight
        for (int i = 0; i <= 8; ++i)
        {
            std::bitset<13> straight_bits(0b11111 << i);
            if ((suit_bits & straight_bits) == straight_bits)
            {
                std::array<int, 5> tiebreakers{};
                tiebreakers[0] = i + 4; // Highest card in the straight
                return HandRank(HandRank::STRAIGHT_FLUSH, tiebreakers);
            }
        }
        // Check for special case: A-2-3-4-5 straight
        std::bitset<13> ace_low_straight_bits(0b1111000000001);
        if ((suit_bits & ace_low_straight_bits) == ace_low_straight_bits)
        {
            std::array<int, 5> tiebreakers{};
            tiebreakers[0] = Card::get_rank("5"); // Highest card in the straight
            return HandRank(HandRank::STRAIGHT_FLUSH, tiebreakers);
        }
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_four_of_a_kind() const
{
    std::bitset<13> mask;
    mask.set();
    for (int suit = 0; suit < 4; ++suit)
    {
        // Extract the bits for the current suit from the cards bitstring using shifting
        std::bitset<13> suit_bits(this->cards.to_ulong() >> (suit * 13));
        // Do a bitwise AND with the mask to check for four of a kind
        mask &= suit_bits;
    }
    // Check if a bit is set in the mask
    if (mask.any())
    {
        std::array<int, 5> tiebreakers{};
        // Primary tie breaker: rank of the four of a kind
        for (int i = 12; i >= 0; --i)
        {
            if (mask.test(i))
            {
                tiebreakers[0] = i;
                break;
            }
        }
        // Secondary tie breaker: rank of the kicker
        tiebreakers[1] = this->get_n_high_ranks(1)[0];
        return HandRank(HandRank::FOUR_OF_A_KIND, tiebreakers);
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_full_house() const
{
    auto three_of_a_kind = this->check_for_three_of_a_kind();
    if (three_of_a_kind)
    {
        // Remove the three of a kind from the cards, and check for pair
        int triplet_rank = (*three_of_a_kind).get_tiebreakers()[0];
        std::bitset<13> suit_mask;
        suit_mask.set(triplet_rank);
        std::bitset<52> mask = suit_mask.to_ulong() | (suit_mask.to_ulong() << 13) | (suit_mask.to_ulong() << 26) | (suit_mask.to_ulong() << 39);
        CardCollection remaining_cards = *this - CardCollection(mask);
        auto pair = remaining_cards.check_for_one_pair();
        if (pair)
        {
            std::array<int, 5> tiebreakers{};
            tiebreakers[0] = triplet_rank;
            tiebreakers[1] = (*pair).get_tiebreakers()[0];
            return HandRank(HandRank::FULL_HOUSE, tiebreakers);
        }
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_flush() const
{
    for (int suit = 0; suit < 4; ++suit)
    {
        // Extract the bits for the current suit from the cards bitstring using shifting
        std::bitset<13> suit_bits(this->cards.to_ulong() >> (suit * 13));
        // Check if the number of bits set in the suit bits is at least 5
        if (suit_bits.count() >= 5)
        {
            std::array<int, 5> tiebreakers{};
            // Get the indices of the five highest cards in the suit
            std::vector<int> high_ranks = CardCollection(suit_bits.to_ulong() << (suit * 13)).get_n_high_ranks(5);
            // Set the tiebreakers to the ranks of the five highest cards
            for (int i = 0; i < 5; ++i)
            {
                tiebreakers[i] = high_ranks[i];
            }
            return HandRank(HandRank::FLUSH, tiebreakers);
        }
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_straight() const
{
    std::bitset<13> ranks_in_hand;
    for (int suit = 0; suit < 4; ++suit)
    {
        // Extract the bits for the current suit from the cards bitstring using shifting
        std::bitset<13> suit_bits(this->cards.to_ulong() >> (suit * 13));
        // OR the suit bits with the ranks_in_hand to get a bitstring with all the ranks in the hand
        ranks_in_hand |= suit_bits;
    }
    // Check if the ranks_in_hand contain a straight
    // Iterate downwards to get the highest straight
    for (int i = 8; i >= 0; --i)
    {
        std::bitset<13> straight_bits(0b11111 << i);
        if ((ranks_in_hand & straight_bits) == straight_bits)
        {
            std::array<int, 5> tiebreakers{};
            tiebreakers[0] = i + 4; // Highest card in the straight
            return HandRank(HandRank::STRAIGHT, tiebreakers);
        }
    }
    // Check for special case: A-2-3-4-5 straight
    std::bitset<13> ace_low_straight_bits(0b1111000000001);
    if ((ranks_in_hand & ace_low_straight_bits) == ace_low_straight_bits)
    {
        std::array<int, 5> tiebreakers{};
        tiebreakers[0] = Card::get_rank("5"); // Highest card in the straight
        return HandRank(HandRank::STRAIGHT, tiebreakers);
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_three_of_a_kind() const
{
    std::bitset<13> suit1_bits(this->cards.to_ulong() >> 0);
    std::bitset<13> suit2_bits(this->cards.to_ulong() >> 13);
    std::bitset<13> suit3_bits(this->cards.to_ulong() >> 26);
    std::bitset<13> suit4_bits(this->cards.to_ulong() >> 39);
    std::bitset<13> triplets = ((suit1_bits & suit2_bits & suit3_bits) | (suit1_bits & suit2_bits & suit4_bits) | (suit1_bits & suit3_bits & suit4_bits) | (suit2_bits & suit3_bits & suit4_bits));
    if (triplets.any())
    {
        std::array<int, 5> tiebreakers{};
        // Primary tie breaker: rank of the three of a kind
        // Iterate downwards to get the highest three of a kind
        for (int i = 12; i >= 0; --i)
        {
            if (triplets.test(i))
            {
                tiebreakers[0] = i;
                break;
            }
        }
        // Secondary tie breaker: ranks of the two highest kickers
        std::vector<int> high_ranks = this->get_n_high_ranks(2);
        tiebreakers[1] = high_ranks[0];
        tiebreakers[2] = high_ranks[1];
        return HandRank(HandRank::THREE_OF_A_KIND, tiebreakers);
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_two_pair() const
{
    auto pair1 = this->check_for_one_pair();
    if (pair1)
    {
        // Remove the first pair from the cards, and check for second pair
        int pair1_rank = (*pair1).get_tiebreakers()[0];
        std::bitset<13> suit_mask;
        suit_mask.set(pair1_rank);
        std::bitset<52> mask = suit_mask.to_ulong() | (suit_mask.to_ulong() << 13) | (suit_mask.to_ulong() << 26) | (suit_mask.to_ulong() << 39);
        CardCollection remaining_cards = *this - CardCollection(mask);
        auto pair2 = remaining_cards.check_for_one_pair();
        if (pair2)
        {
            std::array<int, 5> tiebreakers{};
            int pair2_rank = (*pair2).get_tiebreakers()[0];
            // Primary tie breaker: highest rank of the two pairs
            tiebreakers[0] = std::max(pair1_rank, pair2_rank);
            // Secondary tie breaker: rank of the other pair
            tiebreakers[1] = std::min(pair1_rank, pair2_rank);
            // Tertiary tie breaker: rank of the kicker
            tiebreakers[2] = remaining_cards.get_n_high_ranks_except(1, {pair1_rank, pair2_rank})[0];
            return HandRank(HandRank::TWO_PAIR, tiebreakers);
        }
    }
    return std::nullopt;
}

std::optional<HandRank> CardCollection::check_for_one_pair() const
{
    std::bitset<13> suit1_bits(this->cards.to_ulong() >> 0);
    std::bitset<13> suit2_bits(this->cards.to_ulong() >> 13);
    std::bitset<13> suit3_bits(this->cards.to_ulong() >> 26);
    std::bitset<13> suit4_bits(this->cards.to_ulong() >> 39);
    std::bitset<13> pairs = ((suit1_bits & suit2_bits) | (suit1_bits & suit3_bits) | (suit1_bits & suit4_bits) | (suit2_bits & suit3_bits) | (suit2_bits & suit4_bits) | (suit3_bits & suit4_bits));
    if (pairs.any())
    {
        std::array<int, 5> tiebreakers{};
        // Primary tie breaker: rank of the pair
        // Iterate downwards to get the highest pair
        for (int i = 12; i >= 0; --i)
        {
            if (pairs.test(i))
            {
                tiebreakers[0] = i;
                break;
            }
        }
        // Secondary tie breaker: ranks of the three highest kickers
        std::vector<int> high_ranks = this->get_n_high_ranks_except(3, {tiebreakers[0]});
        tiebreakers[1] = high_ranks[0];
        tiebreakers[2] = high_ranks[1];
        tiebreakers[3] = high_ranks[2];
        return HandRank(HandRank::ONE_PAIR, tiebreakers);
    }
    return std::nullopt;
}

HandRank CardCollection::get_high_card_rank() const
{
    std::array<int, 5> tiebreakers{};
    std::vector<int> high_ranks = this->get_n_high_ranks(5);
    return HandRank(HandRank::HIGH_CARD, high_ranks);
}

std::vector<Card> CardCollection::get_n_high_cards(int n) const
{
    std::vector<Card> high_cards;
    for (int i = 0; i < 52; ++i)
    {
        if (this->cards.test(i))
        {
            high_cards.push_back(Card(i));
        }
    }
    std::sort(high_cards.begin(), high_cards.end(), std::greater<Card>());
    high_cards.resize(n);
    return high_cards;
}

std::vector<int> CardCollection::get_n_high_ranks(int n) const
{
    return CardCollection::get_n_high_ranks_except(n, std::set<int>());
}

std::vector<int> CardCollection::get_n_high_ranks_except(int n, std::set<int> ignore_ranks) const
{
    std::vector<int> high_ranks;
    for (int i = 0; i < 52; ++i)
    {
        if (this->cards.test(i))
        {
            int rank = Card(i).rank;
            if (ignore_ranks.count(rank) == 0)
            {
                high_ranks.push_back(rank);
            }
        }
    }
    std::sort(high_ranks.begin(), high_ranks.end(), std::greater<int>());
    high_ranks.resize(n);
    return high_ranks;
}

HandRank CardCollection::rank_hand() const
{
    std::optional<HandRank> hand_rank;
    if (!hand_rank)
    {
        hand_rank = this->check_for_royal_flush();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_straight_flush();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_four_of_a_kind();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_full_house();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_flush();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_straight();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_three_of_a_kind();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_two_pair();
    }
    if (!hand_rank)
    {
        hand_rank = this->check_for_one_pair();
    }
    if (!hand_rank)
    {
        hand_rank = this->get_high_card_rank();
    }
    return *hand_rank;
}

std::vector<HandRank> CardCollection::rank_all_hands() const
{
    std::vector<HandRank> hand_ranks;
    for (int i = 0; i < Hand::COMBINATIONS.size(); ++i) {
        CardCollection hand = Hand::COMBINATIONS[i];
        hand_ranks.push_back((hand+*this).rank_hand());
    }
    return hand_ranks;
}

int CardCollection::beats(const CardCollection &other) const
{
    HandRank this_rank = this->rank_hand();
    std::optional<HandRank> other_rank = other.check_for_royal_flush();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_straight_flush();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_four_of_a_kind();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_full_house();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_flush();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_straight();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_three_of_a_kind();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_two_pair();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    other_rank = other.check_for_one_pair();
    if (other_rank)
    {
        return this_rank.beats(*other_rank);
    }
    return this_rank.beats(other.get_high_card_rank());
}

int CardCollection::size() const
{
    return this->cards.count();
}

std::vector<Card> CardCollection::to_vector() const
{
    std::vector<Card> card_vector;
    for (int i = 0; i < 52; ++i)
    {
        if (this->cards.test(i))
        {
            card_vector.push_back(Card(i));
        }
    }
    return card_vector;
}

std::string CardCollection::str() const
{
    std::stringstream ss;
    for (int i = 0; i < 52; ++i)
    {
        if (this->cards.test(i))
        {
            Card card(i);
            ss << card.str() << " ";
        }
    }
    return ss.str();
}

std::string CardCollection::get_cli_repr() const
{
    std::vector<Card> card_vector;
    for (int i = 0; i < 52; ++i)
    {
        if (this->cards.test(i))
        {
            card_vector.push_back(Card(i));
        }
    }
    return Card::get_cli_repr_for_cards(card_vector);
}

CardCollection::Iterator CardCollection::begin() const
{
    int first = 0;
    while (first < 52 && !cards.test(first))
        first++;
    return Iterator(*this, first);
}

CardCollection::Iterator CardCollection::end() const
{
    return Iterator(*this, 52);
}

CardCollection CardCollection::generate_deck()
{
    auto res = CardCollection();
    res.cards.set();
    return res;
}

CardCollection::Iterator::Iterator(const CardCollection &coll, int pos) : collection(coll), index(pos) {}

Card CardCollection::Iterator::operator*() const
{
    return Card(index);
}

CardCollection::Iterator &CardCollection::Iterator::operator++()
{
    do
    {
        index++;
    } while (index < 52 && !collection.cards.test(index));
    return *this;
}

CardCollection::Iterator CardCollection::Iterator::operator++(int)
{
    Iterator tmp = *this;
    ++(*this);
    return tmp;
}

bool CardCollection::Iterator::operator==(const Iterator &other) const
{
    return index == other.index;
}

bool CardCollection::Iterator::operator!=(const Iterator &other) const
{
    return index != other.index;
}
