from pathlib import Path
import time, json, requests, re, heapq
from pick import pick
import datetime as dt
from typing import Callable, Any
from functools import wraps
from classes.logger import Logger


def keyboard_interrupt(func):  # pragma: no cover
    """
    Decorator to catch KeyboardInterrupt and EOFError exceptions.

    Provides a delayed exit with an optional user confirmation.
    """

    def wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, EOFError):
            delay = 0.1
            print(f"\nClosing in {delay} second(s)")
            time.sleep(delay)
            exit()

    return wrapped


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


def get_steam_api_key_and_id() -> tuple[str, int]:
    """
    Gets the steam key and steam id from the config file.
    """
    config = Path("configs/config.json")
    with open(config) as file:
        data = json.load(file)
    api_ley = data["steam_data"]["api_key"]
    steam_id = str(data["steam_data"]["steam_id"])
    return api_ley, steam_id


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

    def request_url(self, url, params=None, headers=None, second_try=False):
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if second_try:
                return False
            msg = None
            if isinstance(e, requests.exceptions.ConnectionError):
                msg = "Connection Error: Internet can't be accessed"
            elif isinstance(e, requests.exceptions.TooManyRedirects):
                msg = "Too Many Redirects: Exceeded 30 redirects"
            elif isinstance(e, requests.exceptions.ReadTimeout):
                return False
            else:
                msg = f"Unknown Error: {e}"

            self.error_log.warning(msg)
            time.sleep(5)
            return self.request_url(
                url,
                params=params,
                headers=headers,
                second_try=True,
            )

        msg = "Unknown Error"
        if response.status_code == requests.codes.ok:
            return response
        elif response.status_code == 500:
            msg = "Server Error: make sure your api key and steam id is valid"
        elif response.status_code == 404:
            msg = f"Server Error: 404 Content does not exist. URL: {url}"
        elif response.status_code == 429 or response.status_code == 403:
            msg = "Server Error: Too Many requests made. Waiting to try again"
            self.error_log.warning(response)
            time.sleep(5)
            return self.request_url(url, params=params, headers=headers)

        self.error_log.warning(msg)
        return False

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
        hours_played = round(minutes_played / 60, 1)
        if hours_played == 0.0:
            return None
        return round(minutes_played / 60, 1)

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
        year = re.search(r"[0-9]{4}", date_string)
        if year:
            return year.group(0)
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
        hours_in_day = 24
        hours_in_week = 168
        hours_in_month = 730
        hours_in_year = 8760
        hours = (
            (minutes / 60)
            + hours
            + (days * hours_in_day)
            + (weeks * hours_in_week)
            + (months * hours_in_month)
            + (years * hours_in_year)
        )
        rounded_hours = round(hours)
        # gets format
        if rounded_hours >= hours_in_year:
            total = round(hours / hours_in_year, 1)
            time_passed = f"{total} Year"
        elif rounded_hours >= hours_in_month:
            total = round(hours / hours_in_month, 1)
            time_passed = f"{total} Month"
        elif rounded_hours >= hours_in_week:
            total = round(hours / hours_in_week, 1)
            time_passed = f"{total} Week"
        elif rounded_hours >= hours_in_day:
            total = round(hours / hours_in_day, 1)
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
        # fixs values that end up slightly off
        fix_dict = {
            "60.0 Minutes": "1.0 Hour",
            "24.0 Hours": "1.0 Day",
            "7.0 Days": "1.0 Week",
            "4.0 Weeks": "1.0 Month",
            "12.0 Months": "1.0 Year",
        }
        if time_passed in fix_dict.keys():
            time_passed = fix_dict[time_passed]
        return time_passed

    @staticmethod
    def unicode_remover(string) -> str:
        """
        Removes unicode from `string`.
        """
        if type(string) != str:
            return string
        replace_dict = {
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
        for unicode in replace_dict.keys():
            if unicode in string:
                for unicode, sub in replace_dict.items():
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

    def levenshtein_distance(self, word1: str, word2: str, lower: bool = True) -> int:
        """
        Returns the Levenshtein distance of `word1` and `word2`.
        """
        if lower:
            word1, word2 = word1.lower(), word2.lower()
        cache = [[float("inf")] * (len(word2) + 1) for _ in range(len(word1) + 1)]
        for j in range(len(word2) + 1):
            cache[len(word1)][j] = len(word2) - j
        for i in range(len(word1) + 1):
            cache[i][len(word2)] = len(word1) - i
        for i in range(len(word1) - 1, -1, -1):
            for j in range(len(word2) - 1, -1, -1):
                if word1[i] == word2[j]:
                    cache[i][j] = cache[i + 1][j + 1]
                else:
                    min_change = min(
                        cache[i + 1][j], cache[i][j + 1], cache[i + 1][j + 1]
                    )
                    cache[i][j] = 1 + min_change
        return cache[0][0]

    def lev_dist_matcher(
        self,
        base_string: str,
        string_list: list,
        max_distance: int = 0,
        limit: int = 5,
    ):
        """
        Finds a match for `base_string` in `string_list` using sequence matching.
        """
        if max_distance < 1:
            max_distance = round(len(base_string) * 0.5)
        matches = {}
        for string in string_list:
            distance = self.levenshtein_distance(base_string, string)
            if distance < max_distance:
                max_distance = distance
                matches[string] = distance
        sorted_keys = sorted(matches, key=matches.get)
        if len(sorted_keys) > limit:
            sorted_keys = sorted_keys[0:limit]  # pragma: no cover
        return sorted_keys

    def create_levenshtein_matcher(
        self,
        base_string: str,
        n: int = 5,
    ):
        """
        Creates a closure function for running multiple levenshtein distance checks and keeping the top n results.
        """
        best_matches = []

        def matcher(new_string):
            nonlocal best_matches
            # Calculate Levenshtein distance
            distance = self.levenshtein_distance(base_string, new_string)
            # Add the distance and string to the list
            heapq.heappush(best_matches, (distance, new_string))
            # Keep only the top n best matches
            best_matches = heapq.nsmallest(n, best_matches)
            return [match[1] for match in best_matches]  # return only the strings

        return matcher

    def any_is_num(self, value: any):
        """
        Returns True if the `value` is an int, float or numeric string.
        """
        val_type = type(value)
        if val_type is str:
            if value.replace(".", "", 1).isdigit():
                return True
        elif val_type is int or val_type is float:
            return True
        return False

    def is_response_yes(
        self, msg: str, default_to_yes: bool = True
    ) -> bool:  # pragma: no cover
        """
        Asks for a Yes or No response. Yes returns True and No returns False.
        """
        choices = ["Yes", "No"] if default_to_yes else ["No", "Yes"]
        return pick(choices, msg)[0] == "Yes"

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
