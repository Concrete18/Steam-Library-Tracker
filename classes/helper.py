import datetime as dt
import time

class Helper:


    def api_sleeper(self, api, sleep_length=.5, api_calls={}):
        '''
        Delays delays for a set period of time if the `api` was run too recently.
        Delay length is set by `sleep_length`.
        '''
        cur_datetime = dt.datetime.now()
        if api in api_calls.keys():
            if api_calls[api] + dt.timedelta(seconds=sleep_length) > cur_datetime:
                time.sleep(sleep_length)
        api_calls[api] = cur_datetime
