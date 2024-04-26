#pragma once
#include <vector>
#include <set>
#include <tuple>
#include "Card.hpp"

class Oracle
{
public:
    static std::tuple<bool, std::set<Card>> check_for_royal_flush(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_straight_flush(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_four_of_a_kind(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_full_house(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_flush(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_straight(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_three_of_a_kind(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_two_pair(const std::set<Card> &hand);
    static std::tuple<bool, std::set<Card>> check_for_one_pair(const std::set<Card> &hand);
    static std::vector<Card> get_n_high_cards(const std::set<Card> &hand, int n);
    static std::vector<int> get_n_high_ranks(const std::set<Card> &hand, int n);
    static std::vector<int> rank_hand(const std::set<Card> &cards);
    static int compare_hands(const std::set<Card> &hand1, const std::set<Card> &hand2);
    static std::set<int> find_winner(const std::vector<int> &table, const std::vector<std::vector<int>> &player_hands, const std::vector<bool> &player_is_active);
    static int get_max_bet_allowed(
        const std::vector<bool> &player_has_played,
        int current_player_i,
        const std::vector<int> &current_bets,
        const std::vector<int> &player_piles,
        const std::vector<bool> &player_is_active);
    static float get_winning_probability(const std::set<int> &hand, const std::vector<int> &table, int num_players, int num_simulations = 100);
    static std::vector<std::vector<float>> generate_utility_matrix(const std::vector<int> &table, const std::vector<bool> &player_is_active);
    static std::vector<std::vector<float>> generate_utility_matrix(const std::vector<int> &table, const std::vector<bool> &player_is_active, const std::set<int> &deck);
};
