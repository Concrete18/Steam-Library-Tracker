import json, webbrowser, subprocess
from tqdm import tqdm

# classes
from classes.utils import Utils


class Playstation(Utils):
    def add_playstation_games(self, games):
        """
        Adds playstation games to excel using the given `games` variable.
        """
        added_games = []
        for game in tqdm(
            iterable=games,
            ascii=True,
            unit=" games",
            ncols=100,
        ):
            game_name = self.unicode_remover(game["name"])
            # skip if it any are true
            game_exists = [
                # should be ignored
                self.skip_game(name=game_name),
                # added this session
                game_name in added_games,
                # already exist
                game_name in self.steam.row_idx.keys(),
                # game exists with a playstation version already
                f"{game_name} - Console" in self.steam.row_idx.keys(),
            ]
            if any(game_exists):
                continue
            # adds the game
            added_games.append(game_name)
            self.add_ps_game(
                game_name=game_name,
                play_status="Unplayed",
            )
        total_games_added = len(added_games)
        msg = f"New Game: Added {total_games_added} PS4/PS5 Games."
        print(msg)
        if self.logging:
            self.tracker.info(msg)
        if total_games_added and self.save_to_file:
            self.excel.save()

    # def add_ps_game(self, game_name=None):
    #     """
    #     Adds a playstation games.
    #     """
    #     # sets excel column values
    #     column_info = {
    #         self.my_rating_col: "",
    #         self.name_col: game_name,
    #         self.play_status_col: "Unplayed",
    #         self.ea_col: early_access,
    #         self.time_to_beat_col: self.get_time_to_beat(game_name),
    #         self.prob_comp_col: f'=IFERROR({hours}/{ttb},"Missing Data")',
    #         self.hours_played_col: hours_played,
    #         self.linux_hours_col: linux_hours_played,
    #         self.time_played_col: time_played,
    #         self.app_id_col: app_id,
    #         self.store_link_col: store_link_hyperlink,
    #         self.date_added_col: dt.datetime.now(),
    #         self.date_updated_col: dt.datetime.now(),
    #     }
    #     if steam_info:
    #         for column in self.excel_columns:
    #             if column in steam_info.keys():
    #                 column_info[column] = steam_info[column]
    #     self.steam.add_new_line(column_info)
    #     # logging
    #     if not hours_played:
    #         time_played = "no time"
    #     if self.logging:
    #         info = f"New Game: Added {game_name} with {time_played} played"
    #         self.tracker.info(info)
    #     self.num_games_added += 1
    #     self.steam.format_row(app_id)
    #     self.excel.save()
    #     added_info = [
    #         f"\n > {game_name} added.",
    #         f"   Total Playtime: {hours_played} Hours.",
    #     ]
    #     return added_info

    def check_playstation_json(self):
        """
        Checks `playstation_games.json` to find out if it is newly updated so
        it can add the new games to the sheet.
        """
        with open(self.ps_data) as file:
            data = json.load(file)
        print("\nChecking for new games for PS4 or PS5.")
        games = data["data"]["purchasedTitlesRetrieve"]["games"]
        self.add_playstation_games(games)

    def update_playstation_data(self):
        """
        Opens playstation data json file and web json with latest data
        for manual updating.
        """
        # checks if json exists
        if not self.ps_data.exists():
            print("\nPlayStation JSON does not exist.\nCreating file now.\n")
            self.ps_data.touch()
        subprocess.Popen(f'notepad "{self.ps_data}"')
        webbrowser.open(self.playstation_data_link)
        webbrowser.open(r"https://store.playstation.com/")
        input("\nPress Enter when done.\n")
        self.check_playstation_json()
