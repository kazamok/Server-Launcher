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
    "All Servers": "모듈",
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
    "모두 정지 후 종료": "모두 정지 후 종료",
    "강제 종료": "강제 종료",
    "런처 종료": "런처 종료",
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
        # "MySQL_Process_Example": { # Uncomment and modify to use MySQL as a process
        #     "type": "process",
        #     "process_name": "mysqld.exe",
        #     "start_cmd": ["C:\\xampp\\mysql\\bin\\mysqld.exe", "--console"], # Example path, adjust as needed
        #     "stop_cmd": ["taskkill", "/F", "/IM", "mysqld.exe"], # Example stop command
        #     "cwd": "C:\\xampp\\mysql\\bin", # Example working directory
        #     "show_console": True,
        # },
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
        # No need to convert start_cmd/stop_cmd back to string, they are always lists now.

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
        self.geometry("1000x580")
        self.minsize(1000, 580)
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
        log_frame.pack(fill="x", expand=False, padx=10, pady=10)
        log_label = ctk.CTkLabel(log_frame, text=_("Logs"), font=ctk.CTkFont(family="맑은 고딕", size=14))
        log_label.pack(anchor="w", padx=10, pady=(5,0))
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", height=100, font=ctk.CTkFont(family="맑은 고딕", size=12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Quit Button ---
        quit_button = ctk.CTkButton(main_frame, text=_("Quit"), command=self.on_quit_button_click, fg_color="#FF5722", hover_color="#E64A19", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"), corner_radius=0)
        quit_button.pack(side="right", pady=10, padx=5)

        # --- Config Button ---
        config_button = ctk.CTkButton(main_frame, text=_("Config"), command=self.open_config_window, font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"), corner_radius=0)
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
        start_button = ctk.CTkButton(parent, text=_("Start"), command=lambda n=name: self.start_server(n), fg_color="#43A047", hover_color="#2E7D32", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        start_button.grid(row=row, column=3, padx=5, pady=5)

        # Stop Button
        stop_button = ctk.CTkButton(parent, text=_("Stop"), command=lambda n=name: self.stop_server(n), fg_color="#D32F2F", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
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

        self.start_all_button = ctk.CTkButton(parent, text=_("Start All"), command=lambda: self.start_all_servers(), fg_color="#4CAF50", hover_color="#388E3C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        self.start_all_button.grid(row=row, column=3, padx=5, pady=5)

        self.stop_all_button = ctk.CTkButton(parent, text=_("Stop All"), command=lambda: self.stop_all_servers(), fg_color="#F44336", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
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
        # Check if any server is running
        running_servers = []
        for name in SERVER_CONFIG.keys():
            if name == "auto_restart_enabled": continue # Skip the config entry
            status = self.check_server_status(name)
            if status == _("Running"):
                running_servers.append(name)

        if running_servers:
            # Some servers are running, ask user what to do
            message = f"다음 서버들이 실행 중입니다: {', '.join(running_servers)}\n모두 정지하고 종료하시겠습니까? 또는 강제 종료하시겠습니까?"
            msg = CTkMessagebox(title=_("Server Running"), message=message,
                                icon="question", option_1=_("취소"), option_2=_("모두 정지 후 종료"), option_3=_("강제 종료"))
            response = msg.get()

            if response == _("모두 정지 후 종료"):
                self.log("User chose to stop all servers and exit.")
                # _perform_shutdown_and_exit already calls stop_all_servers and then destroys
                shutdown_thread = threading.Thread(target=self._perform_shutdown_and_exit, daemon=True)
                shutdown_thread.start()
            elif response == _("강제 종료"):
                self.log("User chose to force exit. Terminating launcher immediately.")
                self.after(0, self.destroy) # Force exit
            elif response == _("취소"):
                self.log("Quit cancelled by user.")
        else:
            # All servers are stopped, ask for simple confirmation to exit
            msg = CTkMessagebox(title=_("런처 종료"), message=_("런처를 종료하시겠습니까?"),
                                icon="question", option_1=_("취소"), option_2=_("확인"))
            response = msg.get()
            if response == _("확인"):
                self.log("All servers are stopped. Exiting launcher.")
                self.after(0, self.destroy)
            else:
                self.log("Quit cancelled by user.")

    def _perform_shutdown_and_exit(self):
        self.stop_all_servers()
        self.log("All servers stop commands issued. Exiting application...")
        self.after(0, self.destroy)

class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Server Configuration")
        self.geometry("950x600")
        self.grab_set()

        self.path_entries = {}

        self.server_config_widgets = {} # New dictionary to store widgets for each server

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.scrollable_config_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.scrollable_config_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(self.scrollable_config_frame, text="Server Name", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(self.scrollable_config_frame, text="Type", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(self.scrollable_config_frame, text="Executable/Service Path", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        row_num = 1
        for name, config in SERVER_CONFIG.items():
            if name == "auto_restart_enabled": # Skip this for now, handled separately
                continue
            ctk.CTkLabel(self.scrollable_config_frame, text=name, font=ctk.CTkFont(family="맑은 고딕", size=12)).grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
            
            # Type selection dropdown
            type_optionmenu = ctk.CTkOptionMenu(self.scrollable_config_frame, values=["process", "service"],
                                                command=lambda value, n=name, r=row_num: self._on_type_change(value, n, r),
                                                font=ctk.CTkFont(family="맑은 고딕", size=12), corner_radius=0)
            type_optionmenu.set(config["type"]) # Set initial value
            type_optionmenu.grid(row=row_num, column=1, padx=5, pady=2, sticky="w")

            # Store widgets for dynamic access
            self.server_config_widgets[name] = {
                "type_optionmenu": type_optionmenu,
                "widgets": {} # To store dynamically created widgets
            }
            
            # Initial creation of dynamic fields based on current type
            self._create_dynamic_config_fields(self.scrollable_config_frame, name, config, row_num)
            
            row_num += 1

        

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        save_button = ctk.CTkButton(button_frame, text=_("Save All Configs"), command=self._save_all_configs, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        save_button.pack(side="right", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text=_("Cancel"), command=self.destroy, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        cancel_button.pack(side="right", padx=5)

        # --- Auto Restart Option (Moved to bottom) ---
        auto_restart_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        auto_restart_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        ctk.CTkLabel(auto_restart_frame, text="Auto Restart Enabled", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).pack(side="left", padx=5, pady=5)
        self.auto_restart_switch = ctk.CTkSwitch(auto_restart_frame, text="", onvalue=True, offvalue=False)
        self.auto_restart_switch.pack(side="left", padx=5, pady=5)
        if SERVER_CONFIG.get("auto_restart_enabled", False):
            self.auto_restart_switch.select()
        else:
            self.auto_restart_switch.deselect()

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

    def _create_dynamic_config_fields(self, parent_frame, server_name, config_data, row_num):
        # Destroy all widgets in columns 2 and 3 for the current server's potential rows
        # This is a more aggressive clear to ensure no old widgets remain
        for r in range(row_num, row_num + 5): # Covers the max possible rows for a process config
            for c in range(2, 4): # Covers columns 2 and 3
                for widget in parent_frame.grid_slaves(row=r, column=c):
                    widget.destroy()


        self.server_config_widgets[server_name]["widgets"] = {} # Reset widgets for this server

        if config_data["type"] == "process":
            # Process Name
            process_name_label = ctk.CTkLabel(parent_frame, text="Process Name:", font=ctk.CTkFont(family="맑은 고딕", size=12))
            process_name_label.grid(row=row_num, column=2, padx=(5,0), pady=2, sticky="w")
            process_name_entry = ctk.CTkEntry(parent_frame, width=150, font=ctk.CTkFont(family="맑은 고딕", size=12))
            process_name_entry.grid(row=row_num, column=2, padx=(100,5), pady=2, sticky="w")
            process_name_entry.insert(0, config_data.get("process_name", ""))
            self.server_config_widgets[server_name]["widgets"]["process_name_entry"] = process_name_entry

            # Start Command
            start_cmd_label = ctk.CTkLabel(parent_frame, text="Start Cmd:", font=ctk.CTkFont(family="맑은 고딕", size=12))
            start_cmd_label.grid(row=row_num + 1, column=2, padx=(5,0), pady=2, sticky="w")
            start_cmd_entry = ctk.CTkEntry(parent_frame, width=350, font=ctk.CTkFont(family="맑은 고딕", size=12))
            start_cmd_entry.grid(row=row_num + 1, column=2, padx=(70,5), pady=2, sticky="ew")
            start_cmd_entry.insert(0, config_data["start_cmd"][0] if config_data.get("start_cmd") and isinstance(config_data["start_cmd"], list) else "")
            self.server_config_widgets[server_name]["widgets"]["start_cmd_entry"] = start_cmd_entry

            browse_button = ctk.CTkButton(parent_frame, text="Browse", width=70, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                          command=lambda entry=start_cmd_entry: self._browse_path(entry), corner_radius=0)
            browse_button.grid(row=row_num + 1, column=3, padx=5, pady=2)
            self.server_config_widgets[server_name]["widgets"]["browse_button"] = browse_button

            # Stop Command
            stop_cmd_label = ctk.CTkLabel(parent_frame, text="Stop Cmd:", font=ctk.CTkFont(family="맑은 고딕", size=12))
            stop_cmd_label.grid(row=row_num + 2, column=2, padx=(5,0), pady=2, sticky="w")
            stop_cmd_entry = ctk.CTkEntry(parent_frame, width=350, font=ctk.CTkFont(family="맑은 고딕", size=12))
            stop_cmd_entry.grid(row=row_num + 2, column=2, padx=(70,5), pady=2, sticky="ew")
            stop_cmd_entry.insert(0, config_data["stop_cmd"][0] if config_data.get("stop_cmd") and isinstance(config_data["stop_cmd"], list) else "")
            self.server_config_widgets[server_name]["widgets"]["stop_cmd_entry"] = stop_cmd_entry

            # CWD
            cwd_label = ctk.CTkLabel(parent_frame, text="CWD:", font=ctk.CTkFont(family="맑은 고딕", size=12))
            cwd_label.grid(row=row_num + 3, column=2, padx=(5,0), pady=2, sticky="w")
            cwd_entry = ctk.CTkEntry(parent_frame, width=350, font=ctk.CTkFont(family="맑은 고딕", size=12))
            cwd_entry.grid(row=row_num + 3, column=2, padx=(70,5), pady=2, sticky="ew")
            cwd_entry.insert(0, config_data.get("cwd", ""))
            self.server_config_widgets[server_name]["widgets"]["cwd_entry"] = cwd_entry

            # Show Console
            show_console_checkbox = ctk.CTkCheckBox(parent_frame, text="Show Console", font=ctk.CTkFont(family="맑은 고딕", size=12))
            show_console_checkbox.grid(row=row_num + 4, column=2, padx=5, pady=2, sticky="w")
            if config_data.get("show_console", False):
                show_console_checkbox.select()
            else:
                show_console_checkbox.deselect()
            self.server_config_widgets[server_name]["widgets"]["show_console_checkbox"] = show_console_checkbox

        elif config_data["type"] == "service":
            service_name_label = ctk.CTkLabel(parent_frame, text="Service Name:", font=ctk.CTkFont(family="맑은 고딕", size=12))
            service_name_label.grid(row=row_num, column=2, padx=(5,0), pady=2, sticky="w")
            service_name_entry = ctk.CTkEntry(parent_frame, width=200, font=ctk.CTkFont(family="맑은 고딕", size=12))
            service_name_entry.grid(row=row_num, column=2, padx=(100,5), pady=2, sticky="w")
            service_name_entry.insert(0, config_data.get("service_name", ""))
            self.server_config_widgets[server_name]["widgets"]["service_name_entry"] = service_name_entry

    def _on_type_change(self, new_type, server_name, row_num):
        # Get the current config for the server
        current_config = SERVER_CONFIG[server_name].copy()
        current_config["type"] = new_type # Update type for dynamic field creation

        # Re-create dynamic fields
        self._create_dynamic_config_fields(self.scrollable_config_frame, server_name, current_config, row_num)

    def _save_all_configs(self):
        global SERVER_CONFIG
        updated_configs = SERVER_CONFIG.copy()
        errors = []

        for name, server_widgets in self.server_config_widgets.items():
            selected_type = server_widgets["type_optionmenu"].get()
            updated_configs[name]["type"] = selected_type
            
            if selected_type == "process":
                widgets = server_widgets["widgets"]
                process_name = widgets["process_name_entry"].get()
                start_cmd = widgets["start_cmd_entry"].get()
                stop_cmd = widgets["stop_cmd_entry"].get()
                cwd = widgets["cwd_entry"].get()
                show_console = widgets["show_console_checkbox"].get()

                if not process_name:
                    errors.append(f"Process Name for {name} cannot be empty.")
                if not start_cmd:
                    errors.append(f"Start Command for {name} cannot be empty.")
                elif not os.path.exists(start_cmd):
                    errors.append(f"Start Command path for {name} does not exist:\n{start_cmd}")

                updated_configs[name]["process_name"] = process_name
                updated_configs[name]["start_cmd"] = [start_cmd]
                updated_configs[name]["stop_cmd"] = [stop_cmd] if stop_cmd else [] # Allow empty stop_cmd
                updated_configs[name]["cwd"] = cwd
                updated_configs[name]["show_console"] = show_console

                # Remove service-specific keys if changing from service to process
                updated_configs[name].pop("service_name", None)

            elif selected_type == "service":
                widgets = server_widgets["widgets"]
                service_name = widgets["service_name_entry"].get()

                if not service_name:
                    errors.append(f"Service Name for {name} cannot be empty.")
                
                updated_configs[name]["service_name"] = service_name

                # Remove process-specific keys if changing from process to service
                updated_configs[name].pop("process_name", None)
                updated_configs[name].pop("start_cmd", None)
                updated_configs[name].pop("stop_cmd", None)
                updated_configs[name].pop("cwd", None)
                updated_configs[name].pop("show_console", None)
        
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
