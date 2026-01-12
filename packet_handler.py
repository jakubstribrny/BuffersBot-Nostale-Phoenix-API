"""Packet handling and logging for BuffersBot."""
import json
import time
from utils import SkillConfig


class PacketHandler:
    """Handles packet processing for player state updates."""
    
    @staticmethod
    def update_player_from_packet(player, json_msg):
        """Update player state based on received packet.
        
        Args:
            player: Player object to update
            json_msg: Parsed JSON message from API
        """
        packet_type = str(json_msg.get("type"))
        
        # Handle position updates from movement packets
        if packet_type in ("0", "1"):
            PacketHandler._handle_movement_packet(player, json_msg)
        
        # Handle player info query response
        elif packet_type == "16":
            PacketHandler._handle_player_info(player, json_msg)
        
        # Handle inventory query response
        elif packet_type == "17":
            PacketHandler._handle_inventory(player, json_msg)
        
        # Handle map entities query response
        elif packet_type == "19":
            PacketHandler._handle_map_entities(player, json_msg)
        
        # Handle skills info query response
        elif packet_type == "18":
            PacketHandler._handle_skills_info(player, json_msg)
    
    @staticmethod
    def _handle_movement_packet(player, json_msg):
        """Handle movement-related packets."""
        packet = str(json_msg.get("type")) + " " + json_msg.get("packet", "")
        
        # Player position update from server
        if packet.startswith("1 at " + str(player.id)):
            split_packet = packet.split()
            if len(split_packet) >= 6:
                player.pos = [int(split_packet[4]), int(split_packet[5])]
        
        # Player walk command
        elif packet.startswith("0 walk"):
            split_packet = packet.split()
            if len(split_packet) >= 4:
                player.pos = [int(split_packet[2]), int(split_packet[3])]
    
    @staticmethod
    def _handle_player_info(player, json_msg):
        """Handle player information packet."""
        player_info = json_msg.get("player_info", {})
        player.id = player_info.get("id", 0)
        player.pos[0] = player_info.get("x", 0)
        player.pos[1] = player_info.get("y", 0)
        player.map = int(player_info.get("map_id", 0))
        player.resting = bool(player_info.get("is_resting", False))
        player.name = player_info.get("name", "")
    
    @staticmethod
    def _handle_inventory(player, json_msg):
        """Handle inventory packet (check for bells)."""
        inventory = json_msg.get("inventory", {})
        for item in inventory.get("etc", []):
            if item.get("vnum") == 2072:  # Bell item vnum
                player.bell_amount = int(item.get("quantity", 0))
                player.bell_pos = int(item.get("position", 0))
    
    @staticmethod
    def _handle_map_entities(player, json_msg):
        """Handle map entities packet (check for nearby monsters)."""
        monsters = json_msg.get("monsters", [])
        player.entities_nearby = False
        
        for monster in monsters:
            monster_x = monster.get("x", 0)
            monster_y = monster.get("y", 0)
            
            if abs(monster_x - player.pos[0]) <= 10 or abs(monster_y - player.pos[1]) <= 10:
                player.entities_nearby = True
                break
    
    @staticmethod
    def _handle_skills_info(player, json_msg):
        """Handle skills information packet."""
        skills = json_msg.get("skills", [])
        
        # Reset skill existence flags
        player.buff1_exist = False
        player.buff2_exist = False
        player.buff3_exist = False
        player.buff4_exist = False
        
        for skill in skills:
            skill_vnum = skill.get("vnum")
            is_ready = skill.get("is_ready", False)
            
            if skill_vnum in SkillConfig.FIRST_SKILL:
                player.buff1_exist = True
                player.buff1_ready = is_ready
            
            if skill_vnum in SkillConfig.SECOND_SKILL:
                player.buff2_exist = True
                player.buff2_ready = is_ready
            
            if skill_vnum in SkillConfig.THIRD_SKILL:
                player.buff3_exist = True
                player.buff3_ready = is_ready
            
            if skill_vnum in SkillConfig.FOURTH_SKILL:
                player.buff4_exist = True
                player.buff4_ready = is_ready


def packet_logger_loop(player, stop_check_func):
    """Main packet logging loop for a player.
    
    Args:
        player: Player object
        stop_check_func: Function that returns True when loop should stop
    """
    while player.api.working() and not stop_check_func():
        if not player.api.empty():
            msg = player.api.get_message()
            try:
                json_msg = json.loads(msg)
                PacketHandler.update_player_from_packet(player, json_msg)
            except json.JSONDecodeError:
                pass  # Skip malformed packets
        else:
            time.sleep(0.01)
    
    player.api.close()
