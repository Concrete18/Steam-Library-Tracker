import random, json, os, re, sys, webbrowser, subprocess, shutil, time
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
from pathlib import Path
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
            game_name = self.unicode_fix(game["name"])
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
            self.add_game(
                sheet=self.playstation,
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
