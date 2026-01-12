"""
Helper script to update global variable references to app_state in main.py
Run this once to automatically update all global references.
"""

replacements = [
    ("stop_thread", "app_state.stop_thread"),
    ("buffers_can_buff", "app_state.buffers_can_buff"),
    ("buffers_buffing", "app_state.buffers_buffing"),
    ("one_time_running", "app_state.one_time_running"),
    ("ownercharid", "app_state.ownercharid"),
    ("got_invite ", "app_state.got_invite "),  # Space to avoid got_invite2/3
    ("got_invite2", "app_state.got_invite2"),
    ("got_invite3", "app_state.got_invite3"),
    ("mainleft", "app_state.mainleft"),
    ("cant_invite", "app_state.cant_invite"),
    ("playerleave", "app_state.playerleave"),
    ("main1inmini", "app_state.main1inmini"),
    ("main2inmini", "app_state.main2inmini"),
    ("main3inmini", "app_state.main3inmini"),
    ("main2left", "app_state.main2left"),
    ("main3left", "app_state.main3left"),
    ("are2", "app_state.are2"),
    ("are3", "app_state.are3"),
    ("others_stop", "app_state.others_stop"),
    ("others_leave", "app_state.others_leave"),
    ("buffers_can_buff_red", "app_state.buffers_can_buff_red"),
    ("buffers_can_buff_holy", "app_state.buffers_can_buff_holy"),
    ("buffers_can_buff_blue_mage", "app_state.buffers_can_buff_blue_mage"),
    ("buffers_can_buff_dg", "app_state.buffers_can_buff_dg"),
    ("buffers_can_buff_volcano", "app_state.buffers_can_buff_volcano"),
    ("buffers_can_buff_poss", "app_state.buffers_can_buff_poss"),
    ("buffers_can_buff_war", "app_state.buffers_can_buff_war"),
    ("buffers_can_buff_cruss", "app_state.buffers_can_buff_cruss"),
    ("buffers_can_buff_wk", "app_state.buffers_can_buff_wk"),
    ("buffers_can_buff_demon", "app_state.buffers_can_buff_demon"),
    ("buffers_can_buff_wedding", "app_state.buffers_can_buff_wedding"),
    ("buffer_classes", "app_state.buffer_classes"),
    ("timer_end", "app_state.timer_end"),
    ("'timer'", "'app_state.timer'"),  # For timer checks
]

def update_file():
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.content()
    
    # Remove all "global" declarations
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        # Skip lines that are just global declarations
        if line.strip().startswith("global "):
            continue
        new_lines.append(line)
    
    content = "\n".join(new_lines)
    
    # Make replacements
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("Updated main.py successfully!")

if __name__ == "__main__":
    update_file()
