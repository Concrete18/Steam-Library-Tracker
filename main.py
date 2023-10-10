import random, json, os, re, sys, shutil, time
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import datetime as dt

# classes
from classes.steam import Steam
from classes.playstation import Playstation
from classes.utils import Utils, keyboard_interrupt
from classes.statisitics import Stat
from classes.logger import Logger

# my package
from easierexcel import Excel, Sheet


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
        return config
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


class Tracker(Steam, Playstation, Utils):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    ext_terminal = sys.stdout.isatty()  # is True if terminal is external
    title = "Game Library Tracker"
    # config init
    config = setup()
    with open(config) as file:
        data = json.load(file)
    steam_key = data["settings"]["steam_api_key"]
    steam_id = str(data["settings"]["steam_id"])
    vanity_url = data["settings"]["vanity_url"]
    playstation_data_link = data["settings"]["excel_filename"]
    excel_filename = data["settings"]["excel_filename"]
    logging = data["settings"]["logging"]
    name_ignore_list = [string.lower() for string in data["name_ignore_list"]]
    app_id_ignore_list = data["app_id_ignore_list"]

    # logging setup
    if logging:
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
            "User Tags",
            "Notes",
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
    # excel setup
    excel = Excel(excel_filename, use_logging=logging)
    steam = Sheet(excel, sheet_name="Steam", column_name="App ID", options=options)
    playstation = Sheet(
        excel, sheet_name="Playstation", column_name="Name", options=options
    )
    sales = Sheet(excel, sheet_name="Sales", column_name="Name", options=options)
    # sets play status choices for multiple functions
    play_status_choices = {
        "1": "Played",
        "2": "Playing",
        "3": "Waiting",
        "4": "Finished",
        "5": "Endless",
        "6": "Replay",
        "7": "Must Play",
        "8": "Quit",
        "9": "Unplayed",
        "10": "Ignore",
    }
    # misc
    ps_data = Path("configs\playstation_games.json")

    # columns
    excel_columns = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        my_rating_col := "My Rating",
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
        time_played_col := "Time Played",
        hours_played_col := "Hours Played",
        linux_hours_col := "Linux Hours",
        last_play_time_col := "Last Play Time",
        time_to_beat_col := "Time To Beat in Hours",
        prob_comp_col := "Probable Completion",
        store_link_col := "Store Link",
        release_col := "Release Year",
        app_id_col := "App ID",
    ]

    errors = []

    def __init__(self, save) -> None:
        """
        Game Library Tracking Class.
        """
        self.save_to_file = save
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

    def set_title(self, title=None):
        """
        Sets the CLI windows title.
        """
        if title:
            set_title = title
        else:
            set_title = self.title
        os.system("title " + set_title)

    def get_time_to_beat(self, game_name):
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
        self.api_sleeper("time_to_beat")
        try:
            results = HowLongToBeat().search(game_name)
        except:
            for _ in range(3):
                time.sleep(10)
                results = HowLongToBeat().search(game_name)
            return ""
        if not results:
            self.api_sleeper("time_to_beat")
            if game_name.isupper():
                results = HowLongToBeat().search(game_name.title())
            else:
                results = HowLongToBeat().search(game_name.upper())
        time_to_beat = "NF - Error"
        if results is not None and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = best_element.main_extra
            if time_to_beat == 0.0:
                time_to_beat = best_element.main_story
            if time_to_beat == 0.0:
                return "ND - Error"
        return time_to_beat

    def get_steam_review(self, app_id: int, response=None):
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

    def create_save_every_nth(self, save_on_nth=20):
        counter = 0

        def save_every_nth():
            nonlocal counter
            counter += 1
            if counter % save_on_nth == 0:
                self.excel.save(use_print=False, backup=False)
                counter = 0

        return save_every_nth

    def set_release_year(self, app_id, release_year):
        """
        Sets `app_id`'s release year cell to `release_year` if a year is not
        already set.
        """
        cur_val = self.steam.get_cell(app_id, self.release_col)
        if not self.any_is_num(cur_val):
            return self.steam.update_cell(app_id, self.release_col, release_year)

    def set_genre(self, app_id, genre):
        """
        Sets `app_id`'s genre cell to `genre`.
        """
        return self.steam.update_cell(app_id, self.genre_col, genre)

    def set_early_access(self, app_id, value):
        """
        Sets `app_id`'s early access cell to `value`.
        """
        return self.steam.update_cell(app_id, self.ea_col, value)

    def set_publisher(self, app_id, value):
        """
        Sets `app_id`'s publisher cell to `value`.
        """
        return self.steam.update_cell(app_id, self.pub_col, value)

    def set_developer(self, app_id, value):
        """
        Sets `app_id`'s developer cell to `value`.
        """
        return self.steam.update_cell(app_id, self.dev_col, value)

    def set_time_to_beat(self, app_id, time):
        """
        Sets `app_id`'s Time to beat cell to `time_to_beat`.
        """
        cur_val = self.steam.get_cell(app_id, self.time_to_beat_col)
        if not self.any_is_num(cur_val):
            return self.steam.update_cell(app_id, self.time_to_beat_col, time)

    def set_hours_played(self, app_id, hours):
        """
        Sets `app_id`'s Hours Played cell to `hours`.
        """
        return self.steam.update_cell(app_id, self.hours_played_col, hours)

    def set_linux_hours_played(self, app_id, hours):
        """
        Sets `app_id`'s Linux Hours cell to `hours`.
        """
        return self.steam.update_cell(app_id, self.linux_hours_col, hours)

    def set_last_playtime(self, app_id, set_last_playtime):
        """
        Sets `app_id`'s last play time to `set_last_playtime`.
        """
        column = self.last_play_time_col
        return self.steam.update_cell(app_id, column, set_last_playtime)

    def set_time_played(self, app_id, time_played):
        """
        Sets `app_id`'s time played to `time_played`.
        """
        column = self.time_played_col
        return self.steam.update_cell(app_id, column, time_played)

    def set_play_status(self, app_id, status):
        """
        Sets `app_id`'s Play Status cell to `status`.
        """
        return self.steam.update_cell(app_id, self.play_status_col, status)

    def set_date_updated(self, app_id):
        """
        Sets `app_id`'s Date Updated cell to the current date.
        """
        cur_date = dt.datetime.now()
        return self.steam.update_cell(app_id, self.date_updated_col, cur_date)

    def get_store_link(self, app_id):
        """
        Generates a steam store link to the games page using it's `app_id`.
        """
        return f"https://store.steampowered.com/app/{app_id}/"

    def get_name(self, app_id):
        """
        Gets the games name from the excel sheet.
        """
        return self.steam.get_cell(app_id, self.name_col)

    def get_game_info(self, app_id):
        """
        Gets game info with steam api using a `app_id`.
        """
        info_dict = {
            "game_name": "ND - Error",
            self.dev_col: "ND - Error",
            self.pub_col: "ND - Error",
            self.genre_col: "ND - Error",
            self.ea_col: "No",
            self.steam_rev_per_col: "No Reviews",
            self.steam_rev_total_col: "No Reviews",
            self.user_tags_col: "No Tags",
            self.release_col: "No Year",
            "price": "ND - Error",
            "discount": 0.0,
            "on_sale": False,
            "drm_notice": "ND - Error",
            "categories": "ND - Error",
            "ext_user_account_notice": "ND - Error",
        }

        def get_json_desc(data):
            return [item["description"] for item in data]

        app_details = self.get_app_details(app_id)
        if not app_details:
            return info_dict
        # gets games store data
        store_link = self.get_store_link(app_id)
        self.api_sleeper("store_data")
        response = self.request_url(store_link)
        # steam review data
        percent, total = self.get_steam_review(app_id=app_id, response=response)
        info_dict[self.steam_rev_per_col] = percent
        info_dict[self.steam_rev_total_col] = total
        # get user tags
        tags = self.get_steam_user_tags(app_id=app_id, response=response)
        info_dict[self.user_tags_col] = ", ".join(tags)
        # info_dict setup
        if "data" in app_details[str(app_id)].keys():
            game_info = app_details[str(app_id)]["data"]
            keys = game_info.keys()
            # get game name
            if "name" in keys:
                info_dict["game_name"] = game_info["name"]
            # get developer
            if "developers" in keys:
                output = self.create_and_sentence(game_info["developers"])
                if output != "":
                    info_dict[self.dev_col] = output
            # get publishers
            if "publishers" in keys:
                output = self.create_and_sentence(game_info["publishers"])
                if output != "":
                    info_dict[self.pub_col] = output
            # get genre
            if "genres" in keys:
                genres = get_json_desc(game_info["genres"])
                info_dict[self.genre_col] = ", ".join(genres)
                # early access
                if self.ea_col in info_dict[self.genre_col]:
                    info_dict[self.ea_col] = "Yes"
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
                    info_dict["discount"] = float(discount)
                if on_sale:
                    info_dict["on_sale"] = on_sale
            # get linux compat
            if "linux_compat" in keys:
                info_dict["linux_compat"] = game_info["platforms"]["linux"]
            # categories
            if "categories" in keys:
                categories = get_json_desc(game_info["categories"])
                info_dict["categories"] = self.create_and_sentence(categories)
            # drm info
            if "drm_notice" in keys:
                info_dict["drm_notice"] = game_info["drm_notice"]
            # external account
            if "ext_user_account_notice" in keys:
                info_dict["ext_user_account_notice"] = game_info[
                    "ext_user_account_notice"
                ]
            # runs unicode remover on all values
            return {k: self.unicode_remover(v) for k, v in info_dict.items()}
        return info_dict

    def missing_info_check(self, skip_filled=True, check_status=False):
        """
        Loops through games in row_idx and gets missing data for
        time to beat and additional game info from Steam API.

        Use `skip_filled` to skip non blank entries.

        Use `check_status` to only check games with a specific play status.
        """
        check_list = []
        column_list = [
            self.genre_col,
            self.pub_col,
            self.dev_col,
            self.steam_rev_per_col,
            self.steam_rev_total_col,
            self.user_tags_col,
            self.time_to_beat_col,
            self.release_col,
            self.ea_col,
        ]
        # creates checklist
        for app_id in self.steam.row_idx:
            play_status = self.steam.get_cell(app_id, self.play_status_col)
            if check_status:
                if play_status not in [
                    "Unplayed",
                    "Playing",
                    "Played",
                    "Finished",
                    "Quit",
                    "Replay",
                    "Must Play",
                ]:
                    continue
            if skip_filled:
                for column in column_list:
                    cell = self.steam.get_cell(app_id, column)
                    if cell == None and app_id not in check_list:
                        check_list.append(app_id)
                        continue
            else:
                check_list.append(app_id)
        # checks if data should be updated
        missing_data_total = len(check_list)
        auto_run_limit = 50
        if 0 < missing_data_total <= auto_run_limit:
            print(f"\nGames with missing data is within threshold of {auto_run_limit}.")
        elif missing_data_total > auto_run_limit:
            msg = (
                f"\n{missing_data_total} games are missing data."
                "\nDo you want to retrieve it?\n:"
            )
            if not input(msg) in ["yes", "y"]:
                return
        else:
            return
        try:
            # updates missing column data
            cur_itr = 0
            save_every_nth = self.create_save_every_nth()
            games_with_added_data = []
            for app_id in tqdm(
                iterable=check_list,
                ascii=True,
                unit=" games",
                ncols=40,
                dynamic_ncols=True,
            ):
                game_name = self.get_name(app_id)
                games_with_added_data.append(game_name)
                # How long to beat check
                prev_time_to_beat = self.steam.get_cell(app_id, self.time_to_beat_col)
                if not prev_time_to_beat:
                    if time_to_beat := self.get_time_to_beat(game_name) and game_name:
                        self.set_time_to_beat(app_id, time_to_beat)
                steam_info = self.get_game_info(app_id)
                # updates sheet with data found in steam_info
                special_case_col = [self.release_col]
                for key, val in steam_info.items():
                    if key in self.excel_columns and steam_info[key]:
                        if key not in special_case_col:
                            self.steam.update_cell(app_id, key, val)
                # release year
                if steam_info[self.release_col]:
                    year = steam_info[self.release_col]
                    self.set_release_year(app_id, year)
                if self.save_to_file:
                    save_every_nth()
                # title progress percentage
                cur_itr += 1
                progress = cur_itr / missing_data_total * 100
                self.set_title(f"{progress:.2f}% - {self.title}")
            self.set_title()
            print("\nAdded Data for the following games:")
            print(self.create_and_sentence(games_with_added_data))
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            if self.save_to_file:
                self.excel.save()

    @staticmethod
    def decide_play_status(play_status: str, minutes_played: int or float):
        """
        Using time_played and play_status,
        determines what the play_status should change to.
        """
        minutes_played_type = type(minutes_played)
        if minutes_played_type is not float and minutes_played_type is not int:
            return play_status or ""
        if play_status not in ["Played", "Unplayed", "Must Play", None]:
            return play_status
        # play status change
        if minutes_played >= 60:
            play_status = "Playing"
        elif minutes_played >= 30:
            play_status = "Played"
        else:
            if play_status != "Must Play":
                play_status = "Unplayed"
        return play_status

    def name_change_checker(self, name_changes):
        """
        Checks the `name_changes` to see if they contain any
        name changes to possibly fufill.
        """
        name_change_warning_num = 5
        name_changes_total = len(name_changes)
        if name_changes_total == 0:
            return
        elif name_changes_total > name_change_warning_num:
            print(f"\nName Change Total {name_changes_total}")
            print(f"Over Warning Threshold of {name_change_warning_num}")
            return
        print("\nName Changes:")
        for names_dict in name_changes:
            new_name = names_dict["new_name"]
            old_name = names_dict["old_name"]
            print(f'"{old_name}" to "{new_name}"')
        msg = "Do you want to update the above game names?:\n"
        if input(msg).lower() in ["yes", "y"]:
            for names_dict in name_changes:
                app_id = names_dict["app_id"]
                new_name = names_dict["new_name"]
                self.steam.update_cell(app_id, self.name_col, new_name)
            return
        print("Skipping Name Changes")

    def game_check(self, steam_games, sheet_games):
        """
        Checks for new games or game updates from `steam_games` based on `sheet_games`.
        """
        self.num_games_updated = 0
        self.num_games_added = 0
        self.total_session_playtime = 0
        added_games = []
        updated_games = []
        name_changes = []
        save_every_nth = self.create_save_every_nth()
        # game checking
        for game in tqdm(
            iterable=steam_games,
            ascii=True,
            unit=" games",
            ncols=40,
        ):
            game_name, app_id = game["name"], game["appid"]
            # ignore check
            if self.skip_game(game_name, app_id):
                continue
            # name change check
            cur_game_name = self.get_name(app_id)
            if cur_game_name and cur_game_name != game_name:
                msg = f'Name Change: "{cur_game_name}" to "{game_name}"'
                self.tracker.info(msg)
                name_change_dict = {
                    "new_name": game_name,
                    "old_name": cur_game_name,
                    "app_id": app_id,
                }
                name_changes.append(name_change_dict)
            # sets play time earlier so it only needs to be set up once
            minutes_played = game["playtime_forever"]
            time_played = self.convert_time_passed(min=minutes_played)
            linux_minutes_played = ""
            if "playtime_linux_forever" in game.keys():
                linux_minutes_played = game["playtime_linux_forever"]
            # play status
            cur_play_status = self.steam.get_cell(app_id, self.play_status_col)
            play_status = self.decide_play_status(cur_play_status, minutes_played)
            # updates or adds game
            if app_id in sheet_games:
                sheet_games.remove(app_id)
                update_info = self.update_game(
                    app_id=app_id,
                    game_name=game_name,
                    minutes_played=minutes_played,
                    linux_minutes_played=linux_minutes_played,
                    play_status=play_status,
                    time_played=time_played,
                )
                if update_info:
                    updated_games.append(update_info)
            else:
                added_info = self.add_game(
                    game_name=game_name,
                    minutes_played=minutes_played,
                    linux_minutes_played=linux_minutes_played,
                    time_played=time_played,
                    app_id=app_id,
                    play_status=play_status,
                )
                added_games.append(added_info)
        # saves each time the checks count is divisible by num
        if self.save_to_file:
            save_every_nth()
        # prints the total games updated and added
        if 0 < self.num_games_updated < 50:
            print(f"\nGames Updated: {self.num_games_updated}")
            if self.num_games_updated > 1:
                session_time = round(self.total_session_playtime)
                print(f"Last Session Playtime: {session_time} Hours")
            # prints each game that was updated with info
            for game_info in updated_games:
                for line in game_info:
                    print(line)
        # game names changed
        self.name_change_checker(name_changes)
        # games added
        if self.num_games_added:
            print(f"\nGames Added: {self.num_games_added}")
        if self.num_games_added < 10:
            if added_games:
                for game_info in added_games:
                    for line in game_info:
                        print(line)
        elif self.num_games_added < 50:
            print(self.create_and_sentence(added_games))
        else:
            print("Too Many to show.")
        # checks for removed games
        total_removed_games = len(sheet_games)
        if total_removed_games:
            print("\nGames To Be Removed:", len(sheet_games))
            removed_games_names = [self.get_name(app_id) for app_id in sheet_games]
            print(self.create_and_sentence(removed_games_names))
            response = input("\nDo you want to delele all the above games?\n")
            if response.lower() in ["yes", "y"]:
                for app_id in sheet_games:
                    self.steam.delete_row(str(app_id))
        if self.excel.changes_made and self.save_to_file:
            self.excel.save()
        else:
            print("\nNo Steam games were updated or added.")

    def sync_steam_games(self, steam_id):
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        # TODO auto update game data sometimes
        steam_games = self.get_owned_steam_games(self.steam_key, steam_id)
        sheet_games = [int(app_id) for app_id in self.steam.row_idx.keys()]
        if not steam_games:
            print("\nFailed to retrieve Steam Games")
        else:
            if not sheet_games:
                print(f"Starting First Steam Sync")
            print(f"Found {len(steam_games)} Steam Games\n")
            self.game_check(steam_games, sheet_games)
            return
        input()
        exit()

    def skip_game(self, name: str = None, app_id: int = None) -> bool:
        """
        Checks if the item should be ignored based on `name` or `app_id`.

        Returns False if neither are given and
        priortizes checking `app_id` if both are given.

        `Name` check looks for keywords and if the name is in the name_ignore_list.

        `app_id` check looks for the `app_id` in the app_id_ignore_list.
        """
        # return False if name and app_id is not given
        if not any([name, app_id]):
            return False
        # app_id ignore list
        if app_id and int(app_id) in self.app_id_ignore_list:
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

    def update_last_run(self, name):
        """
        Updates json by `name` with the current date.
        """
        date = dt.datetime.now().strftime("%m/%d/%Y")
        self.data["last_runs"][name] = date
        self.save_json_output(self.data, self.config)

    def update_game(
        self,
        app_id,
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
        previous_hours_played = self.steam.get_cell(app_id, self.hours_played_col)
        current_hours_played = self.hours_played(minutes_played)
        current_linux_hours_played = self.hours_played(linux_minutes_played)
        # makes sure hours played is a number
        if previous_hours_played == None or previous_hours_played == "None":
            previous_hours_played = 0
        else:
            previous_hours_played = float(previous_hours_played)
        if not current_hours_played:
            return
        if current_hours_played > previous_hours_played:
            hours_played = current_hours_played - previous_hours_played
            added_time_played = self.convert_time_passed(hr=hours_played)
            self.set_hours_played(app_id, current_hours_played)
            self.set_linux_hours_played(app_id, current_linux_hours_played)
            self.set_last_playtime(app_id, added_time_played)
            self.set_time_played(app_id, time_played)
            self.set_date_updated(app_id)
            self.set_play_status(app_id, play_status)
            self.steam.format_row(app_id)
            self.total_session_playtime += hours_played
            self.num_games_updated += 1
            # updated game logging
            update_info = [
                f"\n > {game_name} updated.",
                f"   Played {added_time_played}",
                f"   Total Playtime: {current_hours_played} Hours.",
            ]
            # logs play time
            msg = f"Playtime: {game_name} played for {added_time_played}"
            if self.logging:
                self.tracker.info(msg)
            return update_info
        return None

    # def manually_add_game(self):
    #     """
    #     Allows manually adding a game by giving the name,
    #     platform and hours played.
    #     """
    #     game_name = input("\nWhat is the name of the game?\n:")
    #     platform = input("\nWhat is the platform is this on?\n:")
    #     platform_names = {
    #         "playstation 5": "PS5",
    #         "ps5": "PS5",
    #         "playstation 4": "PS4",
    #         "ps4": "PS4",
    #         "sw": "Switch",
    #         "uplay": "Uplay",
    #         "gog": "GOG",
    #         "ms store": "MS Store",
    #         "ms": "MS Store",
    #         "microsoft": "MS Store",
    #     }
    #     if platform.lower() in platform_names:
    #         platform = platform_names[platform.lower()]
    #     hours_played = int(input("\nHow many hours have you played it?\n:") or 0)
    #     print("\nWhat Play Status should it have?")
    #     play_status = self.play_status_picker() or "Unset"
    #     minutes_played = hours_played * 60
    #     time_played = self.convert_time_passed(min=minutes_played)
    #     print(f"\nAdded Game:\n{game_name}")
    #     print(f"Platform: {platform}")
    #     print(f"Time Played: {time_played}")
    #     print(f"Play Status: {play_status}")
    #     self.add_game(
    #         game_name=game_name,
    #         play_status=play_status,
    #         platform=platform,
    #         hours_played=hours_played,
    #         time_played=time_played,
    #         save=True,
    #     )
    #     return game_name, minutes_played, play_status

    def add_game(
        self,
        game_name=None,
        minutes_played=None,
        linux_minutes_played=None,
        time_played=None,
        app_id=None,
        play_status=None,
        save_after_add=False,
    ):
        """
        Adds a game with the game_name, hours played using `minutes_played` and `play_status`.

        If save is True, it will save after adding the game.
        """
        play_status = "Unplayed"
        hours_played = ""
        if minutes_played:
            hours_played = self.hours_played(minutes_played)
            # sets play status
            play_status = self.decide_play_status(play_status, minutes_played)
        linux_hours_played = ""
        if linux_minutes_played:
            linux_hours_played = self.hours_played(linux_minutes_played)
        # store link setup
        store_link_hyperlink = ""
        store_link = self.get_store_link(app_id)
        if store_link:
            store_link_hyperlink = f'=HYPERLINK("{store_link}","Store")'
        early_access = "No"
        # indirect_cell setup
        hours = self.steam.indirect_cell(self.prob_comp_col, self.hours_played_col)
        ttb = self.steam.indirect_cell(self.prob_comp_col, self.time_to_beat_col)
        # sets excel column values
        column_info = {
            self.my_rating_col: "",
            self.name_col: game_name,
            self.play_status_col: play_status,
            self.ea_col: early_access,
            self.time_to_beat_col: self.get_time_to_beat(game_name),
            self.prob_comp_col: f'=IFERROR({hours}/{ttb},"Missing Data")',
            self.hours_played_col: hours_played,
            self.linux_hours_col: linux_hours_played,
            self.time_played_col: time_played,
            self.app_id_col: app_id,
            self.store_link_col: store_link_hyperlink,
            self.date_added_col: dt.datetime.now(),
            self.date_updated_col: dt.datetime.now(),
        }
        steam_info = self.get_game_info(app_id)
        if steam_info:
            for column in self.excel_columns:
                if column in steam_info.keys():
                    column_info[column] = steam_info[column]
        self.steam.add_new_line(column_info)
        # logging
        if not hours_played:
            time_played = "no time"
        if self.logging:
            info = f"New Game: Added {game_name} with {time_played} played"
            self.tracker.info(info)
        self.num_games_added += 1
        self.steam.format_row(app_id)
        if save_after_add and self.save_to_file:
            self.excel.save()
        added_info = [
            f"\n > {game_name} added.",
            f"   Total Playtime: {hours_played} Hours.",
        ]
        return added_info

    def play_status_picker(self):
        """
        Shows a list of Play Status's to choose from.
        Respond with the playstatus or numerical postion of the status from the list.
        """
        prompt = self.create_and_sentence(self.play_status_choices.values()) + "\n:"
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

    def get_random_game_name(self, play_status, choice_list=[]):
        """
        Picks random game with the given `play_status` then removes it from the `choice_list` so it wont show up again during this session.
        """
        if not choice_list:
            for app_id in self.steam.row_idx.keys():
                game_play_status = self.steam.get_cell(app_id, self.play_status_col)
                if not game_play_status:
                    continue
                if game_play_status.lower() == play_status.lower():
                    choice_list.append(app_id)
        # picks random game then removes it from the choice list so it wont show up again during this session
        picked_app_id = random.choice(choice_list)
        choice_list.pop(choice_list.index(picked_app_id))
        picked_game_name = self.steam.get_cell(picked_app_id, self.name_col)
        return picked_game_name, choice_list

    def pick_random_game(self):
        """
        Allows you to pick a play_status to have a random game chosen from. It allows retrying.
        """
        print("\nWhat play status do you want a random game picked from?")
        print("Press Enter to skip:")
        play_status = self.play_status_picker()
        if play_status == None:
            return
        picked_game_name, choice_list = self.get_random_game_name(play_status)
        print(f"\nGame: {picked_game_name}")
        # allows getting another random pick
        msg = "\nPress Enter to pick another random game and No to finish:\n"
        while not input(msg).lower() in ["no", "n"]:
            if not choice_list:
                print(f"All games have already been picked.\n")
                return
            picked_game_name, choice_list = self.get_random_game_name(play_status)
            print(f"\nGame: {picked_game_name}")

    def get_favorite_games(self, rating_limit=8):
        """
        gets favorite games from excel file as a list of dicts
        """
        # starts check with progress bar
        print("\nGame Sale Check\n")
        games = []
        for game in tqdm(
            iterable=self.steam.row_idx.keys(),
            ascii=True,
            unit=" games",
            ncols=100,
        ):
            my_rating = self.steam.get_cell(game, self.my_rating_col)
            store_link = self.steam.get_cell(game, "Store Link")
            ttb = self.steam.get_cell(game, "Time To Beat in Hours")
            if my_rating == None:
                continue
            app_id = self.steam.get_cell(game, "App ID")
            if my_rating >= rating_limit and app_id:
                game_info = self.get_game_info(app_id)
                if not game_info or not "on_sale" in game_info.keys():
                    continue
                # create game_dict
                game_dict = {
                    "Date Updated": dt.datetime.now(),
                    "Name": game_info["game_name"],
                    "Discount": game_info["discount"] * 0.01,
                    "Price": game_info["price"],
                    "My Rating": my_rating,
                    self.steam_rev_per_col: game_info[self.steam_rev_per_col],
                    self.steam_rev_total_col: game_info[self.steam_rev_total_col],
                    self.store_link_col: f'=HYPERLINK("{store_link}","Store")',
                    self.time_to_beat_col: ttb,
                    self.user_tags_col: game_info[self.user_tags_col],
                    self.release_col: game_info[self.release_col],
                    self.genre_col: game_info[self.genre_col],
                    self.ea_col: game_info[self.ea_col],
                    self.dev_col: game_info[self.dev_col],
                    self.pub_col: game_info[self.pub_col],
                }
                games.append(game_dict)
        return games

    def update_sales_sheet(self, games):
        """
        Updates the sales sheet with each games info from `games`.
        """
        for game in games:
            name = game["Name"]
            price = game["Price"]
            discount = game["Discount"]
            if name in self.sales.row_idx.keys():
                self.sales.delete_row(name)
            # checks to see if it should skip the game
            skip_checks = [
                name == "Unset",
                "$" not in price,
                discount == 0,
            ]
            if any(skip_checks):
                continue
            self.sales.add_new_line(game)
        self.sales.format_all_cells()
        if self.save_to_file:
            self.excel.save()

    def update_favorite_games_sales(self):
        """
        Gets sale information for games that are at a minimun rating or higher.
        Rating is set up using an input after running.
        """
        # sets minimum rating to and defaults to 8 if response is blank or invalid
        msg = "\nWhat is the minimum rating for this search? (1-10)\n"
        rating_limit = input(msg) or "8"
        if rating_limit.isnumeric():
            rating_limit = int(rating_limit)
        else:
            print("Invalid response - Using 8 instead.")
            rating_limit = 8
        games = self.get_favorite_games(rating_limit)
        # delete old game sales
        cur_rows = [game for game in self.sales.row_idx.keys()].reverse()
        if cur_rows:
            for game in cur_rows:
                self.sales.delete_row(game)
        # get new game sales
        games = self.get_favorite_games()
        total = len(games)
        # prints info
        print(f"\nFound {total} Favorite Game Sales:\n")
        self.update_sales_sheet(games=games)

    def pick_game_to_update(self, games):
        """
        Allows picking game to update playtime and last_updated.
        """
        #
        print("What game did you play last?")
        for count, game in enumerate(games):
            print(f"{count+1}. {game}")
        msg = "\nWhat game do you want to update the last session for?\n"
        num = self.ask_for_integer(
            msg,
            num_range=(1, len(games)),
            allow_blank=True,
        )
        if num == "":
            return False
        # runs chosen function
        chosen_game = games[num - 1]
        game_idx = self.steam.row_idx[chosen_game]
        new_hours = self.ask_for_integer(
            "\nWhat are the new hours played?\n",
            allow_blank=True,
        )
        if new_hours:
            self.set_hours_played(game_idx, float(new_hours))
            print(f"\nUpdated to {new_hours} Hours.")
        self.set_date_updated(game_idx)

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

    def game_library_actions(self):
        """
        Gives a choice of actions for the current game library.
        """
        na_values = [
            "NaN",
            "NF - Error",
            "Invalid Date",
            "ND - Error",
            "No Tags",
            "No Year",
            "No Score",
            "Not Found",
            "No Reviews",
            "Missing Data",
            "Not Enough Reviews",
            "No Publisher",
            "No Developer",
        ]
        df = self.steam.create_dataframe(na_vals=na_values)
        stats = Stat(df)
        # choice picker
        choices = [
            ("Pick Random Game", self.pick_random_game),
            ("Update Favorite Games Sales", self.update_favorite_games_sales),
            ("Sync Playstation Games", self.update_playstation_data),
            ("Calculate Statistics", stats.get_game_statistics),
            # ("Add Game", self.manually_add_game),
            # ("Update All Cell Formatting", self.steam.format_all_cells),
            ("Open Log", self.open_log),
        ]
        msg = "\nEnter the Number for the action you want to do or just press enter to open in Excel.\n"
        if not self.pick_task(choices, msg):
            self.excel.open_excel()

    def show_errors(self):
        """
        Shows errors that occurred if they were added to the errors list.
        """
        error_total = len(self.errors)
        if not error_total:
            return
        print(f"\n{error_total} Errors Occurred:")
        for error in self.errors:
            print(error)

    def fix_app_ids(self):
        """
        Created to fix steam ID's in case they get messed up.
        """
        app_list = self.get_app_list()
        for app_id in self.steam.row_idx:
            name = self.steam.get_cell(app_id, self.name_col)
            correct_app_id = self.get_app_id(name, app_list)
            if app_id and correct_app_id:
                if int(app_id) != int(correct_app_id):
                    print(name, app_id, correct_app_id)
                    if correct_app_id:
                        self.steam.update_cell(app_id, self.app_id_col, correct_app_id)
            else:
                print(name, app_id, correct_app_id)
                self.steam.update_cell(app_id, self.app_id_col, "")
        self.excel.save()

    @keyboard_interrupt
    def run(self):
        """
        Main run function.
        """
        self.config_check()
        print(f"Starting {self.title}")
        self.sync_steam_games(self.steam_id)
        self.missing_info_check()
        self.show_errors()
        self.game_library_actions()


if __name__ == "__main__":
    App = Tracker(save=True)
    App.run()
