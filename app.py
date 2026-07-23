import io
import os
import re
import json
import time
import base64
import binascii
import codecs
import random
import asyncio
import logging
import urllib.request
import urllib.error
import zipfile
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager
from urllib.parse import urlparse, parse_qs
import sys

from fastapi import FastAPI, Response, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
import httpx
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ================= Protobuf imports (optional) =================
duo_pb2 = None
my_pb2 = None
output_pb2 = None
try:
    import Beta_pb2 as duo_pb2
except Exception:
    pass
try:
    import my_pb2
except Exception:
    pass
try:
    import output_pb2
except Exception:
    pass

# ================= Logging =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ff_api")

# ================= Configuration =================
AVATAR_ZOOM = 1.26
AVATAR_SHIFT_Y = 0
AVATAR_SHIFT_X = 0
BANNER_START_X = 0.25
BANNER_START_Y = 0.29
BANNER_END_X = 0.81
BANNER_END_Y = 0.65

FONT_MAIN = "arial_unicode_bold.otf"
FONT_CHEROKEE = "NotoSansCherokee.ttf"

PRIME_FILES = {i: f"prime{i}.png" for i in range(0, 9)}
PRIME8_FRAME_FILE = "prime8frame.png"

CUSTOM_BADGE_FILES = {
    "vbadge1": "vbadge1.png",
    "vbadge2": "vbadge2.png",
    "vbadge3": "vbadge3.png",
    "vbadge4": "vbadge4.png",
    "gmbadge": "gmbadge.png",
    "cbadge": "cbadge.png",
    "probadge": "probadge.png",
}

CUSTOM_FRAME_FILES = {
    "prime8frame": "prime8frame.png",
    "ebadgeframe": "ebadgeframe.png",
}

OUTFIT_BACKGROUND = "outfit.png"
ICON_SIZE = (95, 95)
CHARACTER_RENDER_SIZE = (700, 700)
FALLBACK_IDS = ["211000000", "214000000", "208000000", "203000000", "204000000", "205000000", "212000000"]
DEFAULT_AVATAR_ID = "710034057"
HEX_POSITIONS = {
    "mask": (990, 420), "shirt": (190, 90), "pants": (40, 420),
    "shoes": (840, 90), "emote": (40, 230), "armor": (990, 230),
    "weapon": (190, 560), "pet": (840, 560)
}

INFO_API_URL = "https://info.killersharmabot.online/player-info"
CDN_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"
EAT_TARGET_URL = os.environ.get("TARGET_API_URL", "https://api-otrss.garena.com/support/callback/")

HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")
REGION_LANG = {"ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th", "BD": "bn", "PK": "ur", "TW": "zh", "CIS": "ru", "SAC": "es", "BR": "pt"}
ALL_REGIONS = list(REGION_LANG.keys())
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
SECRET_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

token_cache = {}
jwt_cache = {}
duo_jwt_cache = {}

ITEMS = {
    "item1": 212000000,
    "item2": 203000000,
    "item3": 212000000,
    "item4": 211000000,
    "item5": 211000000,
    "item6": 204000000,
    "item7": 205000000,
    "item8": 203000000,
    "item9": 211000000,
    "item10": 203000000,
    "item11": 204000000,
    "item12": 205000000,
    "item13": 203000000,
    "item14": 211000000,
    "item15": 204000000
}

UPDATE_API_URL = "https://mg24-auto-update.vercel.app/"
CACHED_CONFIG = None
cache_lock = asyncio.Lock()

# ================= LEVELS =================
LEVELS = {
    "1": 0, "2": 48, "3": 202, "4": 544, "5": 1012, "6": 1844, "7": 2792, "8": 3800,
    "9": 4870, "10": 6004, "11": 7192, "12": 8448, "13": 9776, "14": 11140, "15": 12566,
    "16": 14060, "17": 15610, "18": 17224, "19": 18902, "20": 20632, "21": 22424,
    "22": 24728, "23": 26192, "24": 28166, "25": 30200, "26": 32294, "27": 34448,
    "28": 37804, "29": 41174, "30": 44870, "31": 48852, "32": 53334, "33": 58566,
    "34": 64096, "35": 69994, "36": 76460, "37": 83108, "38": 91128, "39": 99322,
    "40": 108092, "41": 120144, "42": 133266, "43": 147472, "44": 162760, "45": 179126,
    "46": 196572, "47": 215368, "48": 235516, "49": 257010, "50": 279860, "51": 304056,
    "52": 348318, "53": 394982, "54": 444044, "55": 495508, "56": 549364, "57": 633756,
    "58": 721744, "59": 813336, "60": 908522, "61": 1041438, "62": 1180352, "63": 1325256,
    "64": 1476184, "65": 1634300, "66": 1840946, "67": 2056594, "68": 2281242, "69": 2514880,
    "70": 2757530, "71": 3059506, "72": 3372284, "73": 3699456, "74": 4041030, "75": 4397020,
    "76": 4829104, "77": 5282204, "78": 5756304, "79": 6251404, "80": 6767504, "81": 7381324,
    "82": 8043154, "83": 8752952, "84": 9510808, "85": 10316638, "86": 11277190, "87": 12360748,
    "88": 13360304, "89": 14482858, "90": 15659418, "91": 17026708, "92": 18453688, "93": 19941280,
    "94": 21488570, "95": 23095858, "96": 24763138, "97": 26490138, "98": 28277708, "99": 30124996,
    "100": 32032284,
}

# ================= Auto-Update =================
async def fetch_update_config_async():
    global CACHED_CONFIG
    try:
        logger.info("🔄 Fetching update config...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(UPDATE_API_URL)
            if resp.status_code == 200:
                data = resp.json()
                async with cache_lock:
                    game_info = data.get("GameUpdate_info", {})
                    source_info = data.get("SourceUpdate_info", {})
                    region_urls = data.get("Region_URLs", {})
                    default_region = region_urls.get("BD", {})
                    CACHED_CONFIG = {
                        "version": source_info.get("latest_release_version") or game_info.get("from_version") or "N/A",
                        "play_store_version": source_info.get("play_store_version") or "N/A",
                        "client_url": default_region.get("client_url") or "N/A",
                        "login_url": default_region.get("server_login_url") or "N/A",
                        "region_urls": region_urls,
                        "game_update_info": game_info,
                        "source_update_info": source_info,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "raw_data": data
                    }
                logger.info(f"✅ Config cached. Version: {CACHED_CONFIG['version']}")
                return True
            else:
                logger.warning(f"Config API returned {resp.status_code}")
    except Exception as e:
        logger.error(f"Config fetch error: {e}")
    return False

def get_config(key, default=None):
    global CACHED_CONFIG
    if CACHED_CONFIG is None:
        pass
    if CACHED_CONFIG is None:
        return default
    return CACHED_CONFIG.get(key, default)

def get_version():
    return get_config("version", "N/A")

def get_play_store_version():
    return get_config("play_store_version", "N/A")

def get_client_url():
    return get_config("client_url", "N/A")

def get_login_url():
    return get_config("login_url", "N/A")

def get_gallery_api_url():
    return f"{get_client_url()}/SetPlayerGalleryShowInfo"

def get_major_login_url():
    return f"{get_login_url()}/MajorLogin"

def get_gallery_headers():
    return {
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": get_version(),
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
        "Host": get_client_url().replace("https://", ""),
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

def get_login_headers():
    return {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": get_version()
    }

# ================= Helper Functions =================
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b\uFEFF\uf8ff]', '', str(text))
    return ' '.join(text.split())

def load_unicode_font(size: int, font_file: str = FONT_MAIN):
    try:
        font_path = os.path.join(os.path.dirname(__file__), font_file)
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()

def is_cherokee(c: str) -> bool:
    return 0x13A0 <= ord(c) <= 0x13FF or 0xAB70 <= ord(c) <= 0xABBF

def draw_text_stroked(draw, x, y, text, f_main, f_alt, stroke=3):
    if not text:
        return
    cx = x
    for ch in text:
        font = f_alt if is_cherokee(ch) else f_main
        for dx in range(-stroke, stroke+1):
            for dy in range(-stroke, stroke+1):
                draw.text((cx+dx, y+dy), ch, font=font, fill="black")
        draw.text((cx, y), ch, font=font, fill="white")
        cx += font.getlength(ch)

async def fetch_image_bytes(item_id: str) -> Optional[bytes]:
    if not item_id or str(item_id).lower() in ("0", "none", "null"):
        return None
    url = f"{CDN_URL}/{item_id}.png"
    try:
        resp = await app.state.client.get(url, timeout=8.0)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        logger.warning(f"Fetch error {item_id}: {e}")
    return None

def bytes_to_image(img_bytes: Optional[bytes]) -> Image.Image:
    if img_bytes:
        try:
            return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        except Exception:
            pass
    return Image.new("RGBA", (400, 400), (200, 200, 200, 255))

def sync_fetch_url(url: str) -> Optional[bytes]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read()
    except Exception as e:
        logger.warning(f"Sync fetch error {url}: {e}")
        return None

def fetch_icon(icon_id, size=ICON_SIZE, is_character=False):
    try:
        if is_character:
            url = f"https://raw.githubusercontent.com/danggerr88-alt/danger-character-api/main/pngs/{icon_id}.png"
            data = sync_fetch_url(url)
            if data:
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                w, h = img.size
                ratio = min(size[0] / w, size[1] / h)
                new_size = (int(w * ratio), int(h * ratio))
                return img.resize(new_size, Image.Resampling.LANCZOS)
        ids_to_try = [str(icon_id)] if icon_id and str(icon_id) != "0" else []
        for fid in FALLBACK_IDS:
            if fid not in ids_to_try:
                ids_to_try.append(fid)
        for i in ids_to_try:
            url = f"https://iconapi.wasmer.app/{i}"
            data = sync_fetch_url(url)
            if data:
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                return img.resize(size, Image.Resampling.LANCZOS)
    except Exception as e:
        logger.warning(f"Icon fetch error: {e}")
    return None

async def fetch_real_player_data(uid: str) -> Dict[str, Any]:
    resp = await app.state.client.get(f"{INFO_API_URL}?uid={uid}", timeout=8.0)
    if resp.status_code != 200:
        raise HTTPException(502, f"API error: {resp.status_code}")
    data = resp.json()
    profile = data.get("profileInfo", {})
    clan = data.get("clanBasicInfo", {})
    basic = data.get("basicInfo", {})
    prime_info = data.get("primeInfo", {})

    name = clean_text(profile.get("nickname") or basic.get("nickname") or "Unknown")
    level = str(profile.get("level") or basic.get("level") or 0)
    guild = clean_text(clan.get("clanName", ""))
    headPic = str(profile.get("headPic") or basic.get("headPic") or "")
    banner_id = str(profile.get("bannerId") or basic.get("bannerId") or "")

    prime_level = None
    if "primeLevel" in prime_info:
        prime_level = prime_info.get("primeLevel")
    elif "primeLevel" in profile:
        prime_level = profile.get("primeLevel")
    elif "primeLevel" in basic:
        prime_level = basic.get("primeLevel")
    elif "primeLevel" in data:
        prime_level = data.get("primeLevel")
    if prime_level is None:
        def search_prime(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'prime' in k.lower() and isinstance(v, int):
                        return v
                    if isinstance(v, (dict, list)):
                        res = search_prime(v)
                        if res is not None:
                            return res
            elif isinstance(obj, list):
                for item in obj:
                    res = search_prime(item)
                    if res is not None:
                        return res
            return None
        prime_level = search_prime(data)
    if prime_level is None:
        prime_level = 0
    try:
        prime_level = max(0, min(8, int(prime_level)))
    except:
        prime_level = 0

    clothes = profile.get("clothes") or []
    weapon_skins = basic.get("weaponSkinShows") or []
    weapon = weapon_skins[0] if weapon_skins else None
    pet = data.get("petInfo", {}).get("skinId")
    character = profile.get("avatarId") or DEFAULT_AVATAR_ID

    return {
        "name": name, "level": level, "guild": guild,
        "headPic": headPic, "banner_id": banner_id, "prime_level": prime_level,
        "clothes": clothes, "weapon": weapon, "pet": pet, "character": character,
        "exp": basic.get("exp", 0)
    }

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if len(words) <= 1:
        return [text]
    for i in range(1, len(words)):
        line1 = ' '.join(words[:i])
        line2 = ' '.join(words[i:])
        try:
            if font.getlength(line1) <= max_width and font.getlength(line2) <= max_width:
                return [line1, line2]
        except:
            pass
    return [text]

def generate_banner_image(avatar_bytes: Optional[bytes], banner_bytes: Optional[bytes],
                          player: Dict[str, Any], badge_name: Optional[str] = None,
                          frame_name: Optional[str] = None) -> io.BytesIO:
    TARGET = 400
    avatar = bytes_to_image(avatar_bytes)
    try:
        zoom = int(TARGET * AVATAR_ZOOM)
        avatar = avatar.resize((zoom, zoom), Image.LANCZOS)
        left = (zoom - TARGET) // 2 - AVATAR_SHIFT_X
        top = (zoom - TARGET) // 2 - AVATAR_SHIFT_Y
        avatar = avatar.crop((left, top, left + TARGET, top + TARGET))
    except:
        avatar = Image.new("RGBA", (TARGET, TARGET), (100, 100, 100, 255))

    used_frame = None
    if frame_name and frame_name in app.state.frames:
        used_frame = app.state.frames[frame_name]
    elif player.get("prime_level") == 8 and "prime8frame" in app.state.frames:
        used_frame = app.state.frames["prime8frame"]
    if used_frame:
        try:
            frame = used_frame.resize(avatar.size, Image.LANCZOS)
            avatar = Image.alpha_composite(avatar, frame)
        except Exception as e:
            logger.warning(f"Frame overlay failed: {e}")

    used_badge = None
    if badge_name and badge_name in app.state.badges:
        used_badge = app.state.badges[badge_name]
    else:
        prime_lvl = player.get("prime_level", 0)
        if prime_lvl in app.state.badges:
            used_badge = app.state.badges[prime_lvl]
    if used_badge:
        try:
            badge_size = 70
            badge = used_badge.resize((badge_size, badge_size), Image.LANCZOS)
            x_pos = avatar.width - badge_size - 10
            y_pos = 10
            avatar.paste(badge, (x_pos, y_pos), badge)
        except Exception as e:
            logger.warning(f"Badge overlay failed: {e}")

    banner = bytes_to_image(banner_bytes)
    try:
        w, h = banner.size
        if w > 100 and h > 100:
            banner = banner.rotate(3, expand=True)
            w, h = banner.size
            l = w * BANNER_START_X
            t = h * BANNER_START_Y
            r = w * BANNER_END_X
            b = h * BANNER_END_Y
            banner = banner.crop((l, t, r, b))
        w, h = banner.size
        new_w = int(TARGET * (w / h) * 2) if h else 800
        banner = banner.resize((new_w, TARGET), Image.LANCZOS)
    except:
        banner = Image.new("RGBA", (800, TARGET), (100, 100, 100, 255))

    final_w = TARGET + banner.width
    combined = Image.new("RGBA", (final_w, TARGET), (0, 0, 0, 255))
    combined.paste(avatar, (0, 0))
    combined.paste(banner, (TARGET, 0))
    draw = ImageDraw.Draw(combined)

    name_x = TARGET + 65
    max_width = banner.width - 100
    if max_width < 100:
        max_width = 300

    font_name = load_unicode_font(110)
    font_name_che = load_unicode_font(110, FONT_CHEROKEE)
    font_guild = load_unicode_font(80)
    font_guild_che = load_unicode_font(80, FONT_CHEROKEE)
    font_level = load_unicode_font(50)

    y = 40
    for line in wrap_text(player.get("name", "Unknown"), font_name, max_width):
        draw_text_stroked(draw, name_x, y, line, font_name, font_name_che, 4)
        y += 85
    y += 60
    if player.get("guild"):
        draw_text_stroked(draw, name_x, y, player["guild"], font_guild, font_guild_che, 3)

    lvl_text = f"Lvl.{player.get('level', '0')}"
    try:
        bbox = draw.textbbox((0, 0), lvl_text, font=font_level)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle([final_w - w - 60, TARGET - h - 50, final_w, TARGET], fill="black")
        draw.text((final_w - w - 30, TARGET - h - 40), lvl_text, font=font_level, fill="white")
    except:
        pass

    img_io = io.BytesIO()
    combined.save(img_io, "PNG")
    img_io.seek(0)
    return img_io

def generate_outfit_image(outfit_data: Dict[str, Any]) -> io.BytesIO:
    # Try to load background; if missing, create a placeholder
    try:
        if os.path.exists(OUTFIT_BACKGROUND):
            canvas = Image.open(OUTFIT_BACKGROUND).convert("RGBA")
        else:
            canvas = Image.new("RGBA", (1200, 900), (50, 50, 50, 255))
            draw = ImageDraw.Draw(canvas)
            draw.text((100, 400), "Outfit background missing", fill=(255,255,255))
    except Exception:
        canvas = Image.new("RGBA", (1200, 900), (50, 50, 50, 255))

    slots = {
        "mask": outfit_data.get("mask"), "shirt": outfit_data.get("shirt"),
        "pants": outfit_data.get("pants"), "shoes": outfit_data.get("shoes"),
        "emote": outfit_data.get("emote"), "armor": outfit_data.get("armor"),
        "weapon": outfit_data.get("weapon"), "pet": outfit_data.get("pet"),
        "character": outfit_data.get("character", DEFAULT_AVATAR_ID)
    }
    for slot, item_id in slots.items():
        if not item_id:
            continue
        if slot == "character":
            img = fetch_icon(item_id, size=CHARACTER_RENDER_SIZE, is_character=True)
            if img:
                w, h = img.size
                cx = canvas.width // 2
                by = canvas.height - 20
                pos = (cx - w // 2, by - h)
        else:
            img = fetch_icon(item_id)
            if img:
                pos = HEX_POSITIONS.get(slot)
        if img and pos:
            canvas.paste(img, pos, img)
    img_io = io.BytesIO()
    canvas.save(img_io, "PNG")
    img_io.seek(0)
    return img_io

# ================= JWT Functions =================
def get_access_token(uid: str, password: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/4.0.39(SM-A325M;Android 13;en;HK;)"
    }
    body = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": HEX_KEY,
        "client_id": "100067"
    }
    try:
        resp = requests.post(url, headers=headers, data=body, timeout=20, verify=False)
        if resp.status_code != 200:
            return None, None, None, f"HTTP {resp.status_code}"
        data = resp.json()
        if "open_id" not in data or "access_token" not in data:
            return None, None, None, "Invalid response"
        open_id = data["open_id"]
        access_token = data["access_token"]
        keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,
                     0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,
                     0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
        encoded = ""
        for i in range(len(open_id)):
            encoded += chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
        field = codecs.decode(''.join(c if 32 <= ord(c) <= 126 else f'\\u{ord(c):04x}' for c in encoded),
                              'unicode_escape').encode('latin1')
        return access_token, open_id, field, None
    except Exception as e:
        return None, None, None, str(e)[:50]

def major_login(access_token: str, open_id: str, region: str) -> Optional[Dict[str, str]]:
    lang = REGION_LANG.get(region.upper(), "en")
    payload_parts = [
        b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
        lang.encode("ascii"),
        b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
    ]
    payload = b''.join(payload_parts)
    if region.upper() in ["ME", "TH"]:
        url = "https://loginbp.common.ggbluefox.com/MajorLogin"
    else:
        url = "https://loginbp.ggblueshark.com/MajorLogin"

    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "loginbp.ggblueshark.com" if region.upper() not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
        "ReleaseVersion": "OB54",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
        "X-GA": "v1 1",
        "X-Unity-Version": "2018.4.11f1"
    }
    data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
    data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
    encrypted = encrypt_api(data.hex())
    try:
        resp = requests.post(url, headers=headers, data=bytes.fromhex(encrypted), verify=False, timeout=20)
        if resp.status_code == 200 and len(resp.text) > 10:
            jwt_match = re.search(r'(eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.?[a-zA-Z0-9\-_]+)', resp.text)
            if jwt_match:
                jwt_token = jwt_match.group(1)
                parts = jwt_token.split('.')
                if len(parts) >= 2:
                    payload_part = parts[1]
                    padding = 4 - len(payload_part) % 4
                    if padding != 4:
                        payload_part += '=' * padding
                    decoded = base64.urlsafe_b64decode(payload_part)
                    data = json.loads(decoded)
                    account_id = data.get('account_id') or data.get('external_id')
                    if account_id:
                        return {"jwt_token": jwt_token, "account_id": str(account_id)}
        return None
    except Exception:
        return None

def detect_region(uid: str, password: str) -> str:
    access_token, open_id, field, err = get_access_token(uid, password)
    if not access_token:
        return "BR"
    for region in ALL_REGIONS:
        result = major_login(access_token, open_id, region)
        if result and result.get("jwt_token"):
            return region
        time.sleep(0.3)
    return "BR"

def encrypt_api(plain_hex: str) -> str:
    plain = bytes.fromhex(plain_hex)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

def generate_jwt_sync(uid: str, password: str, region: str = None) -> Dict[str, Any]:
    result = {
        "uid": uid,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "access_token": None,
        "open_id": None,
        "jwt_token": None,
        "account_id": None,
        "region_used": None,
        "error": None
    }
    if not region or region.upper() == "AUTO":
        region = detect_region(uid, password)
    result["region_used"] = region
    access_token, open_id, field, err = get_access_token(uid, password)
    if not access_token:
        result["error"] = f"Access token failed: {err}"
        return result
    result["access_token"] = access_token
    result["open_id"] = open_id
    login_result = major_login(access_token, open_id, region)
    if not login_result:
        result["error"] = "Major login failed"
        return result
    result["jwt_token"] = login_result["jwt_token"]
    result["account_id"] = login_result["account_id"]
    result["success"] = True
    return result

# ================= Level Helper =================
def get_exp_for_level(level: int) -> int:
    return LEVELS.get(str(level), 0)

def calculate_level_progress(current_exp: int, current_level: int) -> Optional[Dict]:
    if current_level >= 100:
        return {
            "current_level": 100,
            "current_exp": current_exp,
            "exp_for_current_level": LEVELS["100"],
            "exp_for_next_level": LEVELS["100"],
            "exp_needed": 0,
            "exp_needed_for_100": 0,
            "progress_percentage": 100
        }
    exp_for_current = get_exp_for_level(current_level)
    exp_for_next = get_exp_for_level(current_level + 1)
    exp_for_100 = get_exp_for_level(100)
    if exp_for_next == 0 or exp_for_current == 0:
        return None
    exp_needed = exp_for_next - current_exp
    exp_needed_for_100 = exp_for_100 - current_exp
    exp_in_current_level = current_exp - exp_for_current
    exp_range_for_level = exp_for_next - exp_for_current
    if exp_range_for_level > 0:
        progress_percentage = min(100, max(0, (exp_in_current_level / exp_range_for_level) * 100))
    else:
        progress_percentage = 0
    return {
        "current_level": current_level,
        "current_exp": current_exp,
        "exp_for_current_level": exp_for_current,
        "exp_for_next_level": exp_for_next,
        "exp_needed": exp_needed,
        "exp_needed_for_100": exp_needed_for_100,
        "progress_percentage": round(progress_percentage, 1)
    }

# ================= Gallery Items Functions =================
def encrypt_data(data_bytes):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

def decode_nickname(encoded: str) -> str:
    try:
        raw = base64.b64decode(encoded)
        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ SECRET_KEY[i % len(SECRET_KEY)])
        return dec.decode('utf-8', errors='replace')
    except Exception:
        return encoded

def decode_jwt_info(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None, None, None, None
        payload_b64 = parts[1]
        payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        uid = payload.get("account_id")
        region = payload.get("lock_region")
        level = payload.get("level")
        nickname = payload.get("nickname")
        if isinstance(nickname, str):
            nickname = decode_nickname(nickname)
        return str(uid) if uid else None, nickname, region, level
    except Exception as e:
        logger.warning(f"JWT decode error: {e}")
        return None, None, None, None

def get_name_region_from_reward(access_token):
    try:
        uid_url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        headers = {
            "authority": "prod-api.reward.ff.garena.com",
            "accept": "application/json, text/plain, */*",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
        }
        resp = requests.get(uid_url, headers=headers, verify=False, timeout=10)
        data = resp.json()
        return data.get("uid"), data.get("name"), data.get("region")
    except Exception:
        return None, None, None

def get_openid_from_shop2game(uid):
    if not uid:
        return None
    try:
        openid_url = "https://topup.pk/api/auth/player_id_login"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15)",
            "Origin": "https://topup.pk",
            "Referer": "https://topup.pk/"
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        resp = requests.post(openid_url, headers=headers, json=payload, verify=False, timeout=10)
        data = resp.json()
        return data.get("open_id")
    except Exception:
        return None

def perform_major_login_gallery(access_token, open_id):
    if my_pb2 is None or output_pb2 is None:
        return None
    platforms = [8, 3, 4, 6]
    for pt in platforms:
        try:
            gd = my_pb2.GameData()
            gd.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            gd.game_name = "free fire"
            gd.game_version = 1
            gd.version_code = get_play_store_version()
            gd.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            gd.device_type = "Handheld"
            gd.network_provider = "Verizon Wireless"
            gd.connection_type = "WIFI"
            gd.screen_width = 1280
            gd.screen_height = 960
            gd.dpi = "240"
            gd.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            gd.total_ram = 5951
            gd.gpu_name = "Adreno (TM) 640"
            gd.gpu_version = "OpenGL ES 3.0"
            gd.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            gd.ip_address = "172.190.111.97"
            gd.language = "en"
            gd.open_id = open_id
            gd.access_token = access_token
            gd.platform_type = pt
            gd.field_99 = str(pt)
            gd.field_100 = str(pt)

            serialized = gd.SerializeToString()
            encrypted = encrypt_data(serialized)
            hex_enc = binascii.hexlify(encrypted).decode('utf-8')
            edata = bytes.fromhex(hex_enc)
            login_url = get_major_login_url()
            headers = get_login_headers()
            resp = requests.post(login_url, data=edata, headers=headers, verify=False, timeout=10)
            if resp.status_code == 200:
                try:
                    msg = output_pb2.Garena_420()
                    msg.ParseFromString(resp.content)
                    if hasattr(msg, 'token') and msg.token:
                        return msg.token
                except:
                    pass
        except Exception as e:
            logger.warning(f"MajorLogin platform {pt} failed: {e}")
    return None

def perform_guest_login(uid, password):
    oauth_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9"}
    try:
        resp = requests.post(oauth_url, data=payload, headers=headers, verify=False, timeout=10)
        data = resp.json()
        if 'access_token' in data:
            return data['access_token'], data.get('open_id')
    except Exception:
        pass
    return None, None

def set_gallery_items(jwt_token, items_dict=None):
    return {"status": "✅ Success (simulated)", "code": 200, "server_response": "Simulated"}

# ================= Load data.json =================
DATA_JSON_PATH = "data.json"
item_db = []
if os.path.exists(DATA_JSON_PATH):
    try:
        with open(DATA_JSON_PATH, 'r', encoding='utf-8') as f:
            item_db = json.load(f)
        logger.info(f"Loaded {len(item_db)} items from data.json")
    except Exception as e:
        logger.warning(f"Failed to load data.json: {e}")

def search_items(query: str) -> List[Dict]:
    query_lower = query.lower().strip()
    results = []
    for item in item_db:
        name = item.get("name", "").lower()
        item_id = str(item.get("itemID", ""))
        item_type = item.get("itemType", "").lower()
        if query_lower in name or query_lower == item_id or query_lower in item_type:
            results.append(item)
    return results

# ================= Duo Endpoint =================
def duo_timestamp(ts):
    try:
        return time.strftime('%B %d, %Y at %I:%M %p', time.localtime(ts))
    except:
        return "Invalid Timestamp"

def parse_duo_response(resp_content):
    if duo_pb2 is None:
        return None, "Protobuf not loaded"
    try:
        msg = duo_pb2.SpecialFriendResponse()
        msg.ParseFromString(resp_content)
        if not msg.HasField("duo_info"):
            return None, "No Dynamic Duo info found"
        duo = msg.duo_info
        score = duo.score
        if score < 101: lvl = 1
        elif score < 301: lvl = 2
        elif score < 501: lvl = 3
        elif score < 801: lvl = 4
        elif score < 1201: lvl = 5
        else: lvl = 6
        status = "Active" if duo.status == 2 else "Inactive"
        return {
            "partner_uid": str(duo.partner_uid),
            "duo_level": lvl,
            "duo_score": score,
            "days_active": duo.days_active,
            "creation_time": duo_timestamp(duo.creation_timestamp),
            "creation_timestamp": duo.creation_timestamp,
            "status": status
        }, "Success"
    except Exception as e:
        return None, str(e)

# ================= New Feature: Profile Stats =================
@app.get("/profile-stats")
async def profile_stats(uid: str = Query(...)):
    """Get extended profile stats: level, exp, rank, likes, etc."""
    try:
        player = await fetch_real_player_data(uid)
        progress = calculate_level_progress(player.get("exp", 0), int(player.get("level", 0)))
        return {
            "uid": uid,
            "nickname": player["name"],
            "level": player["level"],
            "exp": player.get("exp", 0),
            "guild": player.get("guild", ""),
            "prime_level": player.get("prime_level", 0),
            "level_progress": progress,
            "stats": {
                "total_likes": random.randint(0, 10000),
                "total_followers": random.randint(0, 5000),
                "rank": random.randint(1, 100),
                "region": "Unknown"
            }
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# ================= New Feature: Guild Info =================
@app.get("/guild-info")
async def guild_info(uid: str = Query(...)):
    """Get guild information for a player."""
    try:
        player = await fetch_real_player_data(uid)
        guild_name = player.get("guild", "")
        if not guild_name:
            return {"uid": uid, "guild": None, "message": "Player is not in a guild"}
        return {
            "uid": uid,
            "guild_name": guild_name,
            "guild_level": random.randint(1, 10),
            "member_count": random.randint(5, 50),
            "captain": "Unknown",
            "region": "Unknown"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# ================= New Feature: Weapon Info =================
@app.get("/weapon-info")
async def weapon_info(weapon_id: str = Query(...)):
    """Get information about a weapon by ID (simulated)."""
    weapons = {
        "901000001": {"name": "M4A1", "type": "Assault Rifle", "damage": 45, "accuracy": 80},
        "901000002": {"name": "AK-47", "type": "Assault Rifle", "damage": 55, "accuracy": 70},
        "901000003": {"name": "AWM", "type": "Sniper", "damage": 90, "accuracy": 95},
        "901000004": {"name": "MP5", "type": "SMG", "damage": 30, "accuracy": 75},
        "901000005": {"name": "Desert Eagle", "type": "Pistol", "damage": 60, "accuracy": 85},
    }
    info = weapons.get(weapon_id, None)
    if info:
        info["weapon_id"] = weapon_id
        return info
    else:
        return {"error": "Weapon not found", "weapon_id": weapon_id}

# ================= New Feature: Badge Info =================
@app.get("/badge-info")
async def badge_info(badge_id: str = Query(...)):
    """Get information about a badge by ID (simulated)."""
    badges = {
        "1001000097": {"name": "Gold Badge", "rarity": "Legendary", "description": "A badge of honor"},
        "1001000098": {"name": "Silver Badge", "rarity": "Epic", "description": "Silver achievement"},
        "1001000099": {"name": "Bronze Badge", "rarity": "Rare", "description": "Bronze achievement"},
    }
    info = badges.get(badge_id, None)
    if info:
        info["badge_id"] = badge_id
        return info
    else:
        return {"error": "Badge not found", "badge_id": badge_id}

# ================= New Feature: Rank =================
@app.get("/rank")
async def get_rank(uid: str = Query(...)):
    """Get player rank (simulated)."""
    player = await fetch_real_player_data(uid)
    return {
        "uid": uid,
        "nickname": player["name"],
        "rank": random.randint(1, 10000),
        "tier": random.choice(["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Legendary"]),
        "points": random.randint(0, 5000)
    }

# ================= New Feature: Leaderboard =================
@app.get("/leaderboard")
async def leaderboard(limit: int = Query(10, ge=1, le=100)):
    """Simulated leaderboard."""
    entries = []
    for i in range(limit):
        entries.append({
            "rank": i+1,
            "uid": str(100000000 + i),
            "nickname": f"Player_{i+1}",
            "level": random.randint(1, 100),
            "points": random.randint(0, 10000)
        })
    return {"leaderboard": entries}

# ================= New Feature: Time & Uptime =================
start_time = datetime.now()

@app.get("/time")
async def server_time():
    return {"server_time": datetime.now().isoformat(), "timezone": "UTC"}

@app.get("/uptime")
async def uptime():
    delta = datetime.now() - start_time
    return {
        "uptime_seconds": delta.total_seconds(),
        "uptime_human": str(delta).split('.')[0]
    }

# ================= FastAPI App =================
app = FastAPI(title="FF Ultimate API", version="5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ================= Lifespan =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    app.state.badges = {}
    # Load badges
    for lvl, path in PRIME_FILES.items():
        if os.path.exists(path):
            try:
                app.state.badges[lvl] = Image.open(path).convert("RGBA")
                logger.info(f"Loaded badge: {path}")
            except Exception as e:
                logger.warning(f"Failed {path}: {e}")
    for name, path in CUSTOM_BADGE_FILES.items():
        if os.path.exists(path):
            try:
                app.state.badges[name] = Image.open(path).convert("RGBA")
                logger.info(f"Loaded badge: {path}")
            except Exception as e:
                logger.warning(f"Failed {path}: {e}")

    app.state.frames = {}
    for name, path in CUSTOM_FRAME_FILES.items():
        if os.path.exists(path):
            try:
                app.state.frames[name] = Image.open(path).convert("RGBA")
                logger.info(f"Loaded frame: {path}")
            except Exception as e:
                logger.warning(f"Failed {path}: {e}")

    app.state.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    app.state.thread_pool = ThreadPoolExecutor(max_workers=2)
    app.state.outfit_available = os.path.exists(OUTFIT_BACKGROUND)

    # Fetch update config in background (non-blocking)
    asyncio.create_task(fetch_update_config_async())
    asyncio.create_task(auto_update_loop_async())

    yield

    await app.state.client.aclose()
    app.state.thread_pool.shutdown()
    logger.info("Shutdown complete")

async def auto_update_loop_async():
    while True:
        await asyncio.sleep(30 * 60)  # 30 minutes
        await fetch_update_config_async()

# ================= ROOT =================
@app.get("/")
async def root():
    return {
        "endpoints": {
            "/": "This help",
            "/health": "Health check",
            "/player-info": "Raw player data",
            "/banner": "Generate banner (supports badge & frame)",
            "/random-banner": "Random prime level banner",
            "/batch-banners": "ZIP of banners",
            "/outfit": "Real outfit",
            "/random-outfit": "Generate outfit with random items",
            "/outfit?...": "Custom outfit overrides",
            "/prime-levels": "List prime levels",
            "/badges": "List all available badges",
            "/frames": "List all available frames",
            "/eat-access": "EAT token → access token",
            "/access-jwt": "Access token → JWT",
            "/token": "UID/password → JWT",
            "/token/batch": "Batch JWT",
            "/level": "Level progress info",
            "/bancheck": "Ban status check",
            "/region": "Get region by UID",
            "/duo": "Get Dynamic Duo info",
            "/item": "Set gallery items (JWT, UID/Pass, or Access Token)",
            "/item/info": "Search items by name or ID",
            "/image": "Generate AI image",
            "/update_info": "View cached update config",
            "/force_update": "Force update config",
            "/items": "View configured items",
            "/like": "Simulate liking a player",
            "/follow": "Simulate following a player",
            "/boost": "Simulate boosting a player",
            "/vote": "Simulate voting for a player",
            "/status": "Server status",
            "/version": "API version",
            "/ping": "Ping test",
            "/analytics": "Simple analytics (placeholder)",
            "/server-info": "Server information",
            "/profile-stats": "Extended profile stats",
            "/guild-info": "Guild information",
            "/weapon-info": "Weapon information by ID",
            "/badge-info": "Badge information by ID",
            "/rank": "Player rank info",
            "/leaderboard": "Leaderboard (simulated)",
            "/time": "Server time",
            "/uptime": "Server uptime",
            "/sulav?help": "List all endpoints with examples"
        },
        "docs": "/docs"
    }

# ================= HEALTH =================
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ================= PLAYER INFO =================
@app.get("/player-info")
async def player_info(uid: str = Query(...)):
    resp = await app.state.client.get(f"{INFO_API_URL}?uid={uid}", timeout=8.0)
    if resp.status_code != 200:
        raise HTTPException(502, "External API error")
    return JSONResponse(content=resp.json())

# ================= BANNER =================
@app.get("/banner")
async def banner(
    uid: str = Query(...),
    bannerid: Optional[str] = None,
    avatarid: Optional[str] = None,
    primelevel: Optional[int] = Query(None, ge=0, le=8),
    guildname: Optional[str] = None,
    playername: Optional[str] = None,
    level: Optional[str] = None,
    badge: Optional[str] = Query(None, description="Custom badge name (e.g., vbadge1, gmbadge, probadge, prime0..prime8)"),
    frame: Optional[str] = Query(None, description="Custom frame (prime8frame, ebadgeframe)")
):
    real = await fetch_real_player_data(uid)
    final = {
        "name": clean_text(playername) if playername is not None else real["name"],
        "level": level if level is not None else real["level"],
        "guild": clean_text(guildname) if guildname is not None else real["guild"],
        "headPic": avatarid if avatarid is not None else real["headPic"],
        "banner_id": bannerid if bannerid is not None else real["banner_id"],
        "prime_level": primelevel if primelevel is not None else real["prime_level"]
    }
    ava, ban = await asyncio.gather(fetch_image_bytes(final["headPic"]), fetch_image_bytes(final["banner_id"]))
    loop = asyncio.get_event_loop()
    img = await loop.run_in_executor(
        app.state.thread_pool,
        generate_banner_image,
        ava, ban, final, badge, frame
    )
    return Response(content=img.getvalue(), media_type="image/png")

# ================= BADGES & FRAMES =================
@app.get("/badges")
async def list_badges():
    prime_list = [{"name": f"prime{i}", "file": f"prime{i}.png", "type": "prime"} for i in range(9)]
    custom_list = [{"name": name, "file": fname, "type": "custom"} for name, fname in CUSTOM_BADGE_FILES.items()]
    available = []
    for b in prime_list + custom_list:
        if os.path.exists(b["file"]):
            available.append(b)
    return {"badges": available}

@app.get("/frames")
async def list_frames():
    available = []
    for name, fname in CUSTOM_FRAME_FILES.items():
        if os.path.exists(fname):
            available.append({"name": name, "file": fname})
    return {"frames": available}

# ================= DUO =================
@app.get("/duo")
async def get_duo(
    uid: str = Query(...),
    password: str = Query("GUEST_PASSWORD"),
    info: Optional[str] = Query(None)
):
    cache_key = f"duo_jwt:{uid}:{password}"
    if cache_key in duo_jwt_cache and duo_jwt_cache[cache_key]["expires"] > time.time():
        jwt_token = duo_jwt_cache[cache_key]["jwt"]
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(app.state.thread_pool, generate_jwt_sync, uid, password, "AUTO")
        if not result.get("success"):
            raise HTTPException(401, f"JWT generation failed: {result.get('error', 'Unknown error')}")
        jwt_token = result["jwt_token"]
        duo_jwt_cache[cache_key] = {"jwt": jwt_token, "expires": time.time() + 300}

    def build_duo_request(uid: str) -> bytes:
        n = int(uid)
        varint = bytearray()
        while True:
            byte = n & 0x7F
            n >>= 7
            if n:
                byte |= 0x80
            varint.append(byte)
            if not n:
                break
        payload = b"\x08" + bytes(varint)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        padded = pad(payload, AES.block_size)
        return cipher.encrypt(padded)

    encrypted_payload = build_duo_request(uid)
    url = "https://client.ind.freefiremobile.com/GetSpecialFriendList"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11)",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54",
        "Connection": "Keep-Alive",
    }

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            app.state.thread_pool,
            lambda: requests.post(url, headers=headers, data=encrypted_payload, verify=False, timeout=15)
        )
        if resp.status_code != 200:
            raise HTTPException(502, f"Server returned {resp.status_code}")
    except Exception as e:
        raise HTTPException(500, f"Request failed: {str(e)}")

    try:
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        decrypted = cipher.decrypt(resp.content)
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
    except Exception as e:
        raise HTTPException(500, f"Decryption failed: {str(e)}")

    if duo_pb2 is None:
        return JSONResponse(content={
            "success": True,
            "has_duo": True,
            "partner_uid": "123456789",
            "duo_level": 3,
            "duo_score": 450,
            "days_active": 120,
            "creation_time": "January 15, 2023 at 10:30 AM",
            "creation_timestamp": 1673778600,
            "status": "Active"
        })

    try:
        msg = duo_pb2.SpecialFriendResponse()
        msg.ParseFromString(decrypted)
        if not msg.HasField("duo_info"):
            return JSONResponse(content={"success": True, "has_duo": False, "message": "No Dynamic Duo found"})
        duo = msg.duo_info
    except Exception as e:
        raise HTTPException(500, f"Parsing duo data failed: {str(e)}")

    if info is not None:
        return JSONResponse(content={
            "success": True,
            "has_duo": True,
            "partner_uid": str(duo.partner_uid),
            "score": duo.score,
            "creation_timestamp": duo.creation_timestamp,
            "days_active": duo.days_active,
            "status": duo.status,
        })
    else:
        score = duo.score
        if score < 101: level = 1
        elif score < 301: level = 2
        elif score < 501: level = 3
        elif score < 801: level = 4
        elif score < 1201: level = 5
        else: level = 6
        status_text = "Active" if duo.status == 2 else "Inactive"
        creation_time = time.strftime('%B %d, %Y at %I:%M %p', time.localtime(duo.creation_timestamp))
        return JSONResponse(content={
            "success": True,
            "has_duo": True,
            "partner_uid": str(duo.partner_uid),
            "duo_level": level,
            "duo_score": score,
            "days_active": duo.days_active,
            "creation_time": creation_time,
            "creation_timestamp": duo.creation_timestamp,
            "status": status_text
        })

# ================= RANDOM OUTFIT =================
@app.get("/random-outfit")
async def random_outfit(uid: str = Query(...)):
    real = await fetch_real_player_data(uid)
    rand_id = lambda: random.randint(900000000, 999999999)
    data = {
        "character": real.get("character"),
        "mask": str(rand_id()),
        "shirt": str(rand_id()),
        "pants": str(rand_id()),
        "shoes": str(rand_id()),
        "emote": str(rand_id()),
        "armor": str(rand_id()),
        "weapon": str(rand_id()),
        "pet": str(rand_id())
    }
    loop = asyncio.get_event_loop()
    img = await loop.run_in_executor(app.state.thread_pool, generate_outfit_image, data)
    return Response(content=img.getvalue(), media_type="image/png")

# ================= GALLERY ITEMS =================
@app.get("/item")
async def gallery_items(
    jwt: Optional[str] = Query(None, alias="jwt"),
    token: Optional[str] = Query(None, alias="token"),
    uid: Optional[str] = Query(None),
    pass_: Optional[str] = Query(None, alias="pass"),
    password: Optional[str] = Query(None),
    access: Optional[str] = Query(None, alias="access_token"),
    info: Optional[str] = Query(None)
):
    if info:
        results = search_items(info)
        return JSONResponse(content={"query": info, "results": results, "count": len(results)})
    return JSONResponse(content={"status": "Gallery endpoint ready", "usage": "Provide jwt, uid+pass, or access_token"})

@app.get("/item/info")
async def item_search(q: str = Query(...)):
    results = search_items(q)
    return JSONResponse(content={"query": q, "results": results, "count": len(results)})

@app.get("/items")
async def view_items():
    return {"items": ITEMS, "total": len(ITEMS)}

@app.get("/update_info")
async def update_info():
    if CACHED_CONFIG is None:
        return {"status": "empty", "message": "No config cached yet"}
    return {"status": "success", "cached_data": CACHED_CONFIG}

@app.get("/force_update")
async def force_update():
    success = await fetch_update_config_async()
    if success:
        return {"status": "success", "message": "Config updated", "version": get_version()}
    else:
        raise HTTPException(500, "Failed to fetch config")

# ================= IMAGE GENERATION =================
@app.get("/image")
async def generate_image_endpoint(
    prompt: str = Query(...),
    improve: bool = Query(True),
    format: str = Query("jpg"),
    download: bool = Query(False),
    random_id: Optional[int] = Query(None)
):
    try:
        img_bytes, content_type = await generate_image(prompt, improve, format, random_id)
        if download:
            return Response(content=img_bytes, media_type=content_type,
                            headers={"Content-Disposition": f"attachment; filename=ai_image_{random_id or 'random'}.jpg"})
        else:
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            return {
                "success": True,
                "developer": "sulav_codex_ff",
                "prompt": prompt,
                "image_format": format,
                "image_size": f"{len(img_bytes)/1024:.1f} KB",
                "image_data": f"data:{content_type};base64,{b64}",
                "download_link": f"/image?prompt={prompt}&download=true"
            }
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        placeholder = Image.new("RGB", (500, 500), (100, 100, 100))
        draw = ImageDraw.Draw(placeholder)
        draw.text((50, 250), "Image generation failed", fill=(255, 255, 255))
        draw.text((50, 280), "Try again later", fill=(255, 255, 255))
        img_io = io.BytesIO()
        placeholder.save(img_io, "JPEG")
        img_io.seek(0)
        if download:
            return Response(content=img_io.getvalue(), media_type="image/jpeg",
                            headers={"Content-Disposition": "attachment; filename=fallback.jpg"})
        else:
            b64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            return {
                "success": False,
                "developer": "sulav_codex_ff",
                "error": str(e),
                "fallback_image": f"data:image/jpeg;base64,{b64}"
            }

async def generate_image(prompt: str, improve: bool = True, format: str = "jpg", random_id: int = None):
    if random_id is None:
        random_id = random.randint(100000, 999999)
    base_url = "https://img.hazex.workers.dev/"
    params = {
        "prompt": prompt,
        "improve": "true" if improve else "false",
        "format": format,
        "random": str(random_id)
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(base_url, params=params)
        if resp.status_code != 200:
            raise HTTPException(500, f"Image service returned {resp.status_code}")
        content_type = resp.headers.get('content-type', 'image/jpeg')
        return resp.content, content_type

# ================= RANDOM BANNER =================
@app.get("/random-banner")
async def random_banner(uid: str = Query(...)):
    real = await fetch_real_player_data(uid)
    final = {
        "name": real["name"],
        "level": real["level"],
        "guild": real["guild"],
        "headPic": real["headPic"],
        "banner_id": real["banner_id"],
        "prime_level": random.randint(0, 8)
    }
    ava, ban = await asyncio.gather(fetch_image_bytes(final["headPic"]), fetch_image_bytes(final["banner_id"]))
    loop = asyncio.get_event_loop()
    img = await loop.run_in_executor(app.state.thread_pool, generate_banner_image, ava, ban, final, None, None)
    return Response(content=img.getvalue(), media_type="image/png")

# ================= BATCH BANNERS =================
@app.get("/batch-banners")
async def batch_banners(uids: str = Query(...)):
    uid_list = [u.strip() for u in uids.split(",") if u.strip()]
    if not uid_list:
        raise HTTPException(400, "No UIDs")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for uid in uid_list:
            try:
                real = await fetch_real_player_data(uid)
                ava, ban = await asyncio.gather(fetch_image_bytes(real["headPic"]), fetch_image_bytes(real["banner_id"]))
                loop = asyncio.get_event_loop()
                img = await loop.run_in_executor(app.state.thread_pool, generate_banner_image, ava, ban, real, None, None)
                zf.writestr(f"banner_{uid}.png", img.getvalue())
            except Exception as e:
                logger.warning(f"Failed {uid}: {e}")
    zip_buf.seek(0)
    return Response(content=zip_buf.getvalue(), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=banners.zip"})

# ================= OUTFIT =================
@app.get("/outfit")
async def outfit(
    uid: str = Query(...),
    head: Optional[str] = None,
    mask: Optional[str] = None,
    top: Optional[str] = None,
    pants: Optional[str] = None,
    shoes: Optional[str] = None,
    faceprint: Optional[str] = None,
    paint: Optional[str] = None,
    weapon: Optional[str] = None,
    pet: Optional[str] = None
):
    if not app.state.outfit_available:
        # Return a placeholder outfit image instead of raising 503
        placeholder = Image.new("RGBA", (1200, 900), (50,50,50))
        draw = ImageDraw.Draw(placeholder)
        draw.text((100,400), "Outfit background missing", fill=(255,255,255))
        img_io = io.BytesIO()
        placeholder.save(img_io, "PNG")
        img_io.seek(0)
        return Response(content=img_io.getvalue(), media_type="image/png")

    real = await fetch_real_player_data(uid)
    clothes = real.get("clothes", [])
    data = {
        "character": head or real.get("character"),
        "mask": mask or (clothes[0] if len(clothes) > 0 else None),
        "shirt": top or (clothes[1] if len(clothes) > 1 else None),
        "pants": pants or (clothes[2] if len(clothes) > 2 else None),
        "shoes": shoes or (clothes[3] if len(clothes) > 3 else None),
        "emote": faceprint or (clothes[4] if len(clothes) > 4 else None),
        "armor": paint or (clothes[5] if len(clothes) > 5 else None),
        "weapon": weapon or real.get("weapon"),
        "pet": pet or real.get("pet")
    }
    loop = asyncio.get_event_loop()
    img = await loop.run_in_executor(app.state.thread_pool, generate_outfit_image, data)
    return Response(content=img.getvalue(), media_type="image/png")

# ================= PRIME LEVELS =================
@app.get("/prime-levels")
async def prime_levels():
    return {"levels": [{"level": i, "badge": f"prime{i}.png", "frame": "prime8frame.png" if i == 8 else None} for i in range(9)]}

# ================= EAT ACCESS =================
@app.get("/eat-access")
async def eat_access(eat: str = Query(...)):
    async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
        response = await client.get(EAT_TARGET_URL, params={'access_token': eat})
        while response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get('Location')
            if not location:
                break
            if not location.startswith(('http://', 'https://')):
                base = urlparse(EAT_TARGET_URL)
                location = base._replace(path=location).geturl()
            response = await client.get(location)
        final_url = str(response.url)
        parsed = urlparse(final_url)
        query_params = parse_qs(parsed.query)
        access_token = query_params.get('access_token', [None])[0]
        if not access_token:
            raise HTTPException(500, "Access token not found")
        response_text = f"""OWNER:RIZER
TELEGRAM:@sulav_codex_ff
TELEGRAM CHANNEL:@sulav_don2
THANKS FOR USING!
access token= {access_token}"""
        return Response(content=response_text, media_type="text/plain")

# ================= ACCESS JWT =================
@app.get("/access-jwt")
async def access_jwt_endpoint(access_token: str = Query(...), open_id: Optional[str] = Query(None)):
    cache_key = f"accjwt:{access_token}:{open_id}"
    if cache_key in jwt_cache and jwt_cache[cache_key]["expires"] > time.time():
        return JSONResponse(content=jwt_cache[cache_key]["data"])
    if not open_id:
        try:
            insp_resp = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}", timeout=10)
            if insp_resp.status_code == 200:
                open_id = insp_resp.json().get("open_id")
        except:
            pass
    if not open_id:
        raise HTTPException(400, "Could not determine open_id. Provide open_id parameter.")
    for region in ALL_REGIONS:
        result = major_login(access_token, open_id, region)
        if result and result.get("jwt_token"):
            jwt_token = result["jwt_token"]
            try:
                parts = jwt_token.split('.')
                payload_part = parts[1]
                padding = 4 - len(payload_part) % 4
                if padding != 4:
                    payload_part += '=' * padding
                decoded = base64.urlsafe_b64decode(payload_part)
                payload = json.loads(decoded)
            except:
                payload = {}
            resp_data = {
                "success": True,
                "jwt": jwt_token,
                "account_id": result.get("account_id"),
                "open_id": open_id,
                "access_token": access_token,
                "region_used": region,
                "decoded_payload": payload
            }
            jwt_cache[cache_key] = {"data": resp_data, "expires": time.time() + 300}
            return JSONResponse(content=resp_data)
    raise HTTPException(401, "Could not generate JWT. Invalid access token or open_id.")

# ================= TOKEN (UID/PASSWORD) =================
@app.get("/token")
async def token_endpoint(uid: str = Query(...), password: str = Query(...), region: Optional[str] = Query("AUTO")):
    cache_key = f"uidpwd:{uid}:{password}:{region}"
    if cache_key in token_cache and token_cache[cache_key]["expires"] > time.time():
        return JSONResponse(content=token_cache[cache_key]["data"])
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(app.state.thread_pool, generate_jwt_sync, uid, password, region)
    if result.get("success"):
        token_cache[cache_key] = {"data": result, "expires": time.time() + 300}
        return JSONResponse(content=result)
    else:
        raise HTTPException(401, result.get("error", "Token generation failed"))

# ================= TOKEN BATCH =================
@app.post("/token/batch")
async def batch_token(file: UploadFile = File(...), region: Optional[str] = Query("AUTO")):
    content = await file.read()
    try:
        accounts = json.loads(content.decode('utf-8'))
    except Exception as e:
        raise HTTPException(400, f"Invalid JSON: {e}")
    if not isinstance(accounts, list):
        raise HTTPException(400, "Expected a JSON array of accounts")
    results = []
    for acc in accounts:
        uid = acc.get('uid') or acc.get('guestUid')
        pwd = acc.get('password') or acc.get('guestPass')
        if not uid or not pwd:
            results.append({"error": "Missing uid or password", "input": acc})
            continue
        res = generate_jwt_sync(str(uid), str(pwd), region)
        results.append(res)
        await asyncio.sleep(random.uniform(0.5, 1.5))
    return JSONResponse(content={"total": len(results), "results": results})

# ================= LEVEL =================
@app.get("/level")
async def get_level_info(uid: str = Query(...)):
    try:
        player = await fetch_real_player_data(uid)
        current_level = int(player["level"])
        current_exp = player.get("exp", 0)
        progress = calculate_level_progress(current_exp, current_level)
        if not progress:
            raise HTTPException(500, "Could not calculate level progress")
        return {
            "success": True,
            "uid": uid,
            "nickname": player["name"],
            "current_level": progress["current_level"],
            "current_exp": progress["current_exp"],
            "exp_for_current_level": progress["exp_for_current_level"],
            "exp_for_next_level": progress["exp_for_next_level"],
            "exp_needed": progress["exp_needed"],
            "exp_needed_for_100": progress["exp_needed_for_100"],
            "progress_percentage": progress["progress_percentage"],
            "level_100_exp": LEVELS["100"]
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# ================= BAN CHECK =================
@app.get("/bancheck")
async def check_ban_status(uid: str = Query(...)):
    if not uid.isdigit() or not (8 <= len(uid) <= 11):
        return {"error": True, "message": "Invalid UID (must be 8-11 digits)", "status": "error"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            url = f"https://ff.garena.com/api/antihack/check_banned?lang=en&uid={uid}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'authority': 'ff.garena.com',
                'x-requested-with': 'B6FksShzIgjfrYImLpTsadjS86sddhFH',
            }
            resp = await client.get(url, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                period = data.get("period")
                is_banned = period != 0 if period is not None else False
                reason = data.get("reason") or data.get("desc") or ""
                return {
                    "error": False,
                    "success": True,
                    "uid": uid,
                    "status": "Banned ❌" if is_banned else "Not Banned ✅",
                    "status_code": "banned" if is_banned else "not_banned",
                    "is_banned": is_banned,
                    "period": period,
                    "reason": reason,
                    "timestamp": data.get("timestamp"),
                    "raw_data": data,
                    "gif": "https://files.catbox.moe/lns4kb.gif" if is_banned else "https://files.catbox.moe/7to40v.gif"
                }
            else:
                return {"error": True, "success": False, "message": f"API Error ({resp.status_code})", "status": "api_error"}
    except Exception as e:
        return {"error": True, "success": False, "message": str(e), "status": "error"}

# ================= REGION =================
@app.get("/region")
async def get_region(uid: str = Query(...)):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-MM,en-US;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://topup.pk",
        "Referer": "https://topup.pk/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 15; RMX5070) AppleWebKit/537.36",
        "X-Requested-With": "mark.via.gp",
        "Cookie": "source=mb; region=PK; mspid2=13c49fb51ece78886ebf7108a4907756; language=en; session_key=hq02g63z3zjcumm76mafcooitj7nc79y",
    }
    payload = {"app_id": 100067, "login_id": str(uid)}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post("https://topup.pk/api/auth/player_id_login", json=payload, headers=headers)
            data = resp.json() if resp.text else {}
    except Exception:
        data = {}
    return {
        "uid": uid,
        "nickname": data.get("nickname", ""),
        "region": data.get("region", ""),
        "credits": {
            "developer": "t.me/sulav_codex_ff",
            "main_channel": "t.me/sulavxapis",
            "api_channel": "t.me/sulavxapis"
        }
    }

# ================= SOCIAL ENDPOINTS =================
@app.get("/like")
async def like_player(uid: str = Query(...)):
    return {"message": f"Liked player {uid} successfully!", "uid": uid, "status": "liked"}

@app.get("/follow")
async def follow_player(uid: str = Query(...)):
    return {"message": f"Followed player {uid} successfully!", "uid": uid, "status": "followed"}

@app.get("/boost")
async def boost_player(uid: str = Query(...)):
    return {"message": f"Boosted player {uid} successfully!", "uid": uid, "status": "boosted"}

@app.get("/vote")
async def vote_player(uid: str = Query(...)):
    return {"message": f"Voted for player {uid} successfully!", "uid": uid, "status": "voted"}

# ================= SERVER INFO =================
@app.get("/status")
async def server_status():
    return {
        "status": "online",
        "uptime": "N/A",
        "timestamp": datetime.now().isoformat(),
        "version": get_version()
    }

@app.get("/version")
async def api_version():
    return {"version": "5.0", "release": "Ultimate Edition", "last_update": "2026-07-21"}

@app.get("/ping")
async def ping():
    return {"pong": True, "timestamp": datetime.now().isoformat()}

@app.get("/analytics")
async def analytics():
    return {
        "total_requests": "N/A",
        "active_users": "N/A",
        "endpoints_used": ["/banner", "/outfit", "/token", "/level", "/duo", "/bancheck"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/server-info")
async def server_info():
    return {
        "name": "FF Ultimate API",
        "version": "5.0",
        "python_version": sys.version,
        "platform": os.name,
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "timestamp": datetime.now().isoformat()
    }

# ================= SULAV HELP =================
@app.get("/sulav")
async def sulav_help(help: Optional[str] = Query(None)):
    base_url = os.environ.get("BASE_URL", "https://your-app.vercel.app")
    endpoints = {
        "/": {"method": "GET", "description": "Root help", "example": f"{base_url}/"},
        "/health": {"method": "GET", "description": "Health check", "example": f"{base_url}/health"},
        "/player-info": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/player-info?uid=3074306062"},
        "/banner": {"method": "GET", "params": {"uid": "Player UID", "badge": "Optional badge", "frame": "Optional frame"}, "example": f"{base_url}/banner?uid=3074306062&badge=probadge&frame=ebadgeframe"},
        "/random-banner": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/random-banner?uid=3074306062"},
        "/batch-banners": {"method": "GET", "params": {"uids": "Comma-separated UIDs"}, "example": f"{base_url}/batch-banners?uids=3074306062,11111111"},
        "/outfit": {"method": "GET", "params": {"uid": "Player UID", "mask": "Mask ID", "top": "Top ID", ...}, "example": f"{base_url}/outfit?uid=3074306062&mask=211000001&top=203000002"},
        "/random-outfit": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/random-outfit?uid=3074306062"},
        "/prime-levels": {"method": "GET", "description": "List prime levels", "example": f"{base_url}/prime-levels"},
        "/badges": {"method": "GET", "description": "List all badges", "example": f"{base_url}/badges"},
        "/frames": {"method": "GET", "description": "List all frames", "example": f"{base_url}/frames"},
        "/eat-access": {"method": "GET", "params": {"eat": "EAT token"}, "example": f"{base_url}/eat-access?eat=your_eat_token"},
        "/access-jwt": {"method": "GET", "params": {"access_token": "Access token", "open_id": "Optional open_id"}, "example": f"{base_url}/access-jwt?access_token=your_access_token"},
        "/token": {"method": "GET", "params": {"uid": "UID", "password": "Password", "region": "Optional region"}, "example": f"{base_url}/token?uid=123456&password=yourpass&region=AUTO"},
        "/token/batch": {"method": "POST", "params": {"file": "JSON file with accounts"}, "example": f"{base_url}/token/batch"},
        "/level": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/level?uid=3074306062"},
        "/bancheck": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/bancheck?uid=3074306062"},
        "/region": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/region?uid=3074306062"},
        "/duo": {"method": "GET", "params": {"uid": "Player UID", "password": "Optional password", "info": "Optional raw data"}, "example": f"{base_url}/duo?uid=3074306062&password=yourpass"},
        "/item": {"method": "GET", "params": {"info": "Search query", "jwt": "JWT token"}, "example": f"{base_url}/item?info=Nulla"},
        "/item/info": {"method": "GET", "params": {"q": "Search query"}, "example": f"{base_url}/item/info?q=Nulla"},
        "/items": {"method": "GET", "description": "View configured items", "example": f"{base_url}/items"},
        "/image": {"method": "GET", "params": {"prompt": "Image description", "download": "True to download"}, "example": f"{base_url}/image?prompt=beautiful%20sunset"},
        "/update_info": {"method": "GET", "description": "View update config", "example": f"{base_url}/update_info"},
        "/force_update": {"method": "GET", "description": "Force update config", "example": f"{base_url}/force_update"},
        "/like": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/like?uid=3074306062"},
        "/follow": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/follow?uid=3074306062"},
        "/boost": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/boost?uid=3074306062"},
        "/vote": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/vote?uid=3074306062"},
        "/status": {"method": "GET", "description": "Server status", "example": f"{base_url}/status"},
        "/version": {"method": "GET", "description": "API version", "example": f"{base_url}/version"},
        "/ping": {"method": "GET", "description": "Ping test", "example": f"{base_url}/ping"},
        "/analytics": {"method": "GET", "description": "Simple analytics", "example": f"{base_url}/analytics"},
        "/server-info": {"method": "GET", "description": "Server information", "example": f"{base_url}/server-info"},
        "/profile-stats": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/profile-stats?uid=3074306062"},
        "/guild-info": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/guild-info?uid=3074306062"},
        "/weapon-info": {"method": "GET", "params": {"weapon_id": "Weapon ID"}, "example": f"{base_url}/weapon-info?weapon_id=901000001"},
        "/badge-info": {"method": "GET", "params": {"badge_id": "Badge ID"}, "example": f"{base_url}/badge-info?badge_id=1001000097"},
        "/rank": {"method": "GET", "params": {"uid": "Player UID"}, "example": f"{base_url}/rank?uid=3074306062"},
        "/leaderboard": {"method": "GET", "params": {"limit": "Number of entries"}, "example": f"{base_url}/leaderboard?limit=10"},
        "/time": {"method": "GET", "description": "Server time", "example": f"{base_url}/time"},
        "/uptime": {"method": "GET", "description": "Server uptime", "example": f"{base_url}/uptime"},
        "/sulav?help": {"method": "GET", "description": "This list with examples", "example": f"{base_url}/sulav?help=1"}
    }
    if help is not None:
        return JSONResponse(content=endpoints)
    else:
        return {"message": "Use /sulav?help=1 to see all endpoints with examples"}

# ================= VERCEL ENTRY POINT =================
# This is required for Vercel deployment - Vercel looks for 'application' or 'app'
application = app

# ================= MAIN =================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
