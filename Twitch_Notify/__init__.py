# This init is required for each cog.
# Import your main class from the cog's folder.
from .twitch_notify import TwitchNotify


def setup(bot):
    # Add the cog to the bot.
    bot.add_cog(TwitchNotify())