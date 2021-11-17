import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import discord

class OilersTracker:
    def __init__(self, db):
        self.replit_db = db
        
    def api_team_prev(self):
        api = 'https://statsapi.web.nhl.com/api/v1/teams/22'
        api += '?expand=team.schedule.previous'
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)

    def api_team_next(self):
        api = 'https://statsapi.web.nhl.com/api/v1/teams/22'
        api += '?expand=team.schedule.next'
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)

    def api_game(self, game_id):
        api = 'https://statsapi.web.nhl.com/api/v1/game/'
        api += game_id
        api += '/content'
        r = requests.get(api)
        if r.status_code != 200:
            return None
        return json.loads(r.content)
    
    def get_game_id(self, api):
        if 'previousGameSchedule' in api['teams'][0]:
            return str(api['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gamePk'])
        if 'nextGameSchedule' in api['teams'][0]:
            return str(api['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gamePk'])
        return None
    
    def print_next_game_time(self):
        oilers_next = self.api_team_next()
        oilers_next = oilers_next['teams'][0]
        oilers_next = oilers_next['nextGameSchedule']['dates'][0]['games'][0]
        next_game_str = 'Next game: '
        next_game_str += oilers_next['teams']['away']['team']['name']
        next_game_str += ' at '
        next_game_str += oilers_next['teams']['home']['team']['name']
        next_game_str += ', ' 
        date = datetime.strptime(oilers_next['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        date -= timedelta(hours=7)
        next_game_str += date.__str__()[:-3] + ' MT'
        return next_game_str
    
    def print_game_info(self, game_id):
        game = self.api_game(game_id)
        # Get headline.
        if len(game['editorial']['preview']['items']) < 1:
            return False, None
        # Needed since I use recap in description.
        description = ''
        if len(game['media']['epg'][2]['items']) >= 1:
            description = '||' + game['media']['epg'][3]['items'][0]['title'] + '||'
        preview_text = BeautifulSoup(game['editorial']['preview']['items'][0]['preview'] + ' Post Game Report', features='html5lib')
        embed=discord.Embed(title=preview_text.get_text().split(';')[0], description=description, color=discord.Colour.orange())

        # Get milestones.
        if len(game['media']['milestones']) < 1:
            return False, embed
        for highlight in game['media']['milestones']['items']:
            if highlight['type'] == 'GOAL':
                embed.add_field(name='||'+highlight['highlight']['title']+'||', value="[Link](" + highlight['highlight']['playbacks'][3]['url'] + ')', inline=True)
                

        # Get recap.
        if len(game['media']['epg'][2]['items']) < 1:
            return False, embed
        if game['media']['epg'][2]['title'] == 'Extended Highlights':
            embed.add_field(name=game['media']['epg'][2]['items'][0]['blurb'], value="[Link](" + game['media']['epg'][2]['items'][0]['playbacks'][3]['url'] + ')', inline=False)
            embed.add_field(name='Next Game', value=self.print_next_game_time())
            # True return means that game is fully printed and no need to continue editing.
            return True, embed
        
    async def run(self, channel):
        # See if previous game needs to be output.
        prev_game_id = self.get_game_id(self.api_team_prev())

        # If prev game doesn't exist, add to db and create message.
        if prev_game_id not in self.replit_db:
          embed_temp = discord.Embed(title="Oilers Game Recap")
          prev_game_msg = await channel.send(embed=embed_temp)
          self.replit_db[prev_game_id] = prev_game_msg.id

        if self.replit_db[prev_game_id] != 'Done':
          # Edit existing message.
          status, text = self.print_game_info(prev_game_id)
          # No info yet.
          if text == None:
            return
          msg = await channel.fetch_message(self.replit_db[prev_game_id])
          await msg.edit(embed=text)
          if status:
            # Game is now complete.
            self.replit_db[prev_game_id] = 'Done'
        
        # Can't handle current game yet.
        ## See if next game has started.
        #next_game = self.api_team_next()
        #next_game_status = next_game['teams'][0]['nextGameSchedule']
        #next_game_status = next_game_status['dates'][0]['games'][0]
        #next_game_status = next_game_status['status']['abstractGameState']
        #if next_game_status == 'Preview':
        #    # Preview so do nothing.
        #    return
        ## Game is live. create message and display.
        #status, text = self.print_game_info(next_game)