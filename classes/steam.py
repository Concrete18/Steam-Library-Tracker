from classes.utils import Utils
from bs4 import BeautifulSoup
from typing import Optional
import re


class Steam(Utils):

    def get_steam_username(self, steam_id: int, steam_key: int) -> str:
        """
        Gets a username based on the given `steam_id`.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/GetPlayerSummaries/v0002/"
        url = main_url + api_action
        params = {"key": steam_key, "steamids": steam_id}
        response = self.request_url(url=url, params=params)
        username = "Unknown"
        player_data = response.json()["response"]["players"]
        if player_data:
            username = player_data[0]["personaname"]
        return username

    @staticmethod
    def get_profile_username(vanity_url):
        if "steamcommunity.com/id" in vanity_url:
            if vanity_url[-1] == "/":
                vanity_url = vanity_url[:-1]
            return vanity_url.split("/")[-1]
        return None

    def get_steam_id(self, vanity_url, steam_key):
        """
        Gets a users Steam ID via their `vanity_url` or `vanity_username`.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/ResolveVanityURL/v0001/"
        url = main_url + api_action
        query = {
            "key": steam_key,
            "vanityurl": vanity_url,
        }
        response = self.request_url(url, params=query)
        if response:
            data = response.json()["response"]
            if "steamid" in data.keys():
                steam_id = data["steamid"]
                return int(steam_id)
        return None

    def get_steam_friends(self, steam_key, steam_id):
        """
        Gets a users Steam friends list.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/GetFriendList/v0001/"
        url = main_url + api_action
        params = {
            "key": steam_key,
            "steamid": steam_id,
            "relationship": "all",
        }
        response = self.request_url(url=url, params=params)
        if response:
            data = response.json()
            return data["friendslist"]["friends"]
        return []

    def get_store_link(self, app_id):
        """
        Generates a steam store link to the games page using it's `app_id`.
        """
        return f"https://store.steampowered.com/app/{app_id}/"

    def get_steam_review(self, app_id: int, response=None) -> tuple[Optional[int]]:
        """
        Scrapes the games review percent and total reviews from
        the steam store page using `app_id` or `store_link`.
        """
        if not response:
            self.api_sleeper("steam_review_scrape")
            store_link = self.get_store_link(app_id)
            response = self.request_url(store_link)
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_review_class = "nonresponsive_hidden responsive_reviewdesc"
        results = soup.find_all(class_=hidden_review_class)
        if len(results) == 1:
            text = results[0].text.strip()
        elif len(results) > 1:
            text = results[1].text.strip()
        else:
            return "-", "-"
        parsed_data = text[2:26].split("% of the ")
        # get percent
        review_perc = parsed_data[0]
        if review_perc.isnumeric():
            if review_perc == "100":
                percent = 1
            else:
                percent = float(f".{review_perc}")
        else:
            percent = "-"
        # get total
        if len(parsed_data) > 1:
            cleaned_num = parsed_data[1].replace(",", "")
            total = int(re.search(r"\d+", cleaned_num).group())
        else:
            total = "-"
        return percent, total

    def get_steam_user_tags(self, app_id: int, response=None):
        """
        Gets a games user tags from Steam.
        """
        if not response:
            self.api_sleeper("steam_review_scrape")
            store_link = self.get_store_link(app_id)
            response = self.request_url(store_link)
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_review_class = "app_tag"
        results = soup.find_all(class_=hidden_review_class)
        tags = []
        ignore_tags = ["+"]
        for tag in results:
            string = tag.text.strip()
            if string not in ignore_tags:
                tags.append(string)
        return tags

    def get_owned_steam_games(self, steam_key: str, steam_id: int):
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
        if response:
            return response.json()["response"]["games"]
        return response

    def get_recently_played_steam_games(
        self, steam_key: str, steam_id: int, game_count: int = 10
    ):
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

    def get_app_details(self, app_id) -> list[dict]:
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

    def get_app_list(self) -> list[dict]:
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
    def get_app_id(game: str, app_list: list[dict]) -> Optional[int]:
        """
        Gets the games app ID from the `app_list`.
        """
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    def get_steam_game_player_count(
        self, app_id: int, steam_api_key: int
    ) -> Optional[int]:
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
