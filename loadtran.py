#!/usr/bin/env python3
import argparse
import hashlib
import hmac as hmac_lib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("\033[91m[!] Thieu: pip install requests\033[0m")
    sys.exit(1)

try:
    from PIL import Image as _PIL_Image
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# =============================================================================
# ANSI COLORS
# =============================================================================

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"
    BG_CYAN   = "\033[46m"
    BG_GREEN  = "\033[42m"
    BG_RED    = "\033[41m"
    BG_PURPLE = "\033[45m"

def ok(msg):   return "{}â  {}{}".format(C.GREEN,  msg, C.RESET)
def err(msg):  return "{}â  {}{}".format(C.RED,    msg, C.RESET)
def warn(msg): return "{}â   {}{}".format(C.YELLOW, msg, C.RESET)
def info(msg): return "{}âº  {}{}".format(C.CYAN,   msg, C.RESET)
def dim(msg):  return "{}{}{}".format(C.GRAY, msg, C.RESET)
def bold(msg): return "{}{}{}".format(C.BOLD, msg, C.RESET)

def hdr(title, width=62):
    inner = " {} ".format(title)
    pad   = max(0, width - len(inner) - 2)
    l, r  = pad // 2, pad - pad // 2
    return ("{}{}{} {}{}{}{} {}{}".format(
        C.BG_CYAN, C.WHITE, C.BOLD,
        "â"*l, inner, "â"*r,
        C.RESET, C.CYAN, C.RESET))

def sep(width=62, char="â", color=C.GRAY):
    return "{}{}{}".format(color, char*width, C.RESET)

# =============================================================================
# CAU HINH
# =============================================================================

COS_BUCKET   = "aovcamp-h5-1254801811"
COS_REGION   = "ap-singapore"
COS_HOST     = "{}.cos.{}.myqcloud.com".format(COS_BUCKET, COS_REGION)
CDN_BASE     = "https://kg-camp.mobagarena.com"
API_BASE     = "https://kgvn-api.mobagarena.com"
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4"}
DEFAULT_HAR  = "0919.har"
MAX_MEDIA_PER_ACC = 6

# Playerimage constants
PI_STICKER_ID = "182"
PI_STICKER_W  = 690.9890109890109
PI_STICKER_H  = 690.9890109890109
PI_STICKER_X  = -194.8712087912088
PI_STICKER_Y  = -85.4572357633227
PI_BG_ID      = "21"
PI_BG_PICURL  = CDN_BASE + "/manage/playerimage_official/iDzT817p.png"
PI_BG_W       = 320
PI_BG_H       = 503.99824175824176

# Timing
POSTER_STAGGER = 3.6
ROUND_DELAY    = 3.0
ACC_STAGGER    = 2.0

FIXED_HEADERS = {
    "camp-source":        "AOV-CAMP",
    "msdk-gameid":        "1137",
    "camp-authtype":      "msdk",
    "areaid":             "1",
    "msdk-os":            "1",
    "logicworldid":       "1011",
    "aov-language":       "VN",
    "msdk-channelid":     "10",
    "aov-region":         "1137",
    "origin":             "https://kgvn-camp.mobagarena.com",
    "x-requested-with":   "com.garena.game.kgvn",
    "referer":            "https://kgvn-camp.mobagarena.com/",
    "sec-ch-ua":          '"Chromium";v="146", "Not-A.Brand";v="24", "Android WebView";v="146"',
    "sec-ch-ua-mobile":   "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-site":     "same-site",
    "sec-fetch-mode":     "cors",
    "sec-fetch-dest":     "empty",
    "accept":             "*/*",
    "accept-language":    "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "accept-encoding":    "gzip, deflate, br, zstd",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 15; SM-A165F Build/AP3A.240905.015.A2; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/146.0.7680.177 "
        "Mobile Safari/537.36 MSDK/5.36.000 mQQAppId/1105779914 "
        "mWXAppId/wx7a814e3ceeda8320 mGameId/1137 MSDKdeviceId/disable"
    ),
}

_print_lock = threading.Lock()
def tprint(msg):
    with _print_lock:
        print(msg, flush=True)

# =============================================================================
# UTILS
# =============================================================================

def gen_traceparent():
    return "00-{}-{}-01".format(os.urandom(16).hex(), os.urandom(8).hex())

def check_connectivity():
    for host in ["kgvn-api.mobagarena.com", "8.8.8.8"]:
        try:
            socket.setdefaulttimeout(5)
            socket.getaddrinfo(host, 443)
            return True
        except socket.gaierror:
            continue
    return False

def make_session():
    s = requests.Session()
    r = Retry(total=3, backoff_factor=1.5,
              status_forcelist=[500,502,503,504],
              allowed_methods=["POST","PUT","GET"])
    a = HTTPAdapter(max_retries=r)
    s.mount("https://", a); s.mount("http://", a)
    return s

def ask_choice(prompt, options):
    print("\n" + "{}{}{}".format(C.CYAN, prompt, C.RESET))
    for k, v in options.items():
        print("    {}[{}]{} {}".format(C.YELLOW+C.BOLD, k, C.RESET, v))
    while True:
        try:
            c = input("    {}Chon: {}".format(C.PURPLE, C.RESET)).strip()
            if c in options:
                return c
            print(warn("Nhap: " + " / ".join(options.keys())))
        except KeyboardInterrupt:
            print("\n" + err("Huy")); sys.exit(0)

def cinput(prompt):
    try:
        return input("{}{}{}".format(C.PURPLE, prompt, C.RESET)).strip()
    except KeyboardInterrupt:
        print("\n" + err("Huy")); sys.exit(0)

def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# =============================================================================
# COS SIGNING
# =============================================================================

def _hmac_sha1(key, msg):
    return hmac_lib.new(key, msg.encode(), hashlib.sha1).hexdigest()

def build_cos_auth(sid, skey, method, pathname, clen):
    now  = int(time.time())
    end  = now + 86400
    kt   = "{};{}".format(now, end)
    sk   = _hmac_sha1(skey.encode(), kt)
    hh   = "content-length={}&host={}".format(clen, COS_HOST)
    hs   = "{}\n{}\n\n{}\n".format(method.lower(), pathname, hh)
    hhttp= hashlib.sha1(hs.encode()).hexdigest()
    s2s  = "sha1\n{}\n{}\n".format(kt, hhttp)
    sig  = _hmac_sha1(sk.encode(), s2s)
    return ("q-sign-algorithm=sha1&q-ak={}"
            "&q-sign-time={}&q-key-time={}"
            "&q-header-list=content-length;host&q-url-param-list="
            "&q-signature={}").format(sid, kt, kt, sig)

# =============================================================================
# PARSE HAR
# =============================================================================

def parse_har(har_path):
    """Tra ve: (auth_token, user_path)"""
    with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
        har = json.load(f)

    auth_token = None
    user_path  = None

    for entry in har["log"]["entries"]:
        req = entry["request"]
        url = req["url"]

        if "kgvn-api.mobagarena.com" in url and not auth_token:
            hdrs = {h["name"].lower(): h["value"]
                    for h in req.get("headers",[])}
            if "msdk-itopencodeparam" in hdrs:
                auth_token = hdrs["msdk-itopencodeparam"]

        if req["method"] == "PUT" and COS_HOST in url and not user_path:
            path  = url.split(COS_HOST)[1].split("?")[0]
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                user_path = "/" + "/".join(parts[:3]) + "/"

        if auth_token and user_path:
            break

    return auth_token, user_path

# =============================================================================
# MEDIA PROCESSING
# =============================================================================

def prepare_media(file_path):
    file_path = Path(file_path)
    ext       = file_path.suffix.lower()
    raw       = file_path.read_bytes()

    if ext in (".jpg",".jpeg",".png",".webp"):
        return {
            "png_bytes":  raw,
            "anim_bytes": None,
            "anim_ext":   None,
            "label":      "{} {:,}B".format(ext.upper().lstrip("."), len(raw)),
            "name":       file_path.name,
        }

    if ext == ".gif":
        if not PILLOW_OK:
            print(err("GIF can Pillow: pip install Pillow")); sys.exit(1)
        try:
            gif = _PIL_Image.open(io.BytesIO(raw))
            gif.seek(0)
            buf = io.BytesIO()
            gif.convert("RGBA").save(buf, format="PNG")
            png_b = buf.getvalue()
            print(info("    GIF: frame1âPNG {:,}B  +  GIF goc {:,}B".format(
                len(png_b), len(raw))))
            return {
                "png_bytes":  png_b,
                "anim_bytes": raw,
                "anim_ext":   "gif",
                "label":      "GIF {:,}B anim".format(len(raw)),
                "name":       file_path.name,
            }
        except Exception as e:
            print(err("Loi GIF: " + str(e))); sys.exit(1)

    if ext == ".mp4":
        if not has_ffmpeg():
            print(err("MP4 can ffmpeg: pkg install ffmpeg")); sys.exit(1)
        tmp_mp4 = tempfile.mktemp(suffix=".mp4")
        tmp_gif = tempfile.mktemp(suffix=".gif")
        tmp_png = tempfile.mktemp(suffix=".png")
        try:
            with open(tmp_mp4,"wb") as f: f.write(raw)
            print(info("    MP4 â GIF (fps=10 scale=320)..."))
            subprocess.run(
                ["ffmpeg","-i",tmp_mp4,
                 "-vf","fps=10,scale=320:-1:flags=lanczos",
                 "-loop","0", tmp_gif, "-y"],
                capture_output=True, check=True)
            with open(tmp_gif,"rb") as f: gif_b = f.read()
            subprocess.run(
                ["ffmpeg","-i",tmp_gif,"-vframes","1",
                 "-f","image2",tmp_png,"-y"],
                capture_output=True, check=True)
            with open(tmp_png,"rb") as f: png_b = f.read()
            for fp in [tmp_mp4,tmp_gif,tmp_png]:
                try: os.unlink(fp)
                except: pass
            print(info("    PNG render {:,}B  GIF anim {:,}B".format(
                len(png_b), len(gif_b))))
            return {
                "png_bytes":  png_b,
                "anim_bytes": gif_b,
                "anim_ext":   "gif",
                "label":      "MP4âGIF {:,}B anim".format(len(gif_b)),
                "name":       file_path.name,
            }
        except subprocess.CalledProcessError as e:
            print(err("ffmpeg that bai: " + str(e))); sys.exit(1)
        except Exception as e:
            print(err("Loi MP4: " + str(e))); sys.exit(1)

    print(err("Dinh dang khong ho tro: " + ext)); sys.exit(1)

def scan_media(directory):
    files = sorted([
        p for p in Path(directory).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ])
    if not files:
        print(err("Khong tim thay media trong: " + directory))
        sys.exit(1)
    return files

def find_har_files(directory="."):
    return sorted(Path(directory).glob("*.har"))

# =============================================================================
# API HELPERS
# =============================================================================

def api_post(session, endpoint, payload, auth_token,
             retry_on_code1=False, max_retries=3, delay=3.0):
    hdrs = dict(FIXED_HEADERS)
    hdrs["content-type"]         = "application/json"
    hdrs["msdk-itopencodeparam"] = auth_token
    hdrs["traceparent"]          = gen_traceparent()
    hdrs["priority"]             = "u=1, i"
    data = {}
    for attempt in range(max_retries):
        try:
            r = session.post(API_BASE+endpoint,
                             json=payload, headers=hdrs, timeout=25)
            r.raise_for_status()
            data = r.json()
            if retry_on_code1 and data.get("code") == 1:
                wait = delay*(attempt+1)
                tprint(warn("  code=1 thu lai {}s [{}/{}]".format(
                    int(wait), attempt+1, max_retries)))
                time.sleep(wait); continue
            return data
        except requests.exceptions.ConnectionError as e:
            tprint(err("Loi ket noi: "+str(e)))
            return {"code":-1,"msg":str(e)}
        except requests.exceptions.Timeout:
            if attempt < max_retries-1:
                tprint(warn("  Timeout [{}/{}] thu lai...".format(
                    attempt+1, max_retries)))
                time.sleep(delay)
            else:
                return {"code":-1,"msg":"timeout"}
    return data

def cos_put(session, url, data, headers, label=""):
    for attempt in range(3):
        try:
            resp = session.put(url, data=data, headers=headers, timeout=60)
            if resp.status_code == 200:
                return resp
            tprint(warn("  COS {} [{}]: {}".format(
                label, resp.status_code, resp.text[:120])))
            if attempt < 2: time.sleep(2)
        except requests.exceptions.ConnectionError as e:
            tprint(err("COS loi: "+str(e))); return None
    return resp

# =============================================================================
# BUILD picInfo  â  PLAYERIMAGE
# =============================================================================

def build_pic_info(pic_info_raw, sticker_url):
    bg = pic_info_raw.get("bg", {})
    return {
        "bg": {
            "id":     bg.get("id",     PI_BG_ID),
            "picUrl": bg.get("picUrl", PI_BG_PICURL),
            "source": 1,
            "width":  bg.get("width",  PI_BG_W),
            "height": bg.get("height", PI_BG_H),
            "posX":   bg.get("posX",   0),
            "posY":   bg.get("posY",   0),
        },
        "stickerList": [{
            "id":     PI_STICKER_ID,
            "picUrl": sticker_url,
            "width":  PI_STICKER_W,
            "height": PI_STICKER_H,
            "posX":   PI_STICKER_X,
            "posY":   PI_STICKER_Y,
            "rotate": 0, "source": 1, "type": 1,
        }],
    }

# =============================================================================
# POSTER WORKER
# =============================================================================

def poster_worker(idx, acc_lbl, auth_token, user_path,
                  media, pic_info_raw, is_share, results):
    tag     = "{}[{} P{:02d}]{}".format(
        C.CYAN+C.BOLD, acc_lbl[:14], idx, C.RESET)
    session = make_session()

    png_b    = media["png_bytes"]
    anim_b   = media["anim_bytes"]
    anim_ext = media["anim_ext"]
    fname    = media.get("name", "?")

    try:
        # A. createposter
        tprint("{} Tao poster {}...".format(tag, dim(fname[:18])))
        r = api_post(session, "/api/game/poster/playerimage/createposter",
                     {}, auth_token)
        if r.get("code") != 0:
            tprint("{} {}".format(tag, err("createposter: "+r.get("msg","")[:40])))
            results[idx-1] = (False, "createposter: "+r.get("msg","")[:40]); return
        pid = r["data"]["posterId"]
        tprint("{} PosterID={}{}{}".format(tag, C.YELLOW, pid, C.RESET))
        time.sleep(0.5)

        # B. COS credentials (per-poster)
        def get_creds(pic_type):
            rc = api_post(session, "/api/tool/getcoscredential",
                         {"scene": "PlayerimagePoster",
                          "posterId": int(pid), "picType": pic_type},
                         auth_token)
            return rc["data"] if rc.get("code") == 0 else None

        creds1 = get_creds(1)
        if not creds1:
            tprint("{} {}".format(tag, err("getCOS FAIL")))
            results[idx-1] = (False, "getCOS fail"); return
        creds2 = get_creds(2) or creds1
        time.sleep(0.3)

        # C. COS upload
        ck   = "{}0/1/{}.png".format(user_path, pid)
        ck_l = "{}0/1/{}_large.png".format(user_path, pid)

        def mkhdr(key, buf, creds_in):
            return {
                "Authorization":        build_cos_auth(
                    creds_in["tmpSecretId"], creds_in["tmpSecretKey"],
                    "PUT", key, len(buf)),
                "Content-Type":         "image/png",
                "Content-Length":       str(len(buf)),
                "Host":                 COS_HOST,
                "x-cos-security-token": creds_in["token"],
                "Origin":               "https://kgvn-camp.mobagarena.com",
                "Referer":              "https://kgvn-camp.mobagarena.com/",
            }

        r2 = cos_put(session, "https://"+COS_HOST+ck,
                     png_b, mkhdr(ck, png_b, creds1), ".png")
        if r2 is None or r2.status_code != 200:
            tprint("{} {}".format(tag, err("COS .png FAIL")))
            results[idx-1] = (False, "COS .png fail"); return
        tprint("{} COS .png {} {:,}B".format(tag, ok("OK"), len(png_b)))

        cos_put(session, "https://"+COS_HOST+ck_l,
                png_b, mkhdr(ck_l, png_b, creds2), "_large")

        sticker_url = CDN_BASE + ck

        # GIF/MP4 animation upload
        if anim_b is not None and anim_ext:
            ck_a = "{}0/1/{}.{}".format(user_path, pid, anim_ext)
            r_a  = cos_put(session, "https://"+COS_HOST+ck_a,
                           anim_b, mkhdr(ck_a, anim_b, creds1), "."+anim_ext)
            if r_a is not None and r_a.status_code == 200:
                sticker_url = CDN_BASE + ck_a
                tprint("{} COS .{} {} {:,}B {}".format(
                    tag, anim_ext, ok("OK"), len(anim_b), dim("(animation)")))
            else:
                tprint("{} {}".format(tag, warn(".{} FAIL â dung .png".format(anim_ext))))

        time.sleep(0.5)

        # D. savepostereditinfo
        pi = build_pic_info(pic_info_raw, sticker_url)
        rs = api_post(session,
                      "/api/game/poster/playerimage/savepostereditinfo",
                      {"picInfo": pi},
                      auth_token,
                      retry_on_code1=True, max_retries=4, delay=4.0)
        tprint("{} editInfo {}".format(
            tag, ok("OK") if rs.get("code")==0 else warn("code={}".format(rs.get("code")))))
        time.sleep(1.5)

        # E. saveposter
        rp = api_post(session,
                      "/api/game/poster/playerimage/saveposter",
                      {"posterId": pid, "isApply": True, "isShare": is_share,
                       "picUrl": CDN_BASE+user_path, "picInfo": pi},
                      auth_token,
                      retry_on_code1=True, max_retries=4, delay=4.0)

        unavail = rp.get("data", {}).get("unavailableResources", [])
        kind    = "{}GIF{}".format(C.CYAN, C.RESET) if anim_b else "IMG"

        if rp.get("code") == 0 and not unavail:
            tprint("{} {} ID={}{}{}  [{}]".format(
                tag, ok("THANH CONG"), C.GREEN, pid, C.RESET, kind))
            results[idx-1] = (True, pid, sticker_url, kind)
        elif rp.get("code") == 0:
            tprint("{} {} (co resource bi tu choi)".format(tag, ok("OK")))
            results[idx-1] = (True, pid, sticker_url, kind)
        else:
            tprint("{} {} {}".format(
                tag, err("THAT BAI"), rp.get("msg","")[:40]))
            results[idx-1] = (False, "saveposter: "+rp.get("msg","")[:40])

    except Exception as e:
        tprint("{} {}".format(tag, err("EXCEPTION: "+str(e)[:50])))
        results[idx-1] = (False, "exception: "+str(e)[:40])

# =============================================================================
# ACC WORKER
# =============================================================================

def acc_worker(acc, media_list, rounds, is_share, acc_results):
    lbl = acc["label"]

    tprint("\n" + sep(62, "â", C.CYAN))
    tprint("{}{}  START  {}{}".format(C.CYAN+C.BOLD, "â¶", lbl, C.RESET))
    tprint(sep(62, "â", C.CYAN))

    auth_token, user_path = parse_har(acc["har"])
    if not auth_token or not user_path:
        tprint(err("  [{}] Khong co token/path â bo qua".format(lbl)))
        acc_results[lbl] = {"ok":0,"fail":0,"rounds":[]}; return

    tprint(dim("  Token   : {}...".format(auth_token[:35])))
    tprint(dim("  COS     : {}".format(user_path)))

    sess = make_session()

    # Lay picInfo hien tai (tuy chon)
    tprint(info("  Lay picInfo hien tai..."))
    r = api_post(sess, "/api/game/poster/playerimage/getpostereditinfo",
                 {}, auth_token)
    if r.get("code") == 0 and r.get("data", {}).get("picInfo"):
        pic_info_raw = r["data"]["picInfo"]
        tprint(ok("  picInfo OK"))
    else:
        pic_info_raw = {}
        tprint(warn("  Dung cau hinh mac dinh"))
    time.sleep(0.5)

    n_media    = len(media_list)
    total_ok   = total_fail = 0
    round_logs = []

    for rnd in range(1, rounds+1):
        tprint("")
        tprint("{}  [{}] Vong {:02d}/{:02d}  â  {} media song song{}".format(
            C.CYAN+C.BOLD, lbl[:16], rnd, rounds, n_media, C.RESET))

        results = [None]*n_media
        threads = []
        for i, m in enumerate(media_list, 1):
            t = threading.Thread(
                target=poster_worker,
                args=(i, lbl, auth_token, user_path,
                      m, pic_info_raw, is_share, results),
                daemon=True,
            )
            threads.append(t)

        for t in threads:
            t.start()
            time.sleep(POSTER_STAGGER)

        for t in threads:
            t.join()

        ok_n   = sum(1 for res in results if res and res[0])
        fail_n = n_media - ok_n
        total_ok   += ok_n
        total_fail += fail_n
        round_logs.append((rnd, results))

        summary = "{} OK  {} FAIL".format(
            "{}{}{}".format(C.GREEN, ok_n,   C.RESET),
            "{}{}{}".format(C.RED,   fail_n, C.RESET))
        tprint("  {}[{}] Vong {:02d}: {}{}".format(
            C.BOLD, lbl[:16], rnd, summary, C.RESET))

        if rnd < rounds:
            tprint(dim("  [{}] Nghi {}s truoc vong tiep...".format(
                lbl[:16], ROUND_DELAY)))
            time.sleep(ROUND_DELAY)

    # Tong ket acc
    tprint("")
    tprint("{}ââ DONE: {} {}".format(C.CYAN+C.BOLD, lbl, C.RESET))
    for rnd, results in round_logs:
        for i, res in enumerate(results, 1):
            g = (rnd-1)*n_media+i
            if res and res[0]:
                kind = res[3] if len(res) > 3 else "?"
                tprint("{}â{}  V{:02d}#{:02d} {}  [{}]  ID={}".format(
                    C.CYAN, C.RESET, rnd, g, ok("OK"), kind, res[1]))
            else:
                msg = str(res[1])[:35] if res else "?"
                tprint("{}â{}  V{:02d}#{:02d} {}  {}".format(
                    C.CYAN, C.RESET, rnd, g, err("FAIL"), msg))
    tprint("{}ââ OK:{} {}{}{}  FAIL:{} {}{}{}  TONG:{}{}".format(
        C.CYAN,
        C.RESET, C.GREEN+C.BOLD, total_ok,   C.RESET,
        C.RESET, C.RED+C.BOLD,   total_fail, C.RESET,
        C.BOLD, rounds*n_media) + C.RESET)

    acc_results[lbl] = {"ok":total_ok,"fail":total_fail,"rounds":round_logs}

# =============================================================================
# MAIN
# =============================================================================

def run(har_path_arg, image_dir, rounds_arg):
    print("")
    print("{}{}".format(C.CYAN, "â"*62))
    print("{}  KGVN  Mod Anh Load Tran  Â·  Multi-Account  v1.0     ".format(
        C.WHITE+C.BOLD))
    print("{}  JPG Â· PNG Â· WEBP Â· GIF Â· MP4  |  Acc chay song song  ".format(C.CYAN))
    print("{}{}".format(C.CYAN, "â"*62) + C.RESET)

    print("\n" + info("Kiem tra ket noi..."))
    if not check_connectivity():
        print(err("Khong co ket noi internet!")); sys.exit(1)
    print(ok("Mang OK"))

    # ---- Tim HAR ----
    use_one = (har_path_arg and har_path_arg != DEFAULT_HAR
               and os.path.exists(har_path_arg))
    if use_one:
        har_files = [Path(har_path_arg)]
    else:
        har_files = find_har_files(".")
        if not har_files and os.path.exists(DEFAULT_HAR):
            har_files = [Path(DEFAULT_HAR)]
    har_files = [h for h in har_files if h.exists()]

    if not har_files:
        print(err("Khong tim thay .har nao!")); sys.exit(1)

    # ---- Parse + hien thi ----
    print("\n" + bold("Phan tich {} file HAR:".format(len(har_files))))
    print("  {}{:<28}  {}{}" .format(C.GRAY, "File", "Trang thai", C.RESET))
    print("  " + sep(50, "â", C.GRAY))
    acc_info = []
    for idx_h, h in enumerate(har_files, 1):
        tok, upath = parse_har(str(h))
        status = ok("OK") if (tok and upath) else err("THIEU TOKEN/PATH")
        lbl    = h.stem
        print("  {}{:02d}.{} {:<28}  {}".format(
            C.YELLOW, idx_h, C.RESET, h.name[:28], status))
        acc_info.append({
            "har": str(h), "token": tok, "user_path": upath, "label": lbl
        })

    valid = [a for a in acc_info if a["token"] and a["user_path"]]
    if not valid:
        print(err("Khong co acc nao hop le!")); sys.exit(1)

    # ---- Chon acc ----
    selected = valid
    if len(valid) > 1:
        print("")
        print("  {}Nhap 'all' / ENTER = dung TAT CA {} acc{}".format(
            C.CYAN, len(valid), C.RESET))
        print("  {}Nhap STT cach nhau (vd: 1 3) = chon rieng{}".format(
            C.GRAY, C.RESET))
        raw = cinput("  > ")
        if raw and raw.lower() != "all":
            try:
                idxs = [int(x)-1 for x in raw.split()]
                sel  = [acc_info[i] for i in idxs
                        if 0<=i<len(acc_info) and acc_info[i]["token"]]
                if sel: selected = sel
                else: print(warn("Khong hop le â Dung tat ca"))
            except Exception:
                print(warn("Nhap sai â Dung tat ca"))

    n_acc = len(selected)
    print("\n  {} acc se chay {}SONG SONG{}:".format(
        n_acc, C.CYAN+C.BOLD, C.RESET))
    for a in selected:
        print("    {}â{} {}".format(C.CYAN, C.RESET, a["label"]))

    # ---- Scan media ----
    print("\n" + info("Quet media trong: " + image_dir))
    all_files = scan_media(image_dir)
    print("  Tim thay {} file:".format(len(all_files)))
    TYPE_COLORS = {
        ".jpg":  "{}JPG{}".format(C.YELLOW, C.RESET),
        ".jpeg": "{}JPG{}".format(C.YELLOW, C.RESET),
        ".png":  "{}PNG{}".format(C.CYAN,   C.RESET),
        ".webp": "{}WEBP{}".format(C.CYAN,  C.RESET),
        ".gif":  "{}GIF{}".format(C.GREEN+C.BOLD, C.RESET),
        ".mp4":  "{}MP4{}".format(C.PURPLE+C.BOLD, C.RESET),
    }
    for i, p in enumerate(all_files, 1):
        tc = TYPE_COLORS.get(p.suffix.lower(), p.suffix.upper())
        print("  {}[{}]{}  {}  {}  {:.1f} KB".format(
            C.YELLOW, i, C.RESET, tc, p.name, p.stat().st_size/1024))

    # ---- Phan cong anh ----
    if len(all_files) == 1:
        img_mode = "2"
        print("\n" + info("1 file duy nhat â tat ca acc dung chung."))
    else:
        if len(all_files) < n_acc:
            print("\n" + warn("{} file < {} acc â mode 1 se lap vong anh.".format(
                len(all_files), n_acc)))
        img_mode = ask_choice(
            "Che do phan cong media:",
            {"1":"Moi acc {}1 bo rieng{}  (acc1âfile1, acc2âfile2, ...)".format(
                C.BOLD, C.RESET),
             "2":"Tat ca acc dung {}chung{}  (toi da {} file/acc)".format(
                C.BOLD, C.RESET, MAX_MEDIA_PER_ACC)}
        )

    if img_mode == "1":
        print("\n  Phan cong (rieng):")
        for i, a in enumerate(selected):
            f = all_files[i % len(all_files)]
            print("    {}{}{}  â  {}".format(C.CYAN, a["label"][:30], C.RESET, f.name))
    else:
        shared = all_files[:MAX_MEDIA_PER_ACC]
        print("\n" + info("Dung chung {} file: {}".format(
            len(shared), ", ".join(p.name for p in shared))))

    # ---- Che do luu ----
    save_mode = ask_choice(
        "Che do LUU:",
        {"1":"{}Luu rieng{}  (chi minh toi dung)".format(C.CYAN, C.RESET),
         "2":"{}Quang truong{}  (moi nguoi thay)".format(C.YELLOW, C.RESET)}
    )
    is_share = (save_mode == "2")

    # ---- So vong ----
    if rounds_arg:
        rounds = max(1, rounds_arg)
    else:
        raw = cinput("\n  So vong lap (moi vong = {}s stagger/poster, ENTER=1): ".format(
            POSTER_STAGGER))
        try:
            rounds = int(raw) if raw else 1
            rounds = max(1, rounds)
        except ValueError:
            rounds = 1

    # ---- Pre-process media ----
    print("\n" + info("Xu ly media truoc khi chay..."))
    shared_media = None
    if img_mode == "2":
        shared_files = all_files[:MAX_MEDIA_PER_ACC]
        shared_media = []
        for p in shared_files:
            print(info("  Xu ly: {}".format(p.name)))
            shared_media.append(prepare_media(p))

    acc_media_map = {}
    for i, a in enumerate(selected):
        lbl = a["label"]
        if img_mode == "1":
            f = all_files[i % len(all_files)]
            print(info("  {} â {}".format(lbl[:25], f.name)))
            acc_media_map[lbl] = [prepare_media(f)]
        else:
            acc_media_map[lbl] = shared_media

    imgs_per    = len(shared_media) if img_mode == "2" else 1
    grand_total = rounds * imgs_per * n_acc
    print("\n  {} acc  Ã  {} vong  â  {}{}{}  poster tong".format(
        n_acc, rounds, C.CYAN+C.BOLD, grand_total, C.RESET))
    print(dim("  Stagger poster: {}s  |  Delay vong: {}s  |  Stagger acc: {}s".format(
        POSTER_STAGGER, ROUND_DELAY, ACC_STAGGER)))

    # ---- Confirm ----
    confirm = cinput("\n  Nhap 'ok' de bat dau, Ctrl+C de huy: ")
    if confirm.lower() != "ok":
        print(err("Huy")); sys.exit(0)

    # ---- Spawn threads ----
    acc_results = {}
    threads     = []
    print("\n" + bold("Bat dau {} acc SONG SONG...".format(n_acc)))
    for a in selected:
        t = threading.Thread(
            target=acc_worker,
            args=(a, acc_media_map[a["label"]], rounds, is_share, acc_results),
            daemon=True,
        )
        threads.append(t)

    for t in threads:
        t.start()
        time.sleep(ACC_STAGGER)

    for t in threads:
        t.join()

    # ---- Tong ket ----
    print("")
    print(sep(62, "â", C.CYAN))
    print("{}  TONG KET  ({} acc song song){}".format(
        C.WHITE+C.BOLD, n_acc, C.RESET))
    print(sep(62, "â", C.GRAY))
    grand_ok=grand_fail=0
    for a in selected:
        res = acc_results.get(a["label"],{"ok":0,"fail":0})
        ok_a, fail_a = res["ok"], res["fail"]
        grand_ok+=ok_a; grand_fail+=fail_a
        print("  {}{:<30}{}  {}OK:{:<4}{}  {}FAIL:{:<4}{}  TONG:{}".format(
            C.CYAN, a["label"][:30], C.RESET,
            C.GREEN, ok_a,   C.RESET,
            C.RED,   fail_a, C.RESET,
            ok_a+fail_a))
    print(sep(62, "â", C.GRAY))
    print("  {}TONG CONG:  OK={}{}{}  FAIL={}{}{}  /  {} poster{}".format(
        C.BOLD,
        C.GREEN, grand_ok,   C.RESET+C.BOLD,
        C.RED,   grand_fail, C.RESET+C.BOLD,
        grand_total, C.RESET))
    print(sep(62, "â", C.CYAN))
    print("\n  {}Mo game â Anh load tran de thay!{}\n".format(C.CYAN, C.RESET))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="KGVN Mod Anh Load Tran - Multi-Account Tool v1.0",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "TINH NANG:\n"
            "  * JPG / PNG / WEBP / GIF / MP4\n"
            "  * Delay 3.6s stagger fix loi -1999 frequency limited\n"
            "  * Acc chay song song dong thoi\n"
            "  * Giao dien mau sac\n"
            "\nCAI DAT:\n"
            "  pip install requests Pillow\n"
            "  # MP4: pkg install ffmpeg  hoac  apt install ffmpeg\n"
            "\nVI DU:\n"
            "  python load_tran.py\n"
            "  python load_tran.py --rounds 3\n"
            "  python load_tran.py --dir /sdcard/DCIM\n"
            "  python load_tran.py --har acc1.har\n"
        ),
    )
    ap.add_argument("--har",    default=DEFAULT_HAR)
    ap.add_argument("--dir",    default=".")
    ap.add_argument("--rounds", type=int, default=None)
    args = ap.parse_args()
    run(args.har, args.dir, args.rounds)
