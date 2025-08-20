import customtkinter as ctk
import subprocess
import threading
import time
import os
import sys
import ctypes
import psutil
import logging
import json
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog

# --- Translation Map ---
TRANSLATIONS = {
    "WISE Server Launcher": "WISE 서버 런처",
    "Quit": "종료",
    "Config": "설정",
    "Status": "상태",
    "Progressing...": "처리 중...",
    "Launcher started. Monitoring servers...": "런처 시작. 서버 모니터링 중...",
    "All Servers": "모든 서버",
    "Stop All": "모두 정지",
    "Start All": "모두 시작",
    "Unknown": "알 수 없음",
    "Start": "시작",
    "Stop": "정지",
    "Path": "경로",
    "Service": "서비스", # For "Service: MySQL84"
    "Running": "실행 중",
    "Stopped": "정지됨",
    "Error": "오류",
    "AUTO-RESTART": "자동 재시작",
    "Quit confirmed. Initiating server shutdown...": "종료 확인됨. 서버 종료 시작 중...",
    "Quit cancelled.": "종료 취소됨.",
    "Server Running": "서버 실행 중",
    "All servers stop commands issued. Exiting application in 2 seconds...": "모든 서버 정지 명령이 실행되었습니다. 2초 후 애플리케이션 종료...",
    "Server Configuration": "서버 설정",
    "Server Name": "서버 이름",
    "Type": "유형",
    "Executable/Service Path": "실행 파일/서비스 경로",
    "Browse": "찾아보기",
    "N/A (Service)": "해당 없음 (서비스)",
    "Auto Restart Enabled": "자동 재시작 활성화",
    "Save All Configs": "모든 설정 저장",
    "Cancel": "취소",
    "Selected new path": "새 경로 선택됨",
    "Configuration Error": "설정 오류",
    "Configuration save failed due to errors": "설정 저장 실패 (오류", # Partial match for f-string
    "All server configurations saved successfully.": "모든 서버 설정이 성공적으로 저장되었습니다.",
    "Configuration Saved": "설정 저장됨",
    "process": "프로세스",
    "service": "서비스",
    "Quit Application": "애플리케이션 종료",
    "확인": "확인",
    "취소": "취소",
}

def _(text):
    return TRANSLATIONS.get(text, text)

# --- Logging Setup ---
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_launcher.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # logging.StreamHandler() # Uncomment to also print logs to console
    ]
)

# --- Configuration ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_config.json')

def load_config():
    default_config = {
        "MySQL": {
            "type": "service",
            "service_name": "MySQL84",
        },
        "Apache": {
            "type": "process",
            "process_name": "httpd.exe",
            "start_cmd": [r"C:\\WISE\\xampp\\apache_start.bat"],
            "stop_cmd": [r"C:\\WISE\\xampp\\apache_stop.bat"],
            "cwd": r"C:\\WISE\\xampp",
            "show_console": False,
        },
        "Backend": {
            "type": "process",
            "process_name": "node.exe", # Assuming node.exe runs the backend
            "start_cmd": [r"C:\\WISE\\Account-manager\\start_backend.bat"],
            "cwd": r"C:\\WISE\\Account-manager",
            "show_console": False,
        },
        "Frontend": {
            "type": "process",
            "process_name": "node.exe", # Assuming node.exe runs the frontend
            "start_cmd": [r"C:\\WISE\\Account-manager\\start_frontend.bat"],
            "cwd": r"C:\\WISE\\Account-manager",
            "show_console": False,
        },
        "Auth Server": {
            "type": "process",
            "process_name": "authserver.exe",
            "start_cmd": [r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo\\authserver.exe"],
            "cwd": r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo",
            "show_console": True,
        },
        "World Server": {
            "type": "process",
            "process_name": "worldserver.exe",
            "start_cmd": [r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo\\worldserver.exe"],
            "cwd": r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo",
            "show_console": True,
        },
        "auto_restart_enabled": False, # New config for auto restart
    }

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            # Ensure start_cmd/stop_cmd are lists for consistency
            for server_name, server_data in loaded_config.items():
                if server_data.get("type") == "process":
                    if "start_cmd" in server_data and isinstance(server_data["start_cmd"], str):
                        server_data["start_cmd"] = [server_data["start_cmd"]]
                    if "stop_cmd" in server_data and isinstance(server_data["stop_cmd"], str):
                        server_data["stop_cmd"] = [server_data["stop_cmd"]]
            # Add auto_restart_enabled if not present in loaded config
            if "auto_restart_enabled" not in loaded_config:
                loaded_config["auto_restart_enabled"] = default_config["auto_restart_enabled"]
            logging.info(f"Configuration loaded from {CONFIG_FILE}")
            return loaded_config
    except FileNotFoundError:
        logging.warning(f"Config file not found at {CONFIG_FILE}. Creating default config.")
        save_config(default_config)
        return default_config
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding config file: {e}. Using default config.")
        save_config(default_config)
        return default_config
    except Exception as e:
        logging.error(f"An unexpected error occurred loading config: {e}. Using default config.")
        save_config(default_config)
        return default_config

def save_config(config_data):
    saveable_config = {}
    for server_name, server_data in config_data.items():
        if server_name == "auto_restart_enabled": # Handle the new config key
            saveable_config[server_name] = server_data
            continue
        saveable_config[server_name] = server_data.copy()
        if saveable_config[server_name].get("type") == "process":
            # Convert start_cmd/stop_cmd back to string for saving if they are lists
            if "start_cmd" in saveable_config[server_name] and isinstance(saveable_config[server_name]["start_cmd"], list):
                saveable_config[server_name]["start_cmd"] = saveable_config[server_name]["start_cmd"][0]
            if "stop_cmd" in saveable_config[server_name] and isinstance(saveable_config[server_name]["stop_cmd"], list):
                saveable_config[server_name]["stop_cmd"] = saveable_config[server_name]["stop_cmd"][0]

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saveable_config, f, indent=4)
        logging.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logging.error(f"Error saving config file: {e}")

SERVER_CONFIG = load_config()

class ServerLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(_("WISE Server Launcher"))
        self.geometry("1000x850")
        self.minsize(1000, 850)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.server_widgets = {}
        self.server_processes = {} # To store Popen objects by server name
        self.last_all_action_time = 0 # Cooldown for Start All/Stop All buttons

        # --- Main Frame ---
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- Grid Container for Server Rows ---
        self.server_list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.server_list_frame.pack(fill="x", padx=10, pady=5)

        # Configure the grid layout for all rows
        self.server_list_frame.grid_columnconfigure(0, weight=2) # Name
        self.server_list_frame.grid_columnconfigure(1, weight=3) # Path
        self.server_list_frame.grid_columnconfigure(2, weight=1) # Status
        self.server_list_frame.grid_columnconfigure(3, weight=0) # Start Button
        self.server_list_frame.grid_columnconfigure(4, weight=0) # Stop Button

        # --- Create All Servers Row ---
        self.create_all_servers_row(self.server_list_frame, row=0)

        # --- Separator ---
        separator = ctk.CTkFrame(self.server_list_frame, height=2, fg_color="gray50")
        separator.grid(row=1, column=0, columnspan=5, sticky="ew", pady=5, padx=5)

        # --- Create Server Rows ---
        row_index = 2
        for name in SERVER_CONFIG.keys():
            if name == "auto_restart_enabled":
                continue
            self.create_server_row(self.server_list_frame, name, row=row_index)
            row_index += 1

        # --- Log Box ---
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        log_label = ctk.CTkLabel(log_frame, text=_("Logs"), font=ctk.CTkFont(family="맑은 고딕", size=14))
        log_label.pack(anchor="w", padx=10, pady=(5,0))
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", height=25, font=ctk.CTkFont(family="맑은 고딕", size=12)) # Set initial height to very small
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Quit Button ---
        quit_button = ctk.CTkButton(main_frame, text=_("Quit"), command=self.on_quit_button_click, fg_color="#FF5722", hover_color="#E64A19", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        quit_button.pack(side="right", pady=10, padx=5)

        # --- Config Button ---
        config_button = ctk.CTkButton(main_frame, text=_("Config"), command=self.open_config_window, font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        config_button.pack(side="right", pady=10, padx=5)

        # --- Start Monitoring ---
        self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        self.monitor_thread.start()
        self.log(_("Launcher started. Monitoring servers..."))

        # --- Handle window closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_quit_button_click)

    def open_config_window(self):
        config_window = ConfigWindow(self)
        config_window.grab_set()

    def create_server_row(self, parent, name, row):
        config = SERVER_CONFIG[name]

        # Server Name and Type
        name_type_label = ctk.CTkLabel(parent, text=f"{name}", font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"))
        name_type_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        # Path Label
        path_text = ""
        if config["type"] == "process" and config.get("start_cmd"):
            path_text = config["start_cmd"][0]
        elif config["type"] == "service" and config.get("service_name"):
            path_text = f"{_("Service")}: {config['service_name']}"
        
        path_label = ctk.CTkLabel(parent, text=f"{path_text}", font=ctk.CTkFont(family="맑은 고딕", size=12), wraplength=400)
        path_label.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        # Status Label
        status_label = ctk.CTkLabel(parent, text=_("Unknown"), text_color="gray", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        status_label.grid(row=row, column=2, padx=10, pady=5, sticky="w")

        # Start Button
        start_button = ctk.CTkButton(parent, text=_("Start"), command=lambda n=name: self.start_server(n), fg_color="#43A047", hover_color="#2E7D32", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        start_button.grid(row=row, column=3, padx=5, pady=5)

        # Stop Button
        stop_button = ctk.CTkButton(parent, text=_("Stop"), command=lambda n=name: self.stop_server(n), fg_color="#D32F2F", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        stop_button.grid(row=row, column=4, padx=5, pady=5)

        self.server_widgets[name] = {
            "status": status_label,
            "start": start_button,
            "stop": stop_button,
            "path_label": path_label, # Store reference to update if config changes
        }

    def create_all_servers_row(self, parent, row):
        # This row now serves as the main header row
        name_header = ctk.CTkLabel(parent, text=_("All Servers"), font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"))
        name_header.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        path_header = ctk.CTkLabel(parent, text=_("Path"), font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        path_header.grid(row=row, column=1, padx=10, pady=2, sticky="w")

        status_header = ctk.CTkLabel(parent, text=_("Status"), font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        status_header.grid(row=row, column=2, padx=10, pady=2, sticky="w")

        self.start_all_button = ctk.CTkButton(parent, text=_("Start All"), command=lambda: self.start_all_servers(), fg_color="#4CAF50", hover_color="#388E3C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        self.start_all_button.grid(row=row, column=3, padx=5, pady=5)

        self.stop_all_button = ctk.CTkButton(parent, text=_("Stop All"), command=lambda: self.stop_all_servers(), fg_color="#F44336", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        self.stop_all_button.grid(row=row, column=4, padx=5, pady=5)

    def log(self, message, level="info"):
        if level.lower() == "info":
            logging.info(message)
        elif level.lower() == "error":
            logging.error(message)
        elif level.lower() == "warning":
            logging.warning(message)
        else:
            logging.debug(message)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.after(0, self._update_log_box, full_message)

    def _update_log_box(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def start_server(self, name):
        config = SERVER_CONFIG[name]
        self.log(f"Attempting to start {name}...")

        try:
            if config["type"] == "service":
                subprocess.run(["net", "start", config["service_name"]], check=True, capture_output=True, text=True)
                self.log(f"Service {name} started successfully.")
            elif config["type"] == "process":
                # Check if the process is already tracked and running
                if name in self.server_processes and self.server_processes[name].poll() is None:
                    pid = self.server_processes[name].pid # Get PID for message
                    message = f"{name} 서버는 이미 실행 중입니다. (PID: {pid})\n추가적인 조치는 취하지 않습니다."
                    CTkMessagebox(title=_("Server Running"), message=message, icon="info")
                    self.log(f"{name} process (PID: {pid}) already running. No action taken.")
                    return
                
                command_to_run = config["start_cmd"]
                # For .bat files, use shell=True. For .exe, it's better without.
                use_shell = command_to_run[0].lower().endswith((".bat", ".cmd"))
                # Hide console window for background processes unless specified otherwise
                show_console = config.get("show_console", False)
                creationflags = 0 if use_shell or show_console else subprocess.CREATE_NO_WINDOW
                
                proc = subprocess.Popen(
                    command_to_run, 
                    cwd=config.get("cwd"), 
                    shell=use_shell,
                    creationflags=creationflags
                )
                self.server_processes[name] = proc
                self.log(f"Started {name} with PID {proc.pid}.")
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            self.log(f"ERROR starting {name}: {e}", level="error")

    def stop_server(self, name):
        config = SERVER_CONFIG[name]
        self.log(f"Attempting to stop {name}...")

        try:
            if config["type"] == "service":
                subprocess.run(["net", "stop", config["service_name"]], check=True, capture_output=True, text=True)
                self.log(f"Service {name} stopped successfully.")
            elif config["type"] == "process":
                # First, try to terminate the tracked process and its children
                if name in self.server_processes and self.server_processes[name].poll() is None:
                    pid = self.server_processes[name].pid
                    self.log(f"Terminating {name} process tree with parent PID {pid}...")
                    try:
                        parent = psutil.Process(pid)
                        # Terminate children first
                        children = parent.children(recursive=True)
                        for child in children:
                            self.log(f"Terminating child process {child.name()} with PID {child.pid}")
                            child.terminate()
                        # Then terminate the parent
                        parent.terminate()
                        # Wait for processes to terminate
                        psutil.wait_procs(children + [parent], timeout=3)
                    except psutil.NoSuchProcess:
                        self.log(f"Process with PID {pid} not found, it might have already been stopped.", level="warning")
                    
                    self.server_processes.pop(name) # Remove from tracking
                    return

                # If there's a stop command, run it
                if config.get("stop_cmd"):
                    command_to_run = config["stop_cmd"]
                    subprocess.run(command_to_run, cwd=config.get("cwd"), check=True, shell=True)
                    self.log(f"Executed stop command for {name}.")
                else:
                    # Fallback: kill any process with that name (use with caution)
                    # This part needs to be careful not to kill essential processes
                    found_and_terminated = False
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            # Check if the process name matches the configured process_name
                            # And if its command line contains the start_cmd (for more specific matching)
                            if proc.info['name'].lower() == config['process_name'].lower():
                                cmdline = proc.cmdline()
                                # Check if any part of the start_cmd is in the process's command line
                                if any(os.path.basename(cmd_part).lower() in arg.lower() for cmd_part in config['start_cmd'] for arg in cmdline):
                                    self.log(f"Found running process {proc.info['name']} with PID {proc.info['pid']}. Terminating...", level="warning")
                                    psutil.Process(proc.info['pid']).terminate()
                                    found_and_terminated = True
                                    break # Terminate only one instance
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue # Process might have exited or access denied
                    if found_and_terminated:
                        self.log(f"Process {name} terminated via fallback method.")
                    else:
                        self.log(f"No running process found for {name} to terminate via fallback.", level="warning")
        except (subprocess.CalledProcessError, psutil.NoSuchProcess, Exception) as e:
            self.log(f"ERROR stopping {name}: {e}", level="error")

    def start_all_servers(self):
        if time.time() - self.last_all_action_time < 15:
            self.log("Start All button is on cooldown. Please wait.", level="warning")
            return
        self.last_all_action_time = time.time()
        self.start_all_button.configure(state="disabled")
        self.stop_all_button.configure(state="disabled")
        threading.Thread(target=self._start_all_worker, daemon=True).start()
        self.after(15 * 1000, self._enable_all_buttons)

    def _start_all_worker(self):
        self.log("Attempting to start all configured servers...")
        # Start services first
        for name in SERVER_CONFIG.keys():
            if name == "auto_restart_enabled": continue
            if SERVER_CONFIG[name]["type"] == "service":
                current_status = self.check_server_status(name)
                if current_status == _("Running"):
                    self.log(f"{name} is already running. Skipping start.", level="info")
                    continue
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.start_server(name)
                self._wait_for_status_change(name, _("Running"))
        # Then processes
        for name in SERVER_CONFIG.keys():
            if name == "auto_restart_enabled": continue
            if SERVER_CONFIG[name]["type"] == "process":
                current_status = self.check_server_status(name)
                if current_status == _("Running"):
                    self.log(f"{name} is already running. Skipping start.", level="info")
                    continue
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.start_server(name)
                self._wait_for_status_change(name, _("Running"))
        self.log("All server start commands issued.")

    def stop_all_servers(self):
        if time.time() - self.last_all_action_time < 15:
            self.log("Stop All button is on cooldown. Please wait.", level="warning")
            return
        self.last_all_action_time = time.time()
        self.start_all_button.configure(state="disabled")
        self.stop_all_button.configure(state="disabled")
        threading.Thread(target=self._stop_all_worker, daemon=True).start()
        self.after(15 * 1000, self._enable_all_buttons)

    def _stop_all_worker(self):
        self.log("Attempting to stop all configured servers...")
        # Stop processes first
        for name in reversed(list(SERVER_CONFIG.keys())):
            if name == "auto_restart_enabled": continue
            if SERVER_CONFIG[name]["type"] == "process":
                current_status = self.check_server_status(name)
                if current_status == _("Stopped"):
                    self.log(f"{name} is already stopped. Skipping stop.", level="info")
                    continue
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.stop_server(name)
                self._wait_for_status_change(name, _("Stopped"))
        # Then services
        for name in reversed(list(SERVER_CONFIG.keys())):
            if name == "auto_restart_enabled": continue
            if SERVER_CONFIG[name]["type"] == "service":
                current_status = self.check_server_status(name)
                if current_status == _("Stopped"):
                    self.log(f"{name} is already stopped. Skipping stop.", level="info")
                    continue
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.stop_server(name)
                self._wait_for_status_change(name, _("Stopped"))
        self.log("All server stop commands issued.")

    def _enable_all_buttons(self):
        self.start_all_button.configure(state="normal")
        self.stop_all_button.configure(state="normal")
        self.log("Start All/Stop All buttons re-enabled.")

    def _wait_for_status_change(self, name, target_status, timeout=2):
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.check_server_status(name)
            if current_status == target_status:
                self.log(f"{name} status changed to {target_status}.")
                return True
            time.sleep(0.1) # Poll every 100 milliseconds
        self.log(f"Timeout waiting for {name} to reach {target_status}.", level="warning")
        return False

    def check_server_status(self, name):
        config = SERVER_CONFIG[name]
        status = "Stopped"
        
        try:
            if config["type"] == "service":
                service = psutil.win_service_get(config["service_name"])
                if service.status() == 'running':
                    status = "Running"
            elif config["type"] == "process":
                # Primary check: is our tracked process alive?
                if name in self.server_processes and self.server_processes[name].poll() is None:
                     status = "Running"
                else:
                    # Fallback check: is any process with that name running?
                    # Use the configured process_name and start_cmd for more accurate matching
                    target_process_name = config['process_name'].lower()
                    target_start_cmd_parts = [os.path.basename(cmd_part).lower() for cmd_part in config['start_cmd']]

                    for proc in psutil.process_iter(['name', 'cmdline']):
                        try:
                            if proc.info['name'].lower() == target_process_name:
                                cmdline = proc.cmdline()
                                # Check if any part of the start_cmd is in the process's command line
                                if any(cmd_part in arg.lower() for cmd_part in target_start_cmd_parts for arg in cmdline):
                                    status = "Running"
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
        except psutil.NoSuchProcess:
            status = "Stopped"
        except Exception as e:
            status = "Error"
            self.log(f"Error checking status for {name}: {e}", level="error")
            
        return status

    def monitor_servers(self):
        while True:
            for name in SERVER_CONFIG.keys():
                if name == "auto_restart_enabled":
                    continue
                status = self.check_server_status(name)
                
                widget = self.server_widgets[name]["status"]
                if status == _("Running"):
                    widget.configure(text=_("Running"), text_color="#66BB6A")
                elif status == _("Stopped"):
                    widget.configure(text=_("Stopped"), text_color="#EF5350")
                else:
                    widget.configure(text=status, text_color="gray")

                if SERVER_CONFIG.get("auto_restart_enabled", False) and status == "Stopped":
                    self.log(f"AUTO-RESTART: {name} is stopped. Restarting...", level="warning")
                    self.start_server(name)
            
            time.sleep(5)

    def on_quit_button_click(self):
        msg = CTkMessagebox(title="Quit Application", message="모든 서버가 닫힙니다 확실합니까?",
                            icon="question", option_1="취소", option_2="확인")
        response = msg.get()
        
        if response == "확인":
            self.log("Quit confirmed. Initiating server shutdown...")
            shutdown_thread = threading.Thread(target=self._perform_shutdown_and_exit)
            shutdown_thread.daemon = True
            shutdown_thread.start()
        else:
            self.log("Quit cancelled.")

    def _perform_shutdown_and_exit(self):
        self.stop_all_servers()
        self.log("All servers stop commands issued. Exiting application in 2 seconds...")
        time.sleep(2)
        self.after(0, self.destroy)

class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Server Configuration")
        self.geometry("700x500")
        self.grab_set()

        self.path_entries = {}

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        scrollable_config_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scrollable_config_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(scrollable_config_frame, text="Server Name", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(scrollable_config_frame, text="Type", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(scrollable_config_frame, text="Executable/Service Path", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        row_num = 1
        for name, config in SERVER_CONFIG.items():
            if name == "auto_restart_enabled": # Skip this for now, handled separately
                continue
            ctk.CTkLabel(scrollable_config_frame, text=name, font=ctk.CTkFont(family="맑은 고딕", size=12)).grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
            ctk.CTkLabel(scrollable_config_frame, text=config["type"].capitalize(), font=ctk.CTkFont(family="맑은 고딕", size=12)).grid(row=row_num, column=1, padx=5, pady=2, sticky="w")

            if config["type"] == "process":
                path_entry = ctk.CTkEntry(scrollable_config_frame, width=350, font=ctk.CTkFont(family="맑은 고딕", size=12))
                path_entry.grid(row=row_num, column=2, padx=5, pady=2, sticky="ew")
                path_entry.insert(0, config["start_cmd"][0] if config["start_cmd"] else "")
                self.path_entries[name] = path_entry

                browse_button = ctk.CTkButton(scrollable_config_frame, text="Browse", width=70, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                              command=lambda entry=path_entry: self._browse_path(entry))
                browse_button.grid(row=row_num, column=3, padx=5, pady=2)
            elif config["type"] == "service":
                service_name_label = ctk.CTkLabel(scrollable_config_frame, text=config["service_name"], font=ctk.CTkFont(family="맑은 고딕", size=12))
                service_name_label.grid(row=row_num, column=2, padx=5, pady=2, sticky="w")
            
            row_num += 1

        # Auto Restart Option
        ctk.CTkLabel(scrollable_config_frame, text="Auto Restart Enabled", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=row_num, column=0, padx=5, pady=10, sticky="w", columnspan=2)
        self.auto_restart_switch = ctk.CTkSwitch(scrollable_config_frame, text="", onvalue=True, offvalue=False)
        self.auto_restart_switch.grid(row=row_num, column=2, padx=5, pady=10, sticky="w")
        if SERVER_CONFIG.get("auto_restart_enabled", False):
            self.auto_restart_switch.select()
        else:
            self.auto_restart_switch.deselect()
        row_num += 1

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        save_button = ctk.CTkButton(button_frame, text=_("Save All Configs"), command=self._save_all_configs, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        save_button.pack(side="right", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text=_("Cancel"), command=self.destroy, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        cancel_button.pack(side="right", padx=5)

    def _browse_path(self, entry_widget):
        initial_dir = os.path.dirname(entry_widget.get()) if os.path.exists(entry_widget.get()) else os.getcwd()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Executable",
            filetypes=(("Executable files", "*.exe *.bat *.cmd"), ("All files", "*.*"))
        )
        if file_path:
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, file_path)
            self.master.log(f"Selected new path: {file_path}")

    def _save_all_configs(self):
        global SERVER_CONFIG
        updated_configs = SERVER_CONFIG.copy()
        errors = []

        for name, entry_widget in self.path_entries.items():
            if updated_configs[name]["type"] == "process":
                new_path = entry_widget.get()
                if not os.path.exists(new_path):
                    errors.append(f"Path for {name} does not exist:\n{new_path}")
                else:
                    updated_configs[name]["start_cmd"] = [new_path]
        
        # Save auto restart setting
        updated_configs["auto_restart_enabled"] = self.auto_restart_switch.get()

        if errors:
            error_message = "The following paths are invalid:\n\n" + "\n\n".join(errors)
            CTkMessagebox(title="Configuration Error", message=error_message, icon="cancel")
            self.master.log(f"Configuration save failed due to errors: {errors}", level="error")
        else:
            SERVER_CONFIG = updated_configs
            save_config(SERVER_CONFIG)
            self.master.log("All server configurations saved successfully.")
            CTkMessagebox(title="Configuration Saved", message="All server configurations saved successfully.", icon="check")
            
            # Update main window's path labels (only for process types)
            for name, config in SERVER_CONFIG.items():
                if name == "auto_restart_enabled": # Skip this
                    continue
                if name in self.master.server_widgets and "path_label" in self.master.server_widgets[name]:
                    path_text = ""
                    if config["type"] == "process" and config.get("start_cmd"):
                        path_text = config["start_cmd"][0]
                    elif config["type"] == "service" and config.get("service_name"):
                        path_text = f"{_('Service')}: {config['service_name']}"
                    self.master.server_widgets[name]["path_label"].configure(text=path_text)

            self.after(10, self.destroy)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

if __name__ == "__main__":
    if is_admin():
        app = ServerLauncher()
        app.mainloop()
    else:
        run_as_admin()