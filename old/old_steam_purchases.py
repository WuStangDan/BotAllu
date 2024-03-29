import requests
import json
import os
import code


class SteamPurchases:
    def __init__(self, db):
        self.api_key = os.environ["STEAM_API_KEYY"]
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
        self.db = db

    def get_steam_profile(self, steam_id):
        #print("test this")
        #print(self.user_api_url + steam_id)
        response = requests.get(self.user_api_url + steam_id)
        response = json.loads(response.text)
        response = response["response"]["players"][0]
        return response

    def add_steam_id(self, steam_id):
        profile = self.get_steam_profile(steam_id)
        if profile["communityvisibilitystate"] != 3:
            return "Steam profile is not public."
        steam_id_games = {}
        steam_id_games["name"] = profile["personaname"]
        steam_id_games["games"] = {}
        games_list = self.get_games_list(steam_id)
        for game in games_list:
            steam_id_games["games"][str(game["appid"])] = game["name"]
        self.db[steam_id] = steam_id_games
        # Return all users currently being tracked.
        output_msg = "`Currently tracking purchases for:\n"
        for id in self.db:
            output_msg += self.db[id]["name"] + "\n"
        output_msg += "`"
        return output_msg

    def get_games_list(self, steam_id):
        #print("test this")
        #print(self.user_api_url + steam_id)
        #code.interact(local=locals())
        response = requests.get(self.api_url + steam_id)
        response = json.loads(response.text)
        response = response["response"]["games"]
        return response

    def get_new_purchases(self, steam_id):
        output = ""
        first_game_link = ""
        games_list = self.get_games_list(steam_id)
        if len(games_list) == len(self.db[steam_id]["games"]):
            return output, first_game_link
        for game in games_list:
            if str(game["appid"]) not in self.db[steam_id]["games"]:
                # Add space to separate games and steam name.
                output += " - " + game["name"]
                if first_game_link == "":
                    # Add link to first game.
                    first_game_link = self.steam_store_url + str(game["appid"])
                # Append game to games list.
                self.db[steam_id]["games"][str(game["appid"])] = game["name"]
        return output, first_game_link

    def run(self):
        output = []
        for id in self.db:
            purchase, link = self.get_new_purchases(id)
            if purchase == "":
                continue
            output += ["`" + self.db[id]["name"] + purchase + "`\n" + link]
        return output


class SteamPlaytime:
    def __init__(self, db):
        self.db = db
        self.api_key = os.environ["STEAM_API_KEYY"]
        self.api_url = (
            "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key="
            + self.api_key
            + "&steamid="
        )

    def get_2week_playtime(self, steam_id):
        print(self.api_url + steam_id)
        response = requests.get(self.api_url + steam_id)
        response = json.loads(response.text)
        response = response["response"]
        if "total_count" not in response:
            # If people don't have profile public.
            return []
        if response["total_count"] == 0:
            return []
        return response["games"]

    def run(self):
        output = "`"
        temp_db = {}
        for steam_id in self.db:
            games = self.get_2week_playtime(steam_id)
            for game in games:
                if "name" not in game:
                    # Some app ids are not public. Skip these.
                    continue
                if game["name"] in temp_db:
                    temp_db[game["name"]] += game["playtime_2weeks"]
                else:
                    temp_db[game["name"]] = game["playtime_2weeks"]
        print(temp_db)
        return output
