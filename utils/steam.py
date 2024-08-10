# standard library
import re, os

# third-party imports
from bs4 import BeautifulSoup
import requests, vdf

# local application imports
from utils.utils import *
from utils.logger import Logger

Log = Logger()
error_log = Log.create_log(name="base_error", log_path="logs/error.log")


class Steam:

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
                if (
                    "response" in data
                    and "players" in data["response"]
                    and "personaname" in data["response"]["players"][0]
                ):
                    return data["response"]["players"][0]["personaname"]
                else:
                    return None
            else:
                return None
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" in str(e):
                return None
            error_log.warning(msg)

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
                    return None
            else:
                return None
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" in str(e):
                return None
            error_log.warning(msg)

    @retry()
    def get_steam_friends(self, steam_key: str, steam_id: int) -> dict:
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
                    return None
            else:
                return None
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" in str(e):
                return None
            error_log.warning(msg)

    @staticmethod
    def get_friends_list_changes(
        prev_friend_ids: list[int],
        cur_friend_ids: list[int],
    ) -> tuple[list[int], list[int]]:
        """
        Gets friends lists changes based on two lists of ID's.
        """
        additions = list(set(cur_friend_ids) - set(prev_friend_ids))
        removals = list(set(prev_friend_ids) - set(cur_friend_ids))
        return additions, removals

    @retry()
    def get_steam_review(self, app_id: int) -> dict:
        """
        Scrapes the games review percent and total reviews from
        the steam store page using `app_id`.
        """
        api_sleeper("steam_review_scrape")
        game_url = self.get_game_url(app_id)
        response = requests.get(game_url)
        result_dict = {"total": None, "percent": None}
        if not response.ok:
            return result_dict
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_review_class = "nonresponsive_hidden responsive_reviewdesc"
        results = soup.find_all(class_=hidden_review_class)
        if len(results) == 1:
            text = results[0].text.strip()
        elif len(results) > 1:
            text = results[1].text.strip()
        else:
            return result_dict
        parsed_data = text[2:26].split(r"% of the ")
        # get percent
        review_percent = parsed_data[0]
        if review_percent.isnumeric():
            if review_percent == "100":
                result_dict["percent"] = 1
            else:
                result_dict["percent"] = float(f".{review_percent}")
        # get total
        if len(parsed_data) > 1:
            cleaned_num = parsed_data[1].replace(",", "")
            result_dict["total"] = int(re.search(r"\d+", cleaned_num).group())
        return result_dict

    @retry()
    def get_steam_user_tags(self, app_id: int):
        """
        Gets a games user tags from Steam.
        """
        api_sleeper("steam_review_scrape")
        response = requests.get(self.get_game_url(app_id))
        if response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            hidden_review_class = "app_tag"
            results = soup.find_all(class_=hidden_review_class)
            tags = []
            IGNORE_TAGS = ("+",)
            for tag in results:
                string = tag.text.strip()
                if string not in IGNORE_TAGS:
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
        api_sleeper("steam_owned_games")
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
                    return None
            else:
                return None
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" in str(e):
                return None
            error_log.warning(msg)

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
        api_sleeper("steam_owned_games")
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
                    return None
            else:
                return None
        except requests.RequestException as e:
            msg = f"Error occurred: {e}"
            if "Test error" in str(e):
                return None
            error_log.warning(msg)

    @staticmethod
    def get_game_url(app_id: int) -> str:
        """
        Generates a steam store url to the games page using it's `app_id`.
        """
        if app_id:
            return f"https://store.steampowered.com/app/{app_id}/"
        return app_id

    @retry()
    def get_app_details(self, app_id) -> list[dict]:
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        api_sleeper("steam_app_details")
        params = {"appids": app_id, "l": "english"}
        response = requests.get(url, params)
        if response.ok:
            return response.json()
        return None

    # TODO check if this breaks retry
    @staticmethod
    @retry()
    def get_app_list() -> list[dict]:
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

    # TODO check if this breaks retry
    @staticmethod
    @retry()
    def get_player_count(app_id: int, steam_key: int) -> int | None:
        """
        Gets a games current player count by `app_id` using the Steam API via the `steam_key`.
        """
        url = f"http://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}&key={steam_key}"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            current_players = data.get("response", {}).get("player_count", "N/A")
            return current_players
        return None

    @staticmethod
    def get_installed_app_ids(library_vdf_path: str = None) -> list:
        """
        Returns a list of all app_ids among all libraries from the steam library
        VDF file in `library_vdf_path`.
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

    def workshop_size(self, workshop_path, app_list):
        """
        Gets data about the size of the steam workshop files for each
        game folder within `workshop_path`.
        """
        app_ids = os.listdir(workshop_path)
        # TODO find out why some app_ids are not found sometimes
        found_entries = filter(lambda entry: str(entry["appid"]) in app_ids, app_list)
        entry_list = []
        for entry in found_entries:
            path = os.path.join(workshop_path, str(entry["appid"]))
            dir_size = get_dir_size(path)
            entry["bytes"] = dir_size
            if dir_size:
                entry_list.append(entry)

        entry_list.sort(key=lambda entry: entry["bytes"], reverse=True)

        return entry_list
