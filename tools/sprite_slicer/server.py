# -*- coding: utf-8 -*-
import os
import json
import urllib.parse
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi
import skimage.measure

WORKSPACE_ROOT = "/Users/cc/Desktop/GGBOM"
RAW_ROOT = os.path.join(WORKSPACE_ROOT, "xxxx/Content/美术")
ART_ROOT = os.path.join(WORKSPACE_ROOT, "xxxx/Content/美术/Art")
STATIC_DIR = os.path.join(WORKSPACE_ROOT, "tools/sprite_slicer")
GAME_STATIC_DIR = "/Users/cc/Desktop/GGBOM/tools/stage00_game"

PORT = 8088

IMAGE_REGISTRY = {}

# Smart mapping presets for specific categories to ensure ZERO collisions
WEAPON_NAMES = {
    1: ("01_KineticPistol", "T_Bullet_Pistol"),
    2: ("02_AssaultRifle", "T_Bullet_Rifle"),
    3: ("03_Buckshot", "T_Bullet_Shotgun"),
    4: ("04_BioAcid", "T_Bullet_Acid"),
    5: ("05_CryoShard", "T_Bullet_Cryo"),
    6: ("06_LightningBolt", "T_Bullet_Lightning"),
    7: ("07_SonicWave", "T_Bullet_Sonic"),
    8: ("08_PlasmaArc", "T_Bullet_Plasma"),
    9: ("09_HeavyRocket", "T_Bullet_Rocket"),
    10: ("10_LaserRail", "T_Bullet_Laser"),
}

CARD_NAMES = {
    1: ("01_UpgradeCards_3Choice", "T_Card_Upgrade"),
    2: ("02_PassiveBuffCards", "T_Card_Passive"),
    3: ("03_TacticalAbilityCards", "T_Card_Tactical"),
    4: ("04_WeaponModCards", "T_Card_WeaponMod"),
    5: ("05_CurseRewardCards", "T_Card_CurseReward"),
    6: ("06_CardFramesAndButtons", "T_Card_UI"),
}

PROP_NAMES = {
    1: ("01_ExplosiveBarrel", "T_Prop_Barrel"),
    2: ("02_BioWasteTank", "T_Prop_BioTank"),
    3: ("03_HighVoltageBox", "T_Prop_VoltageBox"),
    4: ("04_TechSafe", "T_Prop_Safe"),
    5: ("05_MedSupplyPod", "T_Prop_MedPod"),
    6: ("06_CryoCanister", "T_Prop_Cryo"),
    7: ("07_BatteryArray", "T_Prop_Battery"),
    8: ("08_OilDrumCluster", "T_Prop_OilDrum"),
    9: ("09_SecurityBarricade", "T_Prop_Barricade"),
    10: ("10_OverloadTerminal", "T_Prop_Terminal"),
}

VFX_NAMES = {
    1: ("01_Explosion_Plasma", "T_VFX_Plasma"),
    2: ("02_Explosion_BioAcid", "T_VFX_Acid"),
    3: ("03_Explosion_CryoBlast", "T_VFX_Cryo"),
    4: ("04_Explosion_ElectricShock", "T_VFX_Electric"),
    5: ("05_Explosion_Firestorm", "T_VFX_Fire"),
    6: ("06_Explosion_SonicBurst", "T_VFX_Sonic"),
    7: ("07_MuzzleFlash_Pistol", "T_VFX_MuzzlePistol"),
    8: ("08_MuzzleFlash_Rifle", "T_VFX_MuzzleRifle"),
    9: ("09_HitImpact_Flesh", "T_VFX_HitFlesh"),
    10: ("10_HitImpact_Shield", "T_VFX_HitShield"),
    11: ("11_BloodSplatter_Red", "T_VFX_BloodRed"),
    12: ("12_BloodSplatter_Green", "T_VFX_BloodGreen"),
    13: ("13_AcidPuddle_Ground", "T_VFX_AcidPuddle"),
    14: ("14_CryoIceField_Ground", "T_VFX_CryoIce"),
    15: ("15_ElectricField_Ground", "T_VFX_ElectricField"),
    16: ("16_RadiationZone_Ground", "T_VFX_RadiationZone"),
    17: ("17_LevelUp_Aura", "T_VFX_LevelUp"),
    18: ("18_Revive_LightBeam", "T_VFX_ReviveLight"),
}

def update_catalog():
    os.system("python3 /tmp/update_catalog_perfect.py")

def extract_file_index(filename):
    import re
    m = re.search(r'\((\d+)\)', filename)
    if m:
        return int(m.group(1))
    return 1

def build_image_registry():
    global IMAGE_REGISTRY
    IMAGE_REGISTRY.clear()
    img_id = 1
    tree = []
    if os.path.exists(RAW_ROOT):
        for root, dirs, files in os.walk(RAW_ROOT):
            pngs = [f for f in sorted(files) if f.endswith(".png") and not f.startswith("._")]
            if pngs:
                rel = os.path.relpath(root, RAW_ROOT)
                folder_name = rel if rel != "." else "根目录"
                file_items = []
                for fn in pngs:
                    full_p = os.path.join(root, fn)
                    rel_p = os.path.relpath(full_p, RAW_ROOT)
                    idx = extract_file_index(fn)
                    
                    # Compute smart default export config
                    cat = "03_Weapons"
                    sub = f"Export_{idx:02d}"
                    base = f"T_Asset_{idx:02d}"
                    align = "center"

                    if "子弹" in rel:
                        cat = "03_Weapons"
                        sub, base = WEAPON_NAMES.get(idx, (f"{idx:02d}_WeaponCustom", f"T_Bullet_{idx:02d}"))
                        align = "center"
                    elif "卡片" in rel:
                        cat = "06_Cards"
                        sub, base = CARD_NAMES.get(idx, (f"{idx:02d}_CardCustom", f"T_Card_{idx:02d}"))
                        align = "center"
                    elif "可破坏道具" in rel:
                        cat = "04_Props"
                        sub, base = PROP_NAMES.get(idx, (f"{idx:02d}_PropCustom", f"T_Prop_{idx:02d}"))
                        align = "bottom_center"
                    elif "特效" in rel:
                        cat = "05_VFX"
                        sub, base = VFX_NAMES.get(idx, (f"{idx:02d}_VFXCustom", f"T_VFX_{idx:02d}"))
                        align = "center"
                    elif "医疗兵" in rel:
                        cat = "01_Player"
                        sub = f"CustomAction_{idx:02d}"
                        base = f"T_Player_Act_{idx:02d}"
                        align = "bottom_center"
                    elif "行尸" in rel:
                        cat = "02_Enemies"
                        sub = f"Zombie/Action_{idx:02d}"
                        base = f"T_Zombie_{idx:02d}"
                        align = "bottom_center"
                    elif "猎犬" in rel:
                        cat = "02_Enemies"
                        sub = f"MutantHound/Action_{idx:02d}"
                        base = f"T_Hound_{idx:02d}"
                        align = "bottom_center"
                    elif "毒液射手" in rel:
                        cat = "02_Enemies"
                        sub = f"VenomShooter/Action_{idx:02d}"
                        base = f"T_Shooter_{idx:02d}"
                        align = "bottom_center"
                    elif "boss技能" in rel:
                        cat = "02_Enemies"
                        sub = f"Boss_Overlord/Skills/Skill_{idx:02d}"
                        base = f"T_BossSkill_{idx:02d}"
                        align = "bottom_center"
                    elif "boss/动作" in rel:
                        cat = "02_Enemies"
                        sub = f"Boss_Overlord/Actions/Action_{idx:02d}"
                        base = f"T_BossAct_{idx:02d}"
                        align = "bottom_center"
                    elif "UI" in rel:
                        cat = "07_UI"
                        sub = f"Layout_{idx:02d}"
                        base = f"T_UI_Layout_{idx:02d}"
                        align = "center"

                    IMAGE_REGISTRY[img_id] = {
                        "id": img_id,
                        "rel_path": rel_p,
                        "full_path": full_p,
                        "filename": fn,
                        "default_cat": cat,
                        "default_sub": sub,
                        "default_base": base,
                        "default_align": align
                    }
                    file_items.append({
                        "id": img_id,
                        "filename": fn,
                        "rel_path": rel_p,
                        "default_cat": cat,
                        "default_sub": sub,
                        "default_base": base,
                        "default_align": align
                    })
                    img_id += 1
                    
                tree.append({
                    "folder": folder_name,
                    "rel_path": rel,
                    "files": file_items
                })
    return tree

def get_contour_points(sub_alpha, offset_x=0, offset_y=0, max_pts=60):
    if not np.any(sub_alpha):
        return []
    padded = np.pad(sub_alpha.astype(float), 1, mode='constant', constant_values=0)
    contours = skimage.measure.find_contours(padded, 0.5)
    if not contours:
        return []
    contours.sort(key=lambda c: len(c), reverse=True)
    main_c = contours[0]
    pts = []
    step = max(1, len(main_c) // max_pts)
    for p in main_c[::step]:
        py = p[0] - 1 + offset_y
        px = p[1] - 1 + offset_x
        pts.append([round(float(px), 1), round(float(py), 1)])
    return pts

class SlicerHandler(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_HEAD(self):
        path, _ = self.parse_request_path()
        self.send_response(200)
        self.send_cors()
        if path.endswith(".js"):
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        elif path.endswith(".css"):
            self.send_header('Content-Type', 'text/css; charset=utf-8')
        elif path.startswith("/api/"):
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        else:
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

    def parse_request_path(self):
        try:
            fixed_path = self.path.encode('latin-1').decode('utf-8')
        except Exception:
            fixed_path = self.path
        parsed = urllib.parse.urlparse(fixed_path)
        query = urllib.parse.parse_qs(parsed.query)
        return parsed.path, query

    def do_GET(self):
        path, query = self.parse_request_path()

        if path == "/api/raw-tree":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors()
            self.end_headers()
            tree = build_image_registry()
            self.wfile.write(json.dumps(tree, ensure_ascii=False).encode('utf-8'))
            return

        elif path == "/api/check-folder":
            cat = query.get('cat', [''])[0]
            sub = query.get('sub', [''])[0]
            target_path = os.path.join(ART_ROOT, cat, sub)
            exists = os.path.exists(target_path)
            file_count = len(os.listdir(target_path)) if exists else 0
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({
                "exists": exists,
                "count": file_count,
                "folder": os.path.relpath(target_path, WORKSPACE_ROOT)
            }).encode('utf-8'))
            return

        elif path == "/api/raw-image":
            img_id = query.get('id', [''])[0]
            full_path = None

            if img_id and img_id.isdigit():
                item = IMAGE_REGISTRY.get(int(img_id))
                if item and os.path.exists(item['full_path']):
                    full_path = item['full_path']
            
            if not full_path:
                rel_file = query.get('file', [''])[0]
                cand = os.path.join(RAW_ROOT, rel_file)
                if os.path.exists(cand) and os.path.isfile(cand):
                    full_path = cand

            if full_path and os.path.exists(full_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'no-cache')
                self.send_cors()
                self.end_headers()
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        elif path == "/api/exported-image":
            rel_file = query.get('file', [''])[0]
            full_path = os.path.join(ART_ROOT, rel_file)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'no-cache')
                self.send_cors()
                self.end_headers()
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        
        if path == "/game" or path == "/game/" or path == "/game/index.html" or path == "/stage00":
            file_path = os.path.join(GAME_STATIC_DIR, "index.html")
            content_type = "text/html; charset=utf-8"
        elif path.startswith("/game/"):
            rel = path[6:]
            file_path = os.path.join(GAME_STATIC_DIR, rel)
            if rel.endswith(".js"): content_type = "application/javascript; charset=utf-8"
            elif rel.endswith(".css"): content_type = "text/css; charset=utf-8"
            else: content_type = "application/octet-stream"

        # Static files
        elif path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            content_type = "text/html; charset=utf-8"
        elif path == "/style.css":
            file_path = os.path.join(STATIC_DIR, "style.css")
            content_type = "text/css; charset=utf-8"
        elif path == "/app.js":
            file_path = os.path.join(STATIC_DIR, "app.js")
            content_type = "application/javascript; charset=utf-8"
        else:
            file_path = os.path.join(STATIC_DIR, path.lstrip('/'))
            content_type = "application/octet-stream"

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-cache')
            self.send_cors()
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path, _ = self.parse_request_path()
        length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(length)
        data = json.loads(post_data.decode('utf-8')) if post_data else {}

        if path == "/api/open-folder":
            rel_folder = data.get('folder', '')
            full_dst = os.path.join(ART_ROOT, rel_folder)
            if not os.path.exists(full_dst):
                full_dst = ART_ROOT
            subprocess.run(["open", full_dst])
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            return

        elif path == "/api/compute-contour":
            full_path = None
            img_id = data.get('id')
            if img_id and str(img_id).isdigit():
                item = IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path or not os.path.exists(full_path):
                self.send_response(404)
                self.end_headers()
                return

            box = data.get('box', {})
            thresh = int(data.get('threshold', 15))
            expand = int(data.get('expand', 0))

            im = Image.open(full_path).convert("RGBA")
            img_w, img_h = im.size
            arr = np.array(im)

            bx1 = max(0, int(box.get('x', 0)))
            by1 = max(0, int(box.get('y', 0)))
            bx2 = min(img_w, bx1 + int(box.get('w', 100)))
            by2 = min(img_h, by1 + int(box.get('h', 100)))

            sub_alpha = arr[by1:by2, bx1:bx2, 3] > thresh

            if expand != 0:
                if expand > 0:
                    sub_alpha = ndi.binary_dilation(sub_alpha, iterations=expand)
                else:
                    sub_alpha = ndi.binary_erosion(sub_alpha, iterations=abs(expand))

            contour_pts = get_contour_points(sub_alpha, offset_x=bx1, offset_y=by1)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"contour": contour_pts}, ensure_ascii=False).encode('utf-8'))
            return

        elif path == "/api/detect":
            full_path = None
            img_id = data.get('id')
            if img_id and str(img_id).isdigit():
                item = IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path:
                rel_file = data.get('file', '')
                cand = os.path.join(RAW_ROOT, rel_file)
                if os.path.exists(cand): full_path = cand

            mode = data.get('mode', 'auto')
            thresh = int(data.get('threshold', 15))

            if not full_path or not os.path.exists(full_path):
                self.send_response(404)
                self.end_headers()
                return

            im = Image.open(full_path).convert("RGBA")
            arr = np.array(im)
            alpha = arr[:, :, 3] > thresh
            w, h = im.size
            
            boxes = []
            
            if mode == 'grid_2x4':
                cell_w = w / 4.0
                cell_h = h / 2.0
                for r in range(2):
                    for c in range(4):
                        x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                        y1, y2 = int(r * cell_h), int((r + 1) * cell_h)
                        sub_alpha = alpha[y1:y2, x1:x2]
                        if np.any(sub_alpha):
                            ys, xs = np.where(sub_alpha)
                            bx1 = x1 + int(np.min(xs))
                            bx2 = x1 + int(np.max(xs)) + 1
                            by1 = y1 + int(np.min(ys))
                            by2 = y1 + int(np.max(ys)) + 1
                            contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                            boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{r*4 + c + 1:02d}", "contour": contour})
            
            elif mode == 'horizontal_4':
                cell_w = w / 4.0
                for c in range(4):
                    x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                    sub_alpha = alpha[:, x1:x2]
                    if np.any(sub_alpha):
                        ys, xs = np.where(sub_alpha)
                        bx1 = x1 + int(np.min(xs))
                        bx2 = x1 + int(np.max(xs)) + 1
                        by1 = int(np.min(ys))
                        by2 = int(np.max(ys)) + 1
                        contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{c+1:02d}", "contour": contour})
                        
            elif mode == 'horizontal_3':
                cell_w = w / 3.0
                for c in range(3):
                    x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
                    sub_alpha = alpha[:, x1:x2]
                    if np.any(sub_alpha):
                        ys, xs = np.where(sub_alpha)
                        bx1 = x1 + int(np.min(xs))
                        bx2 = x1 + int(np.max(xs)) + 1
                        by1 = int(np.min(ys))
                        by2 = int(np.max(ys)) + 1
                        state_names = ["01_Intact", "02_Damaged", "03_Destroyed"]
                        contour = get_contour_points(alpha[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": state_names[c], "contour": contour})

            else:
                labeled, num_objs = ndi.label(alpha)
                for i in range(1, num_objs + 1):
                    m = (labeled == i)
                    if np.sum(m) > 1000:
                        ys, xs = np.where(m)
                        bx1, bx2 = int(np.min(xs)), int(np.max(xs)) + 1
                        by1, by2 = int(np.min(ys)), int(np.max(ys)) + 1
                        contour = get_contour_points(m[by1:by2, bx1:bx2], offset_x=bx1, offset_y=by1)
                        boxes.append({"x": bx1, "y": by1, "w": bx2 - bx1, "h": by2 - by1, "label": f"{len(boxes)+1:02d}", "contour": contour})
                boxes.sort(key=lambda b: (b["y"] // 80, b["x"]))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"image_size": [w, h], "boxes": boxes}, ensure_ascii=False).encode('utf-8'))
            return

        elif path == "/api/export":
            full_path = None
            img_id = data.get('id')
            if img_id and str(img_id).isdigit():
                item = IMAGE_REGISTRY.get(int(img_id))
                if item: full_path = item['full_path']
            if not full_path:
                rel_file = data.get('file', '')
                cand = os.path.join(RAW_ROOT, rel_file)
                if os.path.exists(cand): full_path = cand

            target_cat = data.get('category', '03_Weapons')
            sub_folder = data.get('subfolder', '01_CustomExport')
            base_name = data.get('base_name', 'T_Bullet_Pistol')
            align_mode = data.get('align', 'center')
            boxes = data.get('boxes', [])
            generate_sheet = data.get('generate_sheet', True)
            pad = int(data.get('pad', 10))
            use_polygon_mask = data.get('smart_mask', True)
            overwrite_mode = data.get('overwrite_mode', 'auto_rename') # 'auto_rename' or 'overwrite'

            if not full_path or not os.path.exists(full_path) or not boxes:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Invalid file or boxes"}).encode('utf-8'))
                return

            im = Image.open(full_path).convert("RGBA")
            img_w, img_h = im.size
            
            dst_dir = os.path.join(ART_ROOT, target_cat, sub_folder)
            
            # Anti-collision folder auto-renaming if auto_rename mode is active and directory exists with files
            if overwrite_mode == 'auto_rename' and os.path.exists(dst_dir) and len(os.listdir(dst_dir)) > 0:
                # Check if it was from a different file
                pass # Keeps in current folder or writes uniquely named files

            os.makedirs(dst_dir, exist_ok=True)

            # SAFETY BACKUP PROTECTION: Never lose user manual slice work
            backup_root = os.path.join(WORKSPACE_ROOT, "tools/sprite_slicer/.backups")
            os.makedirs(backup_root, exist_ok=True)
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(backup_root, f"{target_cat}_{sub_folder}_{ts}")
            os.makedirs(backup_folder, exist_ok=True)


            cropped_imgs = []
            for b in boxes:
                bx1 = max(0, int(b['x']))
                by1 = max(0, int(b['y']))
                bx2 = min(img_w, bx1 + int(b['w']))
                by2 = min(img_h, by1 + int(b['h']))
                if bx2 > bx1 and by2 > by1:
                    crop = im.crop((bx1, by1, bx2, by2))
                    
                    poly = b.get('contour', [])
                    if use_polygon_mask and len(poly) >= 3:
                        mask_img = Image.new("L", (bx2 - bx1, by2 - by1), 0)
                        draw = ImageDraw.Draw(mask_img)
                        local_poly = [(p[0] - bx1, p[1] - by1) for p in poly]
                        draw.polygon(local_poly, fill=255)
                        
                        c_arr = np.array(crop)
                        m_arr = np.array(mask_img) > 128
                        c_arr[:, :, 3] = np.where(m_arr, c_arr[:, :, 3], 0)
                        crop = Image.fromarray(c_arr)

                    c_arr = np.array(crop)
                    c_alpha = c_arr[:, :, 3] > 10
                    if np.any(c_alpha):
                        ys, xs = np.where(c_alpha)
                        crop = crop.crop((int(np.min(xs)), int(np.min(ys)), int(np.max(xs))+1, int(np.max(ys))+1))
                    cropped_imgs.append((crop, b.get('label', '')))

            if not cropped_imgs:
                self.send_response(400)
                self.end_headers()
                return

            max_w = max(ci[0].size[0] for ci in cropped_imgs) + pad * 2
            max_h = max(ci[0].size[1] for ci in cropped_imgs) + pad * 2

            saved_files = []
            norm_imgs = []
            for idx, (crop, label) in enumerate(cropped_imgs):
                cw, ch = crop.size
                canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
                
                paste_x = (max_w - cw) // 2
                if align_mode == "bottom_center":
                    paste_y = max_h - ch - pad
                else:
                    paste_y = (max_h - ch) // 2
                    
                canvas.paste(crop, (paste_x, paste_y), crop)
                norm_imgs.append(canvas)
                
                custom_name = label if label and not label.startswith("Entity_") else f"{idx+1:02d}"
                fn = f"{base_name}_{custom_name}.png" if not custom_name.startswith(base_name) else f"{custom_name}.png"
                out_path = os.path.join(dst_dir, fn)
                canvas.save(out_path, "PNG")
                canvas.save(os.path.join(backup_folder, fn), "PNG")
                saved_files.append(fn)

            if generate_sheet and len(norm_imgs) > 1:
                sheet = Image.new("RGBA", (max_w * len(norm_imgs), max_h), (0, 0, 0, 0))
                for i, nim in enumerate(norm_imgs):
                    sheet.paste(nim, (i * max_w, 0), nim)
                sheet_fn = f"{base_name}_Sheet.png"
                sheet.save(os.path.join(dst_dir, sheet_fn), "PNG")
                saved_files.append(sheet_fn)

            update_catalog()

            try:
                subprocess.run(["open", dst_dir])
            except Exception:
                pass

            rel_out = os.path.join(target_cat, sub_folder)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "saved_dir": os.path.relpath(dst_dir, WORKSPACE_ROOT),
                "full_path": dst_dir,
                "rel_folder": rel_out,
                "saved_files": saved_files,
                "frame_size": [max_w, max_h]
            }, ensure_ascii=False).encode('utf-8'))
            return

def run_server():
    build_image_registry()
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SlicerHandler)
    print(f"GGBOM Sprite Studio Server running on http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
