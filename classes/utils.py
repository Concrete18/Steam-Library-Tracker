from pathlib import Path
import time, json, requests, re
from requests.exceptions import RequestException
from pick import pick
import datetime as dt
from typing import Callable, Any
from functools import wraps
from classes.logger import Logger


def benchmark(round_digits: int = 2) -> Callable[..., Any]:  # pragma: no cover
    """
    Prints `func` name and a benchmark for runtime.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                start = time.perf_counter()
                value = func(*args, **kwargs)
                end = time.perf_counter()
                elapsed = end - start
                print(f"{func.__name__} Completion Time: {elapsed:.{round_digits}f}")
                return value
            except Exception as e:
                print(f"Exception occurred in {func.__name__}: {e}")
                raise

        return wrapped

    return decorator


def retry(max_retries=4, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except RequestException:
                    retries += 1
                    time.sleep(delay)
            print(f"Failed after {max_retries} retries.")
            return None

        return wrapper

    return decorator


class Utils:
    Log = Logger()
    error_log = Log.create_log(name="helper", log_path="logs/error.log")

    @staticmethod
    def check_internet_connection(url="http://www.google.com"):
        """
        Checks if the internet is connected.
        """
        try:
            requests.head(url, timeout=5)
            return True
        except requests.exceptions.RequestException:  # pragma: no cover
            return False

    @staticmethod
    def get_steam_api_key_and_id() -> tuple[str, int]:
        """
        Gets the steam key and steam id from the config file.
        """
        # this function is here for import access
        config = Path("configs/config.json")
        with open(config) as file:
            data = json.load(file)
        api_key = data["steam_data"]["api_key"]
        steam_id = str(data["steam_data"]["steam_id"])
        return api_key, steam_id

    def create_hyperlink(self, url: str, label: str) -> str:
        """
        Generates a steam an excel HYPERLINK to `url` with the `label`.
        """
        return f'=HYPERLINK("{url}","{label}")'

    def api_sleeper(self, api, sleep_length=0.5, api_calls={}) -> None:
        """
        Delays delays for a set period of time if the `api` was run too recently.
        Delay length is set by `sleep_length`.
        """
        cur_datetime = dt.datetime.now()
        if api in api_calls.keys():
            if api_calls[api] + dt.timedelta(seconds=sleep_length) > cur_datetime:
                time.sleep(sleep_length)
        api_calls[api] = cur_datetime

    @staticmethod
    def hours_played(minutes_played: float) -> float:
        """
        Converts `minutes_played` to a hours played in decimal form.
        """
        if not minutes_played:
            return None
        hours_played = round(minutes_played / 60, 1)
        if hours_played == 0.0:
            return None
        return round(minutes_played / 60, 1)

    @staticmethod
    def get_game_url(app_id: int) -> str:
        """
        Generates a steam store url to the games page using it's `app_id`.
        """
        if app_id:
            return f"https://store.steampowered.com/app/{app_id}/"
        return app_id

    @staticmethod
    def string_to_date(date: str) -> dt.datetime:
        """
        Converts String `date` in MM/DD/YYYY format to datetime object.
        """
        return dt.datetime.strptime(date, "%m/%d/%Y")

    @staticmethod
    def get_year(date_string: str) -> int | None:
        """
        Gets the year from `date_string`.
        """
        if year := re.search(r"[0-9]{4}", date_string):
            return int(year.group(0))
        else:
            return None

    @staticmethod
    def days_since(past_date: dt.datetime, current_date: dt.datetime = None) -> int:
        """
        Gets the days since a `past_date`.

        if `current_date` is not given then it is set to the current date.
        """
        if not current_date:
            current_date = dt.datetime.now()
        delta = current_date - past_date
        return delta.days

    @staticmethod
    def format_floats(num, n_digits=None):
        """
        Formats floats to a specific rounding and adds commas for easier readability.
        """
        return f"{round(num, n_digits):,}"

    @staticmethod
    def url_sanitize(string: str, space_replace: str = "-") -> str:
        """
        Removes all illegal URL characters from the given `string`.

        Turns spaces into dashes if `space_to_dash` is true.
        """
        # Replace spaces with the specified character
        string = string.replace(" ", space_replace)
        # Remove illegal characters using regex
        string = re.sub(r"[^a-zA-Z0-9-_~./]+", "", string.lower()).strip()
        # Remove consecutive dashes
        string = re.sub(r"-{2,}", "-", string)
        return string

    @staticmethod
    def convert_time_passed(
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        weeks: int = 0,
        months: int = 0,
        years: int = 0,
    ) -> str:
        """
        Outputs a string for the time passed.

        Parameters:
        - minutes (int): Number of minutes.
        - hours (int): Number of hours.
        - days (int): Number of days.
        - weeks (int): Number of weeks.
        - months (int): Number of months.
        - years (int): Number of years.

        Return format examples:
        - "1.0 Minute"
        - "2.3 Hours"
        - "4.5 Days"
        - "6.7 Weeks"
        - "8.9 Months"
        - "2.1 Years"
        """
        # converts all into hours
        HOURS_IN_DAY = 24
        HOURS_IN_WEEK = 168
        HOURS_IN_MONTH = 730
        HOURS_IN_YEAR = 8_760
        hours = (
            (minutes / 60)
            + hours
            + (days * HOURS_IN_DAY)
            + (weeks * HOURS_IN_WEEK)
            + (months * HOURS_IN_MONTH)
            + (years * HOURS_IN_YEAR)
        )
        rounded_hours = round(hours)
        # gets format
        if rounded_hours >= HOURS_IN_YEAR:
            total = round(hours / HOURS_IN_YEAR, 1)
            time_passed = f"{total} Year"
        elif rounded_hours >= HOURS_IN_MONTH:
            total = round(hours / HOURS_IN_MONTH, 1)
            time_passed = f"{total} Month"
        elif rounded_hours >= HOURS_IN_WEEK:
            total = round(hours / HOURS_IN_WEEK, 1)
            time_passed = f"{total} Week"
        elif rounded_hours >= HOURS_IN_DAY:
            total = round(hours / HOURS_IN_DAY, 1)
            time_passed = f"{total} Day"
        elif hours >= 1:
            total = round(hours, 1)
            time_passed = f"{total} Hour"
        else:
            total = round(hours * 60, 1)
            time_passed = f"{total} Minute"
        # makes string plural if needed
        if total > 1:
            time_passed += "s"
        # fixes values that end up slightly off
        CORRECTION_DICT = {
            "60.0 Minutes": "1.0 Hour",
            "24.0 Hours": "1.0 Day",
            "7.0 Days": "1.0 Week",
            "4.0 Weeks": "1.0 Month",
            "12.0 Months": "1.0 Year",
        }
        if time_passed in CORRECTION_DICT.keys():
            time_passed = CORRECTION_DICT[time_passed]
        return time_passed

    @staticmethod
    def unicode_remover(string) -> str:
        """
        Removes unicode from `string`.
        """
        if type(string) != str:
            return string
        UNICODE_CONVERSIONS = {
            # unicode character
            "â€": "'",
            "®": "",
            "™": "",
            "â„¢": "",
            "Â": "",
            "Ã›": "U",
            "ö": "o",
            "Ã¶": "o",
            # unicode value
            "\u2122": "",  # Trademarked sign
            "\u00ae": "",  # REGISTERED SIGN
            "\u00e5": "a",  # a
            "\u00f6": "o",  # LATIN SMALL LETTER O WITH DIAERESIS
            "\u00e9": "e",  # LATIN SMALL LETTER E WITH ACUTE
            "\u2013": "-",  # EN DASH
            # HTML entities
            "&amp": "&",  # &
            "&quot;": '"',  # "
            "&apos;": "'",  # '
            "&cent;": "",  # cent
            "&copy;": "",  # copyright sign
            "&reg;": "",  # trademark sign
        }
        for unicode in UNICODE_CONVERSIONS.keys():
            if unicode in string:
                for unicode, sub in UNICODE_CONVERSIONS.items():
                    string = string.replace(unicode, sub)
        conv_string = string.encode("ascii", "ignore").decode()
        return conv_string.strip()

    @staticmethod
    def list_to_sentence(str_list: list[str]) -> str:
        """
        Converts a list of strings into a comma seperated string of words
        with "and" instead of a comma between the last two entries.
        """
        str_list_length = len(str_list)
        if str_list_length == 0:
            return ""
        elif str_list_length == 1:
            return str_list[0]
        else:
            comma_separated = ", ".join(str_list[:-1])
            return f"{comma_separated} and {str_list[-1]}"

    def is_response_yes(
        self, prompt: str, default_to_yes: bool = True
    ) -> bool:  # pragma: no cover
        """
        Asks for a Yes or No response. Yes returns True and No returns False.
        """
        choices = ["Yes", "No"] if default_to_yes else ["No", "Yes"]
        return pick(options=choices, title=prompt, indicator="->")[0] == "Yes"

    def create_rich_date_and_time(self, date: dt.datetime = dt.datetime.now()) -> str:
        """
        Returns a formatted date and time for use with Rich Console print.
        """
        formatted_date = f"[secondary]{date.strftime('%A, %B %d, %Y')}[/]"
        formatted_time = f"[secondary]{date.strftime('%I:%M %p')}[/]"
        return f"{formatted_date} [dim]|[/] {formatted_time}"

    def save_json(self, new_data: dict, filename: str):
        """
        Saves data into json format with the given filename.
        """
        json_object = json.dumps(new_data, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
        with open(filename) as file:
            last_check_data = json.load(file)
            if new_data != last_check_data:
                raise PermissionError("Data did not save error")  # pragma: no cover

    def update_last_run(
        self, data: dict, config_path: str, name: str
    ):  # pragma: no cover
        """
        Updates json by `name` with the current date.
        """
        data["last_runs"][name] = time.time()
        self.save_json(data, config_path)

    def recently_executed(self, data: dict, name: str, n_days: int):
        """
        Check if a specific task named `name` was executed within the `n_days`.
        """
        last_runs = data["last_runs"]
        if name in last_runs.keys():
            last_run = last_runs[name]
            sec_since = time.time() - last_run
            check_freq_seconds = n_days * 24 * 60 * 60
            if sec_since < check_freq_seconds:
                return True
        return False
