# standard library
import re

# local imports
from library.utils.utils import *


class GameSkipper:
    def __init__(
        self,
        custom_names_to_ignore: list[str] = [],
        app_id_ignore_list: list[int] = [],
    ) -> None:
        self.media_list = [
            "Amazon Prime Video",
            "HBO GO",
            "HBO Max",
            "Max",
            "Hulu",
            "Media Player",
            "Spotify",
            "Netflix",
            "Plex",
            "Pluto",
            "YouTube VR",
            "Youtube",
        ]

        self.keyword_ignore_list = (
            "demo",
            "youtube",
            "playtest",
            "beta test",
            "open beta",
            "closed beta",
            "online beta",
            "multiplayer beta",
            "preorder",
            "pre-order",
            "playable teaser",
            "soundtrack",
            "test server",
            "bonus content",
            "trial edition",
            "technical test",
            "closed test",
            "open test",
            "public test",
            "public testing",
            "directors' commentary",
        )
        # makes sure the keywords are lower case
        self.keyword_ignore_list = [s.lower() for s in self.keyword_ignore_list]

        self.name_ignore_list = custom_names_to_ignore + self.media_list
        self.app_id_ignore_list = app_id_ignore_list

    def name_check(self, name):
        """
        Checks if the games name means it should be skipped.
        """
        cleaned_name = unicode_remover(name).lower()
        if cleaned_name and cleaned_name in map(str.lower, self.name_ignore_list):
            return True
        # keyword check
        for keyword in self.keyword_ignore_list:
            if re.search(rf"\b{keyword}\b", name.lower()):
                return True
        return False

    def skip_game(self, game_name: str = "", app_id: int = 0) -> bool:
        """
        Checks if a game should be skipped based on `name` or `app_id`.

        Returns False if neither are given and
        prioritizes checking `app_id` if both are given.

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
            return self.name_check(game_name)

        return False
