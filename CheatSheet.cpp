#include "CheatSheet.hpp"
#include "Oracle.hpp"
#include <fstream>
#include <iostream>
#include <csignal>
#include <cstdlib>
#include <algorithm>
#include <map>
#include "Hand.hpp"

std::string CheatSheet::cache_file_path = "cheat-sheet-v2.txt";
bool CheatSheet::cache_loaded = false;

void CheatSheet::load_cache()
{
    std::cout << "Setting up signal handlers" << std::endl;
    setup_signal_handlers();
    std::atexit(save_cache);
    std::ifstream file(cache_file_path);
    std::string line;
    while (getline(file, line))
    {
        size_t first_space_pos = line.find(' ');
        size_t last_space_pos = line.rfind(' ');
        
        // Parse the key as a uint64_t
        uint64_t key = std::stoull(line.substr(0, first_space_pos));
        
        // Parse the probability and simulations count
        float probability = std::stof(line.substr(first_space_pos + 1, last_space_pos - first_space_pos - 1));
        int sims = std::stoi(line.substr(last_space_pos + 1));
        
        // Insert into cache
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
        // Convert the key (uint64_t) to a string and write to file
        file << std::to_string(key) << " " << value.first << " " << value.second << "\n";
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

uint64_t CheatSheet::convert_cards_to_equiv_str(CardCollection &hand, CardCollection &table, int num_players) {
    // Sort the hand and table separately to maintain a consistent order within each group
    std::vector<Card> hand_cards = hand.to_vector();
    std::vector<Card> table_cards = table.to_vector();
    std::sort(hand_cards.begin(), hand_cards.end());
    std::sort(table_cards.begin(), table_cards.end());

    // Suit re-encoding array, initialized to -1 to indicate unmapped suits
    char suits_reencoding[4] = { -1, -1, -1, -1 };
    char next_suit_code = 0;  // Start encoding suits with 0

    uint64_t result = 0;

    // Encode the number of players (4 bits)
    result |= (num_players & 0xF);

    // Encode the hand (first 12 bits: 6 bits for each card)
    int shift = 4;
    for (const Card &card : hand_cards) {
        // Re-encode the suit if it hasn't been encountered yet
        if (suits_reencoding[card.suit] == -1) {
            suits_reencoding[card.suit] = next_suit_code++;
        }

        // Encode the card: 4 bits for rank, 2 bits for suit
        uint64_t card_encoding = (static_cast<uint64_t>(card.rank) << 2) | suits_reencoding[card.suit];

        // Place the card encoding in the correct position within the result
        result |= (card_encoding << shift);

        // Move the shift for the next card's encoding
        shift += 6;  // Hand cards occupy the first 12 bits (2 cards, 6 bits each)
    }

    // Explicitly set shift to 12 + 4, in case the number of cards on hand was not 2
    shift = 12 + 4;

    // Encode the table (remaining bits after the hand, starting at the 12th bit)
    for (const Card &card : table_cards) {
        // Re-encode the suit if it hasn't been encountered yet
        if (suits_reencoding[card.suit] == -1) {
            suits_reencoding[card.suit] = next_suit_code++;
        }

        // Encode the card: 4 bits for rank, 2 bits for suit
        uint64_t card_encoding = (static_cast<uint64_t>(card.rank) << 2) | suits_reencoding[card.suit];

        // Place the card encoding in the correct position within the result
        result |= (card_encoding << shift);

        // Move the shift for the next card's encoding
        shift += 6;  // Each table card also takes up 6 bits
    }

    return result;
}

/**
 * Just a debugging method for inspecting cache keys
 */
void CheatSheet::decode_and_print_cards(uint64_t encoded_value) {
    const int hand_size = 2;  // Hand size is fixed at 2
    const int total_bits = 64; // We are using a 64-bit integer to encode the cards
    const int bits_per_card = 6; // Each card is represented by 6 bits

    int num_player_bits = 4;
    int num_players = encoded_value & 0xF;
    std::cout << "Number of players: " << num_players << std::endl;

    // Calculate the number of cards encoded in the binary value
    int total_cards = 0;
    for (int i = num_player_bits; i < total_bits; i += bits_per_card) {
        if ((encoded_value >> i) & 0x3F) {
            total_cards++;
        }
    }

    int table_size = total_cards - hand_size;

    std::vector<Card> hand_cards;
    std::vector<Card> table_cards;

    hand_cards.reserve(hand_size);
    table_cards.reserve(table_size);

    for (int i = 0; i < total_cards; ++i) {
        // Extract the 6 bits corresponding to the current card
        uint64_t card_encoding = (encoded_value >> ((i * bits_per_card)+num_player_bits)) & 0x3F; // 0x3F = 0b111111 to mask 6 bits

        // Decode rank and suit
        int rank = (card_encoding >> 2) & 0xF; // Top 4 bits are the rank (0-12)
        int suit = card_encoding & 0x3;       // Bottom 2 bits are the suit (0-3)

        // Create a Card object with the decoded rank and suit
        Card decoded_card(rank, suit);

        // Separate cards into hand and table based on the index
        if (i < hand_size) {
            hand_cards.emplace_back(decoded_card);
        } else {
            table_cards.emplace_back(decoded_card);
        }
    }

    // Print the hand cards
    std::cout << "Hand: " << CardCollection(hand_cards).str() << std::endl;

    // Print the table cards
    std::cout << "Table: " << CardCollection(table_cards).str() << std::endl;

    std::cout << "Total cards: " << total_cards << std::endl;
}

float CheatSheet::get_winning_probability(CardCollection &hand, CardCollection &table, int num_players, int num_simulations)
{
    return find_or_simulate(hand, table, num_players, num_simulations).first;
}

float CheatSheet::get_winning_probability(CardCollection &hand, CardCollection &table, int num_players)
{
    return get_winning_probability(hand, table, num_players, 10000);
}

std::vector<float> CheatSheet::get_all_winning_probabilities(CardCollection &table, int num_players, int num_simulations)
{
    std::vector<float> winning_probabilities(Hand::COMBINATIONS.size(), 0.0);
    for (int i = 0; i < Hand::COMBINATIONS.size(); ++i)
    {
        winning_probabilities[i] = get_winning_probability(Hand::COMBINATIONS[i], table, num_players, num_simulations);
    }
    return winning_probabilities;
}

std::vector<float> CheatSheet::get_all_winning_probabilities(CardCollection &table, int num_players)
{
    return get_all_winning_probabilities(table, num_players, 10000);
}

std::pair<float, int> CheatSheet::find_or_simulate(CardCollection &hand, CardCollection &table, int num_players, int num_simulations)
{
    if (!cache_loaded)
    {
        std::cout << "Cache is not loaded, loading cache" << std::endl;
        load_cache();
        cache_loaded = true;
    }
    uint64_t key = convert_cards_to_equiv_str(hand, table, num_players);
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
