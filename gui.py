# gui.py
import os
import subprocess
import threading
import tkinter.filedialog as fd
import customtkinter as ctk
from tkinter import messagebox
import runner as runner
from utils import discover_apps, APP_DIR, CONFIG_FILE, DEFAULT_CONFIG
import platform
import json

ctk.set_default_color_theme("dark-blue")
ctk.set_appearance_mode("dark")

def set_startup(enable):
    system = platform.system()
    launcher_path = os.path.abspath(__file__)
    if system == "Windows":
        import winreg
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
    elif system == "Darwin":
        pass  # macOS support

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
        self.root.geometry("800x600")

        self.config = load_config()
        self.apps = discover_apps()
        self.filtered_apps = self.apps.copy()
        self.context_menu = None

        self.build_layout()
        self.populate_app_list()

    def build_layout(self):
        top_frame = ctk.CTkFrame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.on_search)

        search_entry = ctk.CTkEntry(top_frame, textvariable=self.search_var, placeholder_text="Search apps...")
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        install_btn = ctk.CTkButton(top_frame, text="Install App", command=self.install_app_modal)
        install_btn.pack(side="left", padx=5)

        settings_btn = ctk.CTkButton(top_frame, text="⚙ Settings", command=self.open_settings_window)
        settings_btn.pack(side="right")

        middle_frame = ctk.CTkFrame(self.root)
        middle_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.app_listbox = ctk.CTkTextbox(middle_frame, wrap="none")
        self.app_listbox.pack(side="left", fill="both", expand=True)
        self.app_listbox.bind("<Button-1>", self.launch_selected_app)
        self.app_listbox.bind("<Button-3>", self.show_context_menu)
        self.app_listbox.bind("<<Selection>>", self.show_description)

        self.description_label = ctk.CTkLabel(self.root, text="", anchor="w")
        self.description_label.pack(fill="x", padx=10, pady=(0, 5))

        terminal_frame = ctk.CTkFrame(self.root)
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.terminal_output = ctk.CTkTextbox(terminal_frame)
        self.terminal_output.pack(fill="both", expand=True)
        self.write_intro_to_terminal()

    def write_intro_to_terminal(self):
        import getpass
        user = getpass.getuser()
        self.terminal_output.insert("end", f"Microsoft Windows [Version 10.0.19045.0]\n(c) Microsoft Corporation. All rights reserved.\n\n{user}@launcher$\n")

    def open_settings_window(self):
        win = ctk.CTkToplevel(self.root)
        win.title("Settings")
        win.geometry("300x200")

        startup_var = ctk.BooleanVar(value=self.config.get("run_on_startup", False))
        font_var = ctk.IntVar(value=self.config.get("font_size", 12))

        def save_settings():
            self.config["run_on_startup"] = startup_var.get()
            self.config["font_size"] = font_var.get()
            set_startup(startup_var.get())
            save_config(self.config)
            win.destroy()

        ctk.CTkCheckBox(win, text="Run on Startup", variable=startup_var).pack(pady=10)
        ctk.CTkLabel(win, text="Font Size:").pack()
        ctk.CTkEntry(win, textvariable=font_var).pack(pady=5)
        ctk.CTkButton(win, text="Save", command=save_settings).pack(pady=10)

    def populate_app_list(self):
        self.app_listbox.delete("1.0", "end")
        for app in self.filtered_apps:
            line = f"{app['icon']} {app['name']} ({app['category']})\n"
            self.app_listbox.insert("end", line)

    def on_search(self, *_):
        term = self.search_var.get().lower()
        self.filtered_apps = [a for a in self.apps if term in a['name'].lower() or term in a['description'].lower() or term in a['category'].lower()]
        self.populate_app_list()

    def get_selected_app(self):
        try:
            index = int(self.app_listbox.index("insert").split(".")[0]) - 1
            return self.filtered_apps[index] if 0 <= index < len(self.filtered_apps) else None
        except:
            return None

    def prompt_args_if_needed(self, app):
        if 'args' in app:
            args_win = ctk.CTkInputDialog(text=f"Enter args for {app['name']}:", title="App Arguments")
            return args_win.get_input()
        return None

    def launch_selected_app(self, *_):
        app = self.get_selected_app()
        if not app:
            return
        args = self.prompt_args_if_needed(app)
        self.terminal_output.insert("end", f"\n>>> Launching {app['name']}...\n")
        threading.Thread(target=self.run_app_and_log, args=(app, args), daemon=True).start()

    def run_app_and_log(self, app, extra_args):
        try:
            command = ["python", app['path']]
            if extra_args:
                command += extra_args.split()
            proc = runner.run_app(app)
            for line in proc.stdout:
                self.terminal_output.insert("end", line)
                self.terminal_output.see("end")
        except Exception as e:
            self.terminal_output.insert("end", f"\n[Error: {str(e)}]\n")

    def uninstall_selected_app(self):
        app = self.get_selected_app()
        if not app:
            return
        confirm = messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall '{app['name']}'?")
        if confirm:
            os.remove(app['path'])
            self.apps = discover_apps()
            self.filtered_apps = self.apps.copy()
            self.populate_app_list()

    def install_app_modal(self):
        path = fd.askopenfilename(title="Select .app File", filetypes=[("App Files", "*.app")])
        if not path:
            return
        try:
            dest = APP_DIR / os.path.basename(path)
            with open(path, 'r') as src, open(dest, 'w') as dst:
                dst.write(src.read())
            messagebox.showinfo("Installed", f"{dest.name} installed successfully.")
            self.apps = discover_apps()
            self.filtered_apps = self.apps.copy()
            self.populate_app_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_context_menu(self, event):
        app = self.get_selected_app()
        if not app:
            return
        self.context_menu = ctk.CTkToplevel(self.root)
        self.context_menu.geometry(f"150x100+{event.x_root}+{event.y_root}")
        self.context_menu.overrideredirect(True)

        ctk.CTkButton(self.context_menu, text="Info", command=lambda: self.show_app_info(app)).pack(fill="x")
        ctk.CTkButton(self.context_menu, text="Uninstall", command=lambda: [self.uninstall_selected_app(), self.context_menu.destroy()]).pack(fill="x")
        ctk.CTkButton(self.context_menu, text="Close", command=self.context_menu.destroy).pack(fill="x")

    def show_app_info(self, app):
        messagebox.showinfo(app['name'], f"Description: {app['description']}\nVersion: {app['version']}\nCategory: {app['category']}")

    def show_description(self, *_):
        app = self.get_selected_app()
        if app:
            self.description_label.configure(text=f"{app['description']}")

if __name__ == '__main__':
    root = ctk.CTk()
    app = AppLauncherGUI(root)
    root.mainloop()
