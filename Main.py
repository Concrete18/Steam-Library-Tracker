from requests.models import Response
from Game_Library_Tracker import Tracker
import datetime as dt
import time

Database = Tracker(steam_id=76561197982626192)


def Database_Update():
    overall_start = time.perf_counter()
    Database.Update_Steam_Games()
    overall_finish = time.perf_counter() # stop time for checking elaspsed runtime
    elapsed_time = round(overall_finish-overall_start, 2)
    if elapsed_time != 0:  # converts elapsed seconds into readable format
        converted_elapsed_time = str(dt.timedelta(seconds=elapsed_time))
    else:
        converted_elapsed_time = 'Instant'
    print(f'Update Complete: {converted_elapsed_time}\n')


def Main():
    print('What do you want to do next?')
    response = input('1. Update Play status\n2. Pick Random Game from a Play Status set.\n')
    if response == '1':
        Database.Set_Play_Status()
    elif response == '2':
        print('Not yet supported.')


if __name__ == "__main__":
    Database_Update()

    Main()

    Database.database.close()
