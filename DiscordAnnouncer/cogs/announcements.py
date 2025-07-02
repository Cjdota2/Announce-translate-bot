import discord
from discord.ext import commands
import logging
from typing import Optional, Dict, List
import asyncio
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language"""
        try:
            translator = GoogleTranslator(source='auto', target=target_language)
            translated = await asyncio.to_thread(translator.translate, text)
            return translated
        except Exception as e:
            logger.error(f"Translation failed for {target_language}: {e}")
            return text  # Return original text if translation fails
    
    def find_channel_by_name(self, guild: discord.Guild, channel_name: str) -> Optional[discord.TextChannel]:
        """Find a channel by name in the guild"""
        for channel in guild.text_channels:
            if channel.name.lower() == channel_name.lower():
                return channel
        return None
    
    @commands.command(name='announce', aliases=['announcement'])
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, *, message: str):
        """
        Send an announcement with translations to configured language channels
        Usage: !announce <message>
        Add --everyone or @everyone in the message to ping everyone
        """
        try:
            # Get configured language channels for this guild
            language_channels = self.config.get_all_announcement_language_channels(ctx.guild.id)
            
            if not language_channels:
                await ctx.send("❌ No announcement language channels configured for this server.\n"
                             f"Use `{self.config.command_prefix}set_lang_channel` to configure channels first.")
                return
            
            # Check if @everyone should be mentioned
            mention_everyone = False
            clean_message = message
            
            if "--everyone" in message.lower() or "@everyone" in message.lower():
                mention_everyone = True
                # Clean the message by removing the --everyone flag
                clean_message = message.replace("--everyone", "").replace("@everyone", "").strip()
                logger.info(f"@everyone mention requested for announcement by {ctx.author}")
            
            await ctx.send("🔄 Translating and sending announcements...")
            
            # Create base embed
            base_embed = discord.Embed(
                title="📢 Announcement",
                color=discord.Color.blue(),
                timestamp=ctx.message.created_at
            )
            base_embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url
            )
            base_embed.set_footer(text=f"Announced in #{ctx.channel.name}")
            
            sent_count = 0
            failed_channels = []
            
            # Process each configured language
            for lang_code, channel_id in language_channels.items():
                try:
                    # Get the target channel
                    target_channel = self.bot.get_channel(channel_id)
                    
                    if not target_channel:
                        lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                        failed_channels.append(f"{lang_name} (channel not found)")
                        continue
                    
                    # Create embed for this language
                    embed = base_embed.copy()
                    lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                    
                    # Translate message if not English
                    if lang_code == 'en':
                        translated_message = clean_message
                        embed.add_field(
                            name="Message",
                            value=translated_message,
                            inline=False
                        )
                    else:
                        # Show typing indicator
                        async with target_channel.typing():
                            translated_message = await self.translate_text(clean_message, lang_code)
                        
                        embed.add_field(
                            name=f"Message ({lang_name})",
                            value=translated_message,
                            inline=False
                        )
                        
                        # Add original message as well
                        embed.add_field(
                            name="Original (English)",
                            value=clean_message,
                            inline=False
                        )
                    
                    # Send to target channel with optional @everyone mention
                    if mention_everyone:
                        await target_channel.send(content="@everyone", embed=embed)
                    else:
                        await target_channel.send(embed=embed)
                    sent_count += 1
                    logger.info(f"Announcement sent to {target_channel.name} ({lang_code})")
                    
                except Exception as e:
                    lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                    logger.error(f"Failed to send to {lang_name}: {e}")
                    failed_channels.append(f"{lang_name} (error)")
            
            # Send summary to user
            summary_embed = discord.Embed(
                title="✅ Announcement Summary",
                color=discord.Color.green()
            )
            
            summary_embed.add_field(
                name="Successfully Sent",
                value=f"{sent_count} channels",
                inline=True
            )
            
            if failed_channels:
                summary_embed.add_field(
                    name="Failed/Skipped",
                    value="\n".join(failed_channels),
                    inline=True
                )
            
            configured_langs = []
            for lang_code in language_channels.keys():
                lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                configured_langs.append(f"{lang_name} ({lang_code})")
            
            summary_embed.add_field(
                name="Configured Languages",
                value="\n".join(configured_langs) if configured_langs else "None",
                inline=False
            )
            
            # Add @everyone info to summary if used
            if mention_everyone:
                summary_embed.add_field(
                    name="Special Mention",
                    value="@everyone was pinged in all channels",
                    inline=False
                )
            
            await ctx.send(embed=summary_embed)
            
            logger.info(f"Multi-language announcement sent by {ctx.author} in {ctx.guild.name} (everyone: {mention_everyone})")
        
        except Exception as e:
            logger.error(f"Announcement error: {e}")
            await ctx.send("❌ Failed to send announcements. Please try again.")
    
    @commands.command(name='announce_everyone', aliases=['announce_all'])
    @commands.has_permissions(manage_messages=True)
    async def announce_everyone(self, ctx, *, message: str):
        """
        Send an announcement with @everyone mention to all configured channels
        Usage: !announce_everyone <message>
        """
        # Simply call the regular announce command with @everyone added
        await self.announce(ctx, message=f"{message} @everyone")
    
    @commands.command(name='set_lang_channel')
    @commands.has_permissions(manage_messages=True)
    async def set_language_channel(self, ctx, language_code: str, channel: Optional[discord.TextChannel] = None):
        """
        Set a channel for a specific language announcements
        Usage: !set_lang_channel <language_code> [#channel]
        Example: !set_lang_channel en #announcements-english
        """
        try:
            # Use current channel if not specified
            target_channel = channel or ctx.channel
            
            # Validate language code
            if language_code.lower() not in self.config.available_announcement_languages:
                available_langs = []
                for code, name in self.config.available_announcement_languages.items():
                    available_langs.append(f"`{code}` - {name}")
                
                embed = discord.Embed(
                    title="❌ Invalid Language Code",
                    description=f"Language code `{language_code}` is not available.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Available Languages",
                    value="\n".join(available_langs),
                    inline=False
                )
                embed.add_field(
                    name="Add New Language",
                    value=f"Use `{self.config.command_prefix}add_lang <code> <name>` to add new languages",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Set the channel
            self.config.set_announcement_language_channel(ctx.guild.id, language_code.lower(), target_channel.id)
            
            lang_name = self.config.available_announcement_languages[language_code.lower()]
            
            embed = discord.Embed(
                title="✅ Language Channel Set",
                description=f"**{lang_name}** (`{language_code.lower()}`) announcements will be sent to {target_channel.mention}",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            logger.info(f"Language channel set: {lang_name} -> {target_channel.name} by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Set language channel error: {e}")
            await ctx.send("❌ Failed to set language channel.")
    
    @commands.command(name='remove_lang_channel')
    @commands.has_permissions(manage_messages=True)
    async def remove_language_channel(self, ctx, language_code: str):
        """
        Remove a language channel configuration
        Usage: !remove_lang_channel <language_code>
        """
        try:
            lang_code = language_code.lower()
            
            # Check if language channel exists
            channel_id = self.config.get_announcement_language_channel(ctx.guild.id, lang_code)
            if not channel_id:
                await ctx.send(f"❌ No channel configured for language `{lang_code}`")
                return
            
            # Remove the configuration
            self.config.remove_announcement_language_channel(ctx.guild.id, lang_code)
            
            lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
            await ctx.send(f"✅ Removed {lang_name} (`{lang_code}`) announcement channel configuration")
            
        except Exception as e:
            logger.error(f"Remove language channel error: {e}")
            await ctx.send("❌ Failed to remove language channel.")
    
    @commands.command(name='add_lang')
    @commands.has_permissions(administrator=True)
    async def add_language(self, ctx, language_code: str, *, language_name: str):
        """
        Add a new language to available announcement languages
        Usage: !add_lang <code> <name>
        Example: !add_lang ja Japanese
        """
        try:
            lang_code = language_code.lower()
            
            # Check if language already exists
            if lang_code in self.config.available_announcement_languages:
                await ctx.send(f"❌ Language `{lang_code}` already exists")
                return
            
            # Add the language
            self.config.add_announcement_language(lang_code, language_name)
            
            await ctx.send(f"✅ Added new language: **{language_name}** (`{lang_code}`)")
            logger.info(f"New language added: {language_name} ({lang_code}) by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Add language error: {e}")
            await ctx.send("❌ Failed to add language.")
    
    @commands.command(name='remove_lang')
    @commands.has_permissions(administrator=True)
    async def remove_language(self, ctx, language_code: str):
        """
        Remove a language from available announcement languages
        Usage: !remove_lang <code>
        """
        try:
            lang_code = language_code.lower()
            
            # Check if language exists
            if lang_code not in self.config.available_announcement_languages:
                await ctx.send(f"❌ Language `{lang_code}` not found")
                return
            
            lang_name = self.config.available_announcement_languages[lang_code]
            
            # Remove the language
            self.config.remove_announcement_language(lang_code)
            
            await ctx.send(f"✅ Removed language: **{lang_name}** (`{lang_code}`)")
            logger.info(f"Language removed: {lang_name} ({lang_code}) by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Remove language error: {e}")
            await ctx.send("❌ Failed to remove language.")
    
    @commands.command(name='announcement_info', aliases=['announce_info'])
    async def announcement_info(self, ctx):
        """Show current announcement system configuration"""
        try:
            embed = discord.Embed(
                title="ℹ️ Announcement System Configuration",
                description="Multi-language announcement system settings",
                color=discord.Color.blue()
            )
            
            # Show configured language channels
            language_channels = self.config.get_all_announcement_language_channels(ctx.guild.id)
            
            if language_channels:
                channel_info = []
                for lang_code, channel_id in language_channels.items():
                    lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        channel_info.append(f"**{lang_name}** (`{lang_code}`) → {channel.mention}")
                    else:
                        channel_info.append(f"**{lang_name}** (`{lang_code}`) → ❌ Channel not found")
                
                embed.add_field(
                    name="Configured Language Channels",
                    value="\n".join(channel_info),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Configured Language Channels",
                    value="None configured",
                    inline=False
                )
            
            # Show available languages
            available_langs = []
            for code, name in self.config.available_announcement_languages.items():
                available_langs.append(f"`{code}` - {name}")
            
            embed.add_field(
                name="Available Languages",
                value="\n".join(available_langs),
                inline=False
            )
            
            embed.add_field(
                name="Management Commands",
                value=f"`{self.config.command_prefix}set_lang_channel <code> [#channel]` - Set language channel\n"
                      f"`{self.config.command_prefix}remove_lang_channel <code>` - Remove language channel\n"
                      f"`{self.config.command_prefix}add_lang <code> <name>` - Add new language\n"
                      f"`{self.config.command_prefix}remove_lang <code>` - Remove language",
                inline=False
            )
            
            embed.add_field(
                name="Usage",
                value=f"`{self.config.command_prefix}announce <message>` - Send to all configured channels",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Announcement info error: {e}")
            await ctx.send("❌ Failed to get announcement info.")
    
    @announce.error
    async def announce_error(self, ctx, error):
        """Error handler for announce command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Usage: `{self.config.command_prefix}announce <message>`")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Manage Messages' permission to use this command.")
        else:
            logger.error(f"Announce command error: {error}")
            await ctx.send("❌ An error occurred while processing the announcement command.")
    
    @set_language_channel.error
    async def set_language_channel_error(self, ctx, error):
        """Error handler for set_language_channel command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Usage: `{self.config.command_prefix}set_lang_channel <language_code> [#channel]`")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Manage Messages' permission to use this command.")
        else:
            logger.error(f"Set language channel command error: {error}")
            await ctx.send("❌ An error occurred while setting the language channel.")
    
    @add_language.error
    async def add_language_error(self, ctx, error):
        """Error handler for add_language command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Usage: `{self.config.command_prefix}add_lang <code> <name>`")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Administrator' permission to use this command.")
        else:
            logger.error(f"Add language command error: {error}")
            await ctx.send("❌ An error occurred while adding the language.")

async def setup(bot):
    await bot.add_cog(Announcements(bot))