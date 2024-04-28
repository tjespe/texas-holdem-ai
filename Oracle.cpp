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

float Oracle::get_winning_probability(const CardCollection &hand, const CardCollection &table, int num_players)
{
    return get_winning_probability_n_simulations(hand, table, num_players, 5000);
}

/**
 * Will be used later for caching get_winning_probability results.
 */
std::string _convert_cards_to_equiv_str(const std::set<int> &hand, const std::vector<int> &table)
{
    std::vector<Card> hand_cards;
    for (int c : hand)
    {
        hand_cards.push_back(Card(c));
    }
    std::vector<Card> table_cards;
    for (int c : table)
    {
        table_cards.push_back(Card(c));
    }
    std::sort(hand_cards.begin(), hand_cards.end());
    std::sort(table_cards.begin(), table_cards.end());
    std::map<int, std::string> suits_reencoding;
    std::set<int> encountered_suits;
    for (const Card &card : hand_cards)
    {
        if (encountered_suits.find(card.suit) == encountered_suits.end())
        {
            suits_reencoding[card.suit] = std::string(1, "ABCD"[encountered_suits.size()]);
            encountered_suits.insert(card.suit);
        }
    }
    for (const Card &card : table_cards)
    {
        if (encountered_suits.find(card.suit) == encountered_suits.end())
        {
            suits_reencoding[card.suit] = std::string(1, "ABCD"[encountered_suits.size()]);
            encountered_suits.insert(card.suit);
        }
    }
    std::string hand_str;
    for (const Card &card : hand_cards)
    {
        hand_str += std::to_string(card.rank) + suits_reencoding[card.suit];
    }
    std::string table_str;
    for (const Card &card : table_cards)
    {
        table_str += std::to_string(card.rank) + suits_reencoding[card.suit];
    }
    return "hand:" + hand_str + "_table:" + table_str;
}

/**
 * Simulate num_simulations games and return the probability of winning, given the hand and table cards.
 * Not taking player actions into account, just the cards.
 */
float Oracle::get_winning_probability_n_simulations(const CardCollection &hand, const CardCollection &table, int num_players, int num_simulations)
{
    int wins = 0;
    CardCollection deck = CardCollection::generate_deck() - hand - table;
    for (int i = 0; i < num_simulations; ++i)
    {
        CardCollection deck_copy = deck;
        CardCollection table_copy = table + deck_copy.draw_random_cards(5 - table.size());
        std::vector<CardCollection> player_hands;
        player_hands.push_back(hand);
        while (player_hands.size() < num_players)
        {
            player_hands.push_back(deck_copy.draw_random_cards(2));
        }
        std::set<int> winners = Oracle::find_winner(table_copy, player_hands, std::vector<bool>(num_players, true));
        if (winners.find(0) != winners.end())
        {
            wins++;
        }
    }
    return (float)wins / num_simulations;
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
