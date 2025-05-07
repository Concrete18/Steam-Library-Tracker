# standard library
import datetime as dt
from time import sleep


class ApiThrottler:
    api_calls = {}

    def __init__(self, default_wait: float = 1.0) -> None:
        self.default_wait = default_wait  # set default time to wait

    def wait_if(self, api_name: str, wait: int | float = None) -> bool:
        """
        Delays execution for a set period if the `api_name` was accessed too recently.
        Delay length is set by `sleep_time` in seconds.
        """
        # uses default wait
        if not wait:
            wait = self.default_wait

        cur_datetime = dt.datetime.today()
        delayed = False
        if api_name in self.api_calls:
            # checks if the last call was too recent
            run_limit = self.api_calls[api_name] + dt.timedelta(seconds=wait)
            if run_limit > cur_datetime:
                time_to_sleep = run_limit - cur_datetime
                sleep(time_to_sleep.total_seconds())
                delayed = True

        self.api_calls[api_name] = cur_datetime
        return delayed

    def display(self):
        """
        Displays current API call data stored.
        """
        print("API Calls:")
        if not self.api_calls:
            print("No API calls have run")
            return
        for api, last_run in self.api_calls.items():
            print(f"{api} - {last_run}")
