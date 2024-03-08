import json, subprocess, webbrowser
import datetime as dt
from rich.progress import track

from classes.utils import Utils
from classes.logger import Logger

from easierexcel import Sheet

# :pragma no cover


class Playstation(Utils):

    def __init__(self, excel, options, game_skipper) -> None:
        # super().__init__()
        self.game_skipper = game_skipper
        self.playstation = Sheet(
            excel_object=excel,
            sheet_name="Playstation",
            column_name="Name",
            options=options,
        )

        Log = Logger()
        self.playstation_log = Log.create_log(
            name="friend", log_path="logs/playstation.log"
        )

    EXCEL_COLUMNS = [
        date_added_col := "Date Added",
        date_updated_col := "Date Updated",
        my_rating_col := "My Rating",
        name_col := "Name",
        play_status_col := "Play Status",
        platform_col := "Platform",
        time_to_beat_col := "Time To Beat in Hours",
    ]

    def add_ps_game(self, game_name, platform) -> str:
        """
        Adds a playstation games with `game_name` and `platform` info.
        """
        unicode_free_name = self.unicode_remover(game_name)
        # sets excel column values
        column_info = {
            self.date_added_col: dt.datetime.now(),
            self.date_updated_col: dt.datetime.now(),
            self.name_col: game_name,
            self.play_status_col: "Unplayed",
            self.platform_col: platform,
            self.time_to_beat_col: self.get_time_to_beat(unicode_free_name),
        }
        self.playstation.add_new_line(column_info)
        # logging
        info = f"New PS Game: Added {game_name} for {platform}"
        self.playstation_log.info(info)
        self.playstation.format_row(game_name)
        return f"\n > {game_name} added"

    # TODO move playstation functions to its own class
    def check_playstation_json(self) -> dict:
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

    def sync_playstation_games(self) -> None:
        """
        Adds playstation games to excel using the given `games` variable.
        """
        msg = "\nDo you want to get your most recent Playstation data?\n"
        if self.is_response_yes(msg):
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
            if self.game_skipper.skip_game(game_name):
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
        # Updates Owned on Steam Row
        for game in self.playstation.row_idx.keys():
            games = self.search_games(game, exact=True)
            if games:
                self.playstation.update_cell(
                    game,
                    "Owned on Steam",
                    "Yes",
                )
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
