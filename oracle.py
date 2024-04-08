from typing import Iterable
import unittest

import numpy as np
from Card import Card
from PlayerABC import Player


def check_for_royal_flush(hand: set[Card]):
    """
    Check if a hand has a royal flush.
    Returns a tuple of the form (has_royal_flush, royal_flush), where royal_flush is
    the royal flush if it exists.
    """
    suits = {card.suit for card in hand}
    for suit in suits:
        royal_flush = set()
        for rank in range(Card.get_rank("10"), Card.get_rank("A") + 1):
            if Card(rank, suit) not in hand:
                break
            royal_flush.add(Card(rank, suit))
        else:
            return True, royal_flush
    return False, None


def check_for_straight_flush(hand: set[Card]):
    """
    Check if a hand has a straight flush.
    Returns a tuple of the form (has_straight_flush, straight_flush), where straight_flush
    is the best straight flush if it exists.
    """
    suits = {card.suit for card in hand}
    for suit in suits:
        for rank in range(Card.get_rank("10"), Card.get_rank("2") - 1, -1):
            straight_flush = set()
            for i in range(5):
                if Card(rank + i, suit) not in hand:
                    break
                straight_flush.add(Card(rank + i, suit))
            else:
                return True, straight_flush
        # Special case: A-2-3-4-5
        if Card(Card.get_rank("A"), suit) in hand:
            straight_flush = {Card(Card.get_rank("A"), suit)}
            for i in range(4):
                if Card(Card.get_rank("2") + i, suit) not in hand:
                    break
                straight_flush.add(Card(Card.get_rank("2") + i, suit))
            else:
                return True, straight_flush
    return False, None


def check_for_four_of_a_kind(hand: set[Card]):
    """
    Check if a hand has four of a kind.
    Returns a tuple of the form (has_four_of_a_kind, quadruplet), where
    quadruplet is the four of a kind.
    """
    for rank in range(Card.get_rank("A"), Card.get_rank("2") - 1, -1):
        quadruplet = set()
        for suit in range(4):
            if Card(rank, suit) not in hand:
                break
            quadruplet.add(Card(rank, suit))
        else:
            return True, quadruplet
    return False, None


def check_for_full_house(hand: set[Card]):
    """
    Check if a hand has a full house.
    Returns a tuple of the form (has_full_house, full_house), where
    full_house is the full house.
    """
    has_three, triple = check_for_three_of_a_kind(hand)
    if not has_three:
        return False, None
    has_pair, pair = check_for_one_pair(hand)
    if not has_pair:
        return False, None
    return True, triple | pair


def check_for_flush(hand: set[Card]):
    """
    Check if a hand has a flush.
    Returns a tuple of the form (has_flush, flush), where flush is the flush (if
    there are more than 5 cards, the best 5 are returned)
    """
    for suit in range(4):
        flush = {card for card in hand if card.suit == suit}
        if len(flush) >= 5:
            return True, set(sorted(list(flush), reverse=True)[:5])
    return False, None


def check_for_straight(hand: set[Card]):
    """
    Check if a hand has a straight.
    Returns a tuple of the form (has_straight, straight), where straight is the best
    straight.
    """
    cards_per_rank = [[] for _ in range(13)]
    for card in hand:
        cards_per_rank[card.rank].append(card)
    for rank in range(Card.get_rank("10"), Card.get_rank("2") - 1, -1):
        straight = set()
        for i in range(5):
            cards_with_rank = cards_per_rank[rank + i]
            if not cards_with_rank:
                break
            straight.add(cards_with_rank[0])
        else:
            return True, straight
    # Special case: A-2-3-4-5
    if aces := cards_per_rank[Card.get_rank("A")]:
        straight = {aces[0]}
        for i in range(4):
            cards_with_rank = cards_per_rank[Card.get_rank("2") + i]
            if not cards_with_rank:
                break
            straight.add(cards_with_rank[0])
        else:
            return True, straight
    return False, None


def check_for_three_of_a_kind(hand: set[Card]):
    """
    Check if a hand has three of a kind.
    Returns a tuple of the form (has_three_of_a_kind, triplet), where
    triplet is the set of the relevant three cards.
    """
    for rank in range(Card.get_rank("A"), Card.get_rank("2") - 1, -1):
        triplet = set()
        for suit in range(4):
            if Card(rank, suit) in hand:
                triplet.add(Card(rank, suit))
        if len(triplet) == 3:
            return True, triplet
    return False, None


def check_for_two_pair(hand: set[Card]):
    """
    Check if a hand has two pairs.
    Returns a tuple of the form (has_two_pair, two_pairs), where two_pairs is the set of
    cards that make up the two pairs.
    """
    count_per_rank = [0] * 13
    for card in hand:
        count_per_rank[card.rank] += 1
    pair_ranks = {i for i, count in enumerate(count_per_rank) if count >= 2}
    if len(pair_ranks) >= 2:
        two_pairs = set()
        for rank in list(sorted(pair_ranks, reverse=True))[:2]:
            for suit in range(4):
                if Card(rank, suit) in hand:
                    two_pairs.add(Card(rank, suit))
        return True, two_pairs
    return False, None


def check_for_one_pair(hand: set[Card]):
    """
    Check if a hand has one pair.
    Returns a tuple of the form (has_one_pair, pair), where pair is the set of cards that
    make up the pair.
    """
    for rank in range(Card.get_rank("A"), Card.get_rank("2") - 1, -1):
        pair = set()
        for suit in range(4):
            if Card(rank, suit) in hand:
                pair.add(Card(rank, suit))
        if len(pair) == 2:
            return True, pair
    return False, None


def get_n_high_cards(hand: set[Card], n: int):
    """
    Get the n highest cards in a hand in sorted order.
    """
    return list(sorted(list(hand), reverse=True)[:n])


def get_n_high_ranks(hand: set[Card], n: int):
    """
    Get the n highest ranks in a hand.
    """
    return [c.rank for c in get_n_high_cards(hand, n)]


def rank_hand(cards: set[Card]):
    """
    Rank a hand of cards.
    Returns a list of ranks, where the first rank is the primary rank, the second rank is
    used as a tiebreaker, and so on.
    """
    has_royal_flush, royal_flush = check_for_royal_flush(cards)
    if has_royal_flush:
        return [9]  # All royal flushes are equal
    has_straight_flush, straight_flush = check_for_straight_flush(cards)
    if has_straight_flush:
        return [8, max(straight_flush, key=lambda card: card.rank).rank]
    has_four_of_a_kind, quadruplet = check_for_four_of_a_kind(cards)
    if has_four_of_a_kind:
        quad_rank = next(iter(quadruplet)).rank
        # Four-of-a-kinds are ranked by the rank of the quadruplet, then the rank of the
        # highest card in the hand if there is a tie
        return [7, quad_rank] + get_n_high_ranks(cards - quadruplet, 1)
    has_full_house, full_house = check_for_full_house(cards)
    if has_full_house:
        _, triplet = check_for_three_of_a_kind(full_house)
        pair = full_house - triplet
        # Full houses are ranked by the rank of the triplet, then the rank of the pair
        return [6, next(iter(triplet)).rank, next(iter(pair)).rank]
    has_flush, flush = check_for_flush(cards)
    if has_flush:
        return [5] + get_n_high_ranks(flush, 5)
    has_straight, straight = check_for_straight(cards)
    if has_straight:
        return [4, max(straight, key=lambda card: card.rank).rank]
    has_three_of_a_kind, triplet = check_for_three_of_a_kind(cards)
    if has_three_of_a_kind:
        return [3, next(iter(triplet)).rank] + get_n_high_ranks(cards - triplet, 2)
    has_two_pair, two_pair_cards = check_for_two_pair(cards)
    if has_two_pair:
        pair_ranks = list(
            sorted(
                set(c.rank for c in two_pair_cards),
                reverse=True,
            )
        )
        return [2] + pair_ranks + get_n_high_ranks(cards - two_pair_cards, 1)
    has_one_pair, pair = check_for_one_pair(cards)
    if has_one_pair:
        return [1, next(iter(pair)).rank] + get_n_high_ranks(cards - pair, 3)
    return [0] + get_n_high_ranks(cards, 5)


def compare_hands(hand1: set[Card], hand2: set[Card]):
    """
    Compare two hands of cards.
    Returns 1 if hand1 is better, 0 if they are equal, and -1 if hand2 is better.
    """
    rank1 = rank_hand(hand1)
    rank2 = rank_hand(hand2)
    for r1, r2 in zip(rank1, rank2):
        if r1 > r2:
            return 1
        if r1 < r2:
            return -1
    return 0


def find_winner(
    table: Iterable[int],
    players: list[Player],
    player_is_active: tuple[bool],
) -> set[Player]:
    """
    Find the winner among a list of players.
    Returns a set of winners (can be more than one if there is a tie).
    """
    winners = set()
    best_hand = None
    for i, player in enumerate(players):
        cards = set(Card.from_index(c) for c in player.hand).union(
            set(Card.from_index(c) for c in table)
        )
        if not player_is_active[i]:
            # Player is bust or folded
            continue
        if best_hand is None:
            best_hand = cards
            winners.add(player)
        else:
            comparison = compare_hands(cards, best_hand)
            if comparison == 1:
                best_hand = cards
                winners = {player}
            elif comparison == 0:
                winners.add(player)
    return winners


def get_max_bet_allowed(
    player_has_played: tuple[bool],
    current_player_i: int,
    current_bets: tuple[int],
    player_piles: tuple[int],
    player_is_active: tuple[bool],
):
    """
    To simplify the game, it is not allowed to bet more than the smallest stack.
    Aditionally, a player who has already played cannot reraise, they can only call or fold.
    """
    max_stack_per_player = np.array(player_piles) + np.array(current_bets)
    min_stack = min(max_stack_per_player[np.array(player_is_active)])
    max_allowed = min_stack - current_bets[current_player_i]
    if player_has_played[current_player_i]:
        call_amount = max(current_bets) - current_bets[current_player_i]
        return min(call_amount, max_allowed)
    return max_allowed
