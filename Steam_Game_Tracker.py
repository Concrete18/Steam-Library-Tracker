import sqlite3
import requests
from time import sleep
from Check_for_API_File import Check_for_API
from pprint import pprint


class Tracker:

    def __init__(self, steam_id):
        self.steam_id = str(steam_id)
        self.api_key = Check_for_API()
        self.bulk = 1
        self.database = sqlite3.connect('games_data.db')
        self.cursor = self.database.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
        game_name text,
        platform text,
        playtime_forever int,
        playtime_converted int,
        game_appid text,
        play_status text
        )''')


    def Playtime_Conv(self, playtime_forever):
        if playtime_forever < 61:
            playtime_converted = f'{playtime_forever} minutes'
        else:
            playtime_converted = f'{round(playtime_forever/60, 1)} hours'
        return playtime_converted


    def Add_Steam_Game(self, game_name, playtime_forever, game_appid, play_status, bulk=0):
        self.cursor.execute('''INSERT INTO games VALUES (
        :game_name,
        :platform,
        :playtime_forever,
        :playtime_converted,
        :game_appid,
        :play_status
        )''',
        {
        'game_name': game_name,
        'platform': 'PC',
        'playtime_forever': playtime_forever,
        'playtime_converted': self.Playtime_Conv(playtime_forever),
        'game_appid': game_appid,
        'play_status': play_status,
        })
        print(f'Added ""{game_name}" to Database')
        if bulk == 0:
            self.database.commit()


    def Update_Game(self, game_name, playtime_forever, bulk=0):
        sql_update_query  ='''UPDATE games
        SET playtime_forever = ?
        WHERE game_name = ?;'''
        data = (playtime_forever, game_name)
        cursor.execute(sql_update_query , data)
        print(f'Updated ""{game_name}" in Database')
        if bulk == 0:
            self.database.commit()


    def Update_Steam_Games(self):
        '''Gets games owned by the entered Steam ID.'''
        while len(self.steam_id) != 17:
            steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        base_url = f'''http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=0&format=json&include_appinfo=1'''
        data = requests.get(base_url).json()
        for item in data['response']['games']:
            game_name = item['name']
            playtime_forever = item['playtime_forever']
            playtime_converted = self.Playtime_Conv(playtime_forever)
            game_appid = item['appid']
            if playtime_forever == 0:
                play_status = 'unplayed'
            else:
                play_status = 'unset'
            if game_name in 'database':
                self.Update_Game(game_name, playtime_forever, bulk=1)
            else:
                self.Add_Steam_Game(game_name, playtime_forever, game_appid, play_status, bulk=1)
        self.database.commit()
        print('Update Complete')
