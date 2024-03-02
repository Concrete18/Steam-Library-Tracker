import pytest, json

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
        assert game.game_url == "https://store.steampowered.com/app/12345/"
        assert game.drm_notice == "Has DRM"

    def test_only_required_args(self):
        name = "Test1"
        app_id = 12345
        game = Game(app_id=app_id, name=name)
        # total attributes
        assert len(vars(game)) == 22
        # required values
        assert game.name == name
        assert game.app_id == app_id
        # str
        assert game.game_url == "https://store.steampowered.com/app/12345/"
        # float
        assert game.discount == 0.0
        # false
        assert game.on_sale == False
        assert game.linux_compat == False
        # none
        assert game.developer == None
        assert game.publisher == None
        assert game.early_access == None
        assert game.genre == None
        assert game.categories == None
        assert game.categories_str == None
        assert game.user_tags == None
        assert game.tags_str == None
        assert game.genre_str == None
        assert game.release_year == None
        assert game.steam_review_percent == None
        assert game.steam_review_total == None
        assert game.price == None
        assert game.drm_notice == None
        assert game.time_to_beat == None
        assert game.player_count == None

    def test_no_args(self):
        with pytest.raises(TypeError):
            Game()


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

        assert App.get_app_details(2379780)

    def test_request_error(self, mock_response, mocker):
        App = GetGameInfo()

        mocker.patch("requests.get", return_value=mock_response)

        assert App.get_app_details(None) is None


class TestGetGameInfo:

    @staticmethod
    def get_steam_api_key() -> str:
        """
        Gets the steam API key from the config file.
        """
        with open("configs/config.json") as file:
            data = json.load(file)
        api_key = data["steam_data"]["api_key"]
        return api_key

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
        mocker.patch(
            "classes.steam.Steam.get_steam_game_player_count", return_value=600
        )

        game = App.get_game_info(game_data, self.get_steam_api_key())
        assert isinstance(game, Game)
        # attribute check
        assert game.name == "Balatro"
        assert game.app_id == 2379780
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
        assert game.linux_compat == False
        assert game.categories == [
            "Single-player",
            "Steam Achievements",
            "Full controller support",
            "Steam Cloud",
            "Family Sharing",
        ]
        assert game.drm_notice == None

    def test_not_enough_data(self):
        App = GetGameInfo()

        game_data = {}
        game = App.get_game_info(game_data)
        assert game is None


if __name__ == "__main__":
    pytest.main([__file__])
