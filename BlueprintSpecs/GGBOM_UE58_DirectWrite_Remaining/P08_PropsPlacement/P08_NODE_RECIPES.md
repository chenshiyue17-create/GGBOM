# P08 NODE RECIPES

Prop HealthChanged:
Pct=HP/Max
Pct<=0→Destroyed
else Pct<=0.5且Intact→Damaged
SetSprite

OnDeath:
若ExplosionRadius>0→SphereOverlap→Implements Combat→Damage.Explosion
Disable/adjust collision

Placement Update(ScreenPos):
DeprojectScreenPositionToWorld
LineTrace PlacementGround
Hit? Candidate=HitLocation+ZOffset
Snap X/Y Round(Value/Grid)*Grid
SlopeValid=Dot(HitNormal,Up)>=0.92
BoxOverlap footprint
Ignore Player+Preview
bValid=SlopeValid&&NoBlocking
Preview green/red

Commit:
再次Update/Validate
若invalid return false
Inventory.ConsumeItem(ItemID,1)
若false return
SpawnActor PlaceableClass
OnPlaced
清Preview
