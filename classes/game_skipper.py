import re

from classes.utils import Utils


class GameSkipper(Utils):
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

    keyword_ignore_list = [
        "demo",
        "youtube",
        "playtest",
        "open Beta",
        "closed beta",
        "multiplayer beta",
        "online beta",
        "preorder",
        "pre-order",
        "playable teaser",
        "soundtrack",
        "test server",
        "bonus content",
        "trial edition",
        "closed test",
        "open test",
        "public test",
        "public testing",
        "directors' commentary",
    ]

    def __init__(
        self,
        custom_names_to_ignore: list[str] = [],
        app_id_ignore_list: list[int] = [],
    ) -> None:
        """
        Game Skipping class that determines if a game should be skipped based on the games name or app ID.
        """
        self.name_ignore_list = custom_names_to_ignore + self.media_list
        self.app_id_ignore_list = app_id_ignore_list

    def skip_game(self, game_name: str = None, app_id: int = None) -> bool:
        """
        Checks if a game should be skipped based on `name` or `app_id`.

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
            # checks if name means it should be skipped
            cleaned_name = self.unicode_remover(game_name).lower()
            if cleaned_name and cleaned_name in map(str.lower, self.name_ignore_list):
                return True
            # keyword check
            for keyword in self.keyword_ignore_list:
                if re.search(rf"\b{keyword}\b", game_name.lower()):
                    return True
        return False
