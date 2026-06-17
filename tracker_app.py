import tkinter as tk
from tkinter import scrolledtext, messagebox
import random
import os
import math
import socket
import json
import winsound  # Standard library for beeps on Windows
from datetime import datetime

class TrackingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("ULTRA-TRACKER V4.0 — TACTICAL")
        self.root.geometry("1200x900")
        self.root.configure(bg="#020406")
        
        # Define radar canvas dimensions and center
        self.radar_canvas_width = 600
        self.radar_canvas_height = 400
        self.radar_center_x = self.radar_canvas_width / 2
        self.radar_center_y = self.radar_canvas_height / 2
        self.angle = 0  # For radar animation
        self.blips = [] # To store radar target points (x, y, opacity)
        self.target_pos = {"x": 300, "y": 200} # Initial target position
        self.asaba_landmarks = [
            ("NNEBISI ROAD", 250, 220), ("SUMMIT JUNCTION", 320, 150), 
            ("GOVERNMENT HOUSE", 380, 120), ("OKPANAM ROAD", 200, 100), 
            ("SHOPRITE ASABA", 350, 250), ("DELTA STATE SECRETARIAT", 400, 180),
            ("DENNIS OSADEBAY UNI", 450, 300), ("CABLE POINT", 500, 350), 
            ("INTERIOR LANDS", 150, 280), ("ASABA AIRPORT", 80, 120),
            ("LANDMARK HOTEL", 280, 180), ("RIVER NIGER BRIDGE", 550, 280)
        ]
        self.asaba_buildings = [
            (260, 230, 8), (275, 215, 7), (250, 200, 6), # Near Nnebisi Road
            (330, 160, 9), (315, 145, 8), (340, 130, 7), # Near Summit Junction
            (390, 130, 10), (375, 115, 9), (400, 100, 8), # Near Government House
            (410, 190, 7), (425, 175, 6), (400, 205, 8), # Near Delta State Secretariat
            (180, 270, 7), (165, 290, 6), # Interior Lands
            (90, 110, 10), (70, 130, 9) # Near Airport
        ]
        self.red_zones = [
            ("NIGER BRIDGE BORDER", 550, 280, 45),
            ("SUMMIT DANGER ZONE", 320, 150, 35),
            ("AIRPORT RESTRICTED", 80, 120, 50)
        ]
        
        # Map Transformation States (For Auto Rotation, Zoom, and Movement)
        self.map_rotation = 0
        self.map_scale = 1.0
        self.map_offset_x = 0
        self.map_offset_y = 0
        self.target_scale = 1.0
        self.rot_speed = 0.3
        self.history = [] # To store tracking session history

        self.satellite_mode = False
        self.pulse_size = 0 # For live GPS pulse effect
        
        self.river_data = [520, 0, 540, 100, 560, 250, 580, 400]
        self.road_nnebisi = [0, 220, 550, 280]
        self.road_summit = [320, 0, 320, 400]

        self.scan_x = 0 # Horizontal scanning line
        self.scan_dir = 5

        # Styles & Colors
        self.accent_color = "#00ffcc"
        self.muted_color = "#99ffee"
        self.danger_color = "#ff3b30"
        self.panel_color = "#071011"
        self.bg_color = "#020406"

        # Tracked Device Info
        self.tracked_imei1 = "---"
        self.tracked_imei2 = "---"
        self.tracked_serial = "---"

        # Data initialization
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

        self.generate_blips()
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
        radar_panel = tk.LabelFrame(left_col, text="🌍 LIVE LOCATION", fg=self.accent_color, bg=self.panel_color, font=("Arial", 12, "bold"))
        radar_panel.pack(fill="both", expand=True, padx=5, pady=5)

        self.sat_btn = tk.Button(radar_panel, text="📡 SATELLITE VIEW", command=self.toggle_satellite_view, 
                                 bg=self.bg_color, fg=self.accent_color, relief="flat", font=("Arial", 8, "bold"))
        self.sat_btn.place(relx=1.0, x=-10, y=10, anchor="ne")

        # Set background to panel_color for transparency effect
        self.radar_canvas = tk.Canvas(radar_panel, width=self.radar_canvas_width, height=self.radar_canvas_height, bg=self.panel_color, highlightthickness=0)
        self.radar_canvas.pack(pady=(35, 0))

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

        # History Quick-View
        self.history_panel = tk.LabelFrame(right_col, text="RECENT LOGS", fg=self.accent_color, bg=self.panel_color, font=("Arial", 9))
        self.history_panel.pack(fill="x", pady=5)

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
        
        # Add to local history and play sound
        self.history.append(f"{datetime.now().strftime('%H:%M')} - {self.tracked_serial}")
        if len(self.history) > 3: self.history.pop(0)
        
        # Update history UI
        for widget in self.history_panel.winfo_children(): widget.destroy()
        for entry in self.history:
            tk.Label(self.history_panel, text=entry, fg=self.muted_color, bg=self.panel_color, font=("Arial", 8)).pack(anchor="w")

        winsound.Beep(1000, 200) # Frequency 1000Hz, duration 200ms
        messagebox.showinfo("Tracking Initiated", f"Tracking started for Serial: {self.tracked_serial}")

    def toggle_satellite_view(self):
        self.satellite_mode = not self.satellite_mode
        if self.satellite_mode:
            self.sat_btn.config(text="🛰 TACTICAL VIEW", bg=self.accent_color, fg="#000")
        else:
            self.sat_btn.config(text="📡 SATELLITE VIEW", bg=self.bg_color, fg=self.accent_color)

    def generate_blips(self):
        cx, cy = self.radar_center_x, self.radar_center_y # Center of the radar
        radius_limit = 180 # Max radius for blips to appear within the radar circles (relative to center)
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

    def transform_point(self, x, y):
        """Applies scale, rotation, and offset to a coordinate point."""
        cx, cy = self.radar_center_x, self.radar_center_y
        # Shift, Scale and Offset
        nx = (x - cx + self.map_offset_x) * self.map_scale
        ny = (y - cy + self.map_offset_y) * self.map_scale
        # Rotate point around center
        rad = math.radians(self.map_rotation)
        rx = nx * math.cos(rad) - ny * math.sin(rad)
        ry = nx * math.sin(rad) + ny * math.cos(rad)
        return rx + cx, ry + cy

    def transform_list(self, coords):
        """Transforms a flat list of [x1, y1, x2, y2...] coordinates."""
        res = []
        for i in range(0, len(coords), 2):
            tx, ty = self.transform_point(coords[i], coords[i+1])
            res.extend([tx, ty])
        return res

    def draw_radar(self):
        cx, cy = self.radar_center_x, self.radar_center_y

        # Set dynamic colors based on Satellite mode
        if self.satellite_mode:
            bg_fill = "#0b1a0e" # Dark forest green/earth
            river_fill = "#1e3f66" # Deep water blue
            road_fill = "#444444" # Asphalt grey
            grid_fill = "#152515" # Very subtle earth grid
            land_text = "#ffffff" # White text for better contrast
            building_fill_color = "#666666" # Grey/brown for satellite buildings
            building_outline_color = "#888888"
        else:
            bg_fill = self.panel_color
            river_fill = self.muted_color
            road_fill = self.muted_color
            grid_fill = "#001a1a"
            land_text = self.muted_color
            building_fill_color = "#333333" # Dark grey for tactical buildings
            building_outline_color = "#555555"

        self.radar_canvas.config(bg=bg_fill)
        self.radar_canvas.delete("all")
        
        # Draw Grid Lines (Rotating with Map)
        grid_step = 60
        for i in range(-600, 1200, grid_step):
            p1 = self.transform_point(i, -600); p2 = self.transform_point(i, 1000)
            self.radar_canvas.create_line(p1, p2, fill=grid_fill, width=1)
            p3 = self.transform_point(-600, i); p4 = self.transform_point(1200, i)
            self.radar_canvas.create_line(p3, p4, fill=grid_fill, width=1)

        # Draw River Niger (Stylized and Transformed)
        self.radar_canvas.create_line(self.transform_list(self.river_data), fill=river_fill, width=25 * self.map_scale, smooth=True)
        rx, ry = self.transform_point(540, 50)
        self.radar_canvas.create_text(rx, ry, text="RIVER NIGER", fill=self.accent_color, font=("Arial", int(8 * self.map_scale), "italic"))

        # Draw Major Roads (Transformed)
        self.radar_canvas.create_line(self.transform_list(self.road_nnebisi), fill=road_fill, width=3) 
        self.radar_canvas.create_line(self.transform_list(self.road_summit), fill=road_fill, width=3) 

        # Draw Buildings (only when zoomed in)
        if self.map_scale > 1.2: # Threshold for showing buildings
            for x, y, size in self.asaba_buildings:
                tx, ty = self.transform_point(x, y)
                scaled_size = size * self.map_scale
                self.radar_canvas.create_rectangle(tx - scaled_size/2, ty - scaled_size/2,
                                                   tx + scaled_size/2, ty + scaled_size/2,
                                                   fill=building_fill_color, outline=building_outline_color, width=1)

        # Draw Red Zones (Danger Areas)
        for name, x, y, radius in self.red_zones:
            tx, ty = self.transform_point(x, y)
            tr = radius * self.map_scale
            # Draw dashed danger perimeter
            self.radar_canvas.create_oval(tx-tr, ty-tr, tx+tr, ty+tr, outline=self.danger_color, width=2, dash=(4, 4))
            self.radar_canvas.create_text(tx, ty+tr+10, text=name, fill=self.danger_color, font=("Courier", 8, "bold"))

        # Draw Pulsing GPS Signal at Target Position
        tx, ty = self.transform_point(self.target_pos["x"], self.target_pos["y"])
        pulse_color = self.accent_color
        # Outer fading pulse
        self.radar_canvas.create_oval(tx-self.pulse_size, ty-self.pulse_size, tx+self.pulse_size, ty+self.pulse_size, outline=pulse_color, width=1)
        # Static center point
        self.radar_canvas.create_oval(tx-3, ty-3, tx+3, ty+3, fill=self.danger_color, outline="")

        # Draw Asaba Landmarks (Moving with map)
        for name, x, y in self.asaba_landmarks:
            tx, ty = self.transform_point(x, y)
            self.radar_canvas.create_rectangle(tx-2, ty-2, tx+2, ty+2, fill=self.accent_color, outline="")
            self.radar_canvas.create_text(tx+5, ty, text=name, fill=land_text, font=("Courier", 7, "bold"), anchor="w") # Always show landmark names

    def update_data(self):
        try:
            if not self.root.winfo_exists():
                return
            cx, cy = self.radar_center_x, self.radar_center_y
            # Update Clock
            self.clock_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Randomize Map Transformation for "Search" effect
            if random.random() > 0.96:
                self.target_scale = random.uniform(0.8, 1.3)
                self.rot_speed = random.choice([-0.4, -0.2, 0.2, 0.4])
                self.map_offset_x = max(-80, min(80, self.map_offset_x + random.randint(-15, 15)))
                self.map_offset_y = max(-80, min(80, self.map_offset_y + random.randint(-15, 15)))

            # Smooth interpolation
            self.pulse_size = (self.pulse_size + 2) % 40 # Animate GPS pulse
            self.map_scale += (self.target_scale - self.map_scale) * 0.05
            self.map_rotation += self.rot_speed

            # Update Fake Coords
            new_lat = 6.200891 + random.uniform(-0.02, 0.02)
            new_lon = 6.698627 + random.uniform(-0.02, 0.02)
            
            self.lat_label.config(text=f"LAT: {new_lat:.5f}")
            self.lon_label.config(text=f"LON: {new_lon:.5f}")
            self.battery_label.config(text=f"Battery: {random.randint(20, 99)}%")

            # Update Target Movement (Searching effect)
            if random.random() > 0.8:
                self.target_pos["x"] += random.randint(-15, 15)
                self.target_pos["y"] += random.randint(-15, 15)
                # Keep within bounds
                self.target_pos["x"] = max(50, min(550, self.target_pos["x"]))
                self.target_pos["y"] = max(50, min(350, self.target_pos["y"]))

            # Update Radar Animation
            self.draw_radar()
            
            # Target Crosshair (The "Searching" Box)
            # Map the tracking crosshair to the moving map
            tx, ty = self.transform_point(self.target_pos["x"], self.target_pos["y"])
            self.radar_canvas.create_rectangle(tx-15, ty-15, tx+15, ty+15, outline=self.danger_color, width=1)
            self.radar_canvas.create_line(tx-20, ty, tx+20, ty, fill=self.accent_color)
            self.radar_canvas.create_line(tx, ty-20, tx, ty+20, fill=self.accent_color)
            
            tracking_text = f"LOCKING...\nLAT: {new_lat:.4f}\nLON: {new_lon:.4f}"
            self.radar_canvas.create_text(tx+25, ty-25, text=tracking_text, fill=self.accent_color, font=("Courier", 8, "bold"), anchor="nw")
            
            # Removed radar sweep and blips to focus purely on the map rotation
            
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
                if int(self.log_area.index('end-1c').split('.')[0]) > 50:
                    self.log_area.delete('1.0', '2.0')
                timestamp = datetime.now().strftime("%H:%M:%S")
                if self.tracked_imei1 != "---": # Add tracked device info to logs
                    current_event = f"TRACKING ACTIVE FOR SERIAL: {self.tracked_serial}"
                else:
                    current_event = random.choice(self.fake_events)
                self.log_area.insert(tk.END, f"[{timestamp}] {current_event}\n")
                self.log_area.see(tk.END)
                
                if random.random() > 0.9: # Occasional beep for log activity
                    winsound.Beep(500, 50)

            if random.random() > 0.98:
                self.threat_label.config(text=random.choice(["HIGH", "CRITICAL", "LOCKED"]))
            
            # Randomly add phone database entries
            if random.random() > 0.4:
                if int(self.phone_area.index('end-1c').split('.')[0]) > 20:
                    self.phone_area.delete('1.0', '2.0')
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