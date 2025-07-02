import discord
from discord.ext import commands
import logging
from typing import Optional
import asyncio
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    async def translate_text(self, text: str, target_language: str) -> str:
        try:
            translator = GoogleTranslator(source='auto', target=target_language)
            translated = await asyncio.to_thread(translator.translate, text)
            return translated
        except Exception as e:
            logger.error(f"Translation failed for {target_language}: {e}")
            return text

    def find_channel_by_name(self, guild: discord.Guild, channel_name: str) -> Optional[discord.TextChannel]:
        for channel in guild.text_channels:
            if channel.name.lower() == channel_name.lower():
                return channel
        return None

    @commands.command(name='announce', aliases=['announcement'])
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, *, message: str):
        try:
            language_channels = self.config.get_all_announcement_language_channels(ctx.guild.id)

            if not language_channels:
                await ctx.send("❌ No announcement language channels configured for this server.\n"
                               f"Use `{self.config.command_prefix}set_lang_channel` to configure channels first.")
                return

            mention_everyone = False
            clean_message = message

            if "--everyone" in message.lower() or "@everyone" in message.lower():
                mention_everyone = True
                clean_message = message.replace("--everyone", "").replace("@everyone", "").strip()
                logger.info(f"@everyone mention requested for announcement by {ctx.author}")

            await ctx.send("🔄 Translating and sending announcements...")

            sent_count = 0
            failed_channels = []

            for lang_code, channel_id in language_channels.items():
                try:
                    target_channel = self.bot.get_channel(channel_id)

                    if not target_channel:
                        lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                        failed_channels.append(f"{lang_name} (channel not found)")
                        continue

                    if lang_code == 'en':
                        translated_message = clean_message
                    else:
                        async with target_channel.typing():
                            translated_message = await self.translate_text(clean_message, lang_code)

                    full_message = f"**📢 Announcement**\n{translated_message}"
                    if lang_code != 'en':
                        full_message += f"\n\n*Original (English):* {clean_message}"

                    if mention_everyone:
                        await target_channel.send(f"@everyone\n{full_message}")
                    else:
                        await target_channel.send(full_message)

                    sent_count += 1
                    logger.info(f"Announcement sent to {target_channel.name} ({lang_code})")

                except Exception as e:
                    lang_name = self.config.available_announcement_languages.get(lang_code, lang_code)
                    logger.error(f"Failed to send to {lang_name}: {e}")
                    failed_channels.append(f"{lang_name} (error)")

            summary = f"✅ Announcement Summary\nSuccessfully sent to {sent_count} channels."
            if failed_channels:
                summary += f"\nFailed/Skipped: {', '.join(failed_channels)}"
            if mention_everyone:
                summary += "\n@everyone was pinged in all channels."

            await ctx.send(summary)

        except Exception as e:
            logger.error(f"Announcement error: {e}")
            await ctx.send("❌ Failed to send announcements. Please try again.")

    @commands.command(name='announce_everyone', aliases=['announce_all'])
    @commands.has_permissions(manage_messages=True)
    async def announce_everyone(self, ctx, *, message: str):
        await self.announce(ctx, message=f"{message} @everyone")

async def setup(bot):
    await bot.add_cog(Announcements(bot))
