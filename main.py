import random, json, os, re, sys, time, subprocess, webbrowser, math
from howlongtobeatpy import HowLongToBeat
from pathlib import Path
from pick import pick
import datetime as dt
import pandas as pd

from rich.console import Console
from rich.prompt import IntPrompt
from rich.progress import track
from rich.table import Table
from rich.theme import Theme

# classes
from classes.setup import Setup
from classes.steam import Steam
from classes.utils import Utils, keyboard_interrupt
from classes.logger import Logger

# my package
from easierexcel import Excel, Sheet


class Tracker(Steam, Utils):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    ext_terminal = sys.stdout.isatty()  # is True if terminal is external

    # rich console
    custom_theme = Theme(
        {
            "primary": "bold deep_sky_blue1",
            "secondary": "bold pale_turquoise1",
            "info": "dim cyan",
            "warning": "bold magenta",
            "danger": "bold red",
        }
    )
    console = Console(theme=custom_theme)

    title = "Game Library Tracker"

    # config init
    app = Setup
    config, data = app.setup()

    # steam_data
    steam_key = data["steam_data"]["api_key"]
    steam_id = str(data["steam_data"]["steam_id"])
    vanity_url = data["steam_data"]["vanity_url"]

    # settings
    playstation_data_link = data["settings"]["playstation_data_link"]
    excel_filename = data["settings"]["excel_filename"]
    logging = data["settings"]["logging"]

    # misc
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
        # "light_grey_fill": [],
        "percent": [
            "%",
            "Percent",
            "Discount",
        ],
        "currency": ["Price", "MSRP", "Cost"],
        "integer": ["App ID", "Number", "Release Year"],
        "count_days": ["Days Till Release"],
        "date": ["Last Updated", "Date"],
        "decimal": ["Hours Played", "Linux Hours", "Time To Beat in Hours"],
    }
    # excel setup
    excel = Excel(excel_filename, use_logging=logging)
    steam = Sheet(
        excel_object=excel,
        sheet_name="Steam",
        column_name="App ID",
        options=options,
    )
    playstation = Sheet(
        excel_object=excel,
        sheet_name="Playstation",
        column_name="Name",
        options=options,
    )
    sales = Sheet(
        excel_object=excel,
        sheet_name="Sales",
        column_name="Name",
        options=options,
    )
    # sets play status choices for multiple functions
    play_status_choices = {
        "1": "Played",
        "2": "Unplayed",
        "3": "Endless",
        "4": "Replay",
        "5": "Must Play",
        "6": "Finished",
        "7": "Waiting",
        "8": "Quit",
        "9": "Ignore",
    }
    # misc
    ps_data = Path("configs/playstation_games.json")

    # columns
    excel_columns = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        my_rating_col := "My Rating",
        rating_comp_col := "Rating Comparison",
        steam_rev_per_col := "Steam Review Percent",
        steam_rev_total_col := "Steam Review Total",
        steam_player_count_col := "Player Count",
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
        store_link_col := "Store Link",
        release_col := "Release Year",
        app_id_col := "App ID",
    ]
    # not applicable cell values
    na_values = [
        "NaN",
        "Invalid Date",
        "No Tags",
        "No Year",
        "No Score",
        "Not Found",
        "No Reviews",
        "Missing Data",
        "Few Reviews",
        "Not Enough Reviews",
        "No Publisher",
        "No Developer",
    ]

    errors = []

    def __init__(self, save) -> None:
        """
        Game Library Tracking Class.
        """
        self.save_to_file = save
        if not self.steam_id:
            self.update_steam_id()

    def config_check(self):
        """
        Checks to see if the config data is usable.
        """
        errors = []
        if not self.validate_steam_id(self.steam_id):
            errors.append("Steam ID is Invalid")
        if not self.validate_steam_key(self.steam_key):
            errors.append("Steam API Key is Invalid")
        if errors:
            return False, errors
        else:
            return True, None

    def update_steam_id(self):
        """
        Updates the steam id in the config using the given vanity url if present.
        """
        if not self.vanity_url:
            raise "Steam ID and Vanity URL is blank. Please enter at one of them"
        steam_id = self.get_steam_id(self.vanity_url, self.steam_key)
        if steam_id:
            self.data["settings"]["steam_id"] = steam_id
            self.save_json_output(self.data, self.config)

    def get_steam_friends(self):
        """
        Gets a users Steam friends list.
        """
        main_url = "https://api.steampowered.com/"
        api_action = "ISteamUser/GetFriendList/v0001/"
        url = main_url + api_action
        params = {
            "key": self.steam_key,
            "steamid": self.steam_id,
            "relationship": "all",
        }
        response = self.request_url(url=url, params=params)
        if response:
            data = response.json()
            return data["friendslist"]["friends"]
        return []

    def sync_friends_list(self):
        self.get_friends_list_changes(0)

    def get_friends_list_changes(self, check_freq_days=14):
        """
        Checks for changes to your friends list.
        Shows a table of new and removed friends Steam ID's and usernames.
        """
        # check last run
        if self.recently_executed(self.data, "friends_sync", check_freq_days):
            return
        self.update_last_run(self.data, "friends_sync")
        # get friends
        print("\nStarting Steam Friends Sync")
        prev_friends_ids = self.data["friend_ids"]
        cur_friend_ids = [friend["steamid"] for friend in self.get_steam_friends()]
        # finds changes
        additions = list(set(cur_friend_ids) - set(prev_friends_ids))
        removals = list(set(prev_friends_ids) - set(cur_friend_ids))
        if not additions and not removals:
            self.console.print("No friends added or removed", style="secondary")
            return
        # view changes
        title = "Friends List Updates"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Type", justify="center")
        table.add_column("Username", justify="left")
        table.add_column("Steam ID", justify="left")
        for steam_id in removals:
            username = self.get_steam_username(steam_id, self.steam_key)
            row = [
                "Removed",
                username,
                steam_id,
            ]
            table.add_row(*row)
            # logging
            msg = f"Added to Friends List: {username}"
            self.tracker.info(msg)
        for steam_id in additions:
            username = self.get_steam_username(steam_id, self.steam_key)
            row = [
                "Added",
                username,
                steam_id,
            ]
            table.add_row(*row)
            # logging
            msg = f"Removed from Friends List: {username}"
            self.tracker.info(msg)
        self.console.print(table, new_line_start=True)
        # update friend data in config
        self.data["friend_ids"] = cur_friend_ids
        self.save_json_output(self.data, self.config)

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
        time_to_beat = "-"
        if results is not None and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = best_element.main_extra or best_element.main_story or "-"
        return time_to_beat

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

    def set_time_to_beat(self, app_id, new_ttb, cur_ttb):
        """
        Sets `app_id`'s Time to beat cell to `time_to_beat`.
        """
        if not new_ttb:
            return
        if not self.any_is_num(cur_ttb):
            return self.steam.update_cell(app_id, self.time_to_beat_col, new_ttb)

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

    def set_play_status(self, app_id, new_status, cur_status=None):
        """
        Sets `app_id`'s Play Status cell to `new_status` if it the current status is unplayed.
        """
        if cur_status == "Unplayed" and new_status != cur_status:
            return self.steam.update_cell(app_id, self.play_status_col, new_status)

    def set_date_updated(self, app_id):
        """
        Sets `app_id`'s Date Updated cell to the current date.
        """
        cur_date = dt.datetime.now()
        return self.steam.update_cell(app_id, self.date_updated_col, cur_date)

    @staticmethod
    def get_price_info(game_info: {}):
        """
        Gets price info from `game_info` and returns None if anything is set up
        wrong for any or all return values.
        """
        if "price_overview" not in game_info.keys():
            return None, None, None
        price_data = game_info["price_overview"]
        # price
        price = None
        if "final_formatted" in price_data.keys():
            price_value = price_data["final_formatted"]
            try:
                price = float(price_value.replace("$", ""))
            except:
                price = None
        # discount
        discount = None
        if "discount_percent" in price_data.keys():
            discount = float(price_data["discount_percent"])
        # on sale
        on_sale = None
        if "discount_percent" in price_data.keys():
            on_sale = price_data["discount_percent"] > 0
        return price, discount, on_sale

    def get_game_info(self, app_id):
        """
        Gets game info with steam api using a `app_id`.
        """
        info_dict = {
            "game_name": "-",
            self.dev_col: "-",
            self.pub_col: "-",
            self.genre_col: "-",
            self.ea_col: "No",
            self.steam_rev_per_col: "No Reviews",
            self.steam_rev_total_col: "No Reviews",
            self.user_tags_col: "No Tags",
            self.release_col: "No Year",
            "price": "-",
            "discount": 0.0,
            "on_sale": False,
            "drm_notice": "-",
            "categories": "-",
            "ext_user_account_notice": "-",
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
        if tags:
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
                price, discount, on_sale = self.get_price_info(game_info)
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

    def find_recent_games(
        self,
        df: pd.DataFrame,
        column: str,
        n_days: int = 7,
    ) -> list[dict]:
        """
        Finds recent games by dates in `column` within `n_days`.
        """
        df[column] = pd.to_datetime(df[column])
        filtered_df = df[abs((df[column] - dt.datetime.now()).dt.days) <= n_days]
        return filtered_df.sort_values(
            by=self.date_updated_col, ascending=False
        ).to_dict(orient="records")

    def update_extra_steam_info(self, app_ids):
        """
        ph
        """
        save_every_nth = self.create_save_every_nth()
        update_total = len(app_ids)
        cur_itr = 0
        print()
        desc = "Syncing Game Data"
        for app_id in track(app_ids, description=desc):
            game_data = self.steam.get_row(app_id)
            game_name = game_data[self.name_col]
            # How long to beat check
            cur_ttb = game_data[self.time_to_beat_col]
            if not cur_ttb:
                new_ttb = self.get_time_to_beat(game_name)
                self.set_time_to_beat(app_id, new_ttb, cur_ttb)
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
            progress = cur_itr / update_total * 100
            self.set_title(f"{progress:.2f}% - {self.title}")
        self.set_title()

    def update_all_game_data(self):
        """
        ph
        """
        app_ids = [int(app_id) for app_id in self.steam.row_idx.keys()]
        self.update_extra_steam_info(app_ids)

    def get_recently_played_app_ids(self, df: pd.DataFrame, n_days=30) -> list:
        """
        ph
        """
        # check last run
        if self.recently_executed(self.data, "updated_recently_played", n_days):
            return []
        # get recently played games
        recently_played = App.find_recent_games(df, self.date_updated_col, n_days)
        recently_played_app_ids = [game[self.app_id_col] for game in recently_played]
        return recently_played_app_ids

    def updated_game_data(self, df, skip_filled=True, skip_by_play_status=False):
        """
        Updates game data for games that were played recently and are missing data.

        Use `skip_filled` to skip non blank entries.

        Use `skip_by_play_status` to only check games with a specific play status.
        """
        # starts the update list with recently played games
        update_list = self.get_recently_played_app_ids(df, n_days=30)
        updated_recent = True if update_list else False
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
        # adds games with missing data to update_list
        for app_id in self.steam.row_idx:
            game_data = self.steam.get_row(app_id)
            if skip_by_play_status:
                if game_data[self.play_status_col] not in [
                    "Unplayed",
                    "Played",
                    "Finished",
                    "Quit",
                    "Replay",
                    "Must Play",
                ]:
                    continue
            if skip_filled:
                for column in column_list:
                    cell = game_data[column]
                    if cell == None and app_id not in update_list:
                        update_list.append(app_id)
                        continue
            else:
                update_list.append(app_id)
        # checks if data should be updated
        if update_list:
            msg = f"\nDo you want update data for {len(update_list)} games?\n"
            if not input(msg) in ["yes", "y"]:
                return
        else:
            return
        # updates game data
        try:
            self.update_extra_steam_info(update_list)
            if updated_recent:
                self.update_last_run(self.data, "updated_recently_played")
            print(f"\nUpdated Data for {len(update_list)} games")
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            if self.save_to_file:
                self.excel.save(use_print=False)

    def output_recently_played_games(self, df, n_days=7):
        """
        Creates a table with the recently played Gmes.
        """
        recently_played_games = App.find_recent_games(df, "Date Updated", n_days)
        # creates table
        title = "Recently Played Games"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Days\nSince", justify="center")
        table.add_column("Date Updated", justify="center")
        table.add_column("Name", justify="left")
        table.add_column("Play\nStatus", justify="center")
        table.add_column("Hours\nPlayed", justify="right")
        table.add_column("Time\nTo Beat", justify="right")
        table.add_column("Last\nPlay Time", justify="center")
        # add rows
        for game in recently_played_games[:10]:
            # days since
            last_updated_dt = game[self.date_updated_col]
            last_updated = (
                last_updated_dt.strftime("%a %b %d, %Y") if last_updated_dt else "-"
            )
            days_since = str(abs(self.days_since(last_updated_dt)))
            # last play time
            last_play_time = "-"
            if type(game[self.last_play_time_col]) is str:
                last_play_time = game[self.last_play_time_col]
            # hours played
            hours_played = (
                str(game[self.hours_played_col])
                if not math.isnan(game[self.hours_played_col])
                else "0"
            )
            # time to beat
            ttb = (
                str(game[self.time_to_beat_col])
                if type(game[self.time_to_beat_col]) is float
                else "-"
            )
            # row setup
            row = [
                days_since,
                last_updated,
                game[self.name_col],
                game[self.play_status_col],
                hours_played,
                ttb,
                last_play_time,
            ]
            table.add_row(*row)
        # print table
        self.console.print(table, new_line_start=True)

    def output_play_status_info(self, df):
        """
        Creates a table with counts and percentage of each play status.
        """
        title = "Play Status Statistics\n(Excludes Ignored)"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        play_statuses = df["Play Status"].value_counts()
        total_games = df["Name"].count() - play_statuses["Ignore"]
        row1, row2 = [], []
        for status in self.play_status_choices.values():
            if status == "Ignore":
                continue
            table.add_column(status, justify="center")
            row1.append(str(play_statuses[status]))
            row2.append(f"{play_statuses[status]/total_games:.1%}")
        table.add_row(*row1)
        table.add_row(*row2)
        self.console.print(table, new_line_start=True)

    def output_playtime_info(self, df):
        """
        Creates a table with counts and percentage of each play status.
        """
        title = "Playtime Statistics"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        data = {}
        total_hours_sum = df["Hours Played"].sum()
        linux_hours_sum = df["Linux Hours"].sum()
        data["Total\nHours"] = round(total_hours_sum, 1)
        data["Total\nDays"] = round(total_hours_sum / 24, 1)
        data["Linux\nHours"] = round(linux_hours_sum, 1)
        data["% Linux\nHours"] = f"{linux_hours_sum / total_hours_sum:.1%}"
        # averages
        data["Average\nHours"] = round(df["Hours Played"].mean(), 1)
        data["Median\nHours"] = round(df["Hours Played"].median(), 1)
        # min max
        data["Max\nHours"] = round(df["Hours Played"].max(), 1)

        row = []
        for name, stat in data.items():
            table.add_column(name, justify="center")
            row.append(str(stat))
        table.add_row(*row)

        self.console.print(table, new_line_start=True)

    def output_review_info(self, df):
        """
        Outputs a table of review stats.
        """
        title = "Rating Statistics"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )

        data = {}
        # my ratings
        my_ratings = df["My Rating"]
        data["My\nTotal"] = my_ratings.count()
        data["My\nAverage"] = round(my_ratings.mean(), 1)
        # steam ratings
        steam_ratings = df["Steam Review Percent"].astype("float")
        data["Steam\nTotal"] = steam_ratings.count()
        steam_avg = round(steam_ratings.mean(), 1)
        data["Steam\nAverage"] = f"{round(steam_avg*100)}%"

        row = []
        for name, stat in data.items():
            table.add_column(name, justify="center")
            row.append(str(stat))
        table.add_row(*row)

        self.console.print(table, new_line_start=True)

    def find_tag_rating_avg(self, df):
        """
        Finds the average library owner rating for each game tag.
        """
        # Split the comma-separated values in the 'Genres' column into separate rows
        df_exploded = df.assign(Tag=df["User Tags"].str.split(",")).explode("Tag")

        tag_counts = df_exploded["Tag"].value_counts()
        print("\nTag Counts", tag_counts)
        min_tags = 2
        min_total_ratings = 5

        popular_tags = tag_counts[tag_counts >= min_tags].index

        print("\nPopular Tags", popular_tags)
        df_filtered_tags = df_exploded[df_exploded["Tag"].isin(popular_tags)]

        # Group by the 'Genre' column and calculate the average rating for each genre
        average_ratings_by_genre = df_filtered_tags.groupby("Tag")["My Rating"].mean()

        filtered_tags = average_ratings_by_genre.index[
            average_ratings_by_genre.index.isin(
                tag_counts[tag_counts > min_total_ratings].index
            )
        ]

        # Display the result
        top_30_ratings = filtered_tags.sort_values(ascending=False)
        print(top_30_ratings)

        # for ind in top_30_ratings.index:
        #     print(df["Name"][ind], df["My Rating"][ind])

    def output_statistics(self, dataframe):
        """
        Outputs tables of game library statistics.
        """
        self.output_play_status_info(dataframe)
        self.output_playtime_info(dataframe)
        self.output_review_info(dataframe)

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
        if minutes_played >= 30:
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

    def output_played_games_info(self, played_games):
        """
        Outputs a table of played game stats.
        """
        total_games_played = len(played_games)
        title = f"Games Played: {len(played_games)}"
        if total_games_played > 1:
            title += f"\nLast Session Playtime: {self.total_session_playtime:.1f} Hours"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Name", justify="left")
        table.add_column("Time\nPlayed", justify="center")
        table.add_column("Total\nPlaytime", justify="center")

        for game in played_games:
            row = [
                game["name"],
                game["added_time_played"],
                f"{game['total_playtime']} Hours",
            ]
            table.add_row(*row)
        self.console.print(table, new_line_start=True)

    def output_added_games_info(self, added_games):
        """
        Outputs a table of added game stats.
        """
        title = f"Games Added: {len(added_games)}"
        table = Table(
            title=title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Name", justify="left")
        table.add_column("Total Playtime", justify="center")
        for game in added_games:
            playtime = "Unplayed"
            if game["total_playtime"]:
                playtime = f"{game['total_playtime']} Hours"
            row = [
                game["name"],
                playtime,
            ]
            table.add_row(*row)
        self.console.print(table, new_line_start=True)

    def game_check(self, steam_games, sheet_games):
        """
        Checks for new games or game updates from `steam_games` based on `sheet_games`.
        """
        self.total_session_playtime = 0
        added_games = []
        played_games = []
        name_changes = []
        save_every_nth = self.create_save_every_nth()
        # game checking
        print()
        total_games = len(steam_games)
        desc = f"Syncing [bold]{total_games:,}[/bold] Steam Games"
        for game in track(steam_games, description=desc):
            game_name, app_id = game["name"], game["appid"]
            # ignore check
            if self.skip_game(game_name, app_id):
                continue
            # name change check
            # TODO below fails if game is added at this time.
            cur_game_data = self.steam.get_row(app_id)
            if (
                cur_game_data[self.name_col]
                and cur_game_data[self.name_col] != game_name
            ):
                msg = f'Name Change: "{cur_game_data[self.name_col]}" to "{game_name}"'
                self.tracker.info(msg)
                name_change_dict = {
                    "new_name": game_name,
                    "old_name": cur_game_data[self.name_col],
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
            cur_status = cur_game_data[self.play_status_col]
            new_status = self.decide_play_status(cur_status, minutes_played)
            # updates or adds game
            if app_id in sheet_games:
                sheet_games.remove(app_id)
                update_info = self.update_steam_game(
                    app_id,
                    game_name,
                    minutes_played,
                    linux_minutes_played,
                    new_status,
                    cur_status,
                    time_played,
                )
                if update_info:
                    played_games.append(update_info)
            else:
                added_info = self.add_steam_game(
                    app_id,
                    game_name,
                    minutes_played,
                    linux_minutes_played,
                    time_played,
                    new_status,
                )
                added_games.append(added_info)
        # saves each time the checks count is divisible by num
        if self.save_to_file:
            save_every_nth()
        # prints the total games updated and added
        if 0 < len(played_games) < 50:
            self.output_played_games_info(played_games)
        # game names changed
        self.name_change_checker(name_changes)
        # games added
        total_added_games = len(added_games)
        if 0 < total_added_games < 50:
            if total_added_games > 50:
                added_games = added_games[:50]
                print("Showing First 50 Games Added")
            self.output_added_games_info(added_games)
        # checks for removed games
        total_removed_games = len(sheet_games)
        if total_removed_games:
            print("\nGames To Be Removed:", len(sheet_games))
            removed_games_names = [
                self.steam.get_cell(app_id, self.name_col) for app_id in sheet_games
            ]
            print(self.create_and_sentence(removed_games_names))
            response = input("\nDo you want to delele all the above games?\n")
            if response.lower() in ["yes", "y"]:
                for app_id in sheet_games:
                    self.steam.delete_row(str(app_id))
        if self.excel.changes_made and self.save_to_file:
            self.excel.save(use_print=False)
        else:
            print("\nNo Steam games were added or updated")

    def sync_steam_games(self, steam_key: int, steam_id: int):
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        steam_games = self.get_owned_steam_games(steam_key, steam_id)
        sheet_app_ids = [int(app_id) for app_id in self.steam.row_idx.keys()]
        if not steam_games:
            print("\nFailed to retrieve Steam Games")
        else:
            if not sheet_app_ids:
                print(f"Starting First Steam Sync")
            self.game_check(steam_games, sheet_app_ids)
            return
        input()
        exit()

    def skip_game(self, game_name: str = None, app_id: int = None) -> bool:
        """
        Checks if the item should be ignored based on `name` or `app_id`.

        Returns False if neither are given and
        priortizes checking `app_id` if both are given.

        `Name` check looks for keywords and if the name is in the name_ignore_list or media list.

        `app_id` check looks for the `app_id` in the app_id_ignore_list.
        """
        # return False if name and app_id is not given
        if not any([game_name, app_id]):
            raise ValueError("No game_name or app_id was given")
        # ignore by app id
        if app_id and int(app_id) in self.app_id_ignore_list:
            return True
        # ignore by name
        if game_name:
            # creates name ignore list
            media_list = [
                "Amazon Prime Video",
                "HBO GO",
                "HBO Max",
                "Max",
                "Hulu",
                "Media Player",
                "Spotify",
                "Netflix",
                "PlayStationvue",
                "Plex",
                "Pluto",
                "YouTube VR",
                "Youtube",
            ]
            ignore_list = self.name_ignore_list + media_list
            # checks if name means it should be skipped
            cleaned_name = self.unicode_remover(game_name).lower()
            if cleaned_name and cleaned_name in (name.lower() for name in ignore_list):
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
                "test server",
                "bonus content",
                "trial edition",
                "closed test",
                "public test",
                "public testing",
                "directors' commentary",
            ]
            for string in keyword_ignore_list:
                if re.search(rf"\b{string}\b", game_name.lower()):
                    return True
        return False

    def update_steam_game(
        self,
        app_id,
        game_name,
        minutes_played,
        linux_minutes_played,
        new_status,
        cur_status,
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
            self.set_play_status(app_id, new_status, cur_status)
            self.steam.format_row(app_id)
            self.total_session_playtime += hours_played
            # updated game logging
            msg = f"Playtime: {game_name} played for {added_time_played}"
            if self.logging:
                self.tracker.info(msg)
            return {
                "name": game_name,
                "added_time_played": added_time_played,
                "total_playtime": current_hours_played,
            }
        return None

    def add_steam_game(
        self,
        app_id=None,
        game_name=None,
        minutes_played=None,
        linux_minutes_played=None,
        time_played=None,
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
        store_link = self.get_store_link(app_id)
        store_link_hyperlink = f'=HYPERLINK("{store_link}","Store")'
        # misc
        early_access = "No"
        # sets excel column values
        column_info = {
            self.my_rating_col: "",
            self.name_col: game_name,
            self.play_status_col: play_status,
            self.ea_col: early_access,
            self.time_to_beat_col: self.get_time_to_beat(game_name),
            self.hours_played_col: hours_played,
            self.linux_hours_col: linux_hours_played,
            self.time_played_col: time_played,
            self.app_id_col: app_id,
            self.store_link_col: store_link_hyperlink,
            self.date_added_col: dt.datetime.now(),
            self.date_updated_col: dt.datetime.now(),
        }
        if steam_info := self.get_game_info(app_id):
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
        self.steam.format_row(app_id)
        if save_after_add and self.save_to_file:
            self.excel.save(use_print=False)
        return {
            "name": game_name,
            "total_playtime": hours_played or 0,
        }

    def add_ps_game(self, game_name, platform):
        """
        Adds a playstation games.
        """
        # sets excel column values
        column_info = {
            self.date_added_col: dt.datetime.now(),
            self.date_updated_col: dt.datetime.now(),
            self.name_col: game_name,
            self.play_status_col: "Unplayed",
            self.platform_col: platform,
            self.time_to_beat_col: self.get_time_to_beat(game_name),
        }
        self.playstation.add_new_line(column_info)
        # logging
        if self.logging:
            info = f"New PS Game: Added {game_name} for {platform}"
            self.tracker.info(info)
        self.playstation.format_row(game_name)
        return f"\n > {game_name} added"

    def check_playstation_json(self):
        """
        Checks `playstation_games.json` to find out if it is newly updated so
        it can add the new games to the sheet.
        """
        with open(self.ps_data) as file:
            data = json.load(file)
        return data["data"]["purchasedTitlesRetrieve"]["games"]

    def update_playstation_data(self):
        """
        Opens playstation data json file and web json with latest data
        for manual updating.
        """
        if not self.ps_data.exists():  # checks if json exists
            print("\nPlayStation JSON does not exist.\nCreating file now.\n")
            self.ps_data.touch()
        subprocess.Popen(f'notepad "{self.ps_data}"')
        webbrowser.open(self.playstation_data_link)
        webbrowser.open("https://store.playstation.com/")
        input("\nPress Enter when done.\n")

    def sync_playstation_games(self):
        """
        Adds playstation games to excel using the given `games` variable.
        """
        resonse = input("\nDo you want to get your most recent Playstation data?\n")
        if resonse.lower() in ["yes", "y"]:
            self.update_playstation_data()
        print("\nChecking for new games for Playstation")
        games = self.check_playstation_json()
        if not games:
            print("No Playstation Games Found")
            return
        save_every_nth = self.create_save_every_nth()
        added_ps_games = []
        updated_ps_games = []
        all_game_names = []
        print()
        desc = f"Syncing [bold]{len(games):,}[/bold] Playstation Games"
        for game in track(games, description=desc):
            game_name = self.unicode_remover(game["name"])
            all_game_names.append(game_name)
            latest_platform = "PS5"
            platform = game["platform"]
            if not game["isActive"]:
                print(game_name, "is not active")
            if not game["isDownloadable"]:
                print(game_name, "is not downloadable")
            # ignore check
            if self.skip_game(game_name):
                continue
            # updates existing games
            if game_name in self.playstation.row_idx.keys():
                cur_platform = self.playstation.get_cell(game_name, self.platform_col)
                # sets platform to latest one if that version is owned
                if cur_platform != latest_platform and platform == latest_platform:
                    self.playstation.update_cell(
                        game_name,
                        self.platform_col,
                        latest_platform,
                    )
                    updated_info = f"\n > {game_name} Updated to {latest_platform}"
                    updated_ps_games.append(updated_info)
                # ps plus
                if not game["subscriptionService"] != "NONE":
                    self.playstation.update_cell(game_name, "PS Plus", "Yes")
                else:
                    self.playstation.update_cell(game_name, "PS Plus", "")

            # adds new games
            else:
                added_info = self.add_ps_game(game_name, platform)
                added_ps_games.append(added_info)
            save_every_nth()
        # checking for removed games
        # print("\nall games\n", all_game_names)
        # for game_row in self.playstation.row_idx.keys():
        #     print(game_row)
        #     if game_row not in all_game_names:
        #         print("removed", game_row)
        # added
        if total_added := len(added_ps_games):
            print(f"\nAdded {total_added} PS4/PS5 Games")
            for game_info in added_ps_games:
                print(game_info)
        # updated
        if total_updated := len(updated_ps_games):
            print(f"\nUpdated {total_updated} PS4 Games to {latest_platform} versions")
            for game_info in updated_ps_games:
                print(game_info)
        # removed
        # TODO add info on removed ps games
        # saving
        if total_added or total_updated and self.save_to_file:
            self.excel.save(use_print=False)

    def play_status_picker(self):
        """
        Shows a list of Play Status's to choose from.
        Respond with the playstatus or numerical postion of the status from the list.
        """
        prompt = (
            self.create_and_sentence(list(self.play_status_choices.values())) + "\n:"
        )
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
        self.console.print(f"\nPicked: [secondary]{picked_game_name}[/]")
        # allows getting another random pick
        while not input().lower() in ["no", "n", "cancel", "stop"]:
            if not choice_list:
                print(f"All games have already been picked.\n")
                return
            picked_game_name, choice_list = self.get_random_game_name(play_status)
            self.console.print(f"Picked: [secondary]{picked_game_name}[/]")

    def get_favorite_games(self, min_rating=8):
        """
        gets favorite games from excel file as a list of dicts
        """
        # starts check with progress bar
        print(f"Minimum Rating set to {min_rating}\n")
        games = []
        desc = "Finding Favorite Games"
        for app_id in track(self.steam.row_idx.keys(), description=desc):
            game_data = self.steam.get_row(app_id)
            if game_data[self.my_rating_col] == None:
                continue
            if game_data[self.my_rating_col] >= min_rating and app_id:
                game_info = self.get_game_info(app_id)
                if not game_info or not "on_sale" in game_info.keys():
                    continue
                # create game_dict
                game_dict = {
                    self.date_updated_col: dt.datetime.now(),
                    self.name_col: game_info["game_name"],
                    "Discount": game_info["discount"] * 0.01,
                    "Price": game_info["price"],
                    self.my_rating_col: game_data[self.my_rating_col],
                    self.steam_rev_per_col: game_info[self.steam_rev_per_col],
                    self.steam_rev_total_col: game_info[self.steam_rev_total_col],
                    self.store_link_col: game_data[self.store_link_col],
                    self.time_to_beat_col: game_data[self.time_to_beat_col],
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
                (type(price) is str and "$" not in price),
                discount == 0,
            ]
            if any(skip_checks):
                continue
            self.sales.add_new_line(game)
        self.sales.format_all_cells()
        if self.save_to_file:
            self.excel.save(use_print=False)

    def sync_favorite_games_sales(self):
        """
        Gets sale information for games that are at a minimun rating or higher.
        Rating is set up using an input after running.
        """
        # sets minimum rating to and defaults to 8 if response is blank or invalid
        min_rating = IntPrompt.ask(
            "\nWhat is the minimum rating for this search? (1-10)",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default=8,
            show_choices=False,
            show_default=True,
        )
        # delete old game sales
        cur_rows = [game for game in self.sales.row_idx.keys()].reverse()
        if cur_rows:
            for game in cur_rows:
                self.sales.delete_row(game)
        # get new game sales
        games = self.get_favorite_games(min_rating)
        total_sales = len(games)
        # prints info
        print(f"\nFound {total_sales} Favorite Game Sales:\n")
        self.update_sales_sheet(games=games)

    def update_player_counts(self, df):
        """
        Updates game player counts using the Steam API.
        """
        last_num = 15
        app_ids = []
        print(f"\n1. Update only the {last_num} latest games\n2. Update all games")
        msg = "Pick one:\n"
        response = IntPrompt.ask(
            msg,
            choices=["1", "2"],
            default="1",
            show_choices=False,
            show_default=False,
        )
        update_type = ""
        if response == 1:
            recently_played = App.find_recent_games(df, self.date_updated_col, 30)
            app_ids = [game[self.app_id_col] for game in recently_played]
            update_type = "Recent"
        elif response == 2:
            app_ids = self.steam.row_idx.keys()
            update_type = "All"
        print()
        desc = f"Updating {update_type} Player Counts"
        for app_id in track(app_ids, description=desc):
            player_count = self.get_steam_game_player_count(app_id, self.steam_key)
            self.steam.update_cell(app_id, self.steam_player_count_col, player_count)
            self.api_sleeper("steam_player_count")
        self.excel.save(use_print=False)

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
            print(f"\nUpdated to {new_hours} Hours")
        self.set_date_updated(game_idx)

    def open_log(self):
        osCommandString = f"notepad.exe {self.tracker_log_path}"
        os.system(osCommandString)

    @staticmethod
    def advanced_picker(choices, title):
        """
        Choice picker using the advanced and less compatible Pick module.
        """
        options = [choice[0] for choice in choices]
        selected_index = pick(options, title)[1]
        return choices[selected_index]

    def basic_picker(self, choices, title):
        """
        Choice picker using the basic and more compatible IntPrompt function within the Rich module.
        """
        allowed_choices = []
        for count, (choice, action) in enumerate(choices):
            allowed_choices.append(str(count + 1))
            msg = f"[b]{count+1}.[/] [underline]{choice}[/]"
            self.console.print(msg, highlight=False)
        num = IntPrompt.ask(
            title,
            choices=allowed_choices,
            default=1,
            show_choices=False,
            show_default=False,
        )
        return choices[num - 1]

    def pick_task(self, choices, repeat=True):
        """
        Allows picking a task to do next using a matching number.
        """
        if not sys.stdout.isatty():
            # runs if it is not an interactable terminal
            print("\nSkipping Task Picker.\nInput can't be used")
            return
        print()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()
        selected = None
        if term_program != "vscode":
            input("Press Enter to Pick Next Action:")
            title = "What do you want to do? (press SPACE to mark, ENTER to continue):"
            selected = self.advanced_picker(choices, title)
        else:
            title = "What do you want to do?"
            selected = self.basic_picker(choices, title)
        if selected:
            name, func = selected[0], selected[1]
            msg = f"\n[b underline]{name}[/] Selected"
            self.console.print(msg, highlight=False)
            func()  # runs chosen function
            if "exit" in name.lower():
                return
            if repeat:
                self.pick_task(choices, repeat)

    def game_library_actions(self, df):
        """
        Gives a choice of actions for the current game library.
        """
        # lamdas
        output_statistics_func = lambda: self.output_statistics(df)
        update_player_counts_func = lambda: self.update_player_counts(df)
        # choice picker
        choices = [
            ("Exit and Open the Excel File", self.excel.open_excel),
            ("Random Game Explorer", self.pick_random_game),
            ("Player Counts Sync", update_player_counts_func),
            ("Favorite Games Sales Sync", self.sync_favorite_games_sales),
            ("Game Data Sync", self.update_all_game_data),
            ("Statistics Display", output_statistics_func),
            ("Steam Friends List Sync", self.sync_friends_list),
            ("Playstation Games Sync", self.sync_playstation_games),
            # ("Update All Cell Formatting", self.steam.format_all_cells),
            ("Open Log", self.open_log),
        ]
        self.pick_task(choices)
        exit()

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
        self.excel.save(use_print=False)

    @keyboard_interrupt
    def run(self):
        """
        Main run function.
        """
        self.config_check()
        self.console.print(self.title, style="primary")

        # prints date
        now = dt.datetime.now()
        formatted_date = f"[secondary]{now.strftime('%A, %B %d, %Y')}[/]"
        formatted_time = f"[secondary]{now.strftime('%I:%M %p')}[/]"
        date = f"{formatted_date} [dim]|[/] {formatted_time}"
        self.console.print(date)

        # internet checks
        internet = self.check_internet_connection()
        if internet:
            self.sync_steam_games(self.steam_key, self.steam_id)
        else:
            self.console.print("\nNo Internet Detected", style="warning")

        df = self.steam.create_dataframe(na_vals=self.na_values)
        self.output_recently_played_games(df)

        # extra data updates
        if internet:
            self.updated_game_data(df)
            self.get_friends_list_changes()

        self.show_errors()
        self.game_library_actions(df)


if __name__ == "__main__":
    App = Tracker(save=True)
    App.run()
