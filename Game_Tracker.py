import random, time, json, os, re, sys, hashlib, webbrowser, subprocess
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import datetime as dt
import pandas as pd

# classes
from classes.excel import Excel, Sheet
from classes.logger import Logger
from classes.helper import Helper


class Tracker(Logger, Helper):

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
    last_run = data["settings"]["last_run"]
    ignore_list = [string.lower() for string in data["ignore_list"]]
    # class init
    excel = Excel(excel_filename)
    games = Sheet(excel, "Game Name", sheet_name="Games")
    # current date and time setup
    cur_date = dt.datetime.now()
    excel_date = f"=DATE({cur_date.year}, {cur_date.month}, {cur_date.day})+TIME({cur_date.hour},{cur_date.minute},0)"
    # api call logger
    invalid_months = []
    play_status_choices = {
        "1": "Played",
        "2": "Playing",
        "3": "Waiting",
        "4": "Finished",
        "5": "Quit",
        "6": "Unplayed",
        "7": "Ignore",
        "8": "Demo",
    }

    def config_check(self):
        """
        Checks to see if the config data is usable.
        """
        errors = []
        if len(self.steam_id) != 17:
            errors.append("Steam ID is invalid.")
        if len(errors) > 0:
            return False, errors
        else:
            return True, None

    def get_steam_id(self, vanity_url):
        """
        Gets a users Steam ID via their `vanity_url`.
        """
        base_url = r"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
        url = rf"{base_url}?key={self.steam_api_key}&vanityurl={vanity_url}"
        response = self.request_url(url)
        if response:
            data = response.json()
            steam_id = data["response"]["steamid"]
            return steam_id
        else:
            return False

    @staticmethod
    def hours_played(playtime_forever):
        """
        Converts minutes played to a hours played in decimal form.
        """
        return round(playtime_forever / 60, 4)

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
            time_to_beat = float(str(best_element.gameplay_main).replace("½", ".5"))
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
        if platform == "PS4":
            platform = "playstation-4"
        elif platform == "PS5":
            platform = "playstation-5"
        elif platform in ["Steam", "Uplay", "Origin", "MS Store"]:
            platform = "pc"
        replace_dict = {
            ":": "",
            "'": "",
            "&": "",
            ",": "",
            "?": "",
            "™": "",
            "_": "-",
            " ": "-",
        }
        for string, replace in replace_dict.items():
            game_name = game_name.replace(string, replace)
        user_agent = {"User-agent": "Mozilla/5.0"}
        self.api_sleeper("metacritic")
        review_score = ""
        url = f"https://www.metacritic.com/game/{platform.lower()}/{game_name.lower()}"
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
            review_score = "Page Error"
        return review_score

    def get_app_id(self, game, app_list={}):
        """
        Checks the Steam App list for a game and returns its app id if it exists as entered.
        """
        # sets up app_list if it does not exist
        if app_list == {}:
            url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?l=english"
            response = self.request_url(url)
            if not response:
                return None
            app_list = response.json()["applist"]["apps"]
        # searches for game
        for item in app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    def get_year(self, date):
        """
        Takes the given `date` and changes it to this format, "Sep 14, 2016".
        """
        year = re.search(r"[0-9]{4}", date)
        if year:
            return year.group(0)
        else:
            return "Invalid Date"

    def get_game_info(self, app_id, debug=False):
        """
        Gets game info with steam api using a `app_id`.
        """

        def get_json_desc(data):
            return [item["description"] for item in data]

        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=english"
        self.api_sleeper("steam_app_details")
        response = self.request_url(url)
        if not response:
            return None
        else:
            # TODO make it retry
            info_dict = {}
            dict = response.json()
            if debug:
                print(dict)
                exit()
            if "data" in dict[str(app_id)].keys():
                keys = dict[str(app_id)]["data"].keys()
                info_dict["name"] = dict[str(app_id)]["data"]["name"]
                # get developer
                if "developers" in keys:
                    info_dict["developers"] = ", ".join(
                        dict[str(app_id)]["data"]["developers"]
                    )
                else:
                    info_dict["developers"] = None
                # get publishers
                if "publishers" in keys:
                    info_dict["publishers"] = ", ".join(
                        dict[str(app_id)]["data"]["publishers"]
                    )
                else:
                    info_dict["publishers"] = None
                #  get genre
                if "genres" in keys:
                    info_dict["genre"] = ", ".join(
                        get_json_desc(dict[str(app_id)]["data"]["genres"])
                    )
                else:
                    info_dict["genre"] = None
                #  get metacritic
                if "metacritic" in keys:
                    info_dict["metacritic"] = dict[str(app_id)]["data"]["metacritic"][
                        "score"
                    ]
                else:
                    info_dict["metacritic"] = None
                #  early access
                if "early_access" in keys:
                    info_dict["early_access"] = dict[str(app_id)]["data"][
                        "early_access"
                    ]
                # get release year
                if "release_date" in keys:
                    release_date = dict[str(app_id)]["data"]["release_date"]["date"]
                    release_date = self.get_year(release_date)
                    info_dict["release_date"] = release_date
                else:
                    info_dict["release_date"] = None
                # get price_info
                if "price_overview" in keys:
                    price = dict[str(app_id)]["data"]["price_overview"][
                        "final_formatted"
                    ]
                    discount = dict[str(app_id)]["data"]["price_overview"][
                        "discount_percent"
                    ]
                    on_sale = (
                        dict[str(app_id)]["data"]["price_overview"]["discount_percent"]
                        > 0
                    )
                    info_dict["price"] = price
                    info_dict["discount"] = discount
                    info_dict["on_sale"] = on_sale
                else:
                    info_dict["price"] = None
                    info_dict["discount"] = None
                    info_dict["on_sale"] = None
                # get linux compat
                if "platforms" in keys:
                    info_dict["linux_compat"] = dict[str(app_id)]["data"]["platforms"][
                        "linux"
                    ]
                else:
                    info_dict["linux_compat"] = False
                if "categories" in keys:
                    info_dict["categories"] = ", ".join(
                        get_json_desc(dict[str(app_id)]["data"]["categories"])
                    )
                else:
                    info_dict["categories"] = None
                # drm info
                if "drm_notice" in keys:
                    info_dict["drm_notice"] = dict[str(app_id)]["data"]["drm_notice"]
                else:
                    info_dict["drm_notice"] = None
                # external account
                if "ext_user_account_notice" in keys:
                    info_dict["ext_user_account_notice"] = dict[str(app_id)]["data"][
                        "ext_user_account_notice"
                    ]
                else:
                    info_dict["ext_user_account_notice"] = None
                # runs unicode remover on all values
                final_dict = {k: self.unicode_remover(v) for k, v in info_dict.items()}
                return final_dict
        return False

    @staticmethod
    def string_url_convert(string) -> str:
        """
        Converts given `string` into a url ready string and returns it.
        """
        return re.sub(r"\W+", "", string.replace(" ", "_")).lower()

    def get_store_link(self, game_name, app_id):
        """
        Generates a likely link to the games store page using `game_name` and `app_id`."""
        if not app_id or app_id == "None":
            return ""
        return f"https://store.steampowered.com/app/{app_id}/{self.string_url_convert(game_name)}/"

    def steam_deck_compat(self, app_id):
        """
        Gets a games steam deck verification and other compatibility data by `app_id`.
        """
        url = f"https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport?nAppID={app_id}"
        data = self.request_url(url).json()
        categories = {
            0: "Unknown",
            1: "Unsupported",
            2: "Playable",
            3: "Verified",
        }
        category_num = data["results"]["resolved_category"]
        specific_ratings = data["results"]["resolved_items"]
        result = {"category": categories[category_num]}
        # ph
        PREFIX = "#SteamDeckVerified_TestResult"
        ratings = {
            "controller_func": f"{PREFIX}_DefaultControllerConfigFullyFunctional",
            "controller_glyphs": f"{PREFIX}_ControllerGlyphsMatchDeckDevice",
            "legible_text": f"{PREFIX}_InterfaceTextIsLegible",
            "good_config": f"{PREFIX}_DefaultConfigurationIsPerformant",
        }
        display_type = {
            1: "Note",
            2: "Fail",
            3: "Info",
            4: "Checkmark",
        }
        for rating in specific_ratings:
            for check, key in ratings.items():
                if rating["loc_token"] == key:
                    if rating["display_type"] == 4:
                        result[check] = True
                    else:
                        result[check] = False
        print(result)
        return result

    def requests_loop(self, skip_filled=1, check_status=0):
        """
        Loops through games in row_idx and gets missing data for time to beat and Metacritic score.
        """
        # creates checklist
        check_list = []
        to_check = [
            genre_column_name := "Genre",
            publishers_column_name := "Publishers",
            developers_column_name := "Developers",
            metacritic_column_name := "Metacritic",
            time_to_beat_column_name := "Time To Beat in Hours",
            release_year_column_name := "Release Year",
            # steam_deck_viable_column_name := 'Steam Deck Viable',
        ]
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
                for column in to_check:
                    cell = self.games.get_cell(game, column)
                    if cell == None and game not in check_list:
                        check_list.append(game)
                        continue
            else:
                check_list.append(game)
        # checks if data should be updated
        missing_data = len(check_list)
        auto_update = 50
        if 0 < missing_data <= auto_update:
            print(f"\nMissing data is within auto update threshold of {auto_update}.")
        elif missing_data > auto_update:
            msg = f"\nSome data is missing for {missing_data} games.\nDo you want to retrieve it?\n:"
            if not input(msg) in ["yes", "y"]:
                return
        else:
            return
        try:
            # updates missing data
            print(
                "\nStarting Time To Beat, Metacritic Score and other steam data check."
            )
            save_interval = 15
            running_interval = save_interval
            for game_name in tqdm(
                iterable=check_list, ascii=True, unit="games", dynamic_ncols=True
            ):
                # How long to beat check
                if not self.games.get_cell(game_name, time_to_beat_column_name):
                    time_to_beat = self.get_time_to_beat(game_name)
                    if time_to_beat != None:
                        self.games.update_cell(
                            game_name, time_to_beat_column_name, time_to_beat
                        )
                # metacritic score check
                if not self.games.get_cell(game_name, metacritic_column_name):
                    platform = self.games.get_cell(game_name, "Platform")
                    metacritic_score = self.get_metacritic(game_name, platform)
                    if metacritic_score != None:
                        self.games.update_cell(
                            game_name, metacritic_column_name, metacritic_score
                        )
                # gets steam info if an app id exists for the entry and the platform is Steam
                app_id = self.games.get_cell(game_name, "App ID")
                if not app_id:
                    app_id = self.get_app_id(game_name)
                steam_info = self.get_game_info(app_id)
                platform = self.games.get_cell(game_name, "Platform")
                if steam_info and platform == "Steam":
                    # genre
                    if steam_info["genre"]:
                        self.games.update_cell(
                            game_name, genre_column_name, steam_info["genre"]
                        )
                    else:
                        self.games.update_cell(game_name, genre_column_name, "No Genre")
                    # release year
                    if steam_info["release_date"]:
                        self.games.update_cell(
                            game_name,
                            release_year_column_name,
                            steam_info["release_date"],
                        )
                    else:
                        self.games.update_cell(
                            game_name, release_year_column_name, "No Release Year"
                        )
                    # developer
                    if steam_info["developers"]:
                        self.games.update_cell(
                            game_name, developers_column_name, steam_info["developers"]
                        )
                    else:
                        self.games.update_cell(
                            game_name, developers_column_name, "No Developer"
                        )
                    # publishers
                    if steam_info["publishers"]:
                        self.games.update_cell(
                            game_name, publishers_column_name, steam_info["publishers"]
                        )
                    else:
                        self.games.update_cell(
                            game_name, publishers_column_name, "No Publisher"
                        )
                    # metacritic
                    if steam_info["metacritic"]:
                        self.games.update_cell(
                            game_name, metacritic_column_name, steam_info["metacritic"]
                        )
                    else:
                        if not self.games.get_cell(game_name, metacritic_column_name):
                            self.games.update_cell(
                                game_name, metacritic_column_name, "No Score"
                            )
                else:
                    self.games.update_cell(
                        game_name, release_year_column_name, "No Release Year"
                    )
                    self.games.update_cell(game_name, genre_column_name, "No Data")
                    self.games.update_cell(game_name, developers_column_name, "No Data")
                    self.games.update_cell(game_name, publishers_column_name, "No Data")
                running_interval -= 1
                if running_interval == 0:
                    running_interval = save_interval
                    self.excel.save_excel_sheet(use_print=False, backup=False)
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            self.excel.save_excel_sheet()

    def refresh_steam_games(self, steam_id):
        """
        Gets games owned by the entered Steam ID and runs excel update/add functions.
        """
        # asks for a steam id if the given one is invalid
        while len(steam_id) != 17:
            steam_id = input(
                "\nInvalid Steam ID (It must be 17 numbers.)\nTry Again.\n:"
            )
        print("\nStarting Steam Library Tracking")
        root_url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        url_var = f"?key={self.steam_api_key}&steamid={steam_id}?l=english"
        combinded_url = f"{root_url}{url_var}&include_played_free_games=0&format=json&include_appinfo=1"
        self.api_sleeper("steam_owned_games")
        response = self.request_url(combinded_url)
        if response:
            # checks for games that changed names
            self.removed_from_steam = [
                str(game)
                for game in self.games.row_idx.keys()
                if self.games.get_cell(game, "Platform") == "Steam"
            ]
            self.total_games_updated = 0
            self.total_games_added = 0
            self.added_games = []
            for game in response.json()["response"]["games"]:
                game_name = game["name"]
                if self.should_ignore(game_name):
                    continue
                playtime_forever = game["playtime_forever"]
                game_appid = game["appid"]
                # Demo
                if re.search(r"\bdemo\b", game["name"].lower()) or re.search(
                    r"\btest\b", game["name"].lower()
                ):
                    play_status = "Demo"  # sets play_status to Demo if demo or test appears in the name
                # Unplayed
                elif playtime_forever <= 20:
                    play_status = "Unplayed"  # sets play_status to Unplayed if playtime_forever is 0-15
                # Playing
                elif game["playtime_windows_forever"] > 60:
                    play_status = "Playing"  # sets play_status to Played if playtime_forever is greater then 1 hour
                # Unset
                else:
                    play_status = "Unset"  # sets play_status to Unset if none of the above applies
                # Updates game if it is in the index or adds if it is not.
                # TODO make sure play status is set properly
                # if played more then an hour then set to playing if it was set to unplayed
                if game_name in self.games.row_idx.keys():
                    if game_name in self.removed_from_steam:
                        self.removed_from_steam.remove(game_name)
                    self.update_game(game_name, playtime_forever, play_status)
                else:
                    self.add_game(game_name, playtime_forever, game_appid, play_status)
            if len(self.removed_from_steam) > 0:
                print(
                    f'\nThe following Steam games are unaccounted for:\n{" ,".join(self.removed_from_steam)}'
                )
                for item in self.removed_from_steam:
                    status = self.games.get_cell(item, "Play Status")
                    if "Removed" not in status:
                        self.games.update_cell(
                            item, "Play Status", f"Removed | {status}"
                        )
            return True

    @staticmethod
    def hash_file(file_path):
        """
        Creates a hash for the given `file_path`.
        """
        BUF_SIZE = 65536
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
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
            print("prev", previous_hash)
            print("new ", new_hash)
            self.data["settings"]["playstation_hash"] = new_hash
            self.save_json_output(self.data, self.config)
            with open(self.config) as file:
                data = json.load(file)
        return True

    def should_ignore(self, name):
        """
        Returns True if any keywords are found or it is in the `ignore_list`.
        """
        # keyword check
        keyword_ignore_list = [
            "demo",
            "beta",
            "Youtube" "PreOrder",
            "Pre-Order",
            "Soundtrack",
            "Closed Test",
            "Public Test",
            "Test Server",
            "Bonus Content",
            "Trial Edition",
        ]
        name = name.lower()
        for string in keyword_ignore_list:
            if re.search(rf"\b{string.lower()}\b", name):
                return True
        # ignore list
        if name in self.ignore_list:
            return True
        return False

    @staticmethod
    def unicode_fix(string):
        """
        Basic unicode cleaner.
        """
        inicode_dict = {"â€": "'", "®": "", "™": "", "â„¢": "", "Â": "", "Ã›": "U"}
        for char, replace in inicode_dict.items():
            string = string.replace(char, replace)
        return string.strip()

    def add_playstation_games(self, games):
        """
        Adds playstation games to excel using the given `games` variable.
        """
        added_games = []
        for game in tqdm(iterable=games, ascii=True, unit="games", dynamic_ncols=True):
            game_name = self.unicode_fix(game["name"])
            # skip if it should be ignored or was added this session
            if self.should_ignore(game_name) or game_name in added_games:
                continue
            # skip if it already exist
            a = f"{game_name} - Console"
            if game_name in self.games.row_idx.keys() or a in self.games.row_idx.keys():
                continue
            # TODO skip if the game exists with a playstation version already
            # adds the game
            added_games.append(game_name)
            self.add_game(
                game_name=game_name, play_status="Unplayed", platform=game["platform"]
            )
        total_games_added = len(added_games)
        print(f"Added {total_games_added} PS4/PS5 Games.")
        if total_games_added > 0:
            self.excel.save_excel_sheet()

    def create_df(self, table):
        """
        Creates a dataframe from a `table` found using requests and BeautifulSoup.
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

    def steam_deck_check(self, steam_id, hour_freq=1):
        """
        Checks steam_deck.txt and updates steam deck status with the new info.
        """
        seconds_since_last_run = time.time() - self.last_run
        hours_since_last_run = seconds_since_last_run * 0.000277778
        if hours_since_last_run <= hour_freq:
            hour_till = round(hour_freq - hours_since_last_run, 1)
            print(f"\nSkipping Steam Deck Check.\nNext check due in {hour_till} hours.")
            return
        print("\nStarting Steam Deck Compatibility Check")
        url = f"https://checkmydeck.herokuapp.com/users/{steam_id}/library"
        user_agent = {"User-agent": "Mozilla/5.0"}
        response = self.request_url(url, headers=user_agent)
        if response:
            soup = BeautifulSoup(response.text, "html.parser")
            legend = soup.find("table", id="deckCompatChartLegend")
            # prints data
            category_totals = []
            for item in legend.text.split("\n"):
                if item != "":
                    split_str = item.split(" ")
                    category = split_str[0].replace(":", "").title()
                    count = split_str[1]
                    percent = split_str[3].replace("(", "").replace(")", "")
                    print(f"{count} {category} games at {percent}")
            # finds the table and headers for the report
            table = soup.find("table", id="deckCompatReportTable")
            df = self.create_df(table)
            # loops through table using the dataframe
            first_run = True
            for index, row in df.iterrows():
                # gets rid of possible new lines that could be added
                last_updated = row["Last Change"].replace("\n", "")
                game_name = row["Title"].replace("\n", "")
                status = row["Status"].replace("\n", "")
                if game_name == "Grand Theft Auto: San Andreas":
                    continue
                if self.games.update_cell(game_name, "Steam Deck Status", status):
                    if first_run:
                        print("\nUpdated Games:")
                        first_run = False
                    info = f"{game_name} was updated to {status.title()}"
                    self.logger.info(info)
                    print(info)
            self.excel.save_excel_sheet()
        else:
            print("Failed connect to Steam Deck Data")

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
                app_id, game_name, status = line.split("\t")
            elif len(values) == 4:
                app_id, game_name, ignore, status = line.split("\t")
            if self.games.update_cell(game_name, "Steam Deck Status", status):
                print("failed on", game_name, status)
        self.excel.save_excel_sheet()

    def check_playstation_json(self):
        """
        Checks `playstation_games.json` to find out if it is newly updated so it can add the new games to the sheet.
        """
        # checks if json exists
        json_path = Path("configs\playstation_games.json")
        if not json_path.exists:
            print("PlayStation Json does not exist.")
            webbrowser.open_new(self.playstation_data_link)
            return None
        # create hash file if it does not exist
        if not json_path.exists:
            json_path.touch()
        if not self.check_for_changes(json_path):
            return None
        with open(json_path) as file:
            data = json.load(file)
        print("\nChecking for new games for PS4 or PS5.")
        games = data["data"]["purchasedTitlesRetrieve"]["games"]
        self.add_playstation_games(games)

    def update_game(self, game_name, playtime_forever, play_status):
        """
        Updates the games playtime(if changed) and play status(if unset).
        """
        previous_hours_played = self.games.get_cell(game_name, "Hours Played")
        current_hours_played = self.hours_played(playtime_forever)
        current_platform = self.games.get_cell(game_name, "Platform")
        if (
            current_platform != "Steam"
        ):  # prevents updating games that are owned on Steam and a console.
            return
        elif previous_hours_played == None or previous_hours_played == "None":
            previous_hours_played = 0
        else:
            previous_hours_played = float(previous_hours_played)
        if current_hours_played > previous_hours_played:
            self.games.update_cell(
                game_name, "Hours Played", self.hours_played(playtime_forever)
            )
            self.games.update_cell(game_name, "Date Updated", self.excel_date)
            self.total_games_updated += 1
            if play_status == "unset":
                self.games.update_cell(game_name, "Play Status", "Played")
            unit = "hours"
            added_time = current_hours_played - previous_hours_played
            if added_time < 1:
                added_time = added_time * 60
                unit = "minutes"
            added_time = round(added_time, 1)
            total_hours = round(current_hours_played, 1)
            total_days = round(total_hours / 24, 1)
            days_string = ""
            if total_days >= 1:
                days_string = f" | {total_days} days"
            print(f"\n > {game_name} updated.")
            print(f"   Added {added_time} {unit}")
            print(f"   Total Playtime: {total_hours} hours{days_string}.")
        self.games.format_cells(game_name)

    def add_game(
        self,
        game_name=None,
        playtime_forever="",
        game_appid="",
        play_status="",
        platform="Steam",
    ):
        """
        Appends new game to excel sheet into the correct columns using self.column_i.
        Any columns that are inputted manually are left blank.
        """
        save = 0
        if game_name == None:
            save = 1
            game_name = input(
                "\nDo you want to add a new game?\nIf Yes type the game name.\n:"
            )
            if game_name != "":
                if game_name.lower() in ["yes", "y"]:
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
                hours_played = int(
                    input("\nHow many hours have you played it?\n:") or 0
                )
                print("\nWhat Play Status should it have?")
                play_status = self.play_status_picker() or "Unset"
                print(f"\nAdded Game:\n{game_name}")
                print(f"Platform: {platform}")
                print(f"Hours Played: {hours_played}")
                print(f"Play Status: {play_status}")
            else:
                return
        else:
            if playtime_forever:
                hours_played = self.hours_played(playtime_forever)
            else:
                hours_played = ""
        # store link setup
        store_link_hyperlink = ""
        store_link = self.get_store_link(game_name, game_appid)
        if store_link:
            store_link_hyperlink = f'=HYPERLINK("{store_link}","Store Link")'
        # sets vr support value
        if re.search(r"\bVR\b", game_name):
            vr_support = "Yes"
        elif platform in ["PS5", "PS4", "Switch"]:
            vr_support = "No"
        else:
            vr_support = ""
        column_info = {
            "My Rating": "",
            "Game Name": game_name,
            "Play Status": play_status,
            "Platform": platform,
            "VR Support": vr_support,
            "Time To Beat in Hours": self.get_time_to_beat(game_name),
            "Metacritic": self.get_metacritic(game_name, "Steam"),
            "Rating Comparison": "",
            "Probable Completion": "",
            "Hours Played": hours_played,
            "App ID": game_appid,
            "Store Link": store_link_hyperlink,
            "Date Updated": self.excel_date,
            "Date Added": self.excel_date,
        }
        steam_info = self.get_game_info(game_appid)
        if steam_info:
            columns = [
                "Publishers",
                "Developers",
                "Genre",
                "Release Year",
                "Metacritic",
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
            self.excel.save_excel_sheet()

    def output_completion_data(self):
        """
        Shows total games added and updated games with info.
        """
        if self.total_games_added > 0:
            print(f"\nGames Added: {self.total_games_added}")
            if len(self.added_games) > 0:
                print(", ".join(self.added_games))
        if self.total_games_updated > 0:
            print(f"\nGames Updated: {self.total_games_updated}")
        if len(self.invalid_months) > 0:
            print(self.invalid_months)
        if self.excel.changes_made:
            self.excel.save_excel_sheet()
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
            if len(choice_list) == 0:
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
        print("\nStarting Game Sale Check\n")
        for game, index in tqdm(
            iterable=self.games.row_idx.items(),
            ascii=True,
            unit="games",
            dynamic_ncols=True,
        ):
            my_rating = self.games.get_cell(game, "My Rating")
            if my_rating == None:
                continue
            app_id = self.games.get_cell(game, "App ID")
            if my_rating >= rating_limit and app_id:
                game_dict = self.get_game_info(app_id)
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
        matched_game = self.string_matcher(game_name, self.games.row_idx.keys())
        if matched_game:
            game_idx = self.games.row_idx[matched_game]
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
            self.games.update_cell(game_idx, "Hours Played", float(hours))
            print(f"Updated to {hours} Hours")
            updated = True
        else:
            print("Left Hours Played the same.")
        # sets status if a status is given
        status = input("\nWhat is the new Status?\n").title()
        if status in self.play_status_choices.values():
            self.games.update_cell(game_idx, "Play Status", status)
            print(f"Updated Play Status to {status}")
            updated = True
        else:
            print("Left Play Status the same.")
        if updated:
            self.games.update_cell(game_idx, "Date Updated", self.excel_date)
            self.excel.save_excel_sheet(backup=False)
        else:
            print("No changes made.")
        response = input("Do you want to update another game? Type yes.\n")
        if response.lower() in ["yes", "yeah", "y"]:
            self.custom_update_game()

    def update_last_run(self):
        """
        Updates the last run time in seconds.
        """
        self.data["settings"]["last_run"] = time.time()
        self.save_json_output(self.data, self.config)

    def open_excel_input(self, other_option=False):
        """
        Opens excel file if previous input is passed.
        """
        if not other_option:
            input("\nPress Enter to open the excel sheet.\n")
        else:
            input("\nPress Enter to open the excel sheet.\n")
        os.startfile(self.excel.file_path)
        exit()

    def steam_deck_data_checker(self):
        """
        Prints a message of a possible steam deck key if found in the app id search.
        """
        app_id = 1145360
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=english"
        response = self.request_url(url)
        if response:
            dict = response.json()
            keywords = ["deck"]
            keys = dict[str(app_id)]["data"].keys()
            for keyword in keywords:
                for key in keys:
                    if keyword in key:
                        print("\nPossible Steam Deck Key found")
                        print(key)

    def pick_task(self):
        """
        Allows picking a task to do next using a matching number.
        """
        print("\nWhat do you want to do next?\n")
        choices = [
            "Update Game",  # 1
            "Pick Random Game",  # 2
            "Add Game",  # 3
            "Update the Playstation Data",  # 4
            "Check for and view Favorite Games Sales",  # 5
            "View Favorite Games Sales",  # 6
            "Open Log",  # 7
        ]
        for count, choice in enumerate(choices):
            print(f"{count+1}. {choice}")
        res = input("\nPress Enter without a number to open the excel sheet.\n")
        if res == "1":
            self.custom_update_game()
        elif res == "2":
            self.pick_random_game()
        elif res == "3":
            self.add_game()
        elif res == "4":
            subprocess.Popen(f'notepad "configs\playstation_games.json"')
            webbrowser.open(self.playstation_data_link)
            webbrowser.open(r"https://store.playstation.com/")
            input("Press Enter when done.")
            self.check_playstation_json()
        elif res == "5":
            self.get_favorite_games_sales()
        elif res == "6":
            self.view_favorite_games_sales()
        elif res == "7":
            webbrowser.open("configs/tracker.log")
        elif res == "":
            os.startfile(self.excel.file_path)
            exit()

    def run(self):
        """
        Main run function.
        """
        self.config_check()
        self.arg_func()
        if self.ext_terminal:
            os.system("mode con cols=68 lines=40")
        print("Starting Game Tracker")
        # starts function run with CTRL + C Exit being possible without causing an error
        try:
            self.refresh_steam_games(self.steam_id)
            self.steam_deck_check(steam_id=self.steam_id)
            self.check_playstation_json()
            self.output_completion_data()
            self.requests_loop()
            self.update_last_run()
            self.steam_deck_data_checker()
            self.pick_task()
            self.open_excel_input()
        except KeyboardInterrupt:
            print("\nClosing")


if __name__ == "__main__":
    App = Tracker()
    if not App.ext_terminal:
        # App.view_favorite_games_sales()
        # print(App.get_steam_id('Varnock'))
        # App.steam_deck_check()
        # App.steam_deck_compat(427520)
        # App.steam_deck_compat(1290000)
        # App.get_game_info(1290000, debug=True)
        pass
    # App.custom_update_game()
    App.run()
