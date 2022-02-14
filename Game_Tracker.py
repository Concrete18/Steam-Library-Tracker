import requests, random, time, json, os, re, sys, hashlib, webbrowser, subprocess
from howlongtobeatpy import HowLongToBeat
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import datetime as dt
# classes
from classes.indexer import Indexer
from classes.logger import Logger
from classes.scrape import Scraper
from classes.helper import Helper


class Tracker(Logger, Helper):


    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # config init
    config = Path('configs\config.json')
    with open(config) as file:
        data = json.load(file)

    steam_id = str(data['settings']['steam_id'])
    excel_filename = data['settings']['excel_filename']
    playstation_data_link = data['settings']['playstation_data_link']
    last_run = data['settings']['last_run']
    ignore_list = [string.lower() for string in data['ignore_list']]
    # Indexer init
    excel = Indexer(
        excel_filename=excel_filename,
        workbook_name='Games',
        column_name='Game Name',
        script_dir=script_dir
    )
    # current date and time setup
    cur_date = dt.datetime.now()
    excel_date = f'=DATE({cur_date.year}, {cur_date.month}, {cur_date.day})+TIME({cur_date.hour},{cur_date.minute},0)'
    # api call logger
    invalid_months = []


    def get_api_key(self):
        '''
        Checks for an api_key.txt so it can retrieve the key. If it does not exists,
        it will ask for an API key so it can create an api_key.txt file.
        '''
        # TODO use proper method for getting an api key
        api_path = 'configs/api_key.txt'
        if os.path.isfile(api_path):
            with open(api_path) as f:
                return f.read()
        else:
            api_key = ''
            with open(os.path.join(self.script_dir, api_path), 'w') as f:
                while len(api_key) != 32:
                    api_key = input('Enter your Steam API Key.\n:')
                f.write(api_key)
            return api_key

    @staticmethod
    def request_url(url, headers=None):
        '''
        Quick data request with check for success.
        '''
        response = requests.get(url, headers)
        if response == None:
            return False
        elif response.status_code == requests.codes.ok:
            return response
        else:
            return False

    def get_steam_id(self, vanity_url):
        '''
        Gets a users Steam ID via their `vanity_url`.
        '''
        base_url = r'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/'
        url = rf'{base_url}?key={self.get_api_key()}&vanityurl={vanity_url}'
        response = self.request_url(url)
        if response:
            data = response.json()
            steam_id = data['response']['steamid']
            return steam_id
        else:
            return False

    @staticmethod
    def hours_played(playtime_forever):
        '''
        Converts minutes played to a hours played in decimal form.
        '''
        return round(playtime_forever/60, 4)

    def get_time_to_beat(self, game_name, delay=2):
        '''
        Uses howlongtobeatpy to get the time to beat for entered game.
        '''
        if delay > 0:
            time.sleep(delay)
        self.api_sleeper('time_to_beat')
        results = HowLongToBeat().search(game_name)
        if results is not None and len(results) > 0:
            best_element = max(results, key=lambda element: element.similarity)
            time_to_beat = float(str(best_element.gameplay_main).replace('½','.5'))
            time_to_beat_unit = best_element.gameplay_main_unit
            if time_to_beat_unit == None:
                return 'No Data'
            elif time_to_beat_unit != 'Hours':
                return round(time_to_beat/60, 1)  # converts minutes to hours
            else:
                return time_to_beat
        else:
            return 'Not Found'

    def get_metacritic_score(self, game_name, platform):
        '''
        Uses requests to get the metacritic review score for the entered game.
        '''
        if platform == 'PS4':
            platform = 'playstation-4'
        elif platform == 'PS5':
            platform = 'playstation-5'
        elif platform in ['Steam', 'Uplay', 'Origin', 'MS Store']:
            platform = 'pc'
        replace_dict = {
            ':':'',
            "'":'',
            '&':'',
            ',':'',
            '?':'',
            '™':'',
            '_':'-',
            ' ':'-'
        }
        for string, replace in replace_dict.items():
            game_name = game_name.replace(string, replace)
        url = f'https://www.metacritic.com/game/{platform.lower()}/{game_name.lower()}'
        user_agent = {'User-agent': 'Mozilla/5.0'}
        self.api_sleeper('metacritic')
        review_score = ''
        response = self.request_url(url, headers=user_agent)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            review_score = soup.find(itemprop="ratingValue")
            if review_score != None:
                review_score = int(review_score.text)
            else:
                review_score = 'No Score'
            return review_score
        else:
            review_score = 'Page Error'
        return review_score

    def get_app_id(self, game, app_list={}):
        '''
        Checks the Steam App list for a game and returns its app id if it exists as entered.
        '''
        # sets up app_list if it does not exist
        if app_list == {}:
            url = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/?l=english'
            response = self.request_url(url)
            if not response:
                return None
            app_list = response.json()['applist']['apps']
        # searches for game
        for item in app_list:
            if item["name"] == game:
                return item['appid']
        return None
    
    def get_year(self, date):
        '''
        Takes the given `date` and changes it to this format, "Sep 14, 2016".
        '''
        year = re.search(r'[0-9]{4}', date)
        if year:
            return year.group(0)
        else:
            return 'Invalid Date'

    def get_game_info(self, app_id, debug=False):
        '''
        Gets game info with steam api using a `app_id`.
        '''

        def get_json_desc(data):
            return [item['description'] for item in data]

        url = f'https://store.steampowered.com/api/appdetails?appids={app_id}&l=english'
        self.api_sleeper('steam_app_details')
        response = self.request_url(url)
        if not response:
            return None
        else:
        # TODO make it retry
            info_dict = {}
            dict = response.json()
            if debug:
                print(dict)
                exit()
            if 'data' in dict[str(app_id)].keys():
                keys = dict[str(app_id)]['data'].keys()
                info_dict['name'] = dict[str(app_id)]['data']['name']
                # get developer
                if 'developers' in keys:
                    info_dict['developers'] = ', '.join(dict[str(app_id)]['data']['developers'])
                else:
                    info_dict['developers'] = None
                # get publishers
                if 'publishers' in keys:
                    info_dict['publishers'] = ', '.join(dict[str(app_id)]['data']['publishers'])
                else:
                    info_dict['publishers'] = None
                #  get genre
                if 'genres' in keys:
                    info_dict['genre'] = ', '.join(get_json_desc(dict[str(app_id)]['data']['genres']))
                else:
                    info_dict['genre'] = None
                #  get metacritic
                if 'metacritic' in keys:
                    info_dict['metacritic'] = dict[str(app_id)]['data']['metacritic']['score']
                else:
                    info_dict['metacritic'] = None
                #  early access
                if 'early_access' in keys:
                    info_dict['early_access'] = dict[str(app_id)]['data']['early_access']
                # get release year
                if 'release_date' in keys:
                    release_date = dict[str(app_id)]['data']['release_date']['date']
                    release_date = self.get_year(release_date)
                    info_dict['release_date'] = release_date
                else:
                    info_dict['release_date'] = None
                # get price_info
                if 'price_overview' in keys:
                    price = dict[str(app_id)]['data']['price_overview']['final_formatted']
                    discount = dict[str(app_id)]['data']['price_overview']['discount_percent']
                    on_sale = dict[str(app_id)]['data']['price_overview']['discount_percent'] > 0
                    info_dict['price'] = price
                    info_dict['discount'] = discount
                    info_dict['on_sale'] = on_sale
                else:
                    info_dict['price'] = None
                    info_dict['discount'] = None
                    info_dict['on_sale'] = None
                # get linux compat
                if 'platforms' in keys:
                    info_dict['linux_compat'] = dict[str(app_id)]['data']['platforms']['linux']
                else:
                    info_dict['linux_compat'] = False
                if 'categories' in keys:
                    info_dict['categories'] = ', '.join(get_json_desc(dict[str(app_id)]['data']['categories']))
                else:
                    info_dict['categories'] = None
                # drm info
                if 'drm_notice' in keys:
                    info_dict['drm_notice'] = dict[str(app_id)]['data']['drm_notice']
                else:
                    info_dict['drm_notice'] = None
                # external account
                if 'ext_user_account_notice' in keys:
                    info_dict['ext_user_account_notice']  = dict[str(app_id)]['data']['ext_user_account_notice']
                else:
                    info_dict['ext_user_account_notice'] = None
                # runs unicode remover on all values
                final_dict = {k: self.unicode_remover(v) for k, v in info_dict.items()}
                return final_dict
        return False

    @staticmethod
    def string_url_convert(string) -> str:
        '''
        Converts given `string` into a url ready string and returns it.
        '''
        return re.sub(r'\W+', '', string.replace(' ', '_')).lower()

    def get_store_link(self, game_name, app_id):
        '''
        Generates a likely link to the games store page using `game_name` and `app_id`.'''
        if not app_id or app_id == 'None':
            return ''
        return f'https://store.steampowered.com/app/{app_id}/{self.string_url_convert(game_name)}/'

    def get_linux_compat(self, game):
        '''
        Get games compatability score from Protondb for running on proton.
        '''
        # TODO gain linux compat info javascript likely causing issues
        app_id = self.get_app_id(game)
        url = f'https://www.protondb.com/app/{app_id}'
        self.api_sleeper('proton')
        response = self.request_url(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            if 'You need to enable JavaScript to run this app.' in soup:
                print('You need to enable JavaScript to run this app.')
                return False
            score = soup.find(class_="Summary__ExpandingSpan-sc-18cac2b-1 bRWxzY")
            return score
        else:
            return 'Unknown'
    
    def get_proton_rating(self, game):
        '''
        WIP
        Gets the proton rating for the given `game`.
        '''
        app_id = self.get_app_id(game)
        if app_id is None:
            return 'Not Found'
        if not hasattr(self, 'scraper') and app_id is not None:
            self.scraper = Scraper()
            self.scraper.get_web_driver(headless=True)
        self.api_sleeper('proton')
        url = f'https://www.protondb.com/app/{app_id}'
        class_name = 'Summary__ExpandingSpan-sc-18cac2b-1 bRWxzY'
        self.scraper.driver.get(url)
        try:
            items = self.scraper.driver.find_element_by_class_name(class_name)
        except self.scraper.driver.common.exceptions.NoSuchElementException:
            print('No element found.')
            return
        print(items.text)
        self.scraper.driver.quit()
        return items

    def requests_loop(self, skip_filled=1, check_status=0):
        '''
        Loops through games in row_index and gets missing data for time to beat and Metacritic score.
        '''
        # creates checklist
        check_list = []
        to_check = [
            genre_column_name := 'Genre',
            publishers_column_name := 'Publishers',
            developers_column_name := 'Developers',
            metacritic_column_name := 'Metacritic Score',
            time_to_beat_column_name := 'Time To Beat in Hours',
            release_year_column_name := 'Release Year',
            # steam_deck_viable_column_name := 'Steam Deck Viable',
        ]
        for game in self.excel.row_index:
            play_status = self.excel.get_cell(game, 'Play Status')
            if check_status:
                if play_status not in ['Unplayed', 'Playing', 'Played', 'Finished', 'Quit']:
                    continue
            if skip_filled:
                for column in to_check:
                    cell = self.excel.get_cell(game, column)
                    if cell == None and game not in check_list:
                        check_list.append(game)
                        continue
            else:
                check_list.append(game)
        # checks if data should be updated
        missing_data = len(check_list)
        auto_update = 50
        if 0 < missing_data <= auto_update:
            print(f'\nMissing data is within auto update threshold of {auto_update}.')
        elif missing_data > auto_update:
            msg = f'\nSome data is missing for {missing_data} games.\nDo you want to retrieve it?\n:'
            if not input(msg) in ['yes', 'y']:
                return
        else:
            return
        try:
            # updates missing data
            print('\nStarting Time To Beat, Metacritic Score and other steam data check.')
            save_interval = 15
            running_interval = save_interval
            for game_name in tqdm(iterable=check_list, ascii=True, unit='games', dynamic_ncols=True):
                # How long to beat check
                if not self.excel.get_cell(game_name, time_to_beat_column_name):
                    time_to_beat = self.get_time_to_beat(game_name)
                    if time_to_beat != None:
                        self.excel.update_cell(game_name, time_to_beat_column_name, time_to_beat)
                # metacritic score check
                if not self.excel.get_cell(game_name, metacritic_column_name):
                    platform = self.excel.get_cell(game_name, 'Platform')
                    metacritic_score = self.get_metacritic_score(game_name, platform)
                    if metacritic_score != None:
                        self.excel.update_cell(game_name, metacritic_column_name, metacritic_score)
                # gets steam info if an app id exists for the entry and the platform is Steam
                app_id = self.excel.get_cell(game_name, 'App ID')
                if not app_id:
                    app_id = self.get_app_id(game_name)
                steam_info = self.get_game_info(app_id)
                platform = self.excel.get_cell(game_name, 'Platform')
                if steam_info and platform == 'Steam':
                    # genre
                    if steam_info['genre']:
                        self.excel.update_cell(game_name, genre_column_name, steam_info['genre'])
                    else:
                        self.excel.update_cell(game_name, genre_column_name, 'No Genre')
                    # release year
                    if steam_info['release_date']:
                        self.excel.update_cell(game_name, release_year_column_name, steam_info['release_date'])
                    else:
                        self.excel.update_cell(game_name, release_year_column_name, 'No Release Year')
                    # developer
                    if steam_info['developers']:
                        self.excel.update_cell(game_name, developers_column_name, steam_info['developers'])
                    else:
                        self.excel.update_cell(game_name, developers_column_name, 'No Developer')
                    # publishers
                    if steam_info['publishers']:
                        self.excel.update_cell(game_name, publishers_column_name, steam_info['publishers'])
                    else:
                        self.excel.update_cell(game_name, publishers_column_name, 'No Publisher')
                    # metacritic
                    if steam_info['metacritic']:
                            self.excel.update_cell(game_name, metacritic_column_name, steam_info['metacritic'])
                    else:
                        if not self.excel.get_cell(game_name, metacritic_column_name):
                            self.excel.update_cell(game_name, metacritic_column_name, 'No Score')
                    # linux compatability
                    # if steam_info['linux_compat']:
                    #     linux_compat = self.excel.get_cell(game_name, steam_deck_viable_column_name)
                    #     if linux_compat == 'None':
                    #         self.excel.update_cell(game_name, steam_deck_viable_column_name, 'Native')
                else:
                    self.excel.update_cell(game_name, release_year_column_name, 'No Release Year')
                    self.excel.update_cell(game_name, genre_column_name, 'No Data')
                    self.excel.update_cell(game_name, developers_column_name, 'No Data')
                    self.excel.update_cell(game_name, publishers_column_name, 'No Data')
                running_interval -= 1
                if running_interval == 0:
                    running_interval = save_interval
                    self.excel.save_excel_sheet(show_print=False)
        except KeyboardInterrupt:
            print('\nCancelled')
        finally:
            self.excel.save_excel_sheet()

    def refresh_steam_games(self, steam_id):
        '''
        Gets games owned by the entered Steam ID amd runs excel update/add functions.
        '''
        # asks for a steam id if the given one is invalid
        while len(steam_id) != 17:
            steam_id = input('\nInvalid Steam ID (It must be 17 numbers.)\nTry Again.\n:')
        print('\nStarting Steam Library Tracking')
        root_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
        url_var = f'?key={self.get_api_key()}&steamid={steam_id}?l=english'
        combinded_url = f'{root_url}{url_var}&include_played_free_games=0&format=json&include_appinfo=1'
        try:
            self.api_sleeper('steam_owned_games')
            data = requests.get(combinded_url)
        except requests.exceptions.ConnectionError:
            print("Connection Error: Internet can't be accessed")
            return False
        if data.status_code == requests.codes.ok:
            # checks for games that changed names
            self.removed_from_steam = [str(game) for game in self.excel.row_index.keys() if self.excel.get_cell(game, 'Platform') == 'Steam']
            self.total_games_updated = 0 
            self.total_games_added = 0
            self.added_games = []
            for game in data.json()['response']['games']:
                game_name = game['name']
                if self.should_ignore(game_name):
                    continue
                # TODO include linux playtime
                playtime_forever = game['playtime_forever']
                game_appid = game['appid']
                # Demo
                if re.search(r'\bdemo\b', game['name'].lower()) or re.search(r'\btest\b', game['name'].lower()):
                    play_status = 'Demo'  # sets play_status to Demo if demo or test appears in the name
                # Unplayed
                elif playtime_forever <= 20:
                    play_status = 'Unplayed'  # sets play_status to Unplayed if playtime_forever is 0-15
                # Playing
                elif game['playtime_windows_forever'] > 60:
                    play_status = 'Playing'  # sets play_status to Played if playtime_forever is greater then 1 hour
                # Unset
                else:
                    play_status = 'Unset'  # sets play_status to Unset if none of the above applies
                # Updates game if it is in the index or adds if it is not.
                if game_name in self.excel.row_index.keys():
                    if game_name in self.removed_from_steam:
                        self.removed_from_steam.remove(game_name)
                    self.update_game(game_name, playtime_forever, play_status)
                else:
                    self.add_game(game_name, playtime_forever, game_appid, play_status)
            if len(self.removed_from_steam) > 0:
                print(f'\nThe following Steam games are unaccounted for:\n{" ,".join(self.removed_from_steam)}')
                for item in self.removed_from_steam:
                    status = self.excel.get_cell(item, 'Play Status')
                    if 'Removed' not in status:
                        self.excel.update_cell(item, 'Play Status', f'Removed | {status}')
            return True
        if data.status_code == 500:
            print('Server Error: make sure your api key and steam id is valid.')
        else:
            print('\nFailed to connect to Steam API:\nCheck your internet.')
            print(data.status_code)
            return False

    @staticmethod
    def hash_file(file_path):
        '''
        Creates a hash for the given `file_path`.
        '''
        BUF_SIZE = 65536
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()
    
    def check_for_changes(self, json_path):
        '''
        Checks for changes to the json file.
        '''
        with open(self.config) as file:
            data = json.load(file)
        previous_hash = data['settings']['playstation_hash']
        new_hash = self.hash_file(json_path)
        if new_hash == previous_hash:
            print('\nNo PlayStation games were added or updated.')
            return False
        else:
            data['settings']['playstation_hash'] = new_hash
            self.save_json_output(data, self.config)
        return True

    def should_ignore(self, name):
        '''
        Returns True if any keywords are found or it is in the `ignore_list`.
        '''
        # keyword check
        keyword_ignore_list = [
            'demo',
            'beta',
            'Youtube'
            'PreOrder',
            'Pre-Order',
            'Soundtrack',
            'Closed Test',
            'Public Test',
            'Test Server',
            'Bonus Content',
            'Trial Edition',
        ]
        name = name.lower()
        for string in keyword_ignore_list:
            if re.search(rf'\b{string.lower()}\b', name):
                return True
        # ignore list
        if name in self.ignore_list:
            return True
        return False

    @staticmethod
    def unicode_fix(string):
        '''
        Basic unicode cleaner.
        '''
        inicode_dict = {
            'â€':"'",
            '®':'',
            '™':'',
            'â„¢':'',
            'Â':'',
            'Ã›':'U'
        }
        for char, replace in inicode_dict.items():
            string = string.replace(char, replace)
        return string.strip()

    def add_playstation_games(self, games):
        '''
        Adds playstation games to excel using the given `games` variable.
        '''
        added_games = []
        for game in tqdm(iterable=games, ascii=True, unit='games', dynamic_ncols=True):
            game_name = self.unicode_fix(game['name'])
            # skip if it should be ignored or was added this session
            if self.should_ignore(game_name) or game_name in added_games:
                continue
            # skip if it already exist
            if game_name in self.excel.row_index.keys() or f'{game_name} - Console' in self.excel.row_index.keys():
                continue
            # TODO skip if the game exists with a playstation version already

            # adds the game
            added_games.append(game_name)
            self.add_game(game_name=game_name, play_status='Unplayed', platform=game['platform'])
        total_games_added = len(added_games)
        print(f'Added {total_games_added} PS4/PS5 Games.')
        if total_games_added > 0:
            self.excel.save_excel_sheet()

    def steam_deck_check(self, steam_id=76561197982626192, hour_freq=6, always_run=False):
        '''
        Checks steam_deck.txt and updates steam deck status with the info.
        '''
        seconds_since_last_run = time.time() - self.last_run
        hours_since_last_run = round(seconds_since_last_run*0.000277778)
        if not hours_since_last_run < hour_freq or not always_run:
            print(f'Skipping Steam Deck Check due to last run being {hours_since_last_run} hours ago.')
            return
        print('\nStarting Steam Deck Compatability Check')
        url = f'https://checkmydeck.herokuapp.com/users/{steam_id}/library'
        user_agent = {'User-agent': 'Mozilla/5.0'}
        response = self.request_url(url, headers=user_agent)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            percent = soup.find(id='deckCompatChartPercent').text.split('%')[0]+'%'
            print(f'{percent} of games are playable.')
            table1 = soup.find('table', id='deckCompatReportTable')
            for entry in table1.find_all('tr')[1:]:
                row_data = entry.find_all('td')
                app_id, game_name, status = [i.text for i in row_data]
                if self.excel.update_cell(game_name, 'Steam Deck Status', status):
                    print(f'{game_name} was updated to {status.title()}')
            self.excel.save_excel_sheet(show_print=False)
        else:
            print('Failed to update Steam Deck Data')

    def check_steam_deck_data_file(self):
        with open('configs\steam_deck.txt') as f:
            lines = f.read().splitlines()
        for line in lines:
            app_id, game_name, status = line.split('\t')
            if self.excel.update_cell(game_name, 'Steam Deck Status', status):
                print('failed on', game_name, status)
        self.excel.save_excel_sheet(show_print=True)

    def check_playstation_json(self):
        '''
        Checks `playstation_games.json` to find out if it is newly updated so it can add the new games to the sheet.
        '''
        # checks if json exists
        json_path = Path('configs\playstation_games.json')
        if not json_path.exists:
            print('PlayStation Json does not exist.')
            webbrowser.open_new(self.playstation_data_link)
            return None
        # create hash file if it does not exist
        if not json_path.exists:
            json_path.touch()
        if not self.check_for_changes(json_path):
            return None
        with open(json_path) as file:
            data = json.load(file)
        print('\nChecking for new games for PS4 or PS5.')
        games = data['data']['purchasedTitlesRetrieve']['games']
        self.add_playstation_games(games)

    def update_game(self, game_name, playtime_forever, play_status):
        '''
        Updates the games playtime(if changed) and play status(if unset).
        '''
        previous_hours_played = self.excel.get_cell(game_name, 'Hours Played')
        current_hours_played = self.hours_played(playtime_forever)
        current_platform = self.excel.get_cell(game_name, 'Platform')
        if current_platform != 'Steam':  # prevents updating games that are owned on Steam and a console.
            return
        elif previous_hours_played == None or previous_hours_played == 'None':
            previous_hours_played = 0
        else:
            previous_hours_played = float(previous_hours_played)
        if current_hours_played > previous_hours_played:
            self.excel.update_cell(game_name, 'Hours Played', self.hours_played(playtime_forever))
            self.excel.update_cell(game_name, 'Date Updated', self.excel_date)
            self.total_games_updated += 1
            if play_status == 'unset':
                self.excel.update_cell(game_name, 'Play Status', 'Played')
            unit = 'hours'
            added_time = current_hours_played - previous_hours_played
            if added_time < 1:
                added_time = added_time * 60
                unit = 'minutes'
            added_time = round(added_time, 1)
            total_hours = round(current_hours_played, 1)
            total_days = round(total_hours/24, 1)
            days_string = ''
            if total_days >= 1:
                days_string = f' | {total_days} days'
            print(f'\n > {game_name} updated.\n   Added {added_time} {unit}\n   Total Playtime: {total_hours} hours{days_string}.')
        self.excel.format_cells(game_name)

    def add_game(self, game_name=None, playtime_forever='', game_appid='', play_status='', platform='Steam'):
        '''
        Appends new game to excel sheet into the correct columns using self.column_i.
        Any columns that are inputted manually are left blank.
        '''
        save = 0
        if game_name == None:
            save = 1
            game_name = input('\nDo you want to add a new game?\nIf Yes type the game name.\n:')
            if game_name != '':
                if game_name.lower() in ['yes', 'y']:
                    game_name = input('\nWhat is the name of the game?\n:')
                platform = input('\nWhat is the platform is this on?\n:')
                platform_names = {
                    'playstation 5':'PS5',
                    'ps5':'PS5',
                    'playstation 4':'PS4',
                    'ps4':'PS4',
                    'sw':'Switch',
                    'uplay':'Uplay',
                    'gog':'GOG',
                    'ms store':'MS Store',
                    'ms':'MS Store',
                    'microsoft':'MS Store',
                }
                if platform.lower() in platform_names:
                    platform = platform_names[platform.lower()]
                hours_played = int(input('\nHow many hours have you played it?\n:') or 0)
                print('\nWhat Play Status should it have?')
                play_status = self.play_status_picker() or 'Unset'
                print('\nAdded Game:')
                print(f'{game_name}\nPlatform: {platform}\nHours Played: {hours_played}\nPlay Status: {play_status}')
            else:
                return
        else:
            if playtime_forever:
                hours_played = self.hours_played(playtime_forever)
            else:
                hours_played = ''
        # store link setup
        store_link_hyperlink = ''
        store_link = self.get_store_link(game_name, game_appid)
        if store_link:
            store_link_hyperlink = f'=HYPERLINK("{store_link}","Store Link")'
        # sets vr support value
        if re.search(r'\bVR\b', game_name):
            vr_support = 'Yes'
        elif platform in ['PS5', 'PS4', 'Switch']:
            vr_support = 'No'
        else:
            vr_support = ''
        # TODO add more to column info
        column_info = {
            'My Rating': '',
            'Game Name': game_name,
            'Play Status': play_status,
            'Platform': platform,
            'VR Support': vr_support,
            'Time To Beat in Hours': self.get_time_to_beat(game_name),
            'Metacritic Score': self.get_metacritic_score(game_name, 'Steam'),
            'Rating Comparison':'',
            'Probable Completion':'',
            'Hours Played': hours_played,
            'App ID': game_appid,
            'Store Link': store_link_hyperlink,
            'Date Updated': self.excel_date,
            'Date Added': self.excel_date
            }
        self.excel.add_new_cell(column_info)
        self.added_games.append(game_name)
        self.total_games_added += 1
        # adds game to row_index
        self.excel.row_index[game_name] = self.excel.cur_workbook._current_row
        self.excel.format_cells(game_name)
        if save:
            print('saved')
            self.excel.save_excel_sheet()

    def output_completion_data(self):
        '''
        Shows total games added and updated games with info.
        '''
        if self.total_games_added > 0:
            print(f'\nGames Added: {self.total_games_added}')
            if len(self.added_games) > 0:
                print(', '.join(self.added_games))
        if self.total_games_updated > 0:
            print(f'\nGames Updated: {self.total_games_updated}')
        if len(self.invalid_months) > 0:
            print(self.invalid_months)
        if self.excel.changes_made:
            self.excel.save_excel_sheet()
        else:
            print('\nNo Steam games were added or updated.')
    
    @staticmethod
    def save_json_output(data, filename):
        '''
        Saves data into json format with the given filename.
        '''
        json_object = json.dumps(data, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)

    def play_status_picker(self):
        '''
        Shows a list of Play Status's to choose from.
        Respond with the playstatus or numerical postion of the status from the list.
        '''
        play_status_choices = {
            '1':'Played', '2':'Playing', '3':'Waiting', '4':'Finished',
            '5':'Quit', '6':'Unplayed', '7':'Ignore', '8':'Demo'
        }
        prompt = ', '.join(play_status_choices.values()) + '\n:'
        while True:
            response = input(prompt).lower()
            if len(response) == 1:
                return play_status_choices[response]
            elif response.title() in play_status_choices.values():
                return response
            elif response == '':
                return None
            else:
                print('\nInvalid Response')
                continue

    def pick_random_game(self):
        '''
        Allows you to pick a play_status to have a random game chosen from. It allows retrying.
        '''
        print('\nWhat play status do you want a random game picked from?\nPress Enter to skip.')
        play_status = self.play_status_picker()
        if play_status == None:
            return
        choice_list = []
        for game, index in self.excel.row_index.items():
            game_play_status = self.excel.get_cell(index, 'Play Status').lower()
            if game_play_status == play_status.lower():
                choice_list.append(game)
        # picks random game then removes it from the choice list so it wont show up again during this session
        picked_game = random.choice(choice_list)
        choice_list.pop(choice_list.index(picked_game))
        print(f'\nPicked game with {play_status} status:\n{picked_game}')
        # allows getting another random pick
        while not input('Press Enter to pick another and No for finish.\n:').lower() in ['no', 'n']:
            if len(choice_list) == 0:
                print(f'All games with {play_status} have already been picked.\n')
                return
            picked_game = random.choice(choice_list)
            choice_list.pop(choice_list.index(picked_game))
            print(f'\nPicked game with {play_status} status:\n{picked_game}')

    def get_favorite_games_sales(self):
        '''
        Gets sale information for games that are at a minimun rating or higher.
        Rating is set up using an input after running.
        '''
        # gets favorite games from excel file as a list of dicts
        favorite_games = []
        # sets minimum rating to and defaults to 8 if response is blank or invalid
        rating_limit = input('What is the minimum rating for this search? (1-10)\n') or '8'
        if rating_limit.isnumeric():
            rating_limit = int(rating_limit)
        else:
            print('Invalid response - Using 8 instead.')
            rating_limit = 8
        # starts check with progress bar
        print('\nStarting Game Sale Check\n')
        for game, index in tqdm(iterable=self.excel.row_index.items(), ascii=True, unit='games', dynamic_ncols=True):
            my_rating = self.excel.get_cell(game, 'My Rating')
            if my_rating == None:
                continue
            app_id = self.excel.get_cell(game, 'App ID')
            if my_rating >= rating_limit and app_id:
                game_dict = self.get_game_info(app_id)
                if not game_dict:
                    continue
                game_dict['my_rating'] = my_rating
                if 'on_sale' in game_dict.keys():
                    if game_dict['on_sale']:
                        favorite_games.append(game_dict)
        favorite_games = sorted(favorite_games, key = lambda i: i['discount'], reverse=True)
        print(f'\n{len(favorite_games)} Favorite Games with Current Deals in Descending Order:\n')
        # TODO replace with better code for output
        for game in favorite_games:
            print(f'{game["name"]} - {game["price"]}')
        # save into file
        self.save_json_output(favorite_games, 'configs/favorite_games.json')

    def view_favorite_games_sales(self):
        '''
        Allows viewing different formatted info on the games created during the last run of `get_favorite_games_sales`.
        '''
        df = pd.read_json('configs/favorite_games.json')
        print('Do you want to output as excel(1) or csv(2)?')
        output = input()
        if output == '1':
            output  = 'excel'
        elif output == '2':
            output = 'csv'
        else:
            return
        Path('outputs').mkdir(exist_ok=True)
        if output == 'excel':
            file_path = 'outputs/favorite_games_sales.xlsx'
            df.to_excel(file_path)
            os.startfile(file_path)
        elif output == 'csv':
            df.to_csv('outputs/favorite_games_sales.csv')
            folder = os.path.join(self.script_dir, 'outputs')
            subprocess.Popen(f'explorer "{folder}"')
        else:
            print('Invalid Resposne')
            return

    def arg_func(self):
        '''
        Checks if any arguments were given and runs commands.
        '''
        if len(sys.argv) == 1:
            return
        arg = sys.argv[1].lower()
        if arg == 'help':
            print('Help:\nrefresh- refreshes steam games\nrandom- allows getting random picks from games based on play status')
        elif arg == 'refresh':
            print('Running refresh')
            self.refresh_steam_games(self.steam_id)
        elif arg == 'random':
            self.pick_random_game()
        else:
            print('Invalid Argument Given.')
        input()
        exit()

    def update_last_run(self):
        '''
        Updates the last run time in seconds.
        '''
        self.data['settings']['last_run'] = time.time()
        self.save_json_output(self.data, self.config)

    def open_excel_input(self, other_option=False):
        '''
        Opens excel file if previous input is passed.
        '''
        if not other_option:
            input('\nPress Enter to open the excel sheet.\n')
        else:
            input('\nPress Enter to open the excel sheet.\n')
        os.startfile(self.excel.file_path)
    
    def pick_task(self):
        '''
        Allows picking a task to do next using a matching number.
        '''
        print('\nWhat do you want to do next?\n')
        choices = [
            'Pick Random Game',
            'Add Game',
            'Update the Playstation Data',
            'Check for and view Favorite Games Sales',
            'View Favorite Games Sales'
        ]
        for count, choice in enumerate(choices):
            print(f'{count+1}. {choice}')
        res = input('\nPress Enter without a number to open the excel sheet.\n')
        if res == '1':
            self.pick_random_game()
            self.open_excel_input()
        elif res == '2':
            self.add_game()
            self.open_excel_input()
        elif res == '3':
            subprocess.Popen(f'notepad "configs\playstation_games.json"')
            webbrowser.open(self.playstation_data_link)
            webbrowser.open(r'https://store.playstation.com/')
        elif res == '4':
            self.get_favorite_games_sales()
            self.open_excel_input()
        elif res == '5':
            self.view_favorite_games_sales()
            self.open_excel_input()

    def run(self):
        '''
        Main run function.
        '''
        self.arg_func()
        os.system('mode con cols=68 lines=40')
        print('Starting Game Tracker')
        # starts function run with CTRL Exit being possible without causing an error
        try:
            self.refresh_steam_games(self.steam_id)
            self.steam_deck_check()
            self.check_playstation_json()
            self.output_completion_data()
            self.requests_loop()
            self.update_last_run()
            self.pick_task()
            os.startfile(self.excel.file_path)
        except KeyboardInterrupt:
            print('\nClosing')


if __name__ == "__main__":    
    App = Tracker()
    # print(App.get_game_info(1145360, debug=True))
    # App.view_favorite_games_sales()
    # print(App.get_steam_id('Varnock'))
    # App.check_steam_deck_data()
    # exit()
    App.run()
