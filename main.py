import discord
from discord.ext import tasks
from discord.ext.commands import Bot
from asyncio import sleep
import os
import json
from replit import db
import val

client = discord.Client()

@client.event
async def on_ready():
  print(str(client.user) + " is ready to rock.")
  # Init db.
  if "players" not in db.keys():
    # key: player puuid
    # value: dict containing player stats.
    db["players"] = {}
  # Start leaderboard continous task.
  update_leaderboard.start()

@client.event
async def on_message(message):
  # Ignore our own messages.
  if message.author == client.user:
    return
  
  if message.content.startswith('!BotAllu help'):
    await message.channel.send('!BotAllu adduser RiotName#RiotNumber')

  if message.content.startswith('!BotAllu adduser'):
    if val.add_new_player(message.content[16:]):
      await message.channel.send('Added ' + message.content[16:] + ' to leaderboard.')
    else:
      # Function will return none if the string passed can't be parsed or is othwerwise invalid.
      await message.channel.send('Invalid player name/tag or player already added.')
 
  
  # Sets the current channel to the leaderboard channel.
  if message.content.startswith('!BotAllu set'):
    db["leaderboard_channel_id"] = message.channel.id
    await message.channel.send('Leaderboard channel set here!')

@tasks.loop(seconds=5)
async def update_leaderboard():
  if "leaderboard_channel_id" not in db.keys():
    return
  channel_id = db["leaderboard_channel_id"]
  msg = await client.get_channel(channel_id).history(limit=1).flatten()
  msg = msg[0]
  channel = client.get_channel(channel_id)
  leaderboard = val.generate_leaderboard()
  if msg.author == client.user:
    await msg.edit(content=leaderboard)

client.run(os.environ['TOKEN'])
