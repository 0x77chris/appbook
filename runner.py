from time import sleep
from colorama import Fore
import subprocess
from utils import refresh_screen

def run_app(app):
    print(Fore.CYAN + f"Launching: {app['name']} v{app['version']}")
    print(Fore.YELLOW + f"{app['description']}")
    sleep(3)
    refresh_screen()
    proc = subprocess.Popen(["python", app['path']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    return proc
