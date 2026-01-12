"""Buffer management functionality for BuffersBot."""
import time
import os
from app_state import app_state
from utils import get_random_delay, SkillConfig


class BufferManager:
    """Manages buffer character operations."""
    
    @staticmethod
    def check_skills_ready(player):
        """Check if all buff skills are ready (not on cooldown).
        
        Args:
            player: Player object
            
        Returns:
            True if all skills are on cooldown, False otherwise
        """
        player.api.query_skills_info()
        time.sleep(0.1)
        
        buff_skills_ready = []
        
        if player.buff1_exist:
            buff_skills_ready.append(player.buff1_ready)
        if player.buff2_exist:
            buff_skills_ready.append(player.buff2_ready)
        if player.buff3_exist:
            buff_skills_ready.append(player.buff3_ready)
        if player.buff4_exist:
            buff_skills_ready.append(player.buff4_ready)
        
        return all(not buff_ready for buff_ready in buff_skills_ready)
    
    @staticmethod
    def prepare_for_buffing(player, sp_name):
        """Prepare player for buffing (handle resting state, start bot).
        
        Args:
            player: Player object
            sp_name: Name of the SP
        """
        app_state.buffer_start_buffing(sp_name)
        
        # Handle resting state
        if player.resting:
            time.sleep(get_random_delay(0.3, 0.7))
            player.api.send_packet(f"rest 1 1 {player.id}")
            player.resting = False
            time.sleep(get_random_delay(0.3, 0.7))
        
        # Start bot and inject fake entity packet
        player.api.start_bot()
        player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")
    
    @staticmethod
    def finish_buffing(player, sp_name, delay_value):
        """Finish buffing process (wait for cooldown, stop bot).
        
        Args:
            player: Player object
            sp_name: Name of the SP
            delay_value: Delay between buffers
        """
        # Wait for all skills to be on cooldown
        while not BufferManager.check_skills_ready(player):
            time.sleep(0.5)
        
        player.api.stop_bot()
        time.sleep(0.1)
        time.sleep(delay_value)
        app_state.buffer_stop_buffing(sp_name)
    
    @staticmethod
    def load_settings(player, sp_name):
        """Load Phoenix Bot settings for a specific SP.
        
        Args:
            player: Player object
            sp_name: Name of the SP
        """
        settings_path = os.path.abspath(SkillConfig.SETTINGS_PATHS.get(sp_name, ""))
        if settings_path and os.path.exists(settings_path):
            player.api.load_settings(settings_path)
            time.sleep(1)
    
    @staticmethod
    def wait_for_buff_signal(sp_name, check_interval=0.5):
        """Wait for buffer to receive the signal to start buffing.
        
        Args:
            sp_name: Name of the SP
            check_interval: How often to check (seconds)
        """
        # Wait for specific buffer flag
        can_buff_attr = f"buffers_can_buff_{sp_name}"
        while not getattr(app_state, can_buff_attr, False) and not app_state.stop_thread:
            time.sleep(check_interval)
        
        if app_state.stop_thread:
            return False
        
        # Wait for global buff signal
        while not app_state.buffers_can_buff and not app_state.stop_thread:
            time.sleep(check_interval)
        
        # Wait while another buffer is actively buffing
        while app_state.buffers_buffing and not app_state.stop_thread:
            time.sleep(get_random_delay(0.3, 0.7))
        
        return not app_state.stop_thread


def create_buffer_function(sp_name, error_message):
    """Factory function to create buffer functions for automatic mode.
    
    Args:
        sp_name: Name of the SP
        error_message: Error message to show if not in miniland
        
    Returns:
        Buffer function for the specified SP
    """
    def buffer_function(player, delay_value, show_error_callback, stop_callback):
        BufferManager.load_settings(player, sp_name)
        player.api.query_player_information()
        time.sleep(0.1)
        
        while player.map == SkillConfig.MINILAND_MAP_ID:
            if app_state.stop_thread:
                return
            
            if not BufferManager.wait_for_buff_signal(sp_name):
                return
            
            BufferManager.prepare_for_buffing(player, sp_name)
            BufferManager.finish_buffing(player, sp_name, delay_value)
            
            # Mark this buffer as done
            setattr(app_state, f"buffers_can_buff_{sp_name}", False)
            
            if app_state.stop_thread:
                return
        
        show_error_callback(error_message)
        stop_callback()
        
    return buffer_function


def create_onetime_buffer_function(sp_name, error_message):
    """Factory function to create buffer functions for one-time mode.
    
    Args:
        sp_name: Name of the SP
        error_message: Error message to show if not in miniland
        
    Returns:
        One-time buffer function for the specified SP
    """
    def buffer_function(player, delay_value, show_error_callback):
        BufferManager.load_settings(player, sp_name)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        
        if player.map == SkillConfig.MINILAND_MAP_ID:
            # Wait for global buff signal
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            
            # Wait while another buffer is buffing
            while app_state.buffers_buffing:
                time.sleep(get_random_delay(0.3, 0.7))
            
            BufferManager.prepare_for_buffing(player, sp_name)
            time.sleep(1)
            BufferManager.finish_buffing(player, sp_name, delay_value)
            return
        else:
            show_error_callback(error_message)
    
    return buffer_function
