# standard library
import json

# third-party imports
import pytest

# local imports
from library.game import *
from library.utils.utils import *
from library.steam.scraper import StoreData

WAIT_IF = "library.utils.api_throttler.ApiThrottler.wait_if"


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
            early_access=True,
            price=12.34,
            discount=0.88,
            categories=["Category 1"],
            user_tags=["Tag 1"],
        )
        assert len(vars(game)) == 17
        assert game.app_id == APP_ID
        assert game.name == NAME
        assert game.developer == "Dev"
        assert game.publisher == "Pub"
        assert game.early_access_str == "Yes"
        assert game.genre == ["Testing", "early access"]
        assert game.release_year == 2024
        assert game.price == 12.34
        assert game.discount == 0.88
        assert game.on_sale
        assert game.categories == ["Category 1"]
        assert game.user_tags == ["Tag 1"]

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
            user_tags=["Testing"],
        )
        assert game.early_access_str == "No"

    def test_no_args(self):
        game = Game()
        assert not Game()
        # total attributes
        assert len(vars(game)) == 17
        # required values
        assert game.name == ""
        assert game.app_id == 0
        # str
        assert game.early_access_str == "No"
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
        assert game.review_percent == 0.0
        assert game.review_total == 0
        assert game.price is None
        assert game.tags_str == ""
        assert game.categories_str == ""
        assert game.genre_str == ""


class TestParseReleaseDate:

    def test_success(self):
        APP_DETAILS = {"release_date": {"date": "Feb 20, 2024"}}
        year = parse_release_date(APP_DETAILS)
        assert year == 2024

    def test_insufficient_data(self):
        APP_DETAILS = {"release_date": {}}
        year = parse_release_date(APP_DETAILS)
        assert year == 0


class TestGetPriceInfo:

    def test_success(self):

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

        price, discount = get_price(APP_DETAILS)
        assert price == 29.99
        assert discount == 0.5

    def test_insufficient_data(self):
        price, discount = get_price({})
        assert not price
        assert not discount


class TestGetAppDetails:

    @pytest.fixture
    def mock_response(self, mocker):
        mocker.patch(WAIT_IF, return_value=None)
        with open("tests/data/game_app_details.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        mock_response = mocker.Mock()
        mock_response.json.return_value = data
        mock_response.ok = True
        return mock_response

    def test_success(self, mock_response, mocker):
        mocker.patch(WAIT_IF, return_value=False)
        mocker.patch("requests.get", return_value=mock_response)
        app_details = get_app_details(2379780)
        assert app_details

        app_id = app_details.get("steam_appid", 0)
        game_name = app_details.get("name", "")
        assert app_id == 2379780
        assert game_name == "Balatro"

    def test_request_error(self, mock_response, mocker):
        mocker.patch(WAIT_IF, return_value=False)
        mock_response.ok = False
        mocker.patch("requests.get", return_value=mock_response)
        assert get_app_details(2379780) == {}


class TestGetGameInfo:

    def test_success(self, mocker):
        app_id = 2379780

        with open("tests/data/game_app_details.json", "r", encoding="utf-8") as file:
            app_details_json = json.load(file)
        app_details = app_details_json.get(str(app_id), {}).get("data")

        # mocks get_review_data
        mocker.patch(
            "library.steam.scraper.Scraper.get_review_data", return_value=(0.97, 9856)
        )

        # mocks get_steam_user_tags
        result = ["Roguelike", "Card Game", "Deckbuilding"]
        mocker.patch(
            "library.steam.scraper.Scraper.get_steam_user_tags", return_value=result
        )

        # mocks get_store_page_data
        func = "library.steam.scraper.Scraper.get_store_page_data"
        store_data = StoreData(
            review_percent=0.97,
            review_total=9856,
            early_access=False,
            user_tags=["Roguelike", "Card Game", "Deckbuilding"],
        )
        mocker.patch(func, return_value=store_data)

        api_key, _ = get_steam_key_and_id()

        game = get_game_info(app_details, api_key)
        assert isinstance(game, Game)
        # attribute check
        assert game.app_id == app_id
        assert game.name == "Balatro"
        assert game.developer == "LocalThunk"
        assert game.publisher == "Playstack"
        assert game.genre == ["Casual", "Indie", "Strategy"]
        assert game.early_access_str == "No"
        assert game.review_percent == 0.97
        assert game.review_total == 9856
        assert game.user_tags == ["Roguelike", "Card Game", "Deckbuilding"]
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
        api_key, _ = get_steam_key_and_id()
        app_details = {}
        game = get_game_info(app_details, api_key)
        assert not game

    def test_missing_args(self):
        with pytest.raises(TypeError):
            get_game_info()  # type: ignore
