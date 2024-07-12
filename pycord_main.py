import json
import discord
from discord.ext import tasks
from steam_purchases import SteamPurchases
from steam_playtime import SteamPlaytime

# Load Secrets
SECRETS = {}
with open("BotAlluPrivate/secrets.json", "r") as file:
    SECRETS = json.load(file)

# Load Channel Ids
CHANNEL_IDS = {}
with open("database/channels.json", "r") as file:
    CHANNEL_IDS = json.load(file)


class MyClient(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # An attribute we can access from our task
        self.counter = 0

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        self.ready = True
        # Start the tasks to run in the background
        self.my_background_task.start()

    @tasks.loop(seconds=60 * 15)  # Task that runs every 15 minutes
    async def my_background_task(self):
        channel = self.get_channel(CHANNEL_IDS["steam"])  # Your Channel ID goes here
        self.counter += 1
        check_purchases = SteamPurchases()
        purchases = check_purchases.run()
        for purchase in purchases:
            await channel.send(purchase)

        if check_purchases.gmw_output != "":
            await channel.send(check_purchases.gmw_output)


client = MyClient()


@client.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx):
    name = ctx.author.name
    await ctx.respond(f"Hello {name}!")


@client.slash_command(
    name="steampurchaseusers",
    description="List current steam users who's purchases are tracked",
)
async def steam_purchase_users(ctx):
    await ctx.defer()
    steam_purchases = SteamPurchases()
    output = steam_purchases.get_current_users()
    await ctx.followup.send(f"{output}")


@client.slash_command(
    name="steamtwoweeksplaytime",
    description="List 2 week playtime of games played by multiple memers",
)
async def steam_two_weeks_playtime(ctx):
    await ctx.defer()
    steam_playtime = SteamPlaytime()
    output = steam_playtime.run()
    await ctx.followup.send(f"{output}")


@client.slash_command(
    name="dgmw",
    description="List games that people dgmw",
)
async def steam_dgmw(ctx):
    await ctx.defer()
    steam_purchases = SteamPurchases()
    output = steam_purchases.print_dgmw()
    if len(output) > 1990:
        loc = output[:1990].rfind(":x:")
        await ctx.followup.send(f"{output[:loc]}")
        await ctx.followup.send(f"{output[loc:3800]}")
        if len(output) > 3800:
            await ctx.followup.send(f"......")
    else:
        await ctx.followup.send(f"{output}")


client.run(SECRETS["DISCORD_TOKEN"])
