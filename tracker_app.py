import tkinter as tk
from tkinter import scrolledtext, messagebox
import random
import os
import math
import socket
from datetime import datetime

class TrackingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("ULTRA-TRACKER V4.0 — TACTICAL")
        self.root.geometry("1200x900")
        self.root.configure(bg="#020406")
        
        self.angle = 0  # For radar animation
        self.blips = [] # To store radar target points (x, y, opacity)
        self.generate_blips()

        # Styles & Colors
        self.accent_color = "#00ffcc"
        self.muted_color = "#99ffee"
        self.danger_color = "#ff3b30"
        self.panel_color = "#071011"
        self.bg_color = "#020406"

        # Tracked Device Info (will be updated from input fields)
        self.tracked_imei1 = "---"
        self.tracked_imei2 = "---"
        self.tracked_serial = "---"

        # Bayanan da za su rinka fitowa
        self.fake_events = [
            "READING FLASHING PHONE ...",
            "FORMAT DATA RESET AND FRP CHECK...",
            "Intercepted call signal...",
            "SMS data packet captured...",
            "GPS position updated...",
            "New device ID found...",
            "Voice pattern analysis running...",
            "Uploading encrypted logs...",
            "IMEI status: ACTIVE",
            "Please contact: 09032948833"
        ]

        self.phone_models = [
            "iPhone 14 Pro Max - SN: 9X82G4H2L0",
            "Samsung Galaxy S23 Ultra - SN: 7D92F5B3A1",
            "Tecno Phantom X2 - SN: 1H73D9P0K4",
            "Infinix Zero Ultra - SN: 4L89Z6Q2T8",
            "Huawei P50 Pro - SN: 6K93B7L1R5",
            "Google Pixel 7 Pro - SN: 2N58F9K7S3",
            "Nokia X30 - SN: 8H25R6M9T0",
            "Itel S23 Plus - SN: 3D64K8P1Z9",
            "OnePlus 11 - SN: 5J79L3Q2M1",
            "Sony Xperia 5 IV - SN: 0P41T7R2B8"
        ]

        self.setup_ui()
        self.update_data()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.panel_color, pady=10, padx=20)
        header.pack(fill="x")

        tk.Label(header, text="⚡ TACTICAL SURVEILLANCE", fg=self.accent_color, bg=self.panel_color, font=("Impact", 24)).pack(side="left")
        self.clock_label = tk.Label(header, text="", fg=self.muted_color, bg=self.panel_color, font=("Courier", 12, "bold"))
        self.clock_label.pack(side="right")

        # Warning Box
        warning_frame = tk.Frame(self.root, bg=self.danger_color, pady=10)
        warning_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(warning_frame, text="☢ CRITICAL WARNING — UNAUTHORIZED ACCESS DETECTED", 
                 fg="white", bg=self.danger_color, font=("Arial", 12, "bold")).pack()
        tk.Label(warning_frame, text="LIVE TRACE ACTIVE: DEVICE IS BEING PINPOINTED VIA GLOBAL SATELLITE NETWORK", 
                 fg="white", bg=self.danger_color, font=("Arial", 9)).pack()

        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # --- LEFT COLUMN ---
        left_col = tk.Frame(main_frame, bg=self.bg_color, padx=5, pady=5)
        left_col.pack(side="left", fill="both", expand=True)

        # Radar Panel (Now much bigger)
        radar_panel = tk.LabelFrame(left_col, text="📡 DEEP-SCAN SIGNAL RADAR", fg=self.accent_color, bg=self.panel_color, font=("Arial", 12, "bold"))
        radar_panel.pack(fill="x", padx=5, pady=5)
        
        self.radar_canvas = tk.Canvas(radar_panel, width=600, height=400, bg="#000", highlightthickness=0)
        self.radar_canvas.pack()

        # Logs and Code Stream Row
        bottom_row = tk.Frame(left_col, bg=self.bg_color)
        bottom_row.pack(fill="both", expand=True, pady=5)

        # Logs and Decryption Stream
        logs_decrypt_frame = tk.Frame(bottom_row, bg=self.bg_color)
        logs_decrypt_frame.pack(fill="both", expand=True, side="top")

        # Network Logs
        logs_panel = tk.LabelFrame(logs_decrypt_frame, text="📄 LIVE NETWORK INTERCEPTION", fg=self.accent_color, bg=self.panel_color, padx=10)
        logs_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(logs_panel, width=30, height=8, bg="#000", fg="#00ff00", font=("Courier", 9))
        self.log_area.pack(fill="both", expand=True, pady=5)

        # Decryption Stream (New)
        decrypt_panel = tk.LabelFrame(logs_decrypt_frame, text="🔐 DATA DECRYPTION STREAM", fg=self.accent_color, bg=self.panel_color, padx=10)
        decrypt_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.decrypt_area = tk.Text(decrypt_panel, width=30, height=8, bg="#000", fg=self.danger_color, font=("Courier", 9))
        self.decrypt_area.pack(fill="both", expand=True, pady=5)

        # Database Area
        db_panel = tk.LabelFrame(left_col, text="🔍 GLOBAL DEVICE DATABASE SCANNER", fg=self.accent_color, bg=self.panel_color, padx=10)
        db_panel.pack(fill="x", pady=5)
        self.phone_area = scrolledtext.ScrolledText(db_panel, width=80, height=4, bg="#000", fg=self.accent_color, font=("Courier", 9))
        self.phone_area.pack(fill="x")

        # --- RIGHT COLUMN (Sidebar) ---
        right_col = tk.Frame(main_frame, bg=self.panel_color, width=300, padx=15, pady=15)
        right_col.pack(side="right", fill="y", padx=10)
        right_col.pack_propagate(False)

        # Input Fields for IMEI and Serial
        input_panel = tk.LabelFrame(right_col, text="TARGET ACQUISITION", fg=self.accent_color, bg=self.panel_color, font=("Arial", 10, "bold"))
        input_panel.pack(fill="x", pady=(0, 15))
        
        tk.Label(input_panel, text="IMEI 1:", fg=self.muted_color, bg=self.panel_color, font=("Arial", 8)).pack(anchor="w")
        self.imei1_entry = tk.Entry(input_panel, bg="#000", fg=self.accent_color, insertbackground=self.accent_color, relief="flat")
        self.imei1_entry.pack(fill="x", pady=2)
        self.imei1_entry.insert(0, "353683070000001") # Placeholder

        tk.Label(input_panel, text="IMEI 2:", fg=self.muted_color, bg=self.panel_color, font=("Arial", 8)).pack(anchor="w", pady=(5,0))
        self.imei2_entry = tk.Entry(input_panel, bg="#000", fg=self.accent_color, insertbackground=self.accent_color, relief="flat")
        self.imei2_entry.pack(fill="x", pady=2)
        self.imei2_entry.insert(0, "353683070000002") # Placeholder

        tk.Label(input_panel, text="Serial No.:", fg=self.muted_color, bg=self.panel_color, font=("Arial", 8)).pack(anchor="w", pady=(5,0))
        self.serial_entry = tk.Entry(input_panel, bg="#000", fg=self.accent_color, insertbackground=self.accent_color, relief="flat")
        self.serial_entry.pack(fill="x", pady=2)
        self.serial_entry.insert(0, "SN1234567890") # Placeholder

        tk.Button(input_panel, text="START TRACKING", command=self.start_tracking, bg=self.accent_color, fg="#000", relief="flat", width=25, font=("Arial", 9, "bold")).pack(pady=10)

        # Display of Tracked Device Info
        target_info_panel = tk.LabelFrame(right_col, text="TARGET DEVICE INFO", fg=self.accent_color, bg=self.panel_color, font=("Arial", 10, "bold"))
        target_info_panel.pack(fill="x", pady=10)
        self.target_imei1_label = tk.Label(target_info_panel, text=f"IMEI 1: {self.tracked_imei1}", fg=self.muted_color, bg=self.panel_color, font=("Courier", 9))
        self.target_imei1_label.pack(anchor="w")
        self.target_imei2_label = tk.Label(target_info_panel, text=f"IMEI 2: {self.tracked_imei2}", fg=self.muted_color, bg=self.panel_color, font=("Courier", 9))
        self.target_imei2_label.pack(anchor="w")
        self.target_serial_label = tk.Label(target_info_panel, text=f"SERIAL: {self.tracked_serial}", fg=self.muted_color, bg=self.panel_color, font=("Courier", 9))
        self.target_serial_label.pack(anchor="w")

        # Save Report Button
        tk.Button(right_col, text="💾 SAVE TRACKING REPORT", command=self.save_tracking_data, 
                  bg=self.muted_color, fg="#000", relief="flat", width=25, font=("Arial", 9, "bold")).pack(pady=5)

        tk.Frame(right_col, height=2, bg=self.accent_color).pack(fill="x", pady=15)

        tk.Label(right_col, text="CORE METRICS", fg=self.accent_color, bg=self.panel_color, font=("Arial", 14, "bold")).pack(anchor="w")
        
        # Threat Level Indicator
        tk.Label(right_col, text="THREAT LEVEL:", fg="white", bg=self.panel_color, font=("Arial", 10)).pack(anchor="w", pady=(20,0))
        self.threat_label = tk.Label(right_col, text="HIGH", fg=self.danger_color, bg="#000", font=("Impact", 24), padx=10)
        self.threat_label.pack(fill="x", pady=5)

        # Stats Area
        stats_sub = tk.Frame(right_col, bg=self.panel_color)
        stats_sub.pack(fill="x", pady=10)
        self.lat_label = tk.Label(stats_sub, text="LAT: --", fg=self.accent_color, bg=self.panel_color, font=("Courier", 10))
        self.lat_label.pack(anchor="w")
        self.lon_label = tk.Label(stats_sub, text="LON: --", fg=self.accent_color, bg=self.panel_color, font=("Courier", 10))
        self.lon_label.pack(anchor="w")
        self.ip_label = tk.Label(stats_sub, text="IP: 10.0.0.1", fg=self.accent_color, bg=self.panel_color, font=("Courier", 10))
        self.ip_label.pack(anchor="w")
        
        # Signal Bar
        tk.Label(right_col, text="Signal Strength:", fg=self.muted_color, bg=self.panel_color, font=("Arial", 9)).pack(anchor="w", pady=(10,0))
        self.sig_canvas = tk.Canvas(right_col, width=250, height=25, bg="#000", highlightthickness=0)
        self.sig_canvas.pack(anchor="w", pady=5)
        
        # Device info
        self.battery_label = tk.Label(right_col, text="Battery: 85%", fg=self.accent_color, bg=self.panel_color, font=("Arial", 10))
        self.battery_label.pack(anchor="w", pady=5)
        tk.Label(right_col, text="Encryption: AES-256", fg=self.muted_color, bg=self.panel_color, font=("Arial", 9)).pack(anchor="w")

        tk.Frame(right_col, height=2, bg=self.accent_color).pack(fill="x", pady=15)

        tk.Label(right_col, text="ADMINISTRATION", fg=self.accent_color, bg=self.panel_color, font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(right_col, text="Lead Agent: Danbakarya Tactical", fg=self.muted_color, bg=self.panel_color, font=("Arial", 9)).pack(anchor="w", pady=5)

        tk.Button(right_col, text="COPY TARGET HOTLINE", command=self.copy_contact, bg=self.accent_color, fg="#000", relief="flat", width=25, font=("Arial", 9, "bold")).pack(pady=10)
        tk.Button(right_col, text="TERMINATE CONNECTION", command=lambda: messagebox.showerror("Access Denied", "Only administrators can terminate"), bg=self.danger_color, fg="white", relief="flat", width=25, font=("Arial", 9, "bold")).pack()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def save_tracking_data(self):
        if self.tracked_imei1 == "---":
            messagebox.showwarning("No Data", "Please start tracking first to generate a report.")
            return
        filename = f"tracking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        content = f"DANBAKARYA TACTICAL REPORT\nDate: {datetime.now()}\nIMEI 1: {self.tracked_imei1}\nIMEI 2: {self.tracked_imei2}\nSerial: {self.tracked_serial}\nIP: {self.get_local_ip()}\nStatus: COMPLETED"
        with open(filename, "w") as f:
            f.write(content)
        messagebox.showinfo("Report Saved", f"Tracking report has been saved to: {filename}")

    def start_tracking(self):
        self.tracked_imei1 = self.imei1_entry.get() if self.imei1_entry.get() else "N/A"
        self.tracked_imei2 = self.imei2_entry.get() if self.imei2_entry.get() else "N/A"
        self.tracked_serial = self.serial_entry.get() if self.serial_entry.get() else "N/A"
        self.target_imei1_label.config(text=f"IMEI 1: {self.tracked_imei1}")
        self.target_imei2_label.config(text=f"IMEI 2: {self.tracked_imei2}")
        self.target_serial_label.config(text=f"SERIAL: {self.tracked_serial}")
        messagebox.showinfo("Tracking Initiated", f"Tracking started for Serial: {self.tracked_serial}")

    def generate_blips(self):
        cx, cy = 300, 200 # Center of the radar
        radius_limit = 180 # Max radius for blips to appear within the radar circles
        for _ in range(20): # Increased number of blips for more activity
            # Generate random angle and distance from center
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, radius_limit) # Avoid blips exactly at the center
            
            x = cx + distance * math.cos(angle)
            y = cy - distance * math.sin(angle) # Tkinter y-axis is inverted
            
            self.blips.append({
                "x": x,
                "y": y,
                "opacity": 0,
                "active": False
            })

    def draw_radar(self):
        cx, cy = 300, 200
        self.radar_canvas.delete("all")
        # Background circles
        for r in [50, 100, 150, 190]:
            self.radar_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#003333", width=1)
        self.radar_canvas.create_line(cx-200, cy, cx+200, cy, fill="#003333")
        self.radar_canvas.create_line(cx, cy-200, cx, cy+200, fill="#003333")

    def update_data(self):
        try:
            cx, cy = 300, 200
            # Update Clock
            self.clock_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update Fake Coords
            new_lat = 6.200891 + random.uniform(-0.02, 0.02)
            new_lon = 6.698627 + random.uniform(-0.02, 0.02)
            
            self.lat_label.config(text=f"LAT: {new_lat:.5f}")
            self.lon_label.config(text=f"LON: {new_lon:.5f}")
            self.battery_label.config(text=f"Battery: {random.randint(20, 99)}%")

            # Update Radar Animation
            self.draw_radar()
            self.angle = (self.angle + 4) % 360
            rad = math.radians(self.angle)
            x_end = cx + 190 * math.cos(rad)
            y_end = cy - 190 * math.sin(rad)
            
            # Sweep line with glow
            self.radar_canvas.create_line(cx, cy, x_end, y_end, fill=self.accent_color, width=3)
            
            # Update Blips
            for blip in self.blips:
                blip_angle = (math.degrees(math.atan2(cy - blip['y'], blip['x'] - cx)) + 360) % 360 # Ensure angle is positive
                
                angle_diff = abs(self.angle - blip_angle)
                if angle_diff > 180: # Handle wrap-around for angles (e.g., 355 and 5 degrees are close)
                    angle_diff = 360 - angle_diff

                if angle_diff < 10: # Increased tolerance for detection
                    blip['opacity'] = 255
                
                if blip['opacity'] > 0:
                    color = f"#{blip['opacity']:02x}0000" # Red color for blips
                    self.radar_canvas.create_oval(blip['x']-4, blip['y']-4, blip['x']+4, blip['y']+4, fill=color, outline="")
                    blip['opacity'] -= 15 # Fade out faster
            
            # Update Signal Bar
            self.sig_canvas.delete("all")
            levels = random.randint(3, 10)
            for i in range(levels):
                self.sig_canvas.create_rectangle(i*25, 0, (i*25)+20, 25, fill=self.accent_color, outline="")

            # Update Decryption Stream
            # Limit the number of lines to prevent memory issues and performance degradation
            if int(self.decrypt_area.index('end-1c').split('.')[0]) > 100: # Keep max 100 lines
                self.decrypt_area.delete('1.0', '2.0') # Delete the oldest line
            self.decrypt_area.insert(tk.END, f"{hex(random.getrandbits(32))} {random.randint(0,1)} \n")
            self.decrypt_area.see(tk.END)

            # Randomly change IP
            if random.random() > 0.95:
                new_ip = f"192.168.{random.randint(0,255)}.{random.randint(0,255)}"
                self.ip_label.config(text=f"IP: {new_ip}")

            # Randomly add logs
            if random.random() > 0.7:
                timestamp = datetime.now().strftime("%H:%M:%S")
                if self.tracked_imei1 != "---": # Add tracked device info to logs
                    self.fake_events[-1] = f"TRACKING ACTIVE FOR SERIAL: {self.tracked_serial}"
                    
                event = random.choice(self.fake_events)
                self.log_area.insert(tk.END, f"[{timestamp}] {event}\n")
                self.log_area.see(tk.END)
                
            if random.random() > 0.98:
                self.threat_label.config(text=random.choice(["HIGH", "CRITICAL", "LOCKED"]))
            
            # Randomly add phone database entries
            if random.random() > 0.4:
                phone = random.choice(self.phone_models)
                self.phone_area.insert(tk.END, f"{phone}\n")
                self.phone_area.see(tk.END)
            self.root.after(100, self.update_data) # Faster for radar smoothness
        except Exception as e:
            print(f"An error occurred in update_data: {e}")
            # If an error occurs, you might want to stop the updates or show a message box
            # messagebox.showerror("Error", f"An error occurred: {e}")

    def copy_contact(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("09032948833")
        messagebox.showinfo("Success", "Number copied to clipboard!")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrackingDashboard(root)
    root.mainloop()