from dataclasses import dataclass, field
from howlongtobeatpy import HowLongToBeat
import requests, time

from classes.utils import Utils
from classes.steam import Steam


@dataclass()
class Game(Steam, Utils):
    app_id: int
    name: str
    developer: str | None = None
    publisher: str | None = None
    steam_review_percent: float | None = None
    steam_review_total: int | None = None
    early_access: str = None
    time_to_beat: float | None = None
    release_year: int | None = None
    linux_compat: bool = False
    drm_notice: str | None = None
    # price
    price: float | None = None
    discount: float = 0.0
    on_sale: bool = False
    player_count: int | None = None
    # lists
    genre: list | None = None
    user_tags: list | None = None
    categories: list | None = None
    # no init
    game_url: str = field(init=False)
    genre_str: str = field(init=False)
    tags_str: str = field(init=False)
    categories_str: str = field(init=False)

    def __post_init__(self):
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
    def get_price_info(game_data: dict) -> tuple[float, float, bool]:
        """
        Gets price info from `game_info` and returns None if anything is set up
        wrong for any or all return values.
        """
        if "price_overview" not in game_data.keys():
            return None, None, None
        price_data = game_data["price_overview"]
        # price
        price = None
        if "final" in price_data:
            price = round(price_data["final"] * 0.01, 2)
        # discount
        discount = None
        if "discount_percent" in price_data.keys():
            discount = float(price_data["discount_percent"])
        # on sale
        on_sale = False
        if "discount_percent" in price_data.keys():
            on_sale = price_data["discount_percent"] > 0
            on_sale = price_data.get("discount_percent", {})
        return price, discount, on_sale

    def get_time_to_beat(self, game_name: str) -> float | str:
        """
        Uses howlongtobeatpy to get the time to beat for entered game.
        """
        beat = HowLongToBeat()
        self.api_sleeper("time_to_beat")
        try:
            results = beat.search(game_name)
        except:
            # TODO replace this
            for _ in range(3):
                time.sleep(10)
                results = beat.search(game_name)
            return "-"
        if not results:
            self.api_sleeper("time_to_beat")
            if game_name.isupper():
                results = beat.search(game_name.title())
            else:
                results = beat.search(game_name.upper())
        time_to_beat = "-"
        if results is not None and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = best_element.main_extra or best_element.main_story or "-"
        return time_to_beat

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
        app_id = game_data.get("steam_appid", None)
        game_name = game_data.get("name", None)
        if not app_id or not game_name:
            return None
        game_name_no_unicode = self.unicode_remover(game_name)
        developer = ", ".join(game_data.get("developers", []))
        publisher = ", ".join(game_data.get("publishers", []))
        genre = [desc["description"] for desc in game_data.get("genres", [])]
        early_access = "Yes" if "early access" in genre else "No"
        release_year = self.parse_release_date(game_data)
        price, discount, on_sale = self.get_price_info(game_data)
        linux_compat = game_data.get("platforms", {}).get("linux", False)
        categories = [desc["description"] for desc in game_data.get("categories", [])]
        drm_notice = game_data.get("drm_notice", None)
        # extra internet checks
        review_percent, review_total = self.get_steam_review(app_id=app_id)
        user_tags = self.get_steam_user_tags(app_id=app_id)
        ttb = self.get_time_to_beat(game_name_no_unicode)
        if steam_api_key:
            player_count = self.get_steam_game_player_count(app_id, steam_api_key)

        return Game(
            app_id=app_id,
            name=game_name,
            developer=developer,
            publisher=publisher,
            genre=genre,
            early_access=early_access,
            steam_review_percent=review_percent,
            steam_review_total=review_total,
            user_tags=user_tags,
            time_to_beat=ttb,
            player_count=player_count or None,
            release_year=release_year,
            price=price,
            discount=discount,
            on_sale=on_sale,
            linux_compat=linux_compat,
            categories=categories,
            drm_notice=drm_notice,
        )
