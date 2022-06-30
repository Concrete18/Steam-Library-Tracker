from difflib import SequenceMatcher
import time, json, requests, re
import datetime as dt

# logging
from logging.handlers import RotatingFileHandler
import logging as lg


def keyboard_interrupt(func):
    """
    Catches all KeyboardInterrupt exceptions.
    Closes with a message and delayed program exit.
    """

    def wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            delay = 1
            print(f"\nClosing in {delay} second(s)")
            time.sleep(delay)
            exit()

    return wrapped


class Logger:

    # logger setup
    log_formatter = lg.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%m-%d-%Y %I:%M:%S %p"
    )
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)  # Log Level
    my_handler = RotatingFileHandler(
        "configs/tracker.log", maxBytes=5 * 1024 * 1024, backupCount=2
    )
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    def log_return(self, func):
        """
        Logs return of function when this decoratior is applied.
        """

        def wrapped(*args, **kwargs):
            value = func(*args, **kwargs)
            self.logger.info(value)
            return value

        return wrapped


class Helper(Logger):
    def request_url(self, url, headers=None, second_try=False):
        """
        Quick data request with check for success.
        """
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            if second_try:
                return False
            msg = "Connection Error: Internet can't be accessed"
            self.logger.warning(msg)
            time.sleep(5)
            self.request_url(url, headers, second_try=True)
            return False
        if response.status_code == requests.codes.ok:
            return response
        elif response.status_code == 500:
            msg = "Server Error: make sure your api key and steam id is valid."
            self.logger.warning(msg)
        elif response.status_code == 404:
            msg = f"Server Error: 404 Content moved or was. URL: {url}"
            self.logger.warning(msg)
        elif response.status_code == 429:
            msg = "Server Error: Too Many reqeuests made. Waiting to try again."
            self.logger.warning(msg)
            self.logger.warning(response)
            time.sleep(5)
            self.request_url(url, headers)
        else:
            msg = f"Unknown Error: {response.status_code}"
            self.logger.warning(msg)
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
        return round(minutes_played / 60, 1)

    @staticmethod
    def string_to_date(date: str):
        """
        Converts String `date` in MM/DD/YYYY format to datetime object.
        """
        return dt.datetime.strptime(date, "%m/%d/%Y")

    @staticmethod
    def days_since(past_date, current_date=None):
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
        # Allowed characters (0-9, A-Z, a-z, "-", ".", "_", "~")
        string = re.sub(r"[^a-z0-9-._~]+", "", string.lower()).strip()
        while "--" in string:
            string = string.replace("--", "-")
        return string

    @staticmethod
    def convert_time_passed(minutes_played):
        """
        Using `minutes_played`, outputs a nicely formatted time played and an int for hours played.

        Returns time_played and hours_played
        """
        time_played = f"{round(minutes_played, 1)} Minute(s)"
        hours_played = minutes_played / 60
        if round(hours_played) >= 24:
            days = round(hours_played / 24, 1)
            time_played = f"{days} Day(s)"
        elif minutes_played >= 60:
            hours = round(hours_played, 1)
            time_played = f"{hours} Hour(s)"
        return time_played

    @staticmethod
    def unicode_remover(string) -> str:
        """
        Removes unicode from `string`.
        """
        if type(string) != str:
            return string
        replace_dict = {
            "\u2122": "",  # Trademarked sign
            "\u00ae": "",  # REGISTERED SIGN
            "\u00ae": "",  # REGISTERED SIGN
            "\u00e5": "a",  # a
            "\u00f6": "o",  # LATIN SMALL LETTER O WITH DIAERESIS
            "\u00e9": "e",  # LATIN SMALL LETTER E WITH ACUTE
            "\u2013": "-",  # EN DASH
            "&amp": "&",  # &
        }
        for unicode in replace_dict.keys():
            if unicode in string:
                for unicode, sub in replace_dict.items():
                    string = string.replace(unicode, sub)
                break
        conv_string = string.encode("ascii", "ignore").decode()
        return conv_string.strip()

    def ask_for_integer(
        self, msg=None, num_range=False, allow_blank=False
    ) -> int or bool:
        """
        Asks for a integer until an integer is given.
        """
        if msg is None:
            msg = "Type a Number: "
        num = input(msg)
        if allow_blank and num == "":
            return ""
        if num_range:
            min = num_range[0]
            max = num_range[1]
            while True:
                if num.isdigit():
                    if min <= int(num) <= max:
                        break
                num = input(msg)
                if allow_blank and num == "":
                    return ""
        else:
            while not num.isdigit():
                num = input(msg)
                if allow_blank and num == "":
                    return ""
        return int(num)

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
            match_perc = round(max_similarity, 2)
            print(f"\nTarget: {target_str}\nMatch: {match}\nMatch Perc: {match_perc}")
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
                raise "Data did not save error"


if __name__ == "__main__":
    App = Helper()
    # response = App.request_url("https://store.steampowered.com/app/752564654590/")
    # print(response.url)
    # print(App.unicode_remover("Half-Life 2: Lost Coast"))
