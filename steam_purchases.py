import requests
import json
import os
import code
from datetime import datetime, timedelta
import time


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

        self.steam_price_api = "https://store.steampowered.com/api/appdetails?filters=price_overview&appids="

        self.db = self.load_db()

        self.gmw_output = ""
        self.game_playtime = {}

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
        steam_id_games["gmw"] = {}
        steam_id_games["time"] = {}
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
        # print(self.api_url + steam_id)
        # code.interact(local=locals())
        response_full = requests.get(self.api_url + steam_id)
        response = json.loads(response_full.text)
        if "games" not in response["response"]:
            # Log Error
            with open("database/error.txt", mode="a") as file:
                file.write(
                    self.db[steam_id]["name"]
                    + "-"
                    + steam_id
                    + "-"
                    + str(response_full)
                    + "no games - recorded at %s.\n" % (datetime.now())
                )
            return []

        response = response["response"]["games"]
        return response

    def get_gmw_minutes(self, app_id):
        response_full = requests.get(self.steam_price_api + str(app_id))
        response = json.loads(response_full.text)
        # 100 to dollars, $4 per hour, 60 minutes.
        if len(response[str(app_id)]["data"]) == 0:
            return 0
        # Check if free
        if response[str(app_id)]["data"]["price_overview"]["final_formatted"] == "Free":
            return 0
        gmw_minutes = (
            response[str(app_id)]["data"]["price_overview"]["final"] / 100 / 4 * 60
        )
        return gmw_minutes

    def get_matching_game(self, games_list, appid):
        for game in games_list:
            if str(appid) == str(game["appid"]):
                return game
        return None

    def check_gmw(self, steam_id, games_list):
        delete_app_ids = []
        for appid in self.db[steam_id]["gmw"]:
            game = self.get_matching_game(games_list, appid)
            if game is None:
                # Game is refunded. Delete and print.
                delete_app_ids += [appid]
                game_name = self.db[steam_id]["games"][appid]
                del self.db[steam_id]["games"][appid]
                self.gmw_output += ":coffin: " + self.db[steam_id]["name"] + " returned " + game_name + " \n"
                continue
            # Found matching game in list.
            gmw_min = self.db[steam_id]["gmw"][appid]
            if gmw_min <= game["playtime_forever"]:
                self.gmw_output += (
                    ":white_check_mark: "
                    + self.db[steam_id]["name"]
                    + " GMW in "
                    + game["name"]
                    + " "
                    + "`Paid $"
                    + str(round(gmw_min / 60 * 4))
                    + " with "
                    + str(round(game["playtime_forever"] / 60, 1))
                    + " hrs` \n"
                )

                # Remove from gmw db.
                delete_app_ids += [appid]
        for app_ids in delete_app_ids:
            del self.db[steam_id]["gmw"][app_ids]

    def print_dgmw(self):
        output = ""
        total_gmw = {}
        for steam_id in self.db:
            if len(self.db[steam_id]["gmw"]) == 0:
                continue
            total_gmw[self.db[steam_id]["name"]] = 0
            games_list = self.get_games_list(steam_id)
            for appid in self.db[steam_id]["gmw"]:
                hours_left = self.db[steam_id]["gmw"][appid] / 60 
                hours_in = 0
                game = self.get_matching_game(games_list, appid)
                if game is None:
                    # Means game has been returned.
                    continue
                hours_in = game["playtime_forever"] / 60
                hours_left -= hours_in
                total_gmw[self.db[steam_id]["name"]] += hours_left
                output += (
                    ":x: "
                    + self.db[steam_id]["name"]
                    + " DGMW in "
                    + self.db[steam_id]["games"][appid]
                    + " `Paid $"
                    + str(round(self.db[steam_id]["gmw"][appid] / 60 * 4))
                    + " need "
                    + str(round(hours_left, 1))
                    + " more hrs` \n"
                )

        output += "==="
        for player in total_gmw:
            output += player + " needs " + str(round(total_gmw[player], 1)) + " hours \n"
        return output
    
    def week_passed(self):
        with open("database/prevtime.json", "r") as file:
            prev_time_db = json.load(file)
        prev_time = datetime.fromtimestamp(prev_time_db['prevtime'])

        current_datetime = datetime.now()
        time_diff = current_datetime - prev_time
        one_week = timedelta(weeks=1)
        if time_diff >= one_week:
            return True
        else:
            return False

    def get_new_purchases(self, steam_id):
        output = ""
        first_game_link = ""
        games_list = self.get_games_list(steam_id)
        # Check if ready for time update.
        self.game_playtime[steam_id] = {}

        # Check GMW
        self.check_gmw(steam_id, games_list)

        # causes bugs when some free games get removed.
        #if len(games_list) == len(self.db[steam_id]["games"]):
        #    return output, first_game_link
        for game in games_list:
            self.game_playtime[steam_id][str(game["appid"])] = game["playtime_forever"]
            if str(game["appid"]) not in self.db[steam_id]["games"]:
                # Add space to separate games and steam name.
                output += " - " + game["name"]
                if first_game_link == "":
                    # Add link to first game.
                    first_game_link = self.steam_store_url + str(game["appid"])
                # Append game to games list.
                self.db[steam_id]["games"][str(game["appid"])] = game["name"]
                # Append gmw minutes to gmw list.
                self.db[steam_id]["gmw"][str(game["appid"])] = self.get_gmw_minutes(game["appid"])
        return output, first_game_link

    def run_debug(self):
        output = []
        for steam_id in self.db:
            purchase, link = self.get_new_purchases(steam_id)
            if purchase == "":
                continue
            output += ["`" + self.db[steam_id]["name"] + purchase + "`\n" + link]
        return output

    def run(self):
        output = []
        for steam_id in self.db:
            time.sleep(3)
            purchase, link = self.get_new_purchases(steam_id)
            if purchase == "":
                continue
            output += ["`" + self.db[steam_id]["name"] + purchase + "`\n" + link]
        self.save_db(self.db)
        return output
