import pytest, json, requests
from howlongtobeatpy import HowLongToBeat


from classes.game_info import Game, GetGameInfo


class TestGame:

    def test_given_args(self):
        name = "Test1"
        app_id = 12345
        game = Game(
            name=name,
            app_id=app_id,
            developer="Dev",
            publisher="Pub",
            genre="Testing",
            release_year=2024,
            price=12.34,
            discount=0.88,
            on_sale=True,
            linux_compat="Verified",
            categories="Tests",
            drm_notice="Has DRM",
        )
        assert game.app_id == app_id
        assert game.name == name
        assert game.developer == "Dev"
        assert game.publisher == "Pub"
        assert game.genre == "Testing"
        assert game.release_year == 2024
        assert game.price == 12.34
        assert game.discount == 0.88
        assert game.on_sale == True
        assert game.linux_compat == "Verified"
        assert game.categories == "Tests"
        assert game.drm_notice == "Has DRM"

    def test_no_args(self):
        name = "Test1"
        app_id = 12345
        game = Game(app_id=app_id, name=name)
        assert game.name == name
        assert game.app_id == app_id
        assert game.publisher == "-"
        assert game.genre == "-"
        assert game.release_year == "-"
        assert game.price == "-"
        assert game.discount == 0.0
        assert game.on_sale == False
        assert game.linux_compat == False
        assert game.categories == "-"
        assert game.drm_notice == "-"

    def test_get_genre_str(self):
        name = "Test1"
        app_id = 12345
        game = Game(
            app_id=app_id,
            name=name,
            genre=[
                "Casual",
                "Indie",
                "Strategy",
            ],
        )
        genre_str_answer = "Casual, Indie and Strategy"
        assert game.get_genre_str() == genre_str_answer

    def test_get_categories_str(self):
        name = "Test1"
        app_id = 12345
        game = Game(
            app_id=app_id,
            name=name,
            categories=[
                "Single-player",
                "Steam Achievements",
                "Steam Cloud",
            ],
        )
        categories_str_answer = "Single-player, Steam Achievements and Steam Cloud"
        assert game.get_categories_str() == categories_str_answer


class TestParseReleaseDate:

    def test_success(self):
        App = GetGameInfo()
        game_data = {"release_date": {"date": "Feb 20, 2024"}}
        year = App.parse_release_date(game_data)
        assert year == 2024


class TestGetPriceInfo:

    def test_success(self):
        App = GetGameInfo()

        game_data = {
            "price_overview": {
                "currency": "USD",
                "initial": 5999,
                "final": 2999,
                "discount_percent": 0.5,
                "initial_formatted": "$59.99",
                "final_formatted": "$29.99",
            }
        }

        price, discount, on_sale = App.get_price_info(game_data)
        assert price == 29.99
        assert discount == 0.5
        assert on_sale

    def test_insufficient_data(self):
        App = GetGameInfo()

        price, discount, on_sale = App.get_price_info({})
        assert not price
        assert not discount
        assert not on_sale


class TestGetTimeToBeat:
    def test_success(self):
        App = GetGameInfo()
        ttb = App.get_time_to_beat("Hades")
        assert isinstance(ttb, float)


class TestGetAppDetails:

    @pytest.fixture
    def mock_response(self, mocker):
        mock_response = mocker.Mock()
        with open("tests\example_game_app_details.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            mock_response.json.return_value = data
        mock_response.ok = True
        return mock_response

    def test_success(self, mock_response, mocker):
        App = GetGameInfo()

        mocker.patch("requests.get", return_value=mock_response)

        game_data = App.get_app_details(2379780)

        assert game_data

    def test_request_error(self, mocker):
        App = GetGameInfo()

        test_exception = requests.RequestException("Test error")
        mocker.patch("requests.get", side_effect=test_exception)

        result = App.get_app_details(None)
        assert result is None


class TestGetGameInfo:

    def test_success(self, mocker):
        App = GetGameInfo()

        with open("tests\example_game_app_details.json", "r", encoding="utf-8") as file:
            app_details_json = json.load(file)

        game_data = app_details_json.get(str(2379780), {}).get("data")

        mocker.patch("classes.steam.Steam.get_steam_review", return_value=(0.97, 9856))
        mocker.patch(
            "classes.steam.Steam.get_steam_user_tags",
            return_value=[
                "Roguelike",
                "Card Game",
                "Deckbuilding",
            ],
        )
        mocker.patch("classes.game_info.GetGameInfo.get_time_to_beat", return_value=20)

        game = App.get_game_info(game_data)
        assert game == Game(
            name="Balatro",
            app_id=2379780,
            developer="LocalThunk",
            publisher="Playstack",
            genre=[
                "Casual",
                "Indie",
                "Strategy",
            ],
            early_access="No",
            steam_review_percent=0.97,
            steam_review_total=9856,
            user_tags=[
                "Roguelike",
                "Card Game",
                "Deckbuilding",
            ],
            time_to_beat=20,
            release_year=2024,
            price=14.99,
            discount=0.0,
            on_sale=False,
            linux_compat=False,
            categories=[
                "Single-player",
                "Steam Achievements",
                "Full controller support",
                "Steam Cloud",
                "Family Sharing",
            ],
            drm_notice="-",
        )


if __name__ == "__main__":
    pytest.main([__file__])
