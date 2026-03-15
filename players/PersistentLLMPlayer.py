from players.LLMPlayer import LLMPlayer
from db_interface import get_value, set_value

class PersistentLLMPlayer(LLMPlayer):
    title = "Tenacious"

    def __init__(
        self,
        *args,
        name="Ellie",
        **kwargs
    ):
        super().__init__(*args, name=name, **kwargs)

    @property
    def storage_key(self):
        return PersistentLLMPlayer.__name__ + ",".join(self.opponent_names) + "_reflections"

    def get_to_know_each_other(self, players: list["Player"]):
        super().get_to_know_each_other(players)
        if prev_reflections := get_value(self.storage_key):
            self.reflections = prev_reflections
        else:
            print(f"No saved reflections for {self.storage_key}")

    def game_over(self, *args, **kwargs):
        set_value(self.storage_key, self.reflections)

