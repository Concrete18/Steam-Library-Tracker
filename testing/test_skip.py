import unittest

# classes
from classes.skip import GameSkipper


class SkipGame(unittest.TestCase):
    """
    Tests `skip_game` function.
    """

    def setUp(self):
        self.game_skipper = GameSkipper()

    def test_skip_game(self):
        """
        Tests for True returns.
        """
        self.game_skipper.name_ignore_list = ["Half-Life 2: Lost Coast"]
        self.game_skipper.app_id_ignore_list = [12345, 123458]
        # app_id return true
        self.assertTrue(
            self.game_skipper.skip_game(app_id="12345"),
            "app_id: 12345 should be skipped",
        )
        self.assertTrue(
            self.game_skipper.skip_game(app_id=12345), "app_id: 12345 should be skipped"
        )
        # name return true
        self.assertTrue(
            self.game_skipper.skip_game(game_name="Game with Online Beta"),
            "Game with Online Beta should be skipped",
        )
        self.assertTrue(
            self.game_skipper.skip_game(game_name="Squad - Public Testing"),
            "Squad - Public Testing should be skipped",
        )
        self.assertTrue(
            self.game_skipper.skip_game(game_name="Half-Life 2: Lost Coast"),
            "Half-Life 2: Lost Coast should be skipped",
        )
        self.assertTrue(
            self.game_skipper.skip_game(game_name="half-life 2: lost coast"),
            "half-life 2: lost coast should be skipped",
        )

    def test_skip_media(self):
        """
        Tests for True returns.
        """
        self.assertTrue(
            self.game_skipper.skip_game(game_name="Spotify"),
            "Spotify should be skipped",
        )
        self.assertTrue(
            self.game_skipper.skip_game(game_name="youtube"),
            "Youtube should be skipped",
        )

    def test_dont_skip(self):
        """
        Tests for False returns.
        """
        self.game_skipper.name_ignore_list = ["Half-Life 2: Lost Coast"]
        # app_id return false
        self.assertFalse(self.game_skipper.skip_game(app_id=345643))
        # name return false
        self.assertFalse(self.game_skipper.skip_game(game_name="This is a great game"))

    def test_empty(self):
        """
        Empty args return False.
        """
        with self.assertRaises(ValueError):
            self.game_skipper.skip_game()


if __name__ == "__main__":
    unittest.main()
