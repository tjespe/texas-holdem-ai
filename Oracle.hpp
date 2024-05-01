#pragma once
#include <vector>
#include <set>
#include <tuple>
#include "Card.hpp"
#include "CardCollection.hpp"

class Oracle
{
public:
    static std::set<int> find_winner(const CardCollection &table, const std::vector<CardCollection> &player_hands, const std::vector<bool> &player_is_active);
    static int get_max_bet_allowed(
        const std::vector<bool> &player_has_played,
        int current_player_i,
        const std::vector<int> &bet_in_stage,
        const std::vector<int> &player_piles,
        const std::vector<bool> &player_is_active);
    static std::vector<std::vector<float>> generate_utility_matrix(const CardCollection &table);
    static std::vector<std::vector<float>> generate_utility_matrix(const CardCollection &table, bool both_players_active);
    static std::vector<std::vector<float>> generate_utility_matrix(const CardCollection &table, bool both_players_active, const CardCollection &deck);
};
