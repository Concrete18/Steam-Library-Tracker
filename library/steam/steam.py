# standard library
import os

# third-party imports
import requests, vdf

# local imports
from library.utils.utils import *
from library.logger import Logger
from library.utils.api_throttler import ApiThrottler

Log = Logger()
error_log = Log.create_log(name="base_error", log_path="logs/error.log")

throttler = ApiThrottler()


@retry()
def get_steam_username(steam_id: int, steam_key: str) -> str | None:
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


@retry()
def get_steam_id(vanity_url, steam_key):
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
def get_steam_friends(steam_key: str, steam_id: int) -> dict:
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
                return {}
        else:
            return {}
    except requests.RequestException as e:
        msg = f"Error occurred: {e}"
        if "Test error" in str(e):
            return {}
        error_log.warning(msg)
    return {}


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


@retry(print_error=False)
def get_owned_steam_games(steam_key: str, steam_id: int) -> list:
    """
    Gets the games owned by the given `steam_id`.
    """
    base_url = "http://api.steampowered.com/"
    api_action = "IPlayerService/GetOwnedGames/v0001/"
    url = base_url + api_action
    throttler.wait_if("steam_api", 2)
    params = {
        "key": steam_key,
        "steamid": steam_id,
        "l": "english",
        "include_played_free_games": 0,
        "format": "json",
        "include_appinfo": 1,
    }
    headers = {"User-Agent": "GameLibraryTracker/1.0"}
    response = requests.get(url, params, headers=headers)
    response.raise_for_status()
    if response.ok:
        data = response.json()
        if "response" in data and "games" in data["response"]:
            return data["response"]["games"]
    return []


@retry()
def get_recently_played_steam_games(
    steam_key: str, steam_id: int, game_count: int = 10
):
    """
    Gets the games owned by the given `steam_id`.
    """
    base_url = "http://api.steampowered.com/"
    api_action = "IPlayerService/GetRecentlyPlayedGames/v1/"
    url = base_url + api_action
    throttler.wait_if("steam_api")
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


@retry()
def get_app_list() -> list[dict]:
    """
    Gets the full Steam app list as a dict.
    """
    base_url = "https://api.steampowered.com/"
    endpoint = "ISteamApps/GetAppList/v0002/"
    url = base_url + endpoint
    query = {"l": "english"}
    response = requests.get(url, query)
    if response.ok:
        data = response.json()
        return data.get("applist", {}).get("apps", None)
    return []


def get_app_id(game: str, app_list: list[dict]) -> int | None:
    """
    Gets the games app ID from the `app_list`.
    """
    for item in app_list:
        if item["name"] == game:
            return item["appid"]
    return None

def get_installed_app_ids(library_vdf_path: str = "") -> list:
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


def get_local_config_data(local_config_path: str = "") -> dict:
    """
    Gets the local config data for games from the Steam install data.
    """
    if not local_config_path:
        return {}
    with open(local_config_path, "r", encoding="utf-8") as file:
        data = vdf.load(file)
    return (
        data.get("UserLocalConfigStore", {})
        .get("Software", {})
        .get("valve", {})
        .get("Steam", {})
        .get("apps", {})
    )


def get_game_local_data(
    app_id: int, local_config: dict
) -> tuple[int | None, int | None]:
    """ """
    game_config_data = local_config.get(str(app_id), {})
    last_played = int(game_config_data.get("LastPlayed", 0))
    play_time = int(game_config_data.get("Playtime", 0))
    # replaces zero values with None for both variables
    last_played = None if last_played == 0 else last_played
    play_time = None if play_time == 0 else play_time
    return last_played, play_time


def workshop_size(workshop_path: str, app_list: list) -> list[dict]:
    """
    Gets data about the size of the steam workshop files for each
    game folder within `workshop_path`.
    """
    app_ids = os.listdir(workshop_path)
    # BUG find out why some app_ids are not found sometimes
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
