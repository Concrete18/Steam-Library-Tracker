import pytest, json

from classes.game_info import Game, GetGameInfo
from classes.utils import Utils


class TestGame:

    def test_given_args(self):
        NAME = "Test1"
        APP_ID = 12345
        game = Game(
            name=NAME,
            app_id=APP_ID,
            developer="Dev",
            publisher="Pub",
            genre=["Testing", "early access"],
            release_year=2024,
            price=12.34,
            discount=0.88,
            categories=["Category 1"],
            user_tags=["Tag 1"],
        )
        assert len(vars(game)) == 20
        assert game.app_id == APP_ID
        assert game.name == NAME
        assert game.developer == "Dev"
        assert game.publisher == "Pub"
        assert game.early_access == "Yes"
        assert game.genre == ["Testing", "early access"]
        assert game.release_year == 2024
        assert game.price == 12.34
        assert game.discount == 0.88
        assert game.on_sale
        assert game.categories == ["Category 1"]
        assert game.user_tags == ["Tag 1"]
        assert game.game_url == "https://store.steampowered.com/app/12345/"

    def test_not_on_sale(self):
        NAME = "Test1"
        APP_ID = 12345
        game = Game(
            name=NAME,
            app_id=APP_ID,
            price=10,
            discount=0.0,
        )
        assert not game.on_sale

    def test_not_early_access(self):
        NAME = "Test1"
        APP_ID = 12345
        game = Game(
            name=NAME,
            app_id=APP_ID,
            genre=["Testing"],
        )
        assert game.early_access == "No"

    def test_no_args(self):
        game = Game()
        assert not Game()
        # total attributes
        assert len(vars(game)) == 20
        # required values
        assert game.name == ""
        assert game.app_id == 0
        # str
        assert game.game_url == 0
        assert game.early_access == "No"
        # float
        assert game.discount == 0.0
        # false
        assert game.on_sale == False
        # list
        assert game.genre == []
        assert game.categories == []
        assert game.user_tags == []
        # none
        assert game.developer == ""
        assert game.publisher == ""
        assert game.release_year == 0
        assert game.steam_review_percent == 0.0
        assert game.steam_review_total is None
        assert game.price is None
        assert game.time_to_beat == 0.0
        assert game.player_count is None
        assert game.tags_str == ""
        assert game.categories_str == ""
        assert game.genre_str == ""


class TestParseReleaseDate:

    def test_success(self):
        App = GetGameInfo()
        APP_DETAILS = {"release_date": {"date": "Feb 20, 2024"}}
        year = App.parse_release_date(APP_DETAILS)
        assert year == 2024

    def test_insufficient_data(self):
        App = GetGameInfo()
        APP_DETAILS = {"release_date": {}}
        year = App.parse_release_date(APP_DETAILS)
        assert year == 0


class TestGetPriceInfo:

    def test_success(self):
        App = GetGameInfo()

        APP_DETAILS = {
            "price_overview": {
                "currency": "USD",
                "initial": 5999,
                "final": 2999,
                "discount_percent": 0.5,
                "initial_formatted": "$59.99",
                "final_formatted": "$29.99",
            }
        }

        price, discount = App.get_price_info(APP_DETAILS)
        assert price == 29.99
        assert discount == 0.5

    def test_insufficient_data(self):
        App = GetGameInfo()
        price, discount = App.get_price_info({})
        assert not price
        assert not discount


class TestGetTimeToBeat:
    def test_success(self):
        App = GetGameInfo()
        ttb = App.get_time_to_beat("Hades")
        assert isinstance(ttb, float)


class TestGetAppDetails:

    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        with open("tests/data/game_app_details.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            mock_response.json.return_value = data
        mock_response.ok = True
        return mock_response

    def test_success(self, mock_response, mocker):
        App = GetGameInfo()
        mocker.patch("requests.get", return_value=mock_response)
        assert App.get_app_details(2379780)

    def test_request_error(self, mock_response, mocker):
        App = GetGameInfo()
        mocker.patch("requests.get", return_value=mock_response)
        assert App.get_app_details(None) == {}


class TestGetGameInfo(Utils):

    def test_success(self, mocker):
        App = GetGameInfo()

        with open("tests/data/game_app_details.json", "r", encoding="utf-8") as file:
            app_details_json = json.load(file)
        app_details = app_details_json.get(str(2379780), {}).get("data")

        # mocks get_steam_review
        result = {"total": 9856, "percent": 0.97}
        mocker.patch("classes.steam.Steam.get_steam_review", return_value=result)
        # mocks get_steam_user_tags
        result = ["Roguelike", "Card Game", "Deckbuilding"]
        mocker.patch("classes.steam.Steam.get_steam_user_tags", return_value=result)
        # mocks get_time_to_beat
        mocker.patch("classes.game_info.GetGameInfo.get_time_to_beat", return_value=20)
        # mocks get_steam_game_player_count
        func = "classes.steam.Steam.get_steam_game_player_count"
        mocker.patch(func, return_value=600)

        api_key, _ = self.get_steam_api_key_and_id()

        game = App.get_game_info(app_details, api_key)
        assert isinstance(game, Game)
        # attribute check
        assert game.app_id == 2379780
        assert game.name == "Balatro"
        assert game.developer == "LocalThunk"
        assert game.publisher == "Playstack"
        assert game.genre == ["Casual", "Indie", "Strategy"]
        assert game.early_access == "No"
        assert game.steam_review_percent == 0.97
        assert game.steam_review_total == 9856
        assert game.user_tags == ["Roguelike", "Card Game", "Deckbuilding"]
        assert game.time_to_beat == 20
        assert game.player_count == 600
        assert game.release_year == 2024
        assert game.price == 14.99
        assert game.discount == 0.0
        assert game.on_sale == False
        assert game.categories == [
            "Single-player",
            "Steam Achievements",
            "Full controller support",
            "Steam Cloud",
            "Family Sharing",
        ]

    def test_not_enough_data(self):
        api_key, _ = self.get_steam_api_key_and_id()
        App = GetGameInfo()
        app_details = {}
        game = App.get_game_info(app_details, api_key)
        assert not game

    def test_missing_args(self):
        App = GetGameInfo()
        with pytest.raises(TypeError):
            App.get_game_info()
