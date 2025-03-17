# menu.py
import os
import sys
import subprocess
import time
import platform
from threading import Thread
from queue import Queue, Empty

# Platform-specific key input handling
if platform.system() == 'Windows':
    import msvcrt
else:
    import tty
    import termios
    import sys

class HunterManager:
    def __init__(self):
        self.process = None
        self.log_file = "ILove.log"
        self.log_queue = Queue()
        self.running = False

    def start_hunt(self):
        if not self.process or self.process.poll() is not None:
            self.running = True
            with open(self.log_file, 'w') as f:
                f.write("")
            self.process = subprocess.Popen(
                [sys.executable, 'ILove.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            Thread(target=self.log_reader, daemon=True).start()
            return True
        return False

    def log_reader(self):
        while self.running:
            line = self.process.stdout.readline()
            if line:
                self.log_queue.put(line)
                with open(self.log_file, 'a') as f:
                    f.write(line)
            else:
                time.sleep(0.1)

    def stop_hunt(self):
        if self.process and self.process.poll() is None:
            self.running = False
            self.process.terminate()
            self.process.wait()
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

class TerminalUI:
    MIN_HEIGHT = 5
    MIN_WIDTH = 20

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    if platform.system() == 'Windows':
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            return {'H': 'up', 'P': 'down'}.get(key.decode(), 'unknown')
        elif key == b'\r':
            return 'enter'
        return 'unknown'
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch += sys.stdin.read(2)
                return {'[A': 'up', '[B': 'down'}.get(ch[1:], 'unknown')
            elif ch == '\r':
                return 'enter'
            return 'unknown'
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
    y_padding = max((term_height - height) // 2, 0)
    
    print('\n' * y_padding)
    for line in lines:
        print(' ' * x_padding + line)
    
    print("\n" + "="*20)
    print("Unstable SOL Trading Bot v1.0")
    print("="*20)
    
    menu_width = max(len(option) for option in options) + 4
    menu_x_padding = max((term_width - menu_width) // 2, 0)
    
    for i, option in enumerate(options):
        if i == selected_index:
            print(' ' * menu_x_padding + f" > {option}")
        else:
            print(' ' * menu_x_padding + f"   {option}")
    print("\n" + ' ' * menu_x_padding + "Use ↑/↓ to navigate | Enter to select | Hold Enter on 'Hunt' to stop")

def main_menu(manager):
    menu_options = [
        "Start Hunting       🚀",
        "View Live Logs      📜",
        "Check Status       ✅",
        "Exit                🚪"
    ]
    current_selection = 0
    while True:
        draw_menu(menu_options, current_selection)
        key = get_key()
        
        if key == 'up':
            current_selection = max(0, current_selection - 1)
        elif key == 'down':
            current_selection = min(len(menu_options)-1, current_selection + 1)
        elif key == 'enter':
            if current_selection == 0:  # Start Hunting
                if manager.process and manager.process.poll() is None:
                    return 'view'
                if manager.start_hunt():
                    return 'view'
            elif current_selection == 1:  # View Logs
                return 'view'
            elif current_selection == 2:  # Check Status
                return 'status'
            elif current_selection == 3:  # Exit
                manager.stop_hunt()
                clear_screen()
                print("\n👋 Exiting...")
                sys.exit()

def view_logs(manager):
    clear_screen()
    print("=== Live Logs (Press ESC to return) ===\n")
    start_time = time.time()
    try:
        while True:
            logs = manager.get_logs()
            if logs:
                print(logs, end='')
            
            # Check for ESC key
            if platform.system() == 'Windows':
                if msvcrt.kbhit() and msvcrt.getch() == b'\x1b':
                    break
            else:
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    if sys.stdin.read(1) == '\x1b':
                        break
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            time.sleep(0.1)
            # Auto-return after 30 seconds of inactivity
            if time.time() - start_time > 30:
                break
    except:
        pass

def show_status(manager):
    clear_screen()
    status = "🟢 RUNNING" if manager.process and manager.process.poll() is None else "🔴 STOPPED"
    print(f"\nCurrent Status: {status}")
    print("\nPress Enter to return...")
    get_key()

def main():
    manager = HunterManager()
    while True:
        action = main_menu(manager)
        
        if action == 'view':
            view_logs(manager)
        elif action == 'status':
            show_status(manager)
            clear_screen()

if __name__ == "__main__":
    main()
