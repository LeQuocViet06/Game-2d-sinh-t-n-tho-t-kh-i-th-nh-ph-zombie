import pygame
import sys
import collections
import heapq
import random
import math
import os
import array

# 1. Khởi tạo cấu hình ban đầu
pygame.init()
pygame.mixer.init() 
pygame.mixer.set_num_channels(32) # [CHỐNG VĂNG]: Tăng số lượng kênh âm thanh tránh sập Audio Driver

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mafia: Apocalypse City - Custom AI & Mercenary Squad")
clock = pygame.time.Clock()

# Cấu hình Grid
TILE_SIZE = 40  
GRID_WIDTH = 32   
GRID_HEIGHT = 30  
WORLD_WIDTH = GRID_WIDTH * TILE_SIZE
WORLD_HEIGHT = GRID_HEIGHT * TILE_SIZE

# --- BẢNG MÀU VIP ---
COLOR_BG = (15, 17, 20)             
COLOR_WALL_RUIN = (74, 79, 84)       
COLOR_LAMP_POST = (149, 165, 166)    
COLOR_WRECK_CAR = (192, 57, 43)      
COLOR_TOXIC_BARREL = (39, 174, 96)   
COLOR_TEXT = (240, 240, 245)
COLOR_GREEN = (46, 204, 113)     
COLOR_RED = (231, 76, 60)       
COLOR_BULLET = (254, 202, 87)   
COLOR_GOLD = (255, 215, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_AMMO = (39, 174, 96)          
COLOR_STAMINA = (9, 132, 227)   
COLOR_FLASH = (255, 140, 0)     
COLOR_TANK = (139, 0, 0)         
COLOR_BOSS = (155, 89, 182) 
COLOR_ROAD_MARKING = (220, 220, 220)
COLOR_MERCENARY = (46, 204, 113) 

COLOR_BG_STORY = (15, 17, 20)
COLOR_TEXT_STORY = (230, 230, 235)
COLOR_RED_STORY = (231, 76, 60)
COLOR_GOLD_STORY = (255, 215, 0)
COLOR_LAMP_STORY = (149, 165, 166)

STORY_SLIDES = [
    {
        "title": "NAM 2029: NGAY TAN CUA NHAN LOAI",
        "bg_img": "story_bg1.png",
        "lines": [
            "Mot loai virus sinh hoc khong ro nguon goc bung phat tai trung tam thanh pho.",
            "Chi trong vong 72 gio, toan bo chinh phu sup do.",
            "Nhung nguoi chet song lai, san lung nhung sinh mang cuoi cung..."
        ]
    },
    {
        "title": "KE SONG SOT CUOI CUNG",
        "bg_img": "story_bg2.png",
        "lines": [
            "Ban la mot ong trum Mafia khet tieng, so huu kho vu khi ngam cua the gioi toi pham.",
            "Trong khi cac the luc khac chon cach tron chay hoac dau hang...",
            "Ban quyet dinh o lai, dung sung dan de quet sach ngay tan the nay."
        ]
    },
    {
        "title": "NHIEM VU SINH TU & DONG DOI",
        "bg_img": "story_bg3.png",
        "lines": [
            "Lu Zombie dang keo den theo tung dot gat gao (Dot 2 se cuc ky dong dao va dien cuong!).",
            "Dung lo, ban co thuoc vao Black Market dung tien thue toi da 5 De tu NPC cam AK47 boc lot.",
            "BOSS A* se xuat hien o giay thu 150. Hay dan tran va song sot!"
        ]
    }
]

STORY_BACKGROUNDS = {}
for idx, slide in enumerate(STORY_SLIDES):
    img_path = slide["bg_img"]
    if os.path.exists(img_path):
        try:
            loaded_img = pygame.image.load(img_path).convert()
            STORY_BACKGROUNDS[idx] = pygame.transform.scale(loaded_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except: STORY_BACKGROUNDS[idx] = None
    else: STORY_BACKGROUNDS[idx] = None

# Phông chữ toàn cục
font_sm = pygame.font.SysFont("Segoe UI", 14)
font_md = pygame.font.SysFont("Segoe UI", 16, bold=True)
font_lg = pygame.font.SysFont("Segoe UI", 24, bold=True)
font_title = pygame.font.SysFont("Impact", 54)
font_sub = pygame.font.SysFont("Segoe UI", 18, italic=True)
font_dmg = pygame.font.SysFont("Arial", 16, bold=True)

# [CẢI TIẾN VIP]: Hàm vẽ chữ nổi 3D (Drop Shadow)
def draw_text_vip(surface, text, font, color, x, y, shadow_offset=2):
    shadow = font.render(text, True, (0, 0, 0))
    main_txt = font.render(text, True, color)
    surface.blit(shadow, (x + shadow_offset, y + shadow_offset))
    surface.blit(main_txt, (x, y))

# =====================================================================
# HỆ THỐNG ÂM THANH SÚNG
# =====================================================================
def generate_heavy_shoot_sound(weapon_type):
    sample_rate = 22050
    if weapon_type == "shotgun":
        duration = 0.35; freq = 60; noise_mix = 0.85; volume_factor = 32767 
    elif weapon_type == "ak47":
        duration = 0.18; freq = 90; noise_mix = 0.75; volume_factor = 28000
    elif weapon_type == "gatling":
        duration = 0.08; freq = 110; noise_mix = 0.70; volume_factor = 22000
    elif weapon_type == "uzi":
        duration = 0.10; freq = 160; noise_mix = 0.65; volume_factor = 18000
    else:  
        duration = 0.14; freq = 130; noise_mix = 0.60; volume_factor = 20000

    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        noise = random.uniform(-1, 1)
        wave = math.sin(2 * math.pi * freq * t)
        if wave > 0: wave = 0.5
        else: wave = -0.5
        amplitude = math.exp(-6 * (t / duration))
        val = int((wave * (1 - noise_mix) + noise * noise_mix) * amplitude * volume_factor)
        buf[i] = max(-32768, min(32767, val))
    try: return pygame.mixer.Sound(buffer=buf)
    except: return None

def load_weapon_sound(weapon_id, external_filename):
    if os.path.exists(external_filename):
        try:
            sound = pygame.mixer.Sound(external_filename)
            return sound
        except Exception as e: pass
    return generate_heavy_shoot_sound(weapon_id)

SOUND_WEAPONS = {
    "pistol": load_weapon_sound("pistol", "pistol.wav"),
    "uzi": load_weapon_sound("uzi", "uzi.wav"),
    "ak47": load_weapon_sound("ak47", "ak47.wav"),
    "shotgun": load_weapon_sound("shotgun", "shotgun.wav"),
    "gatling": load_weapon_sound("gatling", "gatling.wav")
}

def get_weapon_sound(weapon_id):
    """Return a Sound for weapon_id, synthesizing a fallback if needed."""
    snd = SOUND_WEAPONS.get(weapon_id)
    if snd is None:
        try:
            snd = generate_heavy_shoot_sound(weapon_id)
            SOUND_WEAPONS[weapon_id] = snd
            print(f"[SOUND] Fallback synthesized for '{weapon_id}'")
        except Exception:
            SOUND_WEAPONS[weapon_id] = None
            snd = None
    return snd

BGM_FILE = "nhac_nen.mp3" 
bgm_playing = False

def play_background_music():
    global bgm_playing
    if os.path.exists(BGM_FILE) and not bgm_playing:
        try:
            pygame.mixer.music.load(BGM_FILE)
            pygame.mixer.music.play(-1) 
            pygame.mixer.music.set_volume(0.8) 
            bgm_playing = True
        except: pass

SETTINGS = {
    "screen_shake": True,
    "zombie_rage": True,
    "sound_effects": True,
    "music_enabled": True
}

# Test mode: start game with Gatling equipped (quick audio testing)
TEST_MODE_GATLING = True

WEAPON_DAMAGE = {
    "pistol": 20, "uzi": 25, "ak47": 40, "shotgun": 35, "gatling": 28
}

# =====================================================================
# HÌNH ẢNH
# =====================================================================
IMG_FILE_WALL = "wall_ruin.png"
IMG_FILE_LAMP = "lamp_post.png"
IMG_FILE_CAR  = "wreck_car.png"
IMG_FILE_BARREL = "toxic_barrel.png"
IMG_FILE_MAFIA_PISTOL = "mafia_pistol.png"
IMG_FILE_MAFIA_UZI = "mafia_uzi.png"         
IMG_FILE_MAFIA_AK = "mafia_ak.png"
IMG_FILE_MAFIA_SHOTGUN = "mafia_shotgun.png"
IMG_FILE_MAFIA_GATLING = "mafia_gatling.png" 
IMG_FILE_ZOMBIE = "zombie.png"
IMG_FILE_MERCENARY = "de_mafia.png"  

def load_tile_image(path):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        except: pass
    return None

def load_spritesheet(path, rows=4, cols=4):
    if not os.path.exists(path): return None
    try:
        sheet = pygame.image.load(path).convert_alpha()
        fw = sheet.get_width() // cols
        fh = sheet.get_height() // rows
        anims = {"down": [], "left": [], "right": [], "up": []}
        dirs = ["down", "left", "right", "up"]
        for r in range(rows):
            for c in range(cols):
                surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                surf.blit(sheet, (0, 0), (c*fw, r*fh, fw, fh))
                scaled = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
                anims[dirs[r]].append(scaled)
        return anims
    except: return None

MAP_IMAGES = {
    1: load_tile_image(IMG_FILE_WALL),
    2: load_tile_image(IMG_FILE_LAMP),
    3: load_tile_image(IMG_FILE_CAR),
    4: load_tile_image(IMG_FILE_BARREL)
}

ZOMBIE_BASE_ANIMS = load_spritesheet(IMG_FILE_ZOMBIE)
ZOMBIE_HEAVY_ANIMS = None
ZOMBIE_BOSS_ANIMS = None

if ZOMBIE_BASE_ANIMS:
    ZOMBIE_HEAVY_ANIMS = {"down": [], "left": [], "right": [], "up": []}
    ZOMBIE_BOSS_ANIMS = {"down": [], "left": [], "right": [], "up": []}
    for d in ["down", "left", "right", "up"]:
        for frame in ZOMBIE_BASE_ANIMS[d]:
            ZOMBIE_HEAVY_ANIMS[d].append(pygame.transform.scale(frame, (60, 60)))
            ZOMBIE_BOSS_ANIMS[d].append(pygame.transform.scale(frame, (88, 88)))

WEAPON_SHOP_IMAGES = {}
shop_files = {"pistol": "shop_pistol.png", "uzi": "shop_uzi.png", "ak47": "shop_ak47.png", "shotgun": "shop_shotgun.png", "gatling": "shop_gatling.png"}
for w_id, file_name in shop_files.items():
    if os.path.exists(file_name):
        try:
            img = pygame.image.load(file_name).convert_alpha()
            WEAPON_SHOP_IMAGES[w_id] = pygame.transform.scale(img, (48, 32))
        except: WEAPON_SHOP_IMAGES[w_id] = None
    else: WEAPON_SHOP_IMAGES[w_id] = None

# =====================================================================
# BẢN ĐỒ THÀNH PHỐ
# =====================================================================
GAME_MAP = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
VERTICAL_STREETS = [5, 16, 26]
HORIZONTAL_STREETS = [4, 13, 22]
ROAD_WIDTH = 5 

def generate_new_map():
    random.seed(pygame.time.get_ticks())
    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH): GAME_MAP[r][c] = 1

    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH):
            is_street = False
            for v_st in VERTICAL_STREETS:
                if v_st <= c < v_st + ROAD_WIDTH: is_street = True
            for h_st in HORIZONTAL_STREETS:
                if h_st <= r < h_st + ROAD_WIDTH: is_street = True
            if c < 8 and r < 7: is_street = True
            if is_street: GAME_MAP[r][c] = 0

    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH):
            if GAME_MAP[r][c] == 0:
                if c < 8 and r < 7: continue
                is_sidewalk = (
                    (r > 0 and GAME_MAP[r-1][c] == 1) or 
                    (r < GRID_HEIGHT-1 and GAME_MAP[r+1][c] == 1) or
                    (c > 0 and GAME_MAP[r][c-1] == 1) or 
                    (c < GRID_WIDTH-1 and GAME_MAP[r][c+1] == 1)
                )
                if is_sidewalk:
                    rand_val = random.random()
                    if rand_val < 0.05: GAME_MAP[r][c] = 2 
                    elif rand_val < 0.08: GAME_MAP[r][c] = 4 
                else:
                    if random.random() < 0.015: GAME_MAP[r][c] = 3 

generate_new_map()

def is_walkable(x, y):
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        return GAME_MAP[y][x] == 0
    return False

def get_neighbors(pos):
    x, y = pos
    neighbors = []
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        if is_walkable(x + dx, y + dy): neighbors.append((x + dx, y + dy))
    return neighbors

def path_a_star(start, target):
    pq = [(0, start)]
    came_from = {start: None}
    g_score = {start: 0}
    while pq:
        _, current = heapq.heappop(pq)
        if current == target: break
        for nxt in get_neighbors(current):
            tentative_g = g_score[current] + 1
            if nxt not in g_score or tentative_g < g_score[nxt]:
                g_score[nxt] = tentative_g
                f_score = tentative_g + (abs(nxt[0]-target[0]) + abs(nxt[1]-target[1]))
                heapq.heappush(pq, (f_score, nxt))
                came_from[nxt] = current
    if target not in came_from: return []
    path, curr = [], target
    while curr != start:
        path.append(curr); curr = came_from[curr]
    path.reverse(); return path

def path_bfs(start, target):
    queue = collections.deque([start])
    came_from = {start: None}
    while queue:
        current = queue.popleft()
        if current == target: break
        for nxt in get_neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                queue.append(nxt)
    if target not in came_from: return []
    path, curr = [], target
    while curr != start:
        path.append(curr); curr = came_from[curr]
    path.reverse(); return path

def path_dfs(start, target):
    stack = [start]
    came_from = {start: None}
    visited = {start}
    while stack:
        current = stack.pop()
        if current == target: break
        neighbors = get_neighbors(current)
        random.shuffle(neighbors)
        for nxt in neighbors:
            if nxt not in visited:
                visited.add(nxt)
                came_from[nxt] = current
                stack.append(nxt)
    if target not in came_from: return []
    path, curr = [], target
    while curr != start:
        path.append(curr); curr = came_from[curr]
    path.reverse(); return path

def path_pure_heuristic(start, target):
    sx, sy = start
    tx, ty = target
    best_move = start
    min_dist = float('inf')
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = sx + dx, sy + dy
        if is_walkable(nx, ny):
            dist = abs(nx - tx) + abs(ny - ty)
            if dist < min_dist:
                min_dist = dist; best_move = (nx, ny)
    return [best_move] if best_move != start else []

# =====================================================================
# THỰC THỂ KHÁC
# =====================================================================
class DamageText:
    def __init__(self, x, y, text, color=(255, 255, 255)):
        self.x = x + random.randint(-10, 10)
        self.y = y - 10
        self.text = str(text)
        self.color = color
        self.lifetime = 45 
        self.vy = -1.2     

    def update(self):
        self.y += self.vy; self.lifetime -= 1

    def draw(self, surface, cam_x, cam_y):
        px, py = int(self.x - cam_x), int(self.y - cam_y)
        if 0 <= px <= SCREEN_WIDTH and 0 <= py <= SCREEN_HEIGHT:
            alpha = min(255, int((self.lifetime / 45) * 255))
            txt_shadow = font_dmg.render(self.text, True, (0, 0, 0))
            txt_main = font_dmg.render(self.text, True, self.color)
            txt_shadow.set_alpha(alpha)
            txt_main.set_alpha(alpha)
            surface.blit(txt_shadow, (px+1, py+1))
            surface.blit(txt_main, (px, py))

class DropItem:
    def __init__(self, g_x, g_y, item_type="ammo", value=30):
        self.x = g_x * TILE_SIZE + TILE_SIZE // 2
        self.y = g_y * TILE_SIZE + TILE_SIZE // 2
        self.type = item_type
        self.value = value
        self.timer = 0

    @property
    def grid_x(self): return int(self.x // TILE_SIZE)

    @property
    def grid_y(self): return int(self.y // TILE_SIZE)

    def update_magnet(self, p_world_x, p_world_y):
        dx = p_world_x - self.x
        dy = p_world_y - self.y
        dist = math.hypot(dx, dy)
        # [CHỐNG VĂNG TUYỆT ĐỐI]: Chặn lỗi ZeroDivisionError
        if 0 < dist < 80:
            speed = 5
            self.x += (dx / dist) * speed
            self.y += (dy / dist) * speed

    def draw(self, surface, cam_x, cam_y):
        self.timer += 0.1
        bounce = math.sin(self.timer) * 3
        px = self.x - cam_x
        py = self.y - cam_y + bounce
        if -20 <= px <= SCREEN_WIDTH + 20 and -20 <= py <= SCREEN_HEIGHT + 20:
            if self.type == "ammo": 
                try: pygame.draw.rect(surface, (10, 10, 10), (int(px-11), int(py-9), 22, 17), 0, 3)
                except: pygame.draw.rect(surface, (10, 10, 10), (int(px-11), int(py-9), 22, 17), 0)
                try: pygame.draw.rect(surface, (30, 130, 76), (int(px-10), int(py-8), 20, 15), 0, 2)
                except: pygame.draw.rect(surface, (30, 130, 76), (int(px-10), int(py-8), 20, 15), 0)
            elif self.type == "health": 
                try: pygame.draw.rect(surface, (10, 10, 10), (int(px-9), int(py-9), 18, 18), 0, 5)
                except: pygame.draw.rect(surface, (10, 10, 10), (int(px-9), int(py-9), 18, 18), 0)
                try: pygame.draw.rect(surface, (231, 76, 60), (int(px-8), int(py-8), 16, 16), 0, 4)
                except: pygame.draw.rect(surface, (231, 76, 60), (int(px-8), int(py-8), 16, 16), 0)
            else: 
                pygame.draw.circle(surface, (10,10,10), (int(px), int(py)), 7)
                pygame.draw.circle(surface, COLOR_GOLD, (int(px), int(py)), 6)

class DropShell:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.vx = random.uniform(-2.5, 2.5); self.vy = random.uniform(-3.5, -1.5)
        self.gravity = 0.25; self.lifetime = 50; self.bounce_count = 0

    def update(self):
        self.vy += self.gravity; self.x += self.vx; self.y += self.vy; self.lifetime -= 1
        if self.bounce_count < 2 and self.vy > 0 and random.random() < 0.1:
            self.vy = -self.vy * 0.4; self.vx *= 0.6; self.bounce_count += 1

    def draw(self, surface, cam_x, cam_y):
        px, py = int(self.x - cam_x), int(self.y - cam_y)
        if 0 <= px <= SCREEN_WIDTH and 0 <= py <= SCREEN_HEIGHT:
            alpha = min(255, max(0, int((self.lifetime / 50) * 255)))
            shell_surf = pygame.Surface((4, 2), pygame.SRCALPHA)
            shell_surf.fill((212, 175, 55, alpha)) 
            surface.blit(shell_surf, (px, py))

class Bullet:
    def __init__(self, start_world_x, start_world_y, target_world_pos, angle_offset=0, is_friendly=True):
        self.x = start_world_x; self.y = start_world_y; self.speed = 16; self.alive = True; self.is_friendly = is_friendly
        dx = target_world_pos[0] - self.x; dy = target_world_pos[1] - self.y
        final_angle = math.atan2(dy, dx) + math.radians(angle_offset)
        self.vx = math.cos(final_angle) * self.speed; self.vy = math.sin(final_angle) * self.speed
        self.history = collections.deque(maxlen=5)

    def update(self):
        self.history.append((self.x, self.y))
        self.x += self.vx; self.y += self.vy
        if self.x < 0 or self.x > WORLD_WIDTH or self.y < 0 or self.y > WORLD_HEIGHT: self.alive = False; return
        g_x, g_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        if 0 <= g_x < GRID_WIDTH and 0 <= g_y < GRID_HEIGHT:
            if GAME_MAP[g_y][g_x] == 1: self.alive = False 

    def draw(self, surface, cam_x, cam_y):
        if self.alive:
            px, py = int(self.x - cam_x), int(self.y - cam_y)
            if len(self.history) >= 2:
                for i in range(1, len(self.history)):
                    p1 = (int(self.history[i-1][0] - cam_x), int(self.history[i-1][1] - cam_y))
                    p2 = (int(self.history[i][0] - cam_x), int(self.history[i][1] - cam_y))
                    alpha = int((i / len(self.history)) * 120)
                    tracer_color = (254, 202, 87, alpha) if self.is_friendly else (235, 94, 40, alpha)
                    tracer_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(tracer_surf, tracer_color, p1, p2, 2)
                    surface.blit(tracer_surf, (0, 0))
            if 0 <= px <= SCREEN_WIDTH and 0 <= py <= SCREEN_HEIGHT:
                pygame.draw.circle(surface, COLOR_BULLET if self.is_friendly else (235, 94, 40), (px, py), 3)

class Character:
    def __init__(self, x, y, initial_weapon_path):
        self.grid_x = x; self.grid_y = y; self.direction = "down"; self.frame_index = 0; self.is_moving = False
        self.hp = 100; self.max_hp = 100; self.stamina = 100.0
        self.all_weapons_anims = {"pistol": load_spritesheet(initial_weapon_path)}
        self.current_weapon = "pistol"; self.input_cooldown = 0; self.radar_timer = 0 

    def update_anim(self, sprinting):
        if self.is_moving:
            self.frame_index += 0.3 if sprinting else 0.15
            if self.frame_index >= 4: self.frame_index = 0
        else: self.frame_index = 0

    def draw(self, surface, cam_x, cam_y):
        px = self.grid_x * TILE_SIZE - cam_x
        py = self.grid_y * TILE_SIZE - cam_y
        
        self.radar_timer += 0.08
        pulse_radius = 16 + math.sin(self.radar_timer) * 3
        pygame.draw.circle(surface, (0, 255, 255, 120), (px + TILE_SIZE//2, py + TILE_SIZE - 4), int(pulse_radius), 2)

        active_anims = self.all_weapons_anims.get(self.current_weapon)
        if active_anims and active_anims.get(self.direction) and len(active_anims[self.direction]) > 0:
            surface.blit(active_anims[self.direction][int(self.frame_index)], (px, py))
        else:
            try: pygame.draw.rect(surface, (41, 128, 185), (px+4, py+4, TILE_SIZE-8, TILE_SIZE-8), 0, 8)
            except: pygame.draw.rect(surface, (41, 128, 185), (px+4, py+4, TILE_SIZE-8, TILE_SIZE-8), 0)

        n_w = font_md.size("BOSS MAFIA")[0]
        draw_text_vip(surface, "BOSS MAFIA", font_md, COLOR_GOLD, px + TILE_SIZE//2 - n_w//2, py - 20, 2)

        hp_ratio = max(0, self.hp) / self.max_hp
        hp_color = (46, 204, 113) if hp_ratio > 0.5 else ((241, 196, 15) if hp_ratio > 0.25 else (231, 76, 60))
        
        try: pygame.draw.rect(surface, (10, 10, 10), (px - 1, py + TILE_SIZE + 1, TILE_SIZE + 2, 6), 0, 3)
        except: pygame.draw.rect(surface, (10, 10, 10), (px - 1, py + TILE_SIZE + 1, TILE_SIZE + 2, 6), 0)
        
        try: pygame.draw.rect(surface, (40, 40, 45), (px, py + TILE_SIZE + 2, TILE_SIZE, 4), 0, 2)
        except: pygame.draw.rect(surface, (40, 40, 45), (px, py + TILE_SIZE + 2, TILE_SIZE, 4), 0)
        
        if hp_ratio > 0:
            try: pygame.draw.rect(surface, hp_color, (px, py + TILE_SIZE + 2, int(TILE_SIZE * hp_ratio), 4), 0, 2)
            except: pygame.draw.rect(surface, hp_color, (px, py + TILE_SIZE + 2, int(TILE_SIZE * hp_ratio), 4), 0)
            
            try: pygame.draw.rect(surface, (200, 255, 200), (px, py + TILE_SIZE + 2, int(TILE_SIZE * hp_ratio), 1), 0, 2)
            except: pygame.draw.rect(surface, (200, 255, 200), (px, py + TILE_SIZE + 2, int(TILE_SIZE * hp_ratio), 1), 0)
        
        try: pygame.draw.rect(surface, (10, 10, 10), (px - 1, py + TILE_SIZE + 8, TILE_SIZE + 2, 5), 0, 2)
        except: pygame.draw.rect(surface, (10, 10, 10), (px - 1, py + TILE_SIZE + 8, TILE_SIZE + 2, 5), 0)
        
        try: pygame.draw.rect(surface, (40, 40, 45), (px, py + TILE_SIZE + 9, TILE_SIZE, 3), 0, 1)
        except: pygame.draw.rect(surface, (40, 40, 45), (px, py + TILE_SIZE + 9, TILE_SIZE, 3), 0)
        
        if self.stamina > 0:
            try: pygame.draw.rect(surface, COLOR_STAMINA, (px, py + TILE_SIZE + 9, int(TILE_SIZE * (self.stamina / 100)), 3), 0, 1)
            except: pygame.draw.rect(surface, COLOR_STAMINA, (px, py + TILE_SIZE + 9, int(TILE_SIZE * (self.stamina / 100)), 3), 0)

class Mercenary:
    def __init__(self, x, y, idx=0):
        self.grid_x = x; self.grid_y = y; self.idx = idx; self.direction = "down"; self.frame_index = 0
        self.is_moving = False; self.move_cooldown = 0; self.base_cooldown = 10 
        self.shoot_cooldown = 0; self.shoot_rate = 35; self.anims = load_spritesheet(IMG_FILE_MERCENARY)
        self.target_offset_x = 0; self.target_offset_y = 0; self.rethink_timer = 0
        self.name = f"De_{self.idx + 1}"

    def update(self, player_obj, zombies):
        if self.move_cooldown > 0: self.move_cooldown -= 1
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        
        self.rethink_timer -= 1
        if self.rethink_timer <= 0:
            self.rethink_timer = random.randint(40, 70)
            self.target_offset_x = random.randint(-3, 3)
            self.target_offset_y = random.randint(-3, 3)
            if self.target_offset_x == 0 and self.target_offset_y == 0:
                self.target_offset_x = random.choice([-1, 1])

        target_x = max(0, min(GRID_WIDTH - 1, player_obj.grid_x + self.target_offset_x))
        target_y = max(0, min(GRID_HEIGHT - 1, player_obj.grid_y + self.target_offset_y))
        if not is_walkable(target_x, target_y): target_x, target_y = player_obj.grid_x, player_obj.grid_y

        start = (self.grid_x, self.grid_y)
        target = (target_x, target_y)
        dist_to_target = abs(self.grid_x - target_x) + abs(self.grid_y - target_y)
        
        self.is_moving = False
        if dist_to_target > 0 and self.move_cooldown == 0:
            path = path_a_star(start, target)
            if path and len(path) > 0:
                nx, ny = path[0]
                dx, dy = nx - self.grid_x, ny - self.grid_y
                if dx > 0: self.direction = "right"
                elif dx < 0: self.direction = "left"
                elif dy > 0: self.direction = "down"
                elif dy < 0: self.direction = "up"
                self.grid_x, self.grid_y = nx, ny
                self.move_cooldown = self.base_cooldown; self.is_moving = True

        self.frame_index = (self.frame_index + 0.15) % 4 if self.is_moving else 0

        if self.shoot_cooldown == 0 and zombies:
            closest_zombie = None; min_dist = 8 
            for zb in zombies:
                d = math.hypot(zb.grid_x - self.grid_x, zb.grid_y - self.grid_y)
                if d < min_dist: min_dist = d; closest_zombie = zb
            
            if closest_zombie:
                self.shoot_cooldown = self.shoot_rate
                mx, my = self.grid_x * TILE_SIZE + TILE_SIZE // 2, self.grid_y * TILE_SIZE + TILE_SIZE // 2
                zx, zy = closest_zombie.grid_x * TILE_SIZE + TILE_SIZE // 2, closest_zombie.grid_y * TILE_SIZE + TILE_SIZE // 2
                bullets.append(Bullet(mx, my, (zx, zy), angle_offset=random.uniform(-4,4), is_friendly=True))
                shells.append(DropShell(mx, my))
                if SETTINGS["sound_effects"]:
                    snd = get_weapon_sound("ak47")
                    if snd:
                        try: snd.play()
                        except: pass

    def draw(self, surface, cam_x, cam_y):
        px = self.grid_x * TILE_SIZE - cam_x
        py = self.grid_y * TILE_SIZE - cam_y
        if -40 <= px <= SCREEN_WIDTH + 40 and -40 <= py <= SCREEN_HEIGHT + 40:
            if self.anims and self.anims.get(self.direction) and len(self.anims[self.direction]) > 0:
                surface.blit(self.anims[self.direction][int(self.frame_index)], (px, py))
            else:
                try: pygame.draw.rect(surface, COLOR_MERCENARY, (px + 6, py + 6, TILE_SIZE - 12, TILE_SIZE - 12), 0, 6)
                except: pygame.draw.rect(surface, COLOR_MERCENARY, (px + 6, py + 6, TILE_SIZE - 12, TILE_SIZE - 12), 0)
                
                try: pygame.draw.rect(surface, (255, 255, 255), (px + 12, py + 12, TILE_SIZE - 24, TILE_SIZE - 24), 2, 6)
                except: pygame.draw.rect(surface, (255, 255, 255), (px + 12, py + 12, TILE_SIZE - 24, TILE_SIZE - 24), 2)
            
            lbl_w = font_sm.size(self.name)[0]
            draw_text_vip(surface, self.name, font_sm, (200, 240, 200), px + TILE_SIZE//2 - lbl_w//2, py - 18, 1)

class Zombie:
    def __init__(self, x, y, color_theme=(231, 76, 60)):
        self.grid_x = x; self.grid_y = y; self.direction = "down"; self.frame_index = 0; self.is_moving = False
        self.hp = 100; self.max_hp = 100
        self.color_theme = color_theme; self.move_cooldown = 0; self.base_cooldown = 24 
        self.is_enraged = False; self.is_heavy = False; self.is_boss = False
        self.ai_type = random.choice(["A*", "BFS", "DFS", "HEURISTIC"])

    def update_ai(self, target_pos):
        start, target = (self.grid_x, self.grid_y), (target_pos[0], target_pos[1])
        if start == target or self.move_cooldown > 0:
            if self.move_cooldown > 0: self.move_cooldown -= 1
            return
        
        if self.is_boss: self.ai_type = "A*"
        path = path_a_star(start, target) if self.ai_type == "A*" else (path_bfs(start, target) if self.ai_type == "BFS" else (path_dfs(start, target) if self.ai_type == "DFS" else path_pure_heuristic(start, target)))

        if path:
            dx, dy = path[0][0] - self.grid_x, path[0][1] - self.grid_y
            if dx > 0: self.direction = "right"
            elif dx < 0: self.direction = "left"
            elif dy > 0: self.direction = "down"
            elif dy < 0: self.direction = "up"
            self.grid_x, self.grid_y = path[0]
            self.is_moving = True
            self.move_cooldown = self.base_cooldown // 2 if (SETTINGS["zombie_rage"] and self.is_enraged) else self.base_cooldown
        else: self.is_moving = False

    def draw(self, surface, cam_x, cam_y):
        world_x, world_y = self.grid_x * TILE_SIZE + TILE_SIZE // 2, self.grid_y * TILE_SIZE + TILE_SIZE // 2
        active_sheet = ZOMBIE_BOSS_ANIMS if self.is_boss else (ZOMBIE_HEAVY_ANIMS if self.is_heavy else ZOMBIE_BASE_ANIMS)
        offset = 44 if self.is_boss else (30 if self.is_heavy else 20)
        px, py = world_x - offset - cam_x, world_y - offset - cam_y
        
        if -100 <= px <= SCREEN_WIDTH + 100 and -100 <= py <= SCREEN_HEIGHT + 100:
            if active_sheet and active_sheet.get(self.direction): surface.blit(active_sheet[self.direction][int(self.frame_index)], (px, py))
            else: pygame.draw.circle(surface, (192, 57, 43) if (SETTINGS["zombie_rage"] and self.is_enraged) else self.color_theme, (int(world_x - cam_x), int(world_y - cam_y)), 40 if self.is_boss else (25 if self.is_heavy else 14))
            
            px_grid, py_grid = self.grid_x * TILE_SIZE - cam_x, self.grid_y * TILE_SIZE - cam_y
            z_hp_ratio = max(0, self.hp) / self.max_hp
            
            try: pygame.draw.rect(surface, (10, 10, 10), (px_grid - 1, py_grid - 9, TILE_SIZE + 2, 6), 0, 3) 
            except: pygame.draw.rect(surface, (10, 10, 10), (px_grid - 1, py_grid - 9, TILE_SIZE + 2, 6), 0)
            
            try: pygame.draw.rect(surface, (50, 20, 20), (px_grid, py_grid - 8, TILE_SIZE, 4), 0, 2)
            except: pygame.draw.rect(surface, (50, 20, 20), (px_grid, py_grid - 8, TILE_SIZE, 4), 0)
            
            if z_hp_ratio > 0:
                try: pygame.draw.rect(surface, COLOR_RED, (px_grid, py_grid - 8, int(TILE_SIZE * z_hp_ratio), 4), 0, 2)
                except: pygame.draw.rect(surface, COLOR_RED, (px_grid, py_grid - 8, int(TILE_SIZE * z_hp_ratio), 4), 0)
                
                try: pygame.draw.rect(surface, (255, 150, 150), (px_grid, py_grid - 8, int(TILE_SIZE * z_hp_ratio), 1), 0, 2)
                except: pygame.draw.rect(surface, (255, 150, 150), (px_grid, py_grid - 8, int(TILE_SIZE * z_hp_ratio), 1), 0)
            
            d_name = "BOSS A*" if self.is_boss else self.ai_type
            n_w = font_sm.size(d_name)[0]
            draw_text_vip(surface, d_name, font_sm, COLOR_GOLD if self.is_boss else (200, 200, 200), px_grid + TILE_SIZE//2 - n_w//2, py_grid - 24, 1)

class HeavyZombie(Zombie):
    def __init__(self, x, y):
        super().__init__(x, y, COLOR_TANK)
        self.hp = 450; self.max_hp = 450; self.base_cooldown = 32; self.is_heavy = True; self.has_shield = True

    def take_damage_logic(self, damage):
        if self.has_shield: self.has_shield = False; return int(damage * 0.3), True
        self.hp -= damage; self.is_enraged = True; return damage, False

class BossZombie(Zombie):
    def __init__(self, x, y):
        super().__init__(x, y, COLOR_BOSS)
        self.hp = 1500; self.max_hp = 1500; self.base_cooldown = 20; self.is_boss = True; self.ai_type = "A*"
        self.last_spawn_hp = 1500 

# --- KHỞI TẠO ĐỐI TƯỢNG HỆ THỐNG ---
player = Character(2, 2, IMG_FILE_MAFIA_PISTOL)
player.all_weapons_anims["uzi"] = load_spritesheet(IMG_FILE_MAFIA_UZI)        
player.all_weapons_anims["ak47"] = load_spritesheet(IMG_FILE_MAFIA_AK)
player.all_weapons_anims["shotgun"] = load_spritesheet(IMG_FILE_MAFIA_SHOTGUN)
player.all_weapons_anims["gatling"] = load_spritesheet(IMG_FILE_MAFIA_GATLING)

bullets, drop_items, zombies_list, damage_texts, mercenaries_list, shells = [], [], [], [], [], []
player_money = 0; shoot_cooldown = 0; game_over = False; game_win = False; auto_play = False 
shake_intensity = 0; flash_duration = 0; flash_pos = (0, 0); flash_angle = 0; dmg_flash_timer = 0 
game_ticks = 0; boss_spawned = False; has_active_session = False; current_story_slide = 0
player_ammo = {"pistol": 36, "uzi": 0, "ak47": 0, "shotgun": 0, "gatling": 0}

if TEST_MODE_GATLING:
    player.current_weapon = "gatling"
    player_ammo["gatling"] = 150

def reset_game():
    global player_money, game_over, game_win, auto_play, shake_intensity, flash_duration, dmg_flash_timer, game_ticks, boss_spawned, has_active_session, current_story_slide
    player.hp = 100; player.stamina = 100; player_money = 0  
    player_ammo["pistol"] = 36
    for k in ["uzi", "ak47", "shotgun", "gatling"]: player_ammo[k] = 0
    player.current_weapon = "pistol"
    bullets.clear(); drop_items.clear(); damage_texts.clear(); zombies_list.clear(); mercenaries_list.clear(); shells.clear()
    game_ticks = 0; boss_spawned = False; current_story_slide = 0; auto_play = False 
    generate_new_map(); player.grid_x, player.grid_y = 2, 2
    for _ in range(4):
        while True:
            rx, ry = random.randint(10, GRID_WIDTH-2), random.randint(10, GRID_HEIGHT-2)
            if is_walkable(rx, ry): zombies_list.append(Zombie(rx, ry)); break
    game_over = False; game_win = False; has_active_session = True

game_state = "MENU"; previous_state = "MENU" 
shop_btn_rect = pygame.Rect(20, SCREEN_HEIGHT - 80, 120, 50)
auto_btn_rect = pygame.Rect(160, SCREEN_HEIGHT - 80, 120, 50) 
rope_pulse = 0

# =====================================================================
# OVERLAY TĨNH (Tối ưu RAM siêu cấp)
# =====================================================================
screen_dim_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
screen_dim_overlay.fill((5, 5, 8, 180))

go_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
go_overlay.fill((20, 5, 5, 220))

win_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
win_overlay.fill((5, 30, 15, 220))

red_flash_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
red_flash_overlay.fill((231, 76, 60, 60))

hud_glass_panel = pygame.Surface((270, 135), pygame.SRCALPHA)
try: pygame.draw.rect(hud_glass_panel, (15, 18, 22, 210), (0, 0, 270, 135), 0, 16)
except: hud_glass_panel.fill((15, 18, 22, 210))
try: pygame.draw.rect(hud_glass_panel, (0, 255, 255, 120), (0, 0, 270, 135), 2, 16)
except: pygame.draw.rect(hud_glass_panel, (0, 255, 255, 120), (0, 0, 270, 135), 2)
try: pygame.draw.rect(hud_glass_panel, (30, 30, 35), (20, 22, 230, 20), 0, 10)
except: hud_glass_panel.fill((30, 30, 35, 255), (20, 22, 230, 20))
try: pygame.draw.rect(hud_glass_panel, (10, 10, 10), (20, 22, 230, 20), 1, 10)
except: pygame.draw.rect(hud_glass_panel, (10, 10, 10), (20, 22, 230, 20), 1)
try: pygame.draw.rect(hud_glass_panel, (30, 30, 35), (20, 52, 230, 10), 0, 5)
except: hud_glass_panel.fill((30, 30, 35, 255), (20, 52, 230, 10))
try: pygame.draw.rect(hud_glass_panel, (10, 10, 10), (20, 52, 230, 10), 1, 5)
except: pygame.draw.rect(hud_glass_panel, (10, 10, 10), (20, 52, 230, 10), 1)

time_panel_bg = pygame.Surface((250, 42), pygame.SRCALPHA)
try: pygame.draw.rect(time_panel_bg, (15, 18, 22, 220), (0, 0, 250, 42), 0, 12)
except: time_panel_bg.fill((15, 18, 22, 220))
try: pygame.draw.rect(time_panel_bg, (255, 215, 0, 120), (0, 0, 250, 42), 2, 12)
except: pygame.draw.rect(time_panel_bg, (255, 215, 0, 120), (0, 0, 250, 42), 2)

MM_SCALE = 3; mm_w = GRID_WIDTH * MM_SCALE; mm_h = GRID_HEIGHT * MM_SCALE
mm_panel_bg = pygame.Surface((mm_w + 24, mm_h + 24), pygame.SRCALPHA)
try: pygame.draw.rect(mm_panel_bg, (15, 18, 22, 210), (0, 0, mm_w + 24, mm_h + 24), 0, 12)
except: mm_panel_bg.fill((15, 18, 22, 210))
try: pygame.draw.rect(mm_panel_bg, (0, 255, 255, 120), (0, 0, mm_w + 24, mm_h + 24), 2, 12)
except: pygame.draw.rect(mm_panel_bg, (0, 255, 255, 120), (0, 0, mm_w + 24, mm_h + 24), 2)

# --- VÒNG LẶP CHÍNH ---
running = True
while running:
    clock.tick(60)
    screen.fill(COLOR_BG)
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False
    
    if SETTINGS["music_enabled"]: play_background_music()
    else:
        if bgm_playing: pygame.mixer.music.stop(); bgm_playing = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: mouse_clicked = True
        elif event.type == pygame.KEYDOWN:
            if (game_over or game_win) and event.key == pygame.K_r:  
                reset_game(); game_state = "STORY"
            if game_state == "STORY" and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if current_story_slide == len(STORY_SLIDES) - 1: game_state = "PLAYING"
                else: current_story_slide += 1
            if game_state == "PLAYING" and not game_over and not game_win:
                if event.key == pygame.K_p: previous_state = "PLAYING"; game_state = "SHOP"
                elif event.key == pygame.K_ESCAPE: previous_state = "PLAYING"; game_state = "MENU"
                elif event.key == pygame.K_o: auto_play = not auto_play
            elif game_state in ["SHOP", "SETTINGS", "TUTORIAL"] and event.key == pygame.K_ESCAPE:
                game_state = previous_state

    if game_state == "MENU":
        title_w = font_title.size("MAFIA: APOCALYPSE CITY")[0]
        pulse_scale = math.sin(pygame.time.get_ticks() * 0.003) * 5
        draw_text_vip(screen, "MAFIA: APOCALYPSE CITY", font_title, COLOR_RED, SCREEN_WIDTH // 2 - title_w // 2, int(60 + pulse_scale), 4)
        
        menu_buttons = [
            {"id": "new_game", "text": "CHOI MOI (NEW GAME)", "base_color": (39, 174, 96), "border": COLOR_GREEN},
            {"id": "continue", "text": "TIEP TUC (CONTINUE)", "disabled": not has_active_session or game_over or game_win, "base_color": (41, 128, 185), "border": COLOR_CYAN},
            {"id": "tutorial", "text": "HUONG DAN CHOI", "base_color": (52, 73, 94), "border": (189, 195, 199)},
            {"id": "settings", "text": "CAI DAT HE THONG", "base_color": (52, 73, 94), "border": (189, 195, 199)},
            {"id": "exit", "text": "THOAT GAME", "base_color": (192, 57, 43), "border": COLOR_RED}
        ]
        btn_y = 170
        for btn in menu_buttons:
            btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 160, btn_y, 320, 50)
            is_hover = btn_rect.collidepoint(mouse_pos) and not btn.get("disabled", False)
            
            if btn.get("disabled", False):
                try: pygame.draw.rect(screen, (30, 30, 35), btn_rect, 0, 12)
                except: pygame.draw.rect(screen, (30, 30, 35), btn_rect, 0)
                
                try: pygame.draw.rect(screen, (50, 50, 55), btn_rect, 2, 12)
                except: pygame.draw.rect(screen, (50, 50, 55), btn_rect, 2)
                draw_text_vip(screen, btn["text"], font_md, (100, 100, 105), btn_rect.centerx - font_md.size(btn["text"])[0]//2, btn_rect.centery - 10)
            else:
                bg_c = btn["border"] if is_hover else btn["base_color"]
                border_c = (255, 255, 255) if is_hover else btn["border"]
                txt_c = (15, 15, 20) if is_hover else COLOR_TEXT
                
                try: pygame.draw.rect(screen, border_c, btn_rect, 0, 12)
                except: pygame.draw.rect(screen, border_c, btn_rect, 0)
                
                inner_rect = btn_rect.inflate(-6, -6)
                try: pygame.draw.rect(screen, bg_c, inner_rect, 0, 9)
                except: pygame.draw.rect(screen, bg_c, inner_rect, 0)
                
                draw_text_vip(screen, btn["text"], font_md, txt_c, btn_rect.centerx - font_md.size(btn["text"])[0]//2, btn_rect.centery - 10, 0 if is_hover else 2)
            
            if mouse_clicked and is_hover:
                if btn["id"] == "new_game": reset_game(); game_state = "STORY"
                elif btn["id"] == "continue": game_state = "PLAYING"
                elif btn["id"] == "tutorial": previous_state = "MENU"; game_state = "TUTORIAL"
                elif btn["id"] == "settings": previous_state = "MENU"; game_state = "SETTINGS"
                elif btn["id"] == "exit": running = False
            btn_y += 65
        pygame.display.flip(); continue

    elif game_state == "STORY":
        if STORY_BACKGROUNDS.get(current_story_slide) is not None:
            screen.blit(STORY_BACKGROUNDS[current_story_slide], (0, 0)); screen.blit(screen_dim_overlay, (0, 0))
        else: screen.fill(COLOR_BG_STORY)
        slide_data = STORY_SLIDES[current_story_slide]
        
        draw_text_vip(screen, slide_data["title"], font_lg, COLOR_RED_STORY, SCREEN_WIDTH // 2 - font_lg.size(slide_data["title"])[0] // 2, 120, 3)
        start_y = 220
        for line in slide_data["lines"]:
            draw_text_vip(screen, line, font_sub, COLOR_TEXT_STORY, SCREEN_WIDTH // 2 - font_sub.size(line)[0] // 2, start_y, 2); start_y += 45
            
        btn_next_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 120, 280, 50)
        is_hover_next = btn_next_rect.collidepoint(mouse_pos)
        is_last_slide = (current_story_slide == len(STORY_SLIDES) - 1)
        
        try: pygame.draw.rect(screen, (255, 255, 255) if is_hover_next else COLOR_GOLD_STORY, btn_next_rect, 0, 12)
        except: pygame.draw.rect(screen, (255, 255, 255) if is_hover_next else COLOR_GOLD_STORY, btn_next_rect, 0)
        
        try: pygame.draw.rect(screen, COLOR_GOLD_STORY if is_hover_next else (230, 126, 34), btn_next_rect.inflate(-6, -6), 0, 9)
        except: pygame.draw.rect(screen, COLOR_GOLD_STORY if is_hover_next else (230, 126, 34), btn_next_rect.inflate(-6, -6), 0)
        
        txt_str = "BAT DAU CHIEN DAU" if is_last_slide else "TIEP THEO (SPACE)"
        draw_text_vip(screen, txt_str, font_md, (15, 15, 20) if is_hover_next else COLOR_BG, btn_next_rect.centerx - font_md.size(txt_str)[0] // 2, btn_next_rect.centery - 10, 0 if is_hover_next else 2)
        
        page_str = f"{current_story_slide + 1} / {len(STORY_SLIDES)}"
        draw_text_vip(screen, page_str, font_sm, COLOR_LAMP_STORY, SCREEN_WIDTH // 2 - font_sm.size(page_str)[0] // 2, SCREEN_HEIGHT - 50, 1)
        
        if mouse_clicked and btn_next_rect.collidepoint(mouse_pos):
            if is_last_slide: game_state = "PLAYING"
            else: current_story_slide += 1
        pygame.display.flip(); continue

    elif game_state == "SETTINGS":
        box_rect = pygame.Rect(SCREEN_WIDTH//2 - 240, SCREEN_HEIGHT//2 - 200, 480, 400)
        try: pygame.draw.rect(screen, (15, 18, 22), box_rect, 0, 16)
        except: pygame.draw.rect(screen, (15, 18, 22), box_rect, 0)
        
        try: pygame.draw.rect(screen, COLOR_CYAN, box_rect, 2, 16)
        except: pygame.draw.rect(screen, COLOR_CYAN, box_rect, 2)
        
        draw_text_vip(screen, "BANG CAI DAT HE THONG", font_lg, COLOR_CYAN, box_rect.centerx - font_lg.size("BANG CAI DAT HE THONG")[0]//2, box_rect.y + 25)
        
        opt_y = box_rect.y + 100
        options = [{"key": "screen_shake", "label": "Rung lac man hinh (Screen Shake)"}, {"key": "zombie_rage", "label": "Quai noi dien tang toc (Zombie Rage)"}, {"key": "sound_effects", "label": "Am thanh sung no (External & SFX)"}, {"key": "music_enabled", "label": f"Nhac nen BGM ({BGM_FILE})"}]
        for opt in options:
            chk_rect = pygame.Rect(box_rect.x + 40, opt_y, 24, 24)
            is_hover_chk = chk_rect.collidepoint(mouse_pos)
            
            try: pygame.draw.rect(screen, (0, 255, 255) if is_hover_chk else (100, 100, 105), chk_rect, 2, 6)
            except: pygame.draw.rect(screen, (0, 255, 255) if is_hover_chk else (100, 100, 105), chk_rect, 2)
            
            if SETTINGS[opt["key"]]: 
                try: pygame.draw.rect(screen, COLOR_CYAN, (chk_rect.x + 5, chk_rect.y + 5, 14, 14), 0, 4)
                except: pygame.draw.rect(screen, COLOR_CYAN, (chk_rect.x + 5, chk_rect.y + 5, 14, 14), 0)
            
            draw_text_vip(screen, opt["label"], font_md, COLOR_TEXT, chk_rect.right + 20, chk_rect.y, 2)
            if mouse_clicked and chk_rect.collidepoint(mouse_pos): SETTINGS[opt["key"]] = not SETTINGS[opt["key"]]
            opt_y += 55
            
        btn_back_rect = pygame.Rect(box_rect.centerx - 120, box_rect.bottom - 70, 240, 45)
        is_hover_b = btn_back_rect.collidepoint(mouse_pos)
        
        try: pygame.draw.rect(screen, COLOR_GREEN if is_hover_b else (39, 174, 96), btn_back_rect, 0, 10)
        except: pygame.draw.rect(screen, COLOR_GREEN if is_hover_b else (39, 174, 96), btn_back_rect, 0)
        
        draw_text_vip(screen, "QUAY LAI PANEL TRUOC", font_md, COLOR_BG, btn_back_rect.centerx - font_md.size("QUAY LAI PANEL TRUOC")[0]//2, btn_back_rect.centery - 10, 0)
        if mouse_clicked and is_hover_b: game_state = previous_state
        pygame.display.flip(); continue

    elif game_state == "TUTORIAL":
        box_rect = pygame.Rect(SCREEN_WIDTH//2 - 280, SCREEN_HEIGHT//2 - 220, 560, 440)
        try: pygame.draw.rect(screen, (15, 18, 22), box_rect, 0, 16)
        except: pygame.draw.rect(screen, (15, 18, 22), box_rect, 0)
        
        try: pygame.draw.rect(screen, COLOR_GOLD, box_rect, 2, 16)
        except: pygame.draw.rect(screen, COLOR_GOLD, box_rect, 2)
        
        draw_text_vip(screen, "CAM NANG SINH TON APOCALYPSE", font_lg, COLOR_GOLD, box_rect.centerx - font_lg.size("CAM NANG SINH TON APOCALYPSE")[0]//2, box_rect.y + 25)
        
        lines = [
            "DI CHUYEN: Dung cum phim [W, A, S, D] hoac phim Mui Ten.",
            "CHAY NHANH: Nhan giu phim [Left SHIFT] de but toc (Ton Stamina).",
            "BAN SUNG: Re chuot de ngam huong, nhan [Chuot Trai] de na dan.",
            "DE TU MAFIA: Vao Shop thue de tu cam AK47 đi tuan ngau nhien yem tro.",
            "HOA LUC PHAN HOA: Dot 2 (sau 50s) quai se dong dao len toi 25 con!",
            "CUA HANG VU KHI: Nhan phim [ P ] hoac click nut SHOP de nang cap sung.",
            "AUTO PLAY: Nhan phim [ O ] de he thong tu dong choi game."
        ]
        ly = box_rect.y + 85
        for ln in lines:
            draw_text_vip(screen, ln, font_md, COLOR_GOLD if "DE TU" in ln or "Dot 2" in ln or "AUTO PLAY" in ln else COLOR_TEXT, box_rect.x + 30, ly, 2); ly += 38
            
        btn_back_rect = pygame.Rect(box_rect.centerx - 120, box_rect.bottom - 60, 240, 45)
        is_hover_b = btn_back_rect.collidepoint(mouse_pos)
        
        try: pygame.draw.rect(screen, (255, 100, 100) if is_hover_b else (192, 57, 43), btn_back_rect, 0, 10)
        except: pygame.draw.rect(screen, (255, 100, 100) if is_hover_b else (192, 57, 43), btn_back_rect, 0)
        
        draw_text_vip(screen, "HIEU ROI, QUAY LAI", font_md, COLOR_BG if is_hover_b else COLOR_TEXT, btn_back_rect.centerx - font_md.size("HIEU ROI, QUAY LAI")[0]//2, btn_back_rect.centery - 10, 0)
        if mouse_clicked and is_hover_b: game_state = previous_state
        pygame.display.flip(); continue

    elif game_state == "SHOP":
        shop_box = pygame.Rect(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 260, 600, 520)
        try: pygame.draw.rect(screen, (15, 18, 22), shop_box, 0, 16)
        except: pygame.draw.rect(screen, (15, 18, 22), shop_box, 0)
        
        try: pygame.draw.rect(screen, COLOR_GOLD, shop_box, 2, 16)
        except: pygame.draw.rect(screen, COLOR_GOLD, shop_box, 2)
        
        draw_text_vip(screen, "CHO DEN VU KHI APOCALYPSE", font_lg, COLOR_GOLD, shop_box.centerx - font_lg.size("CHO DEN VU KHI APOCALYPSE")[0]//2, shop_box.y + 20)
        
        merc_count = len(mercenaries_list)
        merc_price = 500 + (merc_count * 250)
        
        shop_items = [
            {"type": "weapon", "id": "pistol", "name": f"Dan Sung Luc Tactical (DMG: {WEAPON_DAMAGE['pistol']})", "price": 40, "ammo_grant": 24},
            {"type": "weapon", "id": "uzi", "name": f"Sung Tieu Lien UZI (DMG: {WEAPON_DAMAGE['uzi']})", "price": 200, "ammo_grant": 60}, 
            {"type": "weapon", "id": "ak47", "name": f"Truong Lien Thanh AK-47 (DMG: {WEAPON_DAMAGE['ak47']})", "price": 350, "ammo_grant": 45},
            {"type": "weapon", "id": "shotgun", "name": f"Shotgun Dan Chum (DMG: {WEAPON_DAMAGE['shotgun']}x5)", "price": 450, "ammo_grant": 6},
            {"type": "weapon", "id": "gatling", "name": f"Sau Nong Gatling Gun (DMG: {WEAPON_DAMAGE['gatling']})", "price": 750, "ammo_grant": 150},
            {"type": "merc", "id": "mercenary", "name": f"Thue De Tu Mafia (AK47) - [{merc_count}/5]", "price": merc_price, "ammo_grant": 0}
        ]
        
        card_y = shop_box.y + 70
        for item in shop_items:
            card_rect = pygame.Rect(shop_box.x + 25, card_y, shop_box.width - 50, 60)
            is_hover_c = card_rect.collidepoint(mouse_pos)
            
            try: pygame.draw.rect(screen, (25, 28, 35) if is_hover_c else (20, 22, 26), card_rect, 0, 12)
            except: pygame.draw.rect(screen, (25, 28, 35) if is_hover_c else (20, 22, 26), card_rect, 0)
            
            try: pygame.draw.rect(screen, COLOR_GOLD if is_hover_c else (50, 55, 60), card_rect, 2 if is_hover_c else 1, 12)
            except: pygame.draw.rect(screen, COLOR_GOLD if is_hover_c else (50, 55, 60), card_rect, 2 if is_hover_c else 1)
            
            w_img = WEAPON_SHOP_IMAGES.get(item["id"]) if item["type"] == "weapon" else None
            if w_img: screen.blit(w_img, (card_rect.x + 20, card_rect.y + 14))
                
            draw_text_vip(screen, item["name"], font_md, COLOR_MERCENARY if item["type"] == "merc" else COLOR_TEXT, card_rect.x + (85 if w_img else 25), card_rect.y + 20, 2)
            
            btn_buy_rect = pygame.Rect(card_rect.right - 140, card_rect.y + 12, 120, 36)
            is_hover_b = btn_buy_rect.collidepoint(mouse_pos)
            is_disabled = (item["type"] == "merc" and merc_count >= 5)
            can_afford = player_money >= item["price"] and not is_disabled
            
            btn_color = (50, 50, 52) if is_disabled else ((80, 40, 40) if not can_afford else ((155, 89, 182) if item["type"] == "merc" and is_hover_b else ((142, 68, 173) if item["type"] == "merc" else ((255, 230, 0) if is_hover_b else COLOR_GOLD))))
            
            try: pygame.draw.rect(screen, (255, 255, 255) if is_hover_b and can_afford else btn_color, btn_buy_rect, 0, 8)
            except: pygame.draw.rect(screen, (255, 255, 255) if is_hover_b and can_afford else btn_color, btn_buy_rect, 0)
            
            try: pygame.draw.rect(screen, btn_color, btn_buy_rect.inflate(-4, -4), 0, 6)
            except: pygame.draw.rect(screen, btn_color, btn_buy_rect.inflate(-4, -4), 0)
            
            price_str = "MAX OUT" if is_disabled else f"MUA: ${item['price']}"
            draw_text_vip(screen, price_str, font_sm, COLOR_BG if not is_disabled and can_afford else (170,170,170), btn_buy_rect.centerx - font_sm.size(price_str)[0]//2, btn_buy_rect.centery - 10, 0 if can_afford else 1)
            
            if mouse_clicked and is_hover_b and can_afford:
                player_money -= item["price"]
                if item["type"] == "weapon":
                    player.current_weapon = item["id"]; player_ammo[item["id"]] += item["ammo_grant"]
                elif item["type"] == "merc": mercenaries_list.append(Mercenary(player.grid_x, player.grid_y, idx=merc_count))
            card_y += 68
            
        btn_close_rect = pygame.Rect(shop_box.centerx - 100, shop_box.bottom - 50, 200, 40)
        is_hover_cl = btn_close_rect.collidepoint(mouse_pos)
        
        try: pygame.draw.rect(screen, (231, 76, 60) if is_hover_cl else (192, 57, 43), btn_close_rect, 0, 10)
        except: pygame.draw.rect(screen, (231, 76, 60) if is_hover_cl else (192, 57, 43), btn_close_rect, 0)
        
        draw_text_vip(screen, "THOAT (ESC)", font_md, COLOR_BG if is_hover_cl else COLOR_TEXT, btn_close_rect.centerx - font_md.size("THOAT (ESC)")[0]//2, btn_close_rect.centery - 10, 0 if is_hover_cl else 2)
        if mouse_clicked and is_hover_cl: game_state = "PLAYING"
        pygame.display.flip(); continue

    # --- CHẾ ĐỘ CHƠI CHÍNH ---
    if not game_over and not game_win: game_ticks += 1
    survival_seconds = game_ticks // 60

    if shoot_cooldown > 0: shoot_cooldown -= 1
    if flash_duration > 0: flash_duration -= 1
    if player.input_cooldown > 0: player.input_cooldown -= 1
    if shake_intensity > 0: shake_intensity -= 1
    if dmg_flash_timer > 0: dmg_flash_timer -= 1
    
    active_dt = []
    for dt in damage_texts:
        dt.update()
        if dt.lifetime > 0: active_dt.append(dt)
    damage_texts = active_dt

    active_shells = []
    for sh in shells:
        sh.update()
        if sh.lifetime > 0: active_shells.append(sh)
    shells = active_shells
    
    player_world_x = player.grid_x * TILE_SIZE + TILE_SIZE // 2
    player_world_y = player.grid_y * TILE_SIZE + TILE_SIZE // 2

    active_items = []
    for item in drop_items:
        item.update_magnet(player_world_x, player_world_y)
        if math.hypot(player_world_x - item.x, player_world_y - item.y) < 18:
            if item.type == "ammo":
                for k in player_ammo: player_ammo[k] += 60
            elif item.type == "health": player.hp = min(100, player.hp + 30)  
            else: player_money += item.value
        else: active_items.append(item)
    drop_items = active_items
    
    camera_x = max(0, min(player_world_x - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(player_world_y - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
    if SETTINGS["screen_shake"] and shake_intensity > 0:
        camera_x += random.randint(-shake_intensity, shake_intensity); camera_y += random.randint(-shake_intensity, shake_intensity)

    is_player_shooting, is_sprinting = False, False

    if not game_over and not game_win:
        current_wave = 2 if survival_seconds >= 50 else 1
        max_allowed_zombies = 25 if current_wave == 2 else 10
        spawn_rate_ticks = 150 if current_wave == 2 else 240 
        
        if game_ticks % spawn_rate_ticks == 0 and len(zombies_list) < max_allowed_zombies:
            while True:
                rx, ry = random.randint(2, GRID_WIDTH-2), random.randint(2, GRID_HEIGHT-2)
                if is_walkable(rx, ry) and abs(rx - player.grid_x) > 5 and abs(ry - player.grid_y) > 5:
                    heavy_chance = 0.55 if current_wave == 2 else 0.20
                    zombies_list.append(HeavyZombie(rx, ry) if random.random() < heavy_chance else Zombie(rx, ry))
                    break

        if survival_seconds >= 150 and not boss_spawned:
            while True:
                bx, by = random.randint(10, GRID_WIDTH-3), random.randint(10, GRID_HEIGHT-3)
                if is_walkable(bx, by) and abs(bx - player.grid_x) > 6:
                    zombies_list.append(BossZombie(bx, by)); boss_spawned = True; shake_intensity = 25; break

        for merc in mercenaries_list: merc.update(player, zombies_list)

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        
        simulated_mouse_pressed = mouse_buttons[0]
        simulated_mouse_x = mouse_pos[0]
        simulated_mouse_y = mouse_pos[1]
        simulated_k_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        simulated_k_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        simulated_k_up = keys[pygame.K_UP] or keys[pygame.K_w]
        simulated_k_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        simulated_k_shift = keys[pygame.K_LSHIFT]

        # [AUTO PLAY SIÊU GIỎI]
        if auto_play:
            closest_zom = None; min_z_dist = float('inf')
            for zb in zombies_list:
                dist = math.hypot(zb.grid_x - player.grid_x, zb.grid_y - player.grid_y)
                if dist < min_z_dist: min_z_dist = dist; closest_zom = zb
            
            closest_item = None; min_i_dist = float('inf')
            for it in drop_items:
                dist = math.hypot(it.grid_x - player.grid_x, it.grid_y - player.grid_y)
                if it.type == "health" and player.hp < 70: dist -= 15 
                if it.type == "ammo" and player_ammo[player.current_weapon] < 50: dist -= 10 
                if dist < min_i_dist: min_i_dist = dist; closest_item = it

            if closest_zom:
                simulated_mouse_x = closest_zom.grid_x * TILE_SIZE + TILE_SIZE // 2 - camera_x
                simulated_mouse_y = closest_zom.grid_y * TILE_SIZE + TILE_SIZE // 2 - camera_y
                if min_z_dist < 15: simulated_mouse_pressed = True
                if min_z_dist < 4.5: simulated_k_shift = True
                
                if player.input_cooldown == 0:
                    simulated_k_left = simulated_k_right = simulated_k_up = simulated_k_down = False
                    target_x, target_y = player.grid_x, player.grid_y
                    
                    if min_z_dist < 4.5: 
                        if closest_zom.grid_x < player.grid_x: target_x = player.grid_x + 3
                        elif closest_zom.grid_x > player.grid_x: target_x = player.grid_x - 3
                        if closest_zom.grid_y < player.grid_y: target_y = player.grid_y + 3
                        elif closest_zom.grid_y > player.grid_y: target_y = player.grid_y - 3
                    elif closest_item and min_i_dist < 10: 
                        target_x, target_y = closest_item.grid_x, closest_item.grid_y
                    elif min_z_dist > 7: 
                        target_x, target_y = closest_zom.grid_x, closest_zom.grid_y
                        
                    best_nx, best_ny = player.grid_x, player.grid_y
                    min_path_d = float('inf')
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = player.grid_x + dx, player.grid_y + dy
                        if is_walkable(nx, ny):
                            d = abs(nx - target_x) + abs(ny - target_y)
                            if d < min_path_d: min_path_d = d; best_nx, best_ny = nx, ny
                                
                    if best_nx < player.grid_x: simulated_k_left = True
                    elif best_nx > player.grid_x: simulated_k_right = True
                    elif best_ny < player.grid_y: simulated_k_up = True
                    elif best_ny > player.grid_y: simulated_k_down = True

        if simulated_k_shift and player.is_moving and player.stamina > 2:
            is_sprinting = True; player.stamina -= 0.7
        else:
            if player.stamina < 100: player.stamina += 0.3

        current_wp = player.current_weapon
        if simulated_mouse_pressed and player_ammo[current_wp] > 0 and not shop_btn_rect.collidepoint((simulated_mouse_x, simulated_mouse_y)) and not auto_btn_rect.collidepoint((simulated_mouse_x, simulated_mouse_y)):
            is_player_shooting = True
            mouse_world_x = simulated_mouse_x + camera_x
            mouse_world_y = simulated_mouse_y + camera_y
            dx, dy = mouse_world_x - player_world_x, mouse_world_y - player_world_y
            if math.sqrt(dx**2 + dy**2) > 25:
                if abs(dx) > abs(dy): player.direction = "right" if dx > 0 else "left"
                else: player.direction = "down" if dy > 0 else "up"

            if shoot_cooldown == 0:
                player_ammo[current_wp] -= 1
                target_world_coord = (mouse_world_x, mouse_world_y)
                flash_angle = math.atan2(dy, dx)
                
                # Cắt bớt tiếng khi xài Gatling để tránh sập Audio Driver
                if SETTINGS["sound_effects"]:
                    snd = get_weapon_sound(current_wp)
                    if snd:
                        # Throttle Gatling play less (play every 3 ticks) to keep audible
                        if current_wp != "gatling" or game_ticks % 3 == 0:
                            try: snd.play()
                            except: pass

                if current_wp == "shotgun":
                    for angle_offset in [-16, -8, 0, 8, 16]: bullets.append(Bullet(player_world_x, player_world_y, target_world_coord, angle_offset))
                    shells.append(DropShell(player_world_x, player_world_y))
                    shoot_cooldown = 42; shake_intensity = 14  
                elif current_wp == "gatling": 
                    bullets.append(Bullet(player_world_x, player_world_y, target_world_coord, random.uniform(-6, 6))) 
                    shells.append(DropShell(player_world_x, player_world_y))
                    shoot_cooldown = 3; shake_intensity = 4   
                elif current_wp == "uzi": 
                    bullets.append(Bullet(player_world_x, player_world_y, target_world_coord, random.uniform(-2, 2)))
                    shells.append(DropShell(player_world_x, player_world_y))
                    shoot_cooldown = 6; shake_intensity = 2  
                elif current_wp == "ak47":
                    bullets.append(Bullet(player_world_x, player_world_y, target_world_coord, 0))
                    shells.append(DropShell(player_world_x, player_world_y))
                    shoot_cooldown = 9; shake_intensity = 6
                else: 
                    bullets.append(Bullet(player_world_x, player_world_y, target_world_coord, 0))
                    shells.append(DropShell(player_world_x, player_world_y))
                    shoot_cooldown = 20; shake_intensity = 1
                flash_duration = 4; flash_pos = (int(player_world_x + math.cos(flash_angle) * 20), int(player_world_y + math.sin(flash_angle) * 20))

        player.is_moving = False
        new_px, new_py = player.grid_x, player.grid_y
        if player.input_cooldown == 0:
            moving_intent = False
            move_dir = player.direction
            if simulated_k_left: new_px -= 1; move_dir = "left"; moving_intent = True
            elif simulated_k_right: new_px += 1; move_dir = "right"; moving_intent = True
            elif simulated_k_up: new_py -= 1; move_dir = "up"; moving_intent = True
            elif simulated_k_down: new_py += 1; move_dir = "down"; moving_intent = True
            if moving_intent:
                player.is_moving = True
                if not is_player_shooting: player.direction = move_dir
                if is_walkable(new_px, new_py): player.grid_x, player.grid_y = new_px, new_py; player.input_cooldown = 4 if is_sprinting else 8

        # [TỐI ƯU CỰC ĐẠI]: Xoá phần tử chết bằng list mới, chống crash Array Bound
        alive_bullets = []
        new_zombies = []

        for bullet in bullets:
            bullet.update()
            if not bullet.alive: continue

            b_grid_x, b_grid_y = int(bullet.x // TILE_SIZE), int(bullet.y // TILE_SIZE)
            hit_something = False

            for zb in zombies_list:
                if zb.hp <= 0: continue
                if b_grid_x == zb.grid_x and b_grid_y == zb.grid_y:
                    base_damage = WEAPON_DAMAGE.get(player.current_weapon, 20)
                    if not bullet.is_friendly: base_damage = 40 
                    
                    dmg_color, dmg_string = (255, 255, 255), str(base_damage)
                    if zb.is_boss:
                        zb.hp -= base_damage; dmg_color = (155, 89, 182); dmg_string = f"DMG: {base_damage}" 
                        if zb.last_spawn_hp - zb.hp >= 75:
                            zb.last_spawn_hp = zb.hp
                            damage_texts.append(DamageText(zb.grid_x * TILE_SIZE, zb.grid_y * TILE_SIZE - 40, "SUMMON!!!", (255, 0, 0)))
                            for _ in range(2):
                                spawned_zom = False
                                for offset_x in [0, -1, 1, -2, 2]:
                                    for offset_y in [0, -1, 1, -2, 2]:
                                        sx, sy = zb.grid_x + offset_x, zb.grid_y + offset_y
                                        if is_walkable(sx, sy) and (sx, sy) != (player.grid_x, player.grid_y):
                                            if random.random() > 0.5: new_zombies.append(HeavyZombie(sx, sy))
                                            else: new_zombies.append(Zombie(sx, sy))
                                            spawned_zom = True; break
                                    if spawned_zom: break
                    elif zb.is_heavy:
                        dmg_taken, shield_broken = zb.take_damage_logic(base_damage)
                        dmg_string = f"{dmg_taken} (SHIELD BREAK)" if shield_broken else str(dmg_taken)
                        dmg_color = (52, 152, 219) if shield_broken else (230, 126, 34)
                    else:
                        zb.hp -= base_damage
                        if player.current_weapon in ["shotgun", "ak47"]: dmg_color = (255, 215, 0)
                    
                    world_hit_x = zb.grid_x * TILE_SIZE + TILE_SIZE // 2
                    world_hit_y = zb.grid_y * TILE_SIZE + TILE_SIZE // 4
                    damage_texts.append(DamageText(world_hit_x, world_hit_y, dmg_string, dmg_color))
                    hit_something = True
                    break

            if not hit_something: alive_bullets.append(bullet)

        bullets = alive_bullets
        zombies_list.extend(new_zombies)

        alive_zombies = []
        for zb in zombies_list:
            if zb.hp <= 0:
                if zb.is_boss: game_win = True
                elif zb.is_heavy:
                    drop_items.append(DropItem(zb.grid_x, zb.grid_y, "health")); player_money += 450  
                else:
                    drop_items.append(DropItem(zb.grid_x, zb.grid_y, "ammo"))
                    if random.random() > 0.6: drop_items.append(DropItem(zb.grid_x, zb.grid_y, "money", 150))
                    player_money += 100  
            else:
                zb.update_ai((player.grid_x, player.grid_y))
                zb.frame_index = (zb.frame_index + 0.15) % 4 if zb.is_moving else 0
                if player.grid_x == zb.grid_x and player.grid_y == zb.grid_y:
                    player.hp -= 3.5 if zb.is_boss else (1.8 if zb.is_heavy else 0.8)
                    dmg_flash_timer = 4 
                    if player.hp <= 0: game_over = True
                alive_zombies.append(zb)
        zombies_list = alive_zombies
        player.update_anim(is_sprinting)

    # --- RENDER THÀNH PHỐ ---
    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH):
            px, py = c * TILE_SIZE - camera_x, r * TILE_SIZE - camera_y
            if -TILE_SIZE <= px <= SCREEN_WIDTH and -TILE_SIZE <= py <= SCREEN_HEIGHT:
                cell_type = GAME_MAP[r][c]
                if cell_type != 0 and MAP_IMAGES[cell_type] is not None: screen.blit(MAP_IMAGES[cell_type], (px, py))
                else: 
                    if cell_type == 0: pygame.draw.rect(screen, (29, 31, 33), (px, py, TILE_SIZE, TILE_SIZE))

    for v_st in VERTICAL_STREETS:
        center_x_world = int((v_st + ROAD_WIDTH / 2) * TILE_SIZE)
        for r in range(GRID_HEIGHT):
            if r % 2 == 0:
                vx = center_x_world - camera_x; vy_start = r * TILE_SIZE - camera_y
                if -10 <= vx <= SCREEN_WIDTH + 10 and -TILE_SIZE <= vy_start <= SCREEN_HEIGHT + TILE_SIZE:
                    pygame.draw.line(screen, COLOR_ROAD_MARKING, (vx, vy_start + 5), (vx, vy_start + TILE_SIZE - 5), 2)

    for h_st in HORIZONTAL_STREETS:
        center_y_world = int((h_st + ROAD_WIDTH / 2) * TILE_SIZE)
        for c in range(GRID_WIDTH):
            if c % 2 == 0:
                vy = center_y_world - camera_y; vx_start = c * TILE_SIZE - camera_x
                if -TILE_SIZE <= vx_start <= SCREEN_WIDTH + TILE_SIZE and -10 <= vy <= SCREEN_HEIGHT + 10:
                    pygame.draw.line(screen, COLOR_ROAD_MARKING, (vx_start + 5, vy), (vx_start + TILE_SIZE - 5, vy), 2)

    for item in drop_items: item.draw(screen, camera_x, camera_y)
    for sh in shells: sh.draw(screen, camera_x, camera_y) 
    for bullet in bullets: bullet.draw(screen, camera_x, camera_y)
    for zb in zombies_list: zb.draw(screen, camera_x, camera_y)
    for mc in mercenaries_list: mc.draw(screen, camera_x, camera_y)
    player.draw(screen, camera_x, camera_y) 
    for dt in damage_texts: dt.draw(screen, camera_x, camera_y)

    if boss_spawned:
        boss_obj = next((z for z in zombies_list if z.is_boss), None)
        if boss_obj:
            rope_pulse = (rope_pulse + 1) % 60
            boss_w_x = boss_obj.grid_x * TILE_SIZE + TILE_SIZE // 2 - camera_x
            boss_w_y = boss_obj.grid_y * TILE_SIZE + TILE_SIZE // 2 - camera_y
            pl_w_x = player.grid_x * TILE_SIZE + TILE_SIZE // 2 - camera_x
            pl_w_y = player.grid_y * TILE_SIZE + TILE_SIZE // 2 - camera_y
            
            dist_rope = math.hypot(boss_w_x - pl_w_x, boss_w_y - pl_w_y)
            if dist_rope > 0:
                dash_length = 10; steps = int(dist_rope / dash_length)
                rope_intensity = (150 + int(math.sin(rope_pulse * 0.1) * 104)) / 255.0 
                rope_color = (int(155 * rope_intensity), int(89 * rope_intensity), int(182 * rope_intensity))
                for i in range(0, steps, 2):
                    start_p = (pl_w_x + (boss_w_x - pl_w_x) * (i / steps), pl_w_y + (boss_w_y - pl_w_y) * (i / steps))
                    end_p = (pl_w_x + (boss_w_x - pl_w_x) * ((i+1) / steps), pl_w_y + (boss_w_y - pl_w_y) * ((i+1) / steps))
                    pygame.draw.line(screen, rope_color, start_p, end_p, 3)

    if flash_duration > 0 and not game_over and not game_win:
        fx, fy = int(flash_pos[0] - camera_x), int(flash_pos[1] - camera_y)
        pygame.draw.circle(screen, (255, 255, 255), (fx, fy), 4)
        for _ in range(3):
            t_angle, length = flash_angle + random.uniform(-0.4, 0.4), random.randint(12, 22)
            pygame.draw.line(screen, COLOR_FLASH, (fx, fy), (fx + int(math.cos(t_angle) * length), fy + int(math.sin(t_angle) * length)), 3)

    if dmg_flash_timer > 0: screen.blit(red_flash_overlay, (0, 0))

    screen.blit(hud_glass_panel, (15, 15))
    
    hud_hp_ratio = max(0, player.hp) / 100
    hud_hp_color = (46, 204, 113) if hud_hp_ratio > 0.5 else ((241, 196, 15) if hud_hp_ratio > 0.25 else (231, 76, 60))
    if hud_hp_ratio > 0:
        try: pygame.draw.rect(screen, hud_hp_color, (15 + 21, 15 + 23, int(228 * hud_hp_ratio), 18), 0, 8)
        except: pygame.draw.rect(screen, hud_hp_color, (15 + 21, 15 + 23, int(228 * hud_hp_ratio), 18), 0)
        
        try: pygame.draw.rect(screen, (255, 255, 255, 90), (15 + 21, 15 + 23, int(228 * hud_hp_ratio), 8), 0, 8)
        except: pass # Highlight VIP an toàn
    
    draw_text_vip(screen, f"HP: {int(max(0, player.hp))}%", font_md, COLOR_BG, 15 + 135 - font_md.size(f"HP: {int(max(0, player.hp))}%")[0]//2, 15 + 21, 0)

    if player.stamina > 0:
        try: pygame.draw.rect(screen, COLOR_STAMINA, (15 + 21, 15 + 53, int(228 * (player.stamina/100)), 8), 0, 4)
        except: pygame.draw.rect(screen, COLOR_STAMINA, (15 + 21, 15 + 53, int(228 * (player.stamina/100)), 8), 0)
        
    draw_text_vip(screen, "STAMINA (LSHIFT)", font_sm, (180, 190, 200), 15 + 20, 15 + 65, 2)
    draw_text_vip(screen, f"$ {player_money}", font_lg, COLOR_GOLD, 15 + 20, 15 + 85, 2)
    draw_text_vip(screen, f"AMMO: {player_ammo[player.current_weapon]} V", font_md, COLOR_AMMO, 15 + 140, 15 + 92, 2)
    draw_text_vip(screen, f"DE TU: {len(mercenaries_list)}/5", font_sm, COLOR_MERCENARY, 15 + 20, 15 + 112, 2)
    
    screen.blit(time_panel_bg, (SCREEN_WIDTH // 2 - 125, 15))
    wave_name = f"DOT 2 (NGUY HIEM)" if survival_seconds >= 50 else "DOT 1 (KHOAN THAI)"
    if boss_spawned: wave_name = "WARNING: BOSS ENCOUNTER" 
    txt_str = f"TIME: {survival_seconds}s | {wave_name}"
    draw_text_vip(screen, txt_str, font_sm, COLOR_TEXT, SCREEN_WIDTH // 2 - font_sm.size(txt_str)[0]//2, 15 + 21 - font_sm.size(txt_str)[1]//2, 2)

    screen.blit(mm_panel_bg, (SCREEN_WIDTH - (mm_w + 39), 15))
    mm_off_x = SCREEN_WIDTH - (mm_w + 39) + 12; mm_off_y = 15 + 12
    
    try: pygame.draw.rect(screen, (30, 33, 36), (mm_off_x, mm_off_y, mm_w, mm_h), 0, 4)
    except: pygame.draw.rect(screen, (30, 33, 36), (mm_off_x, mm_off_y, mm_w, mm_h), 0)
    
    for r in range(GRID_HEIGHT):
        for c in range(GRID_WIDTH):
            if GAME_MAP[r][c] == 1: pygame.draw.rect(screen, (85, 90, 95), (mm_off_x + c * MM_SCALE, mm_off_y + r * MM_SCALE, MM_SCALE, MM_SCALE))
                
    pygame.draw.rect(screen, COLOR_GREEN, (mm_off_x + player.grid_x * MM_SCALE, mm_off_y + player.grid_y * MM_SCALE, MM_SCALE, MM_SCALE))
    for zb in zombies_list: pygame.draw.rect(screen, COLOR_RED, (mm_off_x + zb.grid_x * MM_SCALE, mm_off_y + zb.grid_y * MM_SCALE, MM_SCALE, MM_SCALE))
    for mc in mercenaries_list: pygame.draw.rect(screen, COLOR_MERCENARY, (mm_off_x + mc.grid_x * MM_SCALE, mm_off_y + mc.grid_y * MM_SCALE, MM_SCALE, MM_SCALE))

    # NÚT BẤM (VIP BO GÓC)
    is_h_shop = shop_btn_rect.collidepoint(mouse_pos)
    try: pygame.draw.rect(screen, (255,255,255) if is_h_shop else COLOR_GOLD, shop_btn_rect, 0, 14)
    except: pygame.draw.rect(screen, (255,255,255) if is_h_shop else COLOR_GOLD, shop_btn_rect, 0)
    
    try: pygame.draw.rect(screen, COLOR_GOLD if is_h_shop else (211, 84, 0), shop_btn_rect.inflate(-4,-4), 0, 10)
    except: pygame.draw.rect(screen, COLOR_GOLD if is_h_shop else (211, 84, 0), shop_btn_rect.inflate(-4,-4), 0)
    
    draw_text_vip(screen, "SHOP [P]", font_md, (15,15,20) if is_h_shop else COLOR_BG, shop_btn_rect.centerx - font_md.size("SHOP [P]")[0]//2, shop_btn_rect.centery - 10, 0 if is_h_shop else 2)
    if mouse_clicked and is_h_shop and not game_over and not game_win: previous_state = "PLAYING"; game_state = "SHOP"
        
    is_h_auto = auto_btn_rect.collidepoint(mouse_pos)
    b_auto_c = COLOR_GREEN if auto_play else (100, 100, 105)
    
    try: pygame.draw.rect(screen, (255,255,255) if is_h_auto else b_auto_c, auto_btn_rect, 0, 14)
    except: pygame.draw.rect(screen, (255,255,255) if is_h_auto else b_auto_c, auto_btn_rect, 0)
    
    try: pygame.draw.rect(screen, b_auto_c if is_h_auto else (max(0, b_auto_c[0]-40), max(0, b_auto_c[1]-40), max(0, b_auto_c[2]-40)), auto_btn_rect.inflate(-4,-4), 0, 10)
    except: pygame.draw.rect(screen, b_auto_c if is_h_auto else (max(0, b_auto_c[0]-40), max(0, b_auto_c[1]-40), max(0, b_auto_c[2]-40)), auto_btn_rect.inflate(-4,-4), 0)
    
    draw_text_vip(screen, "AUTO [O]", font_md, (15,15,20) if is_h_auto else COLOR_BG, auto_btn_rect.centerx - font_md.size("AUTO [O]")[0]//2, auto_btn_rect.centery - 10, 0 if is_h_auto else 2)
    if mouse_clicked and is_h_auto and not game_over and not game_win: auto_play = not auto_play

    if game_over:
        screen.blit(go_overlay, (0, 0)) 
        draw_text_vip(screen, "GAME OVER", font_title, COLOR_RED, SCREEN_WIDTH // 2 - font_title.size("GAME OVER")[0] // 2, SCREEN_HEIGHT // 2 - 40, 4)
        if (pygame.time.get_ticks() // 500) % 2 == 0: 
            draw_text_vip(screen, "Nhan phim [ R ] de Tai Thiet Lap", font_lg, COLOR_GOLD, SCREEN_WIDTH // 2 - font_lg.size("Nhan phim [ R ] de Tai Thiet Lap")[0] // 2, SCREEN_HEIGHT // 2 + 30, 2)

    if game_win:
        screen.blit(win_overlay, (0, 0))
        draw_text_vip(screen, "CHIEN THANG", font_title, COLOR_GREEN, SCREEN_WIDTH // 2 - font_title.size("CHIEN THANG")[0] // 2, SCREEN_HEIGHT // 2 - 40, 4)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            draw_text_vip(screen, "Nhan phim [ R ] de choi lai van moi", font_lg, COLOR_GOLD, SCREEN_WIDTH // 2 - font_lg.size("Nhan phim [ R ] de choi lai van moi")[0] // 2, SCREEN_HEIGHT // 2 + 30, 2)

    pygame.display.flip()

pygame.quit()
sys.exit()