import discord
from discord.ext import tasks
import os
from replit import db
import val
from flask_server import keep_alive
import bookclub
import cheapshark_deals
from oilers import OilersTracker
from dawncraft import McServer

# from ffxiv import StatsFFXIV, MaintenanceFFXIV
from steam_purchases import SteamPurchases
import asyncio
import datetime

intents = discord.Intents(messages=True, guilds=True)
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(str(client.user) + " is ready to rock.")
    # Init db.
    if "players" not in db.keys():
        # key: player puuid
        # value: dict containing player stats.
        db["players"] = {}

    # Used to store bookclub info.
    if "bookclub" not in db.keys():
        db["bookclub"] = {}

    # Used to store deals so that the same one isn't posted multiple times.
    if "dealIDs" not in db.keys():
        db["dealIDs"] = {}

    # Used to store info for oiler tracker.
    if "oiler_games" not in db.keys():
        db["oiler_games"] = {}

    if "ffxiv" not in db.keys():
        db["ffxiv"] = {}

    if "steam" not in db.keys():
        db["steam"] = {}

    if "mcstatus" not in db.keys():
        db["mcstatus"] = {}

    # Start cheapshark continous tasks
    cheapshark.start()
    # Start oiler tracker task.
    update_oilers.start()
    # Start ffxiv task.
    # update_ffxiv.start()
    # Start valorant leaderboard continous task.
    # update_leaderboard.start()
    # Check for Steam Purchases.
    steam_purchases.start()
    mcstatus.start()


@client.event
async def on_message(message):
    # Ignore our own messages.
    if message.author == client.user:
        return

    ###
    # Repeat
    ###
    if message.content.startswith("!BotAllu repeat "):
        if message.author.name != "Ender" or message.author.discriminator != "8157":
            print("Repeat by:")
            print(message.author)
            print("failed.")
            return
        await message.channel.send(message.content[16:])
        await message.delete()
        return

    ###
    # Valorant
    ###
    if message.content.startswith("!BotAllu help"):
        await message.channel.send("!BotAllu adduser RiotName#RiotNumber")
        return

    if message.content.startswith("!BotAllu adduser"):
        if val.add_new_player(message.content[16:]):
            await message.channel.send(
                "Added " + message.content[16:] + " to leaderboard."
            )
        else:
            # Function will return none if the string passed can't be parsed or is othwerwise invalid.
            await message.channel.send(
                "Invalid player name/tag or player already added."
            )
        return

    # Sets the current channel to the leaderboard channel.
    if message.content.startswith("!BotAllu set"):
        db["leaderboard_channel_id"] = message.channel.id
        await message.channel.send("Leaderboard channel set here!")
        return

    ###
    # BookClub
    ###
    if message.content.startswith("!bookclub "):
        if message.content[10:18] == "newgame ":
            bookclub_msg = await message.channel.send(
                'Bookclub progress will go here! Add a player with "!bookclub add PLAYERNAME".'
            )
            db["bookclub"] = {}
            db["bookclub"]["channel_id"] = message.channel.id
            db["bookclub"]["message_id"] = bookclub_msg.id
            db["bookclub"]["game_name"] = message.content[18:]
            db["bookclub"]["players"] = {}
            return
        elif message.content[10:] == "bump":
            # Delete old message.
            channel = client.get_channel(db["bookclub"]["channel_id"])
            msg = await channel.fetch_message(db["bookclub"]["message_id"])
            await msg.delete()

            db["bookclub"]["channel_id"] = message.channel.id
            bookclub_msg = await message.channel.send(bookclub.progress())
            db["bookclub"]["message_id"] = bookclub_msg.id
            await message.delete()
            return

        progress = bookclub.parse_message(message.content[10:])
        if progress == False or type(progress) != str:
            # Output of parse_message should be false for error or string for success.
            await message.channel.send(
                "Invalid command. Please delete this message and yours and try again."
            )
            return

        # Delete users message to keep channel clean.
        await message.delete()
        # Edit existing message.
        channel = client.get_channel(db["bookclub"]["channel_id"])
        msg = await channel.fetch_message(db["bookclub"]["message_id"])
        await msg.edit(content=progress)

    ###
    # Cheapshark Deals
    ###
    if message.content.startswith("!BotAllu dealset"):
        db["dealIDs"]["channel_id"] = message.channel.id
        await message.channel.send("Deals channel set here!")
        return

    ###
    # Oiler Tracker
    ###
    if message.content.startswith("!BotAllu oilers set"):
        db["oiler_games"]["channel_id"] = message.channel.id
        await message.channel.send("Oiler tracker set here.")

    ###
    # FFXIV
    ###
    if message.content.startswith("!BotAllu ffxiv set"):
        db["ffxiv"]["channel_id"] = message.channel.id
        embed = discord.Embed(title="The Fellas")
        await message.channel.send(embed=embed)
        await message.channel.send("FFXIV stats set here.")

    if message.content.startswith("!BotAllu ffxiv news set"):
        db["ffxiv"]["maintenance_channel_id"] = message.channel.id
        await message.channel.send("FFXIV news set here.")

    if message.content.startswith("!BotAllu testimage"):
        image_embed = discord.Embed(title="Group Photo")
        # image_embed.set_image(url='https://i.imgur.com/y6gHPY7.png')
        image_embed.set_image(url="https://i.imgur.com/O7Bm19c.png")
        await message.channel.send(embed=image_embed)

    ###
    # Steam Purchases
    ###
    if message.content.startswith("!BotAllu steam purchases set"):
        db["steam"]["channel_id"] = message.channel.id
        await message.channel.send("Steam purchases set here.")
        return
    if message.content.startswith("!BotAllu purchases add "):
        check_steam_purchases = SteamPurchases(db["steam"]["steamids"])
        steam_id = str(message.content).split(" ")
        if len(steam_id) != 4:
            await message.channel.send("You dun goofed something")
            return
        status = check_steam_purchases.add_steam_id(steam_id[-1])
        if "message_id" not in db["steam"]:
            # Post new message and delete users.
            message_id = await message.channel.send(status)
            db["steam"]["message_id"] = message_id.id
            await message.delete()
        else:
            # Delete previous tracking list and users message, and post updated list.
            channel = client.get_channel(db["steam"]["channel_id"])
            msg = await channel.fetch_message(db["steam"]["message_id"])
            message_id = await message.channel.send(status)
            db["steam"]["message_id"] = message_id.id
            await message.delete()
            await msg.delete()

    ###
    # Minecraft
    ###
    if message.content.startswith("!BotAllu mcstatus set"):
        db["mcstatus"]["channel_id"] = message.channel.id
        await message.channel.send("MC Status set here.")

@tasks.loop(seconds=4000)
async def update_leaderboard():
    if "leaderboard_channel_id" not in db.keys():
        return
    channel_id = db["leaderboard_channel_id"]
    msg_generator = client.get_channel(channel_id).history(limit=1)
    # Flatten generator output into list.
    msg = [i async for i in msg_generator]
    msg = msg[0]
    # channel = client.get_channel(channel_id)
    leaderboard = val.generate_leaderboard()
    if msg.author == client.user:
        await msg.edit(content=leaderboard)


@tasks.loop(seconds=4100)
async def cheapshark():
    if "dealIDs" not in db.keys():
        return
    if "channel_id" not in db["dealIDs"].keys():
        return
    channel_id = db["dealIDs"]["channel_id"]
    channel = client.get_channel(channel_id)
    deal = cheapshark_deals.pull_deals()
    if deal == None:
        return
    await channel.send(deal)


@tasks.loop(seconds=1800)
async def update_oilers():
    # print('oilers start: ' + str(datetime.datetime.now()))
    if "oiler_games" not in db.keys():
        return
    if "channel_id" not in db["oiler_games"]:
        return
    channel_id = db["oiler_games"]["channel_id"]
    channel = client.get_channel(channel_id)
    oiler_tracker = OilersTracker(db["oiler_games"])
    await oiler_tracker.run(channel)
    # print('oilers end: ' + str(datetime.datetime.now()))


@tasks.loop(seconds=3600)
async def update_ffxiv():
    if "ffxiv" not in db.keys():
        return
    if "channel_id" not in db["ffxiv"]:
        return
    if "maintenance_channel_id" not in db["ffxiv"]:
        return

    # Get maintenance news.
    news = MaintenanceFFXIV(db["ffxiv"])
    latest = news.get_maintenance()
    if latest is not None:
        maint_channel_id = db["ffxiv"]["maintenance_channel_id"]
        maint_channel = client.get_channel(maint_channel_id)
        await maint_channel.send(latest)

    # Generate stats.
    ffxiv = StatsFFXIV()
    names_id = ffxiv.get_names_and_id()
    for name, id in names_id.items():
        # API has a 1 second limit.
        await asyncio.sleep(3)
        ffxiv.get_highest_level_job(name, id)
    stats = ffxiv.generate_stats_table()
    await ffxiv.upload_group_photo()
    # Overwrite previous message.
    channel_id = db["ffxiv"]["channel_id"]
    msg = await client.get_channel(channel_id).history(limit=2).flatten()
    stats_msg = msg[0]
    embed_msg = msg[1]
    if stats_msg.author == client.user:
        await stats_msg.edit(content=stats)
    await asyncio.sleep(2)
    if embed_msg.author == client.user:
        embed = discord.Embed(title="The Fellas")
        embed.set_image(url=ffxiv.group_photo_url)
        await embed_msg.edit(embed=embed)


@tasks.loop(seconds=86400)
async def steam_purchases():
    if "steam" not in db.keys():
        return
    if "channel_id" not in db["steam"]:
        return
    if "steamids" not in db["steam"]:
        db["steam"]["steamids"] = {}
    channel_id = db["steam"]["channel_id"]
    channel = client.get_channel(channel_id)
    check_steam_purchases = SteamPurchases(db["steam"]["steamids"])
    purchases = check_steam_purchases.run()
    if len(purchases) == 0:
        return
    for purchase in purchases:
        await channel.send(purchase)

@tasks.loop(seconds=1800)
async def mcstatus():
    if "mcstatus" not in db.keys():
        return
    if "channel_id" not in db["mcstatus"]:
        return
    server = McServer()
    channel_name = server.get_status()
    mc_channel = client.get_channel(db["mcstatus"]["channel_id"])
    await mc_channel.edit(name=channel_name)


keep_alive()
client.run(os.environ["TOKEN"])
