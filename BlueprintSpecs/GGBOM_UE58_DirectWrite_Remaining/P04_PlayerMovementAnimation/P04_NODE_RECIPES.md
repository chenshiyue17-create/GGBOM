# P04 NODE RECIPES

IA_Move Triggered→ActionValue(Vector2D)→Set MoveInput→Normalize→AddMovementInput((X,Y,0))→bMoving=len>0.05→UpdateFacing8
Completed→MoveInput=(0,0),bMoving=false

UpdateFacing8:
Angle=Degrees(Atan2(Y,X))
E [-22.5,22.5)
NE [22.5,67.5)
N [67.5,112.5)
NW [112.5,157.5)
W >=157.5 or <-157.5
SW [-157.5,-112.5)
S [-112.5,-67.5)
SE [-67.5,-22.5)

Dash:
IA_Dash Started→Branch bCanDash&&!bDead
→bCanDash=false
→Health.SetInvulnerable(true)
→沿MoveInput或Facing方向快速位移
→Timer0.25 Health.SetInvulnerable(false)
→Timer1.2 bCanDash=true

YSort每次移动更新：
Priority=Clamp(500+Round(Y*-0.1),300,800)
SetTranslucentSortPriority

ABP:
Any→Death if bDead
Any→Hurt on trigger
Any→Dash if dash
Idle↔Run by bMoving
Attack/Reload/Revive one-shot后回Idle/Run
