import discord
from redbot.core import commands, Config, checks
import aiohttp
import asyncio

class TwitchNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(
            twitch_channel='',
            discord_channel_id=None,
            twitch_client_id='',
            twitch_client_secret='',
            twitch_access_token='',
            is_live=False
        )
        self.loop_task = self.bot.loop.create_task(self.check_twitch_live())

    async def check_twitch_live(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            twitch_channel = await self.config.twitch_channel()
            twitch_client_id = await self.config.twitch_client_id()
            twitch_access_token = await self.config.twitch_access_token()
            discord_channel_id = await self.config.discord_channel_id()
            is_live = await self.config.is_live()

            if twitch_channel and twitch_client_id and twitch_access_token and discord_channel_id:
                headers = {
                    'Client-ID': twitch_client_id,
                    'Authorization': f'Bearer {twitch_access_token}'
                }
                url = f'https://api.twitch.tv/helix/streams?user_login={twitch_channel}'

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            stream = data['data']
                            if stream and not is_live:
                                await self.config.is_live.set(True)
                                await self.notify_discord(twitch_channel, discord_channel_id)
                            elif not stream and is_live:
                                await self.config.is_live.set(False)
            await asyncio.sleep(60)  # Check every minute

    async def notify_discord(self, twitch_channel, discord_channel_id):
        channel = self.bot.get_channel(discord_channel_id)
        if channel:
            await channel.send(f"Hey everyone, {twitch_channel} is now live on Twitch! Check it out at https://www.twitch.tv/{twitch_channel}")

    @commands.group()
    @checks.admin_or_permissions(manage_guild=True)
    async def twitchnotify(self, ctx):
        """Twitch notification settings."""
        pass

    @twitchnotify.command()
    async def setchannel(self, ctx, twitch_channel: str):
        """Set the Twitch channel to monitor."""
        await self.config.twitch_channel.set(twitch_channel)
        await ctx.send(f"Twitch channel set to {twitch_channel}")

    @twitchnotify.command()
    async def setdiscord(self, ctx, channel: discord.TextChannel):
        """Set the Discord channel for notifications."""
        await self.config.discord_channel_id.set(channel.id)
        await ctx.send(f"Discord channel set to {channel.mention}")

    @twitchnotify.command()
    async def setcredentials(self, ctx, client_id: str, client_secret: str, access_token: str):
        """Set the Twitch API credentials."""
        await self.config.twitch_client_id.set(client_id)
        await self.config.twitch_client_secret.set(client_secret)
        await self.config.twitch_access_token.set(access_token)
        await ctx.send("Twitch API credentials set.")
