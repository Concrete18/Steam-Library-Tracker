import random, json, os, re, sys, hashlib, webbrowser, subprocess, shutil
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import datetime as dt
import pandas as pd

# classes
from classes.helper import Helper, keyboard_interrupt
from classes.statisitics import Stat
from classes.logger import Logger

# my package
from easierexcel import Excel, Sheet

# for local testing
# from classes.excel import Excel, Sheet


def setup():
    """
    Creates the config and excel file if they do not exist.
    """
    all_clear = True
    # config check
    config = Path("configs/config.json")
    if not config.exists():
        config_template = Path("templates/config_template.json")
        shutil.copyfile(config_template, config)
        all_clear = False
    # excel check
    excel = Path("Game Library.xlsx")
    if not excel.exists():
        excel_template = Path("templates/Game_Library_Template.xlsx")
        shutil.copyfile(excel_template, excel)
        all_clear = False
    # exits out of function early if all clear
    if all_clear:
        return
    # instructions
    instructsions = [
        "Open the config and update the following entries:",
        "steam_id",
        "steam_api_key",
        "\nOnce updated run again.",
    ]
    for line in instructsions:
        print(line)
    input("Press Enter to Close.")
    exit()


class Tracker(Helper):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    ext_terminal = sys.stdout.isatty()  # is True if terminal is external

    # config init
    setup()
    config = Path("configs\config.json")
    with open(config) as file:
        data = json.load(file)
    steam_key = data["settings"]["steam_api_key"]
    steam_id = str(data["settings"]["steam_id"])
    vanity_url = data["settings"]["vanity_url"]
    excel_filename = data["settings"]["excel_filename"]
    playstation_data_link = data["settings"]["playstation_data_link"]
    name_ignore_list = [string.lower() for string in data["name_ignore_list"]]
    appid_ignore_list = data["appid_ignore_list"]

    # logging setup
    Log = Logger()
    tracker_log_path = "logs/tracker.log"
    tracker = Log.create_log(name="tracker", log_path=tracker_log_path)
    error_log = Log.create_log(name="base_error", log_path="logs/error.log")

    # class init
    options = {
        "shrink_to_fit_cell": True,
        "header": {"bold": True, "font_size": 16},
        "default_align": "center_align",
        "left_align": [
            "Name",
            "Developers",
            "Publishers",
            "Genre",
        ],
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
    }
    excel = Excel(excel_filename)
    games = Sheet(excel, "Name", sheet_name="Games", options=options)
    # sets play status choices for multiple functions
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
    ps_data = Path("configs\playstation_games.json")

    # columns
    excel_columns = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        my_rating_col := "My Rating",
        metacritic_col := "Metacritic",
        rating_comp_col := "Rating Comparison",
        steam_rev_per_col := "Steam Review Percent",
        steam_rev_total_col := "Steam Review Total",
        name_col := "Name",
        play_status_col := "Play Status",
        platform_col := "Platform",
        dev_col := "Developers",
        pub_col := "Publishers",
        genre_col := "Genre",
        user_tags_col := "User Tags",
        ea_col := "Early Access",
        steam_deck_col := "Steam Deck Status",
        time_played_col := "Time Played",
        hours_played_col := "Hours Played",
        linux_hours_col := "Linux Hours",
        last_play_time_col := "Last Play Time",
        time_to_beat_col := "Time To Beat in Hours",
        prob_comp_col := "Probable Completion",
        store_link_col := "Store Link",
        release_col := "Release Year",
        appid_col := "App ID",
    ]
    # TODO determine width for tqdm here

    def __init__(self) -> None:
        """
        Game Library Tracking Class.
        """
        if not self.steam_id:
            self.update_steam_id()

    def validate_steam_id(self, steam_id):
        """
        Validates a `steam_id`.
        """
        steam_id = str(steam_id)
        pattern = r"^\d{17}$"
        if re.match(pattern, steam_id):
            return True
        else:
            return False

    def validate_steam_key(self, steam_key: str):
        """
        Validates a `steam_key`.
        """
        pattern = r"^\w{32}$"
        if re.match(pattern, steam_key):
            return True
        else:
            return False

    def config_check(self):
        """
        Checks to see if the config data is usable.
        """
        errors = []
        if not self.validate_steam_id(self.steam_id):
            errors.append("Steam ID is Invalid.")
        if not self.validate_steam_key(self.steam_key):
            errors.append("Steam API Key is Invalid.")
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
            self.data["settings"]["steam_id"] = steam_id
            self.save_json_output(self.data, self.config)

    @staticmethod
    def get_profile_username(vanity_url):
        result = False
        if "steamcommunity.com/id" in vanity_url:
            if vanity_url[-1] == "/":
                vanity_url = vanity_url[:-1]
            result = vanity_url.split("/")[-1]
        return result

    def get_steam_id(self, vanity_url):
        """
        Gets a users Steam ID via their `vanity_url` or `vanity_username`.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/ResolveVanityURL/v0001/"
        url = main_url + api_action
        query = {
            "key": self.steam_key,
            "vanityurl": vanity_url,
        }
        response = self.request_url(url, params=query)
        if response:
            data = response.json()["response"]
            if "steamid" in data.keys():
                steam_id = data["steamid"]
                return int(steam_id)
        return False

    def get_time_to_beat(self, game_name):
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
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
        # TODO improve error checking
        if game_name is None or platform is None:
            return "Page Error"
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
        review_score = ""
        main_url = "https://www.metacritic.com/"
        url_vars = f"/game/{platform.lower()}/{game_name.lower()}"
        url = main_url + url_vars
        if debug:
            print(url)
        self.api_sleeper("metacritic")
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
            self.error_log.warning(msg)
            review_score = "Page Error"
        return review_score

    def get_appid(self, game, app_list={}):
        """
        Checks the Steam App list for a game
        and returns its app id if it exists as entered.
        """
        # sets up app_list if it does not exist
        if app_list == {}:
            main_url = "https://api.steampowered.com/"
            api_action = "ISteamApps/GetAppList/v0002/"
            url = main_url + api_action
            query = {"l": "english"}
            response = self.request_url(url, params=query)
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

    def get_steam_review(self, appid: int, response=None):
        """
        Scrapes the games review percent and total reviews from
        the steam store page using `appid` or `store_link`.
        """
        if not response:
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

    def get_steam_user_tags(self, appid: int, response=None):
        """
        ph
        """
        if not response:
            self.api_sleeper("steam_review_scrape")
            store_link = self.get_store_link(appid)
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

    def get_game_info(self, appid):
        """
        Gets game info with steam api using a `appid`.
        """
        info_dict = {
            self.dev_col: "No Data",
            self.pub_col: "No Data",
            self.genre_col: "No Data",
            self.ea_col: "No",
            self.metacritic_col: "No Score",
            self.steam_rev_per_col: "No Reviews",
            self.steam_rev_total_col: "No Reviews",
            self.user_tags_col: "No Tags",
            self.release_col: "No Year",
            "price": "No Data",
            "discount": 0.0,
            "on_sale": "No",
            "linux_compat": "Unsupported",
            "drm_notice": "No Data",
            "categories": "No Data",
            "ext_user_account_notice": "No Data",
        }
        if not appid:
            return info_dict

        def get_json_desc(data):
            return [item["description"] for item in data]

        url = "https://store.steampowered.com/api/appdetails"
        self.api_sleeper("steam_app_details")
        query = {"appids": appid, "l": "english"}
        response = self.request_url(url, params=query)
        if not response:
            return info_dict
        dict = response.json()
        # gets games store data
        self.api_sleeper("get_store_link")
        store_link = self.get_store_link(appid)
        response = self.request_url(store_link)
        # steam review data
        self.api_sleeper("get_steam_review")
        percent, total = self.get_steam_review(appid=appid, response=response)
        info_dict[self.steam_rev_per_col] = percent
        info_dict[self.steam_rev_total_col] = total
        # get user tags
        tags = self.get_steam_user_tags(appid=appid, response=response)
        info_dict[self.user_tags_col] = ", ".join(tags)
        # info_dict setup
        if "data" in dict[str(appid)].keys():
            game_info = dict[str(appid)]["data"]
            keys = game_info.keys()
            # below removed due to bugs
            # info_dict[self.name_col] = game_info["name"]
            # get developer
            if "developers" in keys:
                output = self.word_and_list(game_info["developers"])
                info_dict[self.dev_col] = output
            # get publishers
            if "publishers" in keys:
                output = self.word_and_list(game_info["publishers"])
                info_dict[self.pub_col] = output
            # get genre
            if "genres" in keys:
                genres = get_json_desc(game_info["genres"])
                info_dict[self.genre_col] = ", ".join(genres)
                # early access
                if self.ea_col in info_dict[self.genre_col]:
                    info_dict[self.ea_col] = "Yes"
            # get metacritic
            if self.metacritic_col in keys:
                info_dict[self.metacritic_col] = game_info["metacritic"]["score"]
            # get release year
            if "release_date" in keys:
                release_date = game_info["release_date"]["date"]
                release_date = self.get_year(release_date)
                info_dict[self.release_col] = release_date
            # get price_info
            if "price_overview" in keys:
                price_data = game_info["price_overview"]
                price = price_data["final_formatted"]
                discount = price_data["discount_percent"]
                on_sale = price_data["discount_percent"] > 0
                if price:
                    info_dict["price"] = price
                if discount:
                    info_dict["discount"] = discount
                if on_sale:
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
        return self.games.update_cell(game, self.steam_deck_col, status)

    def set_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Hours Played cell to `hours_played`.
        """
        return self.games.update_cell(game_name, self.hours_played_col, hours_played)

    def set_linux_hours_played(self, game_name, hours_played):
        """
        Sets `game`'s Linux Hours cell to `hours_played`.
        """
        return self.games.update_cell(game_name, self.linux_hours_col, hours_played)

    def set_last_playtime(self, game_name, set_last_playtime):
        """
        Sets `game`'s last play time to `set_last_playtime`.
        """
        column = self.last_play_time_col
        return self.games.update_cell(game_name, column, set_last_playtime)

    def set_time_played(self, game_name, time_played):
        """
        Sets `game`'s time played to `time_played`.
        """
        column = self.time_played_col
        return self.games.update_cell(game_name, column, time_played)

    def set_play_status(self, game_name, play_status):
        """
        Sets `game`'s Play Status cell to `play_status`.
        """
        return self.games.update_cell(game_name, self.play_status_col, play_status)

    def set_date_updated(self, game):
        """
        Sets `game`'s Date Updated cell to the current date.
        """
        return self.games.update_cell(game, self.date_updated_col, dt.datetime.now())

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
            play_status = self.games.get_cell(game_name, self.play_status_col)
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
                column_list = [
                    self.genre_col,
                    self.pub_col,
                    self.dev_col,
                    self.metacritic_col,
                    self.steam_rev_per_col,
                    self.steam_rev_total_col,
                    self.user_tags_col,
                    self.time_to_beat_col,
                    self.release_col,
                    self.ea_col,
                ]
                for column in column_list:
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
                ncols=40,
                dynamic_ncols=True,
            ):
                # How long to beat check
                cur_valid = self.games.get_cell(game_name, self.time_to_beat_col)
                if not cur_valid:
                    time_to_beat = self.get_time_to_beat(game_name)
                    if time_to_beat:
                        self.set_time_to_beat(game_name, time_to_beat)
                # metacritic score check
                cur_valid = self.games.get_cell(game_name, self.metacritic_col)
                if not cur_valid:
                    platform = self.games.get_cell(game_name, self.platform_col)
                    metacritic_score = self.get_metacritic(game_name, platform)
                    if metacritic_score:
                        self.set_metacritic(game_name, metacritic_score)
                # gets steam info if an app id exists
                appid = self.games.get_cell(game_name, self.appid_col)
                if not appid:
                    appid = self.get_appid(game_name)
                    if appid:
                        self.games.update_cell(game_name, self.appid_col, appid)
                steam_info = self.get_game_info(appid)
                # TODO turn into for loop if possible.
                # genre
                if steam_info[self.genre_col]:
                    self.set_genre(game_name, steam_info[self.genre_col])
                    # early access
                    if self.ea_col in steam_info[self.genre_col]:
                        self.set_early_access(game_name, "Yes")
                # release year
                if steam_info[self.release_col]:
                    self.set_release_year(game_name, steam_info[self.release_col])
                # developer
                if steam_info[self.dev_col]:
                    self.set_developer(game_name, steam_info[self.dev_col])
                # publishers
                if steam_info[self.pub_col]:
                    self.set_publisher(game_name, steam_info[self.pub_col])
                # steam review percent
                col = self.steam_rev_per_col
                if col in steam_info.keys():
                    percent = steam_info[col]
                    self.games.update_cell(game_name, col, percent)
                # steam review total
                col = self.steam_rev_total_col
                if col in steam_info.keys():
                    total = steam_info[col]
                    self.games.update_cell(game_name, col, total)
                # steam user tags
                col = self.user_tags_col
                if col in steam_info.keys():
                    tags = steam_info[col]
                    self.games.update_cell(game_name, col, tags)
                # metacritic
                if steam_info[self.metacritic_col]:
                    cur_val = self.games.get_cell(game_name, self.metacritic_col)
                    score = steam_info[self.metacritic_col]
                    # only updates metacritic score if it is not numeric
                    if type(cur_val) is not int:
                        if not cur_val.isnumeric():
                            self.set_metacritic(game_name, score)
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
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url = base_url + api_action
        self.api_sleeper("steam_owned_games")
        query = {
            "key": self.steam_key,
            "steamid": steam_id,
            "l": "english",
            "include_played_free_games": 0,
            "format": "json",
            "include_appinfo": 1,
        }
        response = self.request_url(url, params=query)
        return response.json()["response"]["games"]

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
            status = self.games.get_cell(game, self.play_status_col)
            if status is not None:
                if "Removed | " not in status:
                    removed_status = f"Removed | {status}"
                    self.set_play_status(game, removed_status)
                    self.set_date_updated(game)

    def sync_steam_games(self, steam_id):
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        owned_games = self.get_owned_steam_games(steam_id)
        if owned_games:
            # creates a list of all games so found games can be removed from
            # the list to detemine what was removed/renamed from steam
            removed_games = [
                str(game)
                for game in self.games.row_idx.keys()
                if self.games.get_cell(game, self.platform_col) == "Steam"
            ]
            self.num_games_updated = 0
            self.num_games_added = 0
            added_games = []
            updated_games = []
            # save interval setup
            save_interval = 20
            checks = save_interval
            # game checking
            print(f"Found {len(owned_games)} Steam Games.\n")
            for game in tqdm(
                iterable=owned_games,
                ascii=True,
                unit="games",
                ncols=100,
            ):
                game_name = game["name"]
                appid = game["appid"]
                if self.should_ignore(game_name, appid):
                    continue
                # sets play time eariler so it only needs to be set up once
                minutes_played = game["playtime_forever"]
                time_played = self.convert_time_passed(min=minutes_played)
                hours_played = self.hours_played(minutes_played)
                # linux time
                linux_minutes_played = ""
                if "playtime_linux_forever" in game.keys():
                    linux_minutes_played = game["playtime_linux_forever"]
                cur_play_status = self.games.get_cell(game_name, self.play_status_col)
                # checks if play status should change
                play_status = self.play_status(cur_play_status, hours_played)
                appid = game["appid"]
                if game_name in self.games.row_idx.keys():
                    # removes existing games from the list that will only
                    # include games that have been removed or had a name changed
                    if game_name in removed_games:
                        removed_games.remove(game_name)
                    update_info = self.update_game(
                        game_name=game_name,
                        minutes_played=minutes_played,
                        linux_minutes_played=linux_minutes_played,
                        play_status=play_status,
                        time_played=time_played,
                    )
                    if update_info:
                        updated_games.append(update_info)
                else:
                    self.add_game(
                        game_name=game_name,
                        hours_played=hours_played,
                        linux_minutes_played=linux_minutes_played,
                        time_played=time_played,
                        appid=appid,
                        play_status=play_status,
                    )
                    added_games.append(game_name)
                # saves each time the checks count is divisible by 20 and
                # total changes count is greater then a specific number
                if self.num_games_added > save_interval:
                    if checks % save_interval == 0:
                        checks = save_interval
                        self.excel.save(use_print=False)
                    checks += 1
            # prints the total games updated and added
            if 0 < self.num_games_updated < 50:
                print(f"\nGames Updated: {self.num_games_updated}")
                # prints each game that was updated with info
                for game_info in updated_games:
                    for line in game_info:
                        print(line)
            if 0 < self.num_games_added < 50:
                print(f"\nGames Added: {self.num_games_added}")
                if added_games:
                    # prints each game that was added
                    output = self.word_and_list(added_games)
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

    def check_for_changes(self, ps_data):
        """
        Checks for changes to the json file.
        """
        with open(self.config) as file:
            data = json.load(file)
        previous_hash = data["settings"]["playstation_hash"]
        new_hash = self.hash_file(ps_data)
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
            ncols=100,
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
        url = main_url + action_url
        query = {"nAppID": appid, "l": "english"}
        data = self.request_url(url, params=query)
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
            print(f"\nNext Steam Deck Check in {days_till_check} days.")
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
            ncols=100,
        ):
            if game_name in steam_deck_ignore_list:
                continue
            appid = self.games.get_cell(game_name, self.appid_col)
            if not appid:
                continue
            status = self.steam_deck_compat(appid)
            self.api_sleeper("steam_deck")
            if not status:
                empty_results.append(game_name)
                continue
            if self.set_steam_deck(game_name, status):
                info = f"{game_name} was updated to {status}"
                self.tracker.info(info)
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
            print("No Steam Deck Status Changes.")
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
        if not self.ps_data.exists():
            print("\nPlayStation JSON does not exist.")
            self.ps_data.touch()
            webbrowser.open_new(self.playstation_data_link)
            webbrowser.open(r"https://store.playstation.com/")
            return
        if not self.check_for_changes(self.ps_data):
            return None
        with open(self.ps_data) as file:
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
        time_played=None,
    ):
        """
        Updates the games playtime and play status if they changed.
        """
        # all hours
        previous_hours_played = self.games.get_cell(game_name, self.hours_played_col)
        current_hours_played = self.hours_played(minutes_played)
        current_linux_hours_played = self.hours_played(linux_minutes_played)
        # prevents updating games that are owned on Steam and a console.
        current_platform = self.games.get_cell(game_name, self.platform_col)
        if current_platform != "Steam":
            return
        elif previous_hours_played == None or previous_hours_played == "None":
            previous_hours_played = 0
        else:
            previous_hours_played = float(previous_hours_played)
        if not current_hours_played:
            return
        if current_hours_played > previous_hours_played:
            hours_played = current_hours_played - previous_hours_played
            added_time_played = self.convert_time_passed(hr=hours_played)
            self.set_hours_played(game_name, current_hours_played)
            self.set_linux_hours_played(game_name, current_linux_hours_played)
            self.set_last_playtime(game_name, added_time_played)
            self.set_time_played(game_name, time_played)
            self.set_date_updated(game_name)
            self.set_play_status(game_name, play_status)
            self.games.format_row(game_name)
            self.num_games_updated += 1
            # updated game logging
            overall_time_played = self.convert_time_passed(min=minutes_played)
            update_info = [
                f"\n > {game_name} updated.",
                f"   Added {added_time_played}",
                f"   Total Playtime: {overall_time_played}.",
            ]
            # logs play time
            msg = f"{game_name} played for {added_time_played}"
            self.tracker.info(msg)
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
        minutes_played = hours_played * 60
        time_played = self.convert_time_passed(min=minutes_played)
        print(f"\nAdded Game:\n{game_name}")
        print(f"Platform: {platform}")
        print(f"Time Played: {time_played}")
        print(f"Play Status: {play_status}")
        self.add_game(
            game_name=game_name,
            minutes_played=minutes_played,
            play_status=play_status,
            platform=platform,
            time_played=time_played,
            save=True,
        )
        return game_name, minutes_played, play_status

    def add_game(
        self,
        game_name=None,
        linux_minutes_played=None,
        hours_played=None,
        time_played=None,
        appid=None,
        play_status=None,
        platform="Steam",
        save=False,
    ):
        """
        Adds a game with the game_name, hours played using `minutes_played`, `play_status` and `platform`.

        If save is True, it will save after adding the game.
        """
        play_status = "Unplayed"
        if hours_played:
            # sets play status
            play_status = self.play_status(play_status, hours_played)
        linux_hours_played = ""
        if linux_minutes_played:
            linux_hours_played = self.hours_played(linux_minutes_played)
        # store link setup
        store_link_hyperlink = ""
        store_link = self.get_store_link(appid)
        if store_link:
            store_link_hyperlink = f'=HYPERLINK("{store_link}","Store")'
        # base defaults
        steam_deck_status = "UNKNOWN"
        early_access = "No"
        # sets defaults for consoles
        if platform in ["PS5", "PS4", "Switch"]:
            steam_deck_status = "UNSUPPORTED"
        # easy_indirect_cell setup
        rating_com = self.rating_comp_col
        my_rating = self.games.easy_indirect_cell(rating_com, self.my_rating_col)
        metacritic = self.games.easy_indirect_cell(rating_com, self.metacritic_col)
        prob_compl = self.prob_comp_col
        hours = self.games.easy_indirect_cell(prob_compl, self.hours_played_col)
        ttb = self.games.easy_indirect_cell(prob_compl, self.time_to_beat_col)
        # sets excel column values
        column_info = {
            self.my_rating_col: "",
            self.name_col: game_name,
            self.play_status_col: play_status,
            self.platform_col: platform,
            self.ea_col: early_access,
            self.steam_deck_col: steam_deck_status,
            self.time_to_beat_col: self.get_time_to_beat(game_name),
            self.metacritic_col: self.get_metacritic(game_name, "Steam"),
            self.rating_comp_col: f'=IFERROR(({my_rating}*10)/{metacritic}, "Missing Data")',
            self.prob_comp_col: f'=IFERROR({hours}/{ttb},"Missing Data")',
            self.hours_played_col: hours_played,
            self.linux_hours_col: linux_hours_played,
            self.time_played_col: time_played,
            self.appid_col: appid,
            self.store_link_col: store_link_hyperlink,
            self.date_updated_col: dt.datetime.now(),
            self.date_added_col: dt.datetime.now(),
        }
        steam_info = self.get_game_info(appid)
        if steam_info:
            for column in self.excel_columns:
                if column in steam_info.keys():
                    column_info[column] = steam_info[column]
        self.games.add_new_line(column_info)
        # logging
        if platform == "Steam":
            if not hours_played:
                time_played = "no time"
            info = f"Added {game_name} with {time_played} played"
        else:
            info = f"Added {game_name} on {platform}"
        self.tracker.info(info)
        self.num_games_added += 1
        self.games.format_row(game_name)
        if save:
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
        print("\nWhat play status do you want a random game picked from?")
        print("Press Enter to skip")
        play_status = self.play_status_picker()
        if play_status == None:
            return
        choice_list = []
        for game, index in self.games.row_idx.items():
            game_play_status = self.games.get_cell(index, self.play_status_col).lower()
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
            ncols=100,
        ):
            my_rating = self.games.get_cell(game, self.my_rating_col)
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
        fav_total = len(fav_games)
        print(f"\n{fav_total} Favorite Game Deals in Descending Order:\n")
        for game in fav_games:
            print(f'{game["name"]} - {game["price"]}')
        # save into file
        self.save_json_output(fav_games, "configs/favorite_games.json")

    def view_favorite_games_sales(self):
        """
        Allows viewing different formatted info on the games created during
        the last run of `get_favorite_games_sales`.
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

    def get_games_list(self, steam_id):
        """
        Gets names of games owned by `steam_id`.
        """
        self.api_sleeper("steam_api")
        base_url = "http://api.steampowered.com/"
        api_action = "IPlayerService/GetOwnedGames/v0001/"
        url = base_url + api_action
        query = {
            "key": self.steam_key,
            "steamid": steam_id,
            "include_played_free_games": 0,
            "include_appinfo": 1,
            "format": "json",
            "l": "english",
        }
        response = self.request_url(url, params=query)
        if response:
            if "games" in response.json()["response"].keys():
                game_list = []
                for item in response.json()["response"]["games"]:
                    game_name = item["name"]
                    game_list.append(game_name)
                return game_list
        return False

    def create_game_lists(self, steam_ids):
        """
        Creates a list containing a list each of the profiles games entered using the get_games_owned Function.
        """
        game_lists = []
        valid_users = []
        for id in steam_ids:
            games = self.get_games_list(id)
            if games:
                game_lists.append(games)
                valid_users.append(id)
        return game_lists, valid_users

    @staticmethod
    def find_games_in_common(games_list):
        """
        Finds the games in common from each `games_list`.
        """
        base_list = set(games_list[0])
        for game_list in games_list:
            base_list &= set(game_list)
        return base_list

    def find_shared_games(self, steam_ids=[]):
        """
        Finds all of the Steam games in common via Steam ID's given.

        If `steam_ids` is unused, it will ask for Steam ID's for the
        shared games check.
        """
        get_input = True
        if steam_ids:
            get_input = False
        # adds current user's steam id
        steam_ids.append(self.steam_id)
        if get_input:
            steam_id = "init"
            num = 1
            while steam_id:
                msg = f"\nEnter Steam ID {num}:\n"
                steam_id = input(msg)
                if steam_id:
                    if self.validate_steam_id(steam_id):
                        print("\nInvalid Steam ID.\nTry Again.")
                    else:
                        steam_ids.append(steam_id)
                        num += 1
        # steam_ids.append(76561197969291006)
        # steam_ids.append(76561198088659293)
        if len(steam_ids) < 2:
            print("Not enough Steam ID's were given.")
        print("Finding Games in Common.")
        game_lists, valid_users = self.create_game_lists(steam_ids)
        tot_users = len(valid_users)
        common_games = self.find_games_in_common(game_lists)
        tot_com = len(common_games)
        print(f"Found {tot_com} Games in common from {tot_users} users.")
        common_games_str = self.word_and_list(common_games)
        print(f"\nGames in Common:\n{common_games_str}")

    def arg_func(self):
        """
        Checks if any arguments were given and runs commands.
        """
        if len(sys.argv) == 1:
            return
        arg = sys.argv[1].lower()
        if arg == "help":
            print("Help:\nSync-Syncs steam games")
            print("random-allows getting random picks from games based on play status")
        elif arg == "refresh":
            print("Running Sync")
            self.sync_steam_games(self.steam_id)
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
        total_matches = len(matched_games)
        if total_matches == 1:
            match = matched_games[0]
            if match in self.games.row_idx:
                print(f"Found {match}.")
                game_idx = self.games.row_idx[match]
        elif total_matches >= 1:
            games_string = "\n"
            for i, game in enumerate(matched_games):
                games_string += f"{i+1}. {game} | "
            print(games_string[0:-3])
            num = self.ask_for_integer("Type number for game you are looking for.\n")
            game_idx = self.games.row_idx[matched_games[num - 1]]
        else:
            print(f"No Game found matching {game_name}.")
            return
        updated = False
        # sets new hours if a number is given
        print("\nHow many hours have you played?")
        msg = "Add a + before the number to add that to the current total.\n"
        hours = input(msg)
        if hours.isnumeric():
            # replaces current hours with new hours
            self.set_hours_played(game_idx, float(hours))
            print(f"\nUpdated to {hours} Hours.")
            updated = True
        if added_hours := re.search(r"\+\d+", hours).group(0):
            # adds hours to current hours
            added_hours = float(added_hours.replace("+", ""))
            cur_hours = self.games.get_cell(game_name, self.hours_played_col)
            new_hours = cur_hours + added_hours
            self.set_hours_played(game_idx, float(new_hours))
            print(f"Updated to {new_hours} Hours.")
            updated = True
        else:
            print("Left Hours Played the same.")
        # sets status if a status is given
        status = input("\nWhat is the new Status?\n").title()
        if status in self.play_status_choices.values():
            self.set_play_status(game_idx, status)
            print(f"Updated Play Status to {status}.")
            updated = True
        else:
            print("Left Play Status the same.")
        if updated:
            self.set_date_updated(game_idx)
            self.excel.save(backup=False)
        else:
            print("No changes made.")
        response = input("Do you want to update another game?\n")
        if response.lower() in ["yes", "yeah", "y"]:
            self.custom_update_game()

    def update_playstation_data(self):
        """
        Opens playstation data json file and web json with latest data
        for manual updating.
        """
        subprocess.Popen(f'notepad "{self.ps_data}"')
        webbrowser.open(self.playstation_data_link)
        webbrowser.open(r"https://store.playstation.com/")
        input("\nPress Enter when done.")
        self.check_playstation_json()

    def open_log(self):
        osCommandString = f"notepad.exe {self.tracker_log_path}"
        os.system(osCommandString)

    def pick_task(self, choices, msg=None, repeat=True):
        """
        Allows picking a task to do next using a matching number.
        """
        ext_terminal = sys.stdout.isatty()
        if not ext_terminal:
            print("\nSkipping Task Picker.\nInput can't be used.")
            return False
        if not msg:
            msg = "\nWhat do you want to do?\n"
        print(msg)
        for count, (choice, action) in enumerate(choices):
            print(f"{count+1}. {choice}")
        print("Enter only to Open Excel")
        msg = "\nEnter the Number for the corresponding action.\n"
        num = self.ask_for_integer(
            msg,
            num_range=(1, len(choices)),
            allow_blank=True,
        )
        if num == "":
            return False
        # runs chosen function
        choice_num = num - 1
        choices[choice_num][1]()
        if repeat:
            self.pick_task(choices, msg, repeat)
        return True

    def extra_actions(self):
        """
        Gives a choice of less less used actions
        """
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
        choices = [
            ("Get Games in Common", self.find_shared_games),
            ("Sync Steam Deck Game Status", self.steam_deck_check),
            ("Get Favorite Games Sales", self.get_favorite_games_sales),
            ("View Favorite Games Sales", self.view_favorite_games_sales),
            ("Calculate Statistics", stats.get_game_statistics),
            ("Update All Cell Formatting", self.games.format_all_cells),
            ("Exit", self.excel.open_file_input),
        ]
        if not self.pick_task(choices):
            close_in_seconds = 5
            print(f"Opening Excel File then closing in {close_in_seconds}.")
            self.excel.open_excel()
            time.sleep(close_in_seconds)

    def game_library_actions(self):
        """
        Gives a choice of actions for the current game library.
        """
        # choice picker
        choices = [
            ("Update Game", self.custom_update_game),
            ("Add Game", self.manually_add_game),
            ("Sync Playstation Games", self.update_playstation_data),
            ("Pick Random Game", self.pick_random_game),
            ("Open Log", self.open_log),
            ("Extra Choices", self.extra_actions),
            ("Exit", exit),
        ]
        msg = "\nEnter the Number for the action you or nothing to open in Excel.\n"
        if not self.pick_task(choices, msg):
            self.excel.open_excel()

    @keyboard_interrupt
    def run(self):
        """
        Main run function.
        """
        self.config_check()
        self.arg_func()
        print("Starting Game Tracker")
        # runs script with CTRL + C clean program end
        self.sync_steam_games(self.steam_id)
        if self.should_run_steam_deck_update():
            self.steam_deck_check()
        self.check_playstation_json()
        self.missing_info_check()
        self.game_library_actions()


if __name__ == "__main__":
    App = Tracker()
    App.run()
    # val = App.get_steam_user_tags(appid=1229490)
    # print(val)
