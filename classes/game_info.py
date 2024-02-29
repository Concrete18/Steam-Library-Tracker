from dataclasses import dataclass, field
from howlongtobeatpy import HowLongToBeat
import requests, time

from classes.utils import Utils
from classes.steam import Steam
game = App.get_game_info(1458140)

@dataclass(frozen=True)
class Game(Utils):
    app_id: int
    name: str
    developer: str = field(default="-")
    publisher: str = field(default="-")
    genre: list | str = field(default="-")
    early_access: str = field(default="No")
    steam_review_percent: float | str = field(default="-")
    steam_review_total: int | str = field(default="-")
    user_tags: list | str = field(default="-")
    time_to_beat: float | str = field(default="-")
    release_year: int = field(default="-")
    price: float | str = field(default="-")
    discount: float = field(default=0.0)
    on_sale: bool = field(default=False)
    linux_compat: bool = field(default=False)
    categories: list | str = field(default="-")
    drm_notice: str = field(default="-")

    def get_genre_str(self):
        return self.list_to_sentence(self.genre)

    def get_categories_str(self):
        return self.list_to_sentence(self.categories)


class GetGameInfo(Steam, Utils):
    beat = HowLongToBeat()

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
        self.api_sleeper("time_to_beat")
        try:
            results = self.beat.search(game_name)
        except:
            for _ in range(3):
                time.sleep(10)
                results = self.beat.search(game_name)
            return "-"
        if not results:
            self.api_sleeper("time_to_beat")
            if game_name.isupper():
                results = self.beat.search(game_name.title())
            else:
                results = self.beat.search(game_name.upper())
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

    def get_game_info(self, game_data: dict) -> Game | None:
        """
        Retrieves game information using a `app_id` and returns a Game object or None if not found.
        """
        app_id = game_data.get("steam_appid", "-")
        game_name = game_data.get("name", "-")
        developer = ", ".join(game_data.get("developers", []))
        publisher = ", ".join(game_data.get("publishers", []))
        genre = [desc["description"] for desc in game_data.get("genres", [])]
        early_access = "Yes" if "early access" in genre else "No"

        review_percent, review_total = self.get_steam_review(app_id=app_id)
        user_tags = self.get_steam_user_tags(app_id=app_id)
        ttb = self.get_time_to_beat(self.unicode_remover(game_name))

        release_year = self.parse_release_date(game_data)
        price, discount, on_sale = self.get_price_info(game_data)
        linux_compat = game_data.get("platforms", {}).get("linux", False)
        categories = [desc["description"] for desc in game_data.get("categories", [])]
        drm_notice = game_data.get("drm_notice", "-")

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
            release_year=release_year,
            price=price,
            discount=discount,
            on_sale=on_sale,
            linux_compat=linux_compat,
            categories=categories,
            drm_notice=drm_notice,
        )
