import sqlite3
import requests
from time import sleep
from Check_for_API_File import Check_for_API
from pprint import pprint


class Tracker:

    def __init__(self, steam_id):
        self.steam_id = str(steam_id)
        self.api_key = Check_for_API()
        self.games_data = sqlite3.connect('games_data.db')
        self.cursor = self.games_data.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
        game_name text,
        playtime_forever int,
        playtime_converted int,
        game_appid text,
        play_status text
        )''')



    def Update_Game_Database(self):
        '''Gets names of games owned by the entered Steam ID.'''
        while len(self.steam_id) != 17:
            steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        base_url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=0&format=json&include_appinfo=1'
        data = requests.get(base_url).json()
        # pprint(data)
        for item in data['response']['games']:
            game_name = item['name']
            playtime_forever = item['playtime_forever']
            if playtime_forever == 0:
                play_status = 'unplayed'
            else:
                play_status = 'unset'
            if playtime_forever < 61:
                playtime_converted = f'{playtime_forever} minutes'
            elif playtime_forever != 0:
                playtime_converted = f'{round(playtime_forever/60, 1)} hours'
            else:
                playtime_converted = 0
            game_appid = item['appid']
            print(game_name, playtime_converted)
