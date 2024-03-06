from easierexcel import Sheet
from pick import pick
import random

from rich.console import Console
from rich.theme import Theme

from classes.utils import Utils


class RandomGame(Utils):

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
        play_status_choices,
        name_column,
        installed_column,
        play_status_column,
    ) -> None:
        """
        Random Game Picker Class
        """
        self.sheet = steam_sheet
        self.play_status_choices = play_status_choices
        self.name_column = name_column
        self.installed_column = installed_column
        self.play_status_column = play_status_column

    def create_game_list(self, choices: list[str]) -> list[int]:
        """
        Returns a `game_list` that match the chosen restraints based on user input.
        """
        msg = "\nWhat Play/Installed Status do you want a random game picked for?"
        status_choice = pick(choices, msg)[0]
        self.console.print(
            f"\nPicking [secondary]{status_choice}[/] games"
            "\nPress [secondary]Enter[/] to pick another and [secondary]ESC[/] to Stop"
        )

        game_list = []
        for app_id in self.sheet.row_idx.keys():
            if status_choice == "Installed":
                installed = self.sheet.get_cell(app_id, self.installed_column)
                if not installed:
                    continue
                if installed.lower() == "yes":
                    game_list.append(app_id)
            else:
                game_play_status = self.sheet.get_cell(app_id, self.play_status_column)
                if not game_play_status:
                    continue
                if game_play_status.lower() == status_choice.lower():
                    game_list.append(app_id)
        return game_list

    def get_random_game(self, choice_list) -> tuple[str, list]:
        """
        Picks random game with the given `play_status` then removes it from the `choice_list` so it wont show up again during this session.
        """
        if not choice_list:
            return None, choice_list
        picked_app_id = random.choice(choice_list)
        choice_list.pop(choice_list.index(picked_app_id))
        picked_game = self.sheet.get_cell(picked_app_id, self.name_column)
        return picked_game, choice_list

    def pick_game(self, choice_list: list) -> list:
        """
        Picks random game from `choice_list` with `choice`.
        Returns `choice_list` with picked game removed.
        """
        picked_game, choice_list = self.get_random_game(choice_list)
        self.console.print(f"\nPicked: [primary]{picked_game}[/]")
        return choice_list

    def random_game_picker(self) -> None:
        """
        Allows you to pick a play_status or installed status to have a random game chosen from.
        """
        play_statuses = list(self.play_status_choices.values())
        choices = ["Installed", *play_statuses]
        # get game choices
        game_list = self.create_game_list(choices)
        # key setup
        continue_key = "enter"
        stop_key = "esc"
        # loop and pick random games till stop_key is used or game_list is emptied
        while game_list:
            game_list = self.pick_game(game_list)
            allowed_keys = [continue_key, stop_key]
            released_key = self.wait_for_key_release(allowed_keys)
            # quits picking random games
            if released_key == stop_key:
                return

        print(f"No games left to pick.\n")
