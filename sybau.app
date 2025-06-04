# name: Fortnite EU Ping (ping3)
# description: Pings Fortnite EU server using ping3 module. Supports CLI and Tkinter GUI.
# version: 1.0
# category: Network Tools
# icon: 🎮
# args: --gui (optional, to run GUI)

import sys
import tkinter as tk
from tkinter import ttk
from ping3 import ping, exceptions

HOST = "ping-eu.ds.on.epicgames.com"

def ping_host(host):
    """
    Ping the host once, return ping in ms or None if fail.
    """
    try:
        delay = ping(host, timeout=2)
        if delay is None:
            return None
        return round(delay * 1000, 2)  # seconds to ms
    except exceptions.PingError:
        return None

def cli_mode():
    ping_time = ping_host(HOST)
    if ping_time is not None:
        print(f"Current ping to Fortnite Europe server ({HOST}): {ping_time} ms")
    else:
        print("Ping failed.")

class PingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fortnite EU Ping")
        self.geometry("300x150")
        self.resizable(False, False)

        self.host = HOST

        self.label = ttk.Label(self, text="Ping Fortnite Europe Server", font=("Arial", 14))
        self.label.pack(pady=10)

        self.ping_var = tk.StringVar(value="Click 'Ping' to test")
        self.ping_label = ttk.Label(self, textvariable=self.ping_var, font=("Arial", 12))
        self.ping_label.pack(pady=5)

        self.ping_button = ttk.Button(self, text="Ping", command=self.ping_server)
        self.ping_button.pack(pady=10)

    def ping_server(self):
        self.ping_var.set("Pinging...")
        self.update_idletasks()

        ping_time = ping_host(self.host)
        if ping_time is not None:
            self.ping_var.set(f"Ping: {ping_time} ms")
        else:
            self.ping_var.set("Ping failed")

if __name__ == "__main__":
    if "--gui" in sys.argv:
        app = PingApp()
        app.mainloop()
    else:
        cli_mode()
