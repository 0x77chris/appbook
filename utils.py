import os
from pathlib import Path
import re
from compiler import parse_metadata
import json
import subprocess
from tkinter import messagebox
import sys
import shutil
import platform

APP_DIR = Path("apps")
CONFIG_FILE = Path("launcher_config.json")
APPDATA_ROOT = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~/.local/share"), "AppLauncher")
APPDATA_VENV = os.path.join(APPDATA_ROOT, "venv")
APPDATA_APPS = os.path.join(APPDATA_ROOT, "apps")
DEFAULT_CONFIG = {
    "run_on_startup": False,
    "font_size": 12,
    "theme": "default",
    "python_path": os.path.join(APPDATA_VENV, 'Scripts' if platform.system() == 'Windows' else 'bin', 'python'),
    "offline_mode": False
}
Path(APPDATA_ROOT).mkdir(exist_ok=True)


# Ensure venv directory exists

# Function to create and return path to app's venv
def create_venv():
    if not os.path.exists(APPDATA_VENV):
        os.makedirs(APPDATA_VENV, exist_ok=True)
        subprocess.run([sys.executable, '-m', 'venv', APPDATA_VENV], check=True)
        return True
    else:
        return False



# Regex pattern
pattern = r'^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))'

def check_modules(path):
    with open(path, 'r', encoding='utf-8')as f:
        code = f.read()
        
        matches = re.findall(pattern, code, re.MULTILINE)
        
        modules = [mod1 or mod2 for mod1, mod2 in matches]
        resolve_missing_modules(modules, DEFAULT_CONFIG.get("python_path"))

def resolve_missing_modules(modules, python_path):
        offline_mode = DEFAULT_CONFIG.get("offline_mode", False)
        missing = []
        installed = []
        for mod in modules:
            try:
                subprocess.run([python_path, '-c', f'import {mod}'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                print(mod)
                missing.append(mod)

        if missing:
            if offline_mode:
                messagebox.showwarning("Offline Mode", f"The following modules are missing and cannot be installed in offline mode:\n{', '.join(missing)}")
            else:
                if messagebox.askyesno("Missing Modules", f"The following modules are missing:\n{', '.join(missing)}\nInstall them now?"):
                    subprocess.run([python_path, '-m', 'pip', 'install'] + missing, check=True)
                    installed.extend(missing)
                    with open("installed_modules.log", "a", encoding='utf-8') as log:
                        log.write(f"Installed for session: {', '.join(installed)}\n")
                        
        
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
        
def install_app(app_path):
    if not os.path.abspath(app_path).startswith(APPDATA_APPS):
        filename = os.path.basename(app_path)
        safe_path = os.path.join(APPDATA_APPS, filename)
        shutil.copy2(app_path, safe_path)
        return safe_path
    return app_path


    
def discover_apps():
    apps = []
    for filepath in Path(APPDATA_APPS).glob("*.app"):
        apps.append(parse_metadata(filepath))
    return apps

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    return {"run_on_startup": False}

def init_app():


    # Create app directory if it doesn't exist
    Path(APPDATA_APPS).mkdir(exist_ok=True)