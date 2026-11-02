import json
import math
import os
import sys
import time
from pathlib import Path

import pygame


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
SAVE_FILE = APP_DIR / "clicker_save.json"
WIDTH, HEIGHT = 520, 650
BG = (16, 24, 39)
PANEL = (27, 41, 59)
PANEL_LIGHT = (36, 54, 77)
TEXT_MUTED = (145, 162, 186)
GOLD = (244, 201, 93)
WHITE = (246, 248, 252)


class ClickerGame:
    def __init__(self):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption("Clicker Club")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
        pygame.display.set_icon(pygame.image.load(str(RESOURCE_DIR / "icon.png")))
        self.clock = pygame.time.Clock()
        self.fonts = {}
        self.coins = 0
        self.per_click = 1
        self.upgrade_cost = 10
        self.skins = {
            "classic": {"name": "Классика", "price": 0, "outer": (139, 77, 20), "main": (246, 186, 60), "rim": (218, 140, 30), "symbol": (255, 240, 179), "mark": "$"},
            "emerald": {"name": "Изумруд", "price": 100, "outer": (20, 99, 79), "main": (53, 201, 154), "rim": (22, 133, 101), "symbol": (215, 255, 241), "mark": "diamond"},
            "ruby": {"name": "Рубин", "price": 300, "outer": (117, 31, 59), "main": (237, 82, 118), "rim": (184, 43, 80), "symbol": (255, 224, 232), "mark": "heart"},
            "ocean": {"name": "Океан", "price": 750, "outer": (23, 76, 130), "main": (69, 184, 238), "rim": (36, 126, 173), "symbol": (224, 248, 255), "mark": "star"},
        }
        self.owned_skins = {"classic"}
        self.active_skin = "classic"
        self.page = "game"
        self.confirm_reset_open = False
        self.coin_animation_started = None
        self.particles = []
        self.preview_angle = 0.0
        self.buttons = {}
        self.load_game()
        self.running = True
        self.drag_api = None
        if sys.platform == "win32":
            try:
                import ctypes
                self.drag_api = ctypes
            except Exception:
                self.drag_api = None

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
        return self.fonts[key]

    def draw_text(self, text, x, y, size, color=WHITE, bold=False, center=True):
        image = self.font(size, bold).render(str(text), True, color)
        rect = image.get_rect()
        if center:
            rect.center = (round(x), round(y))
        else:
            rect.topleft = (round(x), round(y))
        self.screen.blit(image, rect)
        return rect

    def rounded_rect(self, rect, color, radius=8, border=None, border_width=1):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, rect, border_width, border_radius=radius)

    def add_button(self, key, rect, label, action, *, fill=PANEL_LIGHT, color=WHITE,
                   size=13, bold=True, enabled=True, icon=None):
        rect = pygame.Rect(rect)
        self.buttons[key] = (rect, action, enabled)
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            fill = (32, 46, 64)
            color = (116, 132, 153)
        elif hovered:
            fill = tuple(min(255, channel + 13) for channel in fill)
        self.rounded_rect(rect, fill, 7)
        if icon:
            self.draw_text(icon, rect.x + 22, rect.centery, size + 2, color, bold)
            self.draw_text(label, rect.centerx + 7, rect.centery, size, color, bold)
        else:
            self.draw_text(label, rect.centerx, rect.centery, size, color, bold)

    def draw_gear(self, center, color):
        cx, cy = center
        teeth = []
        for i in range(32):
            angle = math.tau * i / 32
            radius = 14 if i % 4 in (0, 1) else 10
            teeth.append((round(cx + math.cos(angle) * radius),
                          round(cy + math.sin(angle) * radius)))
        pygame.draw.polygon(self.screen, color, teeth)
        pygame.draw.circle(self.screen, PANEL_LIGHT, center, 7)
        pygame.draw.circle(self.screen, color, center, 3)

    def draw_bolt(self, center, color):
        cx, cy = center
        points = [(cx + 3, cy - 13), (cx - 7, cy + 1), (cx - 1, cy + 1),
                  (cx - 4, cy + 13), (cx + 8, cy - 3), (cx + 2, cy - 3)]
        pygame.draw.polygon(self.screen, color, points)

    def draw_skin_mark(self, center, size, skin, back_side=False):
        cx, cy = center
        half = size * .5
        color = skin["symbol"]
        kind = "star" if back_side else skin["mark"]
        if kind == "$":
            glyph = self.font(max(8, round(size)), True).render("$", True, color)
            self.screen.blit(glyph, glyph.get_rect(center=center))
        elif kind == "diamond":
            points = [(cx, cy - half), (cx + half * .72, cy),
                      (cx, cy + half), (cx - half * .72, cy)]
            pygame.draw.polygon(self.screen, color, points)
        elif kind == "heart":
            points = [(cx, cy + half * .62), (cx - half * .62, cy + half * .03),
                      (cx - half * .62, cy - half * .32), (cx - half * .45, cy - half * .58),
                      (cx - half * .2, cy - half * .57), (cx, cy - half * .32),
                      (cx + half * .2, cy - half * .57), (cx + half * .45, cy - half * .58),
                      (cx + half * .62, cy - half * .32), (cx + half * .62, cy + half * .03)]
            pygame.draw.polygon(self.screen, color, points)
        else:
            points = [(cx, cy - half), (cx + half * .2, cy - half * .2),
                      (cx + half, cy), (cx + half * .2, cy + half * .2),
                      (cx, cy + half), (cx - half * .2, cy + half * .2),
                      (cx - half, cy), (cx - half * .2, cy - half * .2)]
            pygame.draw.polygon(self.screen, color, points)

    def draw_background(self):
        self.screen.fill(BG)
        pygame.draw.circle(self.screen, (23, 40, 60), (-15, 125), 175)
        pygame.draw.circle(self.screen, (23, 40, 60), (520, 535), 185)
        pygame.draw.circle(self.screen, (20, 33, 51), (480, 20), 120)

    def draw_title_bar(self):
        pygame.draw.rect(self.screen, (12, 19, 31), (0, 0, WIDTH, 38))
        self.draw_text("●", 18, 19, 11, GOLD, True)
        self.draw_text("CLICKER CLUB", 36, 19, 12, GOLD, True, center=False)
        self.add_button("minimize", (452, 4, 28, 28), "−", self.minimize,
                        fill=(30, 44, 63), size=17)
        self.add_button("close", (484, 4, 28, 28), "×", self.close,
                        fill=(62, 38, 51), size=18)

    def draw_coin(self, center, radius, skin, scale=1.0, preview=False, angle=0):
        cx, cy = center
        rx = max(2, round(radius * scale * (abs(math.cos(angle)) if preview else 1)))
        ry = max(2, round(radius * scale))
        rect = pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2)
        shadow = rect.move(2, max(4, round(radius * 0.08)))
        pygame.draw.ellipse(self.screen, (5, 10, 17), shadow)
        pygame.draw.ellipse(self.screen, skin["outer"], rect)
        rim_rect = rect.inflate(-round(rx * .08), -round(ry * .08))
        pygame.draw.ellipse(self.screen, skin["rim"], rim_rect)
        face_rect = rect.inflate(-round(rx * .18), -round(ry * .18))
        pygame.draw.ellipse(self.screen, skin["main"], face_rect)
        inner = rect.inflate(-round(rx * .32), -round(ry * .32))
        pygame.draw.ellipse(self.screen, skin["rim"], inner, max(1, round(radius * .025)))
        inner_face = inner.inflate(-max(2, round(rx * .045)), -max(2, round(ry * .045)))
        pygame.draw.ellipse(self.screen, skin["main"], inner_face)
        # A curved highlight makes the coin feel raised while keeping its silhouette crisp.
        highlight = rect.inflate(-round(rx * .2), -round(ry * .2))
        pygame.draw.arc(self.screen, skin["symbol"], highlight, math.radians(205), math.radians(315), max(2, round(radius * .035)))
        width_factor = max(.12, abs(math.cos(angle)) if preview else 1)
        symbol_size = max(8, round(radius * .72 * scale * width_factor))
        self.draw_skin_mark((cx, cy - round(radius * .02)), symbol_size, skin,
                            back_side=preview and math.cos(angle) < 0)

    def draw_header(self):
        self.draw_text("Собирай монеты", WIDTH // 2, 77, 29, WHITE, True)
        self.draw_text("Каждый клик приближает к богатству", WIDTH // 2, 107, 13, TEXT_MUTED)

    def draw_balance(self):
        self.rounded_rect((42, 145, 436, 77), PANEL, 5, (42, 58, 78), 2)
        self.draw_text("ТВОЙ БАЛАНС", WIDTH // 2, 165, 11, TEXT_MUTED, True)
        self.draw_text(f"{self.coins:,}".replace(",", " ") + " монет", WIDTH // 2, 194, 24, WHITE, True)

    def draw_game_page(self, now):
        self.draw_header()
        self.add_button("settings", (62, 48, 46, 35), "", self.open_settings,
                        fill=PANEL_LIGHT, size=18)
        self.draw_gear((85, 65), WHITE)
        self.add_button("shop", (410, 48, 82, 35), "СКИНЫ", self.open_shop,
                        fill=PANEL_LIGHT, size=11)
        self.draw_balance()
        scale = 1.0
        if self.coin_animation_started is not None:
            elapsed = (now - self.coin_animation_started) * 1000
            if elapsed >= 170:
                self.coin_animation_started = None
            else:
                # Quick, subtle press and immediate return; all coin layers scale together.
                scale = 1 - .085 * math.sin(math.pi * min(1, elapsed / 170))
        self.draw_coin((260, 359), 114, self.skins[self.active_skin], scale)
        self.draw_text("НАЖМИ НА МОНЕТУ", 260, 499, 13, (220, 229, 242), True)
        self.rounded_rect((42, 526, 436, 94), PANEL, 5, (42, 58, 78), 2)
        self.draw_bolt((72, 554), GOLD)
        self.draw_text("СИЛА КЛИКА", 104, 548, 13, WHITE, True, False)
        self.draw_text(f"Сейчас за клик: {self.per_click} монет", 104, 573, 11, TEXT_MUTED, False, False)
        self.add_button("upgrade", (302, 551, 150, 46), f"+1  ·  {self.upgrade_cost}",
                        self.upgrade, fill=GOLD, color=(24, 34, 53), size=13,
                        enabled=self.coins >= self.upgrade_cost)

    def draw_shop_page(self, now):
        self.draw_header()
        self.add_button("shop_back_top", (410, 48, 82, 35), "СКИНЫ", self.close_shop,
                        fill=PANEL_LIGHT, size=11)
        self.rounded_rect((38, 145, 444, 477), BG, 0, (64, 83, 109), 2)
        self.draw_text("МАГАЗИН СКИНОВ", WIDTH // 2, 184, 22, GOLD, True)
        self.draw_text(f"Баланс: {self.coins} монет", WIDTH // 2, 215, 13, (185, 200, 220))
        # Match the previous 48-frame spin at 35 ms per frame (one turn in 1.68 s).
        self.preview_angle = (self.preview_angle + math.tau / (48 * .035) * self.dt) % math.tau
        for index, (key, skin) in enumerate(self.skins.items()):
            y = 240 + index * 75
            self.rounded_rect((55, y, 410, 66), PANEL, 3)
            self.draw_coin((93, y + 33), 22, skin, preview=True, angle=self.preview_angle)
            if key in self.owned_skins:
                label = skin["name"] + ("  ·  выбрана" if key == self.active_skin else "")
                enabled = key != self.active_skin
                action = lambda k=key: self.buy_or_select_skin(k)
            else:
                label = f"Купить: {skin['name']}  ·  {skin['price']} монет"
                enabled = self.coins >= skin["price"]
                action = lambda k=key: self.buy_or_select_skin(k)
            self.add_button(f"skin_{key}", (132, y + 12, 317, 42), label, action,
                            size=11, enabled=enabled)
        self.add_button("shop_back", (160, 540, 200, 43), "←  НАЗАД К ИГРЕ",
                        self.close_shop, fill=PANEL_LIGHT, size=12)

    def draw_settings_page(self):
        self.draw_header()
        self.add_button("settings_back_top", (62, 48, 46, 35), "", self.close_settings,
                        fill=PANEL_LIGHT, size=18)
        self.draw_gear((85, 65), WHITE)
        self.rounded_rect((38, 145, 444, 477), BG, 0, (64, 83, 109), 2)
        self.draw_text("НАСТРОЙКИ", WIDTH // 2, 197, 23, GOLD, True)
        self.draw_text("Управление прогрессом игры", WIDTH // 2, 230, 13, (185, 200, 220))
        self.add_button("reset", (118, 300, 284, 50), "Сбросить прогресс",
                        self.open_reset_confirm, fill=(169, 62, 75), size=14)
        self.add_button("settings_back", (160, 385, 200, 43), "←  НАЗАД К ИГРЕ",
                        self.close_settings, fill=PANEL_LIGHT, size=12)
        if self.confirm_reset_open:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((4, 8, 15, 174))
            self.screen.blit(overlay, (0, 0))
            self.rounded_rect((55, 238, 410, 204), PANEL, 10, (64, 83, 109), 2)
            self.draw_text("Сбросить прогресс?", WIDTH // 2, 280, 20, GOLD, True)
            self.draw_text("Монеты, улучшения и купленные скины", WIDTH // 2, 318, 12, WHITE)
            self.draw_text("будут удалены.", WIDTH // 2, 339, 12, WHITE)
            self.add_button("confirm_reset", (91, 368, 158, 46), "Сбросить",
                            self.confirm_reset, fill=(169, 62, 75), size=12)
            self.add_button("cancel_reset", (271, 368, 158, 46), "Отмена",
                            self.cancel_reset, fill=PANEL_LIGHT, size=12)

    def draw_particles(self, now):
        alive = []
        for particle in self.particles:
            # Input events can create particles after this frame's timestamp was captured.
            # Clamp their age so the first frame never computes alpha above 255.
            age = max(0.0, min(1.0, (now - particle["start"]) / particle["life"]))
            if age >= 1:
                continue
            alive.append(particle)
            x = particle["x"] + particle["vx"] * age
            y = particle["y"] + particle["vy"] * age + 40 * age * age
            radius = max(1, round(particle["radius"] * (1 - .75 * age)))
            alpha = max(0, min(255, int(round(255 * (1 - age)))))
            color = (255, 255, 255, alpha)
            dot = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, color, (radius + 1, radius + 1), radius)
            self.screen.blit(dot, (round(x - radius - 1), round(y - radius - 1)))
        self.particles = alive

    def draw(self, now):
        self.buttons = {}
        self.draw_background()
        self.draw_title_bar()
        if self.page == "game":
            self.draw_game_page(now)
        elif self.page == "shop":
            self.draw_shop_page(now)
        else:
            self.draw_settings_page()
        self.draw_particles(now)
        pygame.display.flip()

    def open_shop(self):
        self.page = "shop" if self.page != "shop" else "game"
        self.confirm_reset_open = False
        self.particles.clear()
        self.coin_animation_started = None

    def close_shop(self):
        self.page = "game"
        self.particles.clear()
        self.coin_animation_started = None

    def open_settings(self):
        self.page = "settings" if self.page != "settings" else "game"
        self.confirm_reset_open = False
        self.particles.clear()
        self.coin_animation_started = None

    def close_settings(self):
        self.page = "game"
        self.confirm_reset_open = False

    def open_reset_confirm(self):
        self.confirm_reset_open = True

    def cancel_reset(self):
        self.confirm_reset_open = False

    def confirm_reset(self):
        self.coins = 0
        self.per_click = 1
        self.upgrade_cost = 10
        self.owned_skins = {"classic"}
        self.active_skin = "classic"
        self.confirm_reset_open = False
        self.save_safely()

    def buy_or_select_skin(self, key):
        skin = self.skins[key]
        if key not in self.owned_skins:
            if self.coins < skin["price"]:
                return
            self.coins -= skin["price"]
            self.owned_skins.add(key)
        self.active_skin = key
        self.save_safely()

    def upgrade(self):
        if self.coins >= self.upgrade_cost:
            self.coins -= self.upgrade_cost
            self.per_click += 1
            self.upgrade_cost = int(self.upgrade_cost * 1.7) + 1
            self.save_safely()

    def spawn_particles(self):
        for index in range(18):
            angle = math.tau * index / 18 - math.pi / 2
            speed = 120 + (index % 4) * 25
            self.particles.append({
                "x": 260 + math.cos(angle) * 72,
                "y": 359 + math.sin(angle) * 72,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "start": time.perf_counter(),
                "life": .58 + (index % 3) * .08,
                "radius": 3 if index % 4 else 4,
            })

    def click_coin(self):
        self.coins += self.per_click
        now = time.perf_counter()
        self.coin_animation_started = now
        self.spawn_particles()
        self.save_safely()

    def minimize(self):
        pygame.display.iconify()

    def close(self):
        self.save_safely()
        self.running = False

    def begin_window_drag(self):
        if self.drag_api is None:
            return
        try:
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                self.drag_api.windll.user32.ReleaseCapture()
                self.drag_api.windll.user32.SendMessageW(hwnd, 0x00A1, 2, 0)
        except Exception:
            pass

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

    def handle_click(self, pos):
        if pos[1] < 38:
            if pos[0] >= 484:
                self.close()
            elif pos[0] >= 452:
                self.minimize()
            else:
                self.begin_window_drag()
            return
        for rect, action, enabled in reversed(list(self.buttons.values())):
            if rect.collidepoint(pos) and enabled:
                action()
                return
        if self.page == "game" and math.hypot(pos[0] - 260, pos[1] - 359) <= 114:
            self.click_coin()

    def run(self):
        while self.running:
            self.dt = min(self.clock.tick(60) / 1000, .05)
            now = time.perf_counter()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.confirm_reset_open:
                        self.cancel_reset()
                    elif self.page != "game":
                        self.page = "game"
                    else:
                        self.close()
            self.draw(now)
        self.save_safely()
        pygame.quit()


if __name__ == "__main__":
    ClickerGame().run()
