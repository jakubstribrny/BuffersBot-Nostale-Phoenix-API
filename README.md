# BuffersBot - Automated Buffer Management System

A Python-based automation tool for managing buffer characters in NosTale using the Phoenix Bot API.


## Project Structure

The project has been refactored into a modular architecture for better maintainability by Ai. But its a still mess. It was coded in my dark times :D :

```
Buffer API - source - FULL/
├── main.py                 # Main application entry point and UI
├── app_state.py           # Centralized application state management
├── buffer_manager.py      # Buffer character logic and operations
├── character_manager.py   # Player/character management utilities
├── packet_handler.py      # Packet processing and player state updates
├── config_manager.py      # Configuration save/load functionality
├── utils.py               # Utility functions and constants
├── player.py              # Player class definition
├── phoenix.py             # Phoenix Bot API wrapper
├── getports.py            # Port detection for Phoenix Bot
├── classes.py             # Game-specific classes
├── PB_settings/           # Phoenix Bot configuration files
└── Buffer_icons/          # UI icons for different SP classes
```

## Module Overview

### `app_state.py` - Application State Manager
Centralizes all global variables into a single `AppState` class to avoid scattered global declarations.

**Key Features:**
- Thread control flags
- Buffer state tracking
- Invitation and position tracking
- Helper methods for state management

**Usage:**
```python
from app_state import app_state

# Access state
if app_state.buffers_can_buff:
    # Perform buffing

# Modify state
app_state.buffer_start_buffing("holy")
app_state.reset_buffer_flags()
```

### `buffer_manager.py` - Buffer Operations
Handles all buffer-related logic including skill cooldown checks, buffing sequences, and settings management.

**Key Classes/Functions:** ✅ *All Actively Used*
- `BufferManager`: Core buffer operations
  - `check_skills_ready()`: Check if skills are off cooldown (used in have_cd())
  - `prepare_for_buffing()`: Handle resting state and start buffing
  - `finish_buffing()`: Complete buffing sequence
  - `load_settings()`: Load Phoenix Bot configuration

- `create_buffer_function()`: Factory for automatic mode buffers (creates all 11 buffer functions in start())
- `create_onetime_buffer_function()`: Factory for one-time mode buffers (creates all 11 buffer functions in one_time_buff())

*This module replaced ~800 lines of repetitive inline buffer definitions!*

### `character_manager.py` - Character Management
Provides utilities for player initialization, movement, and state management.

**PlayerFactory Class:** ✅ *Actively Used*
- `create_player()`: Initialize a single player (replaces manual Player() + initializeApi() pattern)
- `create_with_thread()`: Create player with packet logger thread

**Utility Functions:** ⚠️ *Available for Future Use*
- `initialize_player_api()`: Connect to Phoenix Bot API
- `wait_for_map()`: Wait for player to reach specific map
- `join_miniland()`: Navigate to miniland
- `leave_miniland()`: Exit miniland (portal or manual)
- `wait_for_invite()`: Wait for party invitations

*Note: The utility functions are currently imported but not yet integrated due to inline code variations. They're available for future refactoring.*

### `packet_handler.py` - Packet Processing
Handles parsing and processing of Phoenix Bot API packets.

**Key Components:**
- `PacketHandler`: Processes different packet types
  - Movement packets (position updates)
  - Player information
  - Inventory data
  - Map entities
  - Skill information

- `packet_logger_loop()`: Main packet processing loop

### `config_manager.py` - Configuration Management
Handles saving and loading of application settings to JSON files.

**Usage:**
```python
from config_manager import ConfigManager

# Save configuration
config_data = {
    "delay_between_chars_seconds": "2.5",
    "x_coord": "15",
    "y_coord": "20"
}
ConfigManager.save_config(config_data, on_success_callback)

# Load configuration
config = ConfigManager.load_config(on_success_callback, on_error_callback)
```

### `utils.py` - Utility Functions
Common utilities and constants used throughout the application.

**Key Functions:** ✅ *All Actively Used*
- `get_random_delay()`: Generate randomized delays (used via getRandomDelay() wrapper)
- `get_random_portal_pos()`: Random portal coordinates (replaced ~40 manual random.randint() pairs)
- `format_timestamp()`: Format datetime for logging
- `resource_path()`: Handle PyInstaller resource paths (used for icons and assets)

**SkillConfig Class:**
Contains all configuration constants:
- Skill vnum lists
- Map IDs
- Settings file paths
- Buffer display names

## Features

### Automatic Buffing Mode
- Set buff point coordinates
- Radius-based activation
- Time-based delays
- Cycle-based delays
- Multiple main character support (up to 3)

### One-Time Buff Mode
- Single buffing cycle
- Manual or automatic miniland exit
- Support for multiple main characters

### Buffer Management
Supports 11 different specialist cards:
- Red Mage
- Holy Mage
- Blue Mage
- Dark Gunner
- Volcano
- Tide Lord
- Warrior
- Crusader
- Wild Keeper
- Demon Warrior
- Wedding Costume

### UI Features
- Character configuration
- Options management
- Configuration save/load
- Real-time status output
- Help/Instructions

## Installation

1. Ensure Python 3.7+ is installed
2. Install required dependencies:
   ```bash
   pip install customtkinter pillow pywinctl
   ```
3. Ensure Phoenix Bot is running with characters logged in

## Usage

### Basic Setup
1. Launch the application
2. Go to "Character config" tab
3. Select your main character(s)
4. Select miniland owner (usually a buffer)
5. Choose which SP cards to use
6. Assign characters to each selected SP

### Configuration
1. Go to "Options config" tab
2. Set delay between buffers
3. Choose automatic buffing mode:
   - **Time-based**: Go to miniland every X seconds
   - **Position-based**: Set buff point coordinates and radius
4. Configure delays and cycles as needed

### Running
1. Go to "Control Panel" tab
2. Click "One time buff" for single cycle
3. Click "Automatic buffing [Start]" for continuous operation
4. Monitor output in the status window

## Code Improvements

The refactoring provides several benefits:

1. **Modularity**: Each module has a single, clear responsibility
2. **Reusability**: Common functions extracted to utility modules
3. **Maintainability**: Easier to locate and modify specific functionality
4. **Testability**: Modules can be tested independently
5. **Readability**: Clear organization and documentation
6. **State Management**: Centralized state reduces bugs from global variables
7. **Error Handling**: Consistent error handling patterns

## Development Notes

### Adding New Buffers
1. Add SP name to `SkillConfig.SETTINGS_PATHS` in `utils.py`
2. Add display name to `SkillConfig.BUFFER_DISPLAY_NAMES`
3. Create corresponding `.ini` file in `PB_settings/`
4. Add icon to `Buffer_icons/`
5. Add SP to buffer tracking in `app_state.py`

### Extending Functionality
- Buffer logic: Modify `buffer_manager.py`
- Character movement: Modify `character_manager.py`
- UI changes: Modify `main.py`
- Packet handling: Modify `packet_handler.py`

## License

This project is for educational purposes. Ensure compliance with game terms of service before use.

## Credits

Created by jakubstribrny
