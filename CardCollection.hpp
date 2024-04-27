#pragma once
#include <bitset>
#include <set>
#include <vector>
#include <optional>
#include "Card.hpp"
#include "HandRank.hpp"

class CardCollection
{
public:
    CardCollection();
    CardCollection(std::vector<int> card_indices);
    CardCollection(std::set<int> card_indices);
    CardCollection(std::vector<Card> cards);
    CardCollection(std::set<Card> cards);
    CardCollection(std::bitset<52> cards);

    /** Operations mutating the collection */
    void add_card(const Card &card);
    void add_cards(const CardCollection &other);
    void remove_card(const Card &card);
    void remove_cards(const CardCollection &other);
    Card draw_random_card();
    CardCollection draw_random_cards(int n);

    /** Operations constructing new collections */
    CardCollection operator+(const CardCollection &other) const;
    CardCollection operator-(const CardCollection &other) const;

    /** Comparators */
    bool operator==(const CardCollection &other) const;
    bool has(const Card &card) const;
    bool is_superset(const CardCollection &other) const;
    bool is_subset(const CardCollection &other) const;
    bool intersects(const CardCollection &other) const;

    /** Functions for checking how good the hand is */
    std::optional<HandRank> check_for_royal_flush() const;
    std::optional<HandRank> check_for_straight_flush() const;
    std::optional<HandRank> check_for_four_of_a_kind() const;
    std::optional<HandRank> check_for_full_house() const;
    std::optional<HandRank> check_for_flush() const;
    std::optional<HandRank> check_for_straight() const;
    std::optional<HandRank> check_for_three_of_a_kind() const;
    std::optional<HandRank> check_for_two_pair() const;
    std::optional<HandRank> check_for_one_pair() const;
    HandRank get_high_card_rank() const;
    std::vector<Card> get_n_high_cards(int n) const;
    std::vector<int> get_n_high_ranks(int n) const;
    std::vector<int> get_n_high_ranks_except(int n, std::set<int> ignore_ranks) const;
    HandRank rank_hand() const;
    std::vector<Card> to_vector() const;

    /** Returns 1 if this collection beats the other, 0 if it's a tie, -1 if it loses */
    int beats(const CardCollection &other) const;

    /** Utility functions */
    std::string str() const;
    std::string get_cli_repr() const;

    /** Other */
    int size() const;

    class Iterator {
    public:
        using iterator_category = std::input_iterator_tag;
        using value_type = Card;
        using difference_type = std::ptrdiff_t;
        using pointer = Card*;
        using reference = Card&;
        Iterator(const CardCollection& coll, int pos);
        const CardCollection& collection;
        int index;

        Card operator*() const;
        Iterator& operator++();
        Iterator operator++(int);
        bool operator==(const Iterator& other) const;
        bool operator!=(const Iterator& other) const;
    };

    // Begin and end methods for iterator
    Iterator begin() const;
    Iterator end() const;

    static CardCollection generate_deck();

private:
    // Store cards in a bit string
    std::bitset<52> cards;
};
