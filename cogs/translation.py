import discord
from discord.ext import commands
import asyncio
import logging
from deep_translator import GoogleTranslator
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class Translation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        
        # Language code mapping for better user experience
        self.language_aliases = {
            'english': 'en',
            'spanish': 'es',
            'french': 'fr',
            'german': 'de',
            'italian': 'it',
            'portuguese': 'pt',
            'russian': 'ru',
            'japanese': 'ja',
            'korean': 'ko',
            'chinese': 'zh',
            'mandarin': 'zh',
            'hindi': 'hi',
            'arabic': 'ar',
            'dutch': 'nl',
            'polish': 'pl',
            'turkish': 'tr'
        }
    
    def get_language_code(self, language: str) -> Optional[str]:
        """Convert language name to code"""
        language = language.lower().strip()
        
        # Get supported languages from deep-translator
        try:
            supported_langs = GoogleTranslator().get_supported_languages()
            
            # Check if it's already a valid code
            if language in supported_langs:
                return language
            
            # Check aliases
            if language in self.language_aliases:
                return self.language_aliases[language]
            
            return None
        except Exception:
            # Fallback to aliases if API fails
            return self.language_aliases.get(language)
    
    @commands.command(name='translate', aliases=['tr'])
    async def translate_command(self, ctx, target_lang: str, *, text: str):
        """
        Translate text to target language
        Usage: !translate <target_language> <text>
        Example: !translate spanish Hello world
        """
        try:
            # Get language code
            target_code = self.get_language_code(target_lang)
            
            if not target_code:
                await ctx.send(f"❌ Unknown language: `{target_lang}`\n"
                             f"Use `{self.config.command_prefix}languages` to see supported languages.")
                return
            
            # Show typing indicator
            async with ctx.typing():
                # Create translator with target language
                translator = GoogleTranslator(source='auto', target=target_code)
                
                # Translate the text
                translated = await asyncio.to_thread(
                    translator.translate,
                    text
                )
                
                # Create embed
                embed = discord.Embed(
                    title="🌐 Translation",
                    color=discord.Color.green()
                )
                
                # Get language name
                target_lang_name = target_lang.title()
                
                embed.add_field(
                    name="Original",
                    value=text[:1000] + ("..." if len(text) > 1000 else ""),
                    inline=False
                )
                
                embed.add_field(
                    name=f"Translation ({target_lang_name})",
                    value=translated[:1000] + ("..." if len(translated) > 1000 else ""),
                    inline=False
                )
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
                
                logger.info(f"Translation: -> {target_lang_name} by {ctx.author}")
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            await ctx.send("❌ Translation failed. Please try again later.")
    
    @commands.command(name='detect', aliases=['detect_lang'])
    async def detect_language(self, ctx, *, text: str):
        """
        Detect the language of given text
        Usage: !detect <text>
        """
        try:
            async with ctx.typing():
                # Simple detection by trying to translate from auto
                translator = GoogleTranslator(source='auto', target='en')
                
                # For now, we'll just acknowledge the request
                embed = discord.Embed(
                    title="🔍 Language Detection",
                    description="Language detection is currently simplified in this version.",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Text",
                    value=text[:500] + ("..." if len(text) > 500 else ""),
                    inline=False
                )
                
                embed.add_field(
                    name="Note",
                    value="Use the translate command to automatically detect and translate text.",
                    inline=False
                )
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            await ctx.send("❌ Language detection failed. Please try again.")
    
    @commands.command(name='languages', aliases=['langs'])
    async def list_languages(self, ctx):
        """List supported languages"""
        try:
            # Create embed with popular languages
            embed = discord.Embed(
                title="🌐 Supported Languages",
                description="Here are some popular supported languages:",
                color=discord.Color.blue()
            )
            
            popular_langs = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese',
                'hi': 'Hindi',
                'ar': 'Arabic',
                'nl': 'Dutch',
                'pl': 'Polish',
                'tr': 'Turkish'
            }
            
            lang_list = []
            for code, name in popular_langs.items():
                lang_list.append(f"`{code}` - {name}")
            
            # Split into two columns
            mid = len(lang_list) // 2
            col1 = '\n'.join(lang_list[:mid])
            col2 = '\n'.join(lang_list[mid:])
            
            embed.add_field(name="Languages (1)", value=col1, inline=True)
            embed.add_field(name="Languages (2)", value=col2, inline=True)
            
            embed.add_field(
                name="Usage",
                value=f"Use `{self.config.command_prefix}translate <language> <text>` to translate",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Languages list error: {e}")
            await ctx.send("❌ Failed to list languages.")
    
    @commands.command(name='auto_translate')
    @commands.has_permissions(manage_messages=True)
    async def toggle_auto_translate(self, ctx, channel: Optional[discord.TextChannel] = None):
        """
        Toggle auto-translation for a channel
        Usage: !auto_translate [#channel]
        """
        try:
            target_channel = channel or ctx.channel
            
            if target_channel.id in self.config.auto_translate_channels:
                self.config.remove_auto_translate_channel(target_channel.id)
                await ctx.send(f"✅ Auto-translation disabled for {target_channel.mention}")
                logger.info(f"Auto-translate disabled for {target_channel.name} by {ctx.author}")
            else:
                self.config.add_auto_translate_channel(target_channel.id)
                await ctx.send(f"✅ Auto-translation enabled for {target_channel.mention}")
                logger.info(f"Auto-translate enabled for {target_channel.name} by {ctx.author}")
        
        except Exception as e:
            logger.error(f"Error toggling auto-translate: {e}")
            await ctx.send("❌ Failed to toggle auto-translation.")
    
    @commands.command(name='auto_translate_status')
    async def auto_translate_status(self, ctx):
        """
        Show auto-translation status for current server
        Usage: !auto_translate_status
        """
        try:
            embed = discord.Embed(
                title="🔄 Auto-Translation Status",
                color=discord.Color.blue()
            )
            
            if self.config.auto_translate_channels:
                enabled_channels = []
                for channel_id in self.config.auto_translate_channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel and channel.guild.id == ctx.guild.id:
                        enabled_channels.append(channel.mention)
                    elif channel_id:
                        enabled_channels.append(f"Unknown channel (ID: {channel_id})")
                
                if enabled_channels:
                    embed.add_field(
                        name="Enabled Channels",
                        value="\n".join(enabled_channels),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Enabled Channels",
                        value="None in this server",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Enabled Channels",
                    value="None",
                    inline=False
                )
            
            embed.add_field(
                name="Current Channel",
                value=f"{ctx.channel.mention} - {'✅ Enabled' if ctx.channel.id in self.config.auto_translate_channels else '❌ Disabled'}",
                inline=False
            )
            
            embed.add_field(
                name="How it works",
                value="Auto-translation detects non-English messages and translates them to English automatically.",
                inline=False
            )
            
            embed.add_field(
                name="Toggle Command",
                value=f"Use `{self.config.command_prefix}auto_translate` to enable/disable for current channel",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Auto-translate status error: {e}")
            await ctx.send("❌ Failed to get auto-translation status.")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-translate messages in designated channels"""
        # Ignore bot messages and commands
        if message.author.bot or message.content.startswith(self.config.command_prefix):
            return
        
        # Skip empty messages or messages with just whitespace
        if not message.content.strip():
            return
        
        # Check if auto-translation is enabled for this channel
        logger.debug(f"Checking auto-translate for channel {message.channel.id}, enabled channels: {self.config.auto_translate_channels}")
        
        if message.channel.id not in self.config.auto_translate_channels:
            return
        
        logger.info(f"Auto-translating message from {message.author} in {message.channel.name}: {message.content[:50]}")
        
        try:
            # Detect source language first
            from deep_translator import single_detection
            
            # Try to detect the language
            try:
                detected_lang = await asyncio.to_thread(
                    single_detection,
                    message.content,
                    api_key=None
                )
                logger.info(f"Detected language: {detected_lang}")
            except Exception as detect_error:
                logger.warning(f"Language detection failed: {detect_error}, proceeding with auto-detection")
                detected_lang = 'auto'
            
            # Skip translation if message is already in English
            if detected_lang == 'en':
                logger.info("Message already in English, skipping translation")
                return
            
            # Auto-translate to English
            translator = GoogleTranslator(source='auto', target='en')
            
            translated = await asyncio.to_thread(
                translator.translate,
                message.content
            )
            
            logger.info(f"Translation result: {translated[:50]}")
            
            # Only send translation if it's significantly different from original
            original_clean = message.content.lower().strip()
            translated_clean = translated.lower().strip()
            
            # Check if translation is actually different (more than just case/whitespace)
            if translated_clean != original_clean and len(translated_clean) > 0:
                # Also check if it's not just punctuation differences
                import re
                original_words = re.findall(r'\b\w+\b', original_clean)
                translated_words = re.findall(r'\b\w+\b', translated_clean)
                
                # Only translate if there are actual word differences
                if original_words != translated_words:
                    embed = discord.Embed(
                        title="🔄 Auto Translation",
                        color=discord.Color.orange()
                    )
                    
                    # Show detected language if available
                    lang_display = detected_lang if detected_lang != 'auto' else 'Unknown'
                    
                    embed.add_field(
                        name=f"Original ({lang_display})",
                        value=message.content[:500] + ("..." if len(message.content) > 500 else ""),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Translation (English)",
                        value=translated[:500] + ("..." if len(translated) > 500 else ""),
                        inline=False
                    )
                    
                    embed.set_footer(text=f"From {message.author.display_name}")
                    
                    await message.channel.send(embed=embed)
                    logger.info(f"Auto-translation sent for message from {message.author}")
                else:
                    logger.info("Translation too similar to original, skipping")
            else:
                logger.info("No significant translation difference, skipping")
        
        except Exception as e:
            logger.error(f"Auto-translation error: {e}")
            # Send a simple error message to help debug
            try:
                await message.channel.send(f"⚠️ Auto-translation failed: {str(e)[:100]}")
            except:
                pass
    
    @translate_command.error
    async def translate_error(self, ctx, error):
        """Error handler for translate command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Usage: `{self.config.command_prefix}translate <language> <text>`")
        else:
            logger.error(f"Translate command error: {error}")
            await ctx.send("❌ An error occurred while processing the translation command.")
    
    @toggle_auto_translate.error
    async def auto_translate_error(self, ctx, error):
        """Error handler for auto_translate command"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need 'Manage Messages' permission to use this command.")
        else:
            logger.error(f"Auto-translate command error: {error}")
            await ctx.send("❌ An error occurred while toggling auto-translation.")

async def setup(bot):
    await bot.add_cog(Translation(bot))