# standard library
from typing import Callable
import time

# third-party imports
from rich.console import Console
from rich.theme import Theme
import requests


class Internet:
    custom_theme = Theme(
        {
            # error
            "info": "dim cyan",
            "warning": "bold magenta",
            "danger": "bold red",
        }
    )
    console = Console(theme=custom_theme)

    def __init__(self):
        self.last_check_time = 0
        self.online = False

    def is_internet_available(self) -> bool:
        """
        Returns True if internet is available, False otherwise.
        """
        if time.time() - self.last_check_time > 600:
            try:
                requests.get("http://www.google.com", timeout=5)
                self.online = True
            except requests.ConnectionError:
                self.online = False
                self.console.print("No Internet Detected", style="warning")
            self.last_check_time = time.time()
        return self.online

    def check(self, func: Callable) -> Callable:
        """
        Checks if the internet is available sets the online class attribute to True or False.
        """

        def wrapper(*args, **kwargs):
            if not self.is_internet_available():
                return None
            return func(*args, **kwargs)

        return wrapper


if __name__ == "__main__":
    internet = Internet()

    @internet.check
    def test():
        if internet.online:
            print("Internet is Online")
        else:
            print("Internet is Offline")

    test()
