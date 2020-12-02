from Check_for_API_File import Check_for_API
from Excel_Indexer import *
import datetime as dt
import openpyxl
import requests
import os
from openpyxl.styles import Border, Side, Alignment
from openpyxl.utils import get_column_letter

class Tracker:


    def __init__(self, steam_id):
        self.steam_id = str(steam_id)
        self.api_key = Check_for_API()
        self.wb = openpyxl.load_workbook(os.path.join(os.getcwd(), 'game_data.xlsx'))
        self.games = self.wb['Games']
        self.column_index, self.row_index = Create_Column_Row_Index(workbook=self.games,
            column_name='Game Name', column_letter='A')
        self.excel_loc = ''


    def refresh_steam_games(self):
        '''Gets games owned by the entered Steam ID.'''
        if len(self.steam_id) != 17:
            self.steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        root_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
        combinded_url = f'''
        {root_url}?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=0&format=json&include_appinfo=1
        '''
        data = requests.get(combinded_url).json()
        self.games_updated = 0
        self.games_added = 0
        for item in data['response']['games']:
            game_name = item['name']
            playtime_forever = item['playtime_forever']
            game_appid = item['appid']
            if playtime_forever == 0:
                play_status = 'Unplayed'
            else:
                play_status = 'unset'
            if game_name in self.row_index.keys():
                self.update_game(game_name, playtime_forever, play_status)
            else:
                self.add_steam_game(game_name, playtime_forever, game_appid, play_status)
        print(f'Games Added: {self.games_added}\nGames Updated: {self.games_updated}')
        self.wb.save('game_data.xlsx')


    def update_game(self, game_name, playtime_forever, play_status):
        current_playtime = self.games.cell(row=self.row_index[game_name],
        column=self.column_index['Minutes Played']).value
        if current_playtime == 'Minutes Played':
            return
        else:
            current_playtime = int(current_playtime)
        if playtime_forever > current_playtime:
            print(game_name, current_playtime)
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Minutes Played']).value = playtime_forever
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Converted Time Played']).value = self.playtime_conv(playtime_forever)
            self.games.cell(row=self.row_index[game_name],
                column=self.column_index['Last Updated']).value = dt.datetime.now()
            self.games_updated += 1
            if play_status == 'unset':
                self.games.cell(row=self.row_index[game_name], column=self.column_index['Play Status']).value = 'Played'
                print('Test')


    def add_steam_game(self, game_name, playtime_forever, game_appid, play_status):
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
            'Last Updated':dt.datetime.now(),
            'Date Added':dt.datetime.now(),
        }
        append_list = []
        for column in self.column_index:
            if column in column_info:
                append_list.append(column_info[column])
            else:
                append_list.append('')
                print(f'Missing data for {column}.')
        self.games.append(append_list)
        # TODO add gridlines to appended rows
        self.games_added += 1


    @staticmethod
    def playtime_conv(playtime_forever):
        '''
        Converts minutes to a written string of minutes(1) or hours(1.0).
        '''
        if playtime_forever < 61:
            playtime_converted = f'{playtime_forever} minutes'
        else:
            playtime_converted = f'{round(playtime_forever/60, 1)} hours'
        return playtime_converted


    def set_styles(self):
        '''
        Sets styles for each column.
        TODO finish centering and setting format for dates and centering of other specific columns.
        '''
        border = Border(left=Side(border_style=None, color='FF000000'),
        right=Side(border_style=None, color='FF000000'),
        top=Side(border_style=None, color='FF000000'),
        bottom=Side(border_style=None, color='FF000000'),
        diagonal=Side(border_style=None, color='FF000000'),
        diagonal_direction=0,
        outline=Side(border_style=None, color='FF000000'),
        vertical=Side(border_style=None, color='FF000000'),
        horizontal=Side(border_style=None, color='FF000000'))
        alignment=Alignment(horizontal='general',
            vertical='bottom',
            text_rotation=0,
            wrap_text=True,
            shrink_to_fit=False,
            indent=0)
        number_format = 'Date'
        date_columns = ['Date Added', 'Last Updated']
        # for column in self.column_index:
        #     print(column)
        #     if column in date_columns:
        #         column_letter = get_column_letter(self.column_index[column])
        #         col = self.wb.column_dimensions[column_letter]
        #         col.border = Bor
        # col.font = Font(bold=True)
        # row = self.wbs.row_dimensions[1]
        # row.font = Font(underline="single")


if __name__ == "__main__":
    App = Tracker(76561197982626192)
    # App.refresh_steam_games()
    App.set_styles()
