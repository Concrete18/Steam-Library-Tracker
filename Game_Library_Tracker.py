from os import stat
import sqlite3
import requests
from time import sleep
from Check_for_API_File import Check_for_API
from pprint import pprint
import datetime as dt


class Tracker:

    def __init__(self, steam_id):
        self.steam_id = str(steam_id)
        self.api_key = Check_for_API()
        self.database = sqlite3.connect('games_data.db')
        self.cursor = self.database.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
        game_name text,
        platform text,
        playtime_forever int,
        playtime_converted int,
        game_appid text,
        play_status text,
        last_updated text
        )''')


    @staticmethod
    def Playtime_Conv(playtime_forever):
        '''Converts minutes to a written string of minutes(1) or hours(1.0).'''
        if playtime_forever < 61:
            playtime_converted = f'{playtime_forever} minutes'
        else:
            playtime_converted = f'{round(playtime_forever/60, 1)} hours'
        return playtime_converted


    def Check_If_Exists(self, game_appid):
        self.cursor.execute("SELECT game_appid FROM games WHERE game_appid = ?", (game_appid,))
        data = self.cursor.fetchone()
        if data is not None:
            return True
        else:
            return False


    def Add_Other_Game(self, game_name, platform, bulk=0):
        '''Adds game to database.'''
        self.cursor.execute('''INSERT INTO games VALUES (
        :game_name,
        :platform,
        :play_status,
        :last_updated
        )''',
        {
        'game_name': game_name,
        'platform': platform,
        'last_updated': dt.datetime.now(),
        })
        print(f'"{game_name}" Added to Database')
        if bulk == 0:
            self.database.commit()


    def Add_Steam_Game(self, game_name, playtime_forever, game_appid, play_status, bulk=0):
        '''Adds steam game to database.'''
        self.cursor.execute('''INSERT INTO games VALUES (
        :game_name,
        :platform,
        :playtime_forever,
        :playtime_converted,
        :game_appid,
        :play_status,
        :last_updated
        )''',
        {
        'game_name': game_name,
        'platform': 'PC',
        'playtime_forever': playtime_forever,
        'playtime_converted': self.Playtime_Conv(playtime_forever),
        'game_appid': game_appid,
        'play_status': play_status,
        'last_updated': dt.datetime.now(),
        })
        print(f'{game_name}\nAdded to Database.\n')
        if bulk == 0:
            self.database.commit()


    def Update_Game(self, game_name, playtime_forever, game_appid, bulk=0):
        '''Updates game to database.'''
        # TODO Only update game if playtime forever is different
        self.cursor.execute("SELECT playtime_forever FROM games WHERE game_appid = ?", (game_appid,))
        current_playtime = self.cursor.fetchone()[0]
        if current_playtime < playtime_forever:
            sql_update_query  ='''UPDATE games SET playtime_forever = ?, playtime_converted = ?, last_updated = ? WHERE game_appid = ?;'''
            data = (playtime_forever, self.Playtime_Conv(playtime_forever), dt.datetime.now(), game_appid)
            self.cursor.execute(sql_update_query, data)
            self.games_updated += 1
            added_time = self.Playtime_Conv(playtime_forever - current_playtime)
            print(f'{game_name}\nUpdated in Database. Added {added_time} minutes.\n')
            if bulk == 0:
                self.database.commit()


    def Set_Play_Status(self):
        '''Runs through unset games to update their status.'''
        print('What play status do you want to update?')
        action = ''
        choices = '1: Played\n2: Unplayed\n3: Unplayed\n4: Currently Playing\n5: Awaiting Updates\n6: Blacklisted\n7: Unset\n'
        response = int(input(choices))
        play_status_dic = {
            1: 'Played',
            2: 'Unplayed',
            3: 'Finished',
            4: 'Currently Playing',
            5: 'Awaiting Updates',
            6: 'Blacklisted',
            7: 'Unset'}
        if response in play_status_dic:
            action = play_status_dic[response].lower()
        self.cursor.execute("SELECT game_name FROM games WHERE play_status = ?", (action,))
        game_list = self.cursor.fetchall()
        print('Press the number key for the status you want to set the game to.')
        print('Type end  to save changes or cancel to not save changes.')
        print(game_list)
        for game in game_list:
            response = input(
            f'''{game[0]}
            1: Played
            2: Unplayed
            3: Finished
            4: Currently Playing
            5: Awaiting Updates
            6: Blacklisted\n''')
            if response == 'end':
                print('Saving Changes')
                self.database.commit()
                return
            elif response == 'cancel':
                print('Changes Ignored')
                return
            elif  type(response) == str:
                print('Unknown response')
            elif int(response) in range(1,6):
                new_status = play_status_dic[int(response)].lower()
                sql_update_query = 'UPDATE games SET play_status = ?, last_updated = ? WHERE game_name = ?;'
                data = (new_status, dt.datetime.now(), game[0])
                self.cursor.execute(sql_update_query, data)
                print(f'Set {game[0]} to {new_status}')


    def Update_Steam_Games(self):
        '''Gets games owned by the entered Steam ID.'''
        if len(self.steam_id) != 17:
            self.steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        base_url = f'''http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=0&format=json&include_appinfo=1'''
        data = requests.get(base_url).json()
        self.games_updated = 0
        self.games_added = 0
        for item in data['response']['games']:
            game_name = item['name']
            playtime_forever = item['playtime_forever']
            game_appid = item['appid']
            if playtime_forever == 0:
                play_status = 'unplayed'
            else:
                play_status = 'unset'
            if self.Check_If_Exists(game_appid):
                self.Update_Game(game_name, playtime_forever, game_appid, bulk=1)
            else:
                self.Add_Steam_Game(game_name, playtime_forever, game_appid, play_status, bulk=1)
                self.games_added += 1
        self.database.commit()
        print(f'Games Added: {self.games_added}\nGames Updated: {self.games_updated}')


    def Update_Playstation_Games(self):
        '''Gets games owned by the entered Steam ID.'''
        if len(self.steam_id) != 17:
            self.steam_id = input('Invalid Steam ID (It must be 17 numbers.)\nTry Again.\n')
        base_url = f'''http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=0&format=json&include_appinfo=1'''
        data = requests.get(base_url).json()
        self.games_updated = 0
        self.games_added = 0
        for item in data['response']['games']:
            game_name = item['name']
            playtime_forever = item['playtime_forever']
            game_appid = item['appid']
            if playtime_forever == 0:
                play_status = 'unplayed'
            else:
                play_status = 'unset'
            if self.Check_If_Exists(game_appid):
                self.Update_Game(game_name, playtime_forever, game_appid, bulk=1)
            else:
                self.Add_Steam_Game(game_name, playtime_forever, game_appid, play_status, bulk=1)
                self.games_added += 1
        self.database.commit()
        print(f'Games Added: {self.games_added}\nGames Updated: {self.games_updated}')
        print('Update Complete')
