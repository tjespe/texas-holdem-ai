#include "CheatSheet.hpp"
#include "Oracle.hpp"
#include <fstream>
#include <iostream>
#include <csignal>
#include <cstdlib>
#include <algorithm>
#include "Hand.hpp"

std::string CheatSheet::cache_file_path = "cheat-sheet.txt";
bool CheatSheet::cache_loaded = false;

void CheatSheet::load_cache()
{
    setup_signal_handlers();
    std::atexit(save_cache);
    std::ifstream file(cache_file_path);
    std::string line;
    while (getline(file, line))
    {
        size_t first_space_pos = line.find(' ');
        size_t last_space_pos = line.rfind(' ');
        std::string key = line.substr(0, first_space_pos);
        float probability = std::stof(line.substr(first_space_pos + 1, last_space_pos - first_space_pos - 1));
        int sims = std::stoi(line.substr(last_space_pos + 1));
        cache[key] = {probability, sims};
    }
    file.close();
}

void CheatSheet::save_cache()
{
    std::cout << "Saving cache" << std::endl;
    std::ofstream file(cache_file_path);
    for (const auto &[key, value] : cache)
    {
        file << key << " " << value.first << " " << value.second << "\n";
    }
    file.close();
}

void CheatSheet::signal_handler(int signal)
{
    std::cout << "Caught signal " << signal << ", saving cache and exiting" << std::endl;
    save_cache();
    exit(signal);
}

void CheatSheet::setup_signal_handlers()
{
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);
}

std::string CheatSheet::convert_cards_to_equiv_str(CardCollection &hand, CardCollection &table)
{
    std::vector<Card> hand_cards = hand.to_vector();
    std::vector<Card> table_cards = table.to_vector();
    std::sort(hand_cards.begin(), hand_cards.end());
    std::sort(table_cards.begin(), table_cards.end());
    std::unordered_map<int, std::string> suits_reencoding;
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

float CheatSheet::get_winning_probability(CardCollection &hand, CardCollection &table, int num_players, int num_simulations)
{
    std::string key = convert_cards_to_equiv_str(hand, table);
    return find_or_simulate(hand, table, num_players, num_simulations).first;
}

float CheatSheet::get_winning_probability(CardCollection &hand, CardCollection &table, int num_players)
{
    return get_winning_probability(hand, table, num_players, 10000);
}

std::vector<float> CheatSheet::get_all_winning_probabilities(CardCollection &table, int num_players, int num_simulations) {
    std::vector<float> winning_probabilities(Hand::COMBINATIONS.size(), 0.0);
    for (int i = 0; i < Hand::COMBINATIONS.size(); ++i) {
        winning_probabilities[i] = get_winning_probability(Hand::COMBINATIONS[i], table, num_players, num_simulations);
    }
    return winning_probabilities;
}

std::vector<float> CheatSheet::get_all_winning_probabilities(CardCollection &table, int num_players) {
    return get_all_winning_probabilities(table, num_players, 10000);
}


std::pair<float, int> CheatSheet::find_or_simulate(CardCollection &hand, CardCollection &table, int num_players, int num_simulations)
{
    if (!cache_loaded)
    {
        load_cache();
        cache_loaded = true;
    }
    std::string key = convert_cards_to_equiv_str(hand, table);
    auto it = cache.find(key);
    if (it != cache.end() && it->second.second >= num_simulations)
    {
        return it->second;
    }
    float prob = get_winning_probability_n_simulations(hand, table, num_players, num_simulations);
    cache[key] = {prob, num_simulations};
    return {prob, num_simulations};
}

float CheatSheet::get_winning_probability_n_simulations(CardCollection &hand, CardCollection &table, int num_players, int num_simulations)
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
