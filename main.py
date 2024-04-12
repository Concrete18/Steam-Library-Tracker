import os, sys, math, traceback
import datetime as dt
import pandas as pd
from difflib import SequenceMatcher
from pick import pick

from rich.console import Console
from rich.prompt import IntPrompt
from rich.progress import track
from rich.table import Table
from rich.theme import Theme

# classes
from setup import Setup
from classes.steam import Steam
from classes.game_info import Game, GetGameInfo
from classes.random_game import RandomGame
from classes.game_skipper import GameSkipper
from classes.utils import Utils, keyboard_interrupt
from classes.logger import Logger

# my package
from easierexcel import Excel, Sheet


class Tracker(GetGameInfo, Steam, Utils):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # config init
    setup = Setup()
    config_path, config_data, ignore_data, excel_options = setup.run()

    # steam_data
    steam_key = config_data["steam_data"]["api_key"]
    steam_id = config_data["steam_data"]["steam_id"]
    vanity_url = config_data["steam_data"]["vanity_url"]
    library_vdf_path = config_data["steam_data"]["library_vdf_path"]

    # settings
    excel_filename = config_data["settings"]["excel_filename"]
    logging = config_data["settings"]["logging"]

    # misc
    NAME_IGNORE_LIST = [string.lower() for string in ignore_data["name_ignore_list"]]
    APP_ID_IGNORE_LIST = ignore_data["app_id_ignore_list"]
    game_skipper = GameSkipper(NAME_IGNORE_LIST, APP_ID_IGNORE_LIST)

    # logging setup
    if logging:
        Log = Logger()
        main_log_path = "logs/main.log"
        main_log = Log.create_log(name="main", log_path=main_log_path)
        friend_log = Log.create_log(name="friend", log_path="logs/friend.log")
        error_log = Log.create_log(name="base_error", log_path="logs/error.log")

    # rich console
    custom_theme = Theme(
        {
            "primary": "bold deep_sky_blue1",
            "secondary": "bold pale_turquoise1",
            "info": "dim cyan",
            "warning": "bold light_goldenrod1",
            "danger": "bold red",
        }
    )
    console = Console(theme=custom_theme)

    # excel file setup
    excel = Excel(excel_filename, use_logging=logging)
    steam = Sheet(
        excel_object=excel,
        sheet_name="Steam",
        column_name="App ID",
        options=excel_options,
    )
    sales = Sheet(
        excel_object=excel,
        sheet_name="Sales",
        column_name="Name",
        options=excel_options,
    )

    # sets play status choices for multiple functions
    PLAY_STATUS_CHOICES = (
        "Played",
        "Unplayed",
        "Finished",
        "Endless",
        "Replay",
        "Must Play",
        "Waiting",
        "Quit",
        "Ignore",
    )

    # columns
    EXCEL_COLUMNS = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        my_rating_col := "My Rating",
        steam_rev_per_col := "Steam Review Percent",
        steam_rev_total_col := "Steam Review Total",
        price_col := "Price",
        discount_col := "Discount",
        steam_player_count_col := "Player Count",
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
        time_to_beat_col := "Time To Beat in Hours",
        store_link_col := "Store Link",
        release_col := "Release Year",
        app_id_col := "App ID",
    ]
    APP_TITLE = "Game Library Tracker"

    def __init__(self, save: bool) -> None:
        """
        Game Library Tracking Class.
        """
        self.save_to_file = save
        if not self.steam_id:
            self.update_steam_id()
        self.internet_connected = self.check_internet_connection()
        if not self.internet_connected:
            self.console.print("\nNo Internet Detected", style="warning")

    def update_steam_id(self):
        """
        Updates the steam id in the config using the given vanity url if present.
        """
        if not self.vanity_url:
            raise "Steam ID and Vanity URL is blank. Please enter at one of them"
        self.steam_id = self.get_steam_id(self.vanity_url, self.steam_key)
        if self.steam_id:
            self.config_data["settings"]["steam_id"] = self.steam_id
            self.save_json(self.config_data, self.config_path)

    def sync_friends_list(self, check_freq_days: int = 7) -> None:
        """
        Checks for changes to your friends list.
        Shows a table of new and removed friends Steam ID's and usernames.
        """
        if not self.internet_connected:
            return
        # check last run
        if self.recently_executed(self.config_data, "friends_sync", check_freq_days):
            return
        self.update_last_run(self.config_data, self.config_path, "friends_sync")
        # get friends
        print("\nStarting Steam Friends Sync")
        prev_friend_ids = self.config_data["friend_ids"]
        friend_data = self.get_steam_friends(self.steam_key, self.steam_id)
        cur_friend_ids = [friend["steamid"] for friend in friend_data]
        # finds changes
        additions, removals = self.steam.get_friends_list_changes(
            prev_friend_ids, cur_friend_ids
        )
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
            username = self.get_steam_username(steam_id, self.steam_key)
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
            username = self.get_steam_username(steam_id, self.steam_key)
            row = [
                "Added",
                username,
                steam_id,
            ]
            table.add_row(*row)
            # logging
            msg = f"Friends List Addition: {username}"
            self.friend_log.info(msg)
        self.console.print(table, new_line_start=True)
        # update friend data in config
        self.config_data["friend_ids"] = cur_friend_ids
        self.save_json(self.config_data, self.config_path)

    def set_title(self, title: str = None) -> None:
        """
        Sets the CLI window title to the specified title if provided.
        If no title is given, it sets the title back to the default.
        """
        set_title = title or self.APP_TITLE
        os.system(f"title {set_title}")

    def create_save_every_nth(self, save_on_nth: int = 20):
        counter = 0

        def save_every_nth():
            nonlocal counter
            counter += 1
            if counter % save_on_nth == 0:
                self.excel.save(use_print=False, backup=False)
                counter = 0

        return save_every_nth

    def set_play_status(self, app_id: int, new_status: str, cur_status: str = None):
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

    def get_game_column_dict(self, game: Game) -> dict:
        """
        Returns a dict of column names and the value for that column.
        """
        store_link = (
            self.create_hyperlink(game.game_url, "Store") if game.game_url else "-"
        )
        return {
            self.dev_col: game.developer or "-",
            self.pub_col: game.publisher or "-",
            self.steam_rev_per_col: game.steam_review_percent or "-",
            self.steam_rev_total_col: game.steam_review_total or "-",
            self.price_col: game.price or "-",
            self.discount_col: game.discount or "-",
            self.steam_player_count_col: game.player_count or "-",
            self.genre_col: game.genre_str or "-",
            self.user_tags_col: game.tags_str or "-",
            self.ea_col: game.early_access or "-",
            self.time_to_beat_col: game.time_to_beat or "-",
            self.store_link_col: store_link,
            self.release_col: game.release_year or "-",
        }

    def update_extra_game_info(self, app_ids: list[int]):
        """
        Updates info that changes often enough that it needs to be updated manually.
        """
        save_every_nth = self.create_save_every_nth()
        print()
        cur_itr = 0
        desc = "Syncing Game Data"
        for app_id in track(app_ids, description=desc):
            game_row = self.steam.get_row(app_id)
            # get new data from the internet
            app_details = self.get_app_details(app_id)
            game = self.get_game_info(app_details, self.steam_key)
            game_data = self.get_game_column_dict(game)
            # update data
            for column, data in game_data.items():
                if not data:
                    continue
                if column == self.time_to_beat_col and game_row[self.time_to_beat_col]:
                    continue
                self.steam.update_cell(app_id, column, data)
            # saves data
            if self.save_to_file:
                save_every_nth()
            # title progress percentage
            cur_itr += 1
            progress = cur_itr / len(app_ids) * 100
            self.set_title(f"{progress:.1f}% - {self.APP_TITLE}")
        self.set_title()

    def update_all_game_data(self):
        """
        Gets app_ids and updates games using update_extra_game_info func.
        """
        app_ids = [int(app_id) for app_id in self.steam.row_idx.keys()]
        self.update_extra_game_info(app_ids)

    def get_recently_played_app_ids(self, df: pd.DataFrame, n_days: int = 30) -> list:
        """
        Gets the app_ids of the recently played games via a dataframe.
        """
        # check last run
        if self.recently_executed(self.config_data, "recently_played", n_days):
            return []
        # get recently played games
        recently_played = App.find_recent_games(df, self.date_updated_col, n_days)
        recently_played_app_ids = [game[self.app_id_col] for game in recently_played]
        return recently_played_app_ids

    def app_ids_to_names(self, app_ids: list[int]) -> list[str]:
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
        Updates game data for games that were played recently and are missing data.

        Use `skip_filled` to skip non blank entries.

        Use `skip_by_play_status` to only check games with a specific play status.
        """
        if not self.internet_connected:
            return
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
                game_list_str = self.list_to_sentence(game_names)
                msg = f"\n{game_list_str}\n\nDo you want to update data for the above {update_games_total} games?"
            else:
                msg = f"\nDo you want to update data for {update_games_total} games?"
            if not self.is_response_yes(msg):
                return
        else:
            return
        # updates game data
        try:
            self.update_extra_game_info(update_list)
            if updated_recent:
                self.update_last_run(
                    self.config_data, self.config_path, "recently_played"
                )
            print(f"\nUpdated Data for {len(update_list)} games")
        except KeyboardInterrupt:
            print("\nCancelled")
        finally:
            if self.save_to_file:
                self.excel.save(use_print=False, backup=False)

    def output_recently_played_games(self, df: pd.DataFrame, n_days: int = 7) -> None:
        """
        Creates a table with the recently played Games.
        """
        recently_played_games = App.find_recent_games(df, "Date Updated", n_days)
        # creates table
        table_title = f"Recently Played Games\nWithin {n_days} Days"
        table = Table(
            title=table_title,
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
        )
        table.add_column("Days\nSince", justify="center")
        table.add_column("Date Updated", justify="center")
        table.add_column("Name", justify="left", min_width=30)
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
            ttb = game[self.time_to_beat_col]
            if ttb > 0:
                ttb = str(float(ttb))
            else:
                ttb = "-"
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

    def output_play_status_info(self, df: pd.DataFrame) -> None:
        """
        Creates a table with counts and percentage of each play status.
        """
        table = Table(
            title="Play Status Stats",
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
            caption="Excludes Ignored",
        )
        # filters out games with "Ignore" play status
        df_filtered = df[df["Play Status"] != "Ignore"]
        play_statuses = df_filtered["Play Status"].value_counts()
        total_games_excluding_ignore = len(df_filtered)
        # Row creation
        row1, row2 = [], []
        for play_status in self.PLAY_STATUS_CHOICES:
            if play_status == "Ignore":
                continue
            count = play_statuses[play_status]
            table.add_column(play_status, justify="center")
            row1.append(str(count))
            row2.append(f"{count / total_games_excluding_ignore:.1%}")
        table.add_row(*row1)
        table.add_row(*row2)
        self.console.print(table, new_line_start=True)

    def output_playtime_info(self, df: pd.DataFrame) -> None:
        """
        Creates a table with counts and percentage of each play status.
        """
        table = Table(
            title="Playtime Stats",
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
            caption="Excludes Ignored",
        )
        # filters out games with "Ignore" play status
        df_filtered = df[df["Play Status"] != "Ignore"]

        total_hours_sum = df_filtered["Hours Played"].sum()
        linux_hours_sum = df_filtered["Linux Hours"].sum()
        average_hours = df_filtered["Hours Played"].mean()
        median_hours = df_filtered["Hours Played"].median()
        max_hours = df_filtered["Hours Played"].max()
        data = {
            "Total\nHours": self.format_floats(total_hours_sum, 1),
            "Total\nDays": self.format_floats(total_hours_sum / 24, 1),
            "Linux\nHours": self.format_floats(linux_hours_sum, 1),
            "% Linux\nHours": self.format_floats(linux_hours_sum / total_hours_sum, 1),
            "Average\nHours": self.format_floats(average_hours, 1),
            "Median\nHours": self.format_floats(median_hours, 1),
            "Max\nHours": self.format_floats(max_hours, 1),
        }
        # row creation
        row = []
        for name, stat in data.items():
            table.add_column(name, justify="center")
            row.append(str(stat))
        table.add_row(*row)
        self.console.print(table, new_line_start=True)

    def output_review_info(self, df: pd.DataFrame) -> None:
        """
        Outputs a table of review stats.
        """
        table = Table(
            title="Rating Stats",
            show_lines=True,
            title_style="bold",
            style="deep_sky_blue1",
            caption="Excludes Ignored",
        )
        # filters out games with "Ignore" play status
        df_filtered = df[df["Play Status"] != "Ignore"]

        data = {}
        # my ratings
        my_ratings = df_filtered["My Rating"]
        data["My\nTotal"] = my_ratings.count()
        data["My\nAverage"] = round(my_ratings.mean(), 1)
        # steam ratings
        steam_ratings = df_filtered["Steam Review Percent"].astype("float")
        data["Steam\nTotal"] = steam_ratings.count()
        steam_avg = round(steam_ratings.mean(), 1)
        data["Steam\nAverage"] = f"{round(steam_avg*100)}%"
        # row creation
        row = []
        for name, stat in data.items():
            table.add_column(name, justify="center")
            row.append(str(stat))
        table.add_row(*row)

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

    def output_statistics(self, dataframe: pd.DataFrame) -> None:
        """
        Outputs tables of game library statistics.
        """
        self.output_play_status_info(dataframe)
        self.output_playtime_info(dataframe)
        self.output_review_info(dataframe)

    @staticmethod
    def decide_play_status(play_status: str, minutes_played: float) -> str:
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

    def name_change_checker(self, name_changes: list[dict]) -> None:
        """
        Checks the `name_changes` to see if they contain any
        name changes to possibly fulfill.
        """
        for names_dict in name_changes:
            new_name = names_dict["new_name"]
            old_name = names_dict["old_name"]
            msg = f'Do you want to update "{old_name}"\'s name to {new_name}?:\n'
            if self.is_response_yes(msg):
                app_id = names_dict["app_id"]
                self.steam.update_cell(app_id, self.name_col, new_name)

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
        self.total_session_playtime = 0
        added_games = []
        played_games = []
        name_changes = []
        save_every_nth = self.create_save_every_nth()
        # game checking
        print()
        total_games = len(steam_games)
        desc = f"Syncing [bold]{total_games:,}[/bold] Steam Games"
        installed_app_ids = self.get_installed_app_ids(self.library_vdf_path)
        for game in track(steam_games, description=desc):
            game_name, app_id = game["name"], game["appid"]
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
            minutes_played = game["playtime_forever"]
            time_played = self.convert_time_passed(minutes=minutes_played)
            linux_minutes_played = ""
            if "playtime_linux_forever" in game.keys():
                linux_minutes_played = game["playtime_linux_forever"]
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
                    play_status=new_status,
                    get_internet_info=len(added_games) <= 10,
                    installed=installed,
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
            removed_game_names = [
                self.steam.get_cell(app_id, self.name_col) for app_id in sheet_games
            ]
            removed_games_names_str = self.list_to_sentence(removed_game_names)
            if self.is_response_yes(
                f"\nDo you want to delete all the following games?\n{removed_games_names_str}"
            ):
                for app_id in sheet_games:
                    self.steam.delete_row(str(app_id))
        if self.excel.changes_made and self.save_to_file:
            self.excel.save(use_print=False)
        else:
            print("\nNo Steam games were added or updated")

    def sync_steam_games(self, steam_key: int, steam_id: int) -> None:
        """
        Gets games owned by the entered `steam_id`
        and runs excel update/add functions.
        """
        if not self.internet_connected:
            return
        owned_games = self.get_owned_steam_games(steam_key, steam_id)
        if owned_games:
            sheet_app_ids = [int(app_id) for app_id in self.steam.row_idx.keys()]
            if not sheet_app_ids:
                print(f"\nStarting First Steam Sync")
            self.sync_steam_games_with_sheet(owned_games, sheet_app_ids)
            return
        print("\nFailed to retrieve Steam Games\nSteam Servers may be down")
        input()
        exit()

    def update_steam_game(
        self,
        app_id: int,
        game_name: str,
        minutes_played: float,
        linux_minutes_played: float,
        new_status: str,
        cur_status: str,
        installed: bool = False,
        time_played: str = None,
    ) -> dict | None:
        """
        Updates the games playtime and play status if they changed.
        """
        installed_value = "Yes" if installed else "No"
        self.steam.update_cell(app_id, self.installed_col, installed_value)
        prev_hours = self.steam.get_cell(app_id, self.hours_played_col)
        try:
            prev_hours = float(prev_hours)
        except (TypeError, ValueError):
            prev_hours = 0.0
        cur_hours = self.hours_played(minutes_played)
        if not cur_hours:
            return
        # only updates if new play time occurred
        if cur_hours > prev_hours:
            hours_played = cur_hours - prev_hours
            self.steam.update_cell(app_id, self.hours_played_col, cur_hours)
            cur_linux_hours = self.hours_played(linux_minutes_played)
            self.steam.update_cell(app_id, self.linux_hours_col, cur_linux_hours)
            added_time = self.convert_time_passed(hours=hours_played)
            self.steam.update_cell(app_id, self.last_play_time_col, added_time)
            self.steam.update_cell(app_id, self.time_played_col, time_played)
            self.set_date_updated(app_id)
            self.set_play_status(app_id, new_status, cur_status)
            self.steam.format_row(app_id)
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
        app_id: int = None,
        game_name: str = None,
        minutes_played: float = None,
        linux_minutes_played: float = None,
        time_played: str = None,
        play_status: str = None,
        get_internet_info: bool = True,
        save_after_add: bool = False,
        installed: bool = False,
    ) -> dict:
        """
        Adds a game with the game_name, hours played using `minutes_played` and `play_status`.

        If save is True, it will save after adding the game.
        """
        hours_played = self.hours_played(minutes_played)
        cur_date = dt.datetime.now()
        base_data = {
            self.name_col: game_name,
            self.app_id_col: app_id,
            self.play_status_col: self.decide_play_status(play_status, minutes_played),
            self.hours_played_col: hours_played,
            self.linux_hours_col: self.hours_played(linux_minutes_played),
            self.time_played_col: time_played,
            self.installed_col: "Yes" if installed else "No",
            self.date_added_col: cur_date,
            self.date_updated_col: cur_date,
        }
        extra_data = {}
        if get_internet_info:
            app_details = self.get_app_details(app_id)
            if app_details:
                game = self.get_game_info(app_details, self.steam_key)
                extra_data = self.get_game_column_dict(game)
        game_data = {**base_data, **extra_data}

        self.steam.add_new_line(game_data)
        # logging
        if self.logging:
            time_played_str = time_played or "no time"
            info = f"New Game: Added {game_name} with {time_played_str} played"
            self.main_log.info(info)
        self.steam.format_row(app_id)
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
            steam_sheet=Tracker.steam,
            name_column=self.name_col,
            installed_column=self.installed_col,
            play_status_choices=self.PLAY_STATUS_CHOICES,
            play_status_column=self.play_status_col,
        )
        Picker.random_game_picker()

    def get_favorite_games(self, min_rating: int = 8) -> list[dict]:
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
                app_details = self.get_app_details(app_id)
                game = self.get_game_info(app_details, self.steam_key)
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
                self.steam_rev_per_col: game.steam_review_percent,
                self.steam_rev_total_col: game.steam_review_total,
                self.dev_col: game.developer,
                self.pub_col: game.publisher,
                self.time_to_beat_col: game.time_to_beat,
                self.user_tags_col: game.tags_str,
                self.release_col: game.release_year,
                self.genre_col: game.genre_str,
                self.ea_col: game.early_access,
                self.store_link_col: self.create_hyperlink(game.game_url, "Store"),
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

    @staticmethod
    def advanced_picker(choices: list[tuple], prompt: str) -> list:
        """
        Choice picker using the advanced and less compatible Pick module.
        """
        options = [choice[0] for choice in choices]
        selected_index = pick(options, prompt, indicator="->")[1]
        return choices[selected_index]

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
            search_query_lower = search_query.lower()
            name_lower = name.lower()
            if exact:
                if search_query_lower == name_lower:
                    possible_games.append(self.steam.get_row(app_id))
            else:
                match = SequenceMatcher(None, search_query_lower, name_lower)
                if match.ratio() >= min_match:
                    possible_games.append(self.steam.get_row(app_id))
        return possible_games

    def game_finder(self, search_query: str = None) -> dict:
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
            if self.is_response_yes(prompt):
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
            chosen_game = self.advanced_picker(games, msg)
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

    def bulk_update_player_count(self, app_ids: list[int], update_type: str) -> list:
        print()  # forced new line due to how track() works
        player_counts = []
        desc = f"Updating {update_type} Player Count(s)"
        for app_id in track(app_ids, description=desc):
            player_count = self.get_steam_game_player_count(app_id, self.steam_key)
            player_counts.append(player_count)
            self.steam.update_cell(
                app_id,
                self.steam_player_count_col,
                player_count,
            )
            self.api_sleeper("steam_player_count")
        return player_counts

    def update_player_counts(self, df: pd.DataFrame, last_num: int = 15) -> None:
        """
        Updates game player counts using the Steam API.
        """
        options = [
            f"Update {last_num} Recently Played Games",
            "Update All Games",
            "Update One Game",
        ]
        PROMPT = "What game(s) do you want to update?"
        selected_action = pick(options, PROMPT, indicator="->")[0]
        update_type = ""
        app_ids = []
        if selected_action == options[0]:
            update_type = "Recent"
            recently_played = App.find_recent_games(df, self.date_updated_col, 30)
            app_ids = [game[self.app_id_col] for game in recently_played]
        elif selected_action == options[1]:
            update_type = "All"
            app_ids = self.steam.row_idx.keys()
        elif selected_action == options[2]:
            update_type = "Single"
            game = self.game_finder()
            if game:
                app_ids = [game["App ID"]]
            else:
                return
        self.bulk_update_player_count(app_ids, update_type)
        self.excel.save(use_print=False, backup=False)

    def pick_game_to_update(self, games: list) -> None:
        """
        Allows picking game to update playtime and last_updated.
        """
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
            return
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

    def open_log(self) -> None:
        osCommandString = f"notepad.exe {self.main_log_path}"
        os.system(osCommandString)

    def pick_task(self, choices: list[tuple], repeat: bool = True) -> None:
        """
        Allows picking a task using Arrow Keys and Enter.
        """
        if not sys.stdout.isatty():
            # runs if it is not an interactable terminal
            print("\nSkipping Task Picker.\nInput can't be used")
            return
        input("\nPress Enter to Pick Next Action:")
        PROMPT = "What do you want to do? (Use Arrow Keys and Enter):"
        selected = self.advanced_picker(choices, PROMPT)
        if selected:
            name, func = selected[0], selected[1]
            msg = f"\n[b underline]{name}[/] Selected"
            self.console.print(msg, highlight=False)
            func()
            if "exit" in name.lower():
                return
            if repeat:
                self.pick_task(choices, repeat)

    def game_library_actions(self, df: pd.DataFrame) -> None:
        """
        Gives a choice of actions for the current game library.
        """
        # choice picker
        choices = [
            ("Exit and Open the Excel File", self.excel.open_excel),
            ("Random Game Explorer", self.start_random_game_picker),
            ("Player Counts Sync", lambda: self.update_player_counts(df)),
            ("Favorite Games Sales Sync", self.sync_favorite_games_sales),
            ("Game Data Sync", self.update_all_game_data),
            ("Statistics Display", lambda: self.output_statistics(df)),
            ("Steam Friends List Sync", lambda: self.sync_friends_list(0)),
            # ("Playstation Games Sync", self.sync_playstation_games),
        ]
        if self.logging:
            choices.append(("Open Log", self.open_log))
        choices.append(("Exit", exit))
        self.pick_task(choices)
        exit()

    def fix_app_ids(self) -> None:
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
        self.excel.save(use_print=False, backup=False)

    @keyboard_interrupt
    def main(self) -> None:
        try:
            self.console.print(self.APP_TITLE, style="primary")

            self.console.print(self.create_rich_date_and_time())

            self.sync_steam_games(self.steam_key, self.steam_id)

            # table data
            df = self.steam.create_dataframe(na_vals=["-", "NaN"])
            self.output_recently_played_games(df)

            # extra data updates
            self.updated_game_data(df)
            self.sync_friends_list()

            self.game_library_actions(df)
        except Exception as e:
            msg = f"Error occurred: {traceback.format_exc()}"
            if "Test error" not in str(e):
                self.error_log.error(msg)


if __name__ == "__main__":
    App = Tracker(save=True)
    App.main()
