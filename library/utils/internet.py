# standard library
import time

# third-party imports
from rich.console import Console
from rich.theme import Theme
import requests


class Internet:
    CHECK_INTERVAL_SECONDS = 600
    TEST_URL = "https://store.steampowered.com/"
    TIMEOUT_SECONDS = 5

    custom_theme = Theme(
        {
            "info": "dim cyan",
            "warning": "bold magenta",
            "danger": "bold red",
        }
    )
    console = Console(theme=custom_theme)

    def __init__(self):
        self.last_check_time = 0
        self.is_online()

    def is_online(self) -> bool:
        """
        Returns True if internet is available, False otherwise.
        """
        now = time.time()
        self.online = False
        if now - self.last_check_time > self.CHECK_INTERVAL_SECONDS:
            try:
                response = requests.get(self.TEST_URL, timeout=self.TIMEOUT_SECONDS)
                if response.ok:
                    self.online = True
            except requests.ConnectionError:
                pass
            self.last_check_time = now
        return self.online

    def print_status(self) -> None:
        """
        Prints info on whether the internet is online or not.
        """
        if self.online:
            self.console.print("Internet is Online", style="info")
        else:
            self.console.print("Internet is Offline", style="warning")


if __name__ == "__main__":
    internet = Internet()
    internet.print_status()
