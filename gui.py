# gui.py
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from utils import discover_apps, APP_DIR, DEFAULT_CONFIG, CONFIG_FILE, init_app
import platform
import json
import winreg

import utils

def set_startup(enable):
    system = platform.system()
    launcher_path = os.path.abspath(__file__)
    if system == "Windows":
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, "AppLauncher", 0, winreg.REG_SZ, f"python \"{launcher_path}\"")
        else:
            try:
                winreg.DeleteValue(key, "AppLauncher")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    elif system == "Linux":
        autostart_path = os.path.expanduser("~/.config/autostart/applauncher.desktop")
        if enable:
            os.makedirs(os.path.dirname(autostart_path), exist_ok=True)
            with open(autostart_path, "w") as f:
                f.write(f"[Desktop Entry]\nType=Application\nExec=python3 {launcher_path}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=AppLauncher\n")
        else:
            if os.path.exists(autostart_path):
                os.remove(autostart_path)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

class AppLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python App Launcher")
        self.root.geometry("1000x600")

        self.config = load_config()
        self.apps = discover_apps()
        self.filtered_apps = self.apps.copy()

        self.build_layout()
        self.populate_app_list()
        


    def build_layout(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)

        tk.Label(top_frame, text="Search:").pack(side="left", padx=5)
        tk.Entry(top_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        tk.Button(top_frame, text="Install App", command=self.install_app_modal).pack(side="left", padx=5)
        tk.Button(top_frame, text="Settings", command=self.open_settings_window).pack(side="right", padx=5)

        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned.pack(fill="both", expand=True)

        # Left pane: App List
        self.app_listbox = tk.Listbox(self.paned)
        self.app_listbox.bind("<Double-Button-1>", self.launch_selected_app)
        self.app_listbox.bind("<<ListboxSelect>>", self.show_description)
        self.paned.add(self.app_listbox)

        # Right pane: Terminal output and description
        right_pane = tk.PanedWindow(self.paned, orient=tk.VERTICAL)
        self.paned.add(right_pane)

        self.terminal_output = tk.Text(right_pane, wrap="word")
        self.terminal_output.insert("end", "App Book Program Runner [Version 0.10 Alpha]\n\n")
        right_pane.add(self.terminal_output)

        self.description_label = tk.Label(right_pane, text="", anchor="w")
        right_pane.add(self.description_label)
        self.install_venv(self.terminal_output)
        

    def open_settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("400x250")

        font_var = tk.IntVar(value=self.config.get("font_size", 12))
        run_var = tk.BooleanVar(value=self.config.get("run_on_startup", False))
        path_var = tk.StringVar(value=self.config.get("python_path", "python"))
        offline_var = tk.BooleanVar(value=self.config.get("offline_mode", False))

        tk.Checkbutton(win, text="Run on Startup", variable=run_var).pack(anchor="w", padx=10, pady=5)
        tk.Label(win, text="Font Size:").pack(anchor="w", padx=10)
        tk.Entry(win, textvariable=font_var).pack(fill="x", padx=10)
        tk.Label(win, text="Python Executable:").pack(anchor="w", padx=10)
        tk.Entry(win, textvariable=path_var).pack(fill="x", padx=10)
        tk.Checkbutton(win, text="Offline Mode", variable=offline_var).pack(anchor="w", padx=10, pady=5)

        def save():
            self.config["run_on_startup"] = run_var.get()
            self.config["font_size"] = font_var.get()
            self.config["python_path"] = path_var.get()
            self.config["offline_mode"] = offline_var.get()
            set_startup(run_var.get())
            save_config(self.config)
            win.destroy()

        tk.Button(win, text="Save", command=save).pack(pady=10)


    def populate_app_list(self):
        self.app_listbox.delete(0, tk.END)
        for app in self.filtered_apps:
            self.app_listbox.insert(tk.END, f"{app['icon']} {app['name']} ({app['category']})")

    def on_search(self, *_):
        term = self.search_var.get().lower()
        self.filtered_apps = [a for a in self.apps if term in a['name'].lower() or term in a['description'].lower() or term in a['category'].lower()]
        self.populate_app_list()

    def get_selected_app(self):
        index = self.app_listbox.curselection()
        if index:
            return self.filtered_apps[index[0]]
        return None


    def prompt_args_if_needed(self, app):
        if 'args' in app:
            return simpledialog.askstring("App Arguments", f"Enter arguments for {app['name']}")
        return None

    def run_app_in_venv(self, app, args, output_widget):
        try:
            python_exe = os.path.join(utils.APPDATA_VENV, 'Scripts' if platform.system() == 'Windows' else 'bin', 'python')
            command = [python_exe, app['path']] + (args.split() if args else [])
            utils.check_modules(app['path'])
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                output_widget.insert("end", line)
                output_widget.see("end")
            self.terminal_output.insert("end", "[Program Ended Successfully with Code 0]")
            
        except Exception as e:
            output_widget.insert("end", f"\n[Error running app in venv: {e}]\n")

    def launch_selected_app(self, *_):
        app = self.get_selected_app()
        if not app:
            return
        args = self.prompt_args_if_needed(app)
        self.terminal_output.insert("end", f"\nLaunching {app['name']} in virtual environment...\n")
        threading.Thread(target=self.run_app_in_venv, args=(app, args, self.terminal_output), daemon=True).start()
        
    def install_venv(self, output_widget):
        output_widget.insert("end", "\n[Checking For Virtual Environment...]\n")
        if utils.create_venv():
            output_widget.insert("end", "\n[Virtual Environment Created!]\n")
        else:
            output_widget.insert("end", "Virtual Environment Found!")
            
        
    def install_app_modal(self):
        path = filedialog.askopenfilename(title="Select .app File", filetypes=[("App Files", "*.app")])
        if not path:
            return
        utils.install_app(path)
        self.apps = discover_apps()
        self.filtered_apps = self.apps.copy()
        self.populate_app_list()

    def show_description(self, *_):
        app = self.get_selected_app()
        if app:
            self.description_label.config(text=f"{app['description']}")


if __name__ == '__main__':
    init_app()
    root = tk.Tk()
    root_app = AppLauncherGUI(root)
    root.mainloop()
