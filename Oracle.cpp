#include "Oracle.hpp"
#include <algorithm>
#include <numeric>
#include <map>
#include <random>
#include <iostream>
#include <climits>
#include "Hand.hpp"

std::set<int> Oracle::find_winner(const CardCollection &table, const std::vector<CardCollection> &player_hands, const std::vector<bool> &player_is_active)
{
    std::set<int> winners;
    HandRank best_hand_rank = HandRank(0, std::array{0, 0, 0, 0, 0});

    for (size_t i = 0; i < player_hands.size(); ++i)
    {
        if (player_is_active[i])
        {
            CardCollection hand = table + player_hands[i];
            HandRank hand_rank = hand.rank_hand();
            if (winners.empty())
            {
                winners.insert(i);
                best_hand_rank = hand_rank;
            }
            else
            {
                int comparison = hand_rank.beats(best_hand_rank);
                if (comparison == 1)
                {
                    winners.clear();
                    winners.insert(i);
                    best_hand_rank = hand_rank;
                }
                else if (comparison == 0)
                {
                    winners.insert(i);
                }
            }
        }
    }
    return winners;
}

/**
 * To simplify the game, it is not allowed to bet more than the smallest stack.
 * Aditionally, a player who has already played cannot reraise, they can only call or fold.
 */
int Oracle::get_max_bet_allowed(
    const std::vector<bool> &player_has_played,
    int current_player_i,
    const std::vector<int> &bet_in_stage,
    const std::vector<int> &player_piles,
    const std::vector<bool> &player_is_active)
{
    std::vector<int> max_stack_per_player;
    for (size_t i = 0; i < player_piles.size(); ++i)
    {
        max_stack_per_player.push_back(player_piles[i] + bet_in_stage[i]);
    }
    int min_stack = INT_MAX;
    for (size_t i = 0; i < player_is_active.size(); ++i)
    {
        if (player_is_active[i])
        {
            min_stack = std::min(min_stack, max_stack_per_player[i]);
        }
    }
    int max_allowed = min_stack - bet_in_stage[current_player_i];
    if (player_has_played[current_player_i])
    {
        int call_amount = *std::max_element(bet_in_stage.begin(), bet_in_stage.end()) - bet_in_stage[current_player_i];
        return std::min(call_amount, max_allowed);
    }
    return max_allowed;
}


std::vector<std::vector<float>> Oracle::generate_utility_matrix(const CardCollection &table)
{
    return generate_utility_matrix(table, true);
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const CardCollection &table, bool both_players_active)
{
    CardCollection deck = CardCollection::generate_deck();
    return generate_utility_matrix(table, both_players_active, deck);
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const CardCollection &table, bool both_players_active, const CardCollection &deck)
{
    CardCollection remaining_deck = deck - table;

    // Initialize utility matrix
    std::vector<std::vector<float>> utility_matrix(Hand::COMBINATIONS.size(), std::vector<float>(Hand::COMBINATIONS.size(), 0.0));

    // Generate combinations of hands for the two players
    for (int i = 0; i < Hand::COMBINATIONS.size(); ++i)
    {
        auto player_hand = Hand(i);
        if (player_hand.get_cards().intersects(table))
        {
            continue;
        }
        if (both_players_active && (i % 50) == 0)
        {
            std::cout << "\r" << 100 * i / Hand::COMBINATIONS.size() << "%" << std::flush;
        }
        for (int j = i + 1; j < Hand::COMBINATIONS.size(); ++j)
        {
            auto opponent_hand = Hand(j);
            if (player_hand.get_cards().intersects(opponent_hand.get_cards()) || opponent_hand.get_cards().intersects(table))
            {
                continue;
            }
            if (!both_players_active)
            {
                // The active player wins all possible hands
                utility_matrix[i][j] = 1.0;
                utility_matrix[j][i] = 1.0;
                continue;
            }
            auto player_cards = table + player_hand.get_cards();
            auto opponents_cards = table + opponent_hand.get_cards();
            // Calculate the utility of the player's hand against the opponent's hand (1 if player wins, -1 if opponent wins, 0 if tie)
            int utility = player_cards.beats(opponents_cards);
            utility_matrix[i][j] = utility;
            utility_matrix[j][i] = -utility;
        }
    }

    return utility_matrix;
}
