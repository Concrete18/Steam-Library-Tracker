import random, time, json, os, re, sys, hashlib, webbrowser, subprocess
from black import main
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import datetime as dt
import pandas as pd

# classes
from classes.excel import Excel, Sheet
from classes.helper import Helper
from classes.helper import keyboard_interrupt


class Tracker(Helper):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    ext_terminal = sys.stdout.isatty()
    # config init
    config = Path("configs\config.json")
    with open(config) as file:
        data = json.load(file)
    steam_api_key = data["settings"]["steam_api_key"]
    steam_id = str(data["settings"]["steam_id"])
    excel_filename = data["settings"]["excel_filename"]
    playstation_data_link = data["settings"]["playstation_data_link"]
    name_ignore_list = [string.lower() for string in data["name_ignore_list"]]
    appid_ignore_list = data["appid_ignore_list"]
    # class init
    options = {
        "shrink_to_fit_cell": True,
        "fill": ["Rating Comparison", "Probable Completion"],
        "percent": [
            "%",
            "Percent",
            "Discount",
            "Rating Comparison",
            "Probable Completion",
        ],
        "currency": ["Price", "MSRP", "Cost"],
        "integer": ["ID", "Number"],
        "count_days": ["Days Till Release", "Days Since Update"],
        "date": ["Last Updated", "Date"],
        "decimal": ["Hours Played"],
        "not_centered": [
            "Name",
            "Tags",
            "Game Name",
            "Developers",
            "Publishers",
            "Genre",
        ],
    }
    excel = Excel(excel_filename, log_file="configs/excel.log")
    games = Sheet(excel, "Game Name", sheet_name="Games", options=options)
    # current date and time setup
    cur_date = dt.datetime.now()
    formatted_date = cur_date.strftime("%#m/%#d/%Y")
    # api call logger
    play_status_choices = {
        "1": "Played",
        "2": "Playing",
        "3": "Waiting",
        "4": "Finished",
        "5": "Quit",
        "6": "Unplayed",
        "7": "Ignore",
    }
    # misc
    json_path = Path("configs\playstation_games.json")
    # columns
    to_check = [
        genre_col := "Genre",
        pub_col := "Publishers",
        dev_col := "Developers",
        metacritic_col := "Metacritic",
        time_to_beat_col := "Time To Beat in Hours",
        release_col := "Release Year",
        ea_col := "Early Access",
    ]

    def config_check(self):
        """
        Checks to see if the config data is usable.
        """
        errors = []
        if len(self.steam_id) != 17:
            errors.append("Steam ID is invalid.")
        if errors:
            return False, errors
        else:
            return True, None

    def get_steam_id(self, vanity_url):
        """
        Gets a users Steam ID via their `vanity_url`.
        """
        main_url = "https://api.steampowered.com/"
        api_action = r"ISteamUser/ResolveVanityURL/v0001/"
        url_var = f"?key={self.steam_api_key}&vanityurl={vanity_url}"
        url = main_url + api_action + url_var
        response = self.request_url(url)
        if response:
            data = response.json()
            steam_id = data["response"]["steamid"]
            return steam_id
        else:
            return False

    def get_time_to_beat(self, game_name, delay=2):
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
        if delay > 0:
            time.sleep(delay)
        self.api_sleeper("time_to_beat")
        results = HowLongToBeat().search(game_name)
        if results is not None and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            string_time = str(best_element.gameplay_main).replace("½", ".5")
            time_to_beat = float(string_time)
            time_to_beat_unit = best_element.gameplay_main_unit
            if time_to_beat_unit == None:
                return "No Data"
            elif time_to_beat_unit != "Hours":
                return round(time_to_beat / 60, 1)  # converts minutes to hours
            else:
                return time_to_beat
        else:
            return "Not Found"

    def get_metacritic(self, game_name, platform, debug=False):
        """
        Uses requests to get the metacritic review score for the entered game.
        """
        if " - Console" in game_name:
            game_name = game_name.replace(" - Console", "")
        if platform == "PS4":
            platform = "playstation-4"
        elif platform == "PS5":
            platform = "playstation-5"
        elif platform in ["Steam", "Uplay", "Origin", "MS Store", "GOG"]:
            platform = "pc"
        game_name = self.url_sanitize(game_name)
        user_agent = {"User-agent": "Mozilla/5.0"}
        self.api_sleeper("metacritic")
        review_score = ""
        main_url = "https://www.metacritic.com/"
        url_vars = f"/game/{platform.lower()}/{game_name.lower()}"
        url = main_url + url_vars
        if debug:
            print(url)
        response = self.request_url(url, headers=user_agent)
        if response:
            soup = BeautifulSoup(response.text, "html.parser")
            review_score = soup.find(itemprop="ratingValue")
            if review_score != None:
                review_score = int(review_score.text)
            else:
                review_score = "No Score"
            return review_score
        else:
            msg = f"Failed to check {url}"
            self.logger.warning(msg)
            review_score = "Page Error"
        return review_score

    def get_appid(self, game, app_list={}):
        """
        Checks the Steam App list for a game
        and returns its app id if it exists as entered.
        """
        # sets up app_list if it does not exist
        if app_list == {}:
            main_url = "http://api.steampowered.com/"
            api_action = "ISteamApps/GetAppList/v0002/?l=english"
            url = main_url + api_action
            response = self.request_url(url)
            if not response:
                return None
            app_list = response.json()["applist"]["apps"]
        # searches for game
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    def get_year(self, date_string):
        """
        Gets the year from `date_string`.
        """
        year = re.search(r"[0-9]{4}", date_string)
        if year:
            return year.group(0)
        else:
            return "Invalid Date"

    def get_game_info(self, appid, debug=False):
        """
        Gets game info with steam api using a `appid`.
        """

        def get_json_desc(data):
            return [item["description"] for item in data]

        main_url = "https://store.steampowered.com/"
        api_action = "api/appdetails"
        url_vars = f"?appids={appid}&l=english"
        url = main_url + api_action + url_vars
        self.api_sleeper("steam_app_details")
        response = self.request_url(url)
        if not response:
            return None
        else:
            info_dict = {}
            dict = response.json()
            if debug:
                print(dict)
                exit()
            if "data" in dict[str(appid)].keys():
                game_info = dict[str(appid)]["data"]
                keys = game_info.keys()
                info_dict["name"] = game_info["name"]
                # get developer
                if "developers" in keys:
                    info_dict["developers"] = ", ".join(game_info["developers"])
                else:
                    info_dict["developers"] = None
                # get publishers
                if "publishers" in keys:
                    info_dict["publishers"] = ", ".join(game_info["publishers"])
                else:
                    info_dict["publishers"] = None
                # get genre
                if "genres" in keys:
                    genres = get_json_desc(game_info["genres"])
                    info_dict["genre"] = ", ".join(genres)
                    # early access
                    # TODO does not update when changed
                    if "Early Access" in info_dict["genre"]:
                        info_dict["early_access"] = "Yes"
                    else:
                        info_dict["early_access"] = "No"
                else:
                    info_dict["genre"] = None
                # get metacritic
                if "metacritic" in keys:
                    info_dict["metacritic"] = game_info["metacritic"]["score"]
                else:
                    info_dict["metacritic"] = None
                # get release year
                if "release_date" in keys:
                    release_date = game_info["release_date"]["date"]
                    release_date = self.get_year(release_date)
                    info_dict["release_date"] = release_date
                else:
                    info_dict["release_date"] = None
                # get price_info
                if "price_overview" in keys:
                    price_data = game_info["price_overview"]
                    price = price_data["final_formatted"]
                    discount = price_data["discount_percent"]
                    on_sale = price_data["discount_percent"] > 0
                    info_dict["price"] = price
                    info_dict["discount"] = discount
                    info_dict["on_sale"] = on_sale
                else:
                    info_dict["price"] = None
                    info_dict["discount"] = None
                    info_dict["on_sale"] = None
                # get linux compat
                if "platforms" in keys:
                    info_dict["linux_compat"] = game_info["platforms"]["linux"]
                else:
                    info_dict["linux_compat"] = False
                if "categories" in keys:
                    categories = get_json_desc(game_info["categories"])
                    info_dict["categories"] = ", ".join(categories)
                else:
                    info_dict["categories"] = None
                # drm info
                if "drm_notice" in keys:
                    info_dict["drm_notice"] = game_info["drm_notice"]
                else:
                    info_dict["drm_notice"] = None
                # external account
                if "ext_user_account_notice" in keys:
                    info_dict["ext_user_account_notice"] = game_info[
                        "ext_user_account_notice"
                    ]
                else:
                    info_dict["ext_user_account_notice"] = None
                # runs unicode remover on all values
                final_dict = {k: self.unicode_remover(v) for k, v in info_dict.items()}
                return final_dict
        return False

    def set_release_year(self, game, release_year):
        """
        Sets `game`'s release year cell to `release_year`.
        """
        self.games.update_cell(game, self.release_col, release_year)

    def set_genre(self, game, genre):
        """
        Sets `game`'s genre cell to `genre`.
        """
        self.games.update_cell(game, self.genre_col, genre)

    def set_early_access(self, game, value):
        """
        Sets `game`'s early access cell to `value`.
        """
        self.games.update_cell(game, self.ea_col, value)

    def set_publisher(self, game, value):
        """
        Sets `game`'s publisher cell to `value`.
        """
        self.games.update_cell(game, self.pub_col, value)

    def set_developer(self, game, value):
        """
        Sets `game`'s developer cell to `value`.
        """
        self.games.update_cell(game, self.dev_col, value)

    def set_metacritic(self, game, score):
        """
        Sets `game`'s metacritic score to `score`.
        """
        self.games.update_cell(game, self.metacritic_col, score)

    def set_time_to_beat(self, game, time_to_beat):
        """
        Sets `game`'s Time to beat cell to `time_to_beat`.
        """
        self.games.update_cell(game, self.time_to_beat_col, time_to_beat)

    def set_steam_deck(self, game, status):
        """
        Sets `game`'s Steam Deck Status to `status`.
        """
        self.games.update_cell(game, "Steam Deck Status", status)

    def set_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Hours Played cell to `hours_played`.
        """
        self.games.update_cell(game_name, "Hours Played", hours_played)

    def set_linux_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Linux Hours cell to `hours_played`.
        """
        self.games.update_cell(game_name, "Linux Hours", hours_played)

    def set_play_status(self, game_name, play_status):
        """
        Sets `game`'s Play Status cell to `play_status`.
        """
        self.games.update_cell(game_name, "Play Status", play_status)

    def set_date_updated(self, game):
        """
        Sets `game`'s Date Updated cell to the current date.
        """
        self.games.update_cell(game, "Date Updated", self.formatted_date)

    def get_store_link(self, appid):
        """
        Generates a steam store link to the games page using it's `appid`.
        """
        if not appid or appid == "None":
            return False
        return f"https://store.steampowered.com/app/{appid}/"

    def requests_loop(self, skip_filled=1, check_status=0):
        """
        Loops through games in row_idx and gets missing data for
        time to beat, Metacritic score and additional game info from Steam API.

        Use `skip_filled` to skip non blank entries.

        Use `check_status` to opnly check games with a with specific play status.
        """
        # creates checklist
        check_list = []
        for game in self.games.row_idx:
            play_status = self.games.get_cell(game, "Play Status")
            if check_status:
                if play_status not in [
                    "Unplayed",
                    "Playing",
                    "Played",
                    "Finished",
                    "Quit",
                ]:
                    continue
            if skip_filled:
                for column in self.to_check:
                    cell = self.games.get_cell(game, column)
                    if cell == None and game not in check_list:
                        check_list.append(game)
                        continue
            else:
                check_list.append(game)
        # checks if data should be updated
        missing_data = len(check_list)
        auto_run = 50
        if 0 < missing_data <= auto_run:
            print(f"\nMissing data is within threshold of {auto_run}.")
        elif missing_data > auto_run:
            msg = (
                f"\nSome data is missing for {missing_data} games."
                "\nDo you want to retrieve it?\n:"
            )
            if not input(msg) in ["yes", "y"]:
                return
        else:
            return
        try:
            # updates missing data
            print("\nTime To Beat, Metacritic and other steam data check.")
            save_interval = 15
            running_interval = save_interval
            for game_name in tqdm(
                iterable=check_list,
                ascii=True,
                unit="games",
                dynamic_ncols=True,
            ):
                # How long to beat check
                if not self.games.get_cell(game_name, self.time_to_beat_col):
                    time_to_beat = self.get_time_to_beat(game_name)
                    if time_to_beat != None:
                        self.set_time_to_beat(game_name, time_to_beat)
                # metacritic score check
                if not self.games.get_cell(game_name, self.metacritic_col):
                    platform = self.games.get_cell(game_name, "Platform")
                    metacritic_score = self.get_metacritic(game_name, platform)
                    if metacritic_score != None:
                        self.set_metacritic(game_name, metacritic_score)
                # gets steam info if an app id exists and Steam is platform
                appid = self.games.get_cell(game_name, "App ID")
                if not appid:
                    appid = self.get_appid(game_name)
                steam_info = self.get_game_info(appid)
                platform = self.games.get_cell(game_name, "Platform")
                if not steam_info or platform != "Steam":
                    pass
                # genre
                if steam_info["genre"]:
                    self.set_genre(game_name, steam_info["genre"])
                    # early access
                    if "Early Access" in steam_info["genre"]:
                        self.set_early_access(game, "Yes")
                    else:
                        self.set_early_access(game, "No")
                else:
                    self.set_genre(game, "No Genre")
                    self.set_early_access(game, "Unknown")
                # release year
                if steam_info["release_date"]:
                    self.set_release_year(game_name, steam_info["release_date"])
                else:
                    self.set_release_year(game_name, "No Release Year")
                # developer
                if steam_info["developers"]:
                    self.set_developer(game_name, steam_info["developers"])
                else:
                    self.set_developer(game_name, "No Developer")
                # publishers
                if steam_info["publishers"]:
                    self.set_publisher(game_name, steam_info["publishers"])
                else:
                    self.set_publisher(game_name, "No Publisher")
                # metacritic
                if steam_info["metacritic"]:
                    self.set_metacritic(game_name, steam_info["metacritic"])
                else:
                    if not self.games.get_cell(game_name, self.metacritic_col):
                        self.set_metacritic(game_name, "No Score")
            else:
                self.set_release_year(game_name, "No Release Year")
                self.set_genre(game, "No Data")
                self.set_developer(game_name, "No Data")
                self.set_publisher(game_name, "No Data")
                self.set_early_access(game_name, "No")
            running_interval -= 1
            if running_interval == 0:
                running_interval = save_interval
                self.excel.save_excel(use_print=False, backup=False)
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            self.excel.save_excel()

    @staticmethod
    def play_status(play_status: str, hours_played: float):
        """
        Using time_played and play_status,
        determines what the play_status should change to.
        """
        hours_played_type = type(hours_played)
        if hours_played_type is not float and hours_played_type is not int:
            return play_status or ""
        if play_status not in ["Played", "Unplayed", "Must Play", None]:
            return play_status
        # play status change
        if hours_played >= 1:
            play_status = "Playing"
        elif hours_played >= 0.5:
            play_status = "Played"
        else:
            if play_status != "Must Play":
                play_status = "Unplayed"
        return play_status

    def get_owned_steam_games(self, steam_id=0):
        """
        ph
        """
        # asks for a steam id if the given one is invalid
        while len(steam_id) != 17:
            msg = "\nInvalid Steam ID (It must be 17 numbers.)\nTry Again.\n:"
            steam_id = input(msg)
        main_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url_var = f"?key={self.steam_api_key}&steamid={steam_id}?l=english"
        options = "include_played_free_games=0&format=json&include_appinfo=1"
        url = main_url + api_action + url_var + options
        self.api_sleeper("steam_owned_games")
        return self.request_url(url)

    def refresh_steam_games(self, steam_id):
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        print("\nSteam Library Tracking")
        response = self.get_owned_steam_games(steam_id)
        if response:
            # checks for games that changed names or no longer exist
            self.removed = [
                str(game)
                for game in self.games.row_idx.keys()
                if self.games.get_cell(game, "Platform") == "Steam"
            ]
            self.total_games_updated = 0
            self.total_games_added = 0
            self.added_games = []
            for game in response.json()["response"]["games"]:
                game_name = game["name"]
                appid = game["appid"]
                if self.should_ignore(game_name, appid):
                    continue
                # sets play time eariler so it only needs to be set up once
                minutes_played = game["playtime_forever"]
                hours_played = self.hours_played(minutes_played)
                # linux time
                linux_minutes_played = ""
                if "playtime_linux_forever" in game.keys():
                    linux_minutes_played = game["playtime_linux_forever"]
                cur_play_status = self.games.get_cell(game_name, "Play Status")
                # checks if play status should change
                play_status = self.play_status(cur_play_status, hours_played)
                appid = game["appid"]
                if game_name in self.games.row_idx.keys():
                    # removes existing games
                    if game_name in self.removed:
                        self.removed.remove(game_name)
                    self.update_game(
                        game_name,
                        minutes_played,
                        linux_minutes_played,
                        play_status,
                    )
                else:
                    self.add_game(
                        game_name,
                        minutes_played,
                        linux_minutes_played,
                        appid,
                        play_status,
                    )
            if self.removed:
                print(f'\nUnaccounted Steam games:\n{", ".join(self.removed)}')
                for game in self.removed:
                    status = self.games.get_cell(game, "Play Status")
                    if status is not None:
                        if "Removed | " not in status:
                            removed_status = f"Removed | {status}"
                            self.set_play_status(game, removed_status)
                            self.set_date_updated(game)
            return True

    @staticmethod
    def hash_file(file_path, buf_size: int = 65536):
        """
        Creates a hash for the given `file_path`.
        """
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()

    def check_for_changes(self, json_path):
        """
        Checks for changes to the json file.
        """
        with open(self.config) as file:
            data = json.load(file)
        previous_hash = data["settings"]["playstation_hash"]
        new_hash = self.hash_file(json_path)
        if new_hash == previous_hash:
            print("\nNo PlayStation games were added or updated.")
            return False
        else:
            self.data["settings"]["playstation_hash"] = new_hash
            self.save_json_output(self.data, self.config)
            with open(self.config) as file:
                data = json.load(file)
        return True

    def should_ignore(self, name: str = None, appid: int = None) -> bool:
        """
        Checks if the item should be ignored based on name or appid.

        Returns False if neither are given and
        priortizes checking appid if both are given.

        `Name` check looks for keywords and if the name is in the name_ignore_list.

        `Appid` check looks for the appid in the appid_ignore_list.
        """
        # return False if name and appid is not given
        if not name and not appid:
            return False
        # appid ignore list
        if appid and appid in self.appid_ignore_list:
            return True
        if name:
            # name ignore list
            filtered_name = self.unicode_remover(name)
            if filtered_name and filtered_name.lower() in self.name_ignore_list:
                return True
            # keyword check
            keyword_ignore_list = [
                "demo",
                "beta",
                "youtube",
                "playtest",
                "preorder",
                "pre-order",
                "soundtrack",
                "yest server",
                "Bonus content",
                "yrial edition",
                "vlosed test",
                "public test",
                "public testing",
                "directors' commentary",
            ]
            for string in keyword_ignore_list:
                if re.search(rf"\b{string}\b", name.lower()):
                    return True
        return False

    @staticmethod
    def unicode_fix(string):
        """
        Basic unicode cleaner.
        """
        inicode_dict = {
            "â€": "'",
            "®": "",
            "™": "",
            "â„¢": "",
            "Â": "",
            "Ã›": "U",
        }
        for char, replace in inicode_dict.items():
            string = string.replace(char, replace)
        return string.strip()

    def add_playstation_games(self, games):
        """
        Adds playstation games to excel using the given `games` variable.
        """
        added_games = []
        for game in tqdm(
            iterable=games,
            ascii=True,
            unit="games",
            dynamic_ncols=True,
        ):
            game_name = self.unicode_fix(game["name"])
            # skip if it any are true
            game_exists = [
                # should be ignored
                self.should_ignore(name=game_name),
                # added this session
                game_name in added_games,
                # already exist
                game_name in self.games.row_idx.keys(),
                # game exists with a playstation version already
                f"{game_name} - Console" in self.games.row_idx.keys(),
            ]
            if any(game_exists):
                continue
            # adds the game
            added_games.append(game_name)
            self.add_game(
                game_name=game_name,
                play_status="Unplayed",
                platform=game["platform"],
            )
        total_games_added = len(added_games)
        print(f"Added {total_games_added} PS4/PS5 Games.")
        if total_games_added > 0:
            self.excel.save_excel()

    def create_dataframe(self, table):
        """
        Creates a dataframe from a `table` found using requests and
        BeautifulSoup.
        """
        # find all headers
        headers = []
        for i in table.find_all("th"):
            title = i.text
            headers.append(title)
        # creates and fills dataframe
        df = pd.DataFrame(columns=headers)
        for j in table.find_all("tr")[1:]:
            row_data = j.find_all("td")
            row = [i.text for i in row_data]
            length = len(df)
            df.loc[length] = row
        return df

    def update_last_run(self, name):
        """
        Updates json by `name` with the current date.
        """
        self.data["last_runs"][name] = self.cur_date.strftime("%m/%d/%Y")
        self.save_json_output(self.data, self.config)

    def steam_deck_compat(self, appid):
        """
        Gets a games steam deck verification and other compatibility data
        by `appid`.
        """
        main_url = "https://store.steampowered.com/"
        action_url = "saleaction/ajaxgetdeckappcompatibilityreport"
        url_var = f"?nAppID={appid}"
        url = main_url + action_url + url_var
        data = self.request_url(url).json()
        if not data:
            return False
        categories = {
            0: "UNKNOWN",
            1: "UNSUPPORTED",
            2: "PLAYABLE",
            3: "VERIFIED",
        }
        results = data["results"]
        if not results:
            return False
        category_id = results["resolved_category"]
        return categories[category_id]

    def steam_deck_check(self, force_run=False):
        """
        Checks steam_deck.txt and updates steam deck status with the new info.
        """
        if not force_run:
            last_check_string = self.data["last_runs"]["steam_deck_check"]
            last_check = self.string_to_date(last_check_string)
            days_since = self.days_since(last_check)
            check_freq = self.data["settings"]["steam_deck_check_freq"]
            if days_since < check_freq:
                days_till_check = check_freq - days_since
                print(f"\nNext Steam Deck Check in {days_till_check} days")
                return
        print("\nSteam Deck Compatibility Check")
        steam_deck_ignore_list = self.data["steam_deck_ignore_list"]
        updated_games = []
        empty_results = []
        for game_name in tqdm(
            iterable=self.games.row_idx,
            ascii=True,
            unit="games",
            dynamic_ncols=True,
        ):
            if game_name in steam_deck_ignore_list:
                continue
            appid = self.games.get_cell(game_name, "App ID")
            if not appid:
                continue
            status = self.steam_deck_compat(appid)
            self.api_sleeper("steam_deck")
            if not status:
                empty_results.append(game_name)
                continue
            if self.set_steam_deck(game_name, status):
                info = f"{game_name} was updated to {status}"
                updated_games.append(info)
        if updated_games:
            print("\nUpdated Games:")
            for game in updated_games:
                print(game)
            self.excel.save_excel()
            if empty_results:
                print("The following Games failed to retrieve data.")
                print(", ".join(empty_results))
        else:
            print("No Steam Deck Status Changes")
        self.update_last_run("steam_deck_check")

    def check_steam_deck_data_file(self):
        """
        Checks steam deck data based on data copied into a text file.
        """
        with open("configs\steam_deck.txt") as f:
            lines = f.read().splitlines()
        for line in lines:
            print(line.split("\t"))
            values = line.split("\t")
            if len(values) == 3:
                appid, game_name, status = line.split("\t")
            elif len(values) == 4:
                appid, game_name, ignore, status = line.split("\t")
            if self.set_steam_deck(game_name, status):
                print("failed on", game_name, status)
        self.excel.save_excel()

    def check_playstation_json(self):
        """
        Checks `playstation_games.json` to find out if it is newly updated so
        it can add the new games to the sheet.
        """
        # checks if json exists
        if not self.json_path.exists:
            print("PlayStation Json does not exist.")
            webbrowser.open_new(self.playstation_data_link)
            return None
        # create hash file if it does not exist
        if not self.json_path.exists:
            self.json_path.touch()
        if not self.check_for_changes(self.json_path):
            return None
        with open(self.json_path) as file:
            data = json.load(file)
        print("\nChecking for new games for PS4 or PS5.")
        games = data["data"]["purchasedTitlesRetrieve"]["games"]
        self.add_playstation_games(games)

    def update_game(
        self,
        game_name,
        minutes_played,
        linux_minutes_played,
        play_status,
    ):
        """
        Updates the games playtime and play status if they changed.
        """
        # all hours
        previous_hours_played = self.games.get_cell(game_name, "Hours Played")
        current_hours_played = self.hours_played(minutes_played)
        current_linux_hours_played = self.hours_played(linux_minutes_played)
        # prevents updating games that are owned on Steam and a console.
        current_platform = self.games.get_cell(game_name, "Platform")
        if current_platform != "Steam":
            return
        elif previous_hours_played == None or previous_hours_played == "None":
            previous_hours_played = 0
        else:
            previous_hours_played = float(previous_hours_played)
        if current_hours_played > previous_hours_played:
            self.set_hours_played(game_name, current_hours_played)
            self.set_linux_hours_played(game_name, current_linux_hours_played)
            self.set_date_updated(game_name)
            self.set_play_status(game_name, play_status)
            self.total_games_updated += 1
            # updated game logging
            hours_played = current_hours_played - previous_hours_played
            added_time_played = self.convert_time_passed(hours_played * 60)
            overall_time_played = self.convert_time_passed(minutes_played)
            print(f"\n > {game_name} updated.")
            print(f"   Added {added_time_played}")
            print(f"   Total Playtime: {overall_time_played}.")
            # logs play time
            msg = f"{game_name} played for {added_time_played}"
            self.logger.info(msg)
        self.games.format_cells(game_name)

    def manually_add_game(self):
        """
        Allows manually adding a game by giving the name,
        platform and hours played.
        """
        game_name = input("\nWhat is the name of the game?\n:")
        platform = input("\nWhat is the platform is this on?\n:")
        platform_names = {
            "playstation 5": "PS5",
            "ps5": "PS5",
            "playstation 4": "PS4",
            "ps4": "PS4",
            "sw": "Switch",
            "uplay": "Uplay",
            "gog": "GOG",
            "ms store": "MS Store",
            "ms": "MS Store",
            "microsoft": "MS Store",
        }
        if platform.lower() in platform_names:
            platform = platform_names[platform.lower()]
        hours_played = int(input("\nHow many hours have you played it?\n:") or 0)
        print("\nWhat Play Status should it have?")
        play_status = self.play_status_picker() or "Unset"
        print(f"\nAdded Game:\n{game_name}")
        print(f"Platform: {platform}")
        print(f"Hours Played: {hours_played}")
        print(f"Play Status: {play_status}")
        self.add_game(
            game_name=game_name,
            minutes_played=hours_played * 60,
            play_status=play_status,
            platform=platform,
            save=True,
        )
        return game_name, hours_played * 60, play_status

    def add_game(
        self,
        game_name=None,
        minutes_played="",
        linux_minutes_played="",
        appid="",
        play_status="",
        platform="Steam",
        save=False,
    ):
        """
        Adds a game with the game_name, hours played using `minutes_played`, `play_status` and `platform`.

        If save is True, it will save after adding the game.
        """
        print(f"Adding {game_name}")
        play_status = "Unplayed"
        hours_played = ""
        if minutes_played:
            hours_played = self.hours_played(minutes_played)
            # sets play status
            play_status = self.play_status(play_status, hours_played)
        linux_hours_played = ""
        if linux_minutes_played:
            linux_hours_played = self.hours_played(linux_minutes_played)
        # store link setup
        store_link_hyperlink = ""
        store_link = self.get_store_link(appid)
        if store_link:
            store_link_hyperlink = f'=HYPERLINK("{store_link}","Store Link")'
        # sets vr support value
        steam_deck_status = "UNKNOWN"
        early_access = "No"
        if re.search(r"\bVR\b", game_name):
            vr_support = "Yes"
        elif platform in ["PS5", "PS4", "Switch"]:
            vr_support = "No"
            steam_deck_status = "UNSUPPORTED"
        else:
            vr_support = ""
        # easy_indirect_cell setup
        rating_com = "Rating Comparison"
        my_rating = self.games.easy_indirect_cell(rating_com, "My Rating")
        metacritic = self.games.easy_indirect_cell(rating_com, "Metacritic")
        prob_compl = "Probable Completion"
        hours = self.games.easy_indirect_cell(prob_compl, "Hours Played")
        ttb = self.games.easy_indirect_cell(prob_compl, "Time To Beat in Hours")
        days_since = "Days Since Update"
        date_updated = self.games.easy_indirect_cell(days_since, "Date Updated")
        # sets excel column values
        column_info = {
            "My Rating": "",
            "Game Name": game_name,
            "Play Status": play_status,
            "Platform": platform,
            "VR Support": vr_support,
            "Early Access": early_access,
            "Steam Deck Status": steam_deck_status,
            "Time To Beat in Hours": self.get_time_to_beat(game_name),
            "Metacritic": self.get_metacritic(game_name, "Steam"),
            "Rating Comparison": f'=IFERROR(({my_rating}*10)/{metacritic}, "Missing Data")',
            "Probable Completion": f'=IFERROR({hours}/{ttb},"Missing Data")',
            "Hours Played": hours_played,
            "Linux Hours": linux_hours_played,
            "App ID": appid,
            "Store Link": store_link_hyperlink,
            "Days Since Update": f"={date_updated}-TODAY()",
            "Date Updated": self.formatted_date,
            "Date Added": self.formatted_date,
        }
        steam_info = self.get_game_info(appid)
        if steam_info:
            columns = [
                "Publishers",
                "Developers",
                "Genre",
                "Release Year",
                "Metacritic",
                "Early Access",
            ]
            for column in columns:
                if column.lower() in steam_info.keys():
                    column_info[column] = steam_info[column.lower()]
        self.games.add_new_line(column_info, game_name)
        self.added_games.append(game_name)
        self.total_games_added += 1
        self.games.format_cells(game_name)
        if save:
            print("saved")
            self.excel.save_excel()

    def output_completion_data(self):
        """
        Shows total games added and updated games with info.
        """
        if self.total_games_added > 0:
            print(f"\nGames Added: {self.total_games_added}")
            if self.added_games:
                print(", ".join(self.added_games))
        if self.total_games_updated > 0:
            print(f"\nGames Updated: {self.total_games_updated}")
        if self.excel.changes_made:
            self.excel.save_excel()
        else:
            print("\nNo Steam games were added or updated.")

    def play_status_picker(self):
        """
        Shows a list of Play Status's to choose from.
        Respond with the playstatus or numerical postion of the status from the list.
        """
        prompt = ", ".join(self.play_status_choices.values()) + "\n:"
        while True:
            response = input(prompt).lower()
            if len(response) == 1:
                return self.play_status_choices[response]
            elif response.title() in self.play_status_choices.values():
                return response
            elif response == "":
                return None
            else:
                print("\nInvalid Response")
                continue

    def pick_random_game(self):
        """
        Allows you to pick a play_status to have a random game chosen from. It allows retrying.
        """
        print(
            "\nWhat play status do you want a random game picked from?\nPress Enter to skip."
        )
        play_status = self.play_status_picker()
        if play_status == None:
            return
        choice_list = []
        for game, index in self.games.row_idx.items():
            game_play_status = self.games.get_cell(index, "Play Status").lower()
            if game_play_status == play_status.lower():
                choice_list.append(game)
        # picks random game then removes it from the choice list so it wont show up again during this session
        picked_game = random.choice(choice_list)
        choice_list.pop(choice_list.index(picked_game))
        print(f"\nPicked game with {play_status} status:\n{picked_game}")
        # allows getting another random pick
        while not input(
            "Press Enter to pick another and No for finish.\n:"
        ).lower() in ["no", "n"]:
            if not choice_list:
                print(f"All games with {play_status} have already been picked.\n")
                return
            picked_game = random.choice(choice_list)
            choice_list.pop(choice_list.index(picked_game))
            print(f"\nPicked game with {play_status} status:\n{picked_game}")

    def get_favorite_games_sales(self):
        """
        Gets sale information for games that are at a minimun rating or higher.
        Rating is set up using an input after running.
        """
        # gets favorite games from excel file as a list of dicts
        fav_games = []
        # sets minimum rating to and defaults to 8 if response is blank or invalid
        rating_limit = (
            input("What is the minimum rating for this search? (1-10)\n") or "8"
        )
        if rating_limit.isnumeric():
            rating_limit = int(rating_limit)
        else:
            print("Invalid response - Using 8 instead.")
            rating_limit = 8
        # starts check with progress bar
        print("\nGame Sale Check\n")
        for game, index in tqdm(
            iterable=self.games.row_idx.items(),
            ascii=True,
            unit="games",
            dynamic_ncols=True,
        ):
            my_rating = self.games.get_cell(game, "My Rating")
            if my_rating == None:
                continue
            appid = self.games.get_cell(game, "App ID")
            if my_rating >= rating_limit and appid:
                game_dict = self.get_game_info(appid)
                if not game_dict:
                    continue
                game_dict["my_rating"] = my_rating
                if "on_sale" in game_dict.keys():
                    if game_dict["on_sale"]:
                        fav_games.append(game_dict)
        fav_games = sorted(fav_games, key=lambda i: i["discount"], reverse=True)
        print(
            f"\n{len(fav_games)} Favorite Games with Current Deals in Descending Order:\n"
        )
        for game in fav_games:
            print(f'{game["name"]} - {game["price"]}')
        # save into file
        self.save_json_output(fav_games, "configs/favorite_games.json")

    def view_favorite_games_sales(self):
        """
        Allows viewing different formatted info on the games created during the last run of `get_favorite_games_sales`.
        """
        df = pd.read_json("configs/favorite_games.json")
        print("Do you want to output as excel(1) or csv(2)?")
        output = input()
        if output == "1":
            output = "excel"
        elif output == "2":
            output = "csv"
        else:
            return
        Path("outputs").mkdir(exist_ok=True)
        if output == "excel":
            file_path = "outputs/favorite_games_sales.xlsx"
            df.to_excel(file_path)
            os.startfile(file_path)
        elif output == "csv":
            df.to_csv("outputs/favorite_games_sales.csv")
            folder = os.path.join(self.script_dir, "outputs")
            subprocess.Popen(f'explorer "{folder}"')
        else:
            print("Invalid Resposne")
            return

    def arg_func(self):
        """
        Checks if any arguments were given and runs commands.
        """
        if len(sys.argv) == 1:
            return
        arg = sys.argv[1].lower()
        if arg == "help":
            print("Help:\nrefresh- refreshes steam games")
            print("random- allows getting random picks from games based on play status")
        elif arg == "refresh":
            print("Running refresh")
            self.refresh_steam_games(self.steam_id)
        elif arg == "random":
            self.pick_random_game()
        else:
            print("Invalid Argument Given.")
        input()
        exit()

    def custom_update_game(self):
        """
        Allows updating a game by typing in an as close a possible version of the game name.
        """
        game_name = input("\nWhat game do you want to update?\n")
        game_idx = None
        matched_games = self.lev_dist_matcher(game_name, self.games.row_idx.keys())
        if not matched_games:
            match = matched_games[0]
            if match in self.games.row_idx:
                print(f"Found {match}")
                game_idx = self.games.row_idx[match]
        elif len(matched_games) >= 1:
            games_string = "\n"
            for i, game in enumerate(matched_games):
                games_string += f"{i+1}. {game} | "
            print(games_string[0:-3])
            num = self.ask_for_integer("Type number for game you are looking for.")
            game_idx = self.games.row_idx[matched_games[num - 1]]
        else:
            print("No Match")
            return
        if not game_idx:
            print(f"No Game found matching {game_name}.")
            return
        updated = False
        # sets new hours if a number is given
        hours = input("\nHow many hours have you played?\n")
        if hours.isnumeric():
            self.set_hours_played(game_idx, float(hours))
            print(f"Updated to {hours} Hours")
            updated = True
        else:
            print("Left Hours Played the same.")
        # sets status if a status is given
        status = input("\nWhat is the new Status?\n").title()
        if status in self.play_status_choices.values():
            self.set_play_status(game_idx, status)
            print(f"Updated Play Status to {status}")
            updated = True
        else:
            print("Left Play Status the same.")
        if updated:
            self.set_date_updated(game_idx)
            self.excel.save_excel(backup=False)
        else:
            print("No changes made.")
        response = input("Do you want to update another game? Type yes.\n")
        if response.lower() in ["yes", "yeah", "y"]:
            self.custom_update_game()

    def update_playstation_data(self):
        """
        Opens playstation data json file and web json with latest data
        for manual updating.
        """
        subprocess.Popen(f'notepad "{self.json_path}"')
        webbrowser.open(self.playstation_data_link)
        webbrowser.open(r"https://store.playstation.com/")
        input("\nPress Enter when done.")
        self.check_playstation_json()

    @staticmethod
    def open_log():
        osCommandString = "notepad.exe configs/tracker.log"
        os.system(osCommandString)

    def pick_task(self):
        """
        Allows picking a task to do next using a matching number.
        """
        print("\nWhat do you want to do next?\n")
        choices = [
            {
                "text": "Update Game",
                "func": self.custom_update_game,
            },
            {
                "text": "Pick Random Game",
                "func": self.pick_random_game,
            },
            {
                "text": "Check Steam Deck Game Status",
                "func": lambda: self.steam_deck_check(force_run=True),
            },
            {
                "text": "Add Game",
                "func": self.manually_add_game,
            },
            {
                "text": "Update the Playstation Data",
                "func": self.update_playstation_data,
            },
            {
                "text": "Check Favorite Games Sales",
                "func": self.get_favorite_games_sales,
            },
            {
                "text": "View Favorite Games Sales",
                "func": self.view_favorite_games_sales,
            },
            {
                "text": "Open Log",
                "func": self.open_log,
            },
        ]
        for count, choice in enumerate(choices):
            print(f"{count+1}. {choice['text']}")
        msg = "\nPress Enter without a number to open the excel sheet.\n"
        res = self.ask_for_integer(
            msg,
            num_range=(1, len(choices)),
            allow_blank=True,
        )
        if res == "":
            os.startfile(self.excel.file_path)
            exit()
        # calls the function for the selected choice
        choices[res - 1]["func"]()

    @keyboard_interrupt
    def run(self):
        """
        Main run function.
        """
        self.config_check()
        self.arg_func()
        print("Starting Game Tracker")
        # starts function run with CTRL + C Exit being possible without causing an error
        self.refresh_steam_games(self.steam_id)
        self.steam_deck_check()
        self.check_playstation_json()
        self.output_completion_data()
        self.requests_loop()
        self.pick_task()
        self.excel.open_file_input()


if __name__ == "__main__":
    App = Tracker()
    if not App.ext_terminal:
        # App.view_favorite_games_sales()
        # print(App.get_steam_id('Varnock'))
        # App.steam_deck_check()
        # App.get_game_info(1290000, debug=True)
        pass
    App.run()
