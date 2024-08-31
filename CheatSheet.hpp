#pragma once

#include <unordered_map>
#include <string>
#include <set>
#include <vector>
#include "CardCollection.hpp"
#include <iostream>

class CheatSheet
{
public:
    static float get_winning_probability(CardCollection &hand, CardCollection &table, int num_players, int num_simulations);
    static float get_winning_probability(CardCollection &hand, CardCollection &table, int num_players);

    /** Returns the winning probabilities for every possible hand given a table */
    static std::vector<float> get_all_winning_probabilities(CardCollection &table, int num_players, int num_simulations);
    static std::vector<float> get_all_winning_probabilities(CardCollection &table, int num_players);

    static void save_cache();

private:
    static inline std::unordered_map<std::string, std::pair<float, int>> cache = {};
    static bool cache_loaded;
    static std::string cache_file_path;


    class Cleaner {
    public:
        Cleaner() {
            std::cout << "CheatSheet::Cleaner() initialized" << std::endl;
        }
        ~Cleaner() {
            std::cout << "CheatSheet::Cleaner() deinitialized" << std::endl;
            CheatSheet::save_cache();
        }
    };

    static Cleaner cleaner;  // Static instance to save cache on program exit

    static void load_cache();
    static std::string convert_cards_to_equiv_str(CardCollection &hand, CardCollection &table);
    static std::pair<float, int> find_or_simulate(CardCollection &hand, CardCollection &table, int num_players, int num_simulations);
    static float get_winning_probability_n_simulations(CardCollection &hand, CardCollection &table, int num_players, int num_simulations);
    static void signal_handler(int signum);
    static void setup_signal_handlers();
};