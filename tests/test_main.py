import pytest

# classes
from main import Tracker
from classes.game_info import Game


class TestAppIdsToNames:
    """
    Tests `app_ids_to_names` function.
    """

    trackerObj = Tracker(save=False)

    def test_success(self, mocker):
        """
        Tests average uses.
        """
        mocker.patch("easierexcel.Sheet.get_cell", return_value="Test")

        app_ids = [12345, 456789]
        names = ["Test", "Test"]
        result = self.trackerObj.app_ids_to_names(app_ids)
        assert result == names


class TestGetGameColumnDict:
    """
    Tests `get_game_column_dict` function.
    """

    trackerObj = Tracker(save=False)

    def test_success(self):
        empty_game = Game()
        column_dict = self.trackerObj.get_game_column_dict(empty_game)
        assert column_dict == {
            "Developers": "-",
            "Publishers": "-",
            "Steam Review Percent": "-",
            "Steam Review Total": "-",
            "Price": "-",
            "Discount": "-",
            "Player Count": "-",
            "Genre": "-",
            "User Tags": "-",
            "Early Access": "No",
            "Time To Beat in Hours": "-",
            "Store Link": "-",
            "Release Year": "-",
        }


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
            {"play_status": None, "minutes": None, "ans": ""},
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
