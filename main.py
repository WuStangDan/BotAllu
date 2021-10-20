import discord
from discord.ext import tasks
import os
from replit import db
import val
from flask_server import keep_alive
import bookclub
import cheapshark_deals

client = discord.Client()

@client.event
async def on_ready():
  print(str(client.user) + " is ready to rock.")
  # Init db.
  if "players" not in db.keys():
    # key: player puuid
    # value: dict containing player stats.
    db["players"] = {}

  if "bookclub" not in db.keys():
    db["bookclub"] = {}

  # Used to store deals so that the same one isn't posted multiple times.
  if "dealIDs" not in db.keys():
    db["dealIDs"] = {}
  # Start leaderboard continous task.
  update_leaderboard.start()
  # Start cheapshark continous tasks
  cheapshark.start()

@client.event
async def on_message(message):
  # Ignore our own messages.
  if message.author == client.user:
    return

  ###
  # Repeat
  ### 
  if message.content.startswith('!BotAllu repeat '):
    if message.author.name != 'Ender' or message.author.discriminator != '8157':
      print("Repeat by:")
      print(message.author)
      print('failed.')
      return
    await message.channel.send(message.content[16:])
    await message.delete()
    return

  ###
  # Valorant
  ###
  if message.content.startswith('!BotAllu help'):
    await message.channel.send('!BotAllu adduser RiotName#RiotNumber')
    return

  if message.content.startswith('!BotAllu adduser'):
    if val.add_new_player(message.content[16:]):
      await message.channel.send('Added ' + message.content[16:] + ' to leaderboard.')
    else:
      # Function will return none if the string passed can't be parsed or is othwerwise invalid.
      await message.channel.send('Invalid player name/tag or player already added.')
    return
 
  # Sets the current channel to the leaderboard channel.
  if message.content.startswith('!BotAllu set'):
    db["leaderboard_channel_id"] = message.channel.id
    await message.channel.send('Leaderboard channel set here!')
    return

  ###
  # BookClub
  ###
  if message.content.startswith('!bookclub '):
    if message.content[10:18] == "newgame ":
      bookclub_msg = await message.channel.send('Bookclub progress will go here! Add a player.')
      db['bookclub'] = {}
      db['bookclub']['channel_id'] = message.channel.id
      db['bookclub']['message_id'] = bookclub_msg.id
      db['bookclub']['game_name'] = message.content[18:]
      db['bookclub']['players'] = {}
      return
    elif message.content[10:] == 'bump':
      ## UNTESTED.
      # Delete old message.
      #channel = client.get_channel(db['bookclub']['channel_id'])
      #msg = await channel.fetch_message(db['bookclub']['message_id'])
      #msg.delete()

      #db['bookclub']['channel_id'] = message.channel.id
      #bookclub_msg = await message.channel.send(bookclub.progress())
      #db['bookclub']['message_id'] = bookclub_msg.id
      #message.delete()
      return

    progress = bookclub.parse_message(message.content[10:])
    if progress == False or type(progress) != str:
      # Output of parse_message should be false for error or string for success.
      await message.channel.send('Invalid command. Please delete this message and yours and try again.')
      return
    
    # Delete users message to keep channel clean.
    await message.delete()
    # Edit existing message.
    channel = client.get_channel(db['bookclub']['channel_id'])
    msg = await channel.fetch_message(db['bookclub']['message_id'])
    await msg.edit(content=progress)

  ###
  # Cheapshark Deals
  ###
  if message.content.startswith('!BotAllu dealset'):
    db["dealIDs"]['channel_id'] = message.channel.id
    await message.channel.send('Deals channel set here!')
    return


@tasks.loop(seconds=600)
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

@tasks.loop(seconds=3600)
async def cheapshark():
  if "dealIDs" not in db.keys():
    return
  if 'channel_id' not in db['dealIDs'].keys():
    return
  channel_id = db['dealIDs']['channel_id']
  channel = client.get_channel(channel_id)
  deal = cheapshark_deals.pull_deals()
  if deal == None:
    return
  await channel.send(deal)

keep_alive()
client.run(os.environ['TOKEN'])