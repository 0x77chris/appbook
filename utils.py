import os
from pathlib import Path
from compiler import parse_metadata
import json
from colorama import Fore, init

APP_DIR = Path("apps")
CONFIG_FILE = Path("launcher_config.json")
DEFAULT_CONFIG = {
    "run_on_startup": False,
    "font_size": 12,
    "theme": "dark"
}


def refresh_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
        
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
        
def install_app():
    path = input("Enter path to the .app file: ").strip()
    if not os.path.exists(path):
        print(Fore.RED + "File not found.")
        return
    dest = APP_DIR / Path(path).name
    with open(path, 'r') as src, open(dest, 'w') as dst:
        dst.write(src.read())
    print(Fore.GREEN + f"Installed {dest.name}")
    
def discover_apps():
    apps = []
    for filepath in APP_DIR.glob("*.app"):
        apps.append(parse_metadata(filepath))
    return apps

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    return {"run_on_startup": False}

def init_app():
    refresh_screen()
        # Initialize colorama
    init(autoreset=True)


    # Create app directory if it doesn't exist
    APP_DIR.mkdir(exist_ok=True)