import random, time, json, os, re, sys, hashlib, webbrowser, subprocess
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import datetime as dt
import pandas as pd

# classes
from classes.excel import Excel, Sheet
from classes.helper import Helper, keyboard_interrupt
from classes.statisitics import Stat


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
    vanity_url = data["settings"]["vanity_url"]
    excel_filename = data["settings"]["excel_filename"]
    playstation_data_link = data["settings"]["playstation_data_link"]
    name_ignore_list = [string.lower() for string in data["name_ignore_list"]]
    appid_ignore_list = data["appid_ignore_list"]
    # class init
    options = {
        "shrink_to_fit_cell": True,
        "default_align": "center_align",
        "header": {"bold": True, "font_size": 16},
        "light_grey_fill": ["Rating Comparison", "Probable Completion"],
        "percent": [
            "%",
            "Percent",
            "Discount",
            "Rating Comparison",
            "Probable Completion",
        ],
        "currency": ["Price", "MSRP", "Cost"],
        "integer": ["App ID", "Number", "Release Year"],
        "count_days": ["Days Till Release"],
        "date": ["Last Updated", "Date"],
        "decimal": ["Hours Played", "Linux Hours", "Time To Beat in Hours"],
        "left_align": [
            "Name",
            "Developers",
            "Publishers",
            "Genre",
        ],
    }
    excel = Excel(excel_filename, log_file="configs/excel.log")
    games = Sheet(excel, "Name", sheet_name="Games", options=options)
    # api call logger
    play_status_choices = {
        "1": "Played",
        "2": "Playing",
        "3": "Waiting",
        "4": "Finished",
        "5": "Endless",
        "6": "Must Play",
        "7": "Quit",
        "8": "Unplayed",
        "9": "Ignore",
    }

    # misc
    ps_json = Path("configs\playstation_games.json")
    # columns
    to_check = [
        genre_col := "Genre",
        pub_col := "Publishers",
        dev_col := "Developers",
        metacritic_col := "Metacritic",
        steam_rev_per_col := "Steam Review Percent",
        steam_rev_total_col := "Steam Review Total",
        time_to_beat_col := "Time To Beat in Hours",
        release_col := "Release Year",
        ea_col := "Early Access",
    ]

    def __init__(self) -> None:
        """
        ph
        """
        if not self.steam_id:
            self.update_steam_id()

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

    def update_steam_id(self):
        """
        Updates the steam id in the config using the given vanity url if present.
        """
        if not self.vanity_url:
            raise "Steam ID and Vanity URL is blank. Please enter at one of them."
        steam_id = self.get_steam_id(self.vanity_url)
        if steam_id:
            pass
            self.data["settings"]["steam_id"] = steam_id
            self.save_json_output(self.data, self.config)

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

    def get_steam_review(self, appid: int):
        """
        Scrapes the games review percent and total reviews from
        the steam store page using `appid` or `store_link`.
        """
        self.api_sleeper("steam_review_scrape")
        store_link = self.get_store_link(appid)
        response = self.request_url(store_link)
        soup = BeautifulSoup(response.text, "html.parser")
        hidden_review_class = "nonresponsive_hidden responsive_reviewdesc"
        results = soup.find_all(class_=hidden_review_class)
        if len(results) == 1:
            text = results[0].text.strip()
        elif len(results) > 1:
            text = results[1].text.strip()
        else:
            return "No Reviews", "No Reviews"
        parsed_data = text[2:26].split("% of the ")
        # get percent
        review_perc = parsed_data[0]
        if review_perc.isnumeric():
            if review_perc == "100":
                percent = 1
            else:
                percent = float(f".{review_perc}")
        else:
            percent = "Not Enough Reviews"
        # get total
        if len(parsed_data) > 1:
            cleaned_num = parsed_data[1].replace(",", "")
            total = int(re.search(r"\d+", cleaned_num).group())
        else:
            total = "No Reviews"
        return percent, total

    def get_game_info(self, appid, game_name=None):
        """
        Gets game info with steam api using a `appid`.
        """
        info_dict = {
            "developers": "No Data",
            "publishers": "No Data",
            "genre": "No Data",
            "early_access": "No",
            "metacritic": "No Data",
            "steam_review_percent": "No Reviews",
            "steam_review_total": "No Reviews",
            "release_date": "No Year",
            "price": "No Data",
            "discount": "No Data",
            "on_sale": "No Data",
            "linux_compat": "Unsupported",
            "drm_notice": "No Data",
            "categories": "No Data",
            "ext_user_account_notice": "No Data",
        }
        if not appid:
            return info_dict

        def get_json_desc(data):
            return [item["description"] for item in data]

        main_url = "https://store.steampowered.com/"
        api_action = "api/appdetails"
        url_vars = f"?appids={appid}&l=english"
        url = main_url + api_action + url_vars
        self.api_sleeper("steam_app_details")
        response = self.request_url(url)
        if not response:
            return info_dict
        dict = response.json()
        # steam review data
        percent, total = self.get_steam_review(appid=appid)
        info_dict["steam_review_percent"] = percent
        info_dict["steam_review_total"] = total
        # info_dict setup
        if "data" in dict[str(appid)].keys():
            game_info = dict[str(appid)]["data"]
            keys = game_info.keys()
            info_dict["name"] = game_info["name"]
            # get developer
            if "developers" in keys:
                output = self.word_and_list(game_info["developers"])
                info_dict["developers"] = output
            # get publishers
            if "publishers" in keys:
                output = self.word_and_list(game_info["publishers"])
                info_dict["publishers"] = output
            # get genre
            if "genres" in keys:
                genres = get_json_desc(game_info["genres"])
                info_dict["genre"] = self.word_and_list(genres)
                # early access
                # TODO does not update when changed
                if "Early Access" in info_dict["genre"]:
                    info_dict["early_access"] = "Yes"
            # get metacritic
            if "metacritic" in keys:
                info_dict["metacritic"] = game_info["metacritic"]["score"]
            # get release year
            if "release_date" in keys:
                release_date = game_info["release_date"]["date"]
                release_date = self.get_year(release_date)
                info_dict["release_date"] = release_date
            # get price_info
            if "price_overview" in keys:
                price_data = game_info["price_overview"]
                price = price_data["final_formatted"]
                discount = price_data["discount_percent"]
                on_sale = price_data["discount_percent"] > 0
                info_dict["price"] = price
                info_dict["discount"] = discount
                info_dict["on_sale"] = on_sale
            # get linux compat
            if "linux_compat" in keys:
                info_dict["linux_compat"] = game_info["platforms"]["linux"]
            # categories
            if "categories" in keys:
                categories = get_json_desc(game_info["categories"])
                info_dict["categories"] = self.word_and_list(categories)
            # drm info
            if "drm_notice" in keys:
                info_dict["drm_notice"] = game_info["drm_notice"]
            # external account
            if "ext_user_account_notice" in keys:
                info_dict["ext_user_account_notice"] = game_info[
                    "ext_user_account_notice"
                ]
            # runs unicode remover on all values
            info_dict = {k: self.unicode_remover(v) for k, v in info_dict.items()}
            return info_dict
        return info_dict

    def set_release_year(self, game, release_year):
        """
        Sets `game`'s release year cell to `release_year`.
        """
        return self.games.update_cell(game, self.release_col, release_year)

    def set_genre(self, game, genre):
        """
        Sets `game`'s genre cell to `genre`.
        """
        return self.games.update_cell(game, self.genre_col, genre)

    def set_early_access(self, game, value):
        """
        Sets `game`'s early access cell to `value`.
        """
        return self.games.update_cell(game, self.ea_col, value)

    def set_publisher(self, game, value):
        """
        Sets `game`'s publisher cell to `value`.
        """
        return self.games.update_cell(game, self.pub_col, value)

    def set_developer(self, game, value):
        """
        Sets `game`'s developer cell to `value`.
        """
        return self.games.update_cell(game, self.dev_col, value)

    def set_metacritic(self, game, score):
        """
        Sets `game`'s metacritic score to `score`.
        """
        return self.games.update_cell(game, self.metacritic_col, score)

    def set_time_to_beat(self, game, time_to_beat):
        """
        Sets `game`'s Time to beat cell to `time_to_beat`.
        """
        return self.games.update_cell(game, self.time_to_beat_col, time_to_beat)

    def set_steam_deck(self, game, status):
        """
        Sets `game`'s Steam Deck Status to `status`.
        """
        return self.games.update_cell(game, "Steam Deck Status", status)

    def set_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Hours Played cell to `hours_played`.
        """
        return self.games.update_cell(game_name, "Hours Played", hours_played)

    def set_linux_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Linux Hours cell to `hours_played`.
        """
        return self.games.update_cell(game_name, "Linux Hours", hours_played)

    def set_play_status(self, game_name, play_status):
        """
        Sets `game`'s Play Status cell to `play_status`.
        """
        return self.games.update_cell(game_name, "Play Status", play_status)

    def set_date_updated(self, game):
        """
        Sets `game`'s Date Updated cell to the current date.
        """
        return self.games.update_cell(game, "Date Updated", dt.datetime.now())

    def get_store_link(self, appid):
        """
        Generates a steam store link to the games page using it's `appid`.
        """
        if not appid or appid == "None":
            return False
        return f"https://store.steampowered.com/app/{appid}/"

    def missing_info_check(self, skip_filled=1, check_status=0):
        """
        Loops through games in row_idx and gets missing data for
        time to beat, Metacritic score and additional game info from Steam API.

        Use `skip_filled` to skip non blank entries.

        Use `check_status` to opnly check games with a with specific play status.
        """
        # creates checklist
        check_list = []
        for game_name in self.games.row_idx:
            play_status = self.games.get_cell(game_name, "Play Status")
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
                    cell = self.games.get_cell(game_name, column)
                    if cell == None and game_name not in check_list:
                        check_list.append(game_name)
                        continue
            else:
                check_list.append(game_name)
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
                cur_valid = self.games.get_cell(game_name, self.time_to_beat_col)
                if not cur_valid:
                    time_to_beat = self.get_time_to_beat(game_name)
                    if time_to_beat != None:
                        self.set_time_to_beat(game_name, time_to_beat)
                # metacritic score check
                cur_valid = self.games.get_cell(game_name, self.metacritic_col)
                if not cur_valid:
                    platform = self.games.get_cell(game_name, "Platform")
                    metacritic_score = self.get_metacritic(game_name, platform)
                    if metacritic_score != None:
                        self.set_metacritic(game_name, metacritic_score)
                # gets steam info if an app id exists
                appid = self.games.get_cell(game_name, "App ID")
                if not appid:
                    appid = self.get_appid(game_name)
                    if appid:
                        self.games.update_cell(game_name, "App ID", appid)
                steam_info = self.get_game_info(appid, game_name)
                # genre
                if steam_info["genre"]:
                    self.set_genre(game_name, steam_info["genre"])
                    # early access
                    if "Early Access" in steam_info["genre"]:
                        self.set_early_access(game_name, "Yes")
                    else:
                        self.set_early_access(game_name, "No")
                else:
                    self.set_genre(game_name, "No Genre")
                    self.set_early_access(game_name, "Unknown")
                # release year
                if steam_info["release_date"]:
                    self.set_release_year(game_name, steam_info["release_date"])
                else:
                    self.set_release_year(game_name, "No Year")
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
                # steam review percent
                col = self.steam_rev_per_col
                if "steam_review_percent" in steam_info.keys():
                    percent = steam_info["steam_review_percent"]
                    self.games.update_cell(game_name, col, percent)
                else:
                    if not self.games.get_cell(game_name, col):
                        self.games.update_cell(game_name, col, "No Reviews")
                # steam review total
                col = self.steam_rev_total_col
                if "steam_review_total" in steam_info.keys():
                    total = steam_info["steam_review_total"]
                    self.games.update_cell(game_name, col, total)
                else:
                    if not self.games.get_cell(game_name, col):
                        self.games.update_cell(game_name, col, "No Reviews")
                # metacritic
                if steam_info["metacritic"]:
                    self.set_metacritic(game_name, steam_info["metacritic"])
                else:
                    if not self.games.get_cell(game_name, self.metacritic_col):
                        self.set_metacritic(game_name, "No Score")
                running_interval -= 1
                if running_interval == 0:
                    running_interval = save_interval
                    self.excel.save(use_print=False, backup=False)
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            self.excel.save()

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
        Gets the games owned by the given `steam_id`.
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

    def update_removed_games(self, removed_games):
        """
        Prints the games that were removed from steam and updates their
        play status and date updated so they are easier to find.
        The games are not removed in case the steam database changed the games
        name so you can keep the data you had on from the original entry.
        """
        removed_games_str = self.word_and_list(removed_games)
        print(f"\nUnaccounted Steam games:\n{removed_games_str}")
        for game in removed_games:
            status = self.games.get_cell(game, "Play Status")
            if status is not None:
                if "Removed | " not in status:
                    removed_status = f"Removed | {status}"
                    self.set_play_status(game, removed_status)
                    self.set_date_updated(game)

    def refresh_steam_games(self, steam_id):
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        response = self.get_owned_steam_games(steam_id)
        if response:
            # creates a list of all games so found games can be removed and the
            # list can be used later
            removed_games = [
                str(game)
                for game in self.games.row_idx.keys()
                if self.games.get_cell(game, "Platform") == "Steam"
            ]
            self.total_games_updated = 0
            self.total_games_added = 0
            self.added_games = []
            checks = 0
            updated_games = []
            owned_games = response.json()["response"]["games"]
            print(f"Found {len(owned_games)} Steam Games\n")
            for game in tqdm(
                iterable=owned_games,
                ascii=True,
                unit="games",
                dynamic_ncols=True,
            ):
                checks += 1
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
                    # removes existing games from the list that will only
                    # include games that have been removed or had a name changed
                    if game_name in removed_games:
                        removed_games.remove(game_name)
                    update_info = self.update_game(
                        game_name,
                        minutes_played,
                        linux_minutes_played,
                        play_status,
                    )
                    if update_info:
                        updated_games.append(update_info)
                else:
                    self.add_game(
                        game_name,
                        minutes_played,
                        linux_minutes_played,
                        appid,
                        play_status,
                    )
                # saves each time the checks count is divisible by 20
                if checks % 20 == 0:
                    self.excel.save(use_print=False)
            # prints the total games updated and added
            if 0 < self.total_games_updated < 50:
                print(f"\nGames Updated: {self.total_games_updated}")
                # prints each game that was updated with info
                for game_info in updated_games:
                    for line in game_info:
                        print(line)
            if 0 < self.total_games_added < 50:
                print(f"\nGames Added: {self.total_games_added}")
                if self.added_games:
                    # prints each game that was added
                    output = self.word_and_list(self.added_games)
                    print(output)
            if self.excel.changes_made:
                self.excel.save()
            else:
                print("\nNo Steam games were updated or added.")
            if removed_games:
                self.update_removed_games(removed_games)

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

    def check_for_changes(self, ps_json):
        """
        Checks for changes to the json file.
        """
        with open(self.config) as file:
            data = json.load(file)
        previous_hash = data["settings"]["playstation_hash"]
        new_hash = self.hash_file(ps_json)
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
            self.excel.save()

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
        date = dt.datetime.now().strftime("%m/%d/%Y")
        self.data["last_runs"][name] = date
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
        data = self.request_url(url)
        if not data:
            return False
        categories = {
            0: "UNKNOWN",
            1: "UNSUPPORTED",
            2: "PLAYABLE",
            3: "VERIFIED",
        }
        results = data.json()["results"]
        if not results:
            return False
        category_id = results["resolved_category"]
        return categories[category_id]

    def should_run_steam_deck_update(self):
        """
        Returns True if the steam_deck_check function should run.

        Checks if enough time has passed since the last run.
        """
        last_check_string = self.data["last_runs"]["steam_deck_check"]
        last_check = self.string_to_date(last_check_string)
        days_since = self.days_since(last_check)
        check_freq = self.data["settings"]["steam_deck_check_freq"]
        if days_since < check_freq:
            days_till_check = check_freq - days_since
            print(f"\nNext Steam Deck Check in {days_till_check} days")
            return False
        return True

    def steam_deck_check(self):
        """
        Checks steam_deck.txt and updates steam deck status with the new info.
        """
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
            if empty_results:
                print("\nThe following Games failed to retrieve data.")
                output = self.word_and_list(empty_results)
                print(output)
            self.excel.save()
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
        self.excel.save()

    def check_playstation_json(self):
        """
        Checks `playstation_games.json` to find out if it is newly updated so
        it can add the new games to the sheet.
        """
        # checks if json exists
        if not self.ps_json.exists():
            print("PlayStation Json does not exist.")
            self.ps_json.touch()
            webbrowser.open_new(self.playstation_data_link)
            return None
        if not self.check_for_changes(self.ps_json):
            # TODO add log
            return None
        with open(self.ps_json) as file:
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
        if not current_hours_played:
            return
        if current_hours_played > previous_hours_played:
            self.set_hours_played(game_name, current_hours_played)
            self.set_linux_hours_played(game_name, current_linux_hours_played)
            self.set_date_updated(game_name)
            self.set_play_status(game_name, play_status)
            self.games.format_row(game_name)
            self.total_games_updated += 1
            # updated game logging
            hours_played = current_hours_played - previous_hours_played
            added_time_played = self.convert_time_passed(hours_played * 60)
            overall_time_played = self.convert_time_passed(minutes_played)
            update_info = [
                f"\n > {game_name} updated.",
                f"   Added {added_time_played}",
                f"   Total Playtime: {overall_time_played}.",
            ]
            # logs play time
            msg = f"{game_name} played for {added_time_played}"
            self.logger.info(msg)
            return update_info
        return None

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
        # sets excel column values
        column_info = {
            "My Rating": "",
            "Name": game_name,
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
            "Date Updated": dt.datetime.now(),
            "Date Added": dt.datetime.now(),
        }
        steam_info = self.get_game_info(appid, game_name)
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
        # TODO change to dict with name and appid
        self.added_games.append(game_name)
        self.total_games_added += 1
        self.games.format_row(game_name)
        if save:
            print("saved")
            self.excel.save()

    def play_status_picker(self):
        """
        Shows a list of Play Status's to choose from.
        Respond with the playstatus or numerical postion of the status from the list.
        """
        prompt = self.word_and_list(self.play_status_choices.values()) + "\n:"
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
                game_dict = self.get_game_info(appid, game)
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
            self.excel.save(backup=False)
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
        subprocess.Popen(f'notepad "{self.ps_json}"')
        webbrowser.open(self.playstation_data_link)
        webbrowser.open(r"https://store.playstation.com/")
        input("\nPress Enter when done.")
        self.check_playstation_json()

    @staticmethod
    def open_log():
        osCommandString = "notepad.exe configs/tracker.log"
        os.system(osCommandString)

    def pick_task(self, choices):
        """
        Allows picking a task to do next using a matching number.
        """
        print("\nWhat do you want to do next?\n")
        for count, (choice, action) in enumerate(choices):
            print(f"{count+1}. {choice}")
        msg = "\nPress Enter without a number to open the excel sheet.\n"
        num = self.ask_for_integer(
            msg,
            num_range=(1, len(choices)),
            allow_blank=True,
        )
        if num == "":
            os.startfile(self.excel.file_path)
            exit()
        # runs chosen function
        choice_num = num - 1
        choices[choice_num][1]()

    @keyboard_interrupt
    def run(self):
        """
        Main run function.
        """
        self.config_check()
        self.arg_func()
        print("Starting Game Tracker")
        # runs script with CTRL + C clean program end
        self.refresh_steam_games(self.steam_id)
        if self.should_run_steam_deck_update():
            self.steam_deck_check()
        self.check_playstation_json()
        self.missing_info_check()
        # statistics setup
        na_values = [
            "No Data",
            "Page Error",
            "No Score",
            "Not Found",
            "No Reviews",
            "No Publisher",
            "No Developer",
            "Invalid Date",
            "No Year",
        ]
        df = self.games.create_dataframe(na_vals=na_values)
        stats = Stat(df)

        # TODO remove below when done testing statistics
        if not self.ext_terminal:
            stats.get_game_statistics()
            input()
            exit()

        # choice picker
        choices = [
            ("Add Game", self.manually_add_game),
            ("Update Game", self.custom_update_game),
            ("Get Statistics", stats.get_game_statistics),
            ("Check Steam Deck Game Status", self.steam_deck_check),
            ("Pick Random Game", self.pick_random_game),
            ("Update the Playstation Data", self.update_playstation_data),
            ("Check Favorite Games Sales", self.get_favorite_games_sales),
            ("View Favorite Games Sales", self.view_favorite_games_sales),
            ("Update All Cell Formatting", self.games.format_all_cells),
            ("Open Log", self.open_log),
        ]
        self.pick_task(choices)
        self.excel.open_file_input()


if __name__ == "__main__":
    App = Tracker()
    App.run()
