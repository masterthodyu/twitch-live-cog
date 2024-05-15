from redbot.core import commands, Config, checks
import aiohttp
import discord
import asyncio

class TwitchNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "twitch_channel": "",
            "discord_channel_id": None,
            "twitch_client_id": "",
            "twitch_client_secret": "",
            "access_token": "",
        }
        self.config.register_global(**default_global)

    @commands.command()
    @checks.admin()
    async def set_twitch_channel(self, ctx, twitch_channel: str):
        """Set the Twitch channel to monitor."""
        await self.config.twitch_channel.set(twitch_channel)
        await ctx.send(f"Twitch channel set to {twitch_channel}")

    @commands.command()
    @checks.admin()
    async def set_discord_channel(self, ctx, discord_channel: discord.TextChannel):
        """Set the Discord channel for notifications."""
        await self.config.discord_channel_id.set(discord_channel.id)
        await ctx.send(f"Discord channel set to {discord_channel.name}")

    @commands.command()
    @checks.admin()
    async def set_twitch_credentials(self, ctx, client_id: str, client_secret: str):
        """Set the Twitch client credentials."""
        await self.config.twitch_client_id.set(client_id)
        await self.config.twitch_client_secret.set(client_secret)
        await ctx.send("Twitch credentials set.")

    @commands.command()
    @checks.is_owner()
    async def start_notifications(self, ctx):
        """Start Twitch live notifications."""
        twitch_channel = await self.config.twitch_channel()
        discord_channel_id = await self.config.discord_channel_id()
        twitch_client_id = await self.config.twitch_client_id()
        twitch_client_secret = await self.config.twitch_client_secret()

        if not all([twitch_channel, discord_channel_id, twitch_client_id, twitch_client_secret]):
            await ctx.send("All configuration options must be set before starting notifications.")
            return

        # Fetch access token
        access_token = await self.get_twitch_access_token(twitch_client_id, twitch_client_secret)
        await self.config.access_token.set(access_token)

        await ctx.send("Twitch live notifications started.")
        await self.notify_when_live(twitch_channel, discord_channel_id, twitch_client_id, access_token)

    async def get_twitch_access_token(self, client_id, client_secret):
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                data = await resp.json()
                return data.get("access_token")

    async def notify_when_live(self, twitch_channel, discord_channel_id, client_id, access_token):
        url = f"https://api.twitch.tv/helix/streams?user_login={twitch_channel}"
        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}"
        }
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(url, headers=headers) as resp:
                    data = await resp.json()
                    if data["data"]:
                        stream_data = data["data"][0]
                        if stream_data["type"] == "live":
                            discord_channel = self.bot.get_channel(discord_channel_id)
                            await discord_channel.send(f"{twitch_channel} is live! Watch at https://www.twitch.tv/{twitch_channel}")
                            break
                await asyncio.sleep(60)  # Check every 60 seconds

def setup(bot):
    bot.add_cog(TwitchNotifier(bot))
