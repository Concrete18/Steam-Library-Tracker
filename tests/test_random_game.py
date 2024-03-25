from classes.random_game import RandomGame
from easierexcel import Excel, Sheet

excel = Excel("tests/data/test_library.xlsx", use_logging=False)
steam = Sheet(excel_object=excel, sheet_name="Steam", column_name="App ID")


class TestCreateGameList:
    """
    Tests `create_game_list` function.
    """

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]

    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self):
        """
        ph
        """
        game_list = self.Picker.create_game_list("Played")
        assert game_list == ["1458140", "2342950", "1336490", "1627720"]


class TestPickGame:
    """
    Tests `pick_game` function.
    """

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]

    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self):
        """
        ph
        """
        can_be_picked = [
            "Balatro",
            "ROUNDS",
            "Pacific Drive",
        ]
        choice_list = [
            2379780,
            1557740,
            1458140,
        ]

        choice_list = self.Picker.pick_game(choice_list)


class TestGetRandomGame:
    """
    Tests `get_random_game` function.
    """

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]

    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self):
        """
        ph
        """
        can_be_picked = [
            "Balatro",
            "ROUNDS",
            "Pacific Drive",
        ]
        choice_list = [
            2379780,
            1557740,
            1458140,
        ]
        picks_left = len(choice_list)
        for _ in choice_list:
            picked_game, choice_list = self.Picker.get_random_game(choice_list)
            picks_left -= 1
            assert picked_game in can_be_picked
            assert len(choice_list) == picks_left
