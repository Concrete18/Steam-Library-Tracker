from dataclasses import dataclass, field
from classes.utils import Utils
import requests


@dataclass(frozen=True, order=True)
class Game(Utils):
    app_id: int
    name: str
    developer: str = "-"
    publisher: str = "-"
    genre: str = "-"
    release_year: int = "-"
    price: float | str = field(default="-")
    discount: float = field(default=0.0)
    on_sale: bool = False
    linux_compat: bool = False
    categories: str = "-"
    drm_notice: str = "-"

    def get_genre_str(self):
        return self.list_to_sentence(self.genre)

    def get_categories_str(self):
        return self.list_to_sentence(self.categories)


class GetGameInfo(Utils):

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
        return price, discount, on_sale

    def get_app_details(self, app_id: int) -> dict | None:
        """
        Gets game details.
        """
        url = "https://store.steampowered.com/api/appdetails"
        self.api_sleeper("steam_app_details")
        params = {"appids": app_id, "l": "english"}
        response = requests.get(url, params=params)
        if response.ok:
            return response.json().get(str(app_id), {}).get("data")
        return None

    def get_game_info(self, game_data: dict) -> Game | None:
        """
        Retrieves game information using a `app_id` and returns a GameInfo object or None if not found.
        """
        app_id = game_data.get("steam_appid", "-")
        game_name = game_data.get("name", "-")
        developer = ", ".join(game_data.get("developers", []))
        publisher = ", ".join(game_data.get("publishers", []))
        genre = [desc["description"] for desc in game_data.get("genres", [])]
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
            release_year=release_year,
            price=price,
            discount=discount,
            on_sale=on_sale,
            linux_compat=linux_compat,
            categories=categories,
            drm_notice=drm_notice,
        )
