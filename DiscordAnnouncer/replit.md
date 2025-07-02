# Discord Translation & Announcement Bot

## Overview

This is a Discord bot built with Python and discord.py that provides announcement capabilities and automatic translation features. The bot uses a modular architecture with cogs for different functionalities, JSON-based configuration management, and comprehensive logging.

## System Architecture

### Core Components
- **Main Bot Class**: `DiscordBot` extends `commands.Bot` with custom configuration and cog loading
- **Configuration System**: JSON-based configuration with runtime access through `BotConfig` class
- **Cog-based Architecture**: Modular command organization using discord.py cogs
- **Logging System**: Structured logging with file and console output

### Technology Stack
- **Runtime**: Python 3.8+
- **Discord Library**: discord.py
- **Translation Service**: Google Translate API (deep-translator)
- **Configuration**: JSON files
- **Environment Management**: python-dotenv

## Key Components

### Bot Core (`bot.py`)
- **Purpose**: Main bot initialization and cog loading
- **Architecture Decision**: Uses discord.py's commands extension for structured command handling
- **Intents Configuration**: Enables message content, guilds, and members intents for full functionality

### Configuration Management (`config.py` & `config.json`)
- **Purpose**: Centralized configuration with runtime access
- **Architecture Decision**: JSON-based configuration for easy editing without code changes
- **Features**: 
  - Per-server announcement channel settings
  - Auto-translation channel configuration
  - Language support configuration
  - Translation confidence thresholds

### Announcements Cog (`cogs/announcements.py`)
- **Purpose**: Handle multi-language announcement commands and channel management
- **Architecture Decision**: Permission-based command access using discord.py decorators
- **Features**:
  - Multi-language announcement system with automatic translation
  - Supports English, Korean, Portuguese (Brazilian), and Indonesian
  - Channel-specific translations (announcements-english, announcements-korean, etc.)
  - Rich embed formatting with original and translated messages
  - Graceful handling of missing channels
  - Author attribution and timestamp tracking

### Translation Cog (`cogs/translation.py`)
- **Purpose**: Provide translation services and language detection
- **Architecture Decision**: Uses Google Translate API for broad language support
- **Features**:
  - Support for 100+ languages
  - Language name and code aliases for user convenience
  - Auto-detection of source languages
  - Channel-specific auto-translation

### Logging Utility (`utils/logger.py`)
- **Purpose**: Centralized logging configuration
- **Architecture Decision**: File-based logging with daily rotation and console output
- **Features**:
  - Structured log format with timestamps
  - Separate log files by date
  - Configurable log levels
  - Discord.py noise reduction

## Data Flow

### Configuration Loading
1. Bot initialization loads `config.json`
2. Configuration validates and provides defaults for missing values
3. Runtime configuration access through `BotConfig` instance

### Command Processing
1. Discord message received
2. Command prefix detection and parsing
3. Permission validation (for restricted commands)
4. Command execution in appropriate cog
5. Response sent to Discord channel

### Translation Workflow
1. Text input received (command or auto-translation trigger)
2. Language detection (if source not specified)
3. Google Translate API call
4. Response formatting and delivery

## External Dependencies

### Required Services
- **Discord Bot Token**: Required for bot authentication
- **Google Translate API**: Used through googletrans library (no API key required)

### Python Packages
- `discord.py`: Discord API interaction
- `googletrans==4.0.0rc1`: Translation services
- `python-dotenv`: Environment variable management

## Deployment Strategy

### Environment Setup
- Environment variables loaded from `.env` file
- Bot token stored securely in environment variables
- Configuration files editable without code changes

### Runtime Requirements
- Python 3.8+ runtime environment
- Network access for Discord API and Google Translate
- File system access for logging and configuration

### Scalability Considerations
- Stateless design allows for easy horizontal scaling
- JSON configuration enables per-deployment customization
- Modular cog architecture supports feature addition/removal

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

- July 02, 2025: **Enhanced Bot Features**
  - Fixed auto-translate feature with improved language detection and smarter filtering
  - Added @everyone support for announcements (use @everyone or --everyone in message)
  - Added dedicated !announce_everyone command for convenience
  - Enhanced logging and debugging for auto-translate functionality
  - Added !auto_translate_status command to check configuration
  - Improved bot intents configuration for better functionality
- July 02, 2025: **Configurable Multi-Language Announcements**
  - Redesigned announcement system to be fully configurable
  - Added 8 default languages: Tagalog, Indonesian, Portuguese, English, Korean, Chinese, Malaysian, Thai
  - Implemented dynamic language-to-channel mapping system
  - Added comprehensive management commands: !set_lang_channel, !remove_lang_channel, !add_lang, !remove_lang
  - Enhanced configuration system with persistent language channel storage
  - Removed hardcoded channel names - now fully user-configurable
  - Added graceful handling for missing channels and translation failures
- July 02, 2025: **Bot Deployment Fixed**
  - Fixed dependency conflicts by switching from googletrans to deep-translator
  - Installed required packages: discord.py, python-dotenv, deep-translator
  - Updated translation cog to work with new library API
  - Created .env file for bot token configuration
  - Fixed privileged intents issue by removing members intent
  - Bot successfully connected to Discord and running
- July 02, 2025: Initial setup