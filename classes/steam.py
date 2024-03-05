from classes.utils import Utils, retry
from bs4 import BeautifulSoup
import re, requests, vdf


class Steam(Utils):

    @retry()
    def get_steam_username(self, steam_id: int, steam_key: int) -> str:
        """
        Gets a username based on the given `steam_id`.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/GetPlayerSummaries/v0002/"
        url = main_url + api_action
        params = {"key": steam_key, "steamids": steam_id}
        try:
            response = requests.get(url, params)
            if response.ok:
                data = response.json()
                print(data)
                if (
                    "response" in data
                    and "players" in data["response"]
                    and "personaname" in data["response"]["players"][0]
                ):
                    return data["response"]["players"][0]["personaname"]
                else:
                    return None  # handle missing keys in the JSON response
            else:
                return None  # handle unsuccessful response
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" not in str(e):
                self.error_log.warning(msg)
            return None  # handle request exceptions

    @staticmethod
    def extract_profile_username(vanity_url):
        if "steamcommunity.com/id" in vanity_url:
            if vanity_url[-1] == "/":
                vanity_url = vanity_url[:-1]
            return vanity_url.split("/")[-1]
        return None

    @retry()
    def get_steam_id(self, vanity_url, steam_key):
        """
        Gets a users Steam ID via their `vanity_url` or `vanity_username`.
        """
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
        query = {"key": steam_key, "vanityurl": vanity_url}
        try:
            response = requests.get(url, query)
            if response.ok:
                data = response.json()
                if "response" in data and "steamid" in data["response"]:
                    return int(data["response"]["steamid"])
                else:
                    return None  # handle missing keys in the JSON response
            else:
                return None  # handle unsuccessful response
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" not in str(e):
                self.error_log.warning(msg)
            return None  # handle request exceptions

    @retry()
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
        try:
            response = requests.get(url, params)
            if response.ok:
                data = response.json()
                if "friendslist" in data and "friends" in data["friendslist"]:
                    return data["friendslist"]["friends"]
                else:
                    return None  # handle missing keys in the JSON response
            else:
                return None  # handle unsuccessful response
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" not in str(e):
                self.error_log.warning(msg)
            return None  # handle request exceptions

    @retry()
    def get_steam_review(self, app_id: int) -> tuple[int] | None:
        """
        Scrapes the games review percent and total reviews from
        the steam store page using `app_id`.
        """
        self.api_sleeper("steam_review_scrape")
        game_url = self.get_game_url(app_id)
        response = requests.get(game_url)
        if not response.ok:
            return ("-", "-")
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_review_class = "nonresponsive_hidden responsive_reviewdesc"
        results = soup.find_all(class_=hidden_review_class)
        if len(results) == 1:
            text = results[0].text.strip()
        elif len(results) > 1:
            text = results[1].text.strip()
        else:
            return ("-", "-")
        parsed_data = text[2:26].split("% of the ")
        # get percent
        review_percent = parsed_data[0]
        if review_percent.isnumeric():
            if review_percent == "100":
                percent = 1
            else:
                percent = float(f".{review_percent}")
        else:
            percent = "-"
        # get total
        if len(parsed_data) > 1:
            cleaned_num = parsed_data[1].replace(",", "")
            total = int(re.search(r"\d+", cleaned_num).group())
        else:
            total = "-"
        return (percent, total)

    @retry()
    def get_steam_user_tags(self, app_id: int):
        """
        Gets a games user tags from Steam.
        """
        self.api_sleeper("steam_review_scrape")
        response = requests.get(self.get_game_url(app_id))
        if response.ok:
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

    @retry()
    def get_owned_steam_games(self, steam_key: str, steam_id: int) -> list | None:
        """
        Gets the games owned by the given `steam_id`.
        """
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        params = {
            "key": steam_key,
            "steamid": steam_id,
            "l": "english",
            "include_played_free_games": 0,
            "format": "json",
            "include_appinfo": 1,
        }
        try:
            response = requests.get(url, params)
            if response.ok:
                data = response.json()
                if "response" in data and "games" in data["response"]:
                    return data["response"]["games"]
                else:
                    return None  # handle missing keys in the JSON response
            else:
                return None  # handle unsuccessful response
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" not in str(e):
                self.error_log.warning(msg)
            return None  # handle request exceptions

    @retry()
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
        params = {
            "key": steam_key,
            "steamid": steam_id,
            "count": game_count,
        }
        try:
            response = requests.get(url, params)
            if response.ok:
                data = response.json()
                if "response" in data and "games" in data["response"]:
                    return data["response"]["games"]
                else:
                    return None  # handle missing keys in the JSON response
            else:
                return None  # handle unsuccessful response
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" not in str(e):
                self.error_log.warning(msg)
            return None  # handle request exceptions

    @retry()
    def get_app_details(self, app_id) -> list[dict]:
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        self.api_sleeper("steam_app_details")
        params = {"appids": app_id, "l": "english"}
        response = requests.get(url, params)
        if response.ok:
            return response.json()
        return None

    @retry()
    def get_app_list(self) -> list[dict]:
        """
        Gets the full Steam app list as a dict.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamApps/GetAppList/v0002/"
        url = main_url + api_action
        query = {"l": "english"}
        response = requests.get(url, query)
        if response.ok:
            app_list = response.json()["applist"]["apps"]
            return app_list
        return None

    @staticmethod
    def get_app_id(game: str, app_list: list[dict]) -> int | None:
        """
        Gets the games app ID from the `app_list`.
        """
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    @retry()
    def get_steam_game_player_count(
        self, app_id: int, steam_api_key: int
    ) -> int | None:
        """
        Gets a games current player count by `app_id` using the Steam API via the `steam_api_key`.
        """
        url = f"http://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}&key={steam_api_key}"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            print(data)
            current_players = data.get("response", {}).get("player_count", "N/A")
            return current_players
        return None

    def get_installed_app_ids(self, library_vdf_path: str = None) -> list:
        """
        ph
        """
        if not library_vdf_path:
            return []
        with open(library_vdf_path, "r", encoding="utf-8") as file:
            data = vdf.load(file)
        if "libraryfolders" not in data:
            return []
        installed_app_ids = []
        for library in data["libraryfolders"].values():
            for app_id in library["apps"].keys():
                installed_app_ids.append(int(app_id))
        return installed_app_ids
