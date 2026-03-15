import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import threading
import time
import webbrowser
import json
import os
import socket
import secrets  # Kryptografisch sicheres Fallback
import requests # Für die API-Abfrage
from datetime import datetime

# --- DATEIPFADE ---
SETTINGS_FILE = "lotto_ultimate_backup.json"
HISTORY_FILE = "lotto_historie.txt"

# --- PRESETS ---
LOTTO_PRESETS = {
    "EUROJACKPOT": ["50", "50", "50", "50", "50", "12", "12"],
    "6aus49": ["49", "49", "49", "49", "49", "49", "10"],
    "FREIHEIT+": ["38", "38", "38", "38", "38", "38", "38"],
    "GLÜCKSSPIRALE": ["9", "9", "9", "9", "9", "9", "9"] 
}

# --- SPENDENLISTE ---
SPENDEN_LISTE = [
    ("NABU", "https://www.nabu.de/spenden-und-mitmachen/index.html"),
    ("Frauenhaus Augsburg", "https://www.skf-augsburg.de/hilfe-angebote/frauenhaus-augsburg"),
    ("Karton revolucija", "https://share.google/fnxRsDErubLFdhUnc"),
    ("WWF Meeresschildkröten", "https://www.wwf.de/themen-projekte/bedrohte-tier-und-pflanzenarten/meeresschildkroeten"),
    ("Plan International", "https://www.plan.de/jetzt-spenden.html"),
    ("Zoo Augsburg", "https://www.zoo-augsburg.com/zoo-unterstuetzen/spenden/"),
    ("Deutsche Schulschachstiftung", "https://schulschachstiftung.de/die-dss-e-v-unterstuetzen"),
    ("Greenpeace Regenwald", "https://share.google/ffKJuz3y1MQ8P3M9h"),
    ("Die Arche Moosach", "https://share.google/s4jLsuFRkr2czilV2"),
    ("Johanniter Notfallhilfe", "https://share.google/cVeYQOFRimKihlhie"),
    ("DKMS", "https://www.dkms.de/aktiv-werden"),
    ("Felix Burda Stiftung", "https://share.google/qxCbkGyXvafqPxGOQ"),
    ("Volle Kraft für Inklusion", "https://www.betterplace.org/de/projects/89166"),
    ("Mukoviszidose Hilfe", "https://www.betterplace.org/de/projects/57867"),
    ("Clowns-Visiten auf den Kinderstationen ", "https://www.betterplace.org/de/projects/12366?utm_campaign=user_share&utm_medium=ppp_sticky&utm_source=Link&utm_content=bp"),
]

class UltimateLottoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lotto Master Tool (Quantum Enhanced)")
        self.root.geometry("600x950")
        self.root.configure(bg="#020617")

        self.is_drawing = False
        self.current_preset = tk.StringVar(value="EUROJACKPOT")
        self.mode = tk.StringVar(value="standard") 
        self.config_entries = [] 
        self.list_entries = []   
        
        self.setup_ui()
        self.load_all()

    def is_online(self):
        try:
            socket.setdefaulttimeout(1.5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except: return False

    def get_random_number(self, pool):
        """Holt eine Zahl: Online via ANU Quantum, Offline via Secrets."""
        if not pool: return 0
        
        if self.is_online():
            try:
                # ANU API: Wir fragen nach einer Zahl (uint8 für kleine Bereiche ausreichend)
                response = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint8", timeout=6)
                if response.status_code == 200:
                    quantum_val = response.json()['data'][0]
                    # Map den Quanten-Wert auf die Pool-Größe
                    return pool[quantum_val % len(pool)]
            except:
                pass # Fallback zu secrets bei API-Fehler
        
        # Offline oder API-Fehler: Kryptografisch sicheres secrets-Modul
        return secrets.choice(pool)

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#020617")
        header_frame.pack(fill="x", pady=10)
        tk.Label(header_frame, text="LOTTO MASTER TOOL", fg="#22d3ee", bg="#020617", font=("Arial", 14, "bold")).pack()
        
        # Modus-Umschalter
        mode_frame = tk.Frame(self.root, bg="#020617")
        mode_frame.pack(pady=5)
        tk.Radiobutton(mode_frame, text="Standard", variable=self.mode, value="standard", 
                       bg="#020617", fg="white", selectcolor="#1e293b", command=self.toggle_ui).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Experte", variable=self.mode, value="expert", 
                       bg="#020617", fg="white", selectcolor="#1e293b", command=self.toggle_ui).pack(side="left", padx=10)

        # --- STANDARD UI ---
        self.std_ui_frame = tk.Frame(self.root, bg="#020617")
        self.std_ui_frame.pack(fill="x", padx=6)
        
        preset_frame = tk.Frame(self.std_ui_frame, bg="#020617")
        preset_frame.pack(fill="x", pady=5)
        for name in LOTTO_PRESETS.keys():
            tk.Button(preset_frame, text=name, bg="#1e293b", fg="white", font=("Arial", 7, "bold"), 
                      command=lambda n=name: self.apply_preset(n)).pack(side="left", expand=True, fill="x", padx=2)

        cfg_row = tk.Frame(self.std_ui_frame, bg="#0f172a", pady=5)
        cfg_row.pack(fill="x")
        for i in range(7):
            f = tk.Frame(cfg_row, bg="#1e293b")
            f.pack(side="left", expand=True, padx=2)
            ent = tk.Entry(f, width=3, justify="center", bg="#020617", fg="#22d3ee", bd=0, font=("Arial", 10, "bold"))
            ent.insert(0, "50")
            ent.pack()
            self.config_entries.append(ent)

        # --- EXPERT UI ---
        self.exp_ui_frame = tk.Frame(self.root, bg="#020617")
        for i in range(7):
            row = tk.Frame(self.exp_ui_frame, bg="#0f172a", pady=1)
            row.pack(fill="x")
            tk.Label(row, text=f"L{i+1}:", fg="#94a3b8", bg="#0f172a", width=4).pack(side="left")
            ent = tk.Entry(row, bg="#1e293b", fg="#fbbf24", bd=0, font=("Arial", 10))
            ent.insert(0, "1, 2, 3, 4, 5")
            ent.pack(side="left", expand=True, fill="x", padx=5)
            self.list_entries.append(ent)

        # --- GEMEINSAME ELEMENTE ---
        self.result_frame = tk.Frame(self.root, bg="#020617")
        self.result_frame.pack(pady=26)
        self.ball_labels = []
        for i in range(7):
            lbl = tk.Label(self.result_frame, text="?", width=3, height=1, fg="#64748b", bg="#1e293b", font=("Arial", 16, "bold"))
            lbl.pack(side="left", expand=True, padx=4)
            self.ball_labels.append(lbl)

        self.hist_area = scrolledtext.ScrolledText(self.root, height=8, bg="#0f172a", fg="#38bdf8", font=("Courier", 9), bd=0)
        self.hist_area.pack(fill="x", padx=20, pady=5)

        self.status_box = tk.Label(self.root, text="Bereit!", fg="#94a3b8", bg="#1e293b", height=3, font=("Arial", 9, "italic"))
        self.status_box.pack(fill="x", padx=20, pady=10)

        btn_frame = tk.Frame(self.root, bg="#020617")
        btn_frame.pack(side="bottom", fill="x", pady=20, padx=20)
        self.draw_btn = tk.Button(btn_frame, text="ZIEHUNG STARTEN", bg="#22d3ee", fg="black", font=("Arial", 12, "bold"), height=2, command=self.start_draw)
        self.draw_btn.pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="❤ KARMA", bg="#f43f5e", fg="white", font=("Arial", 12, "bold"), command=self.do_karma).pack(side="right", padx=5)

        self.toggle_ui()

    def toggle_ui(self):
        if self.mode.get() == "standard":
            self.exp_ui_frame.pack_forget()
            self.std_ui_frame.pack(fill="x", padx=15)
        else:
            self.std_ui_frame.pack_forget()
            self.exp_ui_frame.pack(fill="x", padx=15)

    def apply_preset(self, name):
        self.current_preset.set(name)
        vals = LOTTO_PRESETS[name]
        for i in range(7):
            self.config_entries[i].delete(0, tk.END)
            self.config_entries[i].insert(0, vals[i])
        self.status_box.config(text=f"Lotterie: {name}", fg="#22d3ee")

    def do_karma(self):
        org, url = random.choice(SPENDEN_LISTE)
        if self.is_online():
            self.status_box.config(text=f"Karma-Tipp: {org}", fg="#fbbf24")
            webbrowser.open(url)
        else:
            messagebox.showinfo("Offline", f"Karma-Punkt für {org} gemerkt!")

    def start_draw(self):
        if not self.is_drawing:
            self.save_all()
            threading.Thread(target=self.run_draw, daemon=True).start()

    def run_draw(self):
        self.is_drawing = True
        self.draw_btn.config(state="disabled")
        nums = []
        is_serial = self.current_preset.get() == "GLÜCKSSPIRALE" and self.mode.get() == "standard"
        used = set()

        online = self.is_online()
        source_text = "QUANTUM (ANU)" if online else "KRYPTO (Internal)"
        self.status_box.config(text=f"Ziehung läuft via {source_text}...", fg="#38bdf8")

        for i in range(7):
            if self.mode.get() == "standard":
                try: 
                    limit = int(self.config_entries[i].get())
                    start_val = 0 if is_serial else 1
                except: limit = 50; start_val = 1
                pool = list(range(start_val, limit + 1))
            else:
                raw = self.list_entries[i].get()
                pool = [int(x.strip()) for x in raw.replace(";", ",").split(",") if x.strip().isdigit()]
                if not pool: pool = list(range(1, 51))

            available = [n for n in pool if n not in used] if not is_serial else pool
            if not available: available = pool
            
            # Kurze Animation (lokal zufällig für Speed)
            for _ in range(5):
                self.ball_labels[i].config(text=str(random.choice(pool)))
                time.sleep(0.05)
            
            # Die echte Ziehung (Quantum/Secrets)
            res = self.get_random_number(available)
            nums.append(res)
            used.add(res)
            
            color = "#22d3ee" if i < 5 else "#fbbf24"
            self.ball_labels[i].config(text=str(res), bg=color, fg="black")
            time.sleep(0.1)

        with open(HISTORY_FILE, "a") as f:
            f.write(f"{datetime.now().strftime('%H:%M')} [{source_text[:3]}] -> {nums}\n")
        
        self.root.after(0, self.update_history_display)
        self.is_drawing = False
        self.draw_btn.config(state="normal")
        self.status_box.config(text="Ziehung beendet.", fg="#10b981")

    def update_history_display(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                lines = f.readlines()
                self.hist_area.delete(1.0, tk.END)
                self.hist_area.insert(tk.END, "".join(lines[-12:]))
                self.hist_area.see(tk.END)

    def save_all(self):
        data = {
            "mode": self.mode.get(),
            "preset": self.current_preset.get(),
            "configs": [e.get() for e in self.config_entries],
            "lists": [e.get() for e in self.list_entries]
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)

    def load_all(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.mode.set(data.get("mode", "standard"))
                    self.current_preset.set(data.get("preset", "EUROJACKPOT"))
                    for i, v in enumerate(data.get("configs", [])): 
                        self.config_entries[i].delete(0, tk.END)
                        self.config_entries[i].insert(0, v)
                    for i, v in enumerate(data.get("lists", [])): 
                        self.list_entries[i].delete(0, tk.END)
                        self.list_entries[i].insert(0, v)
            except: pass
        self.update_history_display()
        self.toggle_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateLottoApp(root)
    root.mainloop()
