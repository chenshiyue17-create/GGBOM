import os
import sys
import json
import unreal

def log(msg):
    unreal.log(f"[AUDIT_COMBAT] {msg}")
    print(f"[AUDIT_COMBAT] {msg}")

def audit():
    results = {}
    
    # 1. 检查关卡 MAP_GGBOM_Main.umap 中的默认设置
    world_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    world_asset = unreal.EditorAssetLibrary.load_asset(world_path)
    results["world_loaded"] = world_asset is not None
    
    # 2. 检查所有相关的 Projectile 蓝图资产
    projectile_paths = [
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
        "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion",
        "/Game/Blueprints/Projectiles/BP_Projectile_Base",
        "/Game/Blueprints/Projectiles/BP_Bullet_KineticPistol",
        "/Game/Blueprints/Projectiles/BP_Bullet_AssaultRifle",
        "/Game/Blueprints/Projectiles/BP_Bullet_Buckshot",
        "/Game/Blueprints/Projectiles/BP_Bullet_LaserRail",
        "/Game/Blueprints/Projectiles/BP_Bullet_MicroMissile",
        "/Game/Blueprints/Projectiles/BP_Bullet_PlasmaArc",
        "/Game/Blueprints/Projectiles/BP_Bullet_Incendiary",
        "/Game/Blueprints/Projectiles/BP_Bullet_BioAcid",
        "/Game/Blueprints/Projectiles/BP_Bullet_ToxicSpore",
        "/Game/Blueprints/Projectiles/BP_Bullet_VenomHeavy"
    ]
    
    proj_info = {}
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    
    for p in projectile_paths:
        bp = unreal.EditorAssetLibrary.load_asset(p)
        if not bp:
            proj_info[p] = {"exists": False}
            continue
            
        gen_class = bp.generated_class()
        class_str = str(gen_class) if gen_class else "None"
        
        components = []
        try:
            subobjects = subsystem.k2_gather_subobject_data_for_blueprint(bp)
            for handle in subobjects:
                obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(handle, bp)
                if obj and isinstance(obj, unreal.ActorComponent):
                    comp_data = {
                        "name": obj.get_name(),
                        "class": obj.get_class().get_name()
                    }
                    if hasattr(obj, "get_sprite"):
                        try:
                            sprite = obj.get_sprite()
                            comp_data["sprite"] = sprite.get_path_name() if sprite else "None"
                        except Exception as e:
                            comp_data["sprite_err"] = str(e)
                    if hasattr(obj, "get_flipbook"):
                        try:
                            fb = obj.get_flipbook()
                            comp_data["flipbook"] = fb.get_path_name() if fb else "None"
                        except Exception as e:
                            comp_data["flipbook_err"] = str(e)
                    if hasattr(obj, "is_visible"):
                        try:
                            comp_data["visible"] = obj.is_visible()
                        except Exception:
                            pass
                    components.append(comp_data)
        except Exception as e:
            log(f"Error gathering subobjects for {p}: {e}")
                
        cdo = unreal.get_default_object(gen_class) if gen_class else None
        cdo_vars = {}
        if cdo:
            for prop_name in ["damage", "Damage", "speed", "Speed", "initial_speed", "InitialSpeed", "max_speed", "MaxSpeed", "pierce_count", "PierceCount"]:
                if hasattr(cdo, prop_name):
                    try:
                        cdo_vars[prop_name] = getattr(cdo, prop_name)
                    except Exception:
                        pass
                        
        proj_info[p] = {
            "exists": True,
            "gen_class": class_str,
            "components": components,
            "cdo_vars": cdo_vars
        }
        
    results["projectiles"] = proj_info
    
    # 3. 检查武器蓝图与数据表
    weapon_paths = [
        "/Game/Blueprints/Combat/Weapons/BP_WeaponBase",
        "/Game/Blueprints/Combat/Components/BPC_WeaponComponent",
        "/Game/Blueprints/Core/Components/BPC_WeaponInventory",
        "/Game/Blueprints/Player/BP_Player_Medic"
    ]
    weapon_info = {}
    for wp in weapon_paths:
        asset = unreal.EditorAssetLibrary.load_asset(wp)
        if not asset:
            weapon_info[wp] = {"exists": False}
            continue
        weapon_info[wp] = {
            "exists": True,
            "class": asset.get_class().get_name()
        }
        # 搜集武器类的属性和默认子弹类
        if isinstance(asset, unreal.Blueprint):
            w_cdo = unreal.get_default_object(asset.generated_class())
            if w_cdo:
                w_props = {}
                for pn in ["projectile_class", "ProjectileClass", "bullet_class", "BulletClass", "default_weapon_id", "DefaultWeaponId"]:
                    if hasattr(w_cdo, pn):
                        try:
                            val = getattr(w_cdo, pn)
                            w_props[pn] = str(val)
                        except Exception:
                            pass
                weapon_info[wp]["cdo_props"] = w_props
                
    results["weapons"] = weapon_info
    
    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/full_combat_audit.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    log(f"全量审计已成功完成并落盘: {out_path}")

try:
    audit()
except Exception as e:
    log(f"Audit failed with exception: {e}")
    sys.exit(1)
