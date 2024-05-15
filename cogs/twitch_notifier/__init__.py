# This init is required for each cog.
# Import your main class from the cog's folder.
from .twitch_notifier import TwitchNotifier


def setup(bot):
    # Add the cog to the bot.
    bot.add_cog(TwitchNotifier(bot))