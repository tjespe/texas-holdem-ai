import unittest

from hidden_state_model.helpers import get_observer_with_all_data
from hidden_state_model.observer import Observer
from state_management import generate_root_state


class ObserverTestCase(unittest.TestCase):
    def test_can_process_historical_data(self):
        observer = get_observer_with_all_data()
        # df = observer.get_processed_df()
        # assert df.shape[0] > 0

    def test_can_process_in_game_data(self):
        # Test is empty initially
        observer = Observer()
        df = observer.get_processed_df()
        assert df.empty, "Expected df to be empty"

        # Test can add action and get partial df row
        example_state = generate_root_state(n_players=2)
        observer.observe_action(
            example_state,
            player_name="Test",
            player_type="Test",
            amount=0,
            opponent_names=None,
            hand=None,
        )
        df = observer.get_processed_df()
        assert df.shape[0] == 1, "Expected one row"
        assert observer.df["rank"].isna().all(), "Expected rank to be empty in raw df"
        assert df["excess_rank"].isna().all(), "Expected excess rank to be empty"

        # Test rerunning the same action has no effect
        observer.observe_action(
            example_state,
            player_name="Test",
            player_type="Test",
            amount=0,
            opponent_names=None,
            hand=None,
        )
        df = observer.get_processed_df()
        assert df.shape[0] == 1, "Expected one row"
        assert observer.df["rank"].isna().all(), "Expected rank to be empty in raw df"
        assert df["excess_rank"].isna().all(), "Expected excess rank to be empty"

        # Test can retrofill hand stats and get complete df row
        hand = (0, 1)
        observer.retrofill_hand_stats([example_state], hand)
        assert (
            observer.df["rank"].notna().all()
        ), "Expected no nan values for rank in raw df"
        df = observer.get_processed_df()
        assert df.shape[0] == 1, "Expected one row"
        assert (
            df["excess_rank"].notna().all()
        ), "Exepected no nan values for execess rank after retro fill, got df:\n{}\nProcessed objects:{}".format(
            df[["excess_rank"]],
            observer.processor.processed,
        )


if __name__ == "__main__":
    unittest.main()
