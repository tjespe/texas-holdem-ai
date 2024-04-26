#include "Oracle.hpp"
#include <algorithm>
#include <numeric>
#include <map>
#include <random>

std::tuple<bool, std::set<Card>> Oracle::check_for_royal_flush(const std::set<Card> &hand)
{
    for (auto suit = 0; suit < 4; ++suit)
    {
        std::set<Card> royal_flush;
        for (auto rank = 10; rank <= 14; ++rank)
        { // Assuming Ace high as 14
            Card card(rank, suit);
            if (hand.find(card) == hand.end())
            {
                break;
            }
            royal_flush.insert(card);
        }
        if (royal_flush.size() == 5)
        {
            return {true, royal_flush};
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_straight_flush(const std::set<Card> &hand)
{
    for (auto suit = 0; suit < 4; ++suit)
    {
        for (int start_rank = 14; start_rank >= 5; --start_rank)
        { // Ace can be high or low
            std::set<Card> straight_flush;
            for (int rank = start_rank; rank > start_rank - 5; --rank)
            {
                int effective_rank = (rank == 1) ? 14 : rank; // Ace as high
                Card card(effective_rank, suit);
                if (hand.find(card) == hand.end())
                {
                    break;
                }
                straight_flush.insert(card);
            }
            if (straight_flush.size() == 5)
            {
                return {true, straight_flush};
            }
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_four_of_a_kind(const std::set<Card> &hand)
{
    std::map<int, std::set<Card>> rank_to_cards;
    for (const auto &card : hand)
    {
        rank_to_cards[card.rank].insert(card);
    }
    for (const auto &[rank, cards] : rank_to_cards)
    {
        if (cards.size() == 4)
        {
            return {true, cards};
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_full_house(const std::set<Card> &hand)
{
    auto [has_three, three_of_a_kind] = check_for_three_of_a_kind(hand);
    if (!has_three)
    {
        return {false, {}};
    }
    std::set<Card> remaining(hand.begin(), hand.end());
    for (const Card &card : three_of_a_kind)
    {
        remaining.erase(card);
    }
    auto [has_pair, one_pair] = check_for_one_pair(remaining);
    if (!has_pair)
    {
        return {false, {}};
    }
    std::set<Card> full_house(three_of_a_kind.begin(), three_of_a_kind.end());
    full_house.insert(one_pair.begin(), one_pair.end());
    return {true, full_house};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_flush(const std::set<Card> &hand)
{
    std::map<int, std::set<Card>> suit_to_cards;
    for (const auto &card : hand)
    {
        suit_to_cards[card.suit].insert(card);
    }
    for (const auto &[suit, cards] : suit_to_cards)
    {
        if (cards.size() >= 5)
        {
            return {true, std::set<Card>(cards.rbegin(), std::next(cards.rbegin(), 5))};
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_straight(const std::set<Card> &hand)
{
    if (hand.size() < 5)
    {
        return {false, {}};
    }
    std::vector<int> ranks;
    for (const auto &card : hand)
    {
        ranks.push_back(card.rank);
        // Handle the Ace as both high and low
        if (card.rank == 14)
        {
            ranks.push_back(1);
        }
    }
    std::sort(ranks.begin(), ranks.end());
    auto last = std::unique(ranks.begin(), ranks.end());
    ranks.erase(last, ranks.end());

    int consecutive_count = 1;
    for (size_t i = 1; i < ranks.size(); ++i)
    {
        if (ranks[i] == ranks[i - 1] + 1)
        {
            consecutive_count++;
            if (consecutive_count == 5)
            {
                std::set<Card> straight;
                int start_rank = ranks[i - 4];
                for (const auto &card : hand)
                {
                    if (card.rank >= start_rank && card.rank <= start_rank + 4)
                    {
                        straight.insert(card);
                    }
                }
                return {true, straight};
            }
        }
        else
        {
            consecutive_count = 1;
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_three_of_a_kind(const std::set<Card> &hand)
{
    std::map<int, std::set<Card>> rank_to_cards;
    for (const auto &card : hand)
    {
        rank_to_cards[card.rank].insert(card);
    }
    for (const auto &[rank, cards] : rank_to_cards)
    {
        if (cards.size() == 3)
        {
            return {true, cards};
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_two_pair(const std::set<Card> &hand)
{
    std::map<int, std::set<Card>> rank_to_cards;
    std::vector<std::set<Card>> pairs;
    for (const auto &card : hand)
    {
        rank_to_cards[card.rank].insert(card);
    }
    for (const auto &[rank, cards] : rank_to_cards)
    {
        if (cards.size() >= 2)
        {
            pairs.push_back(std::set<Card>(cards.begin(), std::next(cards.begin(), 2)));
            if (pairs.size() == 2)
            {
                std::set<Card> two_pairs;
                for (const auto &pair : pairs)
                {
                    two_pairs.insert(pair.begin(), pair.end());
                }
                return {true, two_pairs};
            }
        }
    }
    return {false, {}};
}

std::tuple<bool, std::set<Card>> Oracle::check_for_one_pair(const std::set<Card> &hand)
{
    std::map<int, std::set<Card>> rank_to_cards;
    for (const auto &card : hand)
    {
        rank_to_cards[card.rank].insert(card);
    }
    for (const auto &[rank, cards] : rank_to_cards)
    {
        if (cards.size() == 2)
        {
            return {true, std::set<Card>(cards.begin(), std::next(cards.begin(), 2))};
        }
    }
    return {false, {}};
}

std::vector<Card> Oracle::get_n_high_cards(const std::set<Card> &hand, int n)
{
    std::vector<Card> sorted_cards(hand.begin(), hand.end());
    std::sort(sorted_cards.begin(), sorted_cards.end(), CardSortingComparator());
    if (sorted_cards.size() > n)
    {
        sorted_cards.resize(n);
    }
    return sorted_cards;
}

std::vector<int> Oracle::get_n_high_ranks(const std::set<Card> &hand, int n)
{
    std::vector<Card> high_cards = get_n_high_cards(hand, n);
    std::vector<int> high_ranks;
    for (const auto &card : high_cards)
    {
        high_ranks.push_back(card.rank);
    }
    return high_ranks;
}

std::vector<int> Oracle::rank_hand(const std::set<Card> &cards)
{
    auto [has_royal_flush, royal_flush] = check_for_royal_flush(cards);
    if (has_royal_flush)
    {
        return {9}; // Highest rank for royal flush, no tie-breakers as all royal flushes are equal
    }

    auto [has_straight_flush, straight_flush] = check_for_straight_flush(cards);
    if (has_straight_flush)
    {
        return {8, max_element(straight_flush.begin(), straight_flush.end())->rank};
    }

    auto [has_four_of_a_kind, quadruplet] = check_for_four_of_a_kind(cards);
    if (has_four_of_a_kind)
    {
        int quad_rank = quadruplet.begin()->rank;
        std::vector<int> high_ranks = get_n_high_ranks(cards, 1);
        return {7, quad_rank, high_ranks[0]};
    }

    auto [has_full_house, full_house] = check_for_full_house(cards);
    if (has_full_house)
    {
        auto [_, triplet] = check_for_three_of_a_kind(full_house);
        std::set<Card> pair = full_house;
        for (const Card &card : triplet)
        {
            pair.erase(card);
        }
        return {6, triplet.begin()->rank, pair.begin()->rank};
    }

    auto [has_flush, flush] = check_for_flush(cards);
    if (has_flush)
    {
        std::vector<int> high_ranks = get_n_high_ranks(flush, 5);
        return {5, high_ranks[0], high_ranks[1], high_ranks[2], high_ranks[3], high_ranks[4]};
    }

    auto [has_straight, straight] = check_for_straight(cards);
    if (has_straight)
    {
        return {4, max_element(straight.begin(), straight.end())->rank};
    }

    auto [has_three_of_a_kind, triplet] = check_for_three_of_a_kind(cards);
    if (has_three_of_a_kind)
    {
        std::vector<int> high_ranks = get_n_high_ranks(cards, 2);
        return {3, triplet.begin()->rank, high_ranks[0], high_ranks[1]};
    }

    auto [has_two_pair, two_pair_cards] = check_for_two_pair(cards);
    if (has_two_pair)
    {
        std::vector<int> pair_ranks;
        for (const Card &card : two_pair_cards)
        {
            pair_ranks.push_back(card.rank);
        }
        std::sort(pair_ranks.begin(), pair_ranks.end(), std::greater<int>());
        std::vector<int> high_ranks = get_n_high_ranks(cards, 1);
        return {2, pair_ranks[0], pair_ranks[1], high_ranks[0]};
    }

    auto [has_one_pair, pair] = check_for_one_pair(cards);
    if (has_one_pair)
    {
        std::vector<int> high_ranks = get_n_high_ranks(cards, 3);
        return {1, pair.begin()->rank, high_ranks[0], high_ranks[1], high_ranks[2]};
    }

    std::vector<int> high_ranks = get_n_high_ranks(cards, 5);
    return {0, high_ranks[0], high_ranks[1], high_ranks[2], high_ranks[3], high_ranks[4]};
}

/**
 * Compare two hands and return 1 if hand1 wins, -1 if hand2 wins, and 0 if it's a tie.
 */
int Oracle::compare_hands(const std::set<Card> &hand1, const std::set<Card> &hand2)
{
    std::vector<int> rank1 = rank_hand(hand1);
    std::vector<int> rank2 = rank_hand(hand2);
    for (size_t i = 0; i < rank1.size(); ++i)
    {
        if (rank1[i] > rank2[i])
        {
            return 1;
        }
        else if (rank1[i] < rank2[i])
        {
            return -1;
        }
    }
    return 0;
}

std::set<int> Oracle::find_winner(const std::vector<int> &table, const std::vector<std::vector<int>> &player_hands, const std::vector<bool> &player_is_active)
{
    std::set<int> winners;
    for (size_t i = 0; i < player_hands.size(); ++i)
    {
        if (player_is_active[i])
        {
            std::set<Card> hand;
            for (int card : table)
            {
                hand.insert(Card(card));
            }
            for (int card : player_hands[i])
            {
                hand.insert(Card(card));
            }
            if (winners.empty())
            {
                winners.insert(i);
            }
            else
            {
                std::set<Card> winning_hand;
                for (int winner : winners)
                {
                    std::set<Card> winner_hand;
                    for (int card : table)
                    {
                        winner_hand.insert(Card(card));
                    }
                    for (int card : player_hands[winner])
                    {
                        winner_hand.insert(Card(card));
                    }
                    if (compare_hands(hand, winner_hand) == 1)
                    {
                        winning_hand = hand;
                    }
                    else
                    {
                        winning_hand = winner_hand;
                    }
                }
                if (compare_hands(hand, winning_hand) == 1)
                {
                    winners.clear();
                    winners.insert(i);
                }
                else if (compare_hands(hand, winning_hand) == 0)
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
    const std::vector<int> &current_bets,
    const std::vector<int> &player_piles,
    const std::vector<bool> &player_is_active)
{
    std::vector<int> max_stack_per_player;
    for (size_t i = 0; i < player_piles.size(); ++i)
    {
        max_stack_per_player.push_back(player_piles[i] + current_bets[i]);
    }
    int min_stack = INT_MAX;
    for (size_t i = 0; i < player_is_active.size(); ++i)
    {
        if (player_is_active[i])
        {
            min_stack = std::min(min_stack, max_stack_per_player[i]);
        }
    }
    int max_allowed = min_stack - current_bets[current_player_i];
    if (player_has_played[current_player_i])
    {
        int call_amount = *std::max_element(current_bets.begin(), current_bets.end()) - current_bets[current_player_i];
        return std::min(call_amount, max_allowed);
    }
    return max_allowed;
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
    std::sort(hand_cards.begin(), hand_cards.end(), CardSortingComparator());
    std::sort(table_cards.begin(), table_cards.end(), CardSortingComparator());
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
float Oracle::get_winning_probability(const std::set<int> &hand, const std::vector<int> &table, int num_players, int num_simulations)
{
    std::vector<int> simulations;
    for (int i = 0; i < num_simulations; ++i)
    {
        std::vector<int> deck;
        for (int i = 0; i < 52; ++i)
        {
            if (hand.find(i) == hand.end() && std::find(table.begin(), table.end(), i) == table.end())
            {
                deck.push_back(i);
            }
        }
        std::random_device rd;
        std::mt19937 g(rd());
        std::shuffle(deck.begin(), deck.end(), g);
        std::vector<int> new_table = table;
        while (new_table.size() < 5)
        {
            new_table.push_back(deck.back());
            deck.pop_back();
        }
        std::vector<std::vector<int>> player_hands;
        player_hands.push_back(std::vector<int>(hand.begin(), hand.end()));
        while (player_hands.size() < num_players)
        {
            player_hands.push_back({deck.back(), deck.back()});
            deck.pop_back();
        }
        std::set<int> winners = Oracle::find_winner(new_table, player_hands, std::vector<bool>(num_players, true));
        if (winners.find(0) != winners.end())
        {
            simulations.push_back(1);
        }
        else
        {
            simulations.push_back(0);
        }
    }
    return std::accumulate(simulations.begin(), simulations.end(), 0) / (float)num_simulations;
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const std::vector<int> &table, const std::vector<bool> &player_is_active)
{
    std::set<int> deck;
    for (int i = 0; i < 52; ++i)
    {
        deck.insert(i);
    }
    return generate_utility_matrix(table, player_is_active, deck);
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const std::vector<int> &table, const std::vector<bool> &player_is_active, const std::set<int> &deck)
{
    if (player_is_active.size() != 2)
    {
        throw std::invalid_argument("generate_utility_matrix is implemented for two players only.");
    }

    std::set<int> remaining_deck = deck; // Copy of deck to modify
    for (int card : table)
    {
        remaining_deck.erase(card); // Remove table cards from the deck
    }

    std::vector<std::pair<int, int>> possible_hole_cards;
    for (auto it1 = remaining_deck.begin(); it1 != remaining_deck.end(); ++it1)
    {
        auto it2 = it1;
        for (++it2; it2 != remaining_deck.end(); ++it2)
        {
            possible_hole_cards.emplace_back(*it1, *it2);
        }
    }

    // Initialize utility matrix
    std::vector<std::vector<float>> utility_matrix(possible_hole_cards.size(), std::vector<float>(possible_hole_cards.size(), 0.0));

    // Map each pair of cards to an index for easy access in the matrix
    std::map<std::pair<int, int>, int> card_pair_to_index;
    for (int i = 0; i < possible_hole_cards.size(); ++i)
    {
        card_pair_to_index[possible_hole_cards[i]] = i;
    }

    // Generate combinations of hands for the two players
    for (const auto &player1_hand : possible_hole_cards)
    {
        for (const auto &player2_hand : possible_hole_cards)
        {
            if (player1_hand.first == player2_hand.first || player1_hand.first == player2_hand.second ||
                player1_hand.second == player2_hand.first || player1_hand.second == player2_hand.second)
            {
                continue; // Skip overlapping card pairs
            }

            std::vector<std::vector<int>> player_hands(2);
            player_hands[0] = {player1_hand.first, player1_hand.second};
            player_hands[1] = {player2_hand.first, player2_hand.second};

            std::set<int> winners = Oracle::find_winner(table, player_hands, player_is_active);

            if (winners.find(0) != winners.end() && winners.find(1) != winners.end())
            {
                utility_matrix[card_pair_to_index[player1_hand]][card_pair_to_index[player2_hand]] = 0; // Tie
            }
            else if (winners.find(0) != winners.end())
            {
                utility_matrix[card_pair_to_index[player1_hand]][card_pair_to_index[player2_hand]] = 1; // Player 1 wins
            }
            else
            {
                utility_matrix[card_pair_to_index[player1_hand]][card_pair_to_index[player2_hand]] = -1; // Player 2 wins
            }
        }
    }

    return utility_matrix;
}
