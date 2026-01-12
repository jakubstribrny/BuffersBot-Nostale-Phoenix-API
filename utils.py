"""Utility functions for BuffersBot."""
import random
import time
from datetime import datetime
import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_random_delay(min_seconds, max_seconds):
    """Generate a random delay between min and max seconds.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
        
    Returns:
        Random float between min and max
    """
    return random.uniform(min_seconds, max_seconds)


def format_timestamp(dt=None):
    """Format a datetime as a timestamp string.
    
    Args:
        dt: datetime object, defaults to now
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("[%d.%m.%Y - %H:%M:%S]")


def get_random_portal_pos():
    """Get random portal position coordinates.
    
    Returns:
        Tuple of (x, y) coordinates for portal
    """
    portal_x = random.randint(3, 4)
    portal_y = random.randint(7, 9)
    return portal_x, portal_y


def wait_with_check(duration, check_func, check_interval=0.5):
    """Wait for a duration while periodically checking a condition.
    
    Args:
        duration: Total time to wait in seconds
        check_func: Function that returns True to break early
        check_interval: How often to check the function
        
    Returns:
        True if check_func returned True, False if timed out
    """
    elapsed = 0
    while elapsed < duration:
        if check_func():
            return True
        time.sleep(check_interval)
        elapsed += check_interval
    return False


class SkillConfig:
    """Configuration for buffer skills."""
    
    # Skill vnums for different slot types
    FIRST_SKILL = [861, 871, 940, 949, 1083, 1105, 819, 897, 926, 1590, 726, 631]
    SECOND_SKILL = [873, 928, 898]
    THIRD_SKILL = [874, 931]
    FOURTH_SKILL = [875]
    
    # Map IDs
    MINILAND_MAP_ID = 20001
    
    # Settings file paths
    SETTINGS_PATHS = {
        "red": "./PB_settings/red.ini",
        "holy": "./PB_settings/holymage.ini",
        "blue_mage": "./PB_settings/blue_mage.ini",
        "dg": "./PB_settings/dg.ini",
        "volcano": "./PB_settings/volcano.ini",
        "poss": "./PB_settings/tidelord.ini",
        "war": "./PB_settings/war.ini",
        "cruss": "./PB_settings/cruss.ini",
        "wk": "./PB_settings/wk.ini",
        "demon": "./PB_settings/demon.ini",
        "wedding": "./PB_settings/wedding.ini"
    }
    
    # Display names for buffers
    BUFFER_DISPLAY_NAMES = {
        "red": "Red Mage (mage)",
        "holy": "Holy Mage (mage)",
        "blue_mage": "Blue Mage (mage)",
        "dg": "Dark Gunner (mage)",
        "volcano": "Volcano (mage)",
        "poss": "Tide Lord (mage)",
        "war": "Warrior (swordsman)",
        "cruss": "Crusader (swordsman)",
        "wk": "Wild Keeper (archer)",
        "wedding": "Wedding Costume",
        "demon": "Demon Warrior (martial artist)",
        "draconic": "Draconic Fist (martial artist)"
    }
