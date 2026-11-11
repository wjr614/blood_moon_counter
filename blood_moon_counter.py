# Import
import pymem
import struct

import os
from pathlib import Path
import configparser

import math

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# Initialize
roaming_appdata = os.getenv('APPDATA')
program_folder = Path(__file__).resolve().parent
config_path = program_folder / "config.ini"
connection_status = False

# Unchanged Vars
base_search_term = "Init Wii U memory space (base: "
base_length = len("0x000001cbed8a0000")
timer_offset = 2685073324
scheduled_offset = 0x682EDB7F
scheduled_offset_2 = 0xA008C790
cemu_ping = int(1000 / 15)
total = 2520
unit_conversion_factor = 4

# Dynamic Vars
cheats_enabled = False

# Config innit
config = configparser.ConfigParser()
config_path.touch()
config.read(config_path)

def verify_config():
    if not "path" in config:
        config['path'] = {}
    if not "cemu_folder" in config["path"]:
        config["path"]["cemu_folder"] = ""
    if not "preferences" in config:
        config["preferences"] = {}
    if not "use_rounding" in config["preferences"]:
        config["preferences"]["use_rounding"] = "True"
    if not "agreed_to_cheats_warning" in config["preferences"]:
        config["preferences"]["agreed_to_cheats_warning"] = "False"
        

def update_config_file():
    with open(config_path, 'w') as configfile:
        config.write(configfile)

verify_config()
update_config_file()

def select_file():
    path = filedialog.askdirectory(
        title = "Select Cemu Folder",
        initialdir = roaming_appdata,
    )
    if path:
        verify_config()
        config['path']['cemu_folder'] = path
        update_config_file()
        path_label.config(text="Cemu Folder: " + config["path"]["cemu_folder"])

def startup():
    # Read CEMU
    try:
        with open(Path(config["path"]["cemu_folder"]) / "log.txt", "r", encoding="utf-8") as file:
            log = file.read()
            base_start_index = log.find(base_search_term) + len(base_search_term)

            log_check(log.find(base_search_term))

            base_string = log[base_start_index:base_start_index+base_length]
            base = int(base_string, 16)
        new_host_timer = base + timer_offset
        new_host_schedule = base + scheduled_offset
        new_host_schedule_2 = base + scheduled_offset_2
        pm = pymem.Pymem("Cemu.exe")
        connection_loop(pm, new_host_timer, new_host_schedule, new_host_schedule_2)
        return new_host_timer, new_host_schedule, pm
    except FileNotFoundError as e:
        show_error("FileNotFoundError", "Couldn't find Cemu's Log.txt, make sure the Cemu Folder path is set correctly and BOTW is running.")
    except ValueError as e:
        show_error("ValueError", "Couldn't find Cemu Base memory address, make sure BOTW is running before connecting")
    except Exception as e:
        show_error(type(e).__name__, e)   

def log_check(index):
    if index == -1:
        raise ValueError("Couldn't find Cemu Base memory address, make sure BOTW is running before connecting")

def set_moon(pm, address, value):
    try:
        if not cheats_enabled or not connection_status:
            raise Exception("Cheats are disabled, something went wrong")
        set_bytes = struct.pack('>f', value)
        pm.write_bytes(address, set_bytes, 4)
    except Exception as e:
        show_error(type(e).__name__, str(e))

def read_moon(pm, address):
    read_bytes = pm.read_bytes(address, 4)
    moon_value = struct.unpack(">f", read_bytes)[0]
    return moon_value

def set_byte(pm, address, value):
    try:
        if not cheats_enabled or not connection_status:
            raise Exception("Cheats are disabled, something went wrong")
        pm.write_bytes(address, bytes([value]), 1)
    except Exception as e:
        show_error(type(e).__name__, str(e))

def read_byte(pm, address):
    try:
        return pm.read_bytes(address, 1)[0]
    except Exception as e:
        show_error(type(e).__name__, str(e))

def show_error(title, message):
    messagebox.showerror(title, message)

def check_cemu(pm, timer_address):
    global connection_status
    try:
        moon_value = read_moon(pm, timer_address)

        if not math.isfinite(moon_value):
            raise ValueError("Invalid Blood Moon Counter Value")

        connection_status = True
        connected_label.config(fg = "green", text="Connection to BOTW: "+ str(connection_status))
        start_button.config(state="disabled")
        return moon_value
    
    except Exception:
        connection_status = False
        connected_label.config(text="Connection to BOTW: "+ str(connection_status), fg = "red")
        start_button.config(state="normal")

def connection_loop(pm, timer_address, schedule_address, schedule_address_2):
    if connection_status:
        moon_value = check_cemu(pm, timer_address)
        scheduled = read_byte(pm, schedule_address)
        show_connected_widgets(moon_value, scheduled, timer_address)

        if cheats_enabled:
            show_cheat_widgets(pm, timer_address, schedule_address, schedule_address_2)
        else:
            hide_cheat_widgets()

        window.after(cemu_ping, connection_loop, pm, timer_address, schedule_address, schedule_address_2)
    else:
        hide_connected_widgets()
        hide_cheat_widgets()

# Cheats
def write_value(pm, timer_address, seconds):
    try:
        value = float(number_entry.get())
        if seconds:
            value = total - (value / unit_conversion_factor)

        if not math.isfinite(value):
            show_error("Invalid Number", "Please enter a finite number.")
            return

        if value < 0 or value > total:
            if not messagebox.askyesno(
                "Are you sure?",
                f"Entering values outside of the expected range\n(0 - {total} for timer; 0 - {total * unit_conversion_factor} in seconds left) "
                "can cause memory issues or save corruption.\n\n"
                "Do you still wish to continue?"
            ):
                return
        set_moon(pm, timer_address, value)
    except ValueError:
        show_error("ValueError", "Please enter a valid number")
        return
    except Exception as e:
        show_error(type(e).__name__, str(e))
        return

def add_value(pm, timer_address, value):
    moon_value = read_moon(pm, timer_address)
    set_moon(pm, timer_address, moon_value + value)

# GUI
def toggle_cheats():
    global cheats_enabled

    if not cheats_enabled:
        if not config["preferences"]["agreed_to_cheats_warning"] == "True":
            if not messagebox.askyesno(
                "Enable Cheats?",
                "Cheats directly modify BOTW's memory.\n\n"
                "Memory addresses may differ between game versions, "
                "potentially causing crashes or save corruption.\n\n"
                "Make sure you've backed up your save file and "
                "visually check that the countdowns look correct.\n\n"
                "Do you wish to continue?"
            ):
                return
        config["preferences"]["agreed_to_cheats_warning"] = "True"
        update_config_file()
        cheats_enabled = True
    else:
        cheats_enabled = False

def hide_cheat_widgets():
    toggle_scheduled_moon_button.grid_remove()
    number_entry.grid_remove()
    write_value_button.grid_remove()
    write_seconds_button.grid_remove()

    reset_moon_button.grid_remove()
    remove_minute_button.grid_remove()
    remove_five_minute_button.grid_remove()
    remove_thirty_minute_button.grid_remove()

def show_cheat_widgets(pm, timer_address, schedule_address, schedule_address_2):
    toggle_scheduled_moon_button.config(command = lambda: toggle_schedule(pm, schedule_address, schedule_address_2))
    toggle_scheduled_moon_button.grid(row = 6, column = 1, padx = 10, pady = 5, sticky = "w")

    number_entry.grid(row = 7, column = 1, padx = 10, pady = 5, sticky = "w")

    write_value_button.config(command = lambda: write_value(pm, timer_address, False))
    write_value_button.grid(row = 8, column = 1, padx = 10, pady = 5, sticky = "w")

    write_seconds_button.config(command = lambda: write_value(pm, timer_address, True))
    write_seconds_button.grid(row = 9, column = 1, padx = 10, pady = 5, sticky = "w")

    reset_moon_button.config(command = lambda: set_moon(pm, timer_address, 0))
    reset_moon_button.grid(row = 7, column = 0, padx = 10, pady = 5, sticky = "")

    remove_minute_button.config(command = lambda: add_value(pm, timer_address, (60 / unit_conversion_factor)))
    remove_minute_button.grid(row = 8, column = 0, padx = 10, pady = 5, sticky = "")

    remove_five_minute_button.config(command = lambda: add_value(pm, timer_address, (300 / unit_conversion_factor)))
    remove_five_minute_button.grid(row = 9, column = 0, padx = 10, pady = 5, sticky = "")

    remove_thirty_minute_button.config(command = lambda: add_value(pm, timer_address, ((30 * 60) / unit_conversion_factor)))
    remove_thirty_minute_button.grid(row = 10, column = 0, padx = 10, pady = 5, sticky = "")
    

def hide_connected_widgets():
    cemu_base_label.grid_remove()
    moon_count_label.grid_remove()
    moon_count_button.grid_remove()
    moon_countdown_label.grid_remove()
    cheats_button.grid_remove()

def show_connected_widgets(moon_value, scheduled, timer_address):
    cemu_base_label.config(text = f"Base Address: {hex(timer_address - timer_offset)}")
    cemu_base_label.grid(row = 2, column = 1, padx = 10, pady = (0, 30), sticky = "nw")

    cemu_base_copy_button.config(text = f"Copy", width = 10, command = lambda: (window.clipboard_clear(), window.clipboard_append(f"{hex(timer_address - timer_offset)}")))
    cemu_base_copy_button.grid(row = 2, column = 0, padx = 10, pady = (0, 30), sticky = "")

    time_left, negative = time_convert(moon_value)

    if config["preferences"]["use_rounding"] == "True":
        moon_count_label.config(text = f"Moon Timer: {moon_value:.2f} / {total}")
    else:
        moon_count_label.config(text = f"Moon Timer: {moon_value} / {total}")
    moon_count_label.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = "w")

    if config["preferences"]["use_rounding"] == "True":
        moon_count_button.config(text = "Toggle Rounding: On")
    else:
        moon_count_button.config(text = "Toggle Rounding: Off")
    moon_count_button.grid(row = 3, column = 0, padx = 10, pady = 5, sticky = "")

    moon_countdown_label.config(text = f"Countdown: {time_left}   Seconds: {int((total-moon_value) * unit_conversion_factor)}", fg = "red" if negative else "black")
    moon_countdown_label.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = "w")

    scheduled_moon_label.config(text = f"Blood Moon Scheduled: {True if scheduled == 1 else False}")
    scheduled_moon_label.grid(row = 5, column = 1, padx = 10, pady = 2, sticky = "w")

    cheats_button.config(text = "Toggle Cheats: On" if cheats_enabled else "Toggle Cheats: Off", fg = "red" if cheats_enabled else "black")
    cheats_button.grid(row = 6, column = 0, padx = 10, pady = 5, sticky = "")

def toggle_schedule(pm, schedule_address, schedule_address_2):
    scheduled_moon = read_byte(pm, schedule_address)
    if scheduled_moon == 1:
        scheduled_moon = 0
    else: scheduled_moon = 1
    set_byte(pm, schedule_address, scheduled_moon)
    set_byte(pm, schedule_address_2, scheduled_moon)

def time_convert(moon_value):
    negative = ""
    time_left = int((total - moon_value) * unit_conversion_factor)

    if time_left < 0:
        time_left = abs(time_left)
        negative = "-"

    hours = time_left // 3600
    minutes = (time_left % 3600) // 60
    seconds = time_left % 60
    return f"{negative}{hours:02d}:{minutes:02d}:{seconds:02d}", negative

def toggle_rounding():
    if config["preferences"]["use_rounding"] == "True":
        config["preferences"]["use_rounding"] = "False"
    else:
        config["preferences"]["use_rounding"] = "True"
    update_config_file()

def validate_number(value):
    if value in ("", "-", ".", "-."):
        return True

    if " " in value or "nan" in value.lower() or "inf" in value.lower():
        return False

    try:
        float(value)
        return True
    except ValueError:
        return False

window = tk.Tk()
window.title("BOTW Blood Moon Tool")
window.geometry("550x450")
window.grid_columnconfigure(0, minsize = 200)

path_label = tk.Label(window, text = "Cemu Folder: " + config["path"]["cemu_folder"])
path_label.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = "w")

cemu_folder_button = tk.Button(window, text = "Set Cemu Folder", command = select_file)
cemu_folder_button.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "")

start_button = tk.Button(window, text = "Connect to BOTW", command = startup)
start_button.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = "")

connected_label = tk.Label(window, text = "Connection to BOTW: "+ str(connection_status), fg = "red")
connected_label.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = "w")

cemu_base_label = tk.Label(window)
cemu_base_copy_button = tk.Button(window)

moon_count_label = tk.Label(window)
moon_count_button = tk.Button(window, width = 18, command = toggle_rounding)

moon_countdown_label = tk.Label(window)

scheduled_moon_label = tk.Label(window)
toggle_scheduled_moon_button = tk.Button(window, text = "Toggle Scheduled Blood Moon")

# Cheats
cheats_button = tk.Button(window, command = toggle_cheats)

validate_command = window.register(validate_number)

number_entry = tk.Entry(window, width = 15, validate = "key", validatecommand = (validate_command, "%P"))
write_value_button = tk.Button(window, text = "Set Timer Value")
write_seconds_button = tk.Button(window, text = "Set Seconds Left")

reset_moon_button = tk.Button(window, text = "Reset Countdown")
remove_minute_button = tk.Button(window, text = "Remove 1 Minute")
remove_five_minute_button = tk.Button(window, text = "Remove 5 Minutes")
remove_thirty_minute_button = tk.Button(window, text = "Remove 30 Minutes")

window.mainloop()