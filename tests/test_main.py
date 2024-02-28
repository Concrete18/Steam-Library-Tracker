import pytest

# classes
from main import Tracker


class TestGetTimeToBeat:
    """
    Tests `get_time_to_beat` function.
    """

    trackerObj = Tracker(save=False)

    def test_get_time_to_beat(self):
        time_to_beat_tests = [
            "Dishonored 2",
            "Deep Rock Galactic",
            "Inscryption",
        ]
        for name in time_to_beat_tests:
            ttb = self.trackerObj.get_time_to_beat(name)
            assert isinstance(ttb, float)

    def test_works_on_fancy_sting(self):
        ttb = self.trackerObj.get_time_to_beat("ARMORED CORE™ VI FIRES OF RUBICON™")
        assert isinstance(ttb, float)

    def test_not_found(self):
        result = self.trackerObj.get_time_to_beat("6574654 Not a Real Game 564654")
        assert result == "-"


class TestGetStoreLink:
    """
    Tests `get_store_link` function.
    """

    trackerObj = Tracker(save=False)

    def test_get_store_link(self):
        store_link_tests = {
            "752590": "https://store.steampowered.com/app/752590/",
            "629730": "https://store.steampowered.com/app/629730/",
        }
        for app_id, answer in store_link_tests.items():
            store_link = self.trackerObj.get_store_link(app_id)
            assert store_link == answer


class TestGetPriceInfo:
    """
    Tests the get_price_info function to be sure the values are acquired correctly.
    """

    trackerObj = Tracker(save=False)

    def test_normal_data(self):
        game_info = {
            "price_overview": {
                "final_formatted": "19.99$",
                "discount_percent": 0.50,
            }
        }
        price, discount, on_sale = self.trackerObj.get_price_info(game_info)
        assert price == 19.99
        assert discount == 0.5
        assert on_sale

    def test_wrong_currency(self):
        """
        Confirms that a non US Dollar currency for the price causes the price to return as None.
        """
        game_info = {
            "price_overview": {
                "final_formatted": "19.99€",
                "discount_percent": 0.50,
            }
        }
        price, _, _ = self.trackerObj.get_price_info(game_info)
        assert price is None

    def test_invalid_data(self):
        """
        Should return all None if the game_info dict is not correct.
        """
        game_info = {}
        price, discount, on_sale = self.trackerObj.get_price_info(game_info)
        assert price is None
        assert discount is None
        assert on_sale is None

        game_info = {"price_overview": {}}
        price, discount, on_sale = self.trackerObj.get_price_info(game_info)
        assert price is None
        assert discount is None
        assert on_sale is None


class TestPlayStatus:
    """
    Tests `play_status` function.
    """

    trackerObj = Tracker(save=False)

    def test_base(self):
        """
        Tests average uses.
        """
        tests = [
            {"play_status": "Unplayed", "minutes": 5, "ans": "Unplayed"},
            {"play_status": "Unplayed", "minutes": 30, "ans": "Played"},
            {"play_status": "Unplayed", "minutes": 30, "ans": "Played"},
            {"play_status": "Finished", "minutes": 5, "ans": "Finished"},
        ]
        for test in tests:
            play_status = test["play_status"]
            minutes = test["minutes"]
            awnser = test["ans"]
            assert self.trackerObj.decide_play_status(play_status, minutes) == awnser

    def test_do_nothing(self):
        """
        Tests Instances where nothing should be changed.
        """
        tests = [
            {"play_status": "Waiting", "minutes": 600, "ans": "Waiting"},
            {"play_status": "Quit", "minutes": 600, "ans": "Quit"},
            {"play_status": "Finished", "minutes": 600, "ans": "Finished"},
            {"play_status": "Ignore", "minutes": 600, "ans": "Ignore"},
        ]
        for a in tests:
            assert (
                self.trackerObj.decide_play_status(a["play_status"], a["minutes"])
                == a["ans"]
            )

    def test_play_status(self):
        tests = [
            # must play
            {"play_status": "Must Play", "minutes": 0, "ans": "Must Play"},
            {"play_status": "Must Play", "minutes": 30, "ans": "Played"},
            # new game
            {"play_status": None, "minutes": 0, "ans": "Unplayed"},
            {"play_status": None, "minutes": 30, "ans": "Played"},
            # error
            {"play_status": None, "minutes": "Test", "ans": ""},
            {"play_status": "Unplayed", "minutes": "Test", "ans": "Unplayed"},
        ]
        for test in tests:
            result = self.trackerObj.decide_play_status(
                test["play_status"], test["minutes"]
            )
            assert result == test["ans"]

    def test_must_play(self):
        """
        Tests running on games previously set to "Must Play". This allows
        games to go back to normal status changing once they have been played.
        """
        tests = [
            {"play_status": "Must Play", "minutes": 0, "ans": "Must Play"},
            {"play_status": "Must Play", "minutes": 30, "ans": "Played"},
        ]
        for a in tests:
            result = self.trackerObj.decide_play_status(a["play_status"], a["minutes"])
            assert result == a["ans"]

    def test_must_play(self):
        """
        Tests running on new games.
        """
        tests = [
            {"play_status": None, "minutes": 0, "ans": "Unplayed"},
            {"play_status": None, "minutes": 30, "ans": "Played"},
        ]
        for test in tests:
            result = self.trackerObj.decide_play_status(
                test["play_status"], test["minutes"]
            )
            assert result == test["ans"]

    def test_error(self):
        """
        Tests for invalid values given causing nothing to be changed.
        """
        tests = [
            {"play_status": None, "minutes": "Test", "ans": ""},
            {"play_status": "Unplayed", "minutes": "Test", "ans": "Unplayed"},
        ]
        for test in tests:
            result = self.trackerObj.decide_play_status(
                test["play_status"], test["minutes"]
            )
            assert result == test["ans"]


if __name__ == "__main__":
    pytest.main([__file__])
