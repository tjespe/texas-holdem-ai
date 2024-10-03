from datetime import datetime
import numpy as np
from PlayerABC import Player
from State import State
from hidden_state_model.observer import Observer
from hidden_state_model.helpers import get_observer_with_all_data
from cpp_poker.cpp_poker import Oracle

time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
persistent_observer = Observer(
    f"hidden_state_model/data/humanmocker-{time_str}.parquet"
)


class HumanMocker(Player):
    def __init__(self, mock: str, rel_weight_player=2):
        super().__init__()
        self.name = f"Mr. {mock}"
        self.mock = mock
        self.rel_weight_player = rel_weight_player

        # Keep predictor separate from observer, because we don't want our predictor to
        # be updated with new data based on what this player does
        self.predictor = get_observer_with_all_data().predictor

        # Initialize an empty observer to use for processing states
        self.observer = Observer()

        self.opponent_names = []

    def get_to_know_each_other(self, players: list[Player]):
        self.opponent_names = [p.name for p in players if p is not self]

    def _play(self, state: State) -> int:
        state_row = self.observer.get_processed_df_row(state.id)
        actions, distrib = self.predictor.predict_for_row(
            "action", state_row, self.mock, self.rel_weight_player, probabilities=True
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
                self.predictor.predict_for_row(
                    "raise",
                    state_row,
                    self.mock,
                    relative_weight_player=self.rel_weight_player,
                )
            )
            print(f"Got amount: {amount} from model")
            # Ensure higher than call_amount
            amount = max(call_amount, amount)
            # If amount is higher than call_amount, ensure it is at least a big blind higher
            if amount > call_amount:
                amount = max(min_raise, amount)
            # Ensure lower than max_allowed
            amount = min(max_allowed, amount)
            print(
                f"Amount adjusted for [call_amount, min_raise, max_allowed]: [{call_amount}, {min_raise}, {max_allowed}] range: {amount}"
            )
            return amount
        else:
            raise ValueError(f"Unknown action: {action}")

    def play(self, state: State) -> int:
        self.observer.observe_state(
            state,
            self.mock,
            HumanMocker.__name__,
            self.opponent_names,
            self.hand,
        )
        amount = self._play(state)
        self.observer.retrofill_action(state, amount)
        persistent_observer.observe_action(
            state,
            self.name,
            HumanMocker.__name__,
            amount,
            self.opponent_names,
            self.hand,
        )
        return amount
