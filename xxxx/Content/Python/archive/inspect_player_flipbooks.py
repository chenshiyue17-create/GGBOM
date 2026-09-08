import unreal

assets = unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
player_flipbooks = [a for a in assets if "Flipbook" in a and "Player" in a or "Medic" in a]

print(f"Total player flipbooks found: {len(player_flipbooks)}")
for fb in sorted(player_flipbooks):
    print(" ", fb)
