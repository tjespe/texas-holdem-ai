#pragma once
#include <array>
#include <vector>
#include <string>

class HandRank
{
public:
    static const int ROYAL_FLUSH = 9;
    static const int STRAIGHT_FLUSH = 8;
    static const int FOUR_OF_A_KIND = 7;
    static const int FULL_HOUSE = 6;
    static const int FLUSH = 5;
    static const int STRAIGHT = 4;
    static const int THREE_OF_A_KIND = 3;
    static const int TWO_PAIR = 2;
    static const int ONE_PAIR = 1;
    static const int HIGH_CARD = 0;

    int get_rank() const;
    std::array<int, 5> get_tiebreakers() const;
    bool operator<(const HandRank &other) const;
    bool operator==(const HandRank &other) const;
    bool operator>(const HandRank &other) const;

    int beats(const HandRank &other) const;

    HandRank(int rank, const std::array<int, 5> tiebreakers);
    HandRank(int rank, const std::vector<int> tiebreakers);

    std::string get_rank_name() const;
    std::string str() const;

private:
    int rank;
    std::array<int, 5> tiebreakers;
};