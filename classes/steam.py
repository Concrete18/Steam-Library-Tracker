from classes.utils import Utils


class Steam(Utils):
    def get_owned_steam_games(self, steam_key, steam_id=0):
        """
        Gets the games owned by the given `steam_id`.
        """
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        query = {
            "key": steam_key,
            "steamid": steam_id,
            "l": "english",
            "include_played_free_games": 0,
            "format": "json",
            "include_appinfo": 1,
        }
        response = self.request_url(url, params=query)
        return response.json()["response"]["games"]

    def get_recently_played_steam_games(self, steam_key, steam_id=0, game_count=10):
        """
        Gets the games owned by the given `steam_id`.
        """
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetRecentlyPlayedGames/v1/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        query = {
            "key": steam_key,
            "steamid": steam_id,
            "count": game_count,
        }
        response = self.request_url(url, params=query)
        return response.json()["response"]["games"]

    def get_app_details(self, app_id):
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        self.api_sleeper("steam_app_details")
        query = {"appids": app_id, "l": "english"}
        response = self.request_url(url, params=query)
        if response:
            return response.json()
        return None

    def get_app_list(self):
        """
        Gets the full Steam app list as a dict.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamApps/GetAppList/v0002/"
        url = main_url + api_action
        query = {"l": "english"}
        response = self.request_url(url, params=query)
        if not response:
            return None
        app_list = response.json()["applist"]["apps"]
        return app_list

    @staticmethod
    def get_app_id(game, app_list):
        """
        Gets the games app ID from the `app_list`.
        """
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    @staticmethod
    def get_steam_game_player_count(
        self, app_id: int, steam_api_key: int
    ) -> int | None:
        """
        Gets a games current player count by `app_id` using the Steam API via the `steam_api_key`.
        """
        url = f"http://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}&key={steam_api_key}"
        response = self.request_url(url)
        if response:
            data = response.json()
            current_players = data.get("response", {}).get("player_count", "N/A")
            return current_players
        return None
