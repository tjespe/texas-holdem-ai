from State import State
from StateNode import StateNode
import unittest
from state_management import generate_root_state


class StateNodeTestCase(unittest.TestCase):
    def assertTerminal(self, state_node: StateNode):
        return self.assertEqual(
            state_node.state.is_terminal,
            True,
            "Expected final state to be terminal, but found following state:\n"
            + state_node.state.get_cli_repr()
            + "\n"
            + "All players are done? "
            + str(state_node.state.all_players_are_done)
            + "\n"
            + "Player has played? "
            + str(state_node.state.player_has_played)
            + "\n"
            + "Player is active? "
            + str(state_node.state.player_is_active)
            + "\n"
            + "Child states: "
            + str(state_node.children),
        )

    def test_can_create_state_node(self):
        state_node = StateNode(
            state=generate_root_state(n_players=2), end_stage="preflop", max_depth=0
        )
        self.assertIsInstance(state_node, StateNode)

    def test_can_create_one_level(self):
        state_node = StateNode(
            state=generate_root_state(n_players=2),
            end_stage="river",
            max_depth=1,
            max_successors_at_action_nodes=10,
            max_successors_at_chance_nodes=10,
        )
        self.assertIsInstance(state_node.children[0][1], StateNode)

    def test_can_create_full_tree_from_turn_state(self):
        turn_state = State(
            public_cards=(0, 1, 2, 3),
            player_piles=(100, 100),
            current_player_i=1,
            bet_in_stage=(0, 0),
            bet_in_game=(2, 2),
            player_has_played=(True, False),
            player_is_folded=(False, False),
            first_better_i=0,
            big_blind=2,
        )
        state_node = StateNode(
            state=turn_state,
            end_stage="terminal",
            max_depth=100,
            max_successors_at_action_nodes=10,
            max_successors_at_chance_nodes=10,
        )
        while state_node.children:
            state_node = state_node.children[0][1]
        self.assertTerminal(state_node)

    def test_can_create_full_tree_from_preflop(self):
        state_node = StateNode(
            state=generate_root_state(n_players=2),
            end_stage="terminal",
            max_depth=100,
            max_successors_atactione_nodes=3,
            max_successors_at_chance_nodes=3,
        )
        while state_node.children:
            state_node = state_node.children[0][1]
        self.assertTerminal(state_node)


if __name__ == "__main__":
    unittest.main()
