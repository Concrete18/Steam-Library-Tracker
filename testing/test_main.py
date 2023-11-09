import unittest, json

# classes
from main import Tracker


class GetYear(unittest.TestCase):
    """
    Tests `get_year` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_valid(self):
        date_tests = {
            "Sep 14, 2016": "2016",
            "25 Apr, 1991": "1991",
            "16 Nov, 2009": "2009",
            "Mai 25, 1991": "1991",
            "Apr , 2015": "2015",
        }
        for date, year in date_tests.items():
            with self.subTest(date=date):
                result = self.t.get_year(date)
                self.assertEqual(result, year)

    def test_invalid(self):
        result = self.t.get_year("this is not a date")
        self.assertEqual(result, "Invalid Date", f"{result} should not be a year")


class GetTimeToBeat(unittest.TestCase):
    """
    Tests `get_time_to_beat` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_time_to_beat(self):
        time_to_beat_tests = [
            "Dishonored 2",
            "Deep Rock Galactic",
            "Inscryption",
        ]
        for name in time_to_beat_tests:
            with self.subTest(name=name):
                result = self.t.get_time_to_beat(name)
                self.assertIsInstance(result, float)
        result = self.t.get_time_to_beat("Not a Real Game")
        self.assertEqual(result, "NF - Error")


class GetStoreLink(unittest.TestCase):
    """
    Tests `get_store_link` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_store_link(self):
        store_link_tests = {
            "752590": "https://store.steampowered.com/app/752590/",
            "629730": "https://store.steampowered.com/app/629730/",
        }
        for app_id, answer in store_link_tests.items():
            self.assertEqual(self.t.get_store_link(app_id), answer)
            # tests that the url exists
            response = self.t.request_url(answer)
            self.assertIn(app_id, response.url)
            self.assertTrue(response)
        # test for broken link that redirects due to app id not being found
        invalid_url = "https://store.steampowered.com/app/6546546545465484213211545730/"
        response = self.t.request_url(invalid_url)
        self.assertNotIn("6546546545465484213211545730", response.url)


class SteamReview(unittest.TestCase):
    """
    Tests `get_steam_review`. Due to changing reviews, it only tests for aquiring
    floats for percent and integers for total.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_steam_review(self):
        steam_review_tests = [
            752590,
            1161580,
            230410,
        ]
        for app_id in steam_review_tests:
            percent, total = self.t.get_steam_review(app_id=app_id)
            self.assertIsInstance(percent, float)
            self.assertIsInstance(total, int)


class GetGameInfo(unittest.TestCase):
    """
    Tests `get_game_info` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_has_keys(self):
        """
        Checks for keys in the `get_game_info` result dict.
        """
        keys = [
            self.t.dev_col,
            self.t.pub_col,
            self.t.genre_col,
            self.t.ea_col,
            self.t.steam_rev_per_col,
            self.t.steam_rev_total_col,
            self.t.user_tags_col,
            self.t.release_col,
            "price",
            "discount",
            "on_sale",
            "drm_notice",
            "categories",
            "ext_user_account_notice",
        ]
        dict = self.t.get_game_info(1145360)
        for key in keys:
            self.assertIn(key, dict.keys())

    def test_float(self):
        """
        Tests `get_game_info` function for percents.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(game_info["Steam Review Percent"], float)
        self.assertIsInstance(game_info["discount"], float)
        self.assertIsInstance(game_info["price"], float)

    def test_int(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(game_info["Steam Review Total"], int)

    def test_string(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(game_info["Developers"], str)
        self.assertIsInstance(game_info["Publishers"], str)
        self.assertIsInstance(game_info["Genre"], str)
        self.assertIsInstance(game_info["drm_notice"], str)
        self.assertIsInstance(game_info["categories"], str)
        self.assertIsInstance(game_info["Release Year"], str)
        self.assertIsInstance(game_info["ext_user_account_notice"], str)

    def test_other_types(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(game_info, dict)
        self.assertIn(game_info["Early Access"], ["Yes", "No"])
        self.assertIn(game_info["on_sale"], [True, False])

    def test_check_for_default(self):
        """
        Tests for default value when invalid game is given.
        """
        default_dict = {
            self.t.dev_col: "ND - Error",
            self.t.pub_col: "ND - Error",
            self.t.genre_col: "ND - Error",
            self.t.ea_col: "No",
            self.t.steam_rev_per_col: "No Reviews",
            self.t.steam_rev_total_col: "No Reviews",
            self.t.user_tags_col: "No Tags",
            self.t.release_col: "No Year",
            "game_name": "ND - Error",
            "price": "ND - Error",
            "discount": 0.0,
            "on_sale": False,
            "drm_notice": "ND - Error",
            "categories": "ND - Error",
            "ext_user_account_notice": "ND - Error",
        }
        self.assertEqual(self.t.get_game_info(None), default_dict)

    def test_not_empty_string(self):
        """
        Tests to be sure the get_game_info function has no empty string values.
        """
        game_info = self.t.get_game_info(app_id=730)
        for entry in game_info.values():
            self.assertFalse(entry == "")


class GetProfileUsername(unittest.TestCase):
    """
    Tests `get_profile_username` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_profile_username(self):
        gabe_username = "gabelogannewell"
        # ends with no /
        no_slash = "http://steamcommunity.com/id/gabelogannewell"
        result = self.t.get_profile_username(no_slash)
        self.assertEqual(result, gabe_username)
        # ends with /
        with_slash = "http://steamcommunity.com/id/gabelogannewell/"
        result = self.t.get_profile_username(with_slash)
        self.assertEqual(result, gabe_username)

    def test_False(self):
        string = "this is not a url"
        result = self.t.get_profile_username(string)
        self.assertFalse(result)


class GetSteamID(unittest.TestCase):
    """
    Tests `get_steam_id` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)
        with open("configs\config.json") as file:
            data = json.load(file)
        self.t.steam_key = data["settings"]["steam_api_key"]

    def test_get_steam_id(self):
        gabe_steam_id = 76561197960287930
        result = self.t.get_steam_id("gabelogannewell")
        self.assertEqual(result, gabe_steam_id)

    def test_False(self):
        result = self.t.get_steam_id(".")
        self.assertFalse(result)


class ValidateSteamApiKey(unittest.TestCase):
    """
    Tests `validate_steam_key` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_True(self):
        test_api_key = "15D4C014D419C0642B1E707BED41G7D4"
        result = self.t.validate_steam_key(test_api_key)
        self.assertTrue(result)

    def test_False(self):
        test_api_key = "15D4C014D419C0642B7D4"
        result = self.t.validate_steam_key(test_api_key)
        self.assertFalse(result)


class ValidateSteamID(unittest.TestCase):
    """
    Tests `validate_steam_id` function.
    Steam ID's must be allnumbers and 17 characters long.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_True(self):
        steam_ids = [
            76561197960287930,
            "76561197960287930",
        ]
        for id in steam_ids:
            with self.subTest(msg=type(id), id=id):
                result = self.t.validate_steam_id(id)
                self.assertTrue(result)

    def test_False(self):
        steam_ids = [
            765611028793,
            "asjkdhadsjdhjssaj",
        ]
        for id in steam_ids:
            with self.subTest(msg=type(id), id=id):
                result = self.t.validate_steam_id(id)
                self.assertFalse(result)


class SkipGame(unittest.TestCase):
    """
    Tests `skip_game` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_skip_game(self):
        """
        Tests for True returns.
        """
        self.t.name_ignore_list = ["Half-Life 2: Lost Coast"]
        self.t.app_id_ignore_list = [12345, 123458]
        # app_id return true
        self.assertTrue(
            self.t.skip_game(app_id="12345"), "app_id: 12345 should not be skipped"
        )
        self.assertTrue(
            self.t.skip_game(app_id=12345), "app_id: 12345 should not be skipped"
        )
        # name return true
        self.assertTrue(
            self.t.skip_game(game_name="Game Beta"), "Game Beta should not be skipped"
        )
        self.assertTrue(
            self.t.skip_game(game_name="Squad - Public Testing"),
            "Squad - Public Testing should not be skipped",
        )
        self.assertTrue(
            self.t.skip_game(game_name="Half-Life 2: Lost Coast"),
            "Half-Life 2: Lost Coast should not be skipped",
        )
        self.assertTrue(
            self.t.skip_game(game_name="half-life 2: lost coast"),
            "half-life 2: lost coast should not be skipped",
        )

    def test_skip_media(self):
        """
        Tests for True returns.
        """
        self.assertTrue(
            self.t.skip_game(game_name="Spotify"), "Spotify should be skipped"
        )
        self.assertTrue(
            self.t.skip_game(game_name="youtube"), "Youtube should be skipped"
        )

    def test_dont_skip(self):
        """
        Tests for False returns.
        """
        self.t.name_ignore_list = ["Half-Life 2: Lost Coast"]
        # app_id return false
        self.assertFalse(self.t.skip_game(app_id=345643))
        # name return false
        self.assertFalse(self.t.skip_game(game_name="This is a great game"))

    def test_empty(self):
        """
        Empty args return False.
        """
        with self.assertRaises(ValueError):
            self.t.skip_game()


class PlayStatus(unittest.TestCase):
    """
    Tests `play_status` function.
    """

    def setUp(self):
        self.t = Tracker(save=False)

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
            self.assertEqual(self.t.decide_play_status(play_status, minutes), awnser)

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
            self.assertEqual(
                self.t.decide_play_status(a["play_status"], a["minutes"]), a["ans"]
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
            result = self.t.decide_play_status(test["play_status"], test["minutes"])
            self.assertEqual(result, test["ans"])

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
            self.assertEqual(
                self.t.decide_play_status(a["play_status"], a["minutes"]), a["ans"]
            )

    def test_must_play(self):
        """
        Tests running on new games.
        """
        tests = [
            {"play_status": None, "minutes": 0, "ans": "Unplayed"},
            {"play_status": None, "minutes": 30, "ans": "Played"},
        ]
        for test in tests:
            result = self.t.decide_play_status(test["play_status"], test["minutes"])
            self.assertEqual(result, test["ans"])

    def test_error(self):
        """
        Tests for invalid values given causing nothing to be changed.
        """
        tests = [
            {"play_status": None, "minutes": "Test", "ans": ""},
            {"play_status": "Unplayed", "minutes": "Test", "ans": "Unplayed"},
        ]
        for test in tests:
            result = self.t.decide_play_status(test["play_status"], test["minutes"])
            self.assertEqual(result, test["ans"])


if __name__ == "__main__":
    unittest.main()
