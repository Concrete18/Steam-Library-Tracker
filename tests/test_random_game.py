from utils.random_game import RandomGame
from easierexcel import Excel, Sheet

excel = Excel("tests/data/test_library.xlsx", use_logging=False)
steam = Sheet(excel_object=excel, sheet_name="Steam", column_name="App ID")


class TestCreateGameList:

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]
    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_played(self):
        game_list = self.Picker.create_game_list("Played")
        assert game_list == ["1458140", "2342950", "1336490", "1627720"]

    def test_installed(self, mocker):
        # sets everything to show as installed
        mocker.patch("easierexcel.Sheet.get_cell", return_value="Yes")
        game_list = self.Picker.create_game_list("Installed")
        assert game_list == [
            "553850",
            "1364780",
            "2379780",
            "1557740",
            "2321470",
            "1172620",
            "1326470",
            "1458140",
            "2342950",
            "1336490",
            "1627720",
            "367500",
            "383270",
            "1888160",
            "2054970",
            "383180",
        ]


class TestPickGame:

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]
    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self):
        can_be_picked = ["Balatro", "ROUNDS", "Pacific Drive"]
        game_list = [2379780, 1557740, 1458140]
        picked_game, game_list = self.Picker.pick_game(game_list)
        assert picked_game in can_be_picked


class TestRandomPickLoop:

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]
    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self, mocker):
        game_list = [2379780, 1557740, 1458140]
        mocker.patch("builtins.input", return_value="")
        picked = self.Picker.random_pick_loop(game_list)
        assert "Pacific Drive" in picked
        assert "ROUNDS" in picked
        assert "Balatro" in picked

    def test_quit(self, mocker):
        game_list = [2379780, 1557740]
        mocker.patch("builtins.input", return_value="q")
        picked = self.Picker.random_pick_loop(game_list)
        assert picked == []


class TestGetRandomGame:

    PLAY_STATUS_CHOICES = ["Played", "Unplayed"]
    Picker = RandomGame(
        steam_sheet=steam,
        name_column="Name",
        installed_column="Installed",
        play_status_choices=PLAY_STATUS_CHOICES,
        play_status_column="Play Status",
    )

    def test_success(self):
        can_be_picked = ["Balatro", "ROUNDS", "Pacific Drive"]
        game_list = [2379780, 1557740, 1458140]
        picks_left = len(game_list)
        for _ in game_list:
            picked_game, game_list = self.Picker.get_random_game(game_list)
            picks_left -= 1
            assert picked_game in can_be_picked
            assert len(game_list) == picks_left

    def test_empty_list(self):
        picked_game, game_list = self.Picker.get_random_game([])
        assert picked_game is None
        assert game_list == []
