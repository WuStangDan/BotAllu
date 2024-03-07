import json
import discord
from discord.ext import tasks
from new_steam_purchases import SteamPurchases

# Load Secrets
SECRETS = {}
with open('BotAlluPrivate/secrets.json', 'r') as file:
    SECRETS = json.load(file)

# Load Channel Ids
CHANNEL_IDS = {}
with open('database/channels.json', 'r') as file:
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

    @tasks.loop(seconds=60*15)  # Task that runs every 15 minutes
    async def my_background_task(self):
        channel = self.get_channel(CHANNEL_IDS['steam'])  # Your Channel ID goes here
        self.counter += 1
        check_purchases = SteamPurchases(SECRETS["STEAM_API_KEY"])
        purchases = check_purchases.run()
        if len(purchases) == 0:
            return
        for purchase in purchases:
            await channel.send(purchase)



client = MyClient()
@client.slash_command(name = "hello", description = "Say hello to the bot")
async def hello(ctx):
    print(client.counter)
    client.counter += 1
    print(client.counter)
    name = ctx.author.name
    await ctx.respond(f"Hello {name}!")

@client.slash_command(name = "steampurchaseusers", description = "List current steam users who's purchases are tracked")
async def steam_purchase_users(ctx):
    steam_purchases = SteamPurchases(SECRETS["STEAM_API_KEY"])
    output = steam_purchases.get_current_users()

    await ctx.respond(f"{output}")

client.run(SECRETS["DISCORD_TOKEN"])
