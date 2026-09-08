# -*- coding: utf-8 -*-
"""
修复子弹阻挡角色问题:
1. 将 BP_ProjectileBase 的所有组件（BulletFlipbook、根组件等）碰撞预设规范为 OverlapAllDynamic
2. 对 ECC_Pawn 显式设置响应为 ECR_Ignore（彻底杜绝子弹阻挡或推着玩家走）
3. 确保 GenerateOverlapEvents 为 True
4. 编译并保存资产
"""
import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

def fix_projectile_collision():
    print(f"🚀 [1/2] 正在修复子弹蓝图碰撞: {PROJ_BP_PATH}...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到资产: {PROJ_BP_PATH}")
    
    # 1. 遍历蓝图 Subobjects
    handles = unreal.SubobjectDataBlueprintFunctionLibrary.k2_gather_subobject_data_for_blueprint(bp)
    fixed_count = 0
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj and isinstance(obj, unreal.PrimitiveComponent):
            try:
                obj.set_collision_profile_name("OverlapAllDynamic")
                obj.set_editor_property("generate_overlap_events", True)
                obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_IGNORE)
                print(f"  - 已设置 Subobject '{vname}' ({obj.get_class().get_name()}): OverlapAllDynamic, Pawn=Ignore")
                fixed_count += 1
            except Exception as e:
                print(f"  - Subobject '{vname}' 设置警告: {e}")
                
    # 2. 编译蓝图使组件更新生效
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    
    # 3. CDO 属性校验与补强
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        for c in cdo.get_components_by_class(unreal.PrimitiveComponent):
            try:
                c.set_collision_profile_name("OverlapAllDynamic")
                c.set_editor_property("generate_overlap_events", True)
                c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_IGNORE)
                print(f"  - 已设置 CDO Component '{c.get_name()}': OverlapAllDynamic, Pawn=Ignore")
            except Exception as e:
                print(f"  - CDO Component 设置警告: {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 碰撞通道已彻底设为 OverlapAllDynamic 且 Ignore Pawn！")

def verify_player_collision():
    print(f"🔍 [2/2] 检查主角蓝图碰撞: {PLAYER_BP_PATH}...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        print(f"未找到主角: {PLAYER_BP_PATH}")
        return
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        for c in cdo.get_components_by_class(unreal.PrimitiveComponent):
            prof = c.get_editor_property("collision_profile_name")
            pawn_resp = c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
            print(f"  - 玩家组件 '{c.get_name()}' Profile='{prof}', PawnResp={pawn_resp}")

if __name__ == "__main__":
    fix_projectile_collision()
    verify_player_collision()
    print("🎉 子弹防阻挡物理通道修复成功！")
