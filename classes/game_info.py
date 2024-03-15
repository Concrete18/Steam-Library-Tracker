from dataclasses import dataclass, field
from howlongtobeatpy import HowLongToBeat
import requests, time

from classes.utils import Utils, retry
from classes.steam import Steam


@dataclass()
class Game(Utils):
    app_id: int
    name: str
    developer: str | None = None
    publisher: str | None = None
    steam_review_percent: float | None = None
    steam_review_total: int | None = None
    release_year: int | None = None
    price: float | None = None
    discount: float = 0.0
    linux_compat: bool = False
    drm_notice: str | None = None
    player_count: int | None = None
    time_to_beat: float | None = None
    # lists
    genre: list = field(default_factory=list)
    user_tags: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    # no init
    on_sale: bool = field(init=False)
    early_access: str = field(init=False)
    game_url: str = field(init=False)
    genre_str: str = field(init=False)
    tags_str: str = field(init=False)
    categories_str: str = field(init=False)

    def __post_init__(self):
        self.early_access = "Yes" if "early access" in self.genre else "No"
        self.on_sale = False if not self.discount else self.discount > 0
        self.game_url = self.get_game_url(self.app_id)
        # create sentence strings
        self.tags_str = self.convert_to_sentence(self.user_tags)
        self.genre_str = self.convert_to_sentence(self.genre)
        self.categories_str = self.convert_to_sentence(self.categories)

    def convert_to_sentence(self, items: list[str] | None) -> str | None:
        """
        Convert a list of items into a sentence.
        """
        if items:
            return self.list_to_sentence(items)
        return None


class GetGameInfo(Steam, Utils):

    def parse_release_date(self, game_data) -> int:
        release_date = game_data["release_date"]["date"]
        year = self.get_year(release_date)
        return year or "-"

    @staticmethod
    def get_price_info(game_data: dict) -> tuple[float, float]:
        """
        Gets price info from `game_info` and returns None if anything is set up
        wrong for any or all return values.
        """
        if "price_overview" not in game_data.keys():
            return None, None
        price_data = game_data["price_overview"]
        # price
        price = None
        if "final" in price_data:
            price = round(price_data["final"] * 0.01, 2)
        # discount
        discount = float(price_data.get("discount_percent", 0.0))
        return price, discount

    def get_time_to_beat(self, game_name: str) -> float | str:
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
        beat = HowLongToBeat()
        self.api_sleeper("time_to_beat")
        try:
            results = beat.search(game_name)
        except:  # pragma: no cover
            for _ in range(3):
                time.sleep(10)
                results = beat.search(game_name)
            return "-"
        if not results:
            self.api_sleeper("time_to_beat")
            results = beat.search(game_name, similarity_case_sensitive=False)
        time_to_beat = "-"
        if results and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = best_element.main_extra or best_element.main_story or "-"
        return time_to_beat

    @retry()
    def get_app_details(self, app_id: int) -> dict | None:
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id, "l": "english"}
        self.api_sleeper("steam_app_details")
        response = requests.get(url, params=params)
        if response.ok:
            return response.json().get(str(app_id), {}).get("data")
        return None

    def get_game_info(self, game_data: dict, steam_api_key=None) -> Game | None:
        """
        Creates a Game object with data from `game_data`.
        """
        if not game_data:
            return None
        app_id = game_data.get("steam_appid", None)
        game_name = game_data.get("name", None)
        if not app_id or not game_name:
            return None
        developer = ", ".join(game_data.get("developers", []))
        publisher = ", ".join(game_data.get("publishers", []))
        genre = [desc["description"] for desc in game_data.get("genres", [])]
        release_year = self.parse_release_date(game_data)
        price, discount = self.get_price_info(game_data)
        linux_compat = game_data.get("platforms", {}).get("linux", False)
        categories = [desc["description"] for desc in game_data.get("categories", [])]
        drm_notice = game_data.get("drm_notice", None)
        # extra internet checks
        review_percent, review_total = self.get_steam_review(app_id=app_id)
        user_tags = self.get_steam_user_tags(app_id=app_id)
        game_name_no_unicode = self.unicode_remover(game_name)
        ttb = self.get_time_to_beat(game_name_no_unicode)
        player_count = (
            self.get_steam_game_player_count(app_id, steam_api_key)
            if steam_api_key
            else None
        )

        return Game(
            app_id=app_id,
            name=game_name,
            developer=developer,
            publisher=publisher,
            genre=genre,
            steam_review_percent=review_percent,
            steam_review_total=review_total,
            user_tags=user_tags,
            time_to_beat=ttb,
            player_count=player_count,
            release_year=release_year,
            price=price,
            discount=discount,
            linux_compat=linux_compat,
            categories=categories,
            drm_notice=drm_notice,
        )
