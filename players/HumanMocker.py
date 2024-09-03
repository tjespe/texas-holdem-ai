import numpy as np
from PlayerABC import Player
from State import State
from hidden_state_model.action_model import fit_and_predict_proba
from hidden_state_model.raise_model import fit_and_predict_raise
from hidden_state_model.helpers import get_observer_with_all_data
from cpp_poker.cpp_poker import Oracle


class HumanMocker(Player):
    def __init__(self, mock: str, rel_weight_player=2):
        super().__init__()
        self.name = f"Mr. {mock}"
        self.mock = mock
        self.rel_weight_player = rel_weight_player
        self.observer = get_observer_with_all_data()

    def _play(self, state: State) -> int:
        self.observer.observe_state(
            state,
            self.mock,
            HumanMocker.__name__,
            None,
            self.hand,
        )
        actions, distrib = fit_and_predict_proba(
            self.observer.get_processed_df(),
            state.id,
            self.mock,
            relative_weight_player=self.rel_weight_player,
        )
        print("Got distribution: ", distrib, "for", actions, "from model")
        # Sample random action from distribution
        action = np.random.choice(actions, p=distrib)
        call_amount = max(state.bet_in_game) - state.bet_in_game[self.index]
        if action == "fold":
            print("Folding")
            return 0
        elif action == "check":
            print("Checking")
            return 0
        elif action == "call":
            print("Calling")
            return call_amount
        elif action == "raise":
            max_allowed = Oracle.get_max_bet_allowed(
                state.player_has_played,
                state.current_player_i,
                state.bet_in_stage,
                state.player_piles,
                state.player_is_active,
            )
            min_raise = call_amount + state.big_blind
            can_raise = call_amount < min_raise < max_allowed
            if not can_raise:
                print(
                    f"Cannot raise. Call amount: {call_amount}, min_raise: {min_raise}, max_allowed: {max_allowed}"
                )
                return call_amount
            amount = int(
                fit_and_predict_raise(
                    self.observer.get_processed_df(),
                    state.id,
                    self.mock,
                    relative_weight_player=self.rel_weight_player,
                )
            )
            print(f"Got amount: {amount} from model")
            # Ensure higher than call_amount
            amount = max(call_amount, amount)
            # Ensure lower than max_allowed
            amount = min(max_allowed, amount)
            print(
                f"Amount adjusted for [call_amount, max_allowed]: [{call_amount}, {max_allowed}] range: {amount}"
            )
            return amount
        else:
            raise ValueError(f"Unknown action: {action}")

    def play(self, state: State) -> int:
        self.observer.observe_state(
            state,
            self.mock,
            HumanMocker.__name__,
            None,
            self.hand,
        )
        amount = self._play(state)
        self.observer.retrofill_action(state, amount)
        return amount
