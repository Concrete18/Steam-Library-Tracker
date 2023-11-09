from pathlib import Path
import unittest, json

# classes
from classes.steam import Steam


def get_steam_key_and_id():
    """
    ph
    """
    config = Path("configs/config.json")
    with open(config) as file:
        data = json.load(file)
    steam_key = data["settings"]["steam_api_key"]
    steam_id = str(data["settings"]["steam_id"])
    return steam_key, steam_id


class GetOwnedGames(unittest.TestCase):
    steam = Steam()
    steam_key, steam_id = get_steam_key_and_id()

    def test_get_owned_steam_games(self):
        """
        Tests `get_game_info` function.
        """
        owned_games = self.steam.get_owned_steam_games(
            self.steam_key,
            self.steam_id,
        )
        # TODO improve this
        found_game = next(
            (game for game in owned_games if game["name"] == "Dishonored2"), None
        )
        # specific test if dishohored is owned
        if found_game:
            name = found_game["name"]
            app_id = found_game["appid"]
            self.assertEqual(app_id, 205100, "Incorrect appid for Dishonored2")
            self.assertIsInstance(name, str, "Name for Dishonored12 is not a string")
        # test if dishonored is not owned
        else:
            game = owned_games[0]
            self.assertIsInstance(game["appid"], int, "Appid should be an integer")
            self.assertIsInstance(game["name"], str, "Name should be a string")


class GetRecentlyPlayedGames(unittest.TestCase):
    steam = Steam()
    steam_key, steam_id = get_steam_key_and_id()
    owned_games = steam.get_recently_played_steam_games(
        steam_key,
        steam_id,
        game_count=1,
    )

    def test_get_recently_played_steam_games(self):
        """
        Tests `get_game_info` function.
        """
        recently_played_games = self.steam.get_recently_played_steam_games(
            self.steam_key,
            self.steam_id,
            game_count=1,
        )
        game = recently_played_games[0]
        self.assertIsInstance(game["appid"], int, "Appid should be an integer")
        self.assertIsInstance(
            game["playtime_forever"], int, "Playtime_forever should be an integer"
        )
        self.assertIsInstance(game["name"], str, "Name should be a string")


class GetAppList(unittest.TestCase):
    steam = Steam()

    def test_get_app_list(self):
        """
        Tests `get_game_info` function.
        """
        app_list = self.steam.get_app_list()
        self.assertIsInstance(app_list[0]["appid"], int, "Appid should be an integer")
        self.assertIsInstance(app_list[0]["name"], str, "Name should be a string")


class GetAppId(unittest.TestCase):
    steam = Steam()

    app_list = [{"appid": 12345, "name": "Hades"}]

    def test_get_app_id(self):
        app_id = self.steam.get_app_id(
            "Hades",
            self.app_list,
        )
        self.assertEqual(app_id, 12345, "Appid should be 12345 for Hades")

    def test_app_id_not_found(self):
        app_id = self.steam.get_app_id(
            "Not Real",
            self.app_list,
        )
        self.assertEqual(app_id, None, "Appid should not exist")


class GetSteamGamePlayerCount(unittest.TestCase):
    steam_key, _ = get_steam_key_and_id()

    def setUp(self):
        self.Test = Steam()

    def test_get_steam_game_player_count(self):
        """
        Tests `get_steam_game_player_count` function.
        """
        app_id = 730
        player_count = self.Test.get_steam_game_player_count(app_id, self.steam_key)
        self.assertIsInstance(player_count, int, "Player_count should be an int")
