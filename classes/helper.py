from difflib import SequenceMatcher
import time, json, requests
import datetime as dt


class Helper:
    @staticmethod
    def request_url(url, headers=None):
        """
        Quick data request with check for success.
        """
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            input("Connection Error: Internet can't be accessed")
            exit()
        if response.status_code == requests.codes.ok:
            return response
        elif response.status_code == 500:
            input("Server Error: make sure your api key and steam id is valid.")
            exit()
        else:
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

    def request_retryer():
        pass

    @staticmethod
    def unicode_remover(string) -> str:
        """
        ph
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

    def string_matcher(self, target_str, string_list, max_similarity=0.8, debug=False):
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
