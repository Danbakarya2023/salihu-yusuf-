import argparse
import os
import subprocess
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

LOG_FILE = os.path.join(os.path.dirname(__file__), "phone_status_log.txt")


def run_cmd(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8", errors="ignore")
    except FileNotFoundError:
        print("[!] 'adb' was not found. Please install Android platform-tools and make sure it is on PATH.")
        return ""
    except subprocess.CalledProcessError as exc:
        return exc.output.decode("utf-8", errors="ignore") if exc.output else ""


def log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


def check_device():
    out = run_cmd("adb devices")
    if not out:
        return False

    for line in out.splitlines():
        lowered = line.lower()
        if "list of devices attached" in lowered:
            continue
        if "device" in lowered and "offline" not in lowered and "unauthorized" not in lowered:
            return True
    return False


def get_screen_state():
    out = run_cmd("adb shell dumpsys power")

    if "Display Power: state=ON" in out:
        return "SCREEN_ON"
    if "Display Power: state=OFF" in out:
        return "SCREEN_OFF"
    return "UNKNOWN"


def get_lock_state():
    out = run_cmd("adb shell dumpsys window policy")

    if "mDreamingLockscreen=true" in out or "isStatusBarKeyguard=true" in out:
        return "LOCKED"
    if "mDreamingLockscreen=false" in out:
        return "UNLOCKED"
    return "UNKNOWN"


def collect_status():
    connected = check_device()
    if not connected:
        return {"connected": False, "screen": "UNKNOWN", "lock": "UNKNOWN", "status": "DISCONNECTED"}

    screen = get_screen_state()
    lock = get_lock_state()
    return {"connected": True, "screen": screen, "lock": lock, "status": f"{screen} | {lock}"}


def monitor_once():
    snapshot = collect_status()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not snapshot["connected"]:
        log("[!] No device connected")
        return snapshot

    log(f"[{timestamp}] STATUS: {snapshot['status']}")
    return snapshot


def monitor(interval=2):
    log("\n=== PHONE MONITOR STARTED ===\n")

    last_state = ""
    while True:
        snapshot = collect_status()
        if not snapshot["connected"]:
            time.sleep(interval)
            continue

        current_state = snapshot["status"]
        if current_state and current_state != last_state:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"[{timestamp}] STATUS CHANGE: {current_state}")
            last_state = current_state

        time.sleep(interval)


class PhoneMonitorApp(tk.Tk):
    def __init__(self, interval=2.0):
        super().__init__()
        self.interval = interval
        self.title("Phone Monitor Pro")
        self.geometry("900x620")
        self.minsize(860, 580)
        self.configure(bg="#0f172a")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#0f172a")
        self.style.configure("Card.TFrame", background="#111c33")
        self.style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        self.style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#f8fafc")
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#94a3b8")
        self.style.configure("Value.TLabel", font=("Segoe UI", 14, "bold"), foreground="#f8fafc")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        self.style.map("TButton", background=[("active", "#1d4ed8")])
        self.style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff")
        self.style.configure("Danger.TButton", background="#dc2626", foreground="#ffffff")
        self.style.configure("Secondary.TButton", background="#334155", foreground="#ffffff")

        self.running = False
        self.monitor_thread = None
        self.last_state = ""

        self.connection_var = tk.StringVar(value="Checking...")
        self.screen_var = tk.StringVar(value="Waiting")
        self.lock_var = tk.StringVar(value="Waiting")
        self.updated_var = tk.StringVar(value="No update yet")

        self.build_ui()
        self.refresh_log()

    def build_ui(self):
        header = ttk.Frame(self, padding=20)
        header.pack(fill="x")

        ttk.Label(header, text="Phone Monitor Pro", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Live Android device monitoring with a clean desktop dashboard", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(self, padding=(20, 0, 20, 10))
        controls.pack(fill="x")

        ttk.Button(controls, text="Start Monitor", style="Accent.TButton", command=self.start_monitoring).pack(side="left")
        ttk.Button(controls, text="Stop Monitor", style="Danger.TButton", command=self.stop_monitoring).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Check Once", style="Secondary.TButton", command=self.run_once).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Clear Log", style="Secondary.TButton", command=self.clear_log).pack(side="left", padx=(8, 0))

        cards = ttk.Frame(self, padding=(20, 5, 20, 10))
        cards.pack(fill="x")

        self.create_card(cards, "Connection", self.connection_var, 0)
        self.create_card(cards, "Screen", self.screen_var, 1)
        self.create_card(cards, "Lock", self.lock_var, 2)
        self.create_card(cards, "Last Update", self.updated_var, 3)

        log_frame = ttk.Frame(self, padding=(20, 5, 20, 20))
        log_frame.pack(fill="both", expand=True)

        ttk.Label(log_frame, text="Event Log", style="Value.TLabel").pack(anchor="w", pady=(0, 6))
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap="word", height=18, bg="#111c33", fg="#f8fafc", insertbackground="#f8fafc")
        self.log_area.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_card(self, parent, title, variable, column):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=14)
        frame.grid(row=0, column=column, padx=(0, 10), sticky="nsew")
        parent.columnconfigure(column, weight=1)

        ttk.Label(frame, text=title, style="Subtitle.TLabel").pack(anchor="w")
        ttk.Label(frame, textvariable=variable, style="Value.TLabel").pack(anchor="w", pady=(6, 0))

    def start_monitoring(self):
        if self.running:
            return

        self.running = True
        self._append_log("[>] Monitoring started")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.running = False
        self._append_log("[!] Monitoring stopped")

    def run_once(self):
        snapshot = monitor_once()
        self.update_view(snapshot)
        self.refresh_log()

    def clear_log(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as handle:
                handle.write("")
        self.refresh_log()

    def _monitor_loop(self):
        while self.running:
            snapshot = collect_status()
            self.after(0, lambda: self.update_view(snapshot))
            if snapshot["connected"] and snapshot["status"] != self.last_state:
                self.after(0, lambda: self._append_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] STATUS CHANGE: {snapshot['status']}"))
                self.last_state = snapshot["status"]
            time.sleep(self.interval)

    def update_view(self, snapshot):
        if snapshot["connected"]:
            self.connection_var.set("Connected")
            self.screen_var.set(snapshot["screen"])
            self.lock_var.set(snapshot["lock"])
        else:
            self.connection_var.set("Disconnected")
            self.screen_var.set("UNKNOWN")
            self.lock_var.set("UNKNOWN")

        self.updated_var.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.refresh_log()

    def refresh_log(self):
        if not os.path.exists(LOG_FILE):
            return

        with open(LOG_FILE, "r", encoding="utf-8") as handle:
            content = handle.read()

        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.insert(tk.END, content)
        self.log_area.configure(state="disabled")
        self.log_area.see(tk.END)

    def _append_log(self, message):
        self.after(0, lambda: self._append_log_now(message))

    def _append_log_now(self, message):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as handle:
                handle.write("")

        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
        self.refresh_log()

    def on_close(self):
        self.running = False
        self.destroy()


def main():
    parser = argparse.ArgumentParser(description="Monitor Android phone screen and lock state via ADB")
    parser.add_argument("--once", action="store_true", help="Run one check and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between checks")
    args = parser.parse_args()

    if args.once:
        monitor_once()
        return

    try:
        app = PhoneMonitorApp(interval=args.interval)
        app.mainloop()
    except tk.TclError as exc:
        print(f"[!] GUI unavailable: {exc}")
        monitor(interval=args.interval)


if __name__ == "__main__":
    main()