"""
Optimized Menu System for ILove SOL Bot
- Performance monitoring dashboard
- Memory usage tracking
- Support for both original and optimized bot versions
- Async log processing
"""

import os
import sys
import subprocess
import time
import platform
import asyncio
import psutil
from threading import Thread
from queue import Queue, Empty
from dataclasses import dataclass
from typing import Optional, Dict

# Platform-specific key input handling
if platform.system() == 'Windows':
    import msvcrt
else:
    import tty
    import termios

@dataclass
class BotStats:
    """Bot performance statistics"""
    uptime: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    pools_processed: int = 0
    avg_processing_time: float = 0.0
    api_errors: int = 0
    websocket_reconnects: int = 0

class OptimizedHunterManager:
    def __init__(self):
        self.process = None
        self.log_file = "ILove_optimized.log"
        self.fallback_log_file = "ILove.log"
        self.log_queue = Queue()
        self.running = False
        self.start_time = None
        self.stats = BotStats()

    def start_hunt(self, use_optimized: bool = True):
        """Start the hunting bot (optimized or original version)"""
        if self.process and self.process.poll() is None:
            return False
            
        script_name = 'ILove_optimized.py' if use_optimized else 'ILove.py'
        log_file = self.log_file if use_optimized else self.fallback_log_file
        
        # Check if optimized version exists
        if use_optimized and not os.path.exists(script_name):
            print("⚠️ Optimized version not found, falling back to original...")
            script_name = 'ILove.py'
            log_file = self.fallback_log_file
            use_optimized = False
        
        self.running = True
        self.start_time = time.time()
        
        # Clear log file
        with open(log_file, 'w') as f:
            f.write("")
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1  # Line buffered for better real-time output
            )
            
            Thread(target=self.log_reader, daemon=True).start()
            Thread(target=self.stats_updater, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            self.running = False
            return False

    def log_reader(self):
        """Read logs from bot process"""
        current_log = self.log_file if os.path.exists(self.log_file) else self.fallback_log_file
        
        while self.running and self.process:
            if self.process.poll() is not None:
                break
                
            try:
                line = self.process.stdout.readline()
                if line:
                    self.log_queue.put(line)
                    # Also write to file
                    with open(current_log, 'a') as f:
                        f.write(line)
                    
                    # Parse performance metrics from logs
                    self.parse_log_line(line)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Log reader error: {e}")
                break

    def parse_log_line(self, line: str):
        """Parse performance metrics from log lines"""
        try:
            if "Performance Stats" in line:
                # Extract metrics from performance log line
                parts = line.split(" - ")[1].split(", ")
                for part in parts:
                    if "Pools:" in part:
                        self.stats.pools_processed = int(part.split(":")[1].strip())
                    elif "Avg Time:" in part:
                        self.stats.avg_processing_time = float(part.split(":")[1].replace("s", "").strip())
                    elif "API Errors:" in part:
                        self.stats.api_errors = int(part.split(":")[1].strip())
                    elif "Reconnects:" in part:
                        self.stats.websocket_reconnects = int(part.split(":")[1].strip())
        except Exception:
            pass  # Ignore parsing errors

    def stats_updater(self):
        """Update system stats periodically"""
        while self.running and self.process:
            try:
                if self.process.poll() is None:
                    # Get process stats
                    process = psutil.Process(self.process.pid)
                    self.stats.memory_mb = process.memory_info().rss / 1024 / 1024
                    self.stats.cpu_percent = process.cpu_percent()
                    self.stats.uptime = time.time() - self.start_time if self.start_time else 0
                
                time.sleep(5)  # Update every 5 seconds
            except Exception:
                break

    def stop_hunt(self):
        """Stop the hunting bot"""
        if self.process and self.process.poll() is None:
            self.running = False
            self.process.terminate()
            
            # Give it a moment to terminate gracefully
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            return True
        return False

    def get_logs(self, max_lines: int = 50) -> str:
        """Get recent log lines"""
        lines = []
        count = 0
        
        while count < max_lines:
            try:
                line = self.log_queue.get_nowait()
                lines.append(line)
                count += 1
            except Empty:
                break
        
        return ''.join(lines)

    def is_running(self) -> bool:
        """Check if bot is currently running"""
        return self.process is not None and self.process.poll() is None

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    """Get keyboard input cross-platform"""
    if platform.system() == 'Windows':
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            return {'H': 'up', 'P': 'down'}.get(key.decode(), 'unknown')
        elif key == b'\r':
            return 'enter'
        elif key == b'\x1b':
            return 'escape'
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
            elif ch == '\x1b':
                return 'escape'
            return 'unknown'
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def format_time(seconds: float) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def draw_performance_dashboard(manager: OptimizedHunterManager):
    """Draw performance monitoring dashboard"""
    clear_screen()
    
    # Header
    print("=" * 80)
    print("🚀 ILove SOL Bot - Performance Dashboard".center(80))
    print("=" * 80)
    
    # Status
    status = "🟢 RUNNING" if manager.is_running() else "🔴 STOPPED"
    print(f"\nStatus: {status}")
    
    if manager.is_running():
        stats = manager.stats
        print(f"Uptime: {format_time(stats.uptime)}")
        print(f"Memory Usage: {stats.memory_mb:.1f} MB")
        print(f"CPU Usage: {stats.cpu_percent:.1f}%")
        print(f"\nPool Processing:")
        print(f"  • Pools Processed: {stats.pools_processed}")
        print(f"  • Avg Processing Time: {stats.avg_processing_time:.2f}s")
        print(f"  • API Errors: {stats.api_errors}")
        print(f"  • WebSocket Reconnects: {stats.websocket_reconnects}")
        
        # Performance indicators
        print(f"\nPerformance Indicators:")
        memory_status = "🟢 Good" if stats.memory_mb < 200 else "🟡 High" if stats.memory_mb < 500 else "🔴 Critical"
        print(f"  • Memory: {memory_status}")
        
        speed_status = "🟢 Fast" if stats.avg_processing_time < 2 else "🟡 Moderate" if stats.avg_processing_time < 5 else "🔴 Slow"
        print(f"  • Speed: {speed_status}")
        
        error_status = "🟢 Good" if stats.api_errors < 10 else "🟡 Some Issues" if stats.api_errors < 50 else "🔴 Many Errors"
        print(f"  • Reliability: {error_status}")
    
    print("\n" + "=" * 80)
    print("Press 'ESC' to return to main menu | 'R' to refresh")

def draw_menu(options, selected_index):
    """Draw main menu"""
    clear_screen()
    
    # ASCII Art
    art = """
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
    width = max(len(line) for line in lines) if lines else 0
    
    term_width = os.get_terminal_size().columns
    term_height = os.get_terminal_size().lines
    
    x_padding = max((term_width - width) // 2, 0)
    y_padding = max((term_height - len(lines) - len(options) - 10) // 2, 0)
    
    print('\n' * y_padding)
    for line in lines:
        print(' ' * x_padding + line)
    
    print("\n" + ' ' * ((term_width - 35) // 2) + "High-Performance SOL Trading Bot v2.0")
    print(' ' * ((term_width - 25) // 2) + "🚀 Now with Async Processing")
    print()
    
    # Menu options
    menu_width = max(len(option) for option in options) + 4
    menu_x_padding = max((term_width - menu_width) // 2, 0)
    
    for i, option in enumerate(options):
        prefix = " > " if i == selected_index else "   "
        print(' ' * menu_x_padding + f"{prefix}{option}")
    
    print(' ' * menu_x_padding + " " + '-' * (menu_width - 4))
    print("\n" + ' ' * menu_x_padding + "Enter to Select | ↑/↓ to Navigate | ESC to Exit")

def main_menu(manager: OptimizedHunterManager):
    """Main menu loop"""
    menu_options = [
        "Start Optimized Hunt    🚀⚡",
        "Start Standard Hunt     🚀",
        "Performance Dashboard   📊",
        "View Live Logs         📜",
        "Check Status           ✅",
        "Stop Bot               🛑",
        "Exit                   🚪"
    ]
    
    current_selection = 0
    
    while True:
        draw_menu(menu_options, current_selection)
        key = get_key()
        
        if key == 'up':
            current_selection = max(0, current_selection - 1)
        elif key == 'down':
            current_selection = min(len(menu_options) - 1, current_selection + 1)
        elif key == 'escape':
            manager.stop_hunt()
            clear_screen()
            print("\n👋 Exiting...")
            sys.exit()
        elif key == 'enter':
            if current_selection == 0:  # Start Optimized Hunt
                if manager.is_running():
                    return 'dashboard'
                elif manager.start_hunt(use_optimized=True):
                    time.sleep(1)  # Give bot time to start
                    return 'dashboard'
                else:
                    input("\n❌ Failed to start optimized bot. Press Enter to continue...")
            elif current_selection == 1:  # Start Standard Hunt
                if manager.is_running():
                    return 'dashboard'
                elif manager.start_hunt(use_optimized=False):
                    time.sleep(1)
                    return 'dashboard'
                else:
                    input("\n❌ Failed to start standard bot. Press Enter to continue...")
            elif current_selection == 2:  # Performance Dashboard
                return 'dashboard'
            elif current_selection == 3:  # View Logs
                return 'logs'
            elif current_selection == 4:  # Check Status
                return 'status'
            elif current_selection == 5:  # Stop Bot
                if manager.stop_hunt():
                    input("\n✅ Bot stopped successfully. Press Enter to continue...")
                else:
                    input("\n⚠️ No bot running. Press Enter to continue...")
            elif current_selection == 6:  # Exit
                manager.stop_hunt()
                clear_screen()
                print("\n👋 Exiting...")
                sys.exit()

def view_dashboard(manager: OptimizedHunterManager):
    """Performance dashboard view"""
    while True:
        draw_performance_dashboard(manager)
        
        # Non-blocking key check
        key = None
        start_time = time.time()
        
        while time.time() - start_time < 2.0:  # Refresh every 2 seconds
            try:
                if platform.system() == 'Windows':
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x1b':
                            return
                        elif key.lower() == b'r':
                            break
                else:
                    # Unix-like systems - simplified non-blocking check
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if key == '\x1b':
                            return
                        elif key.lower() == 'r':
                            break
                
                time.sleep(0.1)
            except:
                time.sleep(0.1)
        
        if not manager.is_running():
            input("\n⚠️ Bot has stopped. Press Enter to return to menu...")
            return

def view_logs(manager: OptimizedHunterManager):
    """Live logs view"""
    clear_screen()
    print("=== Live Logs (Press ESC to return) ===\n")
    
    try:
        start_time = time.time()
        while True:
            logs = manager.get_logs(10)  # Get last 10 lines
            if logs:
                print(logs, end='')
            
            # Check for ESC key
            if platform.system() == 'Windows':
                if msvcrt.kbhit() and msvcrt.getch() == b'\x1b':
                    break
            else:
                import select
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    if sys.stdin.read(1) == '\x1b':
                        break
            
            time.sleep(0.5)
            
            # Auto-return after 30 seconds of inactivity
            if time.time() - start_time > 30:
                break
    except Exception:
        pass

def show_status(manager: OptimizedHunterManager):
    """Show bot status"""
    clear_screen()
    
    status = "🟢 RUNNING" if manager.is_running() else "🔴 STOPPED"
    print(f"\n📊 Bot Status: {status}")
    
    if manager.is_running():
        stats = manager.stats
        print(f"\n⏱️  Uptime: {format_time(stats.uptime)}")
        print(f"💾 Memory: {stats.memory_mb:.1f} MB")
        print(f"🖥️  CPU: {stats.cpu_percent:.1f}%")
        print(f"🎯 Pools Processed: {stats.pools_processed}")
        
        if stats.avg_processing_time > 0:
            print(f"⚡ Avg Processing: {stats.avg_processing_time:.2f}s")
        if stats.api_errors > 0:
            print(f"⚠️  API Errors: {stats.api_errors}")
        if stats.websocket_reconnects > 0:
            print(f"🔄 Reconnects: {stats.websocket_reconnects}")
    
    print("\nPress Enter to return...")
    get_key()

def main():
    """Main application entry point"""
    manager = OptimizedHunterManager()
    
    try:
        while True:
            action = main_menu(manager)
            
            if action == 'dashboard':
                view_dashboard(manager)
            elif action == 'logs':
                view_logs(manager)
            elif action == 'status':
                show_status(manager)
    except KeyboardInterrupt:
        manager.stop_hunt()
        clear_screen()
        print("\n👋 Goodbye!")
    except Exception as e:
        manager.stop_hunt()
        print(f"\n❌ Error: {e}")
        print("Bot stopped for safety.")

if __name__ == "__main__":
    main()