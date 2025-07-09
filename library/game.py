# standard library
from dataclasses import dataclass, field, fields
import time

# third-party imports
import requests

# local imports
from library.utils.utils import *
from library.steam.steam import *
from library.steam.scraper import Scraper

scraper = Scraper()
throttler = ApiThrottler()


@dataclass()
class Game:
    app_id: int = 0
    name: str = ""
    developer: str = ""
    publisher: str = ""
    review_percent: float = 0.0
    review_total: int = 0
    release_year: int = 0
    early_access: bool = False
    price: float | None = None
    discount: float = 0.0

    # lists
    # -----------------------------
    genre: list = field(default_factory=list)
    user_tags: list = field(default_factory=list)
    categories: list = field(default_factory=list)

    # no init
    # -----------------------------
    on_sale: bool = field(init=False)
    genre_str: str = field(init=False)
    tags_str: str = field(init=False)
    categories_str: str = field(init=False)

    def __post_init__(self):
        # on sale
        self.on_sale = self.discount > 0 if self.discount else False
        # create sentence strings
        self.tags_str = list_to_sentence(self.user_tags)
        self.genre_str = list_to_sentence(self.genre)
        self.categories_str = list_to_sentence(self.categories)

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

    @property
    def early_access_str(self):
        """
        Returns Yes/No depending on the early_access property value.
        """
        return "Yes" if self.early_access else "No"

    @property
    def store_link(self) -> str | None:
        """
        Generates a steam store url to the games page using it's `app_id`.
        """
        if self.app_id:
            return f"https://store.steampowered.com/app/{self.app_id}/"
        return None


def parse_release_date(app_details: dict) -> int:
    release_date = app_details.get("release_date", {}).get("date", {})
    year = get_year(release_date) if release_date else None
    return year or 0


def get_price(app_details: dict) -> tuple[float | None, float]:
    """
    Gets price info from `app_details` and returns None if anything is set up
    wrong for any or all return values.
    """
    if "price_overview" not in app_details:
        return None, 0.0
    price_data = app_details["price_overview"]
    # price
    price = price_data.get("final", None)
    final_price = round(price * 0.01, 2) if price else price
    # discount
    discount = float(price_data.get("discount_percent", 0.0))
    return final_price, discount


@retry()
def get_app_details(app_id: int) -> dict:
    """
    Gets game details.
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id, "cc": "us", "l": "english"}
    throttler.wait_if("steam_store")
    response = requests.get(url, params=params)
    if response.ok:
        data = response.json().get(str(app_id), {})
        if data.get("success"):
            return data.get("data", {})
        else:
            return {"app_id": app_id, "store": "delisted"}
    return {}


def get_game_info(app_details: dict, steam_key: str) -> Game:
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
    release_year = parse_release_date(app_details)
    price, discount = get_price(app_details)
    categories = [desc["description"] for desc in app_details.get("categories", [])]

    # TODO mock this data
    store_data = scraper.get_store_page_data(app_id)
    percent = store_data.review_percent
    total = store_data.review_total
    user_tags = store_data.user_tags
    early_access = store_data.early_access

    return Game(
        app_id=app_id,
        name=game_name,
        developer=developer,
        publisher=publisher,
        genre=genre,
        review_percent=percent,
        review_total=total,
        user_tags=user_tags,
        release_year=release_year,
        early_access=early_access,
        price=price,
        discount=discount,
        categories=categories,
    )
