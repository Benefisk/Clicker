import json
import sys
import tkinter as tk
from pathlib import Path


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
SAVE_FILE = APP_DIR / "clicker_save.json"


class ClickerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Монетный кликер")
        self.root.geometry("520x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#101827")

        self.coins = 0
        self.per_click = 1
        self.upgrade_cost = 10
        self.skins = {
            "classic": {"name": "Классика", "price": 0, "outer": "#8b4d14", "main": "#f6ba3c", "rim": "#da8c1e", "symbol": "#fff0b3", "mark": "$"},
            "emerald": {"name": "Изумруд", "price": 100, "outer": "#14634f", "main": "#35c99a", "rim": "#168565", "symbol": "#d7fff1", "mark": "◆"},
            "ruby": {"name": "Рубин", "price": 300, "outer": "#751f3b", "main": "#ed5276", "rim": "#b82b50", "symbol": "#ffe0e8", "mark": "♥"},
            "ocean": {"name": "Океан", "price": 750, "outer": "#174c82", "main": "#45b8ee", "rim": "#247ead", "symbol": "#e0f8ff", "mark": "✦"},
        }
        self.owned_skins = {"classic"}
        self.active_skin = "classic"
        self.load_game()

        self.canvas = tk.Canvas(root, width=520, height=650, bg="#101827", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_oval(-100, -150, 250, 190, fill="#17283c", outline="")
        self.canvas.create_oval(360, 430, 660, 730, fill="#17283c", outline="")
        self.canvas.create_text(260, 48, text="CLICKER CLUB", fill="#f4c95d",
                                font=("Segoe UI", 13, "bold"))
        self.canvas.create_text(260, 82, text="Собирай монеты", fill="white",
                                font=("Segoe UI", 24, "bold"))
        self.canvas.create_text(260, 111, text="Каждый клик приближает к богатству", fill="#91a2ba",
                                font=("Segoe UI", 10))
        self.canvas.create_rectangle(42, 145, 478, 222, fill="#1b293b", outline="#2a3a50", width=2)
        self.canvas.create_text(260, 164, text="ТВОЙ БАЛАНС", fill="#91a2ba",
                                font=("Segoe UI", 9, "bold"))
        self.coins_label = self.canvas.create_text(260, 194, text="", fill="white",
                                                    font=("Segoe UI", 23, "bold"))
        self.coin_animation_job = None
        self.particle_jobs = {}
        self.create_coin_parts()
        self.settings_button = tk.Button(root, text="⚙", command=self.open_settings,
            font=("Segoe UI Symbol", 15, "bold"), bg="#293b53", fg="white",
            activebackground="#3b5371", relief="flat", cursor="hand2", width=3, pady=3, bd=0)
        self.canvas.create_window(90, 48, window=self.settings_button)
        self.shop_button = tk.Button(root, text="🛍  СКИНЫ", command=self.open_shop,
            font=("Segoe UI", 9, "bold"), bg="#293b53", fg="white",
            activebackground="#3b5371", relief="flat", cursor="hand2", padx=12, pady=6, bd=0)
        self.canvas.create_window(430, 48, window=self.shop_button)
        self.canvas.create_text(260, 499, text="НАЖМИ НА МОНЕТУ", fill="#dce5f2",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_rectangle(42, 526, 478, 620, fill="#1b293b", outline="#2a3a50", width=2)
        self.canvas.create_text(66, 550, text="⚡", fill="#f4c95d", font=("Segoe UI", 18))
        self.canvas.create_text(104, 548, anchor="w", text="СИЛА КЛИКА", fill="white",
                                font=("Segoe UI", 11, "bold"))
        self.click_power_label = self.canvas.create_text(
            104, 574, anchor="w", text="", fill="#91a2ba", font=("Segoe UI", 9))
        self.upgrade_button = tk.Button(root, command=self.upgrade, font=("Segoe UI", 10, "bold"),
            bg="#f4bd45", fg="#182235", activebackground="#ffda70", disabledforeground="#777777",
            relief="flat", cursor="hand2", padx=14, pady=8, bd=0)
        self.canvas.create_window(370, 574, window=self.upgrade_button)
        self.apply_skin()
        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def open_settings(self):
        if getattr(self, "settings_open", False):
            self.close_settings()
            return
        if getattr(self, "shop_open", False):
            self.close_shop()
        self.settings_open = True
        self.settings_panel = tk.Frame(self.root, bg="#101827",
                                       highlightbackground="#40536d", highlightthickness=2)
        self.settings_panel.place(x=42, y=145, width=436, height=475)
        tk.Label(self.settings_panel, text="НАСТРОЙКИ", font=("Segoe UI", 20, "bold"),
                 fg="#f4c95d", bg="#101827").pack(pady=(34, 8))
        tk.Label(self.settings_panel, text="Управление прогрессом игры", font=("Segoe UI", 10),
                 fg="#b9c8dc", bg="#101827").pack(pady=(0, 28))
        tk.Button(self.settings_panel, text="Сбросить прогресс", command=self.reset_progress,
                  font=("Segoe UI", 11, "bold"), bg="#a93e4b", fg="white",
                  activebackground="#c7505c", relief="flat", cursor="hand2",
                  padx=18, pady=10, bd=0).pack(pady=8)
        tk.Button(self.settings_panel, text="←  НАЗАД К ИГРЕ", command=self.close_settings,
                  font=("Segoe UI", 10, "bold"), bg="#293b53", fg="white",
                  activebackground="#3b5371", relief="flat", cursor="hand2",
                  padx=16, pady=8, bd=0).pack(pady=20)

    def close_settings(self):
        panel = getattr(self, "settings_panel", None)
        self.settings_open = False
        if panel is not None:
            try:
                if panel.winfo_exists():
                    panel.place_forget()
                    panel.destroy()
            except tk.TclError:
                pass
        self.settings_panel = None

    def reset_progress(self):
        if getattr(self, "reset_confirm_panel", None) is not None:
            try:
                if self.reset_confirm_panel.winfo_exists():
                    return
            except tk.TclError:
                pass
        self.reset_confirm_panel = tk.Frame(
            self.settings_panel, bg="#1b293b", highlightbackground="#40536d",
            highlightthickness=2)
        self.reset_confirm_panel.place(x=28, y=112, width=376, height=205)
        tk.Label(self.reset_confirm_panel, text="Сбросить прогресс?",
                 font=("Segoe UI", 15, "bold"), fg="#f4c95d",
                 bg="#1b293b").pack(pady=(24, 10))
        tk.Label(self.reset_confirm_panel,
                 text="Монеты, улучшения и купленные скины. Будут удалены.",
                 font=("Segoe UI", 10), fg="#d2dced", bg="#1b293b",
                 justify="center").pack(pady=(0, 16))
        buttons = tk.Frame(self.reset_confirm_panel, bg="#1b293b")
        buttons.pack()
        tk.Button(buttons, text="Сбросить", command=self.confirm_reset,
                  font=("Segoe UI", 10, "bold"), bg="#a93e4b", fg="white",
                  activebackground="#c7505c", relief="flat", cursor="hand2",
                  padx=15, pady=8, bd=0).pack(side="left", padx=6)
        tk.Button(buttons, text="Отмена", command=self.cancel_reset,
                  font=("Segoe UI", 10, "bold"), bg="#293b53", fg="white",
                  activebackground="#3b5371", relief="flat", cursor="hand2",
                  padx=15, pady=8, bd=0).pack(side="left", padx=6)

    def cancel_reset(self):
        panel = getattr(self, "reset_confirm_panel", None)
        if panel is not None:
            panel.destroy()
        self.reset_confirm_panel = None

    def confirm_reset(self):
        self.cancel_reset()
        self.coins = 0
        self.per_click = 1
        self.upgrade_cost = 10
        self.owned_skins = {"classic"}
        self.active_skin = "classic"
        self.apply_skin()
        self.refresh()
        self.save_safely()

    def create_coin_parts(self):
        # Remove the previous visual layers before rebuilding after the shop closes.
        for old_part in getattr(self, "coin_parts", []):
            self.canvas.delete(old_part)
        self.coin_parts = [
            self.canvas.create_oval(145, 244, 375, 474, fill="#8b4d14", outline="#f4a62a", width=5),
            self.canvas.create_oval(158, 257, 362, 461, fill="#f6ba3c", outline="#ffdb77", width=4),
            self.canvas.create_oval(175, 274, 345, 444, outline="#da8c1e", width=3),
            self.canvas.create_text(260, 348, text="$", fill="#fff0b3", font=("Segoe UI", 82, "bold")),
        ]
        self.coin_base_coords = {part: self.canvas.coords(part) for part in self.coin_parts}
        for part in self.coin_parts:
            self.canvas.tag_bind(part, "<Button-1>", self.on_coin_click)
        self.apply_skin()

    def on_coin_click(self, event=None):
        self.coins += self.per_click
        self.refresh()
        self.save_safely()
        if self.coin_animation_job is not None:
            try:
                self.root.after_cancel(self.coin_animation_job)
            except tk.TclError:
                pass
        self.animate_coin(0)
        return "break"

    def animate_coin(self, frame):
        # Absolute coordinates prevent scale drift after repeated clicks or shop visits.
        scales = (0.90, 0.86, 0.90, 0.94, 0.98, 1.0)
        scale = scales[min(frame, len(scales) - 1)]
        symbol = self.coin_parts[3]
        for part, base in self.coin_base_coords.items():
            if part == symbol:
                self.canvas.coords(part, *base)
                self.canvas.itemconfigure(
                    part, font=("Segoe UI", max(12, round(82 * scale)), "bold"))
                continue
            coords = []
            for index, value in enumerate(base):
                center = 260 if index % 2 == 0 else 359
                coords.append(center + (value - center) * scale)
            self.canvas.coords(part, *coords)
        if frame == 0:
            self.spawn_particles()
        if frame < len(scales) - 1:
            self.coin_animation_job = self.root.after(70, lambda: self.animate_coin(frame + 1))
        else:
            self.coin_animation_job = None

    def spawn_particles(self):
        import math
        for i in range(16):
            angle = 2 * math.pi * i / 16 - math.pi / 2
            x, y = 260 + math.cos(angle) * 88, 359 + math.sin(angle) * 88
            particle = self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                                               fill="white", outline="")
            self.animate_particle(particle, math.cos(angle), math.sin(angle), 0)

    def animate_particle(self, particle, dx, dy, frame):
        if frame >= 12:
            self.canvas.delete(particle)
            self.particle_jobs.pop(particle, None)
            return
        self.canvas.move(particle, dx * 8, dy * 8)
        coords = self.canvas.coords(particle)
        if coords:
            self.canvas.scale(particle, (coords[0] + coords[2]) / 2,
                              (coords[1] + coords[3]) / 2, 0.88, 0.88)
        self.particle_jobs[particle] = self.root.after(
            22, lambda: self.animate_particle(particle, dx, dy, frame + 1))

    def stop_click_effects(self):
        if self.coin_animation_job is not None:
            try:
                self.root.after_cancel(self.coin_animation_job)
            except tk.TclError:
                pass
            self.coin_animation_job = None
        for job in self.particle_jobs.values():
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        for particle in list(self.particle_jobs):
            self.canvas.delete(particle)
        self.particle_jobs.clear()
        for part, coords in self.coin_base_coords.items():
            self.canvas.coords(part, *coords)
        if len(self.coin_parts) >= 4:
            self.canvas.itemconfigure(self.coin_parts[3], font=("Segoe UI", 82, "bold"))

    def apply_skin(self):
        skin = self.skins[self.active_skin]
        self.canvas.itemconfig(self.coin_parts[0], fill=skin["outer"])
        self.canvas.itemconfig(self.coin_parts[1], fill=skin["main"])
        self.canvas.itemconfig(self.coin_parts[2], outline=skin["rim"])
        self.canvas.itemconfig(self.coin_parts[3], fill=skin["symbol"], text=skin["mark"])

    def open_shop(self):
        if getattr(self, "shop_open", False):
            self.close_shop()
            return
        if getattr(self, "settings_open", False):
            self.close_settings()
        self.stop_click_effects()
        self.shop_open = True
        # The panel is rebuilt each time it opens, so its rows and previews are too.
        self.shop_entries = {}
        self.shop_previews = []
        self.preview_jobs = {}
        self.shop_panel = tk.Frame(self.root, bg="#101827", highlightbackground="#40536d",
                                   highlightthickness=2)
        self.shop_panel.place(x=42, y=145, width=436, height=475)
        tk.Label(self.shop_panel, text="МАГАЗИН СКИНОВ", font=("Segoe UI", 18, "bold"),
                 fg="#f4c95d", bg="#101827").pack(pady=(18, 4))
        self.shop_balance = tk.Label(self.shop_panel, text="", font=("Segoe UI", 10),
                                     fg="#b9c8dc", bg="#101827")
        self.shop_balance.pack(pady=(0, 10))
        self.shop_rows = tk.Frame(self.shop_panel, bg="#101827")
        self.shop_rows.pack(fill="x", padx=22)
        tk.Button(self.shop_panel, text="←  НАЗАД К ИГРЕ", command=self.close_shop,
                  font=("Segoe UI", 10, "bold"), bg="#293b53", fg="white",
                  activebackground="#3b5371", relief="flat", cursor="hand2",
                  padx=16, pady=8, bd=0).pack(pady=16)
        self.refresh_shop()

    def refresh_shop(self):
        panel = getattr(self, "shop_panel", None)
        if panel is None:
            return
        try:
            if not panel.winfo_exists():
                return
        except tk.TclError:
            return
        self.shop_balance.config(text=f"Баланс: {self.coins} монет")
        if not self.shop_entries:
            self.shop_entries = {}
            self.shop_previews = []
            for key, skin in self.skins.items():
                row = tk.Frame(self.shop_rows, bg="#1b293b", height=66)
                row.pack(fill="x", pady=4)
                row.pack_propagate(False)
                preview = tk.Canvas(row, width=58, height=58, bg="#1b293b", highlightthickness=0)
                preview.pack(side="left", padx=(5, 8), pady=4)
                shadow = preview.create_oval(9, 11, 53, 55, fill="#0c1420", outline="")
                edge = preview.create_oval(6, 6, 50, 50, fill=skin["outer"], outline=skin["rim"], width=2)
                face = preview.create_oval(8, 8, 48, 48, fill=skin["main"], outline=skin["symbol"], width=2)
                inner = preview.create_oval(12, 12, 44, 44, outline=skin["rim"], width=1)
                highlight = preview.create_arc(11, 11, 43, 43, start=65, extent=105,
                                              style="arc", outline=skin["symbol"], width=2)
                mark = preview.create_text(28, 28, text=skin["mark"], fill=skin["symbol"],
                                          font=("Segoe UI", 15, "bold"))
                preview_items = (preview, shadow, edge, face, inner, highlight, mark, skin)
                button = tk.Button(row, command=lambda k=key: self.buy_or_select_skin(k),
                    font=("Segoe UI", 9, "bold"), bg="#24364d", fg="white",
                    disabledforeground="#78869a", activebackground="#385474",
                    relief="flat", cursor="hand2", width=31, pady=8)
                button.pack(side="left", padx=(0, 5), fill="x", expand=True)
                self.shop_entries[key] = (button, preview_items)
                self.shop_previews.append(preview_items)
                self.spin_preview(preview_items, 0)

        for key, (button, _preview) in self.shop_entries.items():
            skin = self.skins[key]
            if key in self.owned_skins:
                button.config(text=skin["name"],
                              state="disabled" if key == self.active_skin else "normal")
            else:
                button.config(text=f"Купить: {skin['name']}  ·  {skin['price']} 🪙",
                              state="normal" if self.coins >= skin["price"] else "disabled")

    def spin_preview(self, items, frame):
        preview, shadow, edge, face, inner, highlight, mark, skin = items
        try:
            if not preview.winfo_exists():
                return
        except tk.TclError:
            return

        # A perspective turn: the face narrows to its edge, flips, then opens again.
        import math
        angle = (frame % 48) * (2 * math.pi / 48)
        width = max(0.08, abs(math.cos(angle)))
        back_side = math.cos(angle) < 0
        cx, cy = 29, 28
        preview.coords(shadow, cx - 22 * width + 2, cy - 18 + 3,
                       cx + 22 * width + 2, cy + 18 + 3)
        preview.coords(edge, cx - 22 * width, cy - 18,
                       cx + 22 * width, cy + 18)
        preview.coords(face, cx - 20 * width, cy - 17,
                       cx + 20 * width, cy + 17)
        preview.coords(inner, cx - 16 * width, cy - 13,
                       cx + 16 * width, cy + 13)
        preview.coords(highlight, cx - 16 * width, cy - 13,
                       cx + 16 * width, cy + 13)
        preview.coords(mark, cx, cy)
        if back_side:
            preview.itemconfigure(face, fill=skin["outer"])
            preview.itemconfigure(mark, text="✦", fill=skin["symbol"])
        else:
            preview.itemconfigure(face, fill=skin["main"])
            preview.itemconfigure(mark, text=skin["mark"], fill=skin["symbol"])
        preview.itemconfigure(mark, font=("Segoe UI", max(5, int(15 * width)), "bold"))
        try:
            self.preview_jobs[preview] = preview.after(
                35, lambda: self.spin_preview(items, frame + 1))
        except tk.TclError:
            return

    def close_shop(self):
        # Stop every preview callback, then hide the complete panel in one UI update.
        for job in getattr(self, "preview_jobs", {}).values():
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        self.preview_jobs = {}
        panel = getattr(self, "shop_panel", None)
        self.shop_open = False
        self.stop_click_effects()
        for part in self.coin_parts:
            self.canvas.tag_bind(part, "<Button-1>", self.on_coin_click)
        if panel is not None:
            try:
                if panel.winfo_exists():
                    panel.place_forget()
                    panel.destroy()
            except tk.TclError:
                pass
        self.shop_panel = None
        self.create_coin_parts()

    def buy_or_select_skin(self, key):
        skin = self.skins[key]
        if key not in self.owned_skins:
            if self.coins < skin["price"]:
                return
            self.coins -= skin["price"]
            self.owned_skins.add(key)
        self.active_skin = key
        self.apply_skin()
        self.refresh()
        self.save_safely()

    def upgrade(self):
        if self.coins >= self.upgrade_cost:
            self.coins -= self.upgrade_cost
            self.per_click += 1
            self.upgrade_cost = int(self.upgrade_cost * 1.7) + 1
            self.refresh()
            self.save_safely()

    def refresh(self):
        self.canvas.itemconfig(self.coins_label, text=f"🪙  {self.coins:,}".replace(",", " "))
        self.canvas.itemconfig(
            self.click_power_label, text=f"Сейчас за клик: {self.per_click} монет")
        self.upgrade_button.config(
            text=f"+1  ·  {self.upgrade_cost} 🪙",
            state="normal" if self.coins >= self.upgrade_cost else "disabled")
        self.refresh_shop()

    def load_game(self):
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            self.coins = max(0, int(data.get("coins", 0)))
            self.per_click = max(1, int(data.get("per_click", 1)))
            self.upgrade_cost = max(10, int(data.get("upgrade_cost", 10)))
            self.owned_skins.update(k for k in data.get("owned_skins", []) if k in self.skins)
            active = data.get("active_skin", "classic")
            self.active_skin = active if active in self.owned_skins else "classic"
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save_game(self):
        data = {"coins": self.coins, "per_click": self.per_click,
                "upgrade_cost": self.upgrade_cost,
                "owned_skins": sorted(self.owned_skins), "active_skin": self.active_skin}
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_safely(self):
        try:
            self.save_game()
        except OSError:
            pass

    def close(self):
        self.save_safely()
        for job in getattr(self, "preview_jobs", {}).values():
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    window = tk.Tk()
    ClickerGame(window)
    window.mainloop()





