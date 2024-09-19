# standard library
from dataclasses import dataclass, field, fields
import time

# third-party imports
import requests
from howlongtobeatpy import HowLongToBeat

# local imports
from utils.utils import *
from utils.steam import *


@dataclass()
class Game:
    app_id: int = 0
    name: str = ""
    developer: str = ""
    publisher: str = ""
    review_percent: float = 0.0
    review_total: int | None = None
    release_year: int = 0
    price: float | None = None
    discount: float = 0.0
    player_count: int | None = None
    # time_to_beat: float = 0.0

    # lists
    # -----------------------------
    genre: list = field(default_factory=list)
    user_tags: list = field(default_factory=list)
    categories: list = field(default_factory=list)

    # no init
    # -----------------------------
    on_sale: bool = field(init=False)
    early_access: str = field(init=False)
    game_url: str = field(init=False)
    genre_str: str = field(init=False)
    tags_str: str = field(init=False)
    categories_str: str = field(init=False)

    def __post_init__(self):
        # on sale
        self.on_sale = self.discount > 0 if self.discount else False
        # game url
        self.game_url = get_game_url(self.app_id) if self.app_id else self.app_id
        # create sentence strings
        self.tags_str = list_to_sentence(self.user_tags)
        self.genre_str = list_to_sentence(self.genre)
        self.categories_str = list_to_sentence(self.categories)
        # early access
        self.early_access = self.is_early_access()

    def __repr__(self):  # pragma: no cover
        string = "Game("
        if self:
            for field in fields(self):
                string += f"\n  {field.name}: {getattr(self, field.name)}"
            string += "\n)"
        else:
            string = "Game(\n  Invalid\n)"
        return string

    def __bool__(self):
        return bool(self.app_id and self.name)

    @property
    def cleaned_name(self):
        return unicode_remover(self.name)

    @staticmethod
    def get_time_to_beat(game_name: str) -> float | str:
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
        beat = HowLongToBeat()
        api_sleeper("time_to_beat")
        try:
            results = beat.search(game_name)
        except:  # pragma: no cover
            time.sleep(10)
            for _ in range(3):
                try:
                    results = beat.search(game_name)
                    break
                except:
                    time.sleep(10)
            return "-"
        if not results:  # pragma: no cover
            api_sleeper("time_to_beat")
            results = beat.search(game_name, similarity_case_sensitive=False)
        time_to_beat = "-"
        if results and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = best_element.main_extra or best_element.main_story or "-"
        return time_to_beat

    def is_early_access(self) -> str:
        if (
            "early access" in self.genre_str.lower()
            or "early access" in self.tags_str.lower()
        ):
            return "Yes"
        return "No"


class GetGameInfo:

    def parse_release_date(self, app_details: dict) -> int:
        release_date = app_details.get("release_date", {}).get("date", {})
        year = get_year(release_date) if release_date else None
        return year or 0

    @staticmethod
    def get_price(app_details: dict) -> tuple[float | None, float]:
        """
        Gets price info from `app_details` and returns None if anything is set up
        wrong for any or all return values.
        """
        if "price_overview" not in app_details:
            return None, None
        price_data = app_details["price_overview"]
        # price
        price = price_data.get("final", None)
        final_price = round(price * 0.01, 2) if price else price
        # discount
        discount = float(price_data.get("discount_percent", 0.0))
        return final_price, discount

    @staticmethod
    @retry()
    def get_app_details(app_id: int) -> dict:
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id, "l": "english"}
        api_sleeper("steam_app_details")
        response = requests.get(url, params=params)
        if response.ok:
            return response.json().get(str(app_id), {}).get("data", {})
        return {}

    def get_game_info(self, app_details: dict, steam_key: str) -> Game:
        """
        Creates a Game object with `app_id`, `game_name` and data from `app_details`.
        """
        if not app_details or not steam_key:
            return Game()
        app_id = app_details.get("steam_appid", 0)
        game_name = app_details.get("name", "")
        developer = ", ".join(app_details.get("developers", []))
        publisher = ", ".join(app_details.get("publishers", []))
        genre = [desc["description"] for desc in app_details.get("genres", [])]
        release_year = self.parse_release_date(app_details)
        price, discount = self.get_price(app_details)
        categories = [desc["description"] for desc in app_details.get("categories", [])]
        # review
        percent, total = get_steam_review(app_id)
        # user tags
        user_tags = get_steam_user_tags(app_id)
        # player count
        player_count = get_player_count(app_id, steam_key) if steam_key else None

        return Game(
            app_id=app_id,
            name=game_name,
            developer=developer,
            publisher=publisher,
            genre=genre,
            review_percent=percent,
            review_total=total,
            user_tags=user_tags,
            player_count=player_count,
            release_year=release_year,
            price=price,
            discount=discount,
            categories=categories,
        )
