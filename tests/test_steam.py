import pytest
import requests

# classes
from classes.steam import Steam
from classes.utils import Utils


class TestGetOwnedSteamGames(Utils):

    @pytest.fixture
    def mock_response(self, mocker):
        # Create a mock response object
        mock_response = mocker.Mock()
        # Set the JSON data for the response
        mock_response.json.return_value = {
            "response": {
                "games": [
                    {"name": "Game 1", "appid": 123},
                    {"name": "Game 2", "appid": 456},
                ]
            }
        }
        # Set the status code and whether the request was successful
        mock_response.ok = True
        return mock_response

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self, mock_response, mocker):
        # Mock requests.get and return the mock response
        mocker.patch("requests.get", return_value=mock_response)
        # Call the function you want to test
        result = self.steam.get_owned_steam_games(self.steam_key, self.steam_id)
        # Assert that the function returns the expected result
        assert result == [
            {"name": "Game 1", "appid": 123},
            {"name": "Game 2", "appid": 456},
        ]

    def test_request_error(self, mocker):
        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        result = self.steam.get_owned_steam_games(self.steam_key, 123456)
        assert result is None


class TestSteamReview:
    """
    Tests `get_steam_review`. Due to changing reviews, it only tests for acquiring
    floats for percent and integers for total.
    """

    steam = Steam()

    def test_success(self):

        # TODO mock request
        result = self.steam.get_steam_review(app_id=752590)
        if result:
            percent, total = result
            assert isinstance(percent, float)
            assert isinstance(total, int)
        else:
            assert False


class TestGetGameUrl:
    """
    Tests `get_game_url` function.
    """

    steam = Steam()

    def test_get_game_url(self):

        store_link_tests = {
            "752590": "https://store.steampowered.com/app/752590/",
            "629730": "https://store.steampowered.com/app/629730/",
        }
        for app_id, answer in store_link_tests.items():
            game_url = self.steam.get_game_url(app_id)
            assert game_url == answer


class TestGetRecentlyPlayedGames(Utils):
    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "response": {
                "games": [
                    {"name": "Game 1", "appid": 123, "playtime_forever": 10},
                    {"name": "Game 2", "appid": 456, "playtime_forever": 20},
                ]
            }
        }
        mock_response.ok = True
        return mock_response

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self, mock_response, mocker):

        mocker.patch("requests.get", return_value=mock_response)

        result = self.steam.get_recently_played_steam_games(
            self.steam_key, self.steam_id, game_count=1
        )

        assert result == [
            {"name": "Game 1", "appid": 123, "playtime_forever": 10},
            {"name": "Game 2", "appid": 456, "playtime_forever": 20},
        ]

    def test_request_error(self, mocker):

        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        result = self.steam.get_recently_played_steam_games(
            self.steam_key, 123456, game_count=1
        )
        assert result is None


class TestGetSteamUsername(Utils):
    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "response": {
                "players": [
                    {
                        "steamid": "1231654654",
                        "personaname": "test_user",
                    },
                ]
            }
        }
        mock_response.ok = True
        return mock_response

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self, mock_response, mocker):

        mocker.patch("requests.get", return_value=mock_response)

        result = self.steam.get_steam_username(self.steam_key, self.steam_id)

        assert result == "test_user"

    def test_request_error(self, mocker):

        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        result = self.steam.get_steam_username(self.steam_key, 123456)
        assert result is None


class TestGetProfileUsername:
    """
    Tests `extract_profile_username` function.
    """

    steam = Steam()

    def test_extract_profile_username(self):
        with_slash = "http://steamcommunity.com/id/gabelogannewell/"
        username = self.steam.extract_profile_username(with_slash)
        assert username == "gabelogannewell"

    def test_False(self):
        string = "this is not a url"
        username = self.steam.extract_profile_username(string)
        assert username is None


class TestGetSteamID:
    """
    Tests `get_steam_id` function.
    """

    @pytest.fixture
    def mock_response(self, mocker):
        # Create a mock response object
        mock_response = mocker.Mock()
        # Set the JSON data for the response
        mock_response.json.return_value = {
            "response": {"steamid": "1231654654", "success": 1}
        }
        # Set the status code and whether the request was successful
        mock_response.ok = True
        return mock_response

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self, mock_response, mocker):
        # TODO mock requests
        mocker.patch("requests.get", return_value=mock_response)

        steam_id = self.steam.get_steam_id("gabelogannewell", self.steam_key)
        assert steam_id == 1231654654

    def test_request_error(self, mocker):
        steam_id = self.steam.get_steam_id("", self.steam_key)

        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        assert steam_id is None


class TestGetSteamFriends:

    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "friendslist": {
                "friends": [
                    {
                        "steamid": "1231654654",
                        "relationship": "friend",
                        "friend_since": 1568506355,
                    },
                    {
                        "steamid": "564612165",
                        "relationship": "friend",
                        "friend_since": 1568706355,
                    },
                ]
            }
        }
        mock_response.ok = True
        return mock_response

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self, mock_response, mocker):
        mocker.patch("requests.get", return_value=mock_response)

        result = self.steam.get_steam_friends(self.steam_key, self.steam_id)
        assert result == [
            {
                "steamid": "1231654654",
                "relationship": "friend",
                "friend_since": 1568506355,
            },
            {
                "steamid": "564612165",
                "relationship": "friend",
                "friend_since": 1568706355,
            },
        ]

    def test_request_error(self, mocker):

        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        result = self.steam.get_steam_friends(self.steam_key, 123456)
        assert result is None


class TestGetSteamGamePlayerCount:

    steam = Steam()
    steam_key, steam_id = steam.get_steam_api_key_and_id()

    def test_success(self):
        """
        Tests `get_steam_game_player_count` function.
        """
        # TODO mock request
        app_id = 730
        player_count = self.steam.get_steam_game_player_count(app_id, self.steam_key)
        assert isinstance(player_count, int)


class TestGetAppList:

    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "applist": {
                "apps": [
                    {
                        "appid": 123456,
                        "name": "Test 1",
                    },
                    {
                        "appid": 654321,
                        "name": "Test 2",
                    },
                ]
            }
        }
        mock_response.ok = True
        return mock_response

    steam = Steam()

    def test_success(self, mock_response, mocker):
        """
        Tests `get_app_list` function.
        """
        mocker.patch("requests.get", return_value=mock_response)

        app_list = self.steam.get_app_list()
        print(app_list)
        assert isinstance(app_list[0]["appid"], int)
        assert isinstance(app_list[0]["name"], str)


class TestGetAppId:
    steam = Steam()

    app_list = [{"appid": 12345, "name": "Hades"}]

    def test_success(self):
        app_id = self.steam.get_app_id("Hades", self.app_list)
        assert app_id == 12345

    def test_request_error(self):
        app_id = self.steam.get_app_id("Not Real", self.app_list)
        assert app_id == None


if __name__ == "__main__":
    pytest.main([__file__])
