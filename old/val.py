import requests
import json
from replit import db
from tabulate import tabulate


# This function fills out a players dict in the database.
# I have to use dicts since replit db can't embed a class or struct.
# Ugly AF but using dicts means I don't have to switch dbs.
def fill_new_player_dict(name, tag, puuid):
    db["players"][puuid] = {}

    d = db["players"][puuid]
    d["name"] = name
    d["tag"] = tag
    d["puuid"] = puuid
    d["friend_score"] = 0
    d["wins"] = 0
    d["losses"] = 0
    d["kills"] = 0
    d["deaths"] = 0
    d["assists"] = 0
    d["mmr"] = 0
    d["total_minutes"] = 0
    # Use this so matches aren't double counted.
    d["parsed_matches"] = {}


# This function adds new players to the player database.
def add_new_player(msg):
    name = msg.split("#")[0]
    tag = msg.split("#")[1]
    response = requests.get(
        "https://api.henrikdev.xyz/valorant/v1/account/" + name + "/" + tag
    )
    if response.status_code == 404:
        return False
    if response.status_code != 200:
        return False

    json_data = json.loads(response.text)
    puuid = json_data["data"]["puuid"]

    # Don't add if player already exists in database.
    if puuid in db["players"]:
        return False
    fill_new_player_dict(name, tag, puuid)
    return True


# TODO: Way more efficient to collect all matches
# for all players, then go through them. Right now
# I have an extra loop for no good reason.
def update_player_data():
    # For each player parse their unrated and competitive match history.
    for i in db["players"]:
        matches = []

        response = requests.get(
            "https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/na/"
            + i
            + "?filter=unrated"
        )
        if response.status_code == 200:
            json_data = json.loads(response.text)
            matches += json_data["data"]

        response = requests.get(
            "https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/na/"
            + i
            + "?filter=competitive"
        )
        if response.status_code == 200:
            json_data = json.loads(response.text)
            matches += json_data["data"]

        # I'm okay with not skipping the match if already parsed,
        # because a new player may have been added and they took part
        # in a previous match. So okay to go through it again.
        for match in matches:
            # If known player count less than 2, match is ignored.
            known_players = []
            for player in match["players"]["all_players"]:
                if player["puuid"] in db["players"]:
                    known_players += [player]
            if len(known_players) < 2:
                continue

            # Go through players and add all stats.
            for player in known_players:
                # Check match id for player to ensure we don't double count matches.
                matchid = match["metadata"]["matchid"]
                if matchid in db["players"][player["puuid"]]["parsed_matches"]:
                    # Potentially update friend score.
                    if (len(known_players) - 1) > db["players"][player["puuid"]][
                        "parsed_matches"
                    ][matchid]:
                        db["players"][player["puuid"]]["friend_score"] += (
                            len(known_players)
                            - 1
                            - db["players"][player["puuid"]]["parsed_matches"][matchid]
                        )
                    db["players"][player["puuid"]]["parsed_matches"][matchid] = (
                        len(known_players) - 1
                    )
                    continue
                else:
                    db["players"][player["puuid"]]["parsed_matches"][matchid] = (
                        len(known_players) - 1
                    )

                d = db["players"][player["puuid"]]
                d["friend_score"] += len(known_players) - 1
                d["kills"] += player["stats"]["kills"]
                d["deaths"] += player["stats"]["deaths"]
                d["assists"] += player["stats"]["assists"]
                d["total_minutes"] += match["metadata"]["game_length"] / 1000 / 60
                # match['teams'] keys are 'red' and 'blue'
                # where player['team'] values are 'Red' and 'Blue'
                # so need to do this.
                if player["team"] == "Blue":
                    player["team"] = "blue"
                if player["team"] == "Red":
                    player["team"] = "red"
                if match["teams"][player["team"]]["has_won"]:
                    d["wins"] += 1
                else:
                    d["losses"] += 1


def generate_leaderboard():
    update_player_data()
    headers = ["", "Friend Score", "Wins", "Kills", "Playtime"]
    table = []
    for puuid in db["players"]:
        d = db["players"][puuid]
        row = [d["name"]]
        row += [d["friend_score"]]
        row += [d["wins"]]
        row += [d["kills"]]
        row += [str(round(d["total_minutes"] / 60)) + " hrs"]

        table += [row]

    # Sort by Friend Score, descending.
    table.sort(reverse=True, key=lambda x: (x[1], x[2], x[3], x[4]))

    leaderboard = tabulate(
        table, headers=headers, colalign=("left", "right", "right", "right", "right")
    )
    # Add ticks to make text fixed width and add description.
    leaderboard = "`" + leaderboard
    leaderboard += "\n\n * Only games played with friends count."
    leaderboard += '\n ** To add friends use "!BotAllu adduser Riotname#RiotNumber"'
    leaderboard += "\n *** For a game with you and 2 friends, your friend score is 2. `"
    return leaderboard
