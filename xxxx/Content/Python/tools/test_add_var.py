# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
pin_type = unreal.EdGraphPinType()
pin_type.pin_category = "bool"
unreal.BlueprintEditorLibrary.add_new_variable(bp, "bFacingRight", pin_type)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
print("ADD_VAR_SUCCESS")
