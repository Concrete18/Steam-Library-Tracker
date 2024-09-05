import pytest

# local imports
from utils.game_skipper import GameSkipper


class TestSkipGame:
    NAME_IGNORE_LIST = ["Half-Life 2: Lost Coast"]
    APP_ID_IGNORE_LIST = [12345, 123458]
    game_skipper = GameSkipper(NAME_IGNORE_LIST, APP_ID_IGNORE_LIST)

    def test_skip_game_with_app_ids(self):
        """
        Tests if game should be skipped by app id.
        """
        assert self.game_skipper.skip_game(app_id="12345") is True
        assert self.game_skipper.skip_game(app_id=12345) is True

    def test_skip_game_with_names(self):
        """
        Tests if game should be skipped by names.
        """
        assert self.game_skipper.skip_game(game_name="Game with Online Beta")
        assert self.game_skipper.skip_game(game_name="Squad - Public Testing")
        assert self.game_skipper.skip_game(game_name="Half-Life 2: Lost Coast")
        assert self.game_skipper.skip_game(game_name="half-life 2: lost coast")

    def test_skip_media(self):
        """
        Tests for True returns.
        """
        assert self.game_skipper.skip_game(game_name="Spotify")
        assert self.game_skipper.skip_game(game_name="youtube")

    def test_dont_skip(self):
        """
        Tests for False returns.
        """
        self.game_skipper.name_ignore_list = ["Half-Life 2: Lost Coast"]
        # app_id return false
        assert not self.game_skipper.skip_game(app_id=345643)
        # name return false
        assert not self.game_skipper.skip_game(game_name="This is a great game")

    def test_empty(self):
        """
        Empty args return False.
        """
        with pytest.raises(ValueError):
            self.game_skipper.skip_game()


if __name__ == "__main__":
    pytest.main([__file__])
