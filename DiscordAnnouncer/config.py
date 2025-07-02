import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BotConfig:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_data = self.load_config()
        
        # Bot settings
        self.command_prefix = self.config_data.get("command_prefix", "!")
        self.auto_translate_enabled = self.config_data.get("auto_translate_enabled", True)
        self.supported_languages = self.config_data.get("supported_languages", [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"
        ])
        
        # Channel settings
        self.announcement_channels = self.config_data.get("announcement_channels", {})
        self.auto_translate_channels = self.config_data.get("auto_translate_channels", [])
        
        # Multi-language announcement settings
        self.announcement_language_channels = self.config_data.get("announcement_language_channels", {})
        self.available_announcement_languages = self.config_data.get("available_announcement_languages", {
            "tl": "Tagalog",
            "id": "Indonesian", 
            "pt": "Portuguese",
            "en": "English",
            "ko": "Korean",
            "zh": "Chinese",
            "ms": "Malaysian",
            "th": "Thai"
        })
        
        # Translation settings
        self.translation_target_language = self.config_data.get("translation_target_language", "en")
        self.translation_confidence_threshold = self.config_data.get("translation_confidence_threshold", 0.8)
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
                return config
            else:
                logger.warning(f"Config file {self.config_file} not found, using defaults")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "command_prefix": "!",
            "auto_translate_enabled": True,
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            "announcement_channels": {},
            "auto_translate_channels": [],
            "translation_target_language": "en",
            "translation_confidence_threshold": 0.8
        }
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                "command_prefix": self.command_prefix,
                "auto_translate_enabled": self.auto_translate_enabled,
                "supported_languages": self.supported_languages,
                "announcement_channels": self.announcement_channels,
                "auto_translate_channels": self.auto_translate_channels,
                "announcement_language_channels": self.announcement_language_channels,
                "available_announcement_languages": self.available_announcement_languages,
                "translation_target_language": self.translation_target_language,
                "translation_confidence_threshold": self.translation_confidence_threshold
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def set_announcement_channel(self, guild_id: int, channel_id: int):
        """Set announcement channel for a guild"""
        self.announcement_channels[str(guild_id)] = channel_id
        self.save_config()
    
    def get_announcement_channel(self, guild_id: int) -> Optional[int]:
        """Get announcement channel for a guild"""
        return self.announcement_channels.get(str(guild_id))
    
    def add_auto_translate_channel(self, channel_id: int):
        """Add channel to auto-translate list"""
        if channel_id not in self.auto_translate_channels:
            self.auto_translate_channels.append(channel_id)
            self.save_config()
    
    def remove_auto_translate_channel(self, channel_id: int):
        """Remove channel from auto-translate list"""
        if channel_id in self.auto_translate_channels:
            self.auto_translate_channels.remove(channel_id)
            self.save_config()
    
    def set_announcement_language_channel(self, guild_id: int, language_code: str, channel_id: int):
        """Set announcement channel for a specific language in a guild"""
        guild_key = str(guild_id)
        if guild_key not in self.announcement_language_channels:
            self.announcement_language_channels[guild_key] = {}
        self.announcement_language_channels[guild_key][language_code] = channel_id
        self.save_config()
    
    def get_announcement_language_channel(self, guild_id: int, language_code: str) -> Optional[int]:
        """Get announcement channel for a specific language in a guild"""
        guild_key = str(guild_id)
        return self.announcement_language_channels.get(guild_key, {}).get(language_code)
    
    def get_all_announcement_language_channels(self, guild_id: int) -> Dict[str, int]:
        """Get all announcement language channels for a guild"""
        guild_key = str(guild_id)
        return self.announcement_language_channels.get(guild_key, {})
    
    def remove_announcement_language_channel(self, guild_id: int, language_code: str):
        """Remove announcement channel for a specific language"""
        guild_key = str(guild_id)
        if guild_key in self.announcement_language_channels:
            if language_code in self.announcement_language_channels[guild_key]:
                del self.announcement_language_channels[guild_key][language_code]
                self.save_config()
    
    def add_announcement_language(self, language_code: str, language_name: str):
        """Add a new language to available announcement languages"""
        self.available_announcement_languages[language_code] = language_name
        self.save_config()
    
    def remove_announcement_language(self, language_code: str):
        """Remove a language from available announcement languages"""
        if language_code in self.available_announcement_languages:
            del self.available_announcement_languages[language_code]
            # Also remove any channels using this language
            for guild_id in self.announcement_language_channels:
                if language_code in self.announcement_language_channels[guild_id]:
                    del self.announcement_language_channels[guild_id][language_code]
            self.save_config()
