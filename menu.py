# menu.py
import os
import sys
import subprocess
import time
import platform
from threading import Thread
from queue import Queue, Empty
import json

# Platform-specific key input handling
if platform.system() == 'Windows':
    import msvcrt
else:
    import tty
    import termios
    import sys
    import select

CONFIG_FILE = 'settings_config.json'

def load_config():
    """Load the configuration from the config file."""
    try:
        if not os.path.exists(CONFIG_FILE):
            # If the file doesn't exist, create it with default values
            default_config = {
                "snipe_options": {
                    "raydium": True, "pump_fun": True, "boosted": False,
                    "program_ids": {"raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", "pump_fun": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"},
                    "instructions": {"raydium": "Program log: initialize2: InitializeInstruction2", "pump_fun": "Program log: Instruction: CreatePool"}
                },
                "rugcheck_config": {
                    "rugcheck_enabled": True, "check_creator": True, "check_mint_authority": True,
                    "check_freeze_authority": True, "check_liquidity": True, "min_liquidity": 5.0,
                    "check_top_holders": True, "max_top_holders_percentage": 70.0,
                    "risk_score_threshold": 40, "include_solscan_link": True,
                    "include_dexscreener_link": True, "send_token_image": True
                }
            }
            save_config(default_config)
            return default_config
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading config: {e}. Loading default config.")
        # Return a default config in case of error
        return {
            "snipe_options": {"raydium": True, "pump_fun": True, "boosted": False},
            "rugcheck_config": {"rugcheck_enabled": True, "min_liquidity": 5.0, "max_top_holders_percentage": 70.0, "risk_score_threshold": 40}
        }

def save_config(config):
    """Save the configuration to the config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        # Get terminal width for centering
        term_width = os.get_terminal_size().columns
        save_message = "Settings saved successfully!"
        x_padding = max((term_width - len(save_message)) // 2, 0)
        print(' ' * x_padding + save_message)
        time.sleep(1)
    except IOError as e:
        print(f"Error saving config: {e}")
        time.sleep(1)

class ProcessManager:
    def __init__(self, script_name, log_file):
        self.script_name = script_name
        self.process = None
        self.log_file = log_file
        self.log_queue = Queue()
        self.running = False

    def start(self):
        if not self.process or self.process.poll() is not None:
            self.running = True
            with open(self.log_file, 'w') as f:
                f.write(f"--- Starting {self.script_name} ---\n")
            self.process = subprocess.Popen(
                [sys.executable, self.script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            Thread(target=self.log_reader, daemon=True).start()
            return True
        return False

    def log_reader(self):
        while self.running:
            if self.process and self.process.stdout:
                try:
                    line = self.process.stdout.readline()
                    if line:
                        self.log_queue.put(line)
                        with open(self.log_file, 'a') as f:
                            f.write(line)
                    else:
                        # Process has likely ended
                        if self.process.poll() is not None:
                            break
                        time.sleep(0.1)
                except Exception:
                    break
            else:
                break
        self.running = False


    def stop(self):
        if self.process and self.process.poll() is None:
            self.running = False
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            return True
        return False

    def get_logs(self):
        lines = []
        while True:
            try:
                lines.append(self.log_queue.get_nowait())
            except Empty:
                break
        return ''.join(lines)

    def get_status(self):
        if self.process and self.process.poll() is None:
            return "RUNNING"
        return "STOPPED"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    if platform.system() == 'Windows':
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            return {'H': 'up', 'P': 'down'}.get(key.decode(errors='ignore'), 'unknown')
        elif key == b'\r':
            return 'enter'
        return key.decode(errors='ignore')
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch_rest = sys.stdin.read(2)
                ch += ch_rest
                return {'[A': 'up', '[B': 'down'}.get(ch[1:], 'unknown')
            elif ch == '\r':
                return 'enter'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def draw_menu(options, selected_index):
    clear_screen()
    art = r"""
     █████    █████                                    
    ░░███    ░░███                                     
     ░███     ░███         ██████  █████ █████  ██████ 
     ░███     ░███        ███░░███░░███ ░░███  ███░░███
     ░███     ░███       ░███ ░███ ░███  ░███ ░███████ 
     ░███     ░███      █░███ ░███ ░░███ ███  ░███░░░  
     █████    ███████████░░██████   ░░█████   ░░██████ 
    ░░░░░    ░░░░░░░░░░░  ░░░░░░     ░░░░░     ░░░░░░  
                                                       
                                                       
                                                       
      █████████     ███████    █████                   
     ███░░░░░███  ███░░░░░███ ░░███                    
    ░███    ░░░  ███     ░░███ ░███                    
    ░░█████████ ░███      ░███ ░███                    
     ░░░░░░░░███░███      ░███ ░███                    
     ███    ░███░░███     ███  ░███      █             
    ░░█████████  ░░░███████░   ███████████             
     ░░░░░░░░░     ░░░░░░░    ░░░░░░░░░░░
    """
    lines = art.split('\n')
    width = max(len(line) for line in lines)
    height = len(lines)
    
    term_width = os.get_terminal_size().columns
    term_height = os.get_terminal_size().lines
    
    x_padding = max((term_width - width) // 2, 0)
    y_padding = max((term_height - height - len(options) - 7) // 2, 0)
    
    print('\n' * y_padding)
    for line in lines:
        print(' ' * x_padding + line)
    print("\n" + ' ' * ((term_width - 28) // 2))
    print(' ' * ((term_width - 28) // 2) + "Unstable SOL Trading Bot v1.0")
    print("\n" + ' ' * ((term_width - 20) // 1))
    
    menu_width = max(len(option) for option in options) + 4
    menu_x_padding = max((term_width - menu_width) // 2, 0)
    
    for i, option in enumerate(options):
        if i == selected_index:
            print(' ' * menu_x_padding + f" > {option}")
        else:
            print(' ' * menu_x_padding + f"   {option}")
    print('\n' + ' ' * menu_x_padding + '-' * (menu_width - 2))
    print(' ' * menu_x_padding + "Use ↑/↓ to Navigate, Enter to Select")

def draw_settings_submenu(title, options, selected_index, config, config_key):
    clear_screen()
    art = r"""
      ░░░░░░
  ░░░░      ░░░░
░░    ██████    ░░
░░  ██████████  ░░
░░  ██████████  ░░
░░    ██████    ░░
  ░░░░      ░░░░
      ░░░░░░
"""
    
    lines = art.split('\n')
    width = max(len(line) for line in lines)
    
    term_width = os.get_terminal_size().columns
    term_height = os.get_terminal_size().lines
    
    x_padding_art = max((term_width - width) // 2, 0)
    
    menu_height = len(options) + 7
    total_height = len(lines) + menu_height
    y_padding = max((term_height - total_height) // 2, 0)
    
    print('\n' * y_padding)
    for line in lines:
        print(' ' * x_padding_art + line)

    title_line = f"--- {title} ---"
    x_padding_title = max((term_width - len(title_line)) // 2, 0)
    print(f"\n{' ' * x_padding_title}{title_line}\n")
    
    max_len = 0
    for option_text, key in options:
        value = config[config_key].get(key)
        display_value = ""
        if isinstance(value, bool):
            display_value = "✅ On" if value else "❌ Off"
        else:
            display_value = str(value)
        max_len = max(max_len, len(f"{option_text}: {display_value}"))

    menu_width = max_len + 6
    menu_x_padding = max((term_width - menu_width) // 2, 0)

    for i, (option_text, key) in enumerate(options):
        value = config[config_key].get(key)
        display_value = ""
        if isinstance(value, bool):
            display_value = "✅ On" if value else "❌ Off"
        else:
            display_value = str(value)
        
        line = f"{option_text}: {display_value}" 
        
        if i == selected_index:
            print(' ' * menu_x_padding + f" > {line}")
        else:
            print(' ' * menu_x_padding + f"   {line}")
            
    print("\n" + ' ' * menu_x_padding + "-" * (menu_width - 2))
    print(' ' * menu_x_padding + "Use ↑/↓ to Navigate, Enter to change.")
    print(' ' * menu_x_padding + "Press 'b' to go Back (and save).")

def edit_numeric_value(prompt, current_value):
    clear_screen()
    term_width = os.get_terminal_size().columns
    term_height = os.get_terminal_size().lines
    
    prompt_line = f"--- {prompt} ---"
    input_prompt = f"Enter new value (current: {current_value}): "
    
    y_padding = max((term_height - 5) // 2, 0)
    x_padding_prompt = max((term_width - len(prompt_line)) // 2, 0)
    
    print('\n' * y_padding)
    print(' ' * x_padding_prompt + prompt_line)
    
    x_padding_input = max((term_width - len(input_prompt) - 10) // 2, 0)
    print('\n' + ' ' * x_padding_input, end='')
    
    try:
        new_value_str = input(input_prompt)
        if new_value_str:
            if isinstance(current_value, int):
                return int(new_value_str)
            elif isinstance(current_value, float):
                return float(new_value_str)
        return current_value
    except ValueError:
        error_msg = "Invalid input. Please enter a number."
        x_padding_error = max((term_width - len(error_msg)) // 2, 0)
        print('\n' + ' ' * x_padding_error + error_msg)
        time.sleep(1.5)
        return current_value

def settings_submenu(title, options, config, config_key):
    current_selection = 0
    while True:
        draw_settings_submenu(title, options, current_selection, config, config_key)
        key = get_key()

        if key == 'up':
            current_selection = (current_selection - 1) % len(options)
        elif key == 'down':
            current_selection = (current_selection + 1) % len(options)
        elif key == 'enter':
            _option_text, key_name = options[current_selection]
            value = config[config_key][key_name]
            if isinstance(value, bool):
                config[config_key][key_name] = not value
            elif isinstance(value, (int, float)):
                config[config_key][key_name] = edit_numeric_value(f"Edit {_option_text}", value)
        elif key == 'b':
            save_config(config)
            break

def settings_menu():
    config = load_config()
    
    menu_options = [
        "Snipe Options",
        "Rugcheck Config",
        "Back to Main Menu"
    ]
    current_selection = 0

    while True:
        clear_screen()
        art = r"""
      ░░░░░░
  ░░░░      ░░░░
░░    ██████    ░░
░░  ██████████  ░░
░░  ██████████  ░░
░░    ██████    ░░
  ░░░░      ░░░░
      ░░░░░░
        """
        
        lines = art.split('\n')
        width = max(len(line) for line in lines)
        
        term_width = os.get_terminal_size().columns
        term_height = os.get_terminal_size().lines
        
        x_padding_art = max((term_width - width) // 2, 0)
        
        menu_height = len(menu_options) + 5
        total_height = len(lines) + menu_height
        y_padding = max((term_height - total_height) // 2, 0)
        
        print('\n' * y_padding)
        for line in lines:
            print(' ' * x_padding_art + line)

        title_line = "--- Settings ---"
        x_padding_title = max((term_width - len(title_line)) // 2, 0)
        print(f"\n{' ' * x_padding_title}{title_line}\n")

        menu_width = max(len(option) for option in menu_options) + 4
        menu_x_padding = max((term_width - menu_width) // 2, 0)

        for i, option in enumerate(menu_options):
            if i == current_selection:
                print(' ' * menu_x_padding + f" > {option}")
            else:
                print(' ' * menu_x_padding + f"   {option}")
        
        print("\n" + ' ' * menu_x_padding + "-" * (menu_width - 2))
        print(' ' * menu_x_padding + "Use ↑/↓ to Navigate, Enter to select.")

        key = get_key()

        if key == 'up':
            current_selection = (current_selection - 1) % len(menu_options)
        elif key == 'down':
            current_selection = (current_selection + 1) % len(menu_options)
        elif key == 'enter':
            if current_selection == 0: # Snipe Options
                snipe_options = [
                    ("Raydium Sniping", "raydium"),
                    ("Pump.fun Sniping", "pump_fun"),
                    ("Boosted Tokens Check", "boosted")
                ]
                settings_submenu("Snipe Options", snipe_options, config, "snipe_options")
            elif current_selection == 1: # Rugcheck Config
                rugcheck_options = [
                    ("Enable Rugcheck", "rugcheck_enabled"),
                    ("Check Mint Authority", "check_mint_authority"),
                    ("Check Freeze Authority", "check_freeze_authority"),
                    ("Check Top Holders", "check_top_holders"),
                    ("Max Top Holders %", "max_top_holders_percentage"),
                    ("Risk Score Threshold", "risk_score_threshold"),
                    ("Send Token Image", "send_token_image")
                ]
                settings_submenu("Rugcheck Config", rugcheck_options, config, "rugcheck_config")
            elif current_selection == 2: # Back
                break

def main_menu(hunter_manager, updater_manager):
    current_selection = 0
    while True:
        hunter_status = hunter_manager.get_status()
        updater_status = updater_manager.get_status()
        
        menu_options = [
            f"Token Hunter        [{hunter_status}]",
            "View Hunter Logs",
            f"Data Updater        [{updater_status}]",
            "View Updater Logs",
            "Settings",
            "Exit"
        ]
        
        draw_menu(menu_options, current_selection)
        key = get_key()
        
        if key == 'up':
            current_selection = (current_selection - 1) % len(menu_options)
        elif key == 'down':
            current_selection = (current_selection + 1) % len(menu_options)
        elif key == 'enter':
            if current_selection == 0:  # Start/Stop Hunting
                if hunter_status == "RUNNING":
                    hunter_manager.stop()
                else:
                    hunter_manager.start()
            elif current_selection == 1:  # View Hunter Logs
                return 'view_hunter_logs'
            elif current_selection == 2:  # Start/StopUpdater
                if updater_status == "RUNNING":
                    updater_manager.stop()
                else:
                    updater_manager.start()
            elif current_selection == 3: # View Updater Logs
                return 'view_updater_logs'
            elif current_selection == 4:  # Settings
                return 'settings'
            elif current_selection == 5:  # Exit
                hunter_manager.stop()
                updater_manager.stop()
                clear_screen()
                print("\n👋 Exiting...")
                sys.exit()

def view_logs(manager):
    clear_screen()
    print(f"--- Live Logs for {manager.script_name} (Press any key to return) ---\n")
    try:
        while True:
            logs = manager.get_logs()
            if logs:
                print(logs, end='')

            # Check for key press to exit
            if platform.system() == 'Windows':
                if msvcrt.kbhit():
                    break
            else:
                # Use select for non-blocking check on Linux/macOS
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    break
            
            time.sleep(0.2)
    except Exception:
        pass
    # Consume the key press that broke the loop
    get_key()


def main():
    hunter_manager = ProcessManager('ILove.py', 'hunter.log')
    updater_manager = ProcessManager('ultimate_utils.py', 'updater.log')
    
    while True:
        action = main_menu(hunter_manager, updater_manager)
        
        if action == 'view_hunter_logs':
            view_logs(hunter_manager)
        elif action == 'view_updater_logs':
            view_logs(updater_manager)
        elif action == 'settings':
            settings_menu()
        clear_screen()

if __name__ == "__main__":
    main()