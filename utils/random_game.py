from easierexcel import Sheet
from pick import pick
import random

from rich.console import Console
from rich.theme import Theme

from utils.utils import *


class RandomGame():

    # rich console
    custom_theme = Theme(
        {
            "primary": "bold deep_sky_blue1",
            "secondary": "bold pale_turquoise1",
        }
    )
    console = Console(theme=custom_theme)

    def __init__(
        self,
        steam_sheet: Sheet,
        name_column,
        installed_column,
        play_status_choices,
        play_status_column,
    ) -> None:
        """
        Random Game Picker Class
        """
        self.sheet = steam_sheet
        self.name_column = name_column
        self.installed_column = installed_column
        self.play_status_choices = play_status_choices
        self.play_status_column = play_status_column

    def create_game_list(self, status_choice: str) -> list[int]:
        """
        Returns a `game_list` that match the chosen restraints based on user input.
        """
        self.console.print(
            f"\nPicking [secondary]{status_choice}[/] games"
            "\nPress [secondary]Enter[/] to pick another and type [secondary]q[/] to stop"
        )
        game_list = []
        for app_id in self.sheet.row_idx.keys():
            if status_choice == "Installed":
                installed = self.sheet.get_cell(app_id, self.installed_column)
                if not installed:  # pragma: no cover
                    continue
                if installed.lower() == "yes":
                    game_list.append(app_id)
            else:
                game_play_status = self.sheet.get_cell(app_id, self.play_status_column)
                if not game_play_status:  # pragma: no cover
                    continue
                if game_play_status.lower() == status_choice.lower():
                    game_list.append(app_id)
        return game_list

    def get_random_game(self, game_list) -> tuple[str, list]:
        """
        Picks random game with the given `play_status` then removes it from the `game_list` so it wont show up again during this session.
        """
        if not game_list:
            return None, game_list
        picked_app_id = random.choice(game_list)
        game_list.pop(game_list.index(picked_app_id))
        picked_game = self.sheet.get_cell(picked_app_id, self.name_column)
        return picked_game, game_list

    def pick_game(self, game_list: list) -> tuple[str, list]:
        """
        Picks random game from `game_list` with `choice`.
        Returns `game_list` with picked game removed.
        """
        picked_game, game_list = self.get_random_game(game_list)
        self.console.print(f"Picked: [primary]{picked_game}[/]")
        return picked_game, game_list

    def random_pick_loop(self, game_list: list) -> list:
        """
        Loops through random picks from the `game_list` until all games have
        been picked or the user enters a stop command.
        """
        picked = []
        quit_strings = ["quit", "q", "s", "stop", "end"]
        while game_list:
            response = input().lower()
            if response in quit_strings:
                return picked
            picked_game, game_list = self.pick_game(game_list)
            picked.append(picked_game)
        print(f"All games have already been picked.\n")
        return picked

    def random_game_picker(self) -> None:  # pragma: no cover
        """
        Allows you to pick a play_status or installed status to have a random game chosen from.
        """
        status_choices = ["Installed", *self.play_status_choices]
        PROMPT = "\nWhat Play/Installed Status do you want a random game picked for?"
        status_choice = pick(status_choices, PROMPT, indicator="->")[0]
        game_list = self.create_game_list(status_choice)
        self.random_pick_loop(game_list)
