import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import json
import logging
from utils.logger import setup_logging
from config import BotConfig

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Load configuration
        self.config = BotConfig()
        
        # Set up bot intents
        intents = discord.Intents.default()
        intents.message_content = True  # This requires enabling in Discord Developer Portal
        intents.guilds = True
        intents.guild_messages = True
        # Note: members intent is privileged and requires special Discord Developer Portal permissions
        
        super().__init__(
            command_prefix=self.config.command_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(
                no_category='Commands',
                commands_heading='Available Commands:'
            )
        )
    
    async def setup_hook(self):
        """Load cogs when bot starts"""
        try:
            await self.load_extension('cogs.announcements')
            await self.load_extension('cogs.translation')
            logger.info("All cogs loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Log guild information
        if self.guilds:
            for guild in self.guilds:
                logger.info(f'Connected to guild: {guild.name} (ID: {guild.id})')
        else:
            logger.info('Bot is not connected to any guilds yet')
            logger.info('To invite the bot, use the OAuth2 URL from Discord Developer Portal')
        
        # Set bot activity
        activity = discord.Game(name=f"{self.config.command_prefix}help")
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a guild"""
        logger.info(f'Bot joined guild: {guild.name} (ID: {guild.id})')
        logger.info(f'Guild has {guild.member_count} members')
        
        # Try to send a message to the system channel or first available channel
        if guild.system_channel:
            try:
                await guild.system_channel.send("👋 Hello! I'm your translation and announcement bot. Type `!help` to see my commands!")
                logger.info(f'Sent welcome message to {guild.system_channel.name}')
            except Exception as e:
                logger.error(f'Could not send welcome message: {e}')
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        logger.info(f'Bot left guild: {guild.name} (ID: {guild.id})')
    
    async def on_message(self, message):
        """Process messages and commands"""
        # Don't respond to bot messages
        if message.author.bot:
            return
        
        # Log received messages for debugging
        logger.info(f'Received message from {message.author}: {message.content[:50]}')
        
        # Process commands
        await self.process_commands(message)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Simple ping command to test bot connectivity"""
        await ctx.send(f'🏓 Pong! Bot is online and responding.')
        logger.info(f'Ping command used by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}')
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided")
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command")
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command")
        
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

def main():
    """Main function to run the bot"""
    # Get bot token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        print("Error: Please set DISCORD_BOT_TOKEN in your environment variables")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        asyncio.run(bot.start(token))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
