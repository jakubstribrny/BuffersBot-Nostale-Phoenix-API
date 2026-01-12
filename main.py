import phoenix
from time import sleep
import json
import time
import threading
import getports
import classes as cl
import random
from player import Player
import customtkinter
import sys
import os
from PIL import Image
from datetime import datetime
from customtkinter import filedialog
import requests

# Import refactored modules
from app_state import app_state
from buffer_manager import BufferManager, create_buffer_function, create_onetime_buffer_function
from character_manager import PlayerFactory, join_miniland, leave_miniland, wait_for_invite, wait_for_map
from packet_handler import packet_logger_loop
from config_manager import ConfigManager
from utils import get_random_delay, get_random_portal_pos, resource_path, SkillConfig

# Function to show an error message in a GUI window
def show_error_message(message):
    test = customtkinter.CTk()
    test.iconbitmap(resource_path("icon.ico"))
    test.title("BAPI Error")
    labelerror = customtkinter.CTkLabel(test, text=message)
    labelerror.pack(padx=20, pady=20)
    test.mainloop()

def initializeApi(player):
    """Initialize API - now uses character_manager internally."""
    try:
        player.port = getports.returnCorrectPort(player.name)
        if player.port is None:
            raise ValueError("Port returned is None")
        player.api = phoenix.Api(player.port)
        if not hasattr(player.api, 'working'):
            raise TypeError("Player.api is not initialized correctly with Api object")
        print(f"Initialized API for player {player.name} on port {player.port}")
    except (TypeError, ValueError) as e:
        show_error(f"Error initializing API for {player.name}: {str(e)}")
    
def packetLogger(Player):
    """Packet logger - now uses packet_handler module."""
    packet_logger_loop(Player, lambda: app_state.stop_thread)

def getRandomDelay(min_val, max_val):
    """Wrapper for get_random_delay from utils."""
    return get_random_delay(min_val, max_val)

def have_enough_bells(player):
    if int(player.bell_amount) > 1:
        return True
    else:
        error_stones = "You dont have enough bells!"
        show_error(error_stones)
        return False

def select_target(Player,target,entity_type):
    api = Player.api
    if int(target) == 0:
        pass
    else:
        api.target_entity(target, entity_type)

# Buffer state management now handled by app_state
def buffer_buffing(sp_name):
    """Mark buffer as actively buffing."""
    app_state.buffer_start_buffing(sp_name)

def buffer_end_buffing(sp_name):
    """Mark buffer as done buffing."""
    app_state.buffer_stop_buffing(sp_name)

def have_cd(player):
    """Check if skills are on cooldown - uses BufferManager."""
    return BufferManager.check_skills_ready(player)


def update_checkboxes(checkbox):
    if checkbox == point_set_check:
        delay_set_check.deselect()
    elif checkbox == delay_set_check:
        point_set_check.deselect()

message_labels = []

def show_message(message, color):
    global message_labels
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("[%d.%m.%Y - %H:%M:%S] ")
    formatted_message = formatted_datetime + message
    label = customtkinter.CTkLabel(master=output_frame, text=formatted_message, text_color=color)
    message_labels.insert(0, label)  # Insert new message at the beginning

    # Clear the frame
    for child in output_frame.winfo_children():
        child.pack_forget()

    # Re-pack all messages in the correct order
    for msg in message_labels:
        msg.pack(pady=5)

def show_error(message):
    show_message(message, "#C55252")

def show_success(message):
    show_message(message, "#0F960E")

def show_log(message):
    show_message(message, "#D8D8D8")


def change_start_button():
    start_button.configure(text='Stop', fg_color="#FD0E35", hover_color="#862425", command=stop_the_thread)

def change_onetime_button():
    manual_start_button.configure(text='One time running..', state="DISABLED", fg_color="#333")

def change_onetime_button_normal():
    manual_start_button.configure(text='One time buff', state="NORMAL", hover=True, fg_color="#1f3858", hover_color="#3e1f58")


def delay_before_next(delay):
    """Timer callback."""
    app_state.timer_end = True

def start_timer(delay):
    """Start delay timer."""
    app_state.timer = threading.Timer(delay, delay_before_next, args=[delay])
    app_state.timer.start()

def all_finished():
    """Check if all buffers finished - uses app_state."""
    return app_state.all_buffers_finished()


def all_in_miniland():
    """Check if all mains are in miniland - uses app_state."""
    if app_state.all_mains_in_miniland():
        time.sleep(getRandomDelay(0.8, 1.3))
        app_state.buffers_can_buff = True
        return True
    return False

can_invite = False
def start():
    if app_state.stop_thread:
        return

    # Use app_state for these flags
    after_cycles_set = str(delay_bfpoint_cycle_var.get())
    delay_bfpoint_time = str(delay_bfpoint_var.get())
    radius = str(area_var.get())
    x = str(x_var.get())
    y = str(y_var.get())
    delay_nopoint_time = str(delay_nopoint.get())

    if x != "" and y != "":
        cords = True
        x = int(x)
        y = int(y)
    else:
        cords = False

    if radius != "":
        radius = int(radius)
    else:
        radius = 0
    
    if delay_bfpoint_time != "":
        delay_bfpoint_time = int(delay_bfpoint_time)
    else:
        delay_bfpoint_time = 0

    if delay_nopoint_time != "":
        delay_nopoint_time = int(delay_nopoint_time)
    else:
        show_error("Delay of going to miniland wasnt set, returning..")
        return

    if after_cycles_set != "":
        after_cycles_set = int(after_cycles_set)
    else:
        after_cycles_set = 0


    if leave_on_own_checkbox_var.get() == 1:
        app_state.playerleave = True
    else:
        app_state.playerleave = False

    try:
        delay_value = float(delay_between_chars_seconds_var.get())
    except ValueError:
        delay_value = float(1.2)
    
    buffer_characters = {buffer_name: dropdown.get() for buffer_name, dropdown in buffer_dropdowns.items()}
     
    def main_character(player):
        # global app_state.stop_thread 
        cycles = 0
        is_first_cycle = True
        buff_point_crossed = False
        # global app_state.mainleft
        # global app_state.timer_end
        # global app_state.got_invite
        # global app_state.cant_invite
        # global app_state.buffers_can_buff
        # global app_state.others_stop, app_state.others_leave
        # global app_state.main1inmini
        if delay_set_check.get() == 1 and not app_state.stop_thread:
            change_start_button()
            show_success("Started automatic buffing!")
            while not app_state.stop_thread:
                player.api.query_player_information()
                time.sleep(0.1)
                if can_invite:
                    can_invite = False
                if app_state.timer_end or is_first_cycle:
                    if is_first_cycle:
                        is_first_cycle = False
                    app_state.mainleft = False
                    app_state.others_stop = True
                    player.api.stop_bot()
                    time.sleep(0.1)
                    can_invite = True
                    while not app_state.got_invite:
                        time.sleep(0.5)
                        if app_state.cant_invite == True:
                            stop_the_thread()
                            return
                        if app_state.stop_thread:
                            return
                    if app_state.got_invite == True:
                                time.sleep(getRandomDelay(0.5, 0.8))
                                player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                time.sleep(0.1)
                                player.api.query_player_information()
                                time.sleep(0.1)
                                while not player.map == 20001 and not app_state.stop_thread:
                                    player.api.query_player_information()
                                    time.sleep(0.2)
                                app_state.main1inmini = True
                                while not all_in_miniland():
                                    time.sleep(0.5)  
                                while not all_finished():
                                    time.sleep(0.5)
                                app_state.buffers_can_buff = False
                                app_state.others_leave = True
                                if app_state.playerleave == True:
                                    player.api.query_player_information()
                                    time.sleep(0.1)
                                    show_log("Main character is buffed you can leave miniland now.")
                                    while player.map == 20001:
                                        time.sleep(getRandomDelay(0.3,0.8))
                                        player.api.query_player_information()
                                        time.sleep(0.5)
                                        if player.map != 20001:
                                            string_autocycle_done = ("Main buffed!")
                                            app_state.mainleft = True  
                                            show_success(string_autocycle_done)
                                            player.api.continue_bot()
                                            app_state.timer_end = False
                                            start_timer(delay_nopoint_time)
                                else:
                                    time.sleep(getRandomDelay(0.3, 0.7))
                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                    time.sleep(1)
                                    player.api.query_player_information()
                                    time.sleep(0.2) 
                                    while player.map == 20001:
                                        time.sleep(getRandomDelay(0.3, 0.7))
                                        portal_pos_x, portal_pos_y = get_random_portal_pos()
                                        player.api.player_walk(portal_pos_x, portal_pos_y)
                                        player.api.pets_walk(portal_pos_x, portal_pos_y)
                                        time.sleep(0.5) 
                                        player.api.query_player_information() 
                                    time.sleep(0.2)                                               
                                    string_autocycle_done = ("Main buffed!")
                                    app_state.mainleft = True  
                                    show_success(string_autocycle_done)
                                    player.api.continue_bot()
                                    app_state.timer_end = False
                                    start_timer(delay_nopoint_time)
                elif app_state.stop_thread:
                    return
        elif point_set_check.get() == 1 and not app_state.stop_thread:
            if not cords:
                show_error("Cant start buff point auto function, u did not set coordinates.")
            else:     
                change_start_button()
                show_success("Started automatic buffing!")
                while not app_state.stop_thread:
                    player.api.query_player_information()
                    time.sleep(0.1)
                    if can_invite:
                        can_invite = False
                    
                    if radius == 0:
                        # Wait until player reaches the exact coordinates
                        while not (player.pos[0] == x and player.pos[1] == y):
                            time.sleep(0.5)
                            player.api.query_player_information()
                            time.sleep(0.1)

                        if not buff_point_crossed:
                            buff_point_crossed = True
                            
                            if is_first_cycle:
                                is_first_cycle = False
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()

                                            if delay_bfpoint_time != 0:
                                                app_state.timer_end = False
                                                start_timer(delay_bfpoint_time)
                            elif after_cycles_set != 0 and delay_bfpoint_time != 0:
                                cycles += 1
                                if cycles >= after_cycles_set and app_state.timer_end:
                                    cycles = 0
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()
                            elif delay_bfpoint_time != 0:
                                if app_state.timer_end:
                                    app_state.mainleft = False
                                    app_state.others_stop = True
                                    player.api.stop_bot()
                                    time.sleep(0.1)
                                    can_invite = True
                                    while not app_state.got_invite:
                                        time.sleep(0.5)
                                        if app_state.cant_invite == True:
                                            stop_the_thread()
                                            return
                                        if app_state.stop_thread:
                                            return
                                    if app_state.got_invite == True:
                                                time.sleep(getRandomDelay(0.5, 0.8))
                                                player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                                time.sleep(0.1)
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                while not player.map == 20001 and not app_state.stop_thread:
                                                    player.api.query_player_information()
                                                    time.sleep(0.2)
                                                app_state.main1inmini = True
                                                while not all_in_miniland():
                                                    time.sleep(0.5)
                                                while not all_finished():
                                                    time.sleep(0.5)
                                                app_state.buffers_can_buff = False
                                                app_state.others_leave = True
                                                if app_state.playerleave == True:
                                                    player.api.query_player_information()
                                                    time.sleep(0.1)
                                                    show_log("Main character is buffed you can leave miniland now.")
                                                    while player.map == 20001:
                                                        time.sleep(getRandomDelay(0.3,0.8))
                                                        player.api.query_player_information()
                                                        time.sleep(0.5)
                                                        if player.map != 20001:
                                                            string_autocycle_done = ("Main buffed!")
                                                            app_state.mainleft = True  
                                                            show_success(string_autocycle_done)
                                                            player.api.continue_bot()
                                                else:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(1)
                                                    player.api.query_player_information()
                                                    time.sleep(0.2) 
                                                    while player.map == 20001:
                                                        time.sleep(getRandomDelay(0.3, 0.7))
                                                        portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                        player.api.player_walk(portal_pos_x, portal_pos_y)
                                                        player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                        time.sleep(0.5) 
                                                        player.api.query_player_information() 
                                                    time.sleep(0.2)                                               
                                                    string_autocycle_done = ("Main buffed!")
                                                    app_state.mainleft = True  
                                                    show_success(string_autocycle_done)
                                                    player.api.continue_bot()
                                                    app_state.timer_end = False
                                                    start_timer(delay_bfpoint_time)
                            else:
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()

                        # Wait for player to leave the extended radius before resetting the flag
                        extended_radius = 5  # Define extended radius
                        while (x - extended_radius <= player.pos[0] <= x + extended_radius) and (y - extended_radius <= player.pos[1] <= y + extended_radius):
                            time.sleep(0.5)
                            player.api.query_player_information()
                            time.sleep(0.1)
                            if app_state.stop_thread:
                                if 'timer' in globals():
                                    timer.cancel()
                                return
                            
                        if buff_point_crossed:
                            buff_point_crossed = False
                            print("Player left radius. Buff point crossed is false now")
                        
                        if app_state.stop_thread:
                            if 'timer' in globals():
                                timer.cancel()
                            return
                    else:
                        # Wait until player enters the radius around the buff point
                        while not ((x - radius <= player.pos[0] <= x + radius) and (y - radius <= player.pos[1] <= y + radius)) and not buff_point_crossed and not app_state.stop_thread:
                            time.sleep(0.5)
                            player.api.query_player_information()
                            time.sleep(0.1)

                        if not buff_point_crossed:
                            buff_point_crossed = True
                            
                            if is_first_cycle:
                                is_first_cycle = False
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()

                                            if delay_bfpoint_time != 0:
                                                app_state.timer_end = False
                                                start_timer(delay_bfpoint_time)
                            elif after_cycles_set != 0 and delay_bfpoint_time != 0:
                                cycles += 1
                                if cycles >= after_cycles_set and app_state.timer_end:
                                    cycles = 0
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()
                            elif delay_bfpoint_time != 0:
                                if app_state.timer_end:
                                    app_state.mainleft = False
                                    app_state.others_stop = True
                                    player.api.stop_bot()
                                    time.sleep(0.1)
                                    can_invite = True
                                    while not app_state.got_invite:
                                        time.sleep(0.5)
                                        if app_state.cant_invite == True:
                                            stop_the_thread()
                                            return
                                        if app_state.stop_thread:
                                            return
                                    if app_state.got_invite == True:
                                                time.sleep(getRandomDelay(0.5, 0.8))
                                                player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                                time.sleep(0.1)
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                while not player.map == 20001 and not app_state.stop_thread:
                                                    player.api.query_player_information()
                                                    time.sleep(0.2)
                                                app_state.main1inmini = True
                                                while not all_in_miniland():
                                                    time.sleep(0.5)
                                                while not all_finished():
                                                    time.sleep(0.5)
                                                app_state.buffers_can_buff = False
                                                app_state.others_leave = True
                                                if app_state.playerleave == True:
                                                    player.api.query_player_information()
                                                    time.sleep(0.1)
                                                    show_log("Main character is buffed you can leave miniland now.")
                                                    while player.map == 20001:
                                                        time.sleep(getRandomDelay(0.3,0.8))
                                                        player.api.query_player_information()
                                                        time.sleep(0.5)
                                                        if player.map != 20001:
                                                            string_autocycle_done = ("Main buffed!")
                                                            app_state.mainleft = True  
                                                            show_success(string_autocycle_done)
                                                            player.api.continue_bot()
                                                else:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(1)
                                                    player.api.query_player_information()
                                                    time.sleep(0.2) 
                                                    while player.map == 20001:
                                                        time.sleep(getRandomDelay(0.3, 0.7))
                                                        portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                        player.api.player_walk(portal_pos_x, portal_pos_y)
                                                        player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                        time.sleep(0.5) 
                                                        player.api.query_player_information() 
                                                    time.sleep(0.2)                                               
                                                    string_autocycle_done = ("Main buffed!")
                                                    app_state.mainleft = True  
                                                    show_success(string_autocycle_done)
                                                    player.api.continue_bot()
                                                    app_state.timer_end = False
                                                    start_timer(delay_bfpoint_time)
                            else:
                                app_state.mainleft = False
                                app_state.others_stop = True
                                player.api.stop_bot()
                                time.sleep(0.1)
                                can_invite = True
                                while not app_state.got_invite:
                                    time.sleep(0.5)
                                    if app_state.cant_invite == True:
                                        stop_the_thread()
                                        return
                                    if app_state.stop_thread:
                                        return
                                if app_state.got_invite == True:
                                            time.sleep(getRandomDelay(0.5, 0.8))
                                            player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                                            time.sleep(0.1)
                                            player.api.query_player_information()
                                            time.sleep(0.1)
                                            while not player.map == 20001 and not app_state.stop_thread:
                                                player.api.query_player_information()
                                                time.sleep(0.2)
                                            app_state.main1inmini = True
                                            while not all_in_miniland():
                                                time.sleep(0.5)
                                            while not all_finished():
                                                time.sleep(0.5)
                                            app_state.buffers_can_buff = False
                                            app_state.others_leave = True
                                            if app_state.playerleave == True:
                                                player.api.query_player_information()
                                                time.sleep(0.1)
                                                show_log("Main character is buffed you can leave miniland now.")
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3,0.8))
                                                    player.api.query_player_information()
                                                    time.sleep(0.5)
                                                    if player.map != 20001:
                                                        string_autocycle_done = ("Main buffed!")
                                                        app_state.mainleft = True  
                                                        show_success(string_autocycle_done)
                                                        player.api.continue_bot()
                                            else:
                                                time.sleep(getRandomDelay(0.3, 0.7))
                                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                time.sleep(1)
                                                player.api.query_player_information()
                                                time.sleep(0.2) 
                                                while player.map == 20001:
                                                    time.sleep(getRandomDelay(0.3, 0.7))
                                                    portal_pos_x, portal_pos_y = get_random_portal_pos()
                                                    player.api.player_walk(portal_pos_x, portal_pos_y)
                                                    player.api.pets_walk(portal_pos_x, portal_pos_y)
                                                    time.sleep(0.5) 
                                                    player.api.query_player_information() 
                                                time.sleep(0.2)                                               
                                                string_autocycle_done = ("Main buffed!")
                                                app_state.mainleft = True  
                                                show_success(string_autocycle_done)
                                                player.api.continue_bot()

                        

                        # Wait for player to leave the extended radius before resetting the flag
                        extended_radius = radius * 2  # Define extended radius
                        while (x - extended_radius <= player.pos[0] <= x + extended_radius) and (y - extended_radius <= player.pos[1] <= y + extended_radius):
                            time.sleep(0.5)
                            player.api.query_player_information()
                            time.sleep(0.1)
                            if app_state.stop_thread:
                                if 'timer' in globals():
                                    timer.cancel()
                                return
                            
                        if buff_point_crossed:
                            buff_point_crossed = False
                            print("Player left radius. Buff point crossed is false now")
                        
                    if app_state.stop_thread:
                        if 'timer' in globals():
                            timer.cancel()
                        return

    def main_character2(player):
        # global app_state.main2left, app_state.main2inmini
        # global app_state.others_stop
        # global app_state.others_leave 
        # global app_state.cant_invite
        # global app_state.stop_thread

        while not app_state.stop_thread:
            while not app_state.others_stop:
                time.sleep(0.5)  
                if app_state.stop_thread:
                    return                       
            app_state.main2left = False
            player.api.stop_bot()
            time.sleep(0.1)
            while not app_state.got_invite2:
                time.sleep(0.5)
                if app_state.cant_invite:
                    stop_the_thread()
                    return
                if app_state.stop_thread:
                    return
            if app_state.got_invite2:
                        time.sleep(getRandomDelay(0.5, 0.8))
                        player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                        time.sleep(0.1)
                        player.api.query_player_information()
                        time.sleep(0.1)
                        while not player.map == 20001:
                            player.api.query_player_information()
                            time.sleep(0.2)
                        app_state.main2inmini = True
                        while not all_in_miniland():
                            time.sleep(0.5)
                        while not app_state.others_leave:
                            time.sleep(0.5)
                        if app_state.playerleave:
                            player.api.query_player_information()
                            time.sleep(0.1)
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3,0.8))
                                player.api.query_player_information()
                                time.sleep(0.5)
                                if player.map != 20001:
                                    app_state.main2left = True  
                                    player.api.continue_bot()
                        else:
                            time.sleep(getRandomDelay(1.4,1.9))
                            portal_pos_x, portal_pos_y = get_random_portal_pos()
                            player.api.player_walk(portal_pos_x, portal_pos_y)
                            player.api.pets_walk(portal_pos_x, portal_pos_y)
                            time.sleep(1)
                            player.api.query_player_information()
                            time.sleep(0.2) 
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3, 0.7))
                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                time.sleep(0.5) 
                                player.api.query_player_information() 
                            time.sleep(0.2)                                               
                            app_state.main2left = True  
                            player.api.continue_bot()

    def main_character3(player):
        # global app_state.main3left, app_state.main3inmini
        # global app_state.others_stop
        # global app_state.others_leave 
        # global app_state.cant_invite
        # global app_state.stop_thread
          
        while not app_state.stop_thread:
            while not app_state.others_stop:
                time.sleep(0.5)  
                if app_state.stop_thread:
                    return                       
            app_state.main3left = False
            player.api.stop_bot()
            time.sleep(0.1)
            while not app_state.got_invite3:
                time.sleep(0.5)
                if app_state.cant_invite:
                    stop_the_thread()
                    return
                if app_state.stop_thread:
                    return
            if app_state.got_invite3:
                        time.sleep(getRandomDelay(0.5, 0.8))
                        player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                        time.sleep(0.1)
                        player.api.query_player_information()
                        time.sleep(0.1)
                        while not player.map == 20001:
                            player.api.query_player_information()
                            time.sleep(0.2)
                        app_state.main3inmini = True
                        while not all_in_miniland():
                            time.sleep(0.5)
                        while not app_state.others_leave:
                            time.sleep(0.5)
                        if app_state.playerleave:
                            player.api.query_player_information()
                            time.sleep(0.1)
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3,0.8))
                                player.api.query_player_information()
                                time.sleep(0.5)
                                if player.map != 20001:
                                    app_state.main3left = True  
                                    player.api.continue_bot()
                        else:
                            time.sleep(getRandomDelay(1.4,1.9))
                            portal_pos_x, portal_pos_y = get_random_portal_pos()
                            player.api.player_walk(portal_pos_x, portal_pos_y)
                            player.api.pets_walk(portal_pos_x, portal_pos_y)
                            time.sleep(1)
                            player.api.query_player_information()
                            time.sleep(0.2) 
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3, 0.7))
                                portal_pos_x, portal_pos_y = get_random_portal_pos()
                                player.api.player_walk(portal_pos_x, portal_pos_y)
                                player.api.pets_walk(portal_pos_x, portal_pos_y)
                                time.sleep(0.5) 
                                player.api.query_player_information() 
                            time.sleep(0.2)                                               
                            app_state.main3left = True  
                            player.api.continue_bot()

    # Create buffer functions using factory (automatic mode)
    buffer_red_mage = create_buffer_function("red", "./PB_settings/red.ini", delay_value)
    buffer_holy = create_buffer_function("holy", "./PB_settings/holymage.ini", delay_value)
    buffer_blue_mage = create_buffer_function("blue_mage", "./PB_settings/blue_mage.ini", delay_value)
    buffer_dg = create_buffer_function("dg", "./PB_settings/dg.ini", delay_value)
    buffer_volcano = create_buffer_function("volcano", "./PB_settings/volcano.ini", delay_value)
    buffer_posseidon = create_buffer_function("poss", "./PB_settings/tidelord.ini", delay_value)
    buffer_warrior = create_buffer_function("war", "./PB_settings/war.ini", delay_value)
    buffer_crusse = create_buffer_function("cruss", "./PB_settings/cruss.ini", delay_value)
    buffer_wk = create_buffer_function("wk", "./PB_settings/wk.ini", delay_value)
    buffer_demon = create_buffer_function("demon", "./PB_settings/demon.ini", delay_value)
    buffer_wedding = create_buffer_function("wedding", "./PB_settings/wedding.ini", delay_value)
    

    def buffer_holy(player):
        # global app_state.buffers_buffing, app_state.buffers_can_buff
        # global app_state.buffers_can_buff_holy
        settings_path = os.path.abspath("./PB_settings/holymage.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "holy"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_holy and not app_state.stop_thread:
                time.sleep(5)
            if app_state.stop_thread:
                return
        # Acquire the lock before performing buffer actions
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
                if app_state.stop_thread:
                    return
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  

            # Simulate casting all skills and waiting for their cooldowns
            while not have_cd(player):
                time.sleep(0.5)
                player.api.query_skills_info()
                time.sleep(0.1)

            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_holy = False
            if app_state.stop_thread:
                return               
        show_error("Holy mage is not in miniland")
        stop_the_thread()
        return
    def buffer_blue_mage(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_blue_mage
        settings_path = os.path.abspath("./PB_settings/blue_mage.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "blue_mage"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_blue_mage and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_blue_mage = False
            if app_state.stop_thread:
                return
            
        show_error("Blue mage is not in miniland")
        stop_the_thread()
        return
    def buffer_dg(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_dg
        settings_path = os.path.abspath("./PB_settings/dg.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "dg"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_dg and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_dg = False
            if app_state.stop_thread:
                return
            
        show_error("Dark Gunner is not in miniland")
        stop_the_thread()
        return
    def buffer_volcano(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_volcano
        settings_path = os.path.abspath("./PB_settings/volcano.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "volcano"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_volcano and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_volcano = False
            if app_state.stop_thread:
                return
            
        show_error("Volcano is not in miniland")
        stop_the_thread()
        return
    def buffer_posseidon(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_poss
        settings_path = os.path.abspath("./PB_settings/tidelord.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "tidelord"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_poss and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_poss = False
            if app_state.stop_thread:
                return
            
        show_error("Tide Lord is not in miniland")
        stop_the_thread()
        return
    def buffer_warrior(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_war
        settings_path = os.path.abspath("./PB_settings/war.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "war"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_war and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_war = False
            if app_state.stop_thread:
                return
            
        show_error("Warrior is not in miniland")
        stop_the_thread()
        return
    def buffer_crusse(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_cruss
        settings_path = os.path.abspath("./PB_settings/cruss.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "cruss"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_cruss and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_cruss = False
            if app_state.stop_thread:
                return
            
        show_error("Crussader is not in miniland")
        stop_the_thread()
        return
    def buffer_wk(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_wk
        settings_path = os.path.abspath("./PB_settings/wk.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "wk"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_wk and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff and not app_state.stop_thread:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_wk = False
            if app_state.stop_thread:
                return
            
        show_error("Wild Keeper is not in miniland")
        stop_the_thread()
        return
    def buffer_demon(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_demon
        settings_path = os.path.abspath("./PB_settings/demon.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "demon"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_demon and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_demon = False
            if app_state.stop_thread:
                return
            
        show_error("Demon Warrior is not in miniland")
        stop_the_thread()
        return
    def buffer_wedding(player):
        # global app_state.buffers_can_buff, app_state.buffers_buffing
        # global app_state.buffers_can_buff_wedding
        settings_path = os.path.abspath("./PB_settings/wedding.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        player.api.query_player_information()
        time.sleep(0.1)
        name_of_sp = "wedding"
        while player.map == 20001:
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff_wedding and not app_state.stop_thread: 
                time.sleep(0.5)
            if app_state.stop_thread:
                return
            while not app_state.buffers_can_buff:
                time.sleep(0.5)
            while app_state.buffers_buffing:
                time.sleep(0.2)
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            while have_cd(player) == False:
                time.sleep(0.2)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            app_state.buffers_can_buff_wedding = False
            if app_state.stop_thread:
                return
            
        show_error("Wedding Costume SP is not in miniland")
        stop_the_thread()
        return
    def owner_of_miniland(player):
        player.api.query_player_information()
        time.sleep(0.1)
        player.api.query_inventory()
        time.sleep(0.1)
        player.api.query_map_entities()
        # global app_state.ownercharid
        app_state.ownercharid = player.id
        main_name = option_chosen
        # global app_state.cant_invite
        app_state.cant_invite = False
        # global app_state.others_stop, app_state.others_leave
        # global app_state.got_invite, app_state.got_invite2, app_state.got_invite3
        # global app_state.are2, app_state.are3
        # global app_state.buffers_can_buff_holy, app_state.buffers_can_buff_red, app_state.buffers_can_buff_war, app_state.buffers_can_buff_cruss, app_state.buffers_can_buff_dg, app_state.buffers_can_buff_blue_mage, app_state.buffers_can_buff_volcano, app_state.buffers_can_buff_poss, app_state.buffers_can_buff_wk, app_state.buffers_can_buff_demon, app_state.buffers_can_buff_wedding

        while player.map == 20001:
            if can_invite and not app_state.stop_thread:
                if app_state.are2:
                    time.sleep(getRandomDelay(0.7,1.1))
                    player.api.send_packet("$Invite " + str(main_name))
                    time.sleep(getRandomDelay(1.5,2))
                    player.api.send_packet("$Invite " + str(main2name))
                    app_state.got_invite = True
                    time.sleep(getRandomDelay(1, 2))
                    app_state.got_invite2 = True
                    while not app_state.mainleft and not app_state.main2left:
                        time.sleep(1)
                    app_state.others_stop = False
                    app_state.others_leave = False
                    can_invite = False
                    app_state.got_invite = False
                    app_state.got_invite2 = False
                    app_state.buffers_can_buff_holy = True
                    app_state.buffers_can_buff_red = True
                    app_state.buffers_can_buff_blue_mage = True
                    app_state.buffers_can_buff_dg = True
                    app_state.buffers_can_buff_volcano = True
                    app_state.buffers_can_buff_poss = True
                    app_state.buffers_can_buff_war = True
                    app_state.buffers_can_buff_cruss = True
                    app_state.buffers_can_buff_wk = True
                    app_state.buffers_can_buff_demon = True
                    app_state.buffers_can_buff_wedding = True
                elif app_state.are3:
                    time.sleep(getRandomDelay(0.7,1.1))
                    player.api.send_packet("$Invite " + str(main_name))
                    time.sleep(getRandomDelay(1.5,2))
                    player.api.send_packet("$Invite " + str(main2name))
                    time.sleep(getRandomDelay(1.5,2))
                    player.api.send_packet("$Invite " + str(main3name))
                    time.sleep(getRandomDelay(0.5,0.7))
                    app_state.got_invite = True
                    time.sleep(getRandomDelay(1, 2))
                    app_state.got_invite2 = True
                    time.sleep(getRandomDelay(1, 2))
                    app_state.got_invite3 = True
                    while not app_state.mainleft and not app_state.main2left and not app_state.main3left:
                        time.sleep(1)
                    app_state.others_stop = False
                    app_state.others_leave = False
                    can_invite = False
                    app_state.got_invite = False
                    app_state.got_invite2 = False
                    app_state.got_invite3 = False
                    app_state.buffers_can_buff_holy = True
                    app_state.buffers_can_buff_red = True
                    app_state.buffers_can_buff_blue_mage = True
                    app_state.buffers_can_buff_dg = True
                    app_state.buffers_can_buff_volcano = True
                    app_state.buffers_can_buff_poss = True
                    app_state.buffers_can_buff_war = True
                    app_state.buffers_can_buff_cruss = True
                    app_state.buffers_can_buff_wk = True
                    app_state.buffers_can_buff_demon = True
                    app_state.buffers_can_buff_wedding = True
                else:
                    player.api.send_packet("$Invite " + str(main_name))
                    app_state.got_invite = True
                    while not app_state.mainleft:
                        time.sleep(1)
                    app_state.others_stop = False
                    app_state.others_leave = False
                    can_invite = False
                    app_state.got_invite = False
                    app_state.buffers_can_buff_holy = True
                    app_state.buffers_can_buff_red = True
                    app_state.buffers_can_buff_blue_mage = True
                    app_state.buffers_can_buff_dg = True
                    app_state.buffers_can_buff_volcano = True
                    app_state.buffers_can_buff_poss = True
                    app_state.buffers_can_buff_war = True
                    app_state.buffers_can_buff_cruss = True
                    app_state.buffers_can_buff_wk = True
                    app_state.buffers_can_buff_demon = True
                    app_state.buffers_can_buff_wedding = True
            if app_state.stop_thread:
                show_success("Stopped the bot")
                return
            time.sleep(0.5)
        show_error("Owner of miniland is not in miniland!")
        app_state.cant_invite = True
        return
    
    option_chosen = main_character_var1.get()
    main2name = main_character_var2.get()
    main3name = main_character_var3.get()
    option_miniowner = miniowner_character_var.get()

    if option_chosen == "":
        show_error("You need to select atleast one of your main characters.")
        return
    
    if option_miniowner == "":
        show_error("You need to select owner of the miniland.")
        return
    
    if option_chosen == option_miniowner:
        show_error("Main character and Owner of miniland are the same, change the owner(to buffer) or main.")
        return
    
    if (main2name and option_chosen == main2name) or (main3name and option_chosen == main3name) or (main2name and main3name and main2name == main3name):
        show_error("Some main characters are same, you need to change that! (If you have just one, just input main character 1)")
        return
    
    if main2name != "" and main3name != "":
        app_state.are3 = True

    if option_chosen != "" and main2name != "" and main3name == "":
        app_state.are2 = True
    

    
    if not app_state.stop_thread: # Initialize the main character
        player = PlayerFactory.create_player(option_chosen)
        
        # Start packetLogger and main_character threads for the main character
        t1 = threading.Thread(target=packetLogger, args=(player,))
        t1.start()
        t2 = threading.Thread(target=main_character, args=(player,))
        t2.start()


        if main2name != "":
            main2 = PlayerFactory.create_player(main2name)

            main2tpacket = threading.Thread(target=packetLogger, args=(main2,))
            main2tpacket.start()
            main2twork = threading.Thread(target=main_character2, args=(main2,))
            main2twork.start()

        if main3name != "":
            main3 = PlayerFactory.create_player(main3name)

            main3tpacket = threading.Thread(target=packetLogger, args=(main3,))
            main3tpacket.start()
            main3twork = threading.Thread(target=main_character3, args=(main3,))
            main3twork.start()

        # Initialize the buffer characters
    buffer_thread_map = {
        "red": buffer_red_mage,
        "holy": buffer_holy,
        "blue_mage": buffer_blue_mage,
        "dg": buffer_dg,
        "volcano": buffer_volcano,
        "poss": buffer_posseidon,
        "war": buffer_warrior,
        "cruss": buffer_crusse,
        "wk": buffer_wk,
        "demon": buffer_demon,
        "wedding": buffer_wedding,
    }

    # global app_state.buffer_classes
    # Initialize the buffer characters
    for buffer_name, char_name in buffer_characters.items():
        buffer_player = PlayerFactory.create_player(char_name)
        
        if not app_state.stop_thread:
            t3 = threading.Thread(target=packetLogger, args=(buffer_player,))
            t3.start()
        
        # Start specific buffer thread based on buffer name
        if buffer_name in buffer_thread_map and not app_state.stop_thread:
            t4 = threading.Thread(target=buffer_thread_map[buffer_name], args=(buffer_player,))
            t4.start()
            app_state.buffer_classes.append(buffer_name)

    # Initialize the main character
    owner_player = PlayerFactory.create_player(option_miniowner)

    if not app_state.stop_thread:
        # Start packetLogger and main_character threads for the main character
        t5 = threading.Thread(target=packetLogger, args=(owner_player,))
        t5.start()
        t6 = threading.Thread(target=owner_of_miniland, args=(owner_player,))
        t6.start()

def stop_the_thread():
    """Stop all threads."""
    app_state.stop_thread = True
    time.sleep(1)
    start_button.configure(text="Start", command=start_again, fg_color="#14B054", hover_color="#148C46")


def mark_first_as_done():
    global first_steps
    first_steps = True
    
def start_again():
    """Restart after stop."""
    app_state.stop_thread = False
    start()

def on_closing():
    """Handle window close."""
    app_state.stop_thread = True
    root.destroy()
    sys.exit(0)


def one_time_buff():
    threads_list = []
    players = []
    # global app_state.playerleave
    # global app_state.stop_thread
    app_state.stop_thread = False
    # global app_state.are2
    # global app_state.are3
    
    if leave_on_own_checkbox_var.get() == 1:
        app_state.playerleave = True
    else:
        app_state.playerleave = False

    try:
        delay_value = float(delay_between_chars_seconds_var.get())
    except ValueError:
        delay_value = float(2.6)
    
    buffer_characters = {buffer_name: dropdown.get() for buffer_name, dropdown in buffer_dropdowns.items()}

    def main_character(player):
        if player.api != 0:
            show_success("Bot started one time function!")
            change_onetime_button()
            # global app_state.one_time_running
            app_state.one_time_running = True
            # global app_state.mainleft
            app_state.mainleft = False
            # global app_state.got_invite
            # global app_state.cant_invite
            # global app_state.main1inmini
            # global app_state.buffers_can_buff
            # query to get player id and position as seen in the packetlogger function
            player.api.query_player_information()
            time.sleep(0.1)
            player.api.query_inventory()
            time.sleep(0.1)
            player.api.query_map_entities()
            time.sleep(0.1)
            while not app_state.got_invite:
                time.sleep(0.5)
                if app_state.cant_invite:
                    change_onetime_button_normal()
                    return
            if app_state.got_invite == True:
                        time.sleep(getRandomDelay(1.8,2.4))
                        player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                        time.sleep(0.1)
                        player.api.query_player_information()
                        time.sleep(0.1)
                        while not player.map == 20001 and not app_state.stop_thread:
                            player.api.query_player_information()
                            time.sleep(0.2)
                        app_state.main1inmini = True
                        while not all_in_miniland():
                            time.sleep(1)
                        time.sleep(getRandomDelay(1.3,1.7))
                        while app_state.buffers_buffing == True:
                            time.sleep(getRandomDelay(0.3,0.7))
                            if app_state.buffers_buffing == False:
                                time.sleep(getRandomDelay(0.8,1.4))
                        time.sleep(1)
                        app_state.buffers_can_buff = False
                        if app_state.playerleave == True:
                            player.api.query_player_information()
                            time.sleep(0.1)
                            show_success("Buffers done buffing, you can leave miniland now.")
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3,0.8))
                                player.api.query_player_information()
                                time.sleep(0.1)
                                if player.map != 20001:
                                    time.sleep(getRandomDelay(0.2, 0.7))
                                    app_state.mainleft = True
                                    break
                        else:
                            portal_pos_x, portal_pos_y = get_random_portal_pos()
                            player.api.player_walk(portal_pos_x, portal_pos_y)
                            player.api.pets_walk(portal_pos_x, portal_pos_y)
                            time.sleep(0.5)
                            app_state.mainleft = True                    
                        change_onetime_button_normal()
                        string_onetime_done = ("Bot finished one time buff function.")
                        show_success(string_onetime_done)
                        app_state.one_time_running = False
                        return
            return
        else:
            return
        
    def main_character2(player):
        if player.api != 0:
            # global app_state.main2left
            app_state.main2left = False
            # global app_state.got_invite2
            # global app_state.cant_invite
            # global app_state.main2inmini
            # global app_state.buffers_can_buff
            # query to get player id and position as seen in the packetlogger function
            player.api.query_player_information()
            time.sleep(0.1)
            while not app_state.got_invite2:
                time.sleep(0.5)
                if app_state.cant_invite:
                    change_onetime_button_normal()
                    return
            if app_state.got_invite2:
                        time.sleep(getRandomDelay(0.8,1.3))
                        player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                        time.sleep(0.1)
                        player.api.query_player_information()
                        time.sleep(0.1)
                        while not player.map == 20001 and not app_state.stop_thread:
                            player.api.query_player_information()
                            time.sleep(0.2)
                        app_state.main2inmini = True
                        while not all_in_miniland():
                            time.sleep(1)
                        time.sleep(getRandomDelay(1.3,1.7))
                        while app_state.buffers_buffing == True:
                            time.sleep(getRandomDelay(0.3,0.7))
                            if app_state.buffers_buffing == False:
                                time.sleep(getRandomDelay(0.8,1.4))
                        if app_state.playerleave == True:
                            player.api.query_player_information()
                            time.sleep(0.1)
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3,0.8))
                                player.api.query_player_information()
                                time.sleep(0.1)
                                if player.map != 20001:
                                    time.sleep(getRandomDelay(0.2, 0.7))
                                    app_state.main2left = True
                                    break
                        else:
                            time.sleep(getRandomDelay(1.5,2.2))
                            portal_pos_x, portal_pos_y = get_random_portal_pos()
                            player.api.player_walk(portal_pos_x, portal_pos_y)
                            player.api.pets_walk(portal_pos_x, portal_pos_y)
                            time.sleep(0.5)
                            app_state.main2left = True                    
                        return
            return
        else:
            return
    def main_character3(player):
        if player.api != 0:
            # global app_state.main3left
            app_state.main3left = False
            # global app_state.got_invite3
            # global app_state.cant_invite
            # global app_state.main3inmini
            # global app_state.buffers_can_buff
            # query to get player id and position as seen in the packetlogger function
            player.api.query_player_information()
            time.sleep(0.1)
            while not app_state.got_invite3:
                time.sleep(0.5)
                if app_state.cant_invite:
                    change_onetime_button_normal()
                    return
            if app_state.got_invite3:
                        time.sleep(getRandomDelay(0.8,1.3))
                        player.api.send_packet("#mjoin^1^"+str(app_state.ownercharid)+"^2")
                        time.sleep(0.1)
                        player.api.query_player_information()
                        time.sleep(0.1)
                        while not player.map == 20001 and not app_state.stop_thread:
                            player.api.query_player_information()
                            time.sleep(0.2)
                        app_state.main3inmini = True
                        while not all_in_miniland():
                            time.sleep(1)
                        time.sleep(getRandomDelay(1.3,1.7))
                        while app_state.buffers_buffing == True:
                            time.sleep(getRandomDelay(0.3,0.7))
                            if app_state.buffers_buffing == False:
                                time.sleep(getRandomDelay(0.8,1.4))
                        if app_state.playerleave == True:
                            player.api.query_player_information()
                            time.sleep(0.1)
                            while player.map == 20001:
                                time.sleep(getRandomDelay(0.3,0.8))
                                player.api.query_player_information()
                                time.sleep(0.1)
                                if player.map != 20001:
                                    time.sleep(getRandomDelay(0.2, 0.7))
                                    app_state.main3left = True
                                    break
                        else:
                            time.sleep(getRandomDelay(3,3.5))
                            portal_pos_x, portal_pos_y = get_random_portal_pos()
                            player.api.player_walk(portal_pos_x, portal_pos_y)
                            player.api.pets_walk(portal_pos_x, portal_pos_y)
                            time.sleep(0.5)
                            app_state.main3left = True                    
                        return
            return
        else:
            return
    
    # Create one-time buffer functions using factory    
    buffer_red_mage = create_onetime_buffer_function("red", "./PB_settings/red.ini", delay_value)
    buffer_holy = create_onetime_buffer_function("holy", "./PB_settings/holymage.ini", delay_value)
    buffer_blue_mage = create_onetime_buffer_function("blue_mage", "./PB_settings/blue_mage.ini", delay_value)
    buffer_dg = create_onetime_buffer_function("dg", "./PB_settings/dg.ini", delay_value)
    buffer_volcano = create_onetime_buffer_function("volcano", "./PB_settings/volcano.ini", delay_value)
    buffer_posseidon = create_onetime_buffer_function("poss", "./PB_settings/tidelord.ini", delay_value)
    buffer_warrior = create_onetime_buffer_function("war", "./PB_settings/war.ini", delay_value)
    buffer_crusse = create_onetime_buffer_function("cruss", "./PB_settings/cruss.ini", delay_value)
    buffer_wk = create_onetime_buffer_function("wk", "./PB_settings/wk.ini", delay_value)
    buffer_demon = create_onetime_buffer_function("demon", "./PB_settings/demon.ini", delay_value)
    buffer_wedding = create_onetime_buffer_function("wedding", "./PB_settings/wedding.ini", delay_value)
        

    def buffer_holy(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/holymage.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "holy"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Holy mage is not in miniland")


    def buffer_blue_mage(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/blue_mage.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "blue_mage"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Blue Mage is not in miniland")
    
    def buffer_dg(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/dg.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "dg"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Dark Gunner is not in miniland")
    
    def buffer_volcano(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/volcano.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "volcano"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Volcano is not in miniland")
    
    def buffer_posseidon(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/tidelord.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "tidelord"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Tide Lord is not in miniland")
    
    def buffer_warrior(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/war.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "war"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Warrior is not in miniland")
    
    def buffer_crusse(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/cruss.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "cruss"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Crussader is not in miniland")
    
    def buffer_wk(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/wk.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "wk"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Wild Keeper is not in miniland")
    
    def buffer_demon(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/demon.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "demon"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Demon Warrior is not in miniland")
    
    def buffer_wedding(player):
        # global app_state.buffers_can_buff
        settings_path = os.path.abspath("./PB_settings/wedding.ini")
        player.api.load_settings(settings_path)
        time.sleep(1)
        print("Loaded settings.")
        player.api.query_player_information()
        time.sleep(0.1)
        if player.map == 20001: 
            name_of_sp = "wedding"
            while app_state.buffers_can_buff == False:
                time.sleep(0.5)
            while app_state.buffers_buffing == True:
                time.sleep(getRandomDelay(0.3, 0.7))
            buffer_buffing(name_of_sp)  
            if player.resting == True:
                time.sleep(getRandomDelay(0.3, 0.7)) 
                player.api.send_packet("rest 1 1 " + str(player.id))
                player.resting = False
                time.sleep(getRandomDelay(0.3, 0.7))              
            player.api.start_bot()
            player.api.recv_packet("in 3 160 1504268 14 25 2 100 100 0 0 0 -1 1 0 -1 - 0 -1 0 0 0 0 0 0 0 0 0 0 0 0")  
            time.sleep(1)              
            while have_cd(player) == False:
                time.sleep(0.5)
            player.api.stop_bot()
            time.sleep(0.1)
            time.sleep(delay_value)
            buffer_end_buffing(name_of_sp)
            return
        else:
            show_error("Wedding Costume buffer is not in miniland")

    def owner_of_miniland(player):
        player.api.query_player_information()
        time.sleep(0.1)
        player.api.query_inventory()
        time.sleep(0.1)
        player.api.query_map_entities()
        # global app_state.ownercharid
        app_state.ownercharid = player.id
        main_name = option_chosen
        # global app_state.cant_invite
        app_state.cant_invite = False
        # global app_state.got_invite, app_state.got_invite2, app_state.got_invite3
        # global app_state.are2, app_state.are3

        if player.map == 20001:
            if app_state.are2:
                time.sleep(getRandomDelay(0.7,1.5))
                player.api.send_packet("$Invite " + str(main_name))
                time.sleep(getRandomDelay(1.5,2))
                player.api.send_packet("$Invite " + str(main2name))
                app_state.got_invite = True
                time.sleep(getRandomDelay(1, 2))
                app_state.got_invite2 = True

                while not app_state.mainleft and not app_state.main2left:
                    time.sleep(1)
                can_invite = False
                app_state.got_invite = False
                app_state.got_invite2 = False
                return
            elif app_state.are3:
                time.sleep(getRandomDelay(0.7,1.5))
                player.api.send_packet("$Invite " + str(main_name))
                time.sleep(getRandomDelay(1.5,2))
                player.api.send_packet("$Invite " + str(main2name))
                time.sleep(getRandomDelay(1.5,2))
                player.api.send_packet("$Invite " + str(main3name))
                app_state.got_invite = True
                time.sleep(getRandomDelay(1, 1.2))
                app_state.got_invite2 = True
                time.sleep(getRandomDelay(1, 1.2))
                app_state.got_invite3 = True

                while not app_state.mainleft and not app_state.main2left and not app_state.main3left:
                    time.sleep(1)
                can_invite = False
                app_state.got_invite = False
                app_state.got_invite2 = False
                app_state.got_invite3 = False
                return
            else:
                time.sleep(getRandomDelay(0.7,1.5))
                player.api.send_packet("$Invite " + str(main_name))
                app_state.got_invite = True
                while app_state.mainleft == False:
                    time.sleep(1)
                if app_state.mainleft == True:
                    can_invite = False
                    app_state.got_invite = False
                    return
                else:
                    return
        else:
            show_error("Owner of miniland is not in miniland!")
            app_state.cant_invite = True
            return

    option_chosen = main_character_var1.get()
    main2name = main_character_var2.get()
    main3name = main_character_var3.get()
    option_miniowner = miniowner_character_var.get()

    if option_chosen == "":
        show_error("You need to select atleast one of your main characters.")
        return
    
    if option_miniowner == "":
        show_error("You need to select owner of the miniland.")
        return
    
    if option_chosen == option_miniowner:
        show_error("Main character and Owner of miniland are the same, change the owner(to buffer) or main.")
        return
    
    if (main2name and option_chosen == main2name) or (main3name and option_chosen == main3name) or (main2name and main3name and main2name == main3name):
        show_error("Some main characters are same, you need to change that! (If you have just one, just input main character 1)")
        return
    
    if main2name != "" and main3name != "":
        app_state.are3 = True

    if option_chosen != "" and main2name != "" and main3name == "":
        app_state.are2 = True
    

    
    # Initialize the main character
    player = PlayerFactory.create_player(option_chosen)
    
    # Start packetLogger and main_character threads for the main character
    t1 = threading.Thread(target=packetLogger, args=(player,))
    t1.start()
    threads_list.append(t1)
    t2 = threading.Thread(target=main_character, args=(player,))
    t2.start()
    threads_list.append(t2)
    players.append(player)


    if main2name != "":
        main2 = PlayerFactory.create_player(main2name)

        main2tpacket = threading.Thread(target=packetLogger, args=(main2,))
        main2tpacket.start()
        main2twork = threading.Thread(target=main_character2, args=(main2,))
        main2twork.start()

    if main3name != "":
        main3 = PlayerFactory.create_player(main3name)

        main3tpacket = threading.Thread(target=packetLogger, args=(main3,))
        main3tpacket.start()
        main3twork = threading.Thread(target=main_character3, args=(main3,))
        main3twork.start()

        # Initialize the buffer characters
    buffer_thread_map = {
        "red": buffer_red_mage,
        "holy": buffer_holy,
        "blue_mage": buffer_blue_mage,
        "dg": buffer_dg,
        "volcano": buffer_volcano,
        "poss": buffer_posseidon,
        "war": buffer_warrior,
        "cruss": buffer_crusse,
        "wk": buffer_wk,
        "demon": buffer_demon,
        "wedding": buffer_wedding,
    }

    # Initialize the buffer characters
    for buffer_name, char_name in buffer_characters.items():
        buffer_player = PlayerFactory.create_player(char_name)
        if char_name == option_chosen:
            show_error("Your main cant be buffer. Sorry about that maybe in the future :-)")
            return
        # Start packetLogger thread for buffer character
        t3 = threading.Thread(target=packetLogger, args=(buffer_player,))
        t3.start()
        threads_list.append(t3)
        
        # Start specific buffer thread based on buffer name
        if buffer_name in buffer_thread_map:
            t4 = threading.Thread(target=buffer_thread_map[buffer_name], args=(buffer_player,))
            t4.start()
        
        players.append(buffer_player)
        threads_list.append(t4)

    # Initialize the main character
    owner_player = PlayerFactory.create_player(option_miniowner)

    # Start packetLogger and main_character threads for the main character
    t5 = threading.Thread(target=packetLogger, args=(owner_player,))
    t5.start()
    threads_list.append(t5)
    t6 = threading.Thread(target=owner_of_miniland, args=(owner_player,))
    t6.start()
    players.append(owner_player)
    threads_list.append(t6)

waiting_for_accept = False
timeout = 10  # Timeout in seconds

def send_invite(player, name, invites_sent):
    global waiting_for_accept
    if name not in invites_sent:
        player.api.send_packet("$Invite " + str(name))
        invites_sent.append(name)
        waiting_for_accept = True

def accept_invite(player, name, invites_accepted):
    # global app_state.ownercharid
    global waiting_for_accept
    player.api.send_packet("#mjoin^1^" + str(app_state.ownercharid) + "^2")
    time.sleep(1)
    player.api.query_player_information()
    time.sleep(0.1)
    if player.map == 20001:
        invites_accepted.append(name)
        waiting_for_accept = False

def invite_players():
    # global app_state.stop_thread
    invites_sent = []
    invites_accepted = []
    buffer_characters = {buffer_name: dropdown.get() for buffer_name, dropdown in buffer_dropdowns.items()}
    app_state.stop_thread = False

    def owner_of_miniland(player):
        # global app_state.ownercharid
        show_success("Inviting buffers to miniland..")
        names = []
        player.api.query_player_information()
        time.sleep(0.1)
        app_state.ownercharid = player.id
        if player.map == 20001:
            for _, char_name in buffer_characters.items():
                buffer_player.name = char_name
                names.append(char_name)
            if player.name in names:
                names.remove(player.name)
            for name in names:
                if app_state.stop_thread:
                    break
                time.sleep(getRandomDelay(2.6, 3.6))
                if name not in invites_accepted:
                    send_invite(player, name, invites_sent)
                    show_log("Inviting " + name)
                    start_time = time.time()
                    while waiting_for_accept and (time.time() - start_time < timeout) and not app_state.stop_thread:
                        time.sleep(getRandomDelay(0.5, 1.5))
                    if not waiting_for_accept:
                        pass
                    else:
                        show_error("Invite timed out for " + name)
                        break   
            if len(names) == len(invites_accepted):
                show_success("Everybody in miniland")
            else:
                show_error("Some buffer is missing in miniland")
        app_state.stop_thread = True

    def buffer_thread(player):
        global waiting_for_accept
        player.api.query_player_information()
        name = player.name
        time.sleep(0.1)
        while name not in invites_sent and not app_state.stop_thread:
            time.sleep(1)
        start_time = time.time()
        while name not in invites_accepted and (time.time() - start_time < timeout) and not app_state.stop_thread:
            if player.map != 20001:
                time.sleep(getRandomDelay(1.8, 2.5))
                accept_invite(player, name, invites_accepted)
            else:
                invites_sent.append(name)
                invites_accepted.append(name)
                waiting_for_accept = False

    # Initialize the buffer characters
    for _, char_name in buffer_characters.items():
        buffer_player = PlayerFactory.create_player(char_name)        
        # Start packetLogger thread for buffer character
        t3 = threading.Thread(target=packetLogger, args=(buffer_player,))
        t3.start()
        t4 = threading.Thread(target=buffer_thread, args=(buffer_player,))
        t4.start()

    option_miniowner = miniowner_character_var.get()
    player = PlayerFactory.create_player(option_miniowner)
    t_owner_packet = threading.Thread(target=packetLogger, args=(player,))
    t_owner_packet.start()
    t_owner = threading.Thread(target=owner_of_miniland, args=(player,))
    t_owner.start()

if __name__ == "__main__":

    error_label = None

    number_of_attempts = 0

    level_of_perf_set = 0

    customtkinter.set_appearance_mode('dark')

    ports = getports.returnAllPorts()
    formatted_ports = [name for name, _ in ports]
    formatted_ports.sort()
    formatted_ports.insert(0, "None")

    formatted_ports_main = [name for name, _ in ports]
    formatted_ports_main.sort()

    def find_image_path(id):
        image_path = resource_path(f"Buffer_icons/{id}.png")
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file '{image_path}' does not exist")
        image_path = os.path.abspath(image_path)
        image = Image.open(image_path)
        buffer_icon = customtkinter.CTkImage(image, size=(50, 50))
        return buffer_icon
    

    # Track the currently selected buttons
    selected_buttons = set()
    buffer_character_vars = {}
    
    def toggle_highlight_button(button, name):
        if name in icon_names:  # Check if the name is valid
            if name in selected_buttons:
                button.configure(fg_color="transparent")
                selected_buttons.remove(name)
            else:
                button.configure(fg_color="#5D3587")
                selected_buttons.add(name)

    def update_buffer_characters():
        for buffer_name, dropdown in buffer_dropdowns.items():
            buffer_characters[buffer_name] = dropdown.get()

    def show_frame(frame):
        frame.tkraise()
        update_button_colors(frame)

    # Function to update button colors based on the active frame
    def update_button_colors(active_frame):
        if active_frame == tab1_frame:
            tab1_button.configure(fg_color="#764F97", hover_color="#764F97")
            tab2_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab3_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab4_button.configure(fg_color="#59525F", hover_color="#764F97")
        elif active_frame == tab2_frame:
            tab1_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab2_button.configure(fg_color="#764F97", hover_color="#764F97")
            tab3_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab4_button.configure(fg_color="#59525F", hover_color="#764F97")
        elif active_frame == tab3_frame:
            tab1_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab2_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab3_button.configure(fg_color="#764F97", hover_color="#764F97")
            tab4_button.configure(fg_color="#59525F", hover_color="#764F97")
        elif active_frame == tab4_frame:
            tab1_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab2_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab3_button.configure(fg_color="#59525F", hover_color="#764F97")
            tab4_button.configure(fg_color="#764F97", hover_color="#764F97")
            
    root = customtkinter.CTk()
    root.iconbitmap(resource_path("icon.ico"))
    root.minsize(850,850)
    root.maxsize(850,850)
    root.title("BuffersBot by Mr. Argent")

    # Header label
    # Create a top frame to hold tab buttons
    top_frame = customtkinter.CTkFrame(master=root, height=50)

    # Create frames for each tab content
    # Create frames for each tab content
    tab1_frame = customtkinter.CTkFrame(master=root)
    tab2_frame = customtkinter.CTkFrame(master=root)
    tab3_frame = customtkinter.CTkFrame(master=root)
    tab4_frame = customtkinter.CTkFrame(master=root)

    for frame in (tab1_frame, tab2_frame, tab3_frame, tab4_frame):
        frame.place(x=0, y=50, relwidth=1, relheight=1)

    top_frame.pack(side="top", fill="x")

    ##CHARCONFIG###
    imageheader_path = resource_path("buffersapilogo.png")
    if not os.path.isfile(imageheader_path):
        raise FileNotFoundError(f"Image File '{imageheader_path}' does not exit")
    imageheader_path = os.path.abspath(imageheader_path)
    imageheader = Image.open(imageheader_path)
    header_image = customtkinter.CTkImage(imageheader, size=(100, 80))
    header_label = customtkinter.CTkLabel(master=tab1_frame, text="", image=header_image)
    header_label.pack(padx=10, pady=10)

    # Create the main frame for characters
    main_character_frame = customtkinter.CTkFrame(master=tab1_frame)
    main_character_frame.pack(pady=10, padx=10, fill="x", expand=True)

    # Function to create a labeled dropdown for main characters
    def create_main_character_dropdown(master, text, options, variable):
        
        label = customtkinter.CTkLabel(master=master, text=text)
        label.pack(side="left")
        
        spacer = customtkinter.CTkFrame(master=master, width=20, height=50, fg_color="transparent")
        spacer.pack(side="left")
        
        dropdown = customtkinter.CTkOptionMenu(master=master, values=options, variable=variable, fg_color="#453b4d", button_color="#532877", button_hover_color="#3e1f58")
        dropdown.pack(side="left")

        spacer = customtkinter.CTkFrame(master=master, width=20, height=50, fg_color="transparent")
        spacer.pack(side="left")
        
        
        return dropdown

    # Variables for dropdowns
    main_character_var1 = customtkinter.StringVar()
    main_character_var2 = customtkinter.StringVar()
    main_character_var3 = customtkinter.StringVar()

    # Create dropdowns for Main Character 1, Main Character 2, and Main Character 3
    spacer = customtkinter.CTkFrame(master=main_character_frame, width=7, height=50, fg_color="transparent")
    spacer.pack(side="left")
    main_character_dropdown1 = create_main_character_dropdown(main_character_frame, "Main Character 1:", formatted_ports_main, main_character_var1)
    main_character_dropdown2 = create_main_character_dropdown(main_character_frame, "Main Character 2:", formatted_ports_main, main_character_var2)
    main_character_dropdown3 = create_main_character_dropdown(main_character_frame, "Main Character 3:", formatted_ports_main, main_character_var3)

    miniowner_character_frame = customtkinter.CTkFrame(master=tab1_frame)
    miniowner_character_frame.pack(pady=10, padx=10, fill="x", expand=True)

    miniownerframe_leftspacer = customtkinter.CTkFrame(master=miniowner_character_frame, width=200, height=50, fg_color="transparent")
    miniownerframe_leftspacer.pack(side="left")

    miniowner_character_label = customtkinter.CTkLabel(master=miniowner_character_frame, text="Owner of the Miniland:")
    miniowner_character_label.pack(side="left")

    miniownerframe_centerspacer = customtkinter.CTkFrame(master=miniowner_character_frame, width=20, height=50, fg_color="transparent")
    miniownerframe_centerspacer.pack(side="left")

    # Create miniowner character dropdown
    miniowner_character_var = customtkinter.StringVar()
    miniowner_character_dropdown = customtkinter.CTkOptionMenu(master=miniowner_character_frame, values=formatted_ports, variable=miniowner_character_var, fg_color="#453b4d", button_color="#532877", button_hover_color="#3e1f58")
    miniowner_character_dropdown.pack(side="left", fill="x", expand=True)

    miniownerframe_rightspacer = customtkinter.CTkFrame(master=miniowner_character_frame, width=200, height=50, fg_color="transparent")
    miniownerframe_rightspacer.pack(side="right")

    # Buffers label
    buffers_label = customtkinter.CTkLabel(master=tab1_frame, text='Buffers', font=(None, 18))
    buffers_label.pack(pady=10)

    red = "red"
    holy = "holy"
    blue_mage = "blue_mage"
    dg = "dg"
    volcano = "volcano"
    poss = "poss"
    war = "war"
    cruss = "cruss"
    wk = "wk"
    wedding = "wedding"
    draconic = "draconic"
    demon = "demon"
    icons = {}
    icon_path_names = ["red", "holy", "blue_mage", "dg", "volcano", "poss", "war", "cruss", "wk", "draconic", "demon", "wedding"]
    buffer_names = ["red", "holy", "blue_mage", "dg", "volcano", "poss", "war", "cruss", "wk", "draconic", "demon", "wedding"]
    buffer_dropdowns = {}
    buffer_characters = {}
    icon_names = [red, holy, blue_mage, dg, volcano, poss, war, cruss, wk, draconic, demon, wedding]

    for name in icon_path_names:
        icons[name] = find_image_path(name)

    # Display image as button
    #a frame to hold the icon button and other elements
    frame = customtkinter.CTkFrame(master=tab1_frame)
    frame.pack(pady=10, padx=10, fill="x", expand=True)

    spacer_width = 20
    spacer_height = 50
    # Create left spacer frame
    left_spacer = customtkinter.CTkFrame(master=frame, width=5, height=spacer_height, fg_color="transparent")
    left_spacer.pack(side="left")
    # Display icon buttons
    def create_icon_button(name, icon):
        button = customtkinter.CTkButton(master=frame, image=icon, text="", width=50, height=50, fg_color="transparent", corner_radius=0, hover_color="#5D3587")
        button.configure(command=lambda b=button, n=name: toggle_highlight_button(b, n))
        return button

    
    for name, icon in icons.items():
        icon_button = create_icon_button(name, icon)
        icon_button.pack(side="left", padx=5)
    
    right_spacer = customtkinter.CTkFrame(master=frame, width=spacer_width, height=spacer_height, fg_color="transparent")

    frame.update()


        # Function to clear all widgets from a frame
    def clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # Function to show dropdowns for selected buffers
    def show_dropdowns():
        # Clear previous dropdowns and labels
        clear_frame(scrollable_frame)

        # Filter out invalid names from selected_buttons
        filtered_buttons = [button for button in selected_buttons if button in icon_names]

        # Sort the filtered_buttons list based on the icon_names
        sorted_buttons = sorted(filtered_buttons, key=lambda x: icon_names.index(x))

        # Display dropdowns for each selected buffer
        for name in sorted_buttons:
            buffer_display_name = {
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
            }[name]
            label = customtkinter.CTkLabel(master=scrollable_frame, text=f"Select Character for {buffer_display_name}:")
            label.pack(pady=5)
            dropdown = customtkinter.CTkOptionMenu(master=scrollable_frame, values=formatted_ports, fg_color="#453b4d", button_color="#532877", button_hover_color="#3e1f58")
            dropdown.pack(pady=5)
            buffer_dropdowns[name] = dropdown

    set_characters_button = customtkinter.CTkButton(master=tab1_frame, text="Use selected SP cards", command=show_dropdowns, fg_color="#532877", hover_color="#3e1f58")
    set_characters_button.pack(pady=10)

        # Create a CTkScrollableFrame
    scrollable_frame = customtkinter.CTkScrollableFrame(master=tab1_frame, height=250)
    scrollable_frame.pack(fill="both", expand=True)

    spacer_frame = customtkinter.CTkFrame(master=tab1_frame, height=20)
    spacer_frame.pack(pady=20)

    ##OPTIONS CONFIG###
    def validate_delay_input(value_if_allowed):
        # Allow only digits and periods
        if value_if_allowed == "" or value_if_allowed.isdigit() or (value_if_allowed.replace('.', '', 1).isdigit() and value_if_allowed.count('.') < 2):
            return True
        return False
    
    def validate_coords_input(value_if_allowed):
        if len(value_if_allowed) <= 3 and (value_if_allowed == "" or value_if_allowed.isdigit()):
            return True
        return False
    
    def validate_area_input(value_if_allowed):
        if len(value_if_allowed) <= 2 and (value_if_allowed == "" or value_if_allowed.isdigit()):
            return True
        return False
    
    def validate_delaycycle_input(value_if_allowed):
        if len(value_if_allowed) <= 2 and (value_if_allowed == "" or value_if_allowed.isdigit()):
            return True
        return False

    def validate_delaybf_input(value_if_allowed):
        if value_if_allowed == "" or value_if_allowed.isdigit() or (value_if_allowed.replace('.', '', 1).isdigit() and value_if_allowed.count('.') < 2):
            return True
        return False
    
    def saveslashloadtext(message):
        saveslashloadtextvar.configure(text=message)

    def save_options_config():
        config = {
            "delay_between_chars_seconds": delay_between_chars_seconds_var.get(),
            "leave_on_own_checkbox": leave_on_own_checkbox_var.get(),
            "delay_set": delay_set.get(),
            "delay_nopoint_val": delay_nopoint.get(),
            "point_set": point_set.get(),
            "coord_input_x": x_var.get(),
            "coord_input_y": y_var.get(),
            "area_var": area_var.get(),
            "delay_bfpoint_var": delay_bfpoint_var.get(),
            "delay_bfpoint_cycle_var": delay_bfpoint_cycle_var.get()
        }
        ConfigManager.save_config(config, on_success_callback=saveslashloadtext)

    def load_options_config():
        config = ConfigManager.load_config(
            on_success_callback=saveslashloadtext,
            on_error_callback=saveslashloadtext
        )
        if config:
            delay_between_chars_seconds_var.set(config.get("delay_between_chars_seconds", ""))
            leave_on_own_checkbox_var.set(config.get("leave_on_own_checkbox", 0))
            delay_set.set(config.get("delay_set", 0))
            delay_nopoint.set(config.get("delay_nopoint_val", ""))
            point_set.set(config.get("point_set", 0))
            x_var.set(config.get("coord_input_x", ""))
            y_var.set(config.get("coord_input_y", ""))
            area_var.set(config.get("area_var", ""))
            delay_bfpoint_var.set(config.get("delay_bfpoint_var", ""))
            delay_bfpoint_cycle_var.set(config.get("delay_bfpoint_cycle_var", ""))

    options_header_label = customtkinter.CTkLabel(master=tab2_frame, text="", image=header_image)
    options_header_label.pack(padx=10, pady=10)

    config_frame = customtkinter.CTkFrame(master=tab2_frame, height=40, fg_color="transparent")
    config_frame.pack(fill="x", expand=False, pady=(0, 10))

# Add spacer frames on the left and right to center the buttons
    left_spacer = customtkinter.CTkFrame(master=config_frame, width=20, height=40, fg_color="transparent")
    left_spacer.pack(side="left", expand=True)

    saveconfig_button = customtkinter.CTkButton(master=config_frame, text="Save options config", command=save_options_config, fg_color="#532877", hover_color="#3e1f58", height=28)
    saveconfig_button.pack(side="left", padx=5)

    loadconfig_button = customtkinter.CTkButton(master=config_frame, text="Load options config", command=load_options_config, fg_color="#532877", hover_color="#3e1f58", height=28)
    loadconfig_button.pack(side="left", padx=5)

    right_spacer = customtkinter.CTkFrame(master=config_frame, width=20, height=40, fg_color="transparent")
    right_spacer.pack(side="left", expand=True)

    saveslashloadtextvar = customtkinter.CTkLabel(master=tab2_frame, text="")
    saveslashloadtextvar.pack()

    general_options_label = customtkinter.CTkLabel(master=tab2_frame, text="General Options:", font=(None, 18))
    general_options_label.pack()

    general_frame = customtkinter.CTkFrame(master=tab2_frame)
    general_frame.pack(fill="both", expand=False, pady=(0, 10))

    delay_between_chars_label = customtkinter.CTkLabel(master=general_frame, text="Delay between buffers in seconds (2, 2.4, 1.74):")
    delay_between_chars_label.pack(pady=5)

    vcmd = (root.register(validate_delay_input), '%P')

    delay_between_chars_seconds_var = customtkinter.StringVar()
    delay_between_chars_seconds_entry = customtkinter.CTkEntry(master=general_frame, textvariable=delay_between_chars_seconds_var, validate="key", validatecommand=vcmd)
    delay_between_chars_seconds_entry.pack(pady=5)

    leave_on_own_checkbox_var = customtkinter.IntVar()
    leave_on_own_checkbox = customtkinter.CTkCheckBox(master=general_frame, text="Leave miniland with main by yourself", variable=leave_on_own_checkbox_var, fg_color="#532877", hover_color="#3e1f58", border_color="#fff")
    leave_on_own_checkbox.pack(pady=5)

    auto_options_label = customtkinter.CTkLabel(master=tab2_frame, text="Auto Options:", font=(None, 18))
    auto_options_label.pack(pady=10)

    auto_frame = customtkinter.CTkFrame(master=tab2_frame)
    auto_frame.pack(fill="both", expand=True)

    delay_set = customtkinter.IntVar()
    delay_set_check = customtkinter.CTkCheckBox(master=auto_frame, text="Go to miniland after every X seconds", variable=delay_set, fg_color="#532877", hover_color="#3e1f58", border_color="#fff", command=lambda: update_checkboxes(delay_set_check))
    delay_set_check.pack(pady=5)

    delay_set_frame = customtkinter.CTkFrame(master=auto_frame, fg_color="transparent")
    delay_set_frame.pack(pady=10)

    vcmd6 = (root.register(validate_delaybf_input), '%P')

    delay_nopoint = customtkinter.StringVar()
    delay_nopoint_entry = customtkinter.CTkEntry(master=delay_set_frame, textvariable=delay_nopoint, validate="key", validatecommand=vcmd6)
    delay_nopoint_entry.pack(padx=5, side="left")

    seconds_label = customtkinter.CTkLabel(master=delay_set_frame, text="seconds")
    seconds_label.pack(side="left")

    point_set = customtkinter.IntVar()
    point_set_check = customtkinter.CTkCheckBox(master=auto_frame, text="Set buff point - where to go to miniland for buffs", variable=point_set, fg_color="#532877", hover_color="#3e1f58", border_color="#fff", command=lambda: update_checkboxes(point_set_check))
    point_set_check.pack(pady=5)

    set_xy_label = customtkinter.CTkLabel(master=auto_frame, text="Set [X][Y] coordinates of buff point")
    set_xy_label.pack()

    xy_frame = customtkinter.CTkFrame(master=auto_frame, fg_color="transparent")
    xy_frame.pack(pady=10)

    vcmd2 = (root.register(validate_coords_input), '%P')
    #Set x,y buff point.
    x_var = customtkinter.StringVar()
    x_entry = customtkinter.CTkEntry(master=xy_frame, textvariable=x_var, validate="key", validatecommand=vcmd2)
    x_entry.pack(padx=5, side="left")

    y_var = customtkinter.StringVar()
    y_entry = customtkinter.CTkEntry(master=xy_frame, textvariable=y_var, validate="key", validatecommand=vcmd2)
    y_entry.pack(padx=5, side="left")

    #Activate buff point x,y  in the area of somehting cells
    area_label = customtkinter.CTkLabel(master=auto_frame, text="Activate buffing cycle if player in the area of X cells around buff point")
    area_label.pack()

    area_frame = customtkinter.CTkFrame(master=auto_frame, fg_color="transparent")
    area_frame.pack(pady=10)

    vcmd3 = (root.register(validate_area_input), '%P')
    area_var = customtkinter.StringVar()
    area_entry = customtkinter.CTkEntry(master=area_frame, textvariable=area_var, validate="key", validatecommand=vcmd3)
    area_entry.pack(padx=5, side="left")

    delay_bfpoint_label = customtkinter.CTkLabel(master=auto_frame, text="Delay usage of buff point in time (Dont use buff point for X seconds)")
    delay_bfpoint_label.pack()

    delay_bfpoint_frame = customtkinter.CTkFrame(master=auto_frame, fg_color="transparent")
    delay_bfpoint_frame.pack(pady=10)

    vcmd4 = (root.register(validate_delaybf_input), '%P')

    delay_bfpoint_var = customtkinter.StringVar()
    delay_bfpoint_entry = customtkinter.CTkEntry(master=delay_bfpoint_frame, textvariable=delay_bfpoint_var, validate="key", validatecommand=vcmd4)
    delay_bfpoint_entry.pack(padx=5, side="left")

    delay_bfpoint_cycle_label = customtkinter.CTkLabel(master=auto_frame, text="Use buff point when crossed X time (Buff cycle will start when its crossed X time.)")
    delay_bfpoint_cycle_label.pack()

    delay_bfpoint_cycle_frame = customtkinter.CTkFrame(master=auto_frame, fg_color="transparent")
    delay_bfpoint_cycle_frame.pack(pady=10)

    vcmd5 = root.register = (root.register(validate_delaycycle_input), '%P')

    delay_bfpoint_cycle_var = customtkinter.StringVar()
    delay_bfpoint_cycle_entry = customtkinter.CTkEntry(master=delay_bfpoint_cycle_frame, textvariable=delay_bfpoint_cycle_var, validate="key", validatecommand=vcmd5)
    delay_bfpoint_cycle_entry.pack(padx=5, side="left")

    def get_delay_value():
        try:
            delay_value = float(delay_between_chars_seconds_var.get())
            print(f"Delay value: {delay_value} seconds")
            # Use the delay value as needed
        except ValueError:
            delay_value = float(2.6)
            print(f"Delay value: {delay_value} seconds")



    #CONTROL PANEL#

    control_header_label = customtkinter.CTkLabel(master=tab3_frame, text="", image=header_image)
    control_header_label.pack(padx=10, pady=10)

    manual_start_button = customtkinter.CTkButton(master=tab3_frame,text="One time buff [Start]",command=one_time_buff, fg_color="#1f3858", hover_color="#18293e")
    manual_start_button.pack(pady=10)
    
    start_button = customtkinter.CTkButton(master=tab3_frame,text="Automatic buffing [Start]",command=start, fg_color="#337a1e", hover_color="#2a6119")
    start_button.pack(pady=10)

    invite_buffers_button = customtkinter.CTkButton(master=tab3_frame,text="Invite all buffers to miniland",command=invite_players, fg_color="#1f3858", hover_color="#18293e")
    invite_buffers_button.pack(pady=10)


    output_label = customtkinter.CTkLabel(master=tab3_frame, text=f"Output from BuffersBot:", font=(None,18))
    output_label.pack(pady=10)

    output_frame = customtkinter.CTkScrollableFrame(master=tab3_frame, height=150)
    output_frame.pack(fill="both", expand=True)

    out_spacer_frame = customtkinter.CTkFrame(master=tab3_frame, height=20)
    out_spacer_frame.pack(pady=20)

    ###Help/Instructions###

    # Function to create a fancy label
    def create_fancy_label(master, text):
        return customtkinter.CTkLabel(
            master=master,
            text=text,
            fg_color="#532877",  # Purple text color
            font=(None, 12),  # Font size and style
            padx=10,  # Horizontal padding
            pady=5,  # Vertical padding
        )

    # Create a frame for settings
    settings_frame = customtkinter.CTkFrame(master=tab4_frame)
    settings_frame.pack(fill="both", expand=True)

    # Setting 1: Set [X][Y] Coordinates of Buff Point
    set_xy_label = create_fancy_label(settings_frame, "Setting 1: Set [X][Y] Coordinates of Buff Point")
    set_xy_label.pack()

    set_xy_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="Specify the coordinates where the buff point will be placed on the game map.\n Enter the X and Y coordinates in the respective fields.",
        padx=10,
        pady=5
    )
    set_xy_explanation.pack()

    # Setting 2: Activate buffing cycle if player in the area of X cells around buff point
    activate_buff_label = create_fancy_label(settings_frame, "Setting 2: Activate buffing cycle if player in the area of X cells around buff point")
    activate_buff_label.pack()

    activate_buff_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="Define the radius of the area around the buff point where the buffing cycle will be activated if the player enters.\n Enter the number of cells around the buff point.",
        padx=10,
        pady=5
    )
    activate_buff_explanation.pack()

    # Setting 3: Delay usage of buff point in time (Don't use buff point for X seconds)
    delay_time_label = create_fancy_label(settings_frame, "Setting 3: Delay usage of buff point in time (Don't use buff point for X seconds)")
    delay_time_label.pack()

    delay_time_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="Specify the duration of time in seconds that the buff point will not be used after activation.\n Enter the desired delay time in seconds.",
        padx=10,
        pady=5
    )
    delay_time_explanation.pack()

    # Setting 4: Delay usage of buff point in cycles (Don't use buff point, unless crossed X times)
    delay_cycles_label = create_fancy_label(settings_frame, "Setting 4: Delay usage of buff point in cycles (Don't use buff point, unless crossed X times)")
    delay_cycles_label.pack()

    delay_cycles_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="Set the number of times the player must cross the specified coordinates before the buff point is used.\n Enter the desired number of crossings required.",
        padx=10,
        pady=5
    )
    delay_cycles_explanation.pack()

    #AUTOSTART
    delay_cycles_label = create_fancy_label(settings_frame, "Automatic Buffing Button")
    delay_cycles_label.pack()

    delay_cycles_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="When started, main character (if standing on buff point) will be buffed (first cycle).\nThen continues by your conditions.\nYou can set delay in time or you can set delay by crossings of bf point\nWhen you want to stop the function, just click stop.\n",
        padx=10,
        pady=5
    )
    delay_cycles_explanation.pack()


    delay_cycles_explanation = customtkinter.CTkLabel(
        master=settings_frame,
        text="Do not change .ini files in PB_settings / unless you know what you are doing!\nVideos of each function working are in folder video_examples.",
        padx=10,
        pady=10
    )
    delay_cycles_explanation.pack()



        # Create tab buttons
    tab1_button = customtkinter.CTkButton(master=top_frame, text="Character config", command=lambda: show_frame(tab1_frame), fg_color="#532877", hover_color="#3e1f58")
    tab1_button.pack(side="left", padx=10, pady=10)

    tab2_button = customtkinter.CTkButton(master=top_frame, text="Options config", command=lambda: show_frame(tab2_frame), fg_color="#59525F", hover_color="#764F97")
    tab2_button.pack(side="left", padx=10, pady=10)

    tab3_button = customtkinter.CTkButton(master=top_frame, text="Control Panel", command=lambda: show_frame(tab3_frame), fg_color="#59525F", hover_color="#764F97")
    tab3_button.pack(side="left", padx=10, pady=10)

    tab4_button = customtkinter.CTkButton(master=top_frame, text="Instructions/Help", command=lambda: show_frame(tab4_frame), fg_color="#59525F", hover_color="#764F97")
    tab4_button.pack(side="right", padx=10, pady=10)

    show_frame(tab1_frame)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()