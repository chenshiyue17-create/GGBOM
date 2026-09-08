# -*- coding: utf-8 -*-
import unreal

pc = unreal.PlayerController
print("Has WasInputKeyJustPressed:", hasattr(pc, "was_input_key_just_pressed"))
