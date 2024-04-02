import requests
import json
import os
import code


def get_steam_api_key():
    SECRETS = {}
    with open("BotAlluPrivate/secrets.json", "r") as file:
        SECRETS = json.load(file)
    return SECRETS["STEAM_API_KEY"]


class SteamPurchases:
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

    def load_db(self):
        with open("database/steampurchases.json", "r") as file:
            return json.load(file)

    def save_db(self, db):
        with open("database/steampurchases.json", "w") as file:
            json.dump(db, file, indent=2)

    def get_steam_profile(self, steam_id):
        # print("test this")
        # print(self.user_api_url + steam_id)
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

    def get_current_users(self):
        # Return all users currently being tracked.
        output_msg = "`Currently tracking purchases for:\n"
        for steam_id in self.db:
            output_msg += self.db[steam_id]["name"] + "\n"
        output_msg += "`"
        return output_msg

    def get_games_list(self, steam_id):
        # print("test this")
        # print(self.user_api_url + steam_id)
        # code.interact(local=locals())
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
        for steam_id in self.db:
            purchase, link = self.get_new_purchases(steam_id)
            if purchase == "":
                continue
            output += ["`" + self.db[steam_id]["name"] + purchase + "`\n" + link]
        self.save_db(self.db)
        return output


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

    #def add_players_playtime(self, games_info):
        #for game in games_info:
            #'name': 'Max Payne 2: The Fall of Max Payne', 'playtime_forever
            #if game['name'] in self.time_db:

    def run(self):
        for steam_id in self.db:
            games_info = self.get_games_list(steam_id)
            add_players_playtime(games_info)



class SteamPlaytime:
    def __init__(self):
        self.api_key = get_steam_api_key()
        self.api_url = (
            "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key="
            + self.api_key
            + "&steamid="
        )

        self.purchase_db = self.load_purchase_db()
        self.db = self.load_db()

    def load_db(self):
        with open("database/steampurchases.json", "r") as file:
            return json.load(file)

    def save_db(self, db):
        with open("database/steampurchases.json", "w") as file:
            json.dump(db, file, indent=2)

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
        multiple_users = {}
        for steam_id in self.db:
            games = self.get_2week_playtime(steam_id)
            for game in games:
                if "name" not in game:
                    # Some app ids are not public. Skip these.
                    continue
                if game["name"] in temp_db:
                    temp_db[game["name"]] += game["playtime_2weeks"]
                    multiple_users[game["name"]] = True
                else:
                    temp_db[game["name"]] = game["playtime_2weeks"]
                    multiple_users[game["name"]] = False
        # Remove games without multiple users.
        for game_name in multiple_users.keys():
            if multiple_users[game_name] is False:
                del temp_db[game_name]
        temp_db = dict(sorted(temp_db.items(), key=lambda item: item[1], reverse=True))
        print(temp_db)
        return output
