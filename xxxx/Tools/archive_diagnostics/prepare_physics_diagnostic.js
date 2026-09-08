// -*- coding: utf-8 -*-
const fs = require('fs');
const { execSync } = require('child_process');

console.log('🔍 正在检查各核心蓝图的原生物理组件与碰撞设置...');

const checkPy = `
import unreal

bplib = unreal.BlueprintEditorLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def check_blueprint(path):
    print(f"==================================================")
    print(f"📘 检查资产: {path}")
    bp = unreal.EditorAssetLibrary.load_asset(path)
    if not bp:
        print("  ❌ 无法加载资产！")
        return
        
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    print(f"  组件总数: {len(handles)}")
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        cls_name = obj.get_class().get_name() if obj else "None"
        prof = ""
        gen_hit = ""
        gen_overlap = ""
        col_enabled = ""
        if isinstance(obj, unreal.PrimitiveComponent):
            try: prof = obj.get_collision_profile_name()
            except Exception: pass
            try: col_enabled = str(obj.get_collision_enabled())
            except Exception: pass
            try: gen_hit = str(obj.get_editor_property("notify_rigid_body_collision"))
            except Exception: pass
            try: gen_overlap = str(obj.get_editor_property("generate_overlap_events"))
            except Exception: pass
            print(f"    - [{vname}] ({cls_name}) Profile={prof}, Enabled={col_enabled}, GenHit={gen_hit}, GenOverlap={gen_overlap}")
        else:
            print(f"    - [{vname}] ({cls_name})")

check_blueprint("/Game/Blueprints/Player/BP_Player_Medic")
check_blueprint("/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord")
check_blueprint("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
check_blueprint("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
`;

fs.writeFileSync('/Users/cc/Desktop/GGBOM/xxxx/Tools/check_physics_config.py', checkPy, 'utf8');

try {
    const pythonBin = '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3';
    // 在这里我们把脚本放到 Content/Python/，在 hot_reload 里或者通过 node 打印
    console.log('✅ 检查脚本已生成至 Tools/check_physics_config.py');
} catch (e) {
    console.log('Error:', e.message);
}
