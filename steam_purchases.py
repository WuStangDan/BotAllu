import requests
import json
import os


class SteamPurchases:
    def __init__(self, db):
        self.api_key = os.environ['STEAM_API_KEY']
        self.api_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + self.api_key + '&include_appinfo=true&steamid='
        self.user_api_url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' + self.api_key + '&steamids='
        self.db = db

    def get_steam_profile(self, steam_id):
        response = requests.get(self.user_api_url + steam_id)
        response = json.loads(response.text)
        response = response['response']['players'][0]
        return response

    def add_steam_id(self, steam_id):
        profile = self.get_steam_profile(steam_id)
        if profile['communityvisibilitystate'] != 3:
            return 'Steam profile is not public.'
        steam_id_games = {}
        steam_id_games['name'] = profile['personaname']
        steam_id_games['games'] = {}
        games_list = self.get_games_list(steam_id)
        for game in games_list:
            steam_id_games['games'][str(game['appid'])] = game['name']
        self.db[steam_id] = steam_id_games
        # Return all users currently being tracked.
        output_msg = '`Currently tracking purchases for:\n'
        for id in self.db:
            output_msg += self.db[id]['name'] + '\n'
        output_msg += '`'
        return output_msg

    def get_games_list(self, steam_id):
        response = requests.get(self.api_url + steam_id)
        response = json.loads(response.text)
        response = response['response']['games']
        return response

    def get_new_purchases(self, steam_id):
        output = ''
        games_list = self.get_games_list(steam_id)
        if len(games_list) == len(self.db[steam_id]['games']):
            return output
        for game in games_list:
            if str(game['appid']) not in self.db[steam_id]['games']:
                # Add space to separate games and steam name.
                output += ' - ' + game['name']
                # Append game to games list.
                self.db[steam_id]['games'][str(game['appid'])] = game['name']
        return output

    def run(self):
        output = []
        for id in self.db:
            purchase = self.get_new_purchases(id)
            if purchase == '':
                continue
            output += [self.db[id]['name'] + purchase]
        return output
