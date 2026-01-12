"""Character and player management for BuffersBot."""
import time
import threading
import phoenix
import getports
from player import Player
from app_state import app_state
from packet_handler import packet_logger_loop
from utils import get_random_delay, get_random_portal_pos, SkillConfig


def initialize_player_api(player, show_error_callback=None):
    """Initialize API connection for a player.
    
    Args:
        player: Player object
        show_error_callback: Optional callback for error messages
        
    Returns:
        True if successful, False otherwise
    """
    try:
        player.port = getports.returnCorrectPort(player.name)
        if player.port is None:
            raise ValueError("Port returned is None")
        player.api = phoenix.Api(player.port)
        if not hasattr(player.api, 'working'):
            raise TypeError("Player.api is not initialized correctly with Api object")
        print(f"Initialized API for player {player.name} on port {player.port}")
        return True
    except (TypeError, ValueError) as e:
        if show_error_callback:
            show_error_callback(f"Error initializing API for {player.name}: {str(e)}")
        return False


def wait_for_map(player, target_map_id, check_interval=0.2):
    """Wait until player is in a specific map.
    
    Args:
        player: Player object
        target_map_id: Map ID to wait for
        check_interval: How often to check
        
    Returns:
        True if successful, False if stopped
    """
    while player.map != target_map_id and not app_state.stop_thread:
        player.api.query_player_information()
        time.sleep(check_interval)
    return not app_state.stop_thread


def leave_miniland(player, use_portal=True):
    """Have player leave miniland.
    
    Args:
        player: Player object
        use_portal: If True, walk to portal. If False, wait for manual leave
        
    Returns:
        True if successful, False if stopped
    """
    if use_portal:
        # Walk to portal and leave
        portal_x, portal_y = get_random_portal_pos()
        player.api.player_walk(portal_x, portal_y)
        player.api.pets_walk(portal_x, portal_y)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.2)
        
        # Keep trying until we leave
        while player.map == SkillConfig.MINILAND_MAP_ID and not app_state.stop_thread:
            time.sleep(get_random_delay(0.3, 0.7))
            portal_x, portal_y = get_random_portal_pos()
            player.api.player_walk(portal_x, portal_y)
            player.api.pets_walk(portal_x, portal_y)
            time.sleep(0.5)
            player.api.query_player_information()
    else:
        # Wait for player to leave manually
        player.api.query_player_information()
        time.sleep(0.1)
        
        while player.map == SkillConfig.MINILAND_MAP_ID and not app_state.stop_thread:
            time.sleep(get_random_delay(0.3, 0.8))
            player.api.query_player_information()
            time.sleep(0.5)
    
    return not app_state.stop_thread


def join_miniland(player):
    """Have player join the owner's miniland.
    
    Args:
        player: Player object
        
    Returns:
        True if successful, False if stopped
    """
    time.sleep(get_random_delay(0.5, 0.8))
    player.api.send_packet(f"#mjoin^1^{app_state.ownercharid}^2")
    time.sleep(0.1)
    player.api.query_player_information()
    time.sleep(0.1)
    
    return wait_for_map(player, SkillConfig.MINILAND_MAP_ID)


def wait_for_invite(invite_flag_name, timeout=None):
    """Wait for an invite flag to be set.
    
    Args:
        invite_flag_name: Name of the invite flag ('got_invite', 'got_invite2', etc.)
        timeout: Optional timeout in seconds
        
    Returns:
        True if invite received, False if cancelled or timed out
    """
    start_time = time.time()
    
    while not getattr(app_state, invite_flag_name):
        if app_state.cant_invite or app_state.stop_thread:
            return False
        if timeout and (time.time() - start_time) > timeout:
            return False
        time.sleep(0.5)
    
    return True


def start_player_threads(player):
    """Start packet logger thread for a player.
    
    Args:
        player: Player object
        
    Returns:
        Thread object
    """
    thread = threading.Thread(
        target=packet_logger_loop,
        args=(player, lambda: app_state.stop_thread)
    )
    thread.start()
    return thread


class PlayerFactory:
    """Factory for creating and initializing players."""
    
    @staticmethod
    def create_player(name, show_error_callback=None):
        """Create and initialize a player.
        
        Args:
            name: Player name
            show_error_callback: Optional error callback
            
        Returns:
            Initialized Player object or None on failure
        """
        player = Player()
        player.name = name
        
        if initialize_player_api(player, show_error_callback):
            return player
        return None
    
    @staticmethod
    def create_with_thread(name, show_error_callback=None):
        """Create player and start its packet logger thread.
        
        Args:
            name: Player name
            show_error_callback: Optional error callback
            
        Returns:
            Tuple of (player, thread) or (None, None) on failure
        """
        player = PlayerFactory.create_player(name, show_error_callback)
        if player:
            thread = start_player_threads(player)
            return player, thread
        return None, None
