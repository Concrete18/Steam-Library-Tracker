# third-party imports
import requests, re
from bs4 import BeautifulSoup
from dataclasses import dataclass, field

# local imports
from library.utils.utils import *
from library.utils.api_throttler import ApiThrottler

throttler = ApiThrottler(default_wait=1)


@dataclass()
class StoreData:
    review_percent: float | None = None
    review_total: int | None = None
    early_access: bool = False
    user_tags: list[str] = field(default_factory=list)


class Scraper:
    url = "https://store.steampowered.com/app/"

    @staticmethod
    def get_review_data(soup: BeautifulSoup) -> tuple[float | None, int | None]:
        """
        Returns the review percent and total.
        """
        hidden_review_class = "nonresponsive_hidden responsive_reviewdesc"
        results = soup.find_all(class_=hidden_review_class)
        text = None
        percent, total = None, None
        if len(results) == 1:
            text = results[0].text.strip()
        elif len(results) > 1:
            text = results[1].text.strip()
        if text:
            parsed_data = text[2:26].split(r"% of the ")
            # get percent
            review_percentage = parsed_data[0]
            if review_percentage.isnumeric():
                if review_percentage == "100":
                    percent = 1
                else:
                    percent = float(f".{review_percentage}")
            # get total
            if len(parsed_data) > 1:
                cleaned_num = parsed_data[1].replace(",", "")
                total = int(re.search(r"\d+", cleaned_num).group()) or None
        return percent, total

    @staticmethod
    def get_steam_user_tags(soup: BeautifulSoup):
        """
        Gets a games user tags from Steam.
        """
        hidden_review_class = "app_tag"
        results = soup.find_all(class_=hidden_review_class)
        tags = []
        IGNORE_TAGS = ("+",)
        for tag in results:
            string = tag.text.strip()
            if string not in IGNORE_TAGS:
                tags.append(string)
        return tags

    @staticmethod
    def get_early_access(soup: BeautifulSoup) -> bool:
        """
        Returns True if the game is currently in early access.
        """
        return bool(soup.find(id="earlyAccessHeader"))

    @retry()
    def get_store_page_data(self, app_id: int) -> StoreData:
        """
        Gets some extra data by scraping the Steam Store page found using it's `app_id`.
        """
        throttler.wait_if("steam_store", 0.75)
        response = requests.get(f"{self.url}{app_id}")
        if not response.ok:
            return StoreData()
        soup = BeautifulSoup(response.text, "html.parser")
        percent, total = self.get_review_data(soup)
        early_access = self.get_early_access(soup)
        user_tags = self.get_steam_user_tags(soup)
        return StoreData(percent, total, early_access, user_tags)
