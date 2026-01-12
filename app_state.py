"""Application state management for BuffersBot.

This module centralizes all global state variables to make them easier to manage
and reduces the need for global variable declarations scattered throughout the code.
"""


class AppState:
    """Centralizes all application state variables."""
    
    def __init__(self):
        # Thread control
        self.stop_thread = False
        self.first_steps = False
        self.one_time_running = False
        
        # Buffer state
        self.buffers_can_buff = False
        self.buffers_buffing = False
        self.buffer_classes = []
        self.buffing_tracker = {}  # Tracks buffing state for each SP
        
        # Per-buffer can_buff flags
        self.buffers_can_buff_red = True
        self.buffers_can_buff_holy = True
        self.buffers_can_buff_blue_mage = True
        self.buffers_can_buff_dg = True
        self.buffers_can_buff_volcano = True
        self.buffers_can_buff_poss = True
        self.buffers_can_buff_war = True
        self.buffers_can_buff_cruss = True
        self.buffers_can_buff_wk = True
        self.buffers_can_buff_demon = True
        self.buffers_can_buff_wedding = True
        
        # Miniland invitation state
        self.ownercharid = 0
        self.got_invite = False
        self.got_invite2 = False
        self.got_invite3 = False
        self.cant_invite = True
        self.can_invite = False
        
        # Main character state
        self.mainleft = False
        self.main1inmini = False
        self.main2inmini = False
        self.main2left = False
        self.main3inmini = False
        self.main3left = False
        
        # Multiple mains tracking
        self.are2 = False
        self.are3 = False
        self.playerleave = False
        
        # Control flags
        self.others_stop = False
        self.others_leave = False
        
        # Timer state
        self.timer_end = False
        self.timer = None
        
        # UI state
        self.selected_button = None
        
    def reset_buffer_flags(self):
        """Reset all buffer can_buff flags to True."""
        self.buffers_can_buff_red = True
        self.buffers_can_buff_holy = True
        self.buffers_can_buff_blue_mage = True
        self.buffers_can_buff_dg = True
        self.buffers_can_buff_volcano = True
        self.buffers_can_buff_poss = True
        self.buffers_can_buff_war = True
        self.buffers_can_buff_cruss = True
        self.buffers_can_buff_wk = True
        self.buffers_can_buff_demon = True
        self.buffers_can_buff_wedding = True
    
    def reset_invite_flags(self):
        """Reset invitation flags."""
        self.got_invite = False
        self.got_invite2 = False
        self.got_invite3 = False
        self.can_invite = False
    
    def reset_main_position_flags(self):
        """Reset main character position flags."""
        self.mainleft = False
        self.main1inmini = False
        self.main2inmini = False
        self.main2left = False
        self.main3inmini = False
        self.main3left = False
    
    def buffer_start_buffing(self, sp_name):
        """Mark a specific buffer as currently buffing."""
        self.buffing_tracker[f"{sp_name}_buffing"] = True
        self.buffers_buffing = any(self.buffing_tracker.values())
    
    def buffer_stop_buffing(self, sp_name):
        """Mark a specific buffer as done buffing."""
        self.buffing_tracker[f"{sp_name}_buffing"] = False
        self.buffers_buffing = any(self.buffing_tracker.values())
    
    def all_buffers_finished(self):
        """Check if all selected buffers have finished buffing."""
        buffer_states = []
        for name in self.buffer_classes:
            state = getattr(self, f"buffers_can_buff_{name}", True)
            buffer_states.append(state)
        return all(not state for state in buffer_states)
    
    def all_mains_in_miniland(self):
        """Check if all main characters are in miniland."""
        if self.are3:
            return self.main1inmini and self.main2inmini and self.main3inmini
        elif self.are2:
            return self.main1inmini and self.main2inmini
        else:
            return self.main1inmini


# Global instance
app_state = AppState()
