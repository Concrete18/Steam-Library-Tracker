import pytest

# classes
from classes.game_skipper import GameSkipper


class TestSkipGame:
    """
    Tests `skip_game` function.
    """

    name_ignore_list = ["Half-Life 2: Lost Coast"]
    app_id_ignore_list = [12345, 123458]
    game_skipper = GameSkipper(name_ignore_list, app_id_ignore_list)

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
        assert self.game_skipper.skip_game(game_name="Game with Online Beta") is True
        assert self.game_skipper.skip_game(game_name="Squad - Public Testing") is True
        assert self.game_skipper.skip_game(game_name="Half-Life 2: Lost Coast") is True
        assert self.game_skipper.skip_game(game_name="half-life 2: lost coast") is True

    def test_skip_media(self):
        """
        Tests for True returns.
        """
        assert self.game_skipper.skip_game(game_name="Spotify") is True
        assert self.game_skipper.skip_game(game_name="youtube") is True

    def test_dont_skip(self):
        """
        Tests for False returns.
        """
        self.game_skipper.name_ignore_list = ["Half-Life 2: Lost Coast"]
        # app_id return false
        assert self.game_skipper.skip_game(app_id=345643) is False
        # name return false
        assert self.game_skipper.skip_game(game_name="This is a great game") is False

    def test_empty(self):
        """
        Empty args return False.
        """
        with pytest.raises(ValueError):
            self.game_skipper.skip_game()


if __name__ == "__main__":
    pytest.main([__file__])
