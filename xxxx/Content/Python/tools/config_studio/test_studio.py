# -*- coding: utf-8 -*-
"""
端到端验证脚本：测试 Config Studio 全部 API 与数据流
"""
import urllib.request
import json

BASE_URL = "http://localhost:8899"

def run_tests():
    print("=== 开始端到端自动化测试 ===")
    
    # 1. 测试首页与资源
    for path, expected_status in [("/", 200), ("/style.css", 200), ("/app.js", 200)]:
        req = urllib.request.Request(f"{BASE_URL}{path}")
        with urllib.request.urlopen(req) as res:
            assert res.status == expected_status, f"{path} 状态码异常: {res.status}"
            content = res.read()
            assert len(content) > 0, f"{path} 内容为空"
            print(f"✅ {path}: OK ({len(content)} 字节)")

    # 2. 测试 /api/data
    req = urllib.request.Request(f"{BASE_URL}/api/data")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
        assert data["status"] == "success"
        assert "characters" in data and "Player_Medic" in data["characters"]
        assert "weapons" in data and "WPN_Rifle_Standard" in data["weapons"]
        assert "enemies" in data and "Enemy_Zombie_Walker" in data["enemies"]
        assert "tiles" in data and "Tile_Stage01_Z1" in data["tiles"]
        assert "hit_effects" in data and "FX_Hit_Sparks" in data["hit_effects"]

        # 校验子弹弹道与物理属性完整性
        rifle = data["weapons"]["WPN_Rifle_Standard"]
        for prop in ["BulletImage", "BulletScale", "ProjectileSpeed", "PierceCount", "LifeSpan", "CollisionRadius", "CollisionHeight"]:
            assert prop in rifle, f"武器缺少子弹物理属性: {prop}"

        # 校验战斗特效行结构
        sparks = data["hit_effects"]["FX_Hit_Sparks"]
        for prop in ["DisplayName", "EffectType", "VFXFolder", "Scale", "FPS", "LifeDuration", "HitStopDurationMs", "CameraShakeIntensity"]:
            assert prop in sparks, f"特效缺少属性: {prop}"

        print(f"✅ /api/data: OK (主角: {len(data['characters'])}, 武器: {len(data['weapons'])}, 怪物: {len(data['enemies'])}, 土地: {len(data['tiles'])}, 特效: {len(data['hit_effects'])})")

    # 3. 测试 /api/art-tree
    req = urllib.request.Request(f"{BASE_URL}/api/art-tree")
    with urllib.request.urlopen(req) as res:
        art_data = json.loads(res.read().decode('utf-8'))
        assert art_data["status"] == "success"
        all_files = art_data.get("all_files", [])
        print(f"✅ /api/art-tree: OK (素材库总计 {len(all_files)} 个切片贴图，顶层分类: {len(art_data['tree'])} 个)")

    # 4. 测试 /api/dir-frames 与 /api/vfx-frames
    test_dir = "01_Player/01_Idle_Run/Dir_01_Down/Idle"
    req = urllib.request.Request(f"{BASE_URL}/api/dir-frames?dir={urllib.parse.quote(test_dir)}")
    with urllib.request.urlopen(req) as res:
        frames_data = json.loads(res.read().decode('utf-8'))
        assert frames_data["status"] == "success"
        assert len(frames_data["frames"]) == 4
        print(f"✅ /api/dir-frames: OK ({test_dir} 包含 {len(frames_data['frames'])} 帧)")

    vfx_folder = "05_VFX/11_Hit_Kinetic"
    req_vfx = urllib.request.Request(f"{BASE_URL}/api/vfx-frames?folder={urllib.parse.quote(vfx_folder)}")
    with urllib.request.urlopen(req_vfx) as res:
        vfx_data = json.loads(res.read().decode('utf-8'))
        assert vfx_data["status"] == "success"
        assert len(vfx_data["frames"]) > 0
        print(f"✅ /api/vfx-frames: OK ({vfx_folder} 包含 {len(vfx_data['frames'])} 帧切片)")

    # 5. 测试 POST /api/save (包含 hit_effects 与子弹新属性落盘)
    save_payload = {
        "author": "端到端自动化测试器",
        "comment": "验证武器子弹全物理参数与战斗特效原子落盘",
        "characters": data["characters"],
        "weapons": data["weapons"],
        "enemies": data["enemies"],
        "cards": data["cards"],
        "waves": data["waves"],
        "tiles": data["tiles"],
        "hit_effects": data["hit_effects"]
    }
    save_req = urllib.request.Request(
        f"{BASE_URL}/api/save",
        data=json.dumps(save_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(save_req) as res:
        assert res.status == 200
        save_res = json.loads(res.read().decode("utf-8"))
        assert save_res["status"] == "success"
        mod_tables = save_res["commit"]["modified_tables"]
        assert "DT_HitEffects.json" in mod_tables
        assert "DT_Weapons.json" in mod_tables
        print(f"✅ /api/save: OK (原子化落盘与审计日志记录成功, 改动表: {mod_tables})")

    print("\n🎉 全部后端 API、武器子弹全物理属性与战斗特效工作台 100% 验证通过！")

if __name__ == "__main__":
    run_tests()
