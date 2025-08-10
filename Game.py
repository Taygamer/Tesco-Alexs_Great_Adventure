"""
# Tesco:Alex's Great Adventure
"""

import tkinter as tk
from tkinter import simpledialog, messagebox, PhotoImage
import os, sys, json, time, math, random, hashlib, binascii, io
from PIL import Image, ImageDraw, ImageTk

# Optional richer sound via pygame
USE_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    USE_PYGAME = True
except Exception:
    USE_PYGAME = False

# winsound fallback for Windows
USE_WINSOUND = sys.platform.startswith("win")
if USE_WINSOUND:
    try:
        import winsound
    except Exception:
        USE_WINSOUND = False

# -------------------------
# Persistence
# -------------------------
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {"users": {}, "current_user": None}
    try:
        with open(USERS_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        try:
            os.rename(USERS_FILE, USERS_FILE + ".bak")
        except Exception:
            pass
        return {"users": {}, "current_user": None}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    else:
        salt = binascii.unhexlify(salt)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf8"), salt, 150000)
    return binascii.hexlify(dk).decode("ascii"), binascii.hexlify(salt).decode("ascii")

def verify_password(stored_hash, stored_salt, attempt):
    dk, _ = hash_password(attempt, salt=stored_salt)
    return dk == stored_hash

# -------------------------
# Sound generation & helpers
# -------------------------
_sound_cache = {}
def _synth_wav(path, freq=440, ms=120, vol=0.12):
    import wave, struct
    sr = 22050
    n = int(sr * ms / 1000.0)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        max_a = int(32767 * vol)
        for i in range(n):
            t = i / sr
            s = int(max_a * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", s))

# prepare small wavs (if pygame)
if USE_PYGAME:
    tmp = os.path.join(os.path.dirname(__file__), "__vn_sounds2__")
    os.makedirs(tmp, exist_ok=True)
    try:
        _synth_wav(os.path.join(tmp, "coin.wav"), freq=1200, ms=90)
        _synth_wav(os.path.join(tmp, "crash.wav"), freq=120, ms=350)
        _synth_wav(os.path.join(tmp, "engine.wav"), freq=160, ms=300)
        _synth_wav(os.path.join(tmp, "click.wav"), freq=800, ms=60)
        _sound_cache["coin"] = os.path.join(tmp, "coin.wav")
        _sound_cache["crash"] = os.path.join(tmp, "crash.wav")
        _sound_cache["engine"] = os.path.join(tmp, "engine.wav")
        _sound_cache["click"] = os.path.join(tmp, "click.wav")
    except Exception:
        USE_PYGAME = False

def play_sound(name):
    if USE_PYGAME and name in _sound_cache:
        try:
            s = pygame.mixer.Sound(_sound_cache[name])
            s.play()
        except Exception:
            pass
    elif USE_WINSOUND:
        try:
            winsound.MessageBeep()
        except Exception:
            pass
    else:
        # no-op
        pass

# -------------------------
# Game constants
# -------------------------
WIDTH, HEIGHT = 1000, 640
FPS = 60
FONT = ("Consolas", 13)
LANES = 3

# shop & cosmetics
BASE_SHOP = [
    {"id":"sneakers","name":"Sneakers","+":"speed +0.5","desc":"+0.5 speed","cost":70,"type":"upgrade"},
    {"id":"mask","name":"Mask","+":"detect -20%","desc":"-20% detection","cost":90,"type":"upgrade"},
    {"id":"wallet2","name":"Wallet x2","desc":"Double coin rewards","cost":220,"type":"upgrade"},
]
ALEX_COS = [
    {"id":"alex_grey","name":"Grey Shirt","cost":0,"category":"alex","color":(120,120,120)},
    {"id":"alex_black","name":"Black Jacket","cost":80,"category":"alex","color":(30,30,30)},
    {"id":"alex_red","name":"Red Tee","cost":110,"category":"alex","color":(200,40,40)},
]
VAN_COS = [
    {"id":"van_blue","name":"Blue Van","cost":0,"category":"van","color":(10,70,150)},
    {"id":"van_white","name":"White Van","cost":100,"category":"van","color":(240,240,240)},
    {"id":"van_stripe","name":"Stripe Skin","cost":160,"category":"van","color":(200,20,20)},
]
SHOP_ITEMS = BASE_SHOP + ALEX_COS + VAN_COS

# -------------------------
# Pixel-art generator
# -------------------------
SPR = 64  # frame size

def new_canvas(sz=SPR): return Image.new("RGBA",(sz,sz),(0,0,0,0))

def generate_alex_frames(base_color=(120,120,120), frames=6):
    out=[]
    for i in range(frames):
        im = new_canvas()
        d = ImageDraw.Draw(im)
        bob = int(math.sin(i/frames * 2*math.pi) * 2)
        # torso
        d.rectangle([18, 24+bob, 46, 46+bob], fill=base_color, outline=(0,0,0))
        # pants
        d.rectangle([18, 46+bob, 46, 58+bob], fill=(20,20,20))
        # head
        d.rectangle([24, 12+bob, 40, 26+bob], fill=(255,214,170), outline=(0,0,0))
        # hair
        d.rectangle([22, 8+bob, 42, 16+bob], fill=(30,30,30))
        # beard
        d.rectangle([24, 22+bob, 40, 26+bob], fill=(18,18,18))
        # piercings occasionally
        if i % 3 == 0:
            d.point((28, 19+bob), fill=(220,220,255))
        # shoes
        d.rectangle([18, 58+bob, 30, 64+bob], fill=(10,10,10))
        d.rectangle([34, 58+bob, 46, 64+bob], fill=(10,10,10))
        out.append(im)
    return out

def generate_worker_frames(color=(30,100,200), frames=4):
    out=[]
    for i in range(frames):
        im = new_canvas()
        d = ImageDraw.Draw(im)
        bob = int(math.sin(i/frames * 2*math.pi) * 2)
        d.rectangle([18, 22+bob, 46, 44+bob], fill=color, outline=(0,0,0))
        d.rectangle([24, 12+bob, 40, 26+bob], fill=(255,224,185), outline=(0,0,0))
        if i % 2 == 0:
            d.rectangle([20, 44+bob, 30, 60+bob], fill=(30,30,30))
            d.rectangle([34, 46+bob, 46, 60+bob], fill=(30,30,30))
        else:
            d.rectangle([20, 46+bob, 30, 60+bob], fill=(30,30,30))
            d.rectangle([34, 44+bob, 46, 60+bob], fill=(30,30,30))
        # Tesco badge
        d.rectangle([30, 28+bob, 34, 32+bob], fill=(255,255,255))
        out.append(im)
    return out

def generate_van_frames(vcolor=(10,70,150), frames=3):
    out=[]
    for i in range(frames):
        im = new_canvas()
        d = ImageDraw.Draw(im)
        d.rectangle([6, 20, 58, 44], fill=vcolor, outline=(0,0,0))
        d.rectangle([10, 22, 26, 32], fill=(210,230,255))
        d.rectangle([30, 22, 52, 32], fill=(210,230,255))
        # wheels animate small offset
        if i % 2 == 0:
            d.ellipse([10, 40, 18, 48], fill=(30,30,30))
            d.ellipse([42, 40, 50, 48], fill=(30,30,30))
        else:
            d.ellipse([9, 41, 17, 49], fill=(30,30,30))
            d.ellipse([43, 39, 51, 47], fill=(30,30,30))
        if i % 2 == 0:
            d.line([8, 28, 56, 28], fill=(255,255,255))
        out.append(im)
    return out

def generate_cone(): 
    im=new_canvas()
    d=ImageDraw.Draw(im)
    d.polygon([(32,16),(18,48),(46,48)], fill=(255,150,40), outline=(0,0,0))
    d.rectangle([26,40,38,44], fill=(255,220,180))
    return im

def generate_crate():
    im=new_canvas()
    d=ImageDraw.Draw(im)
    d.rectangle([12,18,52,50], fill=(150,100,50), outline=(0,0,0))
    d.line([12,30,52,30], fill=(110,70,40))
    d.line([32,18,32,50], fill=(110,70,40))
    return im

def generate_coin_frames(frames=8):
    out=[]
    for i in range(frames):
        im = new_canvas()
        d = ImageDraw.Draw(im)
        # coin is a small circle near center, rotate highlight to fake spin
        r = 10
        cx, cy = 32, 32
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255,215,0), outline=(160,120,0))
        # highlight line rotates
        angle = i / frames * 2 * math.pi
        hx = cx + int(math.cos(angle)*6)
        hy = cy - int(math.sin(angle)*6)
        d.point((hx, hy), fill=(255,255,220))
        out.append(im)
    return out

# Generate everything and convert to Tk
ALEX_PIL = generate_alex_frames((120,120,120), frames=6)
WORKER_PIL = generate_worker_frames((30,100,200), frames=4)
VAN_PIL = generate_van_frames((10,70,150), frames=3)
CONE_PIL = generate_cone()
CRATE_PIL = generate_crate()
COIN_PIL = generate_coin_frames(8)

def pil_to_tk(img):
    return ImageTk.PhotoImage(img)

# single conversion after Tk root created (we'll do in app init)
# store PIL base as globals for tinting
ALEX_BASE = ALEX_PIL
WORKER_BASE = WORKER_PIL
VAN_BASE = VAN_PIL
CONE_BASE = CONE_PIL
CRATE_BASE = CRATE_PIL
COIN_BASE = COIN_PIL

# -------------------------
# Entities
# -------------------------
class TopPlayer:
    def __init__(self, tkassets, profile):
        self.x = 80; self.y = HEIGHT//2 - 30
        self.speed = 2.0
        self.stamina = 100
        self.score = 0.0
        self.coins_collected = 0
        self.detect_radius = 110
        self.anim_i = 0; self.anim_t = 0.0
        self.tk = tkassets
        self.profile = profile
        self.apply_profile()
    def apply_profile(self):
        self.speed = 2.0
        self.detect_radius = 110
        self.score_mult = 1.0
        for it in self.profile.get("owned",[]):
            if it == "sneakers": self.speed += 0.5
            if it == "mask": self.detect_radius *= 0.8
            if it == "wallet2": self.score_mult = 2.0
    def update(self, dt, keys):
        sx = 0; sy = 0
        if keys.get("left"): sx -=1
        if keys.get("right"): sx +=1
        if keys.get("up"): sy -=1
        if keys.get("down"): sy +=1
        sprint = keys.get("sprint")
        spd = self.speed
        if sprint and self.stamina > 1:
            spd *= 1.6
            self.stamina = max(0, self.stamina - 20*dt)
        else:
            self.stamina = min(100, self.stamina + 12*dt)
        if sx !=0 and sy !=0: spd *= 0.7071
        self.x = clamp(self.x + sx * spd * dt * 60, 0, WIDTH-64)
        self.y = clamp(self.y + sy * spd * dt * 60, 0, HEIGHT-80)
        self.score += dt * 6 * self.score_mult
        self.anim_t += dt
        if self.anim_t > 0.12:
            self.anim_t = 0
            self.anim_i = (self.anim_i + 1) % len(self.tk['alex_frames'])
    def draw(self, c):
        # apply cosmetic tint if needed
        equip = self.profile.get("equipped", {}).get("alex", "alex_grey")
        color = None
        for it in ALEX_COS:
            if it['id'] == equip:
                color = it.get("color")
        frame = ALEX_BASE[self.anim_i]
        if color:
            tmp = frame.copy()
            draw = ImageDraw.Draw(tmp)
            draw.rectangle([18,24,46,46], fill=tuple(color)+(255,))
            imgtk = pil_to_tk(tmp); c.create_image(int(self.x), int(self.y), image=imgtk, anchor="nw")
            c.image_cache.append(imgtk)
        else:
            c.create_image(int(self.x), int(self.y), image=self.tk['alex_frames'][self.anim_i], anchor="nw")

class TopWorker:
    def __init__(self, x, y, tkassets):
        self.x=x; self.y=y; self.tk=tkassets
        self.path = self._gen()
        self.pidx=0; self.chasing=False
        self.speed=1.0; self.anim_i=0; self.anim_t=0.0
    def _gen(self):
        pts=[]
        cx,cy = self.x, self.y
        for _ in range(4):
            pts.append((clamp(cx + random.randint(-120,120), 100, WIDTH-160),
                        clamp(cy + random.randint(-80,80), 60, HEIGHT-120)))
        return pts
    def update(self, dt, player):
        dx = player.x - self.x; dy = player.y - self.y
        dist = math.hypot(dx,dy)
        if dist <= player.detect_radius and random.random() < 0.95:
            self.chasing = True
        if self.chasing:
            ang = math.atan2(player.y - self.y, player.x - self.x)
            self.x += math.cos(ang) * self.speed * 1.3 * dt * 60
            self.y += math.sin(ang) * self.speed * 1.3 * dt * 60
            if dist > 420:
                self.chasing = False; self.pidx=0
        else:
            if not self.path: return
            tx,ty = self.path[self.pidx]
            dx = tx - self.x; dy = ty - self.y; d=math.hypot(dx,dy)
            if d < 6: self.pidx=(self.pidx+1)%len(self.path)
            else:
                ang = math.atan2(dy,dx)
                self.x += math.cos(ang) * self.speed * dt * 60
                self.y += math.sin(ang) * self.speed * dt * 60
        self.anim_t += dt
        if self.anim_t > 0.14:
            self.anim_t = 0; self.anim_i = (self.anim_i + 1) % len(self.tk['worker_frames'])
    def draw(self, c):
        c.create_image(int(self.x), int(self.y), image=self.tk['worker_frames'][self.anim_i], anchor="nw")

class VanTop:
    def __init__(self, x, y, tkassets, profile):
        self.x=x; self.y=y; self.tk=tkassets; self.profile=profile
        self.anim_i=0; self.anim_t=0.0; self.stolen=False
    def update(self, dt):
        self.anim_t += dt
        if self.anim_t > 0.12:
            self.anim_t = 0; self.anim_i = (self.anim_i + 1) % len(self.tk['van_frames'])
    def draw(self, c):
        equip = self.profile.get("equipped",{}).get("van", "van_blue")
        color = None
        for it in VAN_COS:
            if it['id'] == equip:
                color = it.get("color")
        frame = VAN_BASE[self.anim_i]
        if color:
            tmp = frame.copy(); draw=ImageDraw.Draw(tmp)
            draw.rectangle([6, 20, 58, 44], fill=tuple(color)+(255,))
            imgtk = pil_to_tk(tmp); c.create_image(int(self.x), int(self.y), image=imgtk, anchor="nw"); c.image_cache.append(imgtk)
        else:
            c.create_image(int(self.x), int(self.y), image=self.tk['van_frames'][self.anim_i], anchor="nw")

# Runner entities
class RunnerVan:
    def __init__(self, tkassets, profile):
        self.tk = tkassets; self.profile = profile
        self.lane = LANES//2; self.target = self.lane
        self.width = 120; self.height = 84
        self.x=0; self.y=0; self.anim_i=0; self.anim_t=0.0
    def set_position(self, lane_x, base_y):
        self.x = lane_x - self.width//2; self.y = base_y - self.height//2
    def update(self, dt):
        self.anim_t += dt
        if self.anim_t > 0.12:
            self.anim_t = 0; self.anim_i = (self.anim_i + 1) % len(self.tk['van_frames'])
    def draw(self, c, lane_x, base_y):
        self.set_position(lane_x, base_y)
        equip = self.profile.get("equipped",{}).get("van","van_blue")
        color=None
        for it in VAN_COS:
            if it['id']==equip: color=it['color']
        frame = VAN_BASE[self.anim_i]
        if color:
            tmp = frame.copy(); draw = ImageDraw.Draw(tmp)
            draw.rectangle([6, 20, 58, 44], fill=tuple(color)+(255,))
            imgtk = pil_to_tk(tmp); c.create_image(int(self.x), int(self.y), image=imgtk, anchor="nw"); c.image_cache.append(imgtk)
        else:
            c.create_image(int(self.x), int(self.y), image=self.tk['van_frames'][self.anim_i], anchor="nw")

class RunnerObstacle:
    def __init__(self, lane, kind, tkassets):
        self.lane=lane; self.kind=kind; self.tk=tkassets
        sizes={"worker":(48,48),"cone":(36,36),"crate":(42,42)}
        self.w,self.h = sizes.get(kind,(44,44))
        self.x=0; self.y=-200
    def set_lane_x(self, lane_x):
        self.x = lane_x - self.w//2
    def update(self, dt, speed):
        self.y += speed * dt
    def draw(self, c):
        if self.kind=="worker":
            c.create_image(int(self.x), int(self.y), image=self.tk['worker_frames'][0], anchor="nw")
        elif self.kind=="cone":
            c.create_image(int(self.x), int(self.y), image=self.tk['cone'], anchor="nw")
        else:
            c.create_image(int(self.x), int(self.y), image=self.tk['crate'], anchor="nw")
    def bbox(self): return (self.x, self.y, self.x+self.w, self.y+self.h)

class Coin:
    def __init__(self, lane, tkassets):
        self.lane = lane; self.tk = tkassets
        self.w = 28; self.h = 28
        self.x=0; self.y = -120
        self.anim_i=0; self.anim_t=0.0
    def set_lane_x(self, lane_x):
        self.x = lane_x - self.w//2
    def update(self, dt, speed):
        self.y += speed * dt
        self.anim_t += dt
        if self.anim_t > 0.08:
            self.anim_t = 0; self.anim_i = (self.anim_i + 1) % len(self.tk['coin_frames'])
    def draw(self, c):
        c.create_image(int(self.x), int(self.y), image=self.tk['coin_frames'][self.anim_i], anchor="nw")
    def bbox(self): return (self.x, self.y, self.x+self.w, self.y+self.h)

# -------------------------
# Utility
# -------------------------
def clamp(v,a,b): return max(a,min(b,v))
def rects_overlap(a,b):
    ax1,ay1,ax2,ay2 = a; bx1,by1,bx2,by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)

# -------------------------
# Main App
# -------------------------
class VanSnatcherApp:
    def __init__(self, root):
        self.root = root; self.root.title("Tesco:Alex's Great Adventure")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#111")
        self.canvas.pack()
        # convert PIL frames to Tk PhotoImages for canvas rendering
        self.tk_assets = {
            'alex_frames': [pil_to_tk(im) for im in ALEX_BASE],
            'worker_frames': [pil_to_tk(im) for im in WORKER_BASE],
            'van_frames': [pil_to_tk(im) for im in VAN_BASE],
            'cone': pil_to_tk(CONE_BASE),
            'crate': pil_to_tk(CRATE_BASE),
            'coin_frames': [pil_to_tk(im) for im in COIN_BASE],
        }
        # load user data
        self.data = load_users()
        if "users" not in self.data: self.data["users"] = {}
        self.current = self.data.get("current_user")
        self.profile = None
        if self.current:
            p = self.data["users"].get(self.current)
            if p and p.get("session_active"):
                self.profile = p
        # game state
        self.mode = "login"  # login, menu, shop, topdown, runner
        self.keys = {}
        self.last = time.time()
        self.top_player = None
        self.top_workers = []
        self.van_top = None
        self.runner_van = None
        self.obstacles = []
        self.coins = []
        self.scroll_speed = 220.0
        self.obs_timer = 0.0
        self.obs_interval = 1.0
        self.runner_score = 0.0
        self.canvas.image_cache = []  # keep refs to PhotoImage
        self.bind_keys()
        # start screen
        if self.profile:
            self.show_menu()
        else:
            self.show_login()
        self.root.after(int(1000/FPS), self.loop)

    # ---------- UI screens ----------
    def show_login(self):
        self.mode = "login"; self.canvas.delete("all"); self.canvas.image_cache.clear()
        # animated background: moving stripes
        self.canvas.create_text(WIDTH//2, 72, text="Tesco:Alex's Great Adventure — LOG IN / SIGN UP", font=("Consolas",22), fill="#fff")
        bx, by, bw, bh = WIDTH//2 - 120, 180, 240, 50
        r1 = self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#2a9d8f", outline="")
        self.canvas.create_text(bx+bw//2, by+bh//2, text="Login", font=("Consolas", 16, "bold"))
        r2 = self.canvas.create_rectangle(bx, by+80, bx+bw, by+80+bh, fill="#e9c46a", outline="")
        self.canvas.create_text(bx+bw//2, by+80+bh//2, text="Sign up", font=("Consolas", 16, "bold"))
        r3 = self.canvas.create_rectangle(bx, by+160, bx+bw, by+160+bh, fill="#ef476f", outline="")
        self.canvas.create_text(bx+bw//2, by+160+bh//2, text="Quit", font=("Consolas", 16, "bold"))
        self.canvas.tag_bind(r1, "<Button-1>", lambda e: self.login_dialog())
        self.canvas.tag_bind(r2, "<Button-1>", lambda e: self.signup_dialog())
        self.canvas.tag_bind(r3, "<Button-1>", lambda e: self.root.destroy())

    def login_dialog(self):
        username = simpledialog.askstring("Login", "Username:", parent=self.root)
        if not username: return
        password = simpledialog.askstring("Login", "Password:", show="*", parent=self.root)
        if password is None: return
        user = self.data["users"].get(username)
        if not user:
            messagebox.showerror("Login", "User not found.")
            return
        if verify_password(user["pw_hash"], user["pw_salt"], password):
            self.current = username; self.profile = user
            self.profile["session_active"] = True
            self.data["current_user"] = username
            save_users(self.data)
            play_sound("click")
            messagebox.showinfo("Welcome", f"Welcome back, {username}!")
            self.show_menu()
        else:
            messagebox.showerror("Login", "Incorrect password.")

    def signup_dialog(self):
        username = simpledialog.askstring("Sign up", "Pick a username:", parent=self.root)
        if not username: return
        if username in self.data["users"]:
            messagebox.showerror("Sign up", "Username already exists.")
            return
        password = simpledialog.askstring("Sign up", "Pick a password:", show="*", parent=self.root)
        if password is None: return
        h,s = hash_password(password)
        profile = {"pw_hash":h, "pw_salt":s, "coins":0, "highscore":0, "owned":[], "equipped":{"alex":"alex_grey","van":"van_blue"}, "multiplier":1.0, "session_active":True}
        self.data["users"][username] = profile
        self.data["current_user"] = username
        save_users(self.data)
        self.current = username; self.profile = profile
        play_sound("click"); messagebox.showinfo("Account", "Account created and logged in.")
        self.show_menu()

    def show_menu(self):
        self.mode = "menu"; self.canvas.delete("all"); self.canvas.image_cache.clear()
        self.canvas.create_text(WIDTH//2, 64, text=f"Tesco:Alex's Great Adventure — {self.current}", font=("Consolas",24), fill="#fff")
        bx,by,bw,bh = WIDTH//2-140, 160, 280, 56
        r1 = self.canvas.create_rectangle(bx,by,bx+bw,by+bh, fill="#2a9d8f")
        self.canvas.create_text(bx+bw//2, by+bh//2, text="Play", font=("Consolas",18,"bold"))
        r2 = self.canvas.create_rectangle(bx,by+90,bx+bw,by+90+bh, fill="#e9c46a")
        self.canvas.create_text(bx+bw//2, by+90+bh//2, text="Shop", font=("Consolas",18,"bold"))
        r3 = self.canvas.create_rectangle(bx,by+180,bx+bw,by+180+bh, fill="#8ecae6")
        self.canvas.create_text(bx+bw//2, by+180+bh//2, text="Log out", font=("Consolas",16,"bold"))
        r4 = self.canvas.create_rectangle(bx,by+270,bx+bw,by+270+bh, fill="#ef476f")
        self.canvas.create_text(bx+bw//2, by+270+bh//2, text="Quit", font=("Consolas",16,"bold"))
        self.canvas.tag_bind(r1, "<Button-1>", lambda e: self.start_topdown())
        self.canvas.tag_bind(r2, "<Button-1>", lambda e: self.open_shop())
        self.canvas.tag_bind(r3, "<Button-1>", lambda e: self.logout())
        self.canvas.tag_bind(r4, "<Button-1>", lambda e: self.root.destroy())
        coins = self.profile.get("coins",0); hs = self.profile.get("highscore",0)
        equip = self.profile.get("equipped",{})
        self.canvas.create_text(WIDTH//2, 520, text=f"Coins: {coins}   Best: {hs}   Alex: {equip.get('alex')}   Van: {equip.get('van')}", font=("Consolas",12), fill="#ddd")

    def logout(self):
        if self.current:
            self.data["users"][self.current] = self.profile
            self.profile["session_active"] = False
            self.data["current_user"] = None
            save_users(self.data)
        self.current = None; self.profile = None
        self.show_login()

    def open_shop(self):
        self.mode = "shop"; self.canvas.delete("all"); self.canvas.image_cache.clear()
        self.canvas.create_text(WIDTH//2, 44, text="SHOP — Cosmetics & Upgrades", font=("Consolas",20), fill="#fff")
        starty = 100
        for idx, item in enumerate(SHOP_ITEMS):
            y = starty + idx*72
            self.canvas.create_rectangle(40, y, WIDTH-40, y+60, fill="#2b2b2b", outline="#444")
            self.canvas.create_text(60, y+18, anchor="w", text=item['name'], font=("Consolas", 12), fill="#fff")
            self.canvas.create_text(60, y+38, anchor="w", text=item.get("desc",""), font=("Consolas", 10), fill="#ccc")
            cost = item.get("cost", 0)
            bx1 = WIDTH-220; bx2 = WIDTH-140
            rect = self.canvas.create_rectangle(bx1, y+12, bx2, y+52, fill="#2a9d8f")
            self.canvas.create_text((bx1+bx2)//2, y+32, text=f"Buy {cost}", font=("Consolas", 12))
            self.canvas.tag_bind(rect, "<Button-1>", lambda e, it=item: self.buy_item(it))
        back = self.canvas.create_rectangle(20, HEIGHT-60, 140, HEIGHT-20, fill="#ef476f")
        self.canvas.create_text(80, HEIGHT-40, text="Back", font=("Consolas", 12))
        self.canvas.tag_bind(back, "<Button-1>", lambda e: self.show_menu())
        self.canvas.create_text(WIDTH-160, HEIGHT-36, text=f"Coins: {self.profile.get('coins',0)}", font=("Consolas", 12))

    def buy_item(self, item):
        uid = item['id']
        coins = self.profile.get("coins", 0)
        if uid in self.profile.get("owned", []):
            self.show_popup("You own this already"); return
        cost = item.get("cost", 0)
        if coins < cost:
            self.show_popup("Not enough coins"); return
        self.profile["coins"] = coins - cost
        self.profile.setdefault("owned", []).append(uid)
        if item.get("category") == "alex":
            self.profile.setdefault("equipped", {})["alex"] = uid
        if item.get("category") == "van":
            self.profile.setdefault("equipped", {})["van"] = uid
        play_sound("coin"); self.show_popup("Purchase successful!")
        self.data["users"][self.current] = self.profile; save_users(self.data)
        self.open_shop()

    def show_popup(self, text, ttl=900):
        self.canvas.delete("popup"); x0 = WIDTH//2-180; y0 = HEIGHT//2-32
        self.canvas.create_rectangle(x0,y0,x0+360,y0+64, fill="#111", outline="#555", tags="popup")
        self.canvas.create_text(WIDTH//2, HEIGHT//2, text=text, font=("Consolas", 12), fill="#fff", tags="popup")
        self.root.after(ttl, lambda: self.canvas.delete("popup"))

    # ---------- Gameplay ----------
    def start_topdown(self):
        self.mode = "topdown"; self.canvas.delete("all"); self.canvas.image_cache.clear()
        self.top_player = TopPlayer(self.tk_assets, self.profile); self.top_player.apply_profile()
        self.top_workers = []
        for i in range(4):
            x = random.randint(200, WIDTH-260); y = random.randint(90, HEIGHT-150)
            self.top_workers.append(TopWorker(x, y, self.tk_assets))
        self.van_top = VanTop(WIDTH-160, HEIGHT//2 - 26, self.tk_assets, self.profile)
        self.last = time.time(); self.show_popup("Steal the van on the right. Avoid workers!")

    def start_runner(self):
        self.mode = "runner"; self.canvas.delete("all"); self.canvas.image_cache.clear()
        road_w = 600; left = WIDTH//2 - road_w//2; step = road_w // (LANES+1)
        self.LANE_XS = [left + step*i for i in range(1,LANES+1)]
        self.runner_van = RunnerVan(self.tk_assets, self.profile)
        self.runner_van.lane = LANES//2; self.runner_van.set_position(self.LANE_XS[self.runner_van.lane], HEIGHT-120)
        self.obstacles = []; self.coins = []
        self.scroll_speed = 220.0; self.obs_timer = 0.0; self.runner_score = 0.0
        self.top_player.coins_collected = 0
        play_sound("engine")

    # ---------- Input ----------
    def bind_keys(self):
        def press(e):
            k = e.keysym.lower()
            if k in ("left","a"): self.keys["left"]=True
            if k in ("right","d"): self.keys["right"]=True
            if k in ("up","w"): self.keys["up"]=True
            if k in ("down","s"): self.keys["down"]=True
            if k == "space": self.keys["sprint"]=True
            if k == "escape":
                if self.mode in ("topdown","runner"): self.show_menu()
        def release(e):
            k = e.keysym.lower()
            if k in ("left","a"): self.keys["left"]=False
            if k in ("right","d"): self.keys["right"]=False
            if k in ("up","w"): self.keys["up"]=False
            if k in ("down","s"): self.keys["down"]=False
            if k == "space": self.keys["sprint"]=False
        self.root.bind("<KeyPress>", press); self.root.bind("<KeyRelease>", release)

    # ---------- Loop ----------
    def loop(self):
        now = time.time(); dt = clamp(now - self.last, 1/1000.0, 1/30.0); self.last = now
        if self.mode == "topdown": self.update_topdown(dt)
        elif self.mode == "runner": self.update_runner(dt)
        self.root.after(int(1000/FPS), self.loop)

    # Topdown
    def update_topdown(self, dt):
        self.top_player.update(dt, self.keys)
        for w in self.top_workers: w.update(dt, self.top_player)
        # collisions
        for w in self.top_workers:
            if math.hypot(w.x - self.top_player.x, w.y - self.top_player.y) < 28:
                play_sound("crash"); self.end_run(caught=True); return
        # detection
        for w in self.top_workers:
            eff = self.top_player.detect_radius
            if "mask" in self.profile.get("owned", []): eff *= 0.8
            if math.hypot(w.x - self.top_player.x, w.y - self.top_player.y) <= eff and random.random() < 0.85:
                play_sound("crash"); self.end_run(caught=True); return
        # steal van
        if not self.van_top.stolen and math.hypot(self.van_top.x - self.top_player.x, self.van_top.y - self.top_player.y) < 56:
            self.van_top.stolen = True
            gained = 50; self.profile["coins"] = self.profile.get("coins",0) + gained; self.top_player.coins_collected += gained
            self.start_runner(); return
        self.draw_topdown()

    def draw_topdown(self):
        c=self.canvas; c.delete("all"); c.image_cache.clear()
        c.create_rectangle(0,0,WIDTH,HEIGHT,fill="#2c3338")
        c.create_rectangle(0,HEIGHT-140,WIDTH,HEIGHT,fill="#222")
        self.van_top.draw(c)
        for w in self.top_workers:
            c.create_oval(w.x - self.top_player.detect_radius, w.y - self.top_player.detect_radius,
                          w.x + self.top_player.detect_radius, w.y + self.top_player.detect_radius,
                          outline="#662222", width=1, stipple="gray50")
            w.draw(c)
        self.top_player.draw(c)
        c.create_text(12,12,anchor="nw", text=f"Stamina: {int(self.top_player.stamina)}", font=FONT, fill="#fff")
        c.create_text(12,34,anchor="nw", text=f"Coins: {self.profile.get('coins',0)}", font=FONT, fill="#fff")
        c.create_text(12,56,anchor="nw", text=f"Score: {int(self.top_player.score)}", font=FONT, fill="#fff")
        if not self.van_top.stolen:
            c.create_text(WIDTH//2, 18, text="Steal the van on the right! Avoid workers!", font=FONT, fill="#ffd")

    # Runner
    def update_runner(self, dt):
        self.scroll_speed += 6.0 * dt
        self.runner_score += dt * (self.scroll_speed / 40.0)
        self.obs_timer += dt
        self.obs_interval = max(0.45, 1.0 - (self.scroll_speed - 220.0) / 800.0)
        if self.obs_timer >= self.obs_interval:
            self.spawn_obstacle()
            self.obs_timer = 0.0
        for ob in list(self.obstacles):
            ob.update(dt, self.scroll_speed)
            if ob.y > HEIGHT + 220: self.obstacles.remove(ob)
        for coin in list(self.coins):
            coin.update(dt, self.scroll_speed)
            if coin.y > HEIGHT + 200: self.coins.remove(coin)
        # lane switching
        if self.keys.get("left"):
            self.runner_van.target = clamp(self.runner_van.lane - 1, 0, LANES-1)
            self.runner_van.lane = self.runner_van.target; self.keys["left"] = False
        if self.keys.get("right"):
            self.runner_van.target = clamp(self.runner_van.lane + 1, 0, LANES-1)
            self.runner_van.lane = self.runner_van.target; self.keys["right"] = False
        # set van pos
        road_w = 600; left = WIDTH//2 - road_w//2; step = road_w // (LANES+1)
        lane_xs = [left + step*i for i in range(1,LANES+1)]
        self.runner_van.set_position(lane_xs[self.runner_van.lane], HEIGHT-120)
        van_box = (self.runner_van.x, self.runner_van.y, self.runner_van.x + self.runner_van.width, self.runner_van.y + self.runner_van.height)
        # check obstacle collision
        for ob in self.obstacles:
            if rects_overlap(van_box, ob.bbox()):
                play_sound("crash"); self.end_run(caught=False); return
        # check coin collection
        for coin in list(self.coins):
            if rects_overlap(van_box, coin.bbox()):
                play_sound("coin"); self.coins.remove(coin)
                gained = 10
                if "wallet2" in self.profile.get("owned", []): gained *= 2
                self.profile["coins"] = self.profile.get("coins",0) + gained
                self.top_player.coins_collected += gained
        self.draw_runner()

    def spawn_obstacle(self):
        lane = random.randint(0, LANES-1)
        kinds = ["worker"]*6 + ["cone"]*3 + ["crate"]*2
        kind = random.choice(kinds)
        ob = RunnerObstacle(lane, kind, self.tk_assets)
        road_w = 600; left = WIDTH//2 - road_w//2; step = road_w // (LANES+1)
        lane_x = left + step*(lane+1)
        ob.set_lane_x(lane_x)
        ob.y = -random.randint(60, 200)
        self.obstacles.append(ob)
        # sometimes spawn a coin near obstacle
        if random.random() < 0.45:
            coin = Coin(lane, self.tk_assets)
            coin.set_lane_x(lane_x)
            coin.y = ob.y - 60
            self.coins.append(coin)

    def draw_runner(self):
        c = self.canvas; c.delete("all"); c.image_cache.clear()
        road_w = 600; left = WIDTH//2 - road_w//2
        c.create_rectangle(left-8, 0, left+road_w+8, HEIGHT, fill="#333")
        # lane separators
        for i in range(LANES+1):
            x = left + (road_w / LANES) * i
            c.create_line(x, 0, x, HEIGHT, fill="#222", dash=(6,8))
        # obstacles
        for ob in self.obstacles: ob.draw(c)
        # coins
        for coin in self.coins: coin.draw(c)
        # van
        lane_x = left + (road_w // (LANES+1)) * (self.runner_van.lane + 1)
        self.runner_van.draw(c, lane_x, HEIGHT-120)
        c.create_text(12, 12, anchor="nw", text=f"Distance: {int(self.runner_score)}", font=FONT, fill="#fff")
        c.create_text(12, 36, anchor="nw", text=f"Coins: {self.profile.get('coins',0)}", font=FONT, fill="#fff")
        c.create_text(WIDTH-12, 12, anchor="ne", text=f"Speed: {int(self.scroll_speed)}", font=FONT, fill="#fff")

    # ---------- End run ----------
    def end_run(self, caught=False):
        total_score = int((self.top_player.score if self.top_player else 0) + self.runner_score)
        coins_earned = int(total_score // 25) + int(self.runner_score // 100)
        if "wallet2" in self.profile.get("owned", []): coins_earned *= 2
        self.profile["coins"] = self.profile.get("coins",0) + coins_earned
        self.profile["highscore"] = max(self.profile.get("highscore",0), total_score)
        self.data["users"][self.current] = self.profile
        save_users(self.data)
        self.canvas.delete("all")
        if caught: self.canvas.create_text(WIDTH//2, HEIGHT//2 - 60, text="CAUGHT! Game Over", font=("Consolas",28), fill="#ff4444")
        else: self.canvas.create_text(WIDTH//2, HEIGHT//2 - 60, text="CRASH! Run Over", font=("Consolas",28), fill="#ffd166")
        self.canvas.create_text(WIDTH//2, HEIGHT//2 - 10, text=f"Score: {total_score}   Coins: {coins_earned}", font=("Consolas",14), fill="#fff")
        self.canvas.create_text(WIDTH//2, HEIGHT//2 + 40, text=f"Total coins: {self.profile.get('coins',0)}", font=("Consolas",12), fill="#fff")
        play_sound("coin"); # celebratory
        self.root.after(1600, lambda: self.show_menu())

# -------------------------
# Entry point
# -------------------------
def main():
    root = tk.Tk()
    app = VanSnatcherApp(root)
    root.config(bg="#111")
    root.iconphoto(False, PhotoImage(file="Tesco.png"))
    root.resizable(False, False)
    root.mainloop()

if __name__ == "__main__":
    main()
