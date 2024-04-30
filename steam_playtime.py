import requests
import json
import os
import code
import math

from steam_purchases import SteamPurchases, get_steam_api_key


class SteamTimeDaily(SteamPurchases):
    def __init__(self):
        self.api_key = get_steam_api_key()
        self.api_url = (
            "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="
            + self.api_key
            + "&include_appinfo=true&skip_unvetted_apps=false&include_played_free_games=true&steamid="
        )
        self.user_api_url = (
            "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="
            + self.api_key
            + "&steamids="
        )
        self.steam_store_url = "https://store.steampowered.com/app/"

        self.db = self.load_db()
        self.time_db = self.load_time_db()

    def load_time_db(self):
        with open("database/steamtimedaily.json", "r") as file:
            return json.load(file)

    def save_time_db(self, db):
        with open("database/steamtimedaily.json", "w") as file:
            json.dump(db, file, indent=2)

    # def add_players_playtime(self, games_info):
    # for game in games_info:
    #'name': 'Max Payne 2: The Fall of Max Payne', 'playtime_forever
    # if game['name'] in self.time_db:

    def run(self):
        for steam_id in self.db:
            games_info = self.get_games_list(steam_id)
            add_players_playtime(games_info)


class SteamPlaytime(SteamPurchases):
    def __init__(self):
        super().__init__()
        self.purchase_db = self.load_db()

    def get_2week_playtime(self, steam_id):
        response = requests.get(self.api_url + steam_id)
        response = json.loads(response.text)
        response = response["response"]
        if "game_count" not in response:
            # If people don't have profile public.
            return []
        if response["game_count"] == 0:
            return []
        return response["games"]

    def run(self):
        output = "In the last 2 weeks the fellas have played for a combined time: \n"
        temp_db = {}
        multiple_users = {}
        for steam_id in self.purchase_db:
            games = self.get_2week_playtime(steam_id)
            for game in games:
                if "name" not in game:
                    # Some app ids are not public. Skip these.
                    continue
                if "playtime_2weeks" not in game:
                    continue
                if game["name"] in temp_db:
                    temp_db[game["name"]] += game["playtime_2weeks"]
                    multiple_users[game["name"]] = True
                else:
                    temp_db[game["name"]] = game["playtime_2weeks"]
                    multiple_users[game["name"]] = False
        # Remove games without multiple users.
        for game_name in multiple_users:
            if multiple_users[game_name] is False:
                del temp_db[game_name]
        temp_db = dict(sorted(temp_db.items(), key=lambda item: item[1], reverse=True))
        # print(temp_db)
        for game in temp_db:
            output += (
                "`"
                + game
                + " - "
                + str(math.floor(temp_db[game] / 60))
                + " hours "
                + str(temp_db[game] % 60)
                + " mins`\n"
            )
        return output
