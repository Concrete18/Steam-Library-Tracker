# standard library
import os, sys, math, traceback, time
import datetime as dt
from typing import Any

# third-party imports
import pandas as pd
from difflib import SequenceMatcher
from pick import pick
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.progress import track, Progress
from rich.table import Table
from rich.theme import Theme
from unidecode import unidecode

# local imports
from setup import Setup
from library.backup import Backup
from library.steam.steam import *
from library.game import *
from library.random_game import RandomGame
from library.game_skipper import GameSkipper
from library.utils.api_throttler import ApiThrottler
from library.action_picker import advanced_picker, action_picker
from library.date_updater import *
from library.utils.utils import *
from library.logger import Logger
from library.utils.internet import Internet

# my package imports
from easierexcel import Excel, Sheet


class Tracker:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    APP_TITLE = "Steam Library Tracker"

    # config init
    # -----------------------------
    setup = Setup()
    config_path, config_data, ignore_data, excel_options = setup.run()

    # steam_data
    # -----------------------------
    steam_data = config_data.get("steam_data", {})
    if not steam_data:
        input("Steam Config not found.")
        sys.exit(0)
    steam_key = steam_data.get("api_key", None)
    steam_id = steam_data.get("steam_id", None)
    steam_id_3 = steam_data.get("steam_id_3", None)
    steam_folder = steam_data.get("steam_folder", None)
    steam_library = steam_data.get("steam_library", None)
    library_path = f"{steam_folder}/steamapps/libraryfolders.vdf"
    local_config_path = f"{steam_folder}/userdata/{steam_id_3}/config/localconfig.vdf"
    workshop_path = f"{steam_library}/steamapps/workshop/content"

    # settings
    # -----------------------------
    excel_filename = config_data["settings"]["excel_filename"]
    backup = Backup(excel_filename, redundancy=4)
    logging = config_data["settings"]["logging"]

    # misc
    # -----------------------------
    NAME_IGNORE_LIST = [string.lower() for string in ignore_data["name_ignore_list"]]
    APP_ID_IGNORE_LIST = ignore_data["app_id_ignore_list"]
    game_skipper = GameSkipper(NAME_IGNORE_LIST, APP_ID_IGNORE_LIST)
    dataframe = None

    # logging setup
    # -----------------------------
    if logging:
        Log = Logger()
        main_log_path = "logs/main.log"
        main_log = Log.create_log(name="main", log_path=main_log_path)
        friend_log = Log.create_log(name="friend", log_path="logs/friend.log")
        error_log = Log.create_log(name="base_error", log_path="logs/error.log")

    # rich console
    # -----------------------------
    custom_theme = Theme(
        {
            "primary": "bold deep_sky_blue1",
            "secondary": "bold pale_turquoise1",
            # error
            "info": "dim cyan",
            "warning": "bold magenta",
            "danger": "bold red",
            # color scale
            "top_scale": "bold green1",
            "high_scale": "bold spring_green1",
            "mid_scale": "bold cyan1",
            "bottom_scale": "bold steel_blue1",
            "faded": "grey58",
            # play status
            "endless": "bold green4",
            "finished": "bold green1",
            "played": "bold light_goldenrod2",
            "unplayed": "bold sky_blue2",
            "waiting": "bold dark_goldenrod",
            "quit": "bold deep_pink2",
            "replay": "bold dodger_blue2",
        }
    )
    console = Console(theme=custom_theme)

    # misc
    throttler = ApiThrottler()
    internet = Internet()

    # sets play status choices for multiple functions
    # -----------------------------
    PLAY_STATUS_CHOICES = (
        "Played",
        "Unplayed",
        "Finished",
        "Endless",
        "Replay",
        "Waiting",
        "Quit",
        "Ignore",
    )

    # columns
    # -----------------------------
    EXCEL_COLUMNS = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        last_played_col := "Last Played",
        my_rating_col := "My Rating",
        steam_rev_per_col := "Steam Review Percent",
        steam_rev_total_col := "Steam Review Total",
        price_col := "Price",
        discount_col := "Discount",
        name_col := "Name",
        play_status_col := "Play Status",
        platform_col := "Platform",
        dev_col := "Developers",
        pub_col := "Publishers",
        genre_col := "Genre",
        user_tags_col := "User Tags",
        ea_col := "Early Access",
        installed_col := "Installed",
        time_played_col := "Time Played",
        hours_played_col := "Hours Played",
        linux_hours_col := "Linux Hours",
        last_play_time_col := "Last Play Time",
        store_link_col := "Store Link",
        release_col := "Release Year",
        app_id_col := "App ID",
    ]

    def __init__(self, save: bool) -> None:
        """
        Game Library Tracking Class.
        """
        self.save_to_file = save
        if not self.steam_id:
            self.update_steam_id()
        self.load_excel_file()

    def load_excel_file(self):
        """
        Loads Excel data from file.
        """
        self.excel = Excel(self.excel_filename, use_logging=self.logging)
        self.steam = Sheet(
            excel_object=self.excel,
            sheet_name="Steam",
            column_name="App ID",
            options=self.excel_options,
        )
        self.sales = Sheet(
            excel_object=self.excel,
            sheet_name="Sales",
            column_name="Name",
            options=self.excel_options,
        )

    def update_steam_id(self):
        """
        Updates the steam id in the config using the given vanity url if present.
        """
        if self.steam_id:
            self.config_data["settings"]["steam_id"] = self.steam_id
            save_json(self.config_data, self.config_path)
        else:
            input("Steam ID is missing.")
            sys.exit(0)

    def auto_backup(self, check_freq_days: int = 14) -> None:
        """
        Auto backs up the excel file every `check_freq_days` days.
        """
        CONFIG_ENTRY = "excel_backup"
        if recently_executed(self.config_data, CONFIG_ENTRY, check_freq_days):
            return
        if self.backup.run():
            self.console.print("\nBacked Up Excel File", style="secondary")
            update_last_run(self.config_data, self.config_path, CONFIG_ENTRY)
        else:
            self.console.print("\nFailed to backed Up Excel File", style="warning")

    def sync_friends_list(self, check_freq_days: int = 7) -> None:
        """
        Checks for changes to your friends list.
        Shows a table of new and removed friends Steam ID's and usernames.
        """
        if not self.internet.online:
            print("\nFriends can't be synced without Internet")
            return
        # check last run
        if recently_executed(self.config_data, "friends_sync", check_freq_days):
            return

        # get friends
        print("\nStarting Steam Friends Sync")
        prev_friend_ids = self.config_data["friend_ids"]
        friend_data = get_steam_friends(self.steam_key, self.steam_id)
        if not friend_data:
            print("No Friends data found.")
            return
        cur_friend_ids = [friend["steamid"] for friend in friend_data]
        # finds changes
        additions, removals = get_friends_list_changes(prev_friend_ids, cur_friend_ids)
        if not additions and not removals:
            self.console.print("No friends were added or removed", style="secondary")
            return
        # view changes
        TABLE_TITLE = "Friends List Updates"
        table = Table(
            title=TABLE_TITLE,
            show_lines=True,
            title_style="bold",
            style="green3",
        )
        table.add_column("Type", justify="center")
        table.add_column("Username", justify="left", min_width=15)
        table.add_column("Steam ID", justify="left")
        # removals
        for steam_id in removals:
            username = get_steam_username(steam_id, self.steam_key) or "Unknown"
            row = [
                "Removed",
                username,
                steam_id,
            ]
            table.add_row(*row)
            # logging
            msg = f"Friends List Removal: {username}"
            self.friend_log.info(msg)
        # additions
        for steam_id in additions:
            username = get_steam_username(steam_id, self.steam_key)
            row = [
                "Added",
                username,
                steam_id,
            ]
            table.add_row(*row)
            # logging
            msg = f"Friends List Addition: {username}"
            self.friend_log.info(unidecode(msg))
        self.console.print(table, new_line_start=True)
        update_last_run(self.config_data, self.config_path, "friends_sync")
        # update friend data in config
        self.config_data["friend_ids"] = cur_friend_ids
        save_json(self.config_data, self.config_path)

    def sync_all(self):
        """
        Runs Steam synchronization.
        """
        self.sync_steam_games(self.steam_key, self.steam_id)
        self.dataframe = self.steam.create_dataframe(na_vals=["-", "NaN"])
        self.output_recently_played_games(self.dataframe)
        # TODO add review score tracking
        self.updated_game_data(self.dataframe)
        self.sync_friends_list()

    def create_save_every_nth(self, save_on_nth: int = 20):
        counter = 0

        def save_every_nth():
            nonlocal counter
            counter += 1
            if counter % save_on_nth == 0:
                self.excel.save(use_print=False, backup=False)
                counter = 0

        return save_every_nth

    def set_play_status(
        self, app_id: int, new_status: str | None, cur_status: str = ""
    ):
        """
        Sets `app_id`'s Play Status cell to `new_status` if it the current status is unplayed.
        """
        if cur_status == "Unplayed" and new_status != cur_status:
            return self.steam.update_cell(str(app_id), self.play_status_col, new_status)

    def set_date_updated(self, app_id):
        """
        Sets `app_id`'s Date Updated cell to the current date.
        """
        cur_date = dt.datetime.now()
        return self.steam.update_cell(app_id, self.date_updated_col, cur_date)

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
            by=self.last_played_col, ascending=False
        ).to_dict(orient="records")

    def get_game_column_dict(self, game: Game) -> dict:
        """
        Returns a dict of column names and the value for that column.
        """
        return {
            self.dev_col: game.developer or "-",
            self.pub_col: game.publisher or "-",
            self.steam_rev_per_col: game.review_percent or "-",
            self.steam_rev_total_col: game.review_total or "-",
            self.price_col: game.price or "-",
            self.discount_col: game.discount or "-",
            self.genre_col: game.genre_str or "-",
            self.user_tags_col: game.tags_str or "-",
            self.ea_col: game.early_access_str or "-",
            self.store_link_col: create_hyperlink(game.store_link, "Store") or "-",
            self.release_col: game.release_year or "-",
        }

    def update_extra_game_info(self, app_ids: list[int], update_type: str | None):
        """
        Updates info that changes often enough that it needs to be updated manually.
        """
        save_every_nth = self.create_save_every_nth()
        print()
        cur_itr = 0
        if not update_type:
            update_type = "Some"
        desc = f"Syncing {update_type} Game Data"
        for app_id in track(app_ids, description=desc):
            game_row = self.steam.get_row(app_id)
            if game_row.get(self.store_link_col) == "Delisted":
                continue
            # get new data from the internet
            app_details = get_app_details(app_id)
            if app_details.get("store") == "delisted":
                self.steam.update_cell(str(app_id), self.store_link_col, "Delisted")
                continue
            game = get_game_info(app_details, self.steam_key)
            game_data = self.get_game_column_dict(game)
            # update data
            for column, data in game_data.items():
                if not data:
                    continue
                if not game_row.get(self.ea_col):
                    continue
                self.steam.update_cell(str(app_id), column, data)
            # saves data
            if self.save_to_file:
                save_every_nth()
            # title progress percentage
            cur_itr += 1
            progress = cur_itr / len(app_ids) * 100
            set_title(f"{progress:.1f}% - {self.APP_TITLE}")
        self.excel.save(use_print=False)
        set_title(self.APP_TITLE)

    def sync_game_data(self, df: pd.DataFrame | None):
        """
        Gets app_ids and updates games using update_extra_game_info func.
        """
        if not self.internet.online:
            print("Game Data can't be synced without Internet")
            return
        if not isinstance(df, pd.DataFrame):
            print("Dataframe is invalid")
            return
        self.load_excel_file()
        app_ids, update_type = self.game_select(df, last_num=50)
        self.update_extra_game_info(app_ids, update_type)

    def check_workshop_size(self):
        """
        Checks the directory size for each games workshop folder.
        """
        if not self.internet.online:
            print("\nWorkshop can't be checked without Internet")
            return
        print()
        total = 0
        with Progress(transient=True) as progress:
            progress.add_task("Checking Workshop Size", total=None)

            app_list = get_app_list()
            entry_list = workshop_size(self.workshop_path, app_list)

            table_title = f"Game Workshop Sizes"
            table = Table(
                title=table_title,
                show_lines=True,
                title_style="bold",
                style="deep_sky_blue1",
            )
            table.add_column("Name", justify="left")
            table.add_column("Size", justify="right")
            # add rows
            for entry in entry_list:
                name = entry["name"]
                size, unit = convert_size(entry["bytes"])
                total += entry["bytes"]
                file_size = f"{size:,} {unit}"
                # row setup
                row = [name, file_size]
                table.add_row(*row)
        # print table
        self.console.print(table, new_line_start=False)
        total_size, unit = convert_size(total)
        self.console.print(f"[b]Total Workshop Size:[/] {total_size:,} {unit}")

    def get_recent_app_ids(
        self, df: pd.DataFrame, column: str, n_days: int = 30
    ) -> list[int]:
        """
        Gets the app_ids of the recently played games via a dataframe.
        """
        # check last run
        if recently_executed(self.config_data, "recently_played", n_days):
            return []
        # get recently played games
        recently_played = self.find_recent_games(df, column, n_days)
        recently_app_ids = [game[self.app_id_col] for game in recently_played]
        return recently_app_ids

    def app_ids_to_names(self, app_ids: list[int]) -> list[Any]:
        """
        Converts a list of App ID's into a list of the games matching the ID's.
        """
        return [self.steam.get_cell(app_id, self.name_col) for app_id in app_ids]

    def updated_game_data(
        self,
        df: pd.DataFrame,
        skip_filled: bool = True,
        skip_by_play_status: bool = False,
    ):
        """
        Updates game data for games that were played recently and/or are missing data.

        Use `skip_filled` to skip non blank entries.

        Use `skip_by_play_status` to only check games with a specific play status.
        """
        if not self.internet.online:
            return
        # starts the update list with recently played games
        update_list = self.get_recent_app_ids(df, self.last_played_col, n_days=30)
        column_list = [
            self.genre_col,
            self.pub_col,
            self.dev_col,
            self.steam_rev_per_col,
            self.steam_rev_total_col,
            self.user_tags_col,
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
                    if cell is None and app_id not in update_list:
                        update_list.append(app_id)
                        continue
            else:
                update_list.append(app_id)
        # checks if data should be updated
        if update_list:
            update_games_total = len(update_list)
            if update_games_total <= 5:
                game_names = self.app_ids_to_names(update_list)
                game_list_str = list_to_sentence(game_names)
                msg = f"\n{game_list_str}\n\nDo you want to update data for the above {update_games_total} games?"
            else:
                msg = f"\nDo you want to update data for {update_games_total} games?"
            if not is_response_yes(msg):
                return
        else:
            return
        # updates game data
        try:
            self.update_extra_game_info(update_list, "Recent")
            if update_list:
                update_last_run(self.config_data, self.config_path, "recently_played")
            print(f"\nUpdated Data for {len(update_list)} games")
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            if self.save_to_file:
                self.excel.save(use_print=False, backup=False)

    @staticmethod
    def days_since_format(days: int) -> str:
        """
        Formats days since for display in a Rich Table.
        """
        if days == 0:
            return f"[top_scale]{days}"
        elif days <= 2:
            return f"[high_scale]{days}"
        elif days <= 4:
            return f"[mid_scale]{days}"
        elif days <= 6:
            return f"[bottom_scale]{days}"
        else:
            return f"[faded]{days}"

    @staticmethod
    def play_status_format(play_status: str) -> str:
        """
        Formats play status for display in a Rich Table.
        """
        if play_status.lower() == "ignore":
            return f"[faded]{play_status}"
        return f"[{play_status.lower()}]{play_status}"

    def output_recently_played_games(self, df: pd.DataFrame, n_days: int = 7) -> None:
        """
        Creates a table with the recently played Games.
        """
        recently_played_games = self.find_recent_games(df, self.last_played_col, n_days)
        # creates table
        table_title = f"Recently Played Games\nWithin {n_days} Days"
        table = Table(
            title=table_title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Days\nSince", justify="center")
        table.add_column("Last Played", justify="center")
        table.add_column("Name", justify="left", min_width=30)
        table.add_column("Play\nStatus", justify="center")
        table.add_column("Hours\nPlayed", justify="right")
        table.add_column("Last\nPlay Time", justify="center")
        # add rows
        for game in recently_played_games[:10]:
            # days since
            last_played_dt = game.get(self.last_played_col)
            last_played = ""
            days_since = ""
            # BUG when a game is added without being played before
            # add a test once the problem is discovered
            try:
                if last_played_dt:
                    last_played = last_played_dt.strftime("%a %b %d, %Y")
                else:
                    last_played = "-"
                if last_played_dt:
                    days_since_int = abs(get_days_since(last_played_dt))
                    days_since = self.days_since_format(days_since_int)
            except:
                pass
            game_name = game[self.name_col]
            play_status = self.play_status_format(game[self.play_status_col])
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
            # row setup
            row = [
                days_since,
                last_played,
                game_name,
                play_status,
                hours_played,
                last_play_time,
            ]
            table.add_row(*row)
        # print table
        self.console.print(table, new_line_start=True)

    def find_tag_rating_avg(self, df: pd.DataFrame):
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

    def output_statistics(self, df: pd.DataFrame | None) -> None:
        """
        Outputs tables of game library statistics.
        """
        print("Statistics are currently a work in progress\n")
        # TODO switch to new system
        if not isinstance(df, pd.DataFrame):
            return

    @staticmethod
    def decide_play_status(
        play_status: str | None, minutes_played: float | None
    ) -> str | None:
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
        if isinstance(minutes_played, float) or isinstance(minutes_played, int):
            if minutes_played >= 30:
                return "Played"
        if play_status != "Must Play":
            return "Unplayed"
        return play_status

    def name_change_checker(self, name_changes: list[dict]) -> None:
        """
        Checks the `name_changes` to see if they contain any
        name changes to possibly fulfill.
        """
        for names_dict in name_changes:
            new_name = names_dict["new_name"]
            old_name = names_dict["old_name"]
            msg = f'Do you want to update "{old_name}"\'s name to {new_name}?:\n'
            if is_response_yes(msg):
                app_id = names_dict["app_id"]
                self.steam.update_cell(app_id, self.name_col, new_name)

    def output_name_changes(self, name_changes: list[dict]) -> None:
        """
        Outputs a table of name changes.
        """
        table = Table(
            title=f"Name Changes: {len(name_changes)}",
            show_lines=True,
            title_style="bold",
            style="green3",
        )
        table.add_column("New Name", justify="left")
        table.add_column("Old Name", justify="left")
        for names_dict in name_changes:
            row = [names_dict["new_name"], names_dict["old_name"]]
            table.add_row(*row)
        self.console.print(table, new_line_start=True)

    def output_played_games_info(self, played_games: list[dict]) -> None:
        """
        Outputs a table of played game stats.
        """
        total_games_played = len(played_games)
        table_title = f"Games Played: {len(played_games)}"
        if total_games_played > 1:
            table_title += f"\nLast Session: {self.total_session_playtime:.1f} Hours"
        table = Table(
            title=table_title,
            show_lines=True,
            title_style="bold",
            style="green3",
        )
        table.add_column("Name", justify="left", min_width=30)
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

    def output_added_games_info(self, added_games: list[dict]) -> None:
        """
        Outputs a table of added game stats.
        """
        table = Table(
            title=f"Games Added: {len(added_games)}",
            show_lines=True,
            title_style="bold",
            style="green3",
        )
        table.add_column("Name", justify="left", min_width=30)
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

    def sync_steam_games_with_sheet(
        self, steam_games: list[dict], sheet_games: list[int]
    ):
        """
        Checks for new games or game updates from `steam_games` based on `sheet_games`.
        """
        # TODO break this down into smaller function
        self.total_session_playtime = 0
        added_games = []
        played_games = []
        name_changes = []
        print()
        total_games = len(steam_games)
        desc = f"Syncing [bold]{total_games:,}[/bold] Steam Games"
        installed_app_ids = get_installed_app_ids(self.library_path)
        local_config = get_local_config_data(self.local_config_path)
        for game in track(steam_games, description=desc):
            game_name, app_id = game["name"], game["appid"]
            # sets last played using localconfig.vdf
            last_played, _ = get_game_local_data(app_id, local_config)
            if isinstance(last_played, int):
                last_played = dt.datetime.fromtimestamp(last_played)
            else:
                last_played = "-"
            # ignore check
            if self.game_skipper.skip_game(game_name, app_id):
                continue
            # name change check
            cur_game_data = self.steam.get_row(app_id)
            old_name = cur_game_data[self.name_col]
            new_name = game_name
            if old_name and old_name != new_name:
                msg = f'Name Change: "{old_name}" to "{new_name}"'
                self.main_log.info(msg)
                name_changes.append(
                    {
                        "new_name": new_name,
                        "old_name": old_name,
                        "app_id": app_id,
                    }
                )
            # sets play time earlier so it only needs to be set up once
            minutes_played = game.get("playtime_forever", 0)
            time_played = convert_time_passed(minutes=minutes_played)
            linux_minutes_played = game.get("playtime_linux_forever", 0)
            # play status
            cur_status = cur_game_data[self.play_status_col]
            new_status = self.decide_play_status(cur_status, minutes_played)
            installed = app_id in installed_app_ids
            # updates or adds game
            if app_id in sheet_games:
                sheet_games.remove(app_id)
                update_info = self.update_steam_game(
                    app_id=app_id,
                    game_name=game_name,
                    minutes_played=minutes_played,
                    linux_minutes_played=linux_minutes_played,
                    new_status=new_status,
                    cur_status=cur_status,
                    time_played=time_played,
                    last_played=last_played,
                    installed=installed,
                )
                if update_info:
                    played_games.append(update_info)
            else:
                added_info = self.add_steam_game(
                    app_id=app_id,
                    game_name=game_name,
                    minutes_played=minutes_played,
                    linux_minutes_played=linux_minutes_played,
                    time_played=time_played,
                    last_played=last_played,
                    play_status=new_status,
                    get_internet_info=len(added_games) <= 10,
                    installed=installed,
                )
                added_games.append(added_info)
        # prints the total games updated and added
        if 0 < len(played_games) < 50:
            self.output_played_games_info(played_games)
        # game names change
        if name_changes:
            for names_dict in name_changes:
                new_name = names_dict["new_name"]
                app_id = names_dict["app_id"]
                self.steam.update_cell(app_id, self.name_col, names_dict["new_name"])
            self.output_name_changes(name_changes)
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
            removed_game_names = []
            for app_id in sheet_games:
                found_app_id = self.steam.get_cell(app_id, self.name_col)
                if isinstance(found_app_id, str):
                    removed_game_names.append(found_app_id)
            removed_games_names_str = list_to_sentence(removed_game_names)
            if is_response_yes(
                f"\nDo you want to delete all the following games?\n{removed_games_names_str}"
            ):
                for app_id in sheet_games:
                    self.steam.delete_row(str(app_id))
        if self.excel.changes_made and self.save_to_file:
            self.excel.save(use_print=False)
        else:
            print("\nNo Steam games were added or updated")

    def sync_steam_games(self, steam_key: str, steam_id: int) -> None:
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        owned_games = []
        if not self.internet.online:
            return
        try:
            owned_games = get_owned_steam_games(steam_key, steam_id)
        except requests.ConnectTimeout:
            text = "\nFailed to retrieve Steam Games\nSteam Servers may be down"
            input(text)
            # TODO make it easy to rerun when the internet or servers are working again
            return
        except:
            time.sleep(15)
            owned_games = get_owned_steam_games(steam_key, steam_id)
        sheet_app_ids = [int(app_id) for app_id in self.steam.row_idx.keys()]
        if not sheet_app_ids:
            print(f"\nStarting First Steam Sync")
        if not owned_games:
            print("No Steam Games were Found")
            return
        self.sync_steam_games_with_sheet(owned_games, sheet_app_ids)

    def update_steam_game(
        self,
        app_id: int,
        game_name: str,
        minutes_played: float,
        linux_minutes_played: float,
        new_status: str | None,
        cur_status: str,
        installed: bool = False,
        time_played: str | None = None,
        last_played: dt.datetime | str | None = "-",
    ) -> dict | None:
        """
        Updates the games playtime and play status if they changed.
        """
        installed_value = "Yes" if installed else "No"
        self.steam.update_cell(str(app_id), self.installed_col, installed_value)
        prev_hours = self.steam.get_cell(app_id, self.hours_played_col)
        if isinstance(prev_hours, int) or isinstance(prev_hours, str):
            prev_hours = float(prev_hours)
        elif not isinstance(prev_hours, float):
            prev_hours = 0.0
        cur_hours = get_hours_played(minutes_played)
        if not cur_hours:
            return
        if last_played:
            self.steam.update_cell(str(app_id), self.last_played_col, last_played)
        # only updates if new play time occurred
        if cur_hours > prev_hours:
            hours_played = cur_hours - prev_hours
            self.steam.update_cell(str(app_id), self.hours_played_col, cur_hours)
            cur_linux_hours = get_hours_played(linux_minutes_played)
            self.steam.update_cell(str(app_id), self.linux_hours_col, cur_linux_hours)
            added_time = convert_time_passed(hours=hours_played)
            self.steam.update_cell(str(app_id), self.last_play_time_col, added_time)
            self.steam.update_cell(str(app_id), self.time_played_col, time_played)
            self.set_date_updated(app_id)
            self.set_play_status(app_id, new_status, cur_status)
            self.steam.format_row(str(app_id))
            self.total_session_playtime += hours_played
            # updated game logging
            msg = f"Playtime: {game_name} played for {added_time}"
            if self.logging:
                self.main_log.info(msg)
            return {
                "name": game_name,
                "added_time_played": added_time,
                "total_playtime": cur_hours,
            }

    def add_steam_game(
        self,
        app_id: int,
        game_name: str,
        minutes_played: float | None = None,
        linux_minutes_played: float | None = None,
        time_played: str | None = None,
        last_played: dt.datetime | str | None = None,
        play_status: str | None = None,
        get_internet_info: bool = True,
        save_after_add: bool = False,
        installed: bool = False,
    ) -> dict:
        """
        Adds a game with the game_name, hours played using `minutes_played` and `play_status`.

        If save is True, it will save after adding the game.
        """
        hours_played = get_hours_played(minutes_played)
        cur_date = dt.datetime.now()
        base_data = {
            self.name_col: game_name,
            self.app_id_col: app_id,
            self.play_status_col: play_status,
            self.hours_played_col: hours_played,
            self.linux_hours_col: get_hours_played(linux_minutes_played),
            self.time_played_col: time_played,
            self.last_played_col: last_played,
            self.installed_col: "Yes" if installed else "No",
            self.date_added_col: cur_date,
            self.date_updated_col: cur_date,
        }
        extra_data = {}
        if get_internet_info:
            app_details = get_app_details(app_id)
            if app_details:
                game = get_game_info(app_details, self.steam_key)
                extra_data = self.get_game_column_dict(game)
        game_data = {**base_data, **extra_data}

        self.steam.add_new_line(game_data)
        # logging
        if self.logging:
            time_played_str = time_played or "no time"
            info = f"New Game: Added {game_name} with {time_played_str} played"
            self.main_log.info(info)
        self.steam.format_row(str(app_id))
        if save_after_add and self.save_to_file:
            self.excel.save(use_print=False, backup=False)
        return {
            "name": game_name,
            "total_playtime": hours_played or 0,
        }

    def start_random_game_picker(self) -> None:
        """
        Allows you to pick a play_status or installed status to have a random game chosen from.
        """
        Picker = RandomGame(
            steam_sheet=self.steam,
            name_column=self.name_col,
            installed_column=self.installed_col,
            play_status_choices=self.PLAY_STATUS_CHOICES,
            play_status_column=self.play_status_col,
        )
        Picker.random_game_picker()

    def get_favorite_games(self, min_rating: int = 8) -> list[tuple[Game, int]]:
        """
        gets favorite games from excel file as a list of dicts
        """
        games = []
        desc = "Finding Favorite Games"
        for app_id in track(self.steam.row_idx.keys(), description=desc):
            game_row = self.steam.get_row(app_id)
            rating = game_row[self.my_rating_col]
            if rating is None:
                continue
            if rating >= min_rating and app_id:
                app_details = get_app_details(app_id)
                game = get_game_info(app_details, self.steam_key)
                if not game.on_sale:
                    continue
                games.append((game, rating))
        return games

    def update_sales_sheet(self, games: list[tuple[Game, int]]) -> None:
        """
        Updates the sales sheet with each games info from `games`.
        """
        # delete old game sales
        cur_rows = list(self.sales.row_idx.keys())
        for game in cur_rows:
            self.sales.delete_row(game)
        # add game rows
        cur_date = dt.datetime.now()
        for game, rating in games:
            # deletes previous row for game if it exists
            if game.name in self.sales.row_idx.keys():
                self.sales.delete_row(game.name)
            # adds new game row
            game_row = {
                self.date_updated_col: cur_date,
                self.app_id_col: game.app_id,
                self.name_col: game.name,
                self.discount_col: game.discount * 0.01,
                self.price_col: game.price,
                self.my_rating_col: rating,
                self.steam_rev_per_col: game.review_percent,
                self.steam_rev_total_col: game.review_total,
                self.dev_col: game.developer,
                self.pub_col: game.publisher,
                self.user_tags_col: game.tags_str,
                self.release_col: game.release_year,
                self.genre_col: game.genre_str,
                self.ea_col: game.early_access_str,
                self.store_link_col: create_hyperlink(game.store_link, "Store"),
            }
            self.sales.add_new_line(game_row)
        # formats all cells and saves
        self.sales.format_all_cells()
        if self.save_to_file:
            self.excel.save(use_print=False, backup=False)

    def sync_favorite_games_sales(self):
        """
        Gets sale information for games that are at a minimun rating or higher.
        Rating is set up using an IntPrompt.ask after running.
        """
        if not self.internet.online:
            print("Favorite Game Sales can't be checked without Internet")
            return
        self.load_excel_file()
        # sets minimum rating to and defaults to 8 if response is blank or invalid
        min_rating = IntPrompt.ask(
            "\nWhat is the minimum rating for this search? (1-10)",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default=8,
            show_choices=False,
            show_default=True,
        )
        print(f"Minimum Rating set to {min_rating}\n")
        # get new game sales
        games = self.get_favorite_games(min_rating)
        if not games:
            print(f"No games rated at or above {min_rating} with sales")
            return
        total_sales = len(games)
        # prints info
        print(f"\nFound {total_sales} Matching Game Sales")
        self.update_sales_sheet(games)

    def search_games(
        self, search_query: str, exact: bool = False, min_match: float = 0.6
    ) -> list[dict]:
        """
        Uses `search_query` to find any games that match within the Steam game library.
        Set `exact` to True for it to require a perfect game name match instead of just
        checking of the `search_query` is within the game name.
        """
        possible_games = []
        for app_id in self.steam.row_idx.keys():
            name = self.steam.get_cell(app_id, "Name")
            if isinstance(name, str):
                search_query_lower = search_query.lower()
                name_lower = name.lower()
            else:
                continue
            if exact:
                if search_query_lower == name_lower:
                    possible_games.append(self.steam.get_row(app_id))
            else:
                match = SequenceMatcher(None, search_query_lower, name_lower)
                if match.ratio() >= min_match:
                    possible_games.append(self.steam.get_row(app_id))
        return possible_games

    def game_finder(self, search_query: str | None = None) -> dict | None:
        """
        Searches for games with the `search_query` and asks which matching game, if any, is the correct one.

        Currently only checks of the `search_query` is in the game name. Case insensitive.
        """
        if not search_query:
            SEARCH_PROMPT = "\nWhat is the game name?:\n"
            search_query = input(SEARCH_PROMPT)
        possible_games = self.search_games(search_query)
        possible_games_length = len(possible_games)
        # only one game match found
        if possible_games_length == 1:
            game_data = possible_games[0]
            game_name = game_data["Name"]
            prompt = f"\nIs this the game you are looking for?\n{game_name}"
            if is_response_yes(prompt):
                print(f"\nSelected: {game_name}")
                return game_data
            else:
                print("\nNo game matches found")
                return {}
        # multiple matchs found
        elif possible_games_length > 1:
            msg = f"{possible_games_length} possible matchs found"
            games = [(game["Name"], game["App ID"]) for game in possible_games]
            no_match = "No Match Found"
            games.append((no_match, 0))
            chosen_game = advanced_picker(games, msg)
            if chosen_game[0] == no_match:
                print(f"\n{no_match}")
                return None
            print(f"\nSelected: {chosen_game[0]}")
            app_id = chosen_game[1]
            game = self.steam.get_row(app_id)
            return game
        else:
            print("\nNo game matches found")
            return {}

    def game_select(
        self, df: pd.DataFrame, last_num: int = 15
    ) -> tuple[list[int], str | None]:
        """
        Allows you to get a list of app ids for recently played games, all games,
        or just one game.
        """
        options = [
            f"{last_num} Recently Played Games",
            "All Games",
            "One Game",
        ]
        PROMPT = "What game(s) do you want to select?"
        selected_action = pick(options, PROMPT, indicator="->")[0]
        update_type = ""
        app_ids = []
        if selected_action == options[0]:
            update_type = "Recent"
            app_ids = self.get_recent_app_ids(df, self.last_played_col, 30)
        elif selected_action == options[1]:
            update_type = "All"
            app_ids = self.steam.row_idx.keys()
        elif selected_action == options[2]:
            update_type = "Single"
            game = self.game_finder()
            if game:
                app_ids = [game["App ID"]]
            else:
                return app_ids, None
        return app_ids, update_type  # type: ignore

    def update_add_dates(self):
        """
        Updates Games "Added Date".
        """
        self.load_excel_file()
        print()
        with Progress(transient=True) as progress:
            progress.add_task("Updating Added Dates", total=None)

            purchase_data = load_purchase_data()
            app_list = get_app_list()
            games_data = create_game_data(purchase_data, app_list)

            dates_to_update = get_dates_to_update(
                games_data, self.steam, self.date_added_col
            )
            for app_id, purchase_datetime in dates_to_update.items():
                self.steam.update_cell(app_id, self.date_added_col, purchase_datetime)

            msg = f"\n\n{len(dates_to_update)} games Added dates were updated"
            self.console.print(msg)

        self.excel.save(use_print=False, backup=False)

    def resync_all(self):
        """
        Reloads excel file and runs Steam sync again.
        """
        online = self.internet.is_online()
        if not online:
            return
        if self.excel.changes_made:
            self.excel.save(use_print=False)
        os.system("cls")
        self.load_excel_file()
        self.main()

    def open_log(self) -> None:
        osCommandString = f"notepad.exe {self.main_log_path}"
        os.system(osCommandString)

    def game_library_actions(self) -> None:
        """
        Gives a choice of actions for the current game library.
        """
        game_data_sync = lambda: (self.sync_game_data(self.dataframe))
        stat_display = lambda: (self.output_statistics(self.dataframe))
        choices = [
            ("Resync", self.resync_all),
            ("Open in Excel", self.excel.open_excel),
            ("Random Game Explorer", self.start_random_game_picker),
            ("Favorite Games Sales Sync", self.sync_favorite_games_sales),
            ("Game Data Sync", game_data_sync),
            ("Statistics Display", stat_display),
            ("Workshop Storage Check", self.check_workshop_size),
            ("Steam Friends List Sync", lambda: self.sync_friends_list(0)),
            ("Update Library Add Dates", lambda: self.update_add_dates()),
            ("Backup Excel File", lambda: self.backup.run()),
        ]
        final_choices = [entry for entry in choices if entry is not None]
        if self.logging:
            final_choices.append(("Open Log", self.open_log))
        final_choices.extend(
            [
                ("Cancel", lambda: None),
                ("Exit", lambda: sys.exit(0)),
            ]
        )
        action_picker(final_choices)
        sys.exit(0)

    def fix_app_ids(self) -> None:
        """
        Created to fix steam ID's in case they get messed up.
        """
        app_list = get_app_list()
        for app_id in self.steam.row_idx:
            name = self.steam.get_cell(app_id, self.name_col)
            if not isinstance(name, str):
                continue
            correct_app_id = get_app_id(name, app_list)
            if app_id and correct_app_id:
                if int(app_id) != int(correct_app_id):
                    print(name, app_id, correct_app_id)
                    if correct_app_id:
                        self.steam.update_cell(app_id, self.app_id_col, correct_app_id)
            else:
                print(name, app_id, correct_app_id)
                self.steam.update_cell(app_id, self.app_id_col, "")
        self.excel.save(use_print=False, backup=False)

    def intro(self):
        """
        Prints app title and date/time.
        """
        set_title(self.APP_TITLE)
        self.console.print(Panel(self.APP_TITLE, style="primary", expand=False))
        rich_date = create_rich_date_and_time()
        self.console.print(rich_date)

    def main(self) -> None:
        try:
            self.intro()
            self.internet.print_status()
            self.sync_all()
            self.auto_backup()
            self.game_library_actions()
        except (KeyboardInterrupt, EOFError):
            delay = 0.1
            print(f"\nClosing in {delay} second(s)")
            time.sleep(delay)
            sys.exit(0)
        except Exception as e:
            msg = f"\nError occurred: {traceback.format_exc()}"
            if "Test error" not in str(e):
                self.error_log.error(msg)
            input(msg)


if __name__ == "__main__":
    App = Tracker(save=True)
    App.main()
