import subprocess
import sys
import importlib.util

# --- 의존성 검사 및 설치 ---
def check_and_install_dependencies():
    """필요한 패키지가 있는지 확인하고 없으면 설치합니다."""
    required_packages = {
        "customtkinter": "customtkinter",
        "psutil": "psutil",
        "CTkMessagebox": "CTkMessagebox"
    }
    for package, import_name in required_packages.items():
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            print(f"'{package}'를 찾을 수 없습니다. 설치를 시작합니다...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError as e:
                print(f"{package} 설치에 실패했습니다. 수동으로 설치한 후 다시 시도해주세요. 오류: {e}")
                sys.exit(1)

# --- 스크립트 시작 시 의존성 검사 실행 ---
check_and_install_dependencies()

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
import copy # 딥코드에 대한 복사본 추가
import traceback # 자세한 예외를 로깅하려면
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog

# --- 번역 맵 ---
# UI에 표시되는 텍스트를 한국어로 번역하기 위한 딕셔너리입니다.
TRANSLATIONS = {
    "Server Launcher": "아제로스코어 런처",
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
    "Service": "서비스", # "Service: MySQL84"용
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
    "Configuration save failed due to errors": "설정 저장 실패 (오류", # f-string 부분 일치
    "All server configurations saved successfully.": "모든 서버 설정이 성공적으로 저장되었습니다.",
    "Configuration Saved": "설정 저장됨",
    "process": "프로세스",
    "service": "서비스",
    "Quit Application": "애플리케케이션 종료",
    "확인": "확인",
    "취소": "취소",
    # ConfigWindow에 대한 새로운 번역
    "Select a server to configure its settings.": "설정할 서버를 선택하세요.",
    "Settings for: {} ": "{} 설정:",
    "Process Name:": "프로세스 이름:",
    "Start Cmd:": "시작 명령어:",
    "Stop Cmd:": "정지 명령어:",
    "CWD:": "실행 폴더:",
    "Show Console": "콘솔 보이기",
    "Service Name:": "서비스 이름:",
    "Select Executable": "실행 파일 선택",
    "The following configuration errors occurred:\n\n": "다음 설정 오류가 발생했습니다:\n\n",
    "Process Name for {} cannot be empty.": "{}의 프로세스 이름은 비워둘 수 없습니다.",
    "Start Command for {} cannot be empty.": "{}의 시작 명령어는 비워둘 수 없습니다.",
    "Start Command path for {} does not exist:\n{}:": "{}의 시작 명령어 경로가 존재하지 않습니다:\n{}:",
    "Service Name for {} cannot be empty.": "{}의 서비스 이름은 비워둘 수 없습니다.",
    # MySQL 관련
    "Find Service": "서비스 찾기",
    "MySQL Service Detection": "MySQL 서비스 감지",
    "Could not find a running MySQL service.": "실행 중인 MySQL 서비스를 찾을 수 없습니다.",
    "Found service: {}. Use this?": "서비스를 찾았습니다: {}. 사용하시겠습니까?",
    "If you run MySQL from a folder (e.g., XAMPP), choose 'process'.": "만약 폴더(예: XAMPP)에서 MySQL을 실행한다면 '프로세서'를 선택하세요.",
    "If MySQL is installed and runs on boot, choose 'service'.": "MySQL이 설치되어 부팅 시 자동 실행된다면 '서비스'를 선택하세요.",
    "Edit Config File": "설정 파일 열기",
    "Config file not found:": "설정 파일을 찾을 수 없습니다:",
    "Quit Launcher?": "런처 종료?",
    "Are you sure you want to quit?\nRunning servers will not be affected.": "정말로 종료하시겠습니까?\n실행 중인 서버는 종료되지 않습니다.",
    # 에디터 설정
    "Editor": "에디터",
    "Select Editor Executable": "에디터 실행 파일 선택",
    "Editor not found:": "에디터를 찾을 수 없습니다:",
    "Editor path is not configured.": "에디터 경로가 설정되지 않았습니다.",
    "Yes": "예",
    "No": "아니오",
}

# --- 번역 함수 ---
def _(text):
    return TRANSLATIONS.get(text, text)

# --- 애플리케이션 경로 확인 ---
def get_base_path():
    """ Get the base path, whether running from source or as a bundled exe. """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (e.g., PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # We are running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

# --- 로깅 설정 ---
# 로그 파일을 애플리케이션 위치에 'server_launcher.log'로 생성합니다.
log_file = os.path.join(get_base_path(), 'server_launcher.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # logging.StreamHandler() # 콘솔에도 로그를 출력하려면 주석 해제
    ]
)

# --- 설정 파일 관리 ---
CONFIG_FILE = os.path.join(get_base_path(), 'server_config.json')

def load_config():
    default_config = {
        "MySQL": {
            "type": "service",
            "service_name": "MySQL84",
            "config_path": "C:/WISE/Xampp/mysql/bin/my.ini"
        },
        # "MySQL_Process_Example": { # MySQL을 프로세스로 사용하려면 주석을 해제하고 수정하세요
        #     "type": "process",
        #     "process_name": "mysqld.exe",
        #     "start_cmd": ["C:\\xampp\\mysql\\bin\\mysqld.exe", "--console"], # 예시 경로, 필요에 따라 수정
        #     "stop_cmd": ["taskkill", "/F", "/IM", "mysqld.exe"], # 예시 중지 명령
        #     "cwd": "C:\\xampp\\mysql\\bin", # 예시 작업 디렉토리
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
            "process_name": "node.exe", # node.exe가 백엔드를 실행한다고 가정
            "start_cmd": [r"C:\\WISE\\Account-manager\\start_backend.bat"],
            "stop_cmd": ["for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :5000') do taskkill /PID %a /F"],
            "cwd": r"C:\\WISE\\Account-manager",
            "show_console": False,
        },
        "Frontend": {
            "type": "process",
            "process_name": "node.exe", # node.exe가 프론트엔드를 실행한다고 가정
            "start_cmd": [r"C:\\WISE\\Account-manager\\start_frontend.bat"],
            "stop_cmd": ["for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :3000') do taskkill /PID %a /F"],
            "cwd": r"C:\\WISE\\Account-manager",
            "show_console": False,
        },
        "Auth Server": {
            "type": "process",
            "process_name": "authserver.exe",
            "start_cmd": [r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo\\authserver.exe"],
            "cwd": r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo",
            "show_console": False,
            "config_path": r"C:/WISE/BUILD/bin/RelWithDebInfo/configs/authserver.conf"
        },
        "World Server": {
            "type": "process",
            "process_name": "worldserver.exe",
            "start_cmd": [r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo\\worldserver.exe"],
            "cwd": r"C:\\WISE\\BUILD\\bin\\RelWithDebInfo",
            "show_console": False,
            "config_path": r"C:/WISE/BUILD/bin/RelWithDebInfo/configs/worldserver.conf"
        },
        "auto_restart_enabled": False, # 자동 재시작을 위한 새로운 설정
        "editor_path": "notepad.exe", # 기본 에디터
    }

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            # 로드된 설정에 새로운 키가 없으면 기본값으로 추가합니다.
            for server_name, server_data in loaded_config.items():
                if isinstance(server_data, dict) and server_data.get("type") == "process":
                    if "start_cmd" in server_data and isinstance(server_data["start_cmd"], str):
                        server_data["start_cmd"] = [server_data["start_cmd"]]
                    if "stop_cmd" in server_data and isinstance(server_data["stop_cmd"], str):
                        server_data["stop_cmd"] = [server_data["stop_cmd"]]
            # 로드된 설정에 새 키가 없으면 추가
            if "auto_restart_enabled" not in loaded_config:
                loaded_config["auto_restart_enabled"] = default_config["auto_restart_enabled"]
            if "editor_path" not in loaded_config:
                loaded_config["editor_path"] = default_config["editor_path"]
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
        # 데이터가 딕셔너리(서버 설정)인 경우 복사합니다.
        if isinstance(server_data, dict):
            saveable_config[server_name] = server_data.copy()
        # 그렇지 않은 경우(editor_path 또는 auto_restart_enabled와 같은 전역 설정) 값을 할당하기만 하면 됩니다.
        else:
            saveable_config[server_name] = server_data

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saveable_config, f, indent=4)
        logging.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logging.error(f"Error saving config file: {e}")

# --- 전역 설정 변수 ---
SERVER_CONFIG = load_config()

# --- 메인 애플리케이션 클래스 ---
class ServerLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(_("Server Launcher"))
        self.geometry("1000x580")
        self.minsize(1000, 580)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- 클래스 변수 초기화 ---
        self.server_widgets = {}  # 서버별 UI 위젯 저장
        self.server_processes = {} # 서버 프로세스(Popen 객체) 저장
        self.last_all_action_time = 0 # '모두 시작/정지' 버튼 쿨다운
        self.server_checkbox_vars = {} # 체크박스 변수 저장
        self.checkboxes = {} # 체크박스 위젯 저장
        self.select_all_var = ctk.BooleanVar() # '전체 선택' 체크박스 변수

        # --- 자동 재시작 관련 변수 ---
        self.intended_stops = set() # 사용자가 의도적으로 중지한 서버 목록
        self.restart_attempts = {name: 0 for name in SERVER_CONFIG if isinstance(SERVER_CONFIG[name], dict)} # 서버별 재시작 시도 횟수
        self.server_stable_timers = {} # 서버 안정화 타이머
        self.MAX_RESTARTS = 2 # 최대 재시작 횟수 2
        self.STABILITY_THRESHOLD = 60 # seconds # 안정화 시간 (초)

        # --- 메인 프레임 생성 ---
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- 서버 목록을 담을 프레임 ---
        self.server_list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.server_list_frame.pack(fill="x", padx=10, pady=5)

        # --- 그리드 레이아웃 설정 ---
        self.server_list_frame.grid_columnconfigure(0, weight=0)  # 체크박스
        self.server_list_frame.grid_columnconfigure(1, weight=2)  # 이름
        self.server_list_frame.grid_columnconfigure(2, weight=3)  # 경로
        self.server_list_frame.grid_columnconfigure(3, weight=1)  # 상태
        self.server_list_frame.grid_columnconfigure(4, weight=0)  # 시작 버튼
        self.server_list_frame.grid_columnconfigure(5, weight=0)  # 정지 버튼

        # --- '모든 서버' 행 생성 ---
        self.create_all_servers_row(self.server_list_frame, row=0)

        # --- 구분선 ---
        separator = ctk.CTkFrame(self.server_list_frame, height=2, fg_color="gray50")
        separator.grid(row=1, column=0, columnspan=6, sticky="ew", pady=5, padx=5)

        # --- 각 서버 행 생성 ---
        row_index = 2
        for name, config in SERVER_CONFIG.items():
            if not isinstance(config, dict): # 서버 설정이 아닌 항목은 건너뜀
                continue 
            self.create_server_row(self.server_list_frame, name, row=row_index)
            row_index += 1

        # --- 로그 박스 ---
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="x", expand=False, padx=10, pady=10)
        log_label = ctk.CTkLabel(log_frame, text=_("Logs"), font=ctk.CTkFont(family="맑은 고딕", size=14))
        log_label.pack(anchor="w", padx=10, pady=(5,0))
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", height=100, font=ctk.CTkFont(family="맑은 고딕", size=12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        # --- 종료 버튼 ---
        quit_button = ctk.CTkButton(main_frame, text=_("Quit"), command=self.on_quit_button_click, fg_color="#FF5722", hover_color="#E64A19", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"), corner_radius=0)
        quit_button.pack(side="right", pady=10, padx=5)

        # --- 설정 버튼 ---
        config_button = ctk.CTkButton(main_frame, text=_("Config"), command=self.open_config_window, font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"), corner_radius=0)
        config_button.pack(side="right", pady=10, padx=5)

        # --- 모니터링 시작 ---
        self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        self.monitor_thread.start()
        self.log(_("Launcher started. Monitoring servers..."))

        # --- 창 닫기 처리 ---
        self.protocol("WM_DELETE_WINDOW", self.on_quit_button_click)

    def open_config_window(self):
        config_window = ConfigWindow(self)
        config_window.grab_set()

    def create_server_row(self, parent, name, row):
        config = SERVER_CONFIG[name]

        # 체크박스
        self.server_checkbox_vars[name] = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(parent, text="", variable=self.server_checkbox_vars[name], command=self.on_checkbox_select, onvalue=True, offvalue=False)
        checkbox.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.checkboxes[name] = checkbox

        # 서버 이름 및 유형
        name_type_label = ctk.CTkLabel(parent, text=f"{name}", font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"))
        name_type_label.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        # 경로 레이블
        path_text = ""
        if config["type"] == "process" and config.get("start_cmd"):
            path_text = config["start_cmd"][0]
        elif config["type"] == "service" and config.get("service_name"):
            path_text = f"{_('Service')}: {config['service_name']}"
        
        path_label = ctk.CTkLabel(parent, text=f"{path_text}", font=ctk.CTkFont(family="맑은 고딕", size=12), wraplength=350) # 줄 바꿈 길이 조정
        path_label.grid(row=row, column=2, padx=10, pady=5, sticky="w")

        # 상태 레이블
        status_label = ctk.CTkLabel(parent, text=_("Unknown"), text_color="gray", font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        status_label.grid(row=row, column=3, padx=10, pady=5, sticky="w")

        # 시작 버튼
        start_button = ctk.CTkButton(parent, text=_("Start"), command=lambda n=name: self.start_server(n), fg_color="#43A047", hover_color="#2E7D32", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        start_button.grid(row=row, column=4, padx=5, pady=5)

        # 정지 버튼
        stop_button = ctk.CTkButton(parent, text=_("Stop"), command=lambda n=name: self.stop_server(n), fg_color="#D32F2F", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        stop_button.grid(row=row, column=5, padx=5, pady=5)

        self.server_widgets[name] = {
            "status": status_label,
            "start": start_button,
            "stop": stop_button,
            "path_label": path_label, # 설정 변경 시 업데이트를 위한 참조 저장
        }

    def create_all_servers_row(self, parent, row):
        # 이 행은 이제 메인 헤더 행 역할을 합니다
        select_all_checkbox = ctk.CTkCheckBox(parent, text="", variable=self.select_all_var, command=self.toggle_all_checkboxes, onvalue=True, offvalue=False)
        select_all_checkbox.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        name_header = ctk.CTkLabel(parent, text=_("All Servers"), font=ctk.CTkFont(family="맑은 고딕", size=16, weight="bold"))
        name_header.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        path_header = ctk.CTkLabel(parent, text=_("Path"), font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        path_header.grid(row=row, column=2, padx=10, pady=2, sticky="w")

        status_header = ctk.CTkLabel(parent, text=_("Status"), font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        status_header.grid(row=row, column=3, padx=10, pady=2, sticky="w")

        self.start_all_button = ctk.CTkButton(parent, text=_("Start All"), command=lambda: self.start_all_servers(), fg_color="#4CAF50", hover_color="#388E3C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0, state="disabled")
        self.start_all_button.grid(row=row, column=4, padx=5, pady=5)

        self.stop_all_button = ctk.CTkButton(parent, text=_("Stop All"), command=lambda: self.stop_all_servers(), fg_color="#F44336", hover_color="#B71C1C", width=80, height=30, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0, state="disabled")
        self.stop_all_button.grid(row=row, column=5, padx=5, pady=5)

    def toggle_all_checkboxes(self):
        is_checked = self.select_all_var.get()
        for name, var in self.server_checkbox_vars.items():
            var.set(is_checked)
        self.update_all_buttons_state()

    def on_checkbox_select(self):
        all_checked = all(var.get() for var in self.server_checkbox_vars.values())
        self.select_all_var.set(all_checked)
        self.update_all_buttons_state()

    def update_all_buttons_state(self):
        any_selected = any(var.get() for var in self.server_checkbox_vars.values())
        button_state = "normal" if any_selected else "disabled"
        self.start_all_button.configure(state=button_state)
        self.stop_all_button.configure(state=button_state)

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

    def start_server(self, name, is_auto_restart=False):
        # 이미 실행 중인 경우 수동 시작 방지
        if not is_auto_restart and self.check_server_status(name) == "Running":
            message = f"{name} 서버는 이미 실행 중입니다.\n추가적인 조치는 취하지 않습니다."
            CTkMessagebox(title=_("Server Running"), message=message, icon="info")
            self.log(f"{name} is already running. Manual start ignored.")
            return

        # 사용자가 이 서버를 실행하려고 함을 표시
        if name in self.intended_stops:
            self.intended_stops.remove(name)

        # 더블 클릭을 방지하기 위해 즉시 UI 업데이트
        self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
        self.server_widgets[name]["start"].configure(state="disabled")
        self.server_widgets[name]["stop"].configure(state="disabled")

        config = SERVER_CONFIG[name]
        self.log(f"Attempting to start {name}...")

        try:
            if config["type"] == "service":
                subprocess.run(["net", "start", config["service_name"]], check=True, capture_output=True, text=True)
                self.log(f"Service {name} started successfully.")
            elif config["type"] == "process":
                command_to_run = config["start_cmd"]
                use_shell = command_to_run[0].lower().endswith((".bat", ".cmd"))
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
            
            # 서버가 성공적으로 시작되면 재시작 시도 횟수를 재설정하는 검사를 예약합니다.
            if name in self.server_stable_timers:
                self.server_stable_timers[name].cancel() # 기존 타이머 취소
            
            timer = threading.Timer(self.STABILITY_THRESHOLD, self._mark_server_as_stable, args=[name])
            self.server_stable_timers[name] = timer
            timer.start()

        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            self.log(f"ERROR starting {name}: {e}", level="error")
            # 시작이 실패하면 즉시 중지된 것으로 간주되므로 바로 다시 시작하지 마십시오.
            self.intended_stops.add(name)

    def stop_server(self, name):
        # 사용자가 이 서버를 중지하려고 함을 표시
        self.intended_stops.add(name)
        
        # 서버가 수동으로 중지되면 안정성 타이머를 취소합니다.
        if name in self.server_stable_timers:
            self.server_stable_timers[name].cancel()
            del self.server_stable_timers[name]

        # 더블 클릭을 방지하기 위해 즉시 UI 업데이트
        self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
        self.server_widgets[name]["start"].configure(state="disabled")
        self.server_widgets[name]["stop"].configure(state="disabled")

        config = SERVER_CONFIG[name]
        self.log(f"Attempting to stop {name}...")

        try:
            if config["type"] == "service":
                subprocess.run(["net", "stop", config["service_name"]], check=True, capture_output=True, text=True)
                self.log(f"Service {name} stopped successfully.")
            elif config["type"] == "process":
                # 먼저 추적된 프로세스와 그 자식 프로세스를 종료해 보십시오.
                if name in self.server_processes and self.server_processes[name].poll() is None:
                    pid = self.server_processes[name].pid
                    self.log(f"Terminating {name} process tree with parent PID {pid}...")
                    try:
                        parent = psutil.Process(pid)
                        # 자식 프로세스 먼저 종료
                        children = parent.children(recursive=True)
                        for child in children:
                            self.log(f"Terminating child process {child.name()} with PID {child.pid}")
                            child.terminate()
                        # 그 다음 부모 프로세스 종료
                        parent.terminate()
                        # 프로세스가 종료될 때까지 기다립니다.
                        psutil.wait_procs(children + [parent], timeout=3)
                    except psutil.NoSuchProcess:
                        self.log(f"Process with PID {pid} not found, it might have already been stopped.", level="warning")
                    
                    self.server_processes.pop(name) # 추적에서 제거
                    return

                # 중지 명령이 있으면 실행
                if config.get("stop_cmd"):
                    # shell=True를 사용할 때 명령은 문자열이어야 합니다.
                    # 설정은 명령을 리스트로 저장하므로 첫 번째 요소를 사용합니다.
                    command_to_run = config["stop_cmd"][0]
                    # cmd 창이 깜박이고 콘솔에 출력되는 것을 방지하려면 capture_output=True를 사용하십시오.
                    subprocess.run(command_to_run, cwd=config.get("cwd"), check=True, shell=True, capture_output=True)
                    self.log(f"Executed stop command for {name}.")
                else:
                    # 대체 방법: 해당 이름의 모든 프로세스를 종료합니다 (주의해서 사용)
                    # 이 부분은 필수 프로세스를 죽이지 않도록 주의해야 합니다.
                    found_and_terminated = False
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            # 프로세스 이름이 구성된 process_name과 일치하는지 확인
                            # 그리고 명령줄에 start_cmd가 포함되어 있는지 확인 (더 구체적인 일치를 위해)
                            if proc.info['name'].lower() == config['process_name'].lower():
                                cmdline = proc.cmdline()
                                # start_cmd의 일부가 프로세스의 명령줄에 있는지 확인
                                if any(os.path.basename(cmd_part).lower() in arg.lower() for cmd_part in config['start_cmd'] for arg in cmdline):
                                    self.log(f"Found running process {proc.info['name']} with PID {proc.info['pid']}. Terminating...", level="warning")
                                    psutil.Process(proc.info['pid']).terminate()
                                    found_and_terminated = True
                                    break # 하나의 인스턴스만 종료
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if found_and_terminated:
                        self.log(f"Process {name} terminated via fallback method.")
                    else:
                        self.log(f"No running process found for {name} to terminate via fallback.", level="warning")
        except (subprocess.CalledProcessError, psutil.NoSuchProcess, Exception) as e:
            self.log(f"ERROR stopping {name}: {e}", level="error")

    def start_all_servers(self):
        # 1. 선택한 서버 중 실제로 시작해야 하는 서버를 식별합니다.
        servers_to_start = [name for name, var in self.server_checkbox_vars.items() if var.get() and self.check_server_status(name) == "Stopped"]

        # 2. 시작할 서버가 없으면 기록하고 쿨다운 없이 종료합니다.
        if not servers_to_start:
            self.log("All selected servers are already running or none are selected for starting.", level="info")
            return

        # 3. 동적 쿨다운을 계산하여 적용하고 버튼을 비활성화합니다.
        cooldown_duration = (len(servers_to_start) * 2) + 3
        self.log(f"Starting {len(servers_to_start)} server(s). Cooldown set to {cooldown_duration} seconds.")

        self.last_all_action_time = time.time()
        self.start_all_button.configure(state="disabled")
        self.stop_all_button.configure(state="disabled")
        
        # 4. 필요한 서버만으로 작업자 스레드를 시작합니다.
        threading.Thread(target=self._start_all_worker, args=(servers_to_start,), daemon=True).start()
        self.after(cooldown_duration * 1000, self._enable_all_buttons)

    def _start_all_worker(self, servers_to_start):
        self.log(f"Attempting to start: {', '.join(servers_to_start)}")
        # 서비스를 먼저 시작
        for name in servers_to_start:
            if SERVER_CONFIG[name]["type"] == "service":
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.start_server(name)
                self._wait_for_status_change(name, _("Running"))
        # 그 다음 프로세스
        for name in servers_to_start:
            if SERVER_CONFIG[name]["type"] == "process":
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.start_server(name)
                self._wait_for_status_change(name, _("Running"))
        self.log("All targeted server start commands issued.")

    def stop_all_servers(self):
        # 1. 선택한 서버 중 실제로 중지해야 하는 서버를 식별합니다.
        servers_to_stop = [name for name, var in self.server_checkbox_vars.items() if var.get() and self.check_server_status(name) == "Running"]

        # 2. 중지할 서버가 없으면 기록하고 쿨다운 없이 종료합니다.
        if not servers_to_stop:
            self.log("All selected servers are already stopped or none are selected for stopping.", level="info")
            return

        # 3. 동적 쿨다운을 계산하여 적용하고 버튼을 비활성화합니다.
        cooldown_duration = (len(servers_to_stop) * 2) + 3
        self.log(f"Stopping {len(servers_to_stop)} server(s). Cooldown set to {cooldown_duration} seconds.")

        self.last_all_action_time = time.time()
        self.start_all_button.configure(state="disabled")
        self.stop_all_button.configure(state="disabled")

        # 4. 필요한 서버만으로 작업자 스레드를 시작합니다.
        threading.Thread(target=self._stop_all_worker, args=(servers_to_stop,), daemon=True).start()
        self.after(cooldown_duration * 1000, self._enable_all_buttons)

    def _stop_all_worker(self, servers_to_stop):
        self.log(f"Attempting to stop: {', '.join(servers_to_stop)}")
        # 프로세스를 먼저 중지
        for name in reversed(servers_to_stop):
            if SERVER_CONFIG[name]["type"] == "process":
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.stop_server(name)
                self._wait_for_status_change(name, _("Stopped"))
        # 그 다음 서비스
        for name in reversed(servers_to_stop):
            if SERVER_CONFIG[name]["type"] == "service":
                self.server_widgets[name]["status"].configure(text=_("Progressing..."), text_color="orange")
                self.stop_server(name)
                self._wait_for_status_change(name, _("Stopped"))
        self.log("All targeted server stop commands issued.")

    def _enable_all_buttons(self):
        self.update_all_buttons_state()
        self.log("Start All/Stop All buttons re-enabled.")

    def _wait_for_status_change(self, name, target_status, timeout=2):
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.check_server_status(name)
            if current_status == target_status:
                self.log(f"{name} status changed to {target_status}.")
                return True
            time.sleep(0.1) # 100밀리초마다 폴링
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
                # 기본 확인: 추적된 프로세스가 살아 있습니까?
                if name in self.server_processes and self.server_processes[name].poll() is None:
                     status = "Running"
                else:
                    # 대체 확인: 해당 이름으로 실행 중인 프로세스가 있습니까?
                    # 더 정확한 일치를 위해 구성된 process_name 사용
                    target_process_name = config['process_name'].lower()

                    for proc in psutil.process_iter(['name', 'cmdline']):
                        try:
                            if proc.info['name'].lower() == target_process_name:
                                # 이전 확인은 배치 파일로 시작된 프로세스에 대해 너무 엄격해서,
                                # 구성된 process_name과 일치시키는 것이 여기에서 더 신뢰할 수 있음.
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
            for name, config in SERVER_CONFIG.items():
                if not isinstance(config, dict): # 'auto_restart_enabled' 또는 'editor_path'와 같은 비서버 항목 건너뛰기
                    continue 

                status = self.check_server_status(name)
                
                # 상태 레이블 업데이트
                widget = self.server_widgets[name]["status"]
                if status == "Running":
                    widget.configure(text=_("Running"), text_color="#66BB6A")
                elif status == "Stopped":
                    widget.configure(text=_("Stopped"), text_color="#EF5350")
                else: # 오류 등에 대한 수정된 상태 표시
                    widget.configure(text=_(status), text_color="gray") 

                # 버튼 상태 업데이트
                start_button = self.server_widgets[name]["start"]
                stop_button = self.server_widgets[name]["stop"]

                if status == "Running":
                    start_button.configure(state="disabled")
                    stop_button.configure(state="normal")
                elif status == "Stopped":
                    start_button.configure(state="normal")
                    stop_button.configure(state="disabled")
                else:  # "오류" 또는 기타 상태의 경우
                    start_button.configure(state="disabled")
                    stop_button.configure(state="disabled")

                # 자동 재시작 처리
                config = SERVER_CONFIG[name]
                if config.get("auto_restart", False) and status == "Stopped" and name not in self.intended_stops:
                    if self.restart_attempts.get(name, 0) < self.MAX_RESTARTS:
                        self.restart_attempts[name] = self.restart_attempts.get(name, 0) + 1
                        self.log(f"AUTO-RESTART: {name} is stopped unexpectedly. Restarting... (Attempt {self.restart_attempts[name]}/{self.MAX_RESTARTS})", level="warning")
                        self.start_server(name, is_auto_restart=True)
                    else:
                        self.log(f"AUTO-RESTART DISABLED: {name} has failed to start {self.MAX_RESTARTS} times. Disabling auto-restart for this server.", level="error")
                        # 로그 스팸을 방지하기 위해 이 세션에 대한 자동 재시작 비활성화
                        config["auto_restart"] = False 
                        # 선택적으로 사용자에게 메시지를 표시할 수 있습니다.
                        # self.after(0, lambda n=name: CTkMessagebox(title="Auto-restart Disabled", message=f"{n} failed to start multiple times and auto-restart has been disabled for it."))

            time.sleep(5)

    def _mark_server_as_stable(self, name):
        """서버가 안정적으로 유지되면 재시작 횟수를 재설정하기 위해 타이머에 의해 호출됩니다."""
        if self.check_server_status(name) == "Running":
            if self.restart_attempts.get(name, 0) > 0:
                self.log(f"{name} has been stable for {self.STABILITY_THRESHOLD} seconds. Resetting restart attempts.", level="info")
                self.restart_attempts[name] = 0
        
        # 타이머 참조 정리
        if name in self.server_stable_timers:
            del self.server_stable_timers[name]

    def on_quit_button_click(self):
        msg = CustomMessageBox(
            title=_("Quit Launcher?"),
            message=_("Are you sure you want to quit?\nRunning servers will not be affected."),
            font=ctk.CTkFont(family="맑은 고딕", size=12),
            option_1=_("No"),
            option_2=_("Yes")
        )
        response = msg.get()
        if response == _("Yes"):
            self.log("User confirmed quit. Exiting launcher.")
            self.destroy()
        else:
            self.log("User cancelled quit.")

class CustomMessageBox(ctk.CTkToplevel):
    def __init__(self, title, message, font, option_1, option_2):
        super().__init__()

        self.title(title)
        self.lift()
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(10, self.lift)
        self.response = None

        # 부모 창의 중앙에 대화 상자 배치
        parent = self.master
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        self_width = 350
        self_height = 150
        pos_x = parent_x + (parent_width // 2) - (self_width // 2)
        pos_y = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.grab_set() # 모달로 만들기

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        message_label = ctk.CTkLabel(main_frame, text=message, font=font, wraplength=320, justify="center")
        message_label.pack(pady=(0, 20), expand=True, fill="both")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        # 버튼 1 (예: "아니요")
        btn1 = ctk.CTkButton(button_frame, text=option_1, font=font, width=100, command=lambda: self._button_click(option_1))
        btn1.pack(side="left", padx=10)

        # 버튼 2 (예: "예")
        btn2 = ctk.CTkButton(button_frame, text=option_2, font=font, width=100, command=lambda: self._button_click(option_2))
        btn2.pack(side="right", padx=10)

    def _button_click(self, response):
        self.response = response
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self.response = None
        self.grab_release()
        self.destroy()

    def get(self):
        self.wait_window()
        return self.response

class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title(_("Server Configuration"))
        self.geometry("950x600")
        self.minsize(950, 600)
        self.grab_set()

        self.selected_server_name = None
        self.server_config_widgets = {}
        self.highlight_color = "#107C41"  # 선택 및 호버를 위한 녹색
        self.modified_servers = set()

        # 변경 사항을 스테이징하기 위해 설정의 임시 사본 만들기
        self.temp_config = copy.deepcopy(SERVER_CONFIG)

        # 메인 컨테이너 프레임
        container = ctk.CTkFrame(self)
        container.pack(pady=20, padx=20, fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=3)
        container.grid_rowconfigure(0, weight=1)

        # --- 왼쪽: 서버 목록 ---
        server_list_container = ctk.CTkFrame(container, fg_color="transparent")
        server_list_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(server_list_container, text=_("Server Name"), font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(server_list_container, text=_("Type"), font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        row_num = 1
        for name, config in self.temp_config.items():
            if not isinstance(config, dict): # 'editor_path'와 같은 비서버 항목 건너뛰기
                continue 

            select_button = ctk.CTkButton(server_list_container, text=name, 
                                          font=ctk.CTkFont(family="맑은 고딕", size=12),
                                          command=lambda n=name: self._select_server(n),
                                          anchor="w", corner_radius=0,
                                          hover_color=self.highlight_color,
                                          width=150)
            select_button.grid(row=row_num, column=0, padx=5, pady=2, sticky="w")

            type_optionmenu = ctk.CTkOptionMenu(server_list_container, values=[_("process"), _("service")],
                                                command=lambda value, n=name: self._on_type_change(value, n),
                                                font=ctk.CTkFont(family="맑은 고딕", size=12),
                                                dropdown_font=ctk.CTkFont(family="맑은 고딕", size=12), corner_radius=0)
            type_optionmenu.set(_(config["type"]))
            type_optionmenu.grid(row=row_num, column=1, padx=5, pady=2, sticky="w")

            self.server_config_widgets[name] = {
                "select_button": select_button,
                "type_optionmenu": type_optionmenu,
                "widgets": {}
            }
            row_num += 1

        # --- 오른쪽: 세부 정보 패널 ---
        self.details_frame = ctk.CTkFrame(container)
        self.details_frame.grid(row=0, column=1, sticky="nsew")
        self.details_frame.grid_propagate(False)
        ctk.CTkLabel(self.details_frame, text=_("Select a server to configure its settings."), font=ctk.CTkFont(family="맑은 고딕", size=14)).pack(pady=20, padx=10)

        # --- 하단 버튼 및 옵션 ---
        bottom_frame = ctk.CTkFrame(container, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        bottom_frame.grid_columnconfigure(0, weight=1) # 왼쪽을 확장 가능하게 만들기

        # 왼쪽의 에디터 설정을 위한 프레임
        editor_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        editor_frame.grid(row=0, column=0, sticky="ew", padx=(5,10))
        editor_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(editor_frame, text=_("Editor"), font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold")).grid(row=0, column=0, padx=(0,5), pady=5)
        self.editor_path_entry = ctk.CTkEntry(editor_frame, font=ctk.CTkFont(family="맑은 고딕", size=12))
        self.editor_path_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.editor_path_entry.insert(0, self.temp_config.get("editor_path", "notepad.exe"))
        
        browse_editor_button = ctk.CTkButton(editor_frame, text=_("Browse"), width=70, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                             command=self._browse_editor_path, corner_radius=0)
        browse_editor_button.grid(row=0, column=2, padx=5, pady=5)

        # 오른쪽의 다른 컨트롤을 위한 프레임
        controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")

        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.pack(side="left")

        save_button = ctk.CTkButton(button_frame, text=_("Save All Configs"), command=self._save_all_configs, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        save_button.pack(side="right", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text=_("Cancel"), command=self.destroy, font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"), corner_radius=0)
        cancel_button.pack(side="right", padx=5)

    def _browse_editor_path(self):
        initial_dir = os.path.dirname(self.editor_path_entry.get()) if os.path.exists(self.editor_path_entry.get()) else os.getcwd()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir, title=_("Select Editor Executable"),
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*")))
        if file_path:
            self.editor_path_entry.delete(0, ctk.END)
            self.editor_path_entry.insert(0, file_path)
            self.master.log(f"Selected new editor path: {file_path}")
            # 이것은 모두와 함께 저장되는 전역 설정이므로 _mark_as_modified를 호출할 필요가 없습니다.

    def _mark_as_modified(self, server_name, *args):
        """서버를 수정된 것으로 표시하고 버튼 텍스트를 업데이트합니다."""
        if server_name not in self.modified_servers:
            self.modified_servers.add(server_name)
            self._update_server_list_indicators()

    def _update_server_list_indicators(self):
        """수정된 서버에 대해 '*'를 표시하도록 서버 목록 버튼을 업데이트합니다."""
        for name, widgets in self.server_config_widgets.items():
            button = widgets["select_button"]
            if name in self.modified_servers:
                button.configure(text=f"{name} *")
            else:
                button.configure(text=name)

    def _update_temp_config_from_ui(self, server_name):
        """UI 위젯에서 값을 읽어 temp_config 사전에 저장합니다."""
        if server_name is None or server_name not in self.server_config_widgets or not self.server_config_widgets[server_name].get("widgets"):
            return

        widgets = self.server_config_widgets[server_name]["widgets"]

        # 이 함수는 다른 서버 유형에 대해 UI를 다시 그리기 전에 호출됩니다.
        # 잠재적으로 새로운 server_type이 아닌 실제로 존재하는 위젯을 기반으로 UI를 읽어야 합니다.
        if "process_name_entry" in widgets: # 이 위젯은 'process' 유형에만 존재합니다.
            self.temp_config[server_name]["process_name"] = widgets["process_name_entry"].get()
            self.temp_config[server_name]["start_cmd"] = [widgets["start_cmd_entry"].get()]
            self.temp_config[server_name]["stop_cmd"] = [widgets["stop_cmd_entry"].get()] if widgets["stop_cmd_entry"].get() else []
            self.temp_config[server_name]["cwd"] = widgets["cwd_entry"].get()
            self.temp_config[server_name]["show_console"] = True if widgets["show_console_checkbox"].get() == 1 else False
            self.temp_config[server_name]["auto_restart"] = True if widgets["auto_restart_checkbox"].get() == 1 else False
        elif "service_name_entry" in widgets: # 이 위젯은 'service' 유형에만 존재합니다.
            self.temp_config[server_name]["service_name"] = widgets["service_name_entry"].get()
            self.temp_config[server_name]["auto_restart"] = True if widgets["auto_restart_checkbox"].get() == 1 else False

        if "config_path_entry" in widgets:
            self.temp_config[server_name]["config_path"] = widgets["config_path_entry"].get()

    def _select_server(self, server_name):
        """서버 선택, 이전 상태 저장 및 새 상태 표시를 처리합니다."""
        if self.selected_server_name is not None and self.selected_server_name != server_name:
            self._update_temp_config_from_ui(self.selected_server_name)

        self.selected_server_name = server_name
        self._update_button_highlights()
        self._display_server_details(server_name)

    def _on_type_change(self, new_type_translated, server_name):
        """유형이 변경될 때 로직을 처리합니다."""
        # 유형 역번역
        new_type = "process" if new_type_translated == _("process") else "service"

        # 유형을 변경하고 다시 그리기 전에 먼저 현재 UI 상태를 저장합니다.
        if self.selected_server_name == server_name:
            self._update_temp_config_from_ui(server_name)

        self._mark_as_modified(server_name)

        # 이제 임시 설정에서 유형을 업데이트합니다.
        self.temp_config[server_name]['type'] = new_type
        
        # 현재 선택된 서버가 변경 중인 서버인 경우 세부 정보 보기를 다시 그립니다.
        if self.selected_server_name == server_name:
            # 'process'로 전환할 때 MySQL에 대한 특별 처리
            if server_name == "MySQL" and new_type == "process":
                self.temp_config[server_name].update({
                    "process_name": "mysqld.exe",
                    "start_cmd": [os.path.join(os.getcwd(), "Xampp", "mysql_start.bat").replace("\\", "/")],
                    "stop_cmd": [os.path.join(os.getcwd(), "Xampp", "mysql_stop.bat").replace("\\", "/")],
                    "cwd": os.path.join(os.getcwd(), "Xampp").replace("\\", "/"),
                    "show_console": False
                })

            self._display_server_details(server_name)

    def _update_button_highlights(self):
        default_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        for name, widgets in self.server_config_widgets.items():
            button = widgets["select_button"]
            if name == self.selected_server_name:
                button.configure(fg_color=self.highlight_color)
            else:
                button.configure(fg_color=default_color)

    def _find_and_set_mysql_service(self, entry_widget):
        self.master.log("Scanning for MySQL services...")
        found_service = None
        try:
            for service in psutil.win_service_iter():
                if "mysql" in service.name().lower():
                    found_service = service
                    break # 윈도우서비스 중 유력한 프로세스 후보를 찾았고, 선택
            
            if found_service:
                msg = CTkMessagebox(title=_("MySQL Service Detection"), 
                                    message=_("Found service: {}. Use this?").format(found_service.name()),
                                    icon="question", option_1=_("Cancel"), option_2=_("OK"))
                if msg.get() == "OK":
                    entry_widget.delete(0, ctk.END)
                    entry_widget.insert(0, found_service.name())
                    self.master.log(f"Set MySQL service to '{found_service.name()}'")
                    self._mark_as_modified("MySQL")
            else:
                CTkMessagebox(title=_("MySQL Service Detection"), message=_("Could not find a running MySQL service."), icon="warning")
                self.master.log("Could not find a running MySQL service.", level="warning")

        except Exception as e:
            self.master.log(f"Error scanning for services: {e}", level="error")
            CTkMessagebox(title=_("Error"), message=str(e), icon="cancel")

    def _open_config_file(self, server_name):
        config_path = self.temp_config.get(server_name, {}).get("config_path")
        editor_path = self.temp_config.get("editor_path", "notepad.exe") # temp_config에서 편집기 가져오기

        if not editor_path:
            self.master.log("Editor path is not configured.", level="error")
            CTkMessagebox(title=_("Error"), message=_("Editor path is not configured."), icon="cancel")
            return

        if config_path and os.path.exists(config_path):
            try:
                # subprocess.Popen을 사용하여 파일과 함께 편집기 실행
                subprocess.Popen([editor_path, config_path])
                self.master.log(f"Opening config file for {server_name} with {editor_path}: {config_path}")
            except FileNotFoundError:
                self.master.log(f"Editor executable not found at: {editor_path}", level="error")
                CTkMessagebox(title=_("Error"), message=f"{_('Editor not found:')}\n{editor_path}", icon="cancel")
            except Exception as e:
                self.master.log(f"Failed to open config file {config_path} with {editor_path}: {e}", level="error")
                CTkMessagebox(title=_("Error"), message=str(e), icon="cancel")
        else:
            self.master.log(f"Config file not found for {server_name} at path: {config_path}", level="warning")
            CTkMessagebox(title=_("Error"), message=f"{_('Config file not found:')}\n{config_path}", icon="cancel")

    def _browse_path(self, entry_widget, server_name):
        initial_dir = os.path.dirname(entry_widget.get()) if os.path.exists(entry_widget.get()) else os.getcwd()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir, title=_("Select Executable"),
            filetypes=(("Executable files", "*.exe *.bat *.cmd"), ("All files", "*.*")))
        if file_path:
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, file_path)
            self.master.log(f"{_('Selected new path')}: {file_path}")
            self._mark_as_modified(server_name)

    def _display_server_details(self, server_name):
        """temp_config를 기반으로 지정된 서버에 대한 위젯으로 세부 정보 패널을 채웁니다."""
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        self.server_config_widgets[server_name]["widgets"] = {}
        config_data = self.temp_config[server_name]

        ctk.CTkLabel(self.details_frame, text=_("Settings for: {}").format(server_name), font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold")).pack(pady=(10, 20), padx=10, anchor="w")

        # MySQL에 대한 특별 지침
        if server_name == "MySQL":
            guide_frame = ctk.CTkFrame(self.details_frame, fg_color=("gray85", "gray20"))
            guide_frame.pack(fill="x", padx=10, pady=(0, 15))
            ctk.CTkLabel(guide_frame, text=_("If MySQL is installed and runs on boot, choose 'service'."), 
                         font=ctk.CTkFont(family="맑은 고딕", size=12)).pack(anchor="w", padx=10, pady=(5, 2))
            ctk.CTkLabel(guide_frame, text=_("If you run MySQL from a folder (e.g., XAMPP), choose 'process'."), 
                         font=ctk.CTkFont(family="맑은 고딕", size=12)).pack(anchor="w", padx=10, pady=(2, 5))

        # --- 설정 경로 입력 및 버튼 ---
        if "config_path" in config_data:
            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(row_frame, text=_("Config Path:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            config_path_entry = ctk.CTkEntry(row_frame, font=ctk.CTkFont(family="맑은 고딕", size=12))
            config_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            config_path_entry.insert(0, config_data.get("config_path", ""))
            config_path_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["config_path_entry"] = config_path_entry
            
            edit_button = ctk.CTkButton(row_frame, text=_("Edit Config File"), width=120, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                          command=lambda n=server_name: self._open_config_file(n), corner_radius=0)
            edit_button.pack(side="left")

        # 구분선
        if config_data["type"] == "process" or config_data["type"] == "service":
             separator = ctk.CTkFrame(self.details_frame, height=1, fg_color="gray50")
             separator.pack(fill="x", padx=10, pady=10)

        if config_data["type"] == "process":
            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=_("Process Name:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            process_name_entry = ctk.CTkEntry(row_frame, width=200, font=ctk.CTkFont(family="맑은 고딕", size=12))
            process_name_entry.pack(side="left", fill="x", expand=True)
            process_name_entry.insert(0, config_data.get("process_name", ""))
            process_name_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["process_name_entry"] = process_name_entry

            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=_("Start Cmd:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            start_cmd_entry = ctk.CTkEntry(row_frame, font=ctk.CTkFont(family="맑은 고딕", size=12))
            start_cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            start_cmd_list = config_data.get("start_cmd", [])
            if start_cmd_list:
                start_cmd_entry.insert(0, start_cmd_list[0])
            start_cmd_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["start_cmd_entry"] = start_cmd_entry
            browse_button = ctk.CTkButton(row_frame, text=_("Browse"), width=70, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                          command=lambda entry=start_cmd_entry, n=server_name: self._browse_path(entry, n), corner_radius=0)
            browse_button.pack(side="left")

            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=_("Stop Cmd:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            stop_cmd_entry = ctk.CTkEntry(row_frame, font=ctk.CTkFont(family="맑은 고딕", size=12))
            stop_cmd_entry.pack(side="left", fill="x", expand=True)
            stop_cmd_list = config_data.get("stop_cmd", [])
            if stop_cmd_list:
                stop_cmd_entry.insert(0, stop_cmd_list[0])
            stop_cmd_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["stop_cmd_entry"] = stop_cmd_entry

            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=_("CWD:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            cwd_entry = ctk.CTkEntry(row_frame, font=ctk.CTkFont(family="맑은 고딕", size=12))
            cwd_entry.pack(side="left", fill="x", expand=True)
            cwd_entry.insert(0, config_data.get("cwd", ""))
            cwd_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["cwd_entry"] = cwd_entry

            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            show_console_checkbox = ctk.CTkCheckBox(row_frame, text=_("Show Console"), font=ctk.CTkFont(family="맑은 고딕", size=12))
            show_console_checkbox.pack(side="left")
            if config_data.get("show_console", False):
                show_console_checkbox.select()
            show_console_checkbox.configure(command=lambda n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["show_console_checkbox"] = show_console_checkbox

            auto_restart_checkbox = ctk.CTkCheckBox(row_frame, text=_("Auto Restart Enabled"), font=ctk.CTkFont(family="맑은 고딕", size=12))
            auto_restart_checkbox.pack(side="left", padx=20)
            if config_data.get("auto_restart", False):
                auto_restart_checkbox.select()
            auto_restart_checkbox.configure(command=lambda n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["auto_restart_checkbox"] = auto_restart_checkbox

        elif config_data["type"] == "service":
            row_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=_("Service Name:"), font=ctk.CTkFont(family="맑은 고딕", size=12), width=100, anchor="w").pack(side="left")
            service_name_entry = ctk.CTkEntry(row_frame, width=200, font=ctk.CTkFont(family="맑은 고딕", size=12))
            service_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            service_name_entry.insert(0, config_data.get("service_name", ""))
            service_name_entry.bind("<KeyRelease>", lambda event, n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["service_name_entry"] = service_name_entry

            # MySQL에 대해서만 서비스를 자동으로 찾는 버튼 추가
            if server_name == "MySQL":
                find_button = ctk.CTkButton(row_frame, text=_("Find Service"), width=90, height=25, font=ctk.CTkFont(family="맑은 고딕", size=12),
                                              command=lambda entry=service_name_entry: self._find_and_set_mysql_service(entry), corner_radius=0)
                find_button.pack(side="left")

                # 필드가 비어 있으면 자동으로 서비스 검색
                if not config_data.get("service_name"):
                    self.after(100, lambda entry=service_name_entry: self._find_and_set_mysql_service(entry))

            row_frame_auto_restart = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row_frame_auto_restart.pack(fill="x", padx=10, pady=2)
            auto_restart_checkbox = ctk.CTkCheckBox(row_frame_auto_restart, text=_("Auto Restart Enabled"), font=ctk.CTkFont(family="맑은 고딕", size=12))
            auto_restart_checkbox.pack(side="left", pady=5)
            if config_data.get("auto_restart", False):
                auto_restart_checkbox.select()
            auto_restart_checkbox.configure(command=lambda n=server_name: self._mark_as_modified(n))
            self.server_config_widgets[server_name]["widgets"]["auto_restart_checkbox"] = auto_restart_checkbox

    def _save_all_configs(self):
        global SERVER_CONFIG
        
        if self.selected_server_name:
            self._update_temp_config_from_ui(self.selected_server_name)

        errors = []
        for name, config in self.temp_config.items():
            if name in ["auto_restart_enabled", "editor_path"]: continue
            
            if config['type'] == 'process':
                start_cmd = config.get("start_cmd", [""])[0]
                if not config.get("process_name"): errors.append(_("Process Name for {}" ).format(name))
                if not start_cmd: errors.append(_("Start Command for {}" ).format(name))
                elif not os.path.exists(start_cmd): errors.append(_("Start Command path for {} does not exist:\n{}" ).format(name, start_cmd))
            
            elif config['type'] == 'service':
                if not config.get("service_name"): errors.append(_("Service Name for {}" ).format(name))

        # UI에서 전역 설정 업데이트
        self.temp_config["editor_path"] = self.editor_path_entry.get()

        if errors:
            error_message = _("The following configuration errors occurred:\n\n") + "\n\n".join(errors)
            CTkMessagebox(title=_("Configuration Error"), message=error_message, icon="cancel")
            self.master.log(f"Configuration save failed due to errors: {errors}", level="error")
        else:
            SERVER_CONFIG.clear()
            SERVER_CONFIG.update(self.temp_config)
            save_config(SERVER_CONFIG)
            self.master.log(_("All server configurations saved successfully."))
            CTkMessagebox(title=_("Configuration Saved"), message=_("All server configurations saved successfully."), icon="check")

            self.modified_servers.clear()
            self._update_server_list_indicators()
            
            for name, config in SERVER_CONFIG.items():
                if name in ["auto_restart_enabled", "editor_path"]: continue
                if name in self.master.server_widgets and "path_label" in self.master.server_widgets[name]:
                    path_text = ""
                    if config["type"] == "process" and config.get("start_cmd"):
                        path_text = config["start_cmd"][0]
                    elif config["type"] == "service" and config.get("service_name"):
                        path_text = f"{_('Service')}: {config['service_name']}"
                    self.master.server_widgets[name]["path_label"].configure(text=path_text)

            self.destroy()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

if __name__ == "__main__":
    if is_admin():
        try:
            app = ServerLauncher()
            app.mainloop()
        except Exception as e:
            logging.error("An unhandled exception occurred which caused the application to close.")
            logging.error(traceback.format_exc())
            # 앱이 보이지 않을 가능성이 높으므로 사용자에게 메시지 상자를 표시하려고 시도합니다.
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw() # 빈 루트 창 숨기기
                messagebox.showerror(
                    "Critical Error",
                    f"A critical error occurred and the launcher must close.\n\n"
                    f"Please check the 'server_launcher.log' file for details.\n\n"
                    f"Error: {e}"
                )
            except Exception as mb_e:
                logging.error(f"Failed to show fallback error message box: {mb_e}")
    else:
        run_as_admin()

