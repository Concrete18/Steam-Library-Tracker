from openpyxl.styles.borders import Side
import openpyxl
import requests, random, shutil, time, json, os, re
import datetime as dt
from howlongtobeatpy import HowLongToBeat


class Indexer:


    def column_index(self, workbook):
        '''
        Creates excel sheet index based on column names such as Anime name and Score.
        The starting_row var is the number of the row that the main column is on.
        '''
        column_index = {}
        for i in range(1, len(workbook['1'])+1):
            title = workbook.cell(row=1, column=i).value
            if title is not None:
                column_index[title] = i
        return column_index


    def row_index(self, workbook, column_name, column_letter):
        '''
        Creates excel sheet index based on anime names.
        The starting_col var is the number of the column that the main column is on.
        '''
        column_index = self.column_index(workbook, )
        row_index = {}
        for i in range(1, len(workbook[column_letter])):
            title = workbook.cell(row=i+1, column=column_index[column_name]).value
            if title is not None:
                row_index[title] = i+1
        return row_index


    def create_column_row_index(self, workbook=None, column_name=None, column_letter='B'):
        '''
        Creates the column and row index.
        '''
        column_index = self.column_index(workbook)
        row_index = self.row_index(workbook, column_name, column_letter)
        return column_index, row_index


    # TODO move excel stuff into this class


    def update_cell(self):
        '''
        ph
        '''
        pass


    def view_cell(self):
        '''
        ph
        '''
        pass


class Tracker:

    # config init
    with open('config.json') as file:
        data = json.load(file)
    steam_id = str(data['settings']['steam_id'])
    excel_filename = data['settings']['excel_filename']
    # var init
    file_path = os.path.join(os.getcwd(), excel_filename + '.xlsx')
    wb = openpyxl.load_workbook(file_path)
    games = wb['Games']
    excel = Indexer()
    column_index, row_index = excel.create_column_row_index(
        workbook=games,
        column_name='Game Name',
        column_letter='A')
    date_format = '%m/%d/%Y'


    @staticmethod
    def get_api_key():
        '''
        Checks for an api_key.txt so it can retrieve the key. If it does not exists,
        it will ask for an API key so it can create an api_key.txt file.
        '''
        if os.path.isfile('api_key.txt'):
            with open('api_key.txt') as f:
                return f.read()
        else:
            api_key = ''
            with open(os.path.join(os.getcwd(), 'api_key.txt'), 'w') as f:
                while len(api_key) != 32:
                    api_key = input('Enter your Steam API Key.\n')
                f.write(api_key)
            return api_key


    @staticmethod
    def playtime_conv(playtime_forever):
        '''
        Converts minutes to a written string of minutes(1) or hours(1.0).
        '''
        if playtime_forever <= 60:
            return f'{playtime_forever} minutes'
        else:
            return f'{round(playtime_forever/60, 1)} hours'


    def get_time_to_beat(self):
        '''
        ph
        '''
        skip_filled = 1
        time_to_beat_column_name = 'Time To Beat in Hours'
        try:
            for game_name in self.row_index:
                if skip_filled:
                    hltb = self.games.cell(row=self.row_index[game_name],
                        column=self.column_index[time_to_beat_column_name]).value
                    if hltb != None:
                        continue
                start = time.perf_counter()
                play_status = self.games.cell(row=self.row_index[game_name],
                    column=self.column_index['Play Status']).value
                if play_status in ['Unplayed', 'Playing', 'Played']:
                    results = HowLongToBeat().search(game_name)
                    if results is not None and len(results) > 0:
                        best_element = max(results, key=lambda element: element.similarity)
                        time_to_beat = str(best_element.gameplay_main).replace('½','.5')
                        time_to_beat_unit = best_element.gameplay_main_unit
                        if time_to_beat_unit == None:
                            continue
                        elif time_to_beat_unit != 'Hours':
                            time_to_beat = round(float(time_to_beat)/60, 1)  # converts minutes to hours
                        print(best_element.game_name, time_to_beat, time_to_beat_unit)
                        # TODO switch to hours only
                        self.games.cell(row=self.row_index[game_name],
                            column=self.column_index[time_to_beat_column_name]).value = time_to_beat
                end = time.perf_counter()
                print('Time to check', round(end-start, 2))
                if end-start < 2:
                    time.sleep(1)
        except KeyboardInterrupt:
            print('\nCancelled')
        finally:
            self.save_excel_sheet()


    def format_cells(self, game_name):
        '''
        Aligns specific columns to center and adds border to cells.
        '''
        # alignment setting
        alignment = openpyxl.styles.alignment.Alignment(
            horizontal='center', vertical='center', text_rotation=0, wrap_text=False, shrink_to_fit=True, indent=0)
        center_list = [
            'My Rating', 'Play Status', 'Platform', 'VR Support', 'Release', 'Minutes Played',
            'Converted Time Played', 'App ID', 'Last Updated', 'Date Added']
        for cell in center_list:
            self.games.cell(
                row=self.row_index[game_name], column=self.column_index[cell]).alignment = alignment
        # border setting
        border = openpyxl.styles.borders.Border(
            left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'),
            diagonal=None, outline=True, start=None, end=None)
        border_list = [
            'My Rating', 'Game Name', 'Play Status', 'Platform', 'VR Support', 'Release', 'Minutes Played',
            'Converted Time Played', 'App ID', 'Last Updated', 'Date Added']
        for cell in border_list:
            self.games.cell(
                row=self.row_index[game_name], column=self.column_index[cell]).border = border


    def refresh_steam_games(self, steam_id):
        '''
        Gets games owned by the entered Steam ID amd runs excel update/add functions.
        '''
        # asks for a steam id if the given one is invalid
        if len(steam_id) != 17:
            steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        root_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
        url_var = f'?key={self.get_api_key()}&steamid={steam_id}'
        combinded_url = f'{root_url}{url_var}&include_played_free_games=0&format=json&include_appinfo=1'
        try:
            data = requests.get(combinded_url)
        except requests.exceptions.ConnectionError:
            print('Internet Error')
            return False
        if data.status_code == requests.codes.ok:
            self.total_games_updated = 0
            self.total_games_added = 0
            self.added_games = []
            for game in data.json()['response']['games']:
                game_name = game['name']
                playtime_forever = game['playtime_forever']
                game_appid = game['appid']
                # Demo
                if re.search(r'\bdemo\b', game['name'].lower()) or re.search(r'\btest\b', game['name'].lower()):
                    play_status = 'Demo'  # sets play_status to Demo if demo or test appears in the name
                # Unplayed
                elif playtime_forever <= 20:
                    play_status = 'Unplayed'  # sets play_status to Unplayed if playtime_forever is 0-15
                # Played
                elif game['playtime_windows_forever'] > 10 * 60:  # hours multiplied by minutes in an hour
                    play_status = 'Played'  # sets play_status to Played if playtime_forever is greater then 10 hours
                # Unset
                else:
                    play_status = 'Unset'  # sets play_status to Unset if none of the above applies
                # Updates game if it is in the index or adds if it is not.
                if game_name in self.row_index.keys():
                    self.update_game(game_name, playtime_forever, play_status)
                else:
                    self.add_game(game_name, playtime_forever, game_appid, play_status)
                    self.added_games.append(game_name)
                # formats the added/updated cells to be sure it is set right
                self.format_cells(game['name'])
            return True
        if data.status_code == 500:
            print('Server Error: make sure your api key and steam id is valid.')
        else:
            print('\nFailed to connect to Steam API:\nCheck your internet.')
            print(data.status_code)
            return False


    def save_excel_sheet(self):
        '''
        Backs up the excel file before saving the changes.
        It will keep trying to save until it completes in case of permission errors caused by the file being open.
        '''
        shutil.copy(self.file_path, os.path.join(os.getcwd(), self.excel_filename + '.bak'))
        # saves the file once it is closed
        complete = False
        print('\nSaving.\nMake sure the excel sheet is closed.')
        while complete != True:
            try:
                self.wb.save(self.excel_filename + '.xlsx')
                print('Save Complete.')
                complete = True
            except PermissionError:
                time.sleep(.1)


    def update_game(self, game_name, playtime_forever, play_status):
        '''
        Updates the games playtime(if changed) and play status(if unset).
        '''
        current_playtime = self.games.cell(row=self.row_index[game_name],
            column=self.column_index['Minutes Played']).value
        current_platform = self.games.cell(row=self.row_index[game_name], column=self.column_index['Platform']).value
        if current_playtime == 'Minutes Played' or current_platform != 'Steam':
            return
        elif current_playtime == None:
            print(f'Missing current_playtime for {game_name}')
            current_playtime = 0
        else:
            current_playtime = int(current_playtime)
        if playtime_forever > current_playtime:
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Minutes Played']).value = playtime_forever
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Converted Time Played']).value = self.playtime_conv(playtime_forever)
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Last Updated']).value = dt.datetime.now().strftime(self.date_format)
            self.total_games_updated += 1
            if play_status == 'unset':
                self.games.cell(row=self.row_index[game_name], column=self.column_index['Play Status']).value = 'Played'
            added_time = self.playtime_conv(playtime_forever - current_playtime)
            print(f'\n > {game_name} updated.\n   Added {added_time}.')


    def add_game(self, game_name, playtime_forever, game_appid, play_status):
        '''
        Appends new game to excel sheet into the correct columns using self.column_index.
        Any columns that are inputted manually are left blank.
        '''
        column_info = {
            'My Rating':'',
            'Game Name':game_name,
            'Platform':'Steam',
            'Release':'',
            'VR Support':'',
            'Minutes Played':playtime_forever,
            'Converted Time Played':self.playtime_conv(playtime_forever),
            'App ID':game_appid,
            'Play Status':play_status,
            'Last Updated':dt.datetime.now().strftime(self.date_format),
            'Date Added':dt.datetime.now().strftime(self.date_format),
        }
        append_list = []
        for column in self.column_index:
            if column in column_info:
                append_list.append(column_info[column])
            else:
                append_list.append('')
                print(f'Missing data for {column}.')
        self.games.append(append_list)
        self.total_games_added += 1
        # adds game to row_index
        self.row_index[game_name] = self.games._current_row


    def pick_random_game(self):
        '''
        Allows you to pick a play_status to have a random game chosen from. It allows retrying.
        '''
        if input('\nDo you want to pick a random game with a specific play status?\n').lower() in ['yes', 'y', 'yeah']:
            print('\nWhat play status do you want a random game picked from?')
            play_status_choices = {
                '1':'Played', '2':'Playing', '3':'Waiting', '4':'Finished',
                '5':'Quit', '6':'Unplayed', '7':'Ignore', '8':'Demo'
            }
            play_status = input(', '.join(play_status_choices.values()) + '\n')
            if len(play_status) == 1:
                play_status = play_status_choices[play_status]
            choice_list = []
            for game, index in self.row_index.items():
                game_play_status = self.games.cell(row=index, column=self.column_index['Play Status']).value.lower()
                if game_play_status == play_status.lower():
                    choice_list.append(game)
            picked_game = random.choice(choice_list)
            # TODO add improvements to output
            print(f'\nPicked game with {play_status} status:\n{picked_game}')
            # allows getting another random pick
            while not input('Press Enter to pick another and No for finish.').lower() in ['no', 'n']:
                picked_game = random.choice(choice_list)
                print(f'\nPicked game with {play_status} status:\n{picked_game}')


    def run(self):
        '''
        Main run function.
        '''
        print('Starting Game Tracker')
        if self.refresh_steam_games(self.steam_id):
            # shows total games added and updated(includes info that was updated)
            print(f'\nGames Added: {self.total_games_added}')
            if len(self.added_games) > 0:
                added_games_string = ', '.join(self.added_games)
                print(added_games_string)
            print(f'\nGames Updated: {self.total_games_updated}')
            self.save_excel_sheet()
        try:
            self.pick_random_game()
            input('\nPress Enter to open updated file in Excel.\n')
            os.startfile(self.file_path)  # opens excel file if previous input is passed
        except KeyboardInterrupt:
            print('Closing')


if __name__ == "__main__":
    # Tracker().run()
    Tracker().get_time_to_beat()
