from difflib import SequenceMatcher
from pathlib import Path
import time, json, requests, re
import datetime as dt
import pandas as pd


# logging import if helper.py is main
if __name__ != "__main__":
    from classes.logger import Logger
else:
    from logger import Logger


def keyboard_interrupt(func):
    """
    Catches all KeyboardInterrupt exceptions.
    Closes with a message and delayed program exit.
    """

    def wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            delay = 0.1
            print(f"\nClosing in {delay} second(s)")
            time.sleep(delay)
            exit()

    return wrapped


def benchmark(func):
    """
    Prints `func` name and a benchmark for runtime.
    """

    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        value = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(f"{func.__name__} Completion Time: {elapsed:.2f}")
        return value

    return wrapped


def get_steam_key_and_id():
    """
    Gets the steam key and steam id from the config file.
    """
    config = Path("configs/config.json")
    with open(config) as file:
        data = json.load(file)
    steam_key = data["steam_data"]["api_key"]
    steam_id = str(data["steam_data"]["steam_id"])
    return steam_key, steam_id


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
        except requests.exceptions.RequestException:
            return False

    def request_url(self, url, params=None, headers=None, second_try=False):
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if second_try:
                return False

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
                url, params=params, headers=headers, second_try=True
            )

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
    def hours_played(minutes_played):
        """
        Converts `minutes_played` to a hours played in decimal form.
        """
        hours_played = round(minutes_played / 60, 1)
        if hours_played == 0.0:
            return None
        return round(minutes_played / 60, 1)

    @staticmethod
    def string_to_date(date: str):
        """
        Converts String `date` in MM/DD/YYYY format to datetime object.
        """
        return dt.datetime.strptime(date, "%m/%d/%Y")

    @staticmethod
    def get_year(date_string):
        """
        Gets the year from `date_string`.
        """
        year = re.search(r"[0-9]{4}", date_string)
        if year:
            return year.group(0)
        else:
            return "Invalid Date"

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
    def url_sanitize(string, space_replace="-"):
        """
        Removes all illegal URL characters from the given `string`.

        Turns spaces into dashes if `space_to_dash` is true.
        """
        string = string.replace(" ", space_replace)
        # Allowed characters (0-9, A-Z, a-z, "-", "_", "~")
        string = re.sub(r"[^a-z0-9-_~]+", "", string.lower()).strip()
        while "--" in string:
            string = string.replace("--", "-")
        return string

    @staticmethod
    def convert_time_passed(min=0, hr=0, day=0, wk=0, mnth=0, yr=0):
        """
        Outputs a string for when the time passed.
        Takes minutes:`min`, hours:`hr`, days:`day`, weeks:`wk`
        months:`mnth` and years:`yr`.

        Return format examples:

        1.0 Minute(s)

        2.3 Hour(s)

        4.5 Day(s)

        6.7 Week(s)

        8.9 Month(s)

        2.1 Years(s)
        """
        # converts all into hours
        hours_in_day = 24
        hours_in_week = 168
        hours_in_month = 730
        hours_in_year = 8760
        hours = (
            (min / 60)
            + hr
            + (day * hours_in_day)
            + (wk * hours_in_week)
            + (mnth * hours_in_month)
            + (yr * hours_in_year)
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
    def create_and_sentence(str_list: [str]) -> str:
        """
        Converts a list of strings into a comma seperated string of words
        with "and" instead of a comma between the last two entries.
        """
        str_list_length = len(str_list)
        if str_list_length == 0:
            result = ""
        elif str_list_length == 1:
            result = str_list[0]
        else:
            result = ", ".join(str_list[:-1])
            result += " and " + str_list[-1]
        return result

    def lev_distance(self, word1: str, word2: str, lower=True) -> int:
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

    def sim_matcher(self, target_str, string_list, max_similarity=0.8, debug=False):
        """
        Finds a match for target_str in string_list using sequence matching.
        """
        match = None
        for string in string_list:
            if string.lower() == target_str.lower():
                return string
            match_perc = SequenceMatcher(
                None, target_str.lower(), string.lower()
            ).ratio()
            if match_perc > max_similarity:
                max_similarity = match_perc
                match = string
        if debug:
            print(
                f"\nTarget: {target_str}\nMatch: {match}\nMatch Perc: {max_similarity:.2f}"
            )
        return match

    def lev_dist_matcher(
        self,
        target_str: str,
        string_list: list,
        max_distance=None,
        limit: int = 5,
        debug=False,
    ):
        """
        Finds a match for target_str in string_list using sequence matching.
        """
        if max_distance == None:
            max_distance = round(len(target_str) * 0.5)
            # max_distance = float("inf")
        starting_max = max_distance
        matches = {}
        match = None
        for string in string_list:
            distance = self.lev_distance(target_str, string)
            if distance < max_distance:
                max_distance = distance
                match = string
                matches[string] = distance
        if debug:
            print(f"\nTarget: {target_str}\nMatch: {match}")
            print(f"Distance: {max_distance}\nStarting Max:{starting_max}")
        sorted_keys = sorted(matches, key=matches.get)
        if len(sorted_keys) > limit:
            sorted_keys = sorted_keys[0:limit]
        return sorted_keys

    def any_is_num(self, value):
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

    def save_json_output(self, new_data, filename):
        """
        Saves data into json format with the given filename.
        """
        json_object = json.dumps(new_data, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
        with open(filename) as file:
            last_check_data = json.load(file)
            if new_data != last_check_data:
                raise PermissionError("Data did not save error")

    def update_last_run(self, data, name):
        """
        Updates json by `name` with the current date.
        """
        data["last_runs"][name] = time.time()
        self.save_json_output(data, self.config)

    def recently_executed(self, data, name, n_days):
        """
        Check if a specific task named `name` was executed within the `n_days`.
        """
        last_runs = data["last_runs"]
        if name in last_runs.keys():
            last_run = last_runs[name]
            sec_since = time.time() - last_run
            check_freq_seconds = n_days * 24 * 60 * 60
            print(check_freq_seconds / 24 / 60 / 60)
            if sec_since < check_freq_seconds:
                return True
        return False

    def create_dataframe(self, table):
        """
        Creates a dataframe from a `table` found using requests and
        BeautifulSoup.
        """
        # find all headers
        headers = []
        for i in table.find_all("th"):
            title = i.text
            headers.append(title)
        # creates and fills dataframe
        df = pd.DataFrame(columns=headers)
        for j in table.find_all("tr")[1:]:
            row_data = j.find_all("td")
            row = [i.text for i in row_data]
            length = len(df)
            df.loc[length] = row
        return df


if __name__ == "__main__":
    App = Utils()
