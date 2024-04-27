#include "Oracle.hpp"
#include <algorithm>
#include <numeric>
#include <map>
#include <random>
#include <iostream>
#include "Hand.hpp"

std::tuple<bool, std::set<Card>> Oracle::check_for_royal_flush(const std::set<Card> &hand)
{
    for (auto suit = 0; suit < 4; ++suit)
    {
        std::set<Card> royal_flush;
        for (auto rank = Card::get_rank("10"); rank <= Card::get_rank("A"); ++rank)
        {
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
    std::sort(sorted_cards.begin(), sorted_cards.end(), std::greater<Card>());
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

std::vector<int> Oracle::rank_hand(const std::set<Card> &cards, std::vector<int> *compare_to)
{
    int stop_rank = 0;
    if (compare_to != NULL && compare_to->size() > 0)
    {
        stop_rank = compare_to->at(0);
    }
    auto [has_royal_flush, royal_flush] = check_for_royal_flush(cards);
    if (has_royal_flush)
    {
        return {9}; // Highest rank for royal flush, no tie-breakers as all royal flushes are equal
    }
    if (stop_rank == 9)
    {
        return {0}; // No royal flush, but the other hand has it, so this hand loses
    }

    auto [has_straight_flush, straight_flush] = check_for_straight_flush(cards);
    if (has_straight_flush)
    {
        return {8, max_element(straight_flush.begin(), straight_flush.end())->rank};
    }
    if (stop_rank == 8)
    {
        return {0}; // No straight flush, but the other hand has it, so this hand loses
    }

    auto [has_four_of_a_kind, quadruplet] = check_for_four_of_a_kind(cards);
    if (has_four_of_a_kind)
    {
        int quad_rank = quadruplet.begin()->rank;
        std::vector<int> high_ranks = get_n_high_ranks(cards, 1);
        return {7, quad_rank, high_ranks[0]};
    }
    if (stop_rank == 7)
    {
        return {0}; // No four of a kind, but the other hand has it, so this hand loses
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
    if (stop_rank == 6)
    {
        return {0}; // No full house, but the other hand has it, so this hand loses
    }

    auto [has_flush, flush] = check_for_flush(cards);
    if (has_flush)
    {
        std::vector<int> high_ranks = get_n_high_ranks(flush, 5);
        return {5, high_ranks[0], high_ranks[1], high_ranks[2], high_ranks[3], high_ranks[4]};
    }
    if (stop_rank == 5)
    {
        return {0}; // No flush, but the other hand has it, so this hand loses
    }

    auto [has_straight, straight] = check_for_straight(cards);
    if (has_straight)
    {
        return {4, max_element(straight.begin(), straight.end())->rank};
    }
    if (stop_rank == 4)
    {
        return {0}; // No straight, but the other hand has it, so this hand loses
    }

    auto [has_three_of_a_kind, triplet] = check_for_three_of_a_kind(cards);
    if (has_three_of_a_kind)
    {
        std::vector<int> high_ranks = get_n_high_ranks(cards, 2);
        return {3, triplet.begin()->rank, high_ranks[0], high_ranks[1]};
    }
    if (stop_rank == 3)
    {
        return {0}; // No three of a kind, but the other hand has it, so this hand loses
    }

    auto [has_two_pair, two_pair_cards] = check_for_two_pair(cards);
    if (has_two_pair)
    {
        std::set<int> pair_rank_set;
        for (const Card &card : two_pair_cards)
        {
            pair_rank_set.insert(card.rank);
        }
        std::vector<int> pair_ranks(pair_rank_set.begin(), pair_rank_set.end());
        std::sort(pair_ranks.begin(), pair_ranks.end(), std::greater<int>());
        std::vector<int> high_ranks = get_n_high_ranks(cards, 1);
        return {2, pair_ranks[0], pair_ranks[1], high_ranks[0]};
    }
    if (stop_rank == 2)
    {
        return {0}; // No two pair, but the other hand has it, so this hand loses
    }

    auto [has_one_pair, pair] = check_for_one_pair(cards);
    if (has_one_pair)
    {
        std::vector<int> high_ranks = get_n_high_ranks(cards, 3);
        return {1, pair.begin()->rank, high_ranks[0], high_ranks[1], high_ranks[2]};
    }
    if (stop_rank == 1)
    {
        return {0}; // No one pair, but the other hand has it, so this hand loses
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
    std::vector<int> rank2 = rank_hand(hand2, &rank1);
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
    std::set<Card> best_hand;

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
                best_hand = hand;
            }
            else
            {
                int comparison = compare_hands(hand, best_hand);
                if (comparison == 1)
                {
                    winners.clear();
                    winners.insert(i);
                    best_hand = hand;
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
float Oracle::get_winning_probability(const std::set<int> &hand, const std::vector<int> &table, int num_players, int num_simulations)
{
    std::vector<int> simulations;
    std::vector<int> deck;
    for (int i = 0; i < 52; ++i)
    {
        if (hand.find(i) == hand.end() && std::find(table.begin(), table.end(), i) == table.end())
        {
            deck.push_back(i);
        }
    }
    for (int i = 0; i < num_simulations; ++i)
    {
        std::vector<int> deck_copy = deck;
        std::random_device rd;
        std::mt19937 g(rd());
        std::shuffle(deck_copy.begin(), deck_copy.end(), g);
        std::vector<int> new_table = table;
        while (new_table.size() < 5)
        {
            new_table.push_back(deck_copy.back());
            deck_copy.pop_back();
        }
        std::cout << "Table:\n"
                  << Card::get_cli_repr_for_cards(new_table) << std::endl;
        std::vector<std::vector<int>> player_hands;
        player_hands.push_back(std::vector<int>(hand.begin(), hand.end()));
        while (player_hands.size() < num_players)
        {
            player_hands.push_back({deck_copy.back(), deck_copy.back()});
            deck_copy.pop_back();
        }
        for (int pi = 0; pi < num_players; ++pi)
        {
            std::cout << "Player " << pi << " hand:\n"
                      << Card::get_cli_repr_for_cards(player_hands[pi]) << std::endl;
        }
        std::cout << "In total, " << player_hands.size() << " players.\n";
        std::cout << "Requested num of players: " << num_players << std::endl;
        std::set<int> winners = Oracle::find_winner(new_table, player_hands, std::vector<bool>(num_players, true));
        if (winners.find(0) != winners.end())
        {
            std::cout << "Player 0 wins!" << std::endl;
            simulations.push_back(1);
        }
        else
        {
            std::cout << "Player 0 loses!" << std::endl;
            simulations.push_back(0);
        }
    }
    return std::accumulate(simulations.begin(), simulations.end(), 0) / (float)num_simulations;
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const CardCollection &table, const std::vector<bool> &player_is_active, int perspective)
{
    CardCollection deck = CardCollection::generate_deck();
    return generate_utility_matrix(table, player_is_active, perspective, deck);
}

std::vector<std::vector<float>> Oracle::generate_utility_matrix(const CardCollection &table, const std::vector<bool> &player_is_active, int perspective, const CardCollection &deck)
{
    if (player_is_active.size() != 2)
    {
        throw std::invalid_argument("generate_utility_matrix is implemented for two players only.");
    }

    CardCollection remaining_deck = deck - table;

    // Initialize utility matrix
    std::vector<std::vector<float>> utility_matrix(Hand::COMBINATIONS.size(), std::vector<float>(Hand::COMBINATIONS.size(), 0.0));

    // Generate combinations of hands for the two players
    int overlaps = 0;
    int skips_by_active = 0;
    int comparison_count = 0;
    for (int i = 0; i < Hand::COMBINATIONS.size(); ++i)
    {
        auto player_hand = Hand(i);
        if (player_hand.get_cards().intersects(table))
        {
            // std::cout << "Player hand " << player_hand.str() << " overlaps with table " << table.str() << std::endl;
            overlaps++;
            continue;
        }
        if ((i % 100) == 0)
        {
            std::cout << "i: " << i << std::endl;
        }
        for (int j = i + 1; j < Hand::COMBINATIONS.size(); ++j)
        {
            auto opponent_hand = Hand(j);
            if (player_hand.get_cards().intersects(opponent_hand.get_cards()))
            {
                // std::cout << "Overlapping hands: " << player_hand.str() << " and " << opponent_hand.str() << std::endl;
                overlaps++;
                continue;
            }
            if (player_hand.get_cards().intersects(table) || opponent_hand.get_cards().intersects(table))
            {
                // std::cout << "Player hand " << player_hand.str() << " overlaps with table " << table.str() << std::endl;
                overlaps++;
                continue;
            }
            if (player_hand.get_cards().intersects(table) || opponent_hand.get_cards().intersects(table))
            {
                // std::cout << "Opponent hand " << opponent_hand.str() << " overlaps with table " << table.str() << std::endl;
                overlaps++;
                continue;
            }
            if (player_is_active[perspective] && !player_is_active[1 - perspective])
            {
                utility_matrix[i][j] = 1.0;
                utility_matrix[j][i] = 1.0;
                skips_by_active++;
                continue;
            }
            auto player_cards = table + player_hand.get_cards();
            auto opponents_cards = table + opponent_hand.get_cards();
            // Calculate the utility of the player's hand against the opponent's hand (1 if player wins, -1 if opponent wins, 0 if tie)
            int utility = player_cards.beats(opponents_cards);
            utility_matrix[i][j] = utility;
            utility_matrix[j][i] = -utility;
            comparison_count++;
        }
    }
    std::cout << "Overlaps: " << overlaps << std::endl;
    std::cout << "Skips by active: " << skips_by_active << std::endl;
    std::cout << "Comparisons: " << comparison_count << std::endl;

    return utility_matrix;
}
