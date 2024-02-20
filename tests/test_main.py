import pytest

# classes
from main import Tracker
from classes.utils import get_steam_api_key_and_id


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
            # tests that the url exists
            assert self.trackerObj.request_url(store_link)

    def test_invalid_link(self):
        """
        Test for broken link that redirects due to the app ID not being found
        """
        fake_app_id = "6546546545465484213211545730"
        invalid_url = f"https://store.steampowered.com/app/{fake_app_id}/"
        response = self.trackerObj.request_url(invalid_url)
        assert fake_app_id not in response.url


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


class TestGetGameInfo:
    """
    Tests `get_game_info` function.
    """

    trackerObj = Tracker(save=False)

    def test_has_keys(self):
        """
        Checks for keys in the `get_game_info` result dict.
        """
        keys = [
            self.trackerObj.dev_col,
            self.trackerObj.pub_col,
            self.trackerObj.genre_col,
            self.trackerObj.ea_col,
            self.trackerObj.steam_rev_per_col,
            self.trackerObj.steam_rev_total_col,
            self.trackerObj.user_tags_col,
            self.trackerObj.release_col,
            "price",
            "discount",
            "on_sale",
            "drm_notice",
            "categories",
        ]
        dict = self.trackerObj.get_game_info(1145360)
        for key in keys:
            assert key in dict.keys()

    def test_float(self):
        """
        Tests `get_game_info` function for percents.
        """
        game_info = self.trackerObj.get_game_info(app_id=752590)
        assert isinstance(game_info["Steam Review Percent"], float)
        assert isinstance(game_info["discount"], float)
        assert isinstance(game_info["price"], float)

    def test_int(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.trackerObj.get_game_info(app_id=752590)
        assert isinstance(game_info["Steam Review Total"], int)

    def test_string(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.trackerObj.get_game_info(app_id=752590)
        assert isinstance(game_info["Developers"], str)
        assert isinstance(game_info["Publishers"], str)
        assert isinstance(game_info["Genre"], str)
        assert isinstance(game_info["drm_notice"], str)
        assert isinstance(game_info["categories"], str)
        assert isinstance(game_info["Release Year"], str)

    def test_other_types(self):
        """
        Tests `get_game_info` function for specific types of results.
        """
        game_info = self.trackerObj.get_game_info(app_id=752590)
        assert isinstance(game_info, dict)
        assert isinstance(game_info["on_sale"], bool)
        assert game_info["Early Access"] in ["Yes", "No"]

    def test_check_for_default(self):
        """
        Tests for default value when invalid game is given.
        """
        default_dict = {
            self.trackerObj.dev_col: "-",
            self.trackerObj.pub_col: "-",
            self.trackerObj.genre_col: "-",
            self.trackerObj.ea_col: "No",
            self.trackerObj.steam_rev_per_col: "-",
            self.trackerObj.steam_rev_total_col: "-",
            self.trackerObj.user_tags_col: "-",
            self.trackerObj.release_col: "-",
            "game_name": "-",
            "price": "-",
            "discount": 0.0,
            "on_sale": False,
            "drm_notice": "-",
            "categories": "-",
        }
        assert self.trackerObj.get_game_info(None) == default_dict

    def test_not_empty_string(self):
        """
        Tests to be sure the get_game_info function has no empty string values.
        """
        game_info = self.trackerObj.get_game_info(app_id=730)
        for value in game_info.values():
            assert value != ""


class TestGetProfileUsername:
    """
    Tests `get_profile_username` function.
    """

    trackerObj = Tracker(save=False)

    def test_get_profile_username(self):
        gabe_username = "gabelogannewell"
        # ends with no /
        no_slash = "http://steamcommunity.com/id/gabelogannewell"
        username = self.trackerObj.get_profile_username(no_slash)
        assert username == gabe_username
        # ends with /
        with_slash = "http://steamcommunity.com/id/gabelogannewell/"
        username = self.trackerObj.get_profile_username(with_slash)
        assert username == gabe_username

    def test_False(self):
        string = "this is not a url"
        username = self.trackerObj.get_profile_username(string)
        assert username is None


class TestGetSteamID:
    """
    Tests `get_steam_id` function.
    """

    steam_key, _ = get_steam_api_key_and_id()

    trackerObj = Tracker(save=False)

    def test_get_steam_id(self):
        gabe_steam_id = 76561197960287930
        steam_id = self.trackerObj.get_steam_id("gabelogannewell", self.steam_key)
        assert steam_id == gabe_steam_id

    def test_False(self):
        steam_id = self.trackerObj.get_steam_id("", self.steam_key)
        assert steam_id is None


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
