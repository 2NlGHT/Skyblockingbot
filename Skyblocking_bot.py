import discord
from discord.ext import commands
import aiohttp
import re

# Define the Mojang API base URL for IGN to UUID conversion
MOJANG_API_URL = "https://api.mojang.com/users/profiles/minecraft"

class HypixelAPI:
    BASE_URL = "https://api.hypixel.net/v2/"

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def shutdown(self):
        await self.session.close()

    async def get_uuid(self, ign, profile_id):
        try:
            async with self.session.get(f"{MOJANG_API_URL}/{ign}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data["id"]
                else:
                    return None
        except aiohttp.ClientResponseError as e:
            raise ValueError(f"Failed to fetch UUID for {ign}: {e}")

    async def get_coin_purse(self, uuid, profile_id):
        try:
            data = await self.get_data("skyblock/profiles", params={"key": self.api_key, "uuid": uuid, "profileid": profile_id})
            if data.get("success", False):
                profiles_data = data.get("profiles")
                if profiles_data:
                    for profile in profiles_data:
                        members_data = profile.get('members', {})
                        member_data = members_data.get(str(uuid), {})
                        coin_purse = member_data.get('currencies', {}).get('coin_purse', 0)
                        return coin_purse
            else:
                return -1
        except ValueError as e:
            raise ValueError(f"Failed to fetch coin purse for UUID {uuid}: {e}")

    async def get_data(self, endpoint, params=None):
        query_params = HTTPQueryParams.create().add("key", self.api_key)
        if params:
            for key, value in params.items():
                query_params.add(key, value)

        url = query_params.get_as_query_string(f"{self.BASE_URL}{endpoint}")

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            raise ValueError(f"Failed to fetch data from {url}: {e}")

class HTTPQueryParams:
    @staticmethod
    def create():
        return HTTPQueryParams()

    def __init__(self):
        self.params = {}

    def add(self, key, value):
        self.params[key] = value
        return self

    def get_as_query_string(self, base):
        url = base
        started_query = False

        for key, value in self.params.items():
            if not started_query:
                started_query = True
                url += "?"
            else:
                url += "&"

            url += f"{key}={value}"

        return url

# Create a new bot instance with a command prefix and intents
intents = discord.Intents.all()
intents.messages = True  # Enable message content intent

bot = commands.Bot(command_prefix='.', intents=intents)

# Define the SkyblockBot class for Discord commands
class SkyblockBot(commands.Cog):
    def __init__(self, bot, hypixel_api):
        self.bot = bot
        self.api = hypixel_api

    @commands.command(name="purse")  # Changed the command name to "purse"
    async def purse(self, ctx, ign=None):  # Changed the method name to "purse"
        """
        Retrieves the coin purse amount for a given Minecraft IGN.
        
        Usage: .purse <Minecraft IGN>
        Example: .purse Notch
        """
        if ign is None:
            await ctx.send("Please provide a Minecraft IGN.")
            return

        # Validate the format of the IGN
        if not re.match(r'^[a-zA-Z0-9_]{3,16}$', ign):
            await ctx.send("Invalid Minecraft IGN. Please provide a valid IGN.")
            return

        try:
            # Convert IGN to UUID
            uuid = await self.api.get_uuid(ign, '4e8966c4-1d0a-432c-a325-446eb0aab5bd')
            if uuid:
                # Fetch coin purse
                coin_purse = await self.api.get_coin_purse(uuid, '4e8966c4-1d0a-432c-a325-446eb0aab5bd')
                if coin_purse != -1:
                    await ctx.send(f"Coin purse for {ign}: {coin_purse}")
                else:
                    await ctx.send(f"Failed to fetch coin purse for {ign}.")
            else:
                await ctx.send(f"Failed to convert Minecraft IGN to UUID for {ign}.")
        except ValueError as e:
            await ctx.send(f"An error occurred: {e}")

# Load the SkyblockBot cog when the bot is ready
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    try:
        global hypixel_api
        hypixel_api = HypixelAPI("YOUR_API_KEY")  # Replace YOUR_API_KEY with your actual Hypixel API key
        await bot.add_cog(SkyblockBot(bot, hypixel_api))
        print("SkyblockBot cog loaded successfully")
    except Exception as e:
        print(f"Failed to load SkyblockBot cog: {e}")

# Run the bot with your Discord token
bot.run('YOUR_DISCORD_TOKEN')  # Replace YOUR_DISCORD_TOKEN with your actual Discord bot token
