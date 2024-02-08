from unittest.mock import patch, call
import unittest

# classes
from main import Tracker
from classes.utils import get_steam_key_and_id


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
        for date, answer in date_tests.items():
            with self.subTest(date=date):
                year = self.t.get_year(date)
                self.assertEqual(year, answer, "The year was not correctly found")

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
                ttb = self.t.get_time_to_beat(name)
                self.assertIsInstance(ttb, float, "The time to beat is not a float")

    def test_not_found(self):
        result = self.t.get_time_to_beat("6574654 Not a Real Game 564654")
        self.assertEqual(result, "-", "No time to beat should be found")


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
            store_link = self.t.get_store_link(app_id)
            self.assertEqual(store_link, answer, "The store link does mot match")
            # tests that the url exists
            response = self.t.request_url(store_link)
            self.assertTrue(response, "The link does not go to a real page")

    def test_invalid_link(self):
        """
        Test for broken link that redirects due to the app ID not being found
        """
        fake_app_id = "6546546545465484213211545730"
        invalid_url = f"https://store.steampowered.com/app/{fake_app_id}/"
        response = self.t.request_url(invalid_url)
        self.assertNotIn(
            fake_app_id,
            response.url,
            "The fake app ID should not be in the url",
        )


class GetPriceInfo(unittest.TestCase):
    """
    Tests the get_price_info function to be sure the values are acquired correctly.
    """

    def setUp(self):
        self.t = Tracker(save=False)

    def test_normal_data(self):
        game_info = {
            "price_overview": {
                "final_formatted": "19.99$",
                "discount_percent": 0.50,
            }
        }
        price, discount, on_sale = self.t.get_price_info(game_info)
        self.assertEqual(price, 19.99)
        self.assertEqual(discount, 0.5)
        self.assertEqual(on_sale, True)

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
        price, _, _ = self.t.get_price_info(game_info)
        self.assertIsNone(price, "Price should be None if it is not in US currency")

    def test_invalid_data(self):
        """
        Should return all None if the game_info dict is not correct.
        """
        game_info = {}
        price, discount, on_sale = self.t.get_price_info(game_info)
        self.assertIsNone(price)
        self.assertIsNone(discount)
        self.assertIsNone(on_sale)

        game_info = {"price_overview": {}}
        price, discount, on_sale = self.t.get_price_info(game_info)
        self.assertIsNone(price)
        self.assertIsNone(discount)
        self.assertIsNone(on_sale)


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
        ]
        dict = self.t.get_game_info(1145360)
        for key in keys:
            self.assertIn(key, dict.keys(), f"{key} should exist")

    def test_float(self):
        """
        Tests `get_game_info` function for percents.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(
            game_info["Steam Review Percent"],
            float,
            "Steam review percent should be a float",
        )
        self.assertIsInstance(
            game_info["discount"],
            float,
            "Discount percent should be a float",
        )
        self.assertIsInstance(
            game_info["price"],
            float,
            "Price should be a float",
        )

    def test_int(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(
            game_info["Steam Review Total"],
            int,
            "Steam Review Total should be an int",
        )

    def test_string(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(
            game_info["Developers"],
            str,
            "Developers should be a string",
        )
        self.assertIsInstance(
            game_info["Publishers"],
            str,
            "Publishers should be a string",
        )
        self.assertIsInstance(
            game_info["Genre"],
            str,
            "Genre should be a string",
        )
        self.assertIsInstance(
            game_info["drm_notice"],
            str,
            "drm_notice should be a string",
        )
        self.assertIsInstance(
            game_info["categories"],
            str,
            "categories should be a string",
        )
        self.assertIsInstance(
            game_info["Release Year"],
            str,
            "Release year should be a string",
        )

    def test_other_types(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.t.get_game_info(app_id=752590)
        self.assertIsInstance(game_info, dict)
        self.assertIn(
            game_info["Early Access"],
            ["Yes", "No"],
            "Early Access key value should be Yes or No",
        )
        self.assertIn(
            game_info["on_sale"],
            [True, False],
            "on_sale key value should be True or False",
        )

    def test_check_for_default(self):
        """
        Tests for default value when invalid game is given.
        """
        default_dict = {
            self.t.dev_col: "-",
            self.t.pub_col: "-",
            self.t.genre_col: "-",
            self.t.ea_col: "No",
            self.t.steam_rev_per_col: "No Reviews",
            self.t.steam_rev_total_col: "No Reviews",
            self.t.user_tags_col: "No Tags",
            self.t.release_col: "No Year",
            "game_name": "-",
            "price": "-",
            "discount": 0.0,
            "on_sale": False,
            "drm_notice": "-",
            "categories": "-",
        }
        self.assertEqual(self.t.get_game_info(None), default_dict)

    def test_not_empty_string(self):
        """
        Tests to be sure the get_game_info function has no empty string values.
        """
        game_info = self.t.get_game_info(app_id=730)
        for value in game_info.values():
            self.assertNotEqual(value, "", "No values should be blank")


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
        username = self.t.get_profile_username(no_slash)
        self.assertEqual(username, gabe_username, f"Should return {gabe_username}")
        # ends with /
        with_slash = "http://steamcommunity.com/id/gabelogannewell/"
        username = self.t.get_profile_username(with_slash)
        self.assertEqual(username, gabe_username, f"Should return {gabe_username}")

    def test_False(self):
        string = "this is not a url"
        username = self.t.get_profile_username(string)
        self.assertIsNone(username, "Should return None")


class GetSteamID(unittest.TestCase):
    """
    Tests `get_steam_id` function.
    """

    steam_key, _ = get_steam_key_and_id()

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_steam_id(self):
        gabe_steam_id = 76561197960287930
        steam_id = self.t.get_steam_id("gabelogannewell", self.steam_key)
        self.assertEqual(steam_id, gabe_steam_id, f"steam_id should be {gabe_steam_id}")

    def test_False(self):
        steam_id = self.t.get_steam_id("", self.steam_key)
        self.assertIsNone(steam_id, "steam_id should be None")


class GetSteamUsername(unittest.TestCase):
    """
    Tests `get_steam_username` function.
    """

    steam_key, _ = get_steam_key_and_id()

    def setUp(self):
        self.t = Tracker(save=False)

    def test_get_steam_username(self):
        steam_id = 76561197960287930
        username = self.t.get_steam_username(steam_id, self.steam_key)
        self.assertIsInstance(
            username,
            str,
            "Steam username should be a str",
        )

    def test_False(self):
        username = self.t.get_steam_username(123, self.steam_key)
        self.assertEqual(username, "Unknown", "username should be Unknown")


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


@patch("builtins.print")
class ShowErrors(unittest.TestCase):
    def setUp(self):
        self.t = Tracker(save=False)

    def test_show_errors(self, mock_print):
        """
        Tests to be sure errors are printed properly.
        """
        self.t.errors = ["This failed"]

        self.t.show_errors()

        # import sys
        # sys.stdout.write(str(mock_print.call_args) + "\n")
        # sys.stdout.write(str(mock_print.call_args_list) + "\n")

        expected_calls = [
            call(f"\n1 Errors Occurred:"),
            call("This failed"),
        ]

        mock_print.assert_has_calls(expected_calls, any_order=False)


if __name__ == "__main__":
    unittest.main()
