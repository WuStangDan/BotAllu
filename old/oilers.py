import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import discord


class OilersTracker:
    def __init__(self, db):
        self.replit_db = db

    def api_team_prev(self):
        api = "https://statsapi.web.nhl.com/api/v1/teams/22"
        api += "?expand=team.schedule.previous"
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)

    def api_team_next(self):
        api = "https://statsapi.web.nhl.com/api/v1/teams/22"
        api += "?expand=team.schedule.next"
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)

    def api_game(self, game_id):
        api = "https://statsapi.web.nhl.com/api/v1/game/"
        api += game_id
        api += "/content"
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)

    def playoffs_money_puck(self):
        r = requests.get(
            "https://moneypuck.com/moneypuck/simulations/simulations_recent.csv"
        )
        for row in r.text.splitlines():
            if "ALL,EDM" in row:
                break
        return row.split(",")[4:8]

    def get_game_id_and_title(self, api):
        in_playoffs = False
        game_found = False
        if "previousGameSchedule" in api["teams"][0]:
            info = api["teams"][0]["previousGameSchedule"]["dates"][0]["games"][0]
            game_found = True
        if "nextGameSchedule" in api["teams"][0]:
            info = api["teams"][0]["nextGameSchedule"]["dates"][0]["games"][0]
            game_found = True
        if game_found == False:
            return "", ""
        away = info["teams"]["away"]
        home = info["teams"]["home"]
        # Away team name and record.
        title = away["team"]["name"] + " "
        if "previousGameSchedule" in api["teams"][0]:
            # Record of old game.
            title += " "
        title += "(" + str(away["leagueRecord"]["wins"]) + "-"
        title += str(away["leagueRecord"]["losses"]) + "-"
        if not in_playoffs:
            title += (
                str(away["leagueRecord"]["ot"]) + ") "
            )  # Doesn't appear during playoffs.
        else:
            title += ") "
        if "previousGameSchedule" in api["teams"][0]:
            title += " "
        title += "at "
        # Home team name and record.
        title += home["team"]["name"] + " "
        if "previousGameSchedule" in api["teams"][0]:
            title += " "
        title += "(" + str(home["leagueRecord"]["wins"]) + "-"
        title += str(home["leagueRecord"]["losses"]) + "-"
        if not in_playoffs:
            title += (
                str(home["leagueRecord"]["ot"]) + ")"
            )  # Doesn't appear during playoffs.
        else:
            title += ")"
        if "previousGameSchedule" in api["teams"][0]:
            title += " "
        title += " - " + info["status"]["abstractGameState"]
        return str(info["gamePk"]), title

    def stats_projection(self):
        url = "https://projects.fivethirtyeight.com/2023-nhl-predictions/"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        # Get name index to match playoff percent.
        names = soup.find_all("span", class_="name")
        for i in range(len(names)):
            if names[i].text == "Oilers":
                break
        projected_points = soup.find_all("td", class_="proj-points")
        projected_points = projected_points[i].text
        odds = soup.find_all("td", class_="odds")
        # Multiplied by 3 because list contains playoff odds,
        # make cup final odds, and win stanely cup odds for each team.
        make_playoffs = odds[i * 3 + 0].text
        make_final = odds[i * 3 + 1].text
        win_cup = odds[i * 3 + 2].text

        ordinal = lambda n: "%d%s" % (
            n,
            "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
        )

        win_cup_rank = ordinal(i + 1)

        return projected_points, make_playoffs, make_final, win_cup, win_cup_rank

    def print_next_game_time(self):
        in_playoffs = False
        oilers_next = self.api_team_next()
        oilers_next = oilers_next["teams"][0]
        next_game_str = ""
        if "nextGameSchedule" in oilers_next:
            oilers_next = oilers_next["nextGameSchedule"]["dates"][0]["games"][0]
            next_game_str += oilers_next["teams"]["away"]["team"]["name"]
            next_game_str += " at "
            next_game_str += oilers_next["teams"]["home"]["team"]["name"]
            next_game_str += ", "
            date = datetime.strptime(oilers_next["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            date -= timedelta(hours=6)
            next_game_str += date.__str__()[:-3] + " MT"
        # Regular Season
        if not in_playoffs:
            (
                projected_points,
                make_playoffs,
                make_final,
                win_cup,
                win_cup_rank,
            ) = self.stats_projection()
            next_game_str += "\n`\nEDM Stats Projection (fivethirtyeight.com)"
            next_game_str += (
                "\nProj. Points / Make Playoffs: "
                + projected_points
                + " / "
                + make_playoffs
            )
            next_game_str += (
                "\nWin Cup Rank / Win Cup %:     "
                + win_cup_rank
                + " / "
                + win_cup
                + "`"
            )
        # Playoffs
        else:
            round1, round2, round3, cup = self.playoffs_money_puck()
            next_game_str += "\n`\nEDM Odds Projection (moneypuck.com)"
            next_game_str += f"\nWin Round 1: {float(round1)*100:.1f}% | Win Round 2: {float(round2)*100:.1f}%"
            next_game_str += f"\nWin Conference: {float(round3)*100:.1f}% | Win Cup: {float(cup)*100:.1f}%`"
        return next_game_str

    def print_game_info(self, game_id, title):
        if "Preview" in title:
            return None, False
        game = self.api_game(game_id)
        # Needed since I potentially use recap in description.
        description = ""
        if len(game["media"]["epg"][3]["items"]) >= 1:
            description = "" + game["media"]["epg"][3]["items"][0]["title"] + ""
        embed = discord.Embed(
            title=title, description=description, color=discord.Colour.orange()
        )

        # Get Highlights
        highlight_order = []
        for i in range(len(game["highlights"]["gameCenter"]["items"])):
            id = int(game["highlights"]["gameCenter"]["items"][i]["id"])
            highlight_order += [[id, i]]
        for highlight_index in sorted(highlight_order):
            highlight = game["highlights"]["gameCenter"]["items"][highlight_index[1]]
            highlight_name = "" + highlight["blurb"].split(": ")[-1] + ""
            embed.add_field(
                name=highlight_name,
                value="[Link](" + highlight["playbacks"][3]["url"] + ")",
                inline=True,
            )

        # Get recap.
        if len(game["media"]["epg"][2]["items"]) < 1:
            return embed, False
        if game["media"]["epg"][2]["title"] == "Extended Highlights":
            embed.add_field(
                name=game["media"]["epg"][2]["items"][0]["blurb"],
                value="[Link]("
                + game["media"]["epg"][2]["items"][0]["playbacks"][3]["url"]
                + ")",
                inline=False,
            )
            # playoffs not supplied
            embed.add_field(name="Next Game", value=self.print_next_game_time())

            return embed, True

    async def write_discord_msg(self, game_id, game_embed, finished, channel):
        in_playoffs = False
        if game_embed == None:
            # Nothing to output.
            return
        if game_id not in self.replit_db:
            # Message doesn't exist, create and add to db.
            msg = await channel.send(embed=game_embed)
            self.replit_db[game_id] = msg.id
        else:
            if self.replit_db[game_id] == "finished":
                # Message in final state, no more updates required.
                return
            # Message exists, edit existing message.
            msg = await channel.fetch_message(self.replit_db[game_id])
            await msg.edit(embed=game_embed)
            if finished is True and in_playoffs is False:
                self.replit_db[game_id] = "finished"

    async def run(self, channel):
        # TODO Add proper error handling if no nextgameschedule.
        # Get prev game ID and attempt to output.
        prev_game_id, title = self.get_game_id_and_title(self.api_team_prev())
        if title == "":
            return
        prev_embed, prev_finished = self.print_game_info(prev_game_id, title)
        await self.write_discord_msg(prev_game_id, prev_embed, prev_finished, channel)

        # Get next game ID and attemp to output.
        next_game_id, title = self.get_game_id_and_title(self.api_team_next())
        if title == "":
            return
        next_embed, next_finished = self.print_game_info(next_game_id, title)
        await self.write_discord_msg(next_game_id, next_embed, next_finished, channel)
