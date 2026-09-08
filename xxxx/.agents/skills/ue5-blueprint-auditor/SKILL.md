---
name: ue5-blueprint-auditor
description: >
  General-purpose Unreal Engine 5 Blueprint auditor for any UE5 project.
  Audits Blueprint assets, parent classes, variables, functions, macros,
  interfaces, components, event graphs, construction scripts, animation
  blueprints, UMG widgets, input, AI, replication, SaveGame, data dependencies,
  runtime behavior, logs, integration, performance, packaging evidence, and
  acceptance tests. Read-only by default. Never treats asset existence,
  compilation success, generated scripts, or unconditional PASS logs as proof
  of functional correctness.
---

# UE5 Blueprint Auditor

## Mission

Independently verify that Unreal Engine 5 Blueprint work is actually implemented,
structurally correct, functionally correct, integrated, reproducible, and free
of blocking runtime defects.

This skill is project-agnostic.

It must work with:
- UE5.0+
- first-person, third-person, top-down, 2D, 3D, mobile, desktop, console projects;
- single-player and multiplayer;
- pure Blueprint and mixed Blueprint/C++ projects;
- gameplay, UI, animation, AI, tools, editor utilities, data-driven systems.

The auditor does not assume any specific game architecture.

---

# 1. Default mode

Default:
`READ_ONLY_AUDIT`

Do not modify production content.

Forbidden unless user explicitly enables mutation:
- rewiring Event Graphs;
- changing variable defaults;
- changing parent classes;
- changing Project Settings;
- modifying DataTables/DataAssets;
- editing UMG layout;
- fixing replication settings;
- deleting/replacing production assets;
- adding fake PASS markers.

Allowed:
- inspect assets;
- open Blueprint graphs;
- inspect Class Defaults;
- inspect components;
- inspect interfaces;
- inspect dependencies;
- inspect animation graphs/state machines;
- inspect UMG hierarchy;
- inspect networking settings;
- inspect Project Settings;
- run PIE;
- run Functional Tests / Automation Tests;
- inspect Output Log;
- inspect packaged-build evidence;
- generate audit reports.

If evidence is impossible without creating a temporary test harness:
- return `BLOCKED`, unless user explicitly sets:
  `AUDIT_ALLOW_TEMP_TESTS=true`
- temporary assets may only be created under:
  `/Game/Tests/AuditTemp/`
- never mutate production Blueprints in audit mode.

---

# 2. Scope

Audit any of these asset/system categories:

## Core Blueprint types
- Actor Blueprint
- Pawn Blueprint
- Character Blueprint
- PlayerController
- AIController
- GameMode / GameModeBase
- GameState / GameStateBase
- PlayerState
- GameInstance
- HUD
- SaveGame
- ActorComponent
- SceneComponent
- Blueprint Interface
- Blueprint Function Library
- Blueprint Macro Library
- Level Blueprint
- Editor Utility Blueprint / Widget

## UI
- UserWidget / UMG
- CommonUI widgets
- drag/drop
- input modes
- focus/navigation
- anchors/layout
- responsive UI
- event-driven vs Tick/bindings

## Animation
- Animation Blueprint
- State Machines
- Blend Spaces
- Montages
- Anim Notifies
- Linked Anim Layers
- Control Rig integration
- Paper2D/PaperZD if present

## AI
- Blueprint AI state logic
- AIController
- Behavior Tree / Blackboard references
- EQS references
- perception
- navigation
- target selection
- timers vs Tick

## Data-driven systems
- DataTables
- Primary Data Assets
- Data Assets
- Gameplay Tags
- Enums / Structs
- Soft References / Hard References
- asset manager dependencies

## Input
- Enhanced Input
- Input Actions
- Mapping Contexts
- trigger/modifier logic
- UI/game input mode interaction

## Networking
- Replicated variables
- RepNotify
- Server RPC
- Client RPC
- NetMulticast RPC
- Authority checks
- ownership
- prediction assumptions
- listen server / dedicated server behavior

## Persistence
- SaveGame
- profile/session separation
- serialization boundaries
- load/create/save flow

## Performance
- Blueprint Tick
- GetAllActorsOfClass
- repeated Cast
- repeated widget bindings
- dynamic material churn
- Spawn/Destroy churn
- timers
- loops
- recursion
- latent actions
- object pooling
- GC pressure

---

# 3. Contract discovery

Before auditing, discover the project's expected behavior.

Use this priority:

1. explicit user acceptance criteria;
2. project-local audit/test contract files;
3. design/specification documents;
4. existing Functional Tests / Automation Tests;
5. code comments / Blueprint descriptions;
6. generic UE5 baseline checks from this skill.

Recognized project contract filenames include:
- `*_DIRECT_SPEC.json`
- `*_TEST_SPEC.json`
- `*_ACCEPTANCE.json`
- `*_AUDIT_CONTRACT.json`
- `ACCEPTANCE.md`
- `TEST_PLAN.md`
- `SPEC.md`
- `README.md`

Do not force a project to follow one naming convention.

If no project-specific functional contract exists:
- audit structural/runtime correctness;
- report behavior that cannot be judged as `UNSPECIFIED`, not FAIL.

Never invent expected values.

---

# 4. Universal PASS formula

A feature can PASS only when all required layers pass:

`PASS = Asset && Structure && Logic && Functional && Integration && Logs && Evidence`

Optional categories may be N/A.

Definitions:

## Asset
Required assets exist, load, and have correct class/parent.

## Structure
Variables/functions/components/interfaces/defaults/settings match contract.

## Logic
Critical Blueprint graph behavior is correct.

## Functional
Runtime input produces expected output.

## Integration
Connected systems communicate correctly.

## Logs
No blocking runtime errors.

## Evidence
Expected vs actual is reproducible.

If any required layer fails:
`STATUS=FAIL`

If a required layer cannot be tested because external evidence is unavailable:
`STATUS=BLOCKED`

---

# 5. Never accept these as functional proof

Do not PASS from:

- `.uasset` exists;
- Blueprint Compile = Success;
- Save = Success;
- Python script ran;
- Editor Utility ran;
- Git commit exists;
- developer agent says done;
- screenshot of Content Browser only;
- screenshot of green compile icon only;
- `PrintString("PASS")` without assertion chain;
- empty function with correct name;
- variable/function list without runtime test;
- one happy-path test when edge cases matter.

---

# 6. PASS marker integrity

If an implementation prints:
`TEST_OK`, `PASS`, `FEATURE_OK`, or similar:

trace its execution path.

Valid:

`Real assertions -> Branch(True) -> PASS marker`

Invalid:

`BeginPlay -> PASS marker`

Invalid:

`Delay -> PASS marker`

Invalid:

`Compile Success -> PASS marker`

Invalid:

`Always True variable -> PASS marker`

If invalid:
`PASS_MARKER_INTEGRITY=FAIL`

This alone blocks functional PASS.

---

# 7. Audit levels

## Level 1 — Asset

Capture:
- asset path;
- Blueprint type;
- parent class;
- compilation state;
- loadability;
- broken references;
- redirects;
- duplicate/suffixed accidental assets.

## Level 2 — Structure

Inspect:
- variables;
- types;
- defaults;
- categories;
- exposed-on-spawn;
- instance editable;
- replication flags;
- components;
- attachment hierarchy;
- collision;
- functions;
- input/output pins;
- pure/const flags where relevant;
- macros;
- dispatchers;
- interfaces;
- class settings.

## Level 3 — Graph logic

Inspect critical paths:
- Event BeginPlay;
- Event Tick;
- Construction Script;
- input events;
- overlap/hit events;
- RPC events;
- interface implementations;
- state transitions;
- timers;
- latent actions;
- branches;
- loops;
- sequence ordering;
- null checks;
- cleanup;
- duplicate event bindings;
- delegate unbinding.

Do not audit cosmetic node placement.

## Level 4 — Functional runtime

Every assertion must contain:

INPUT
PRECONDITION
EXPECTED
ACTUAL
RESULT

Example:

INPUT:
`ApplyDamage(30)`

PRE:
`HP=100`

EXPECTED:
`HP=70`

ACTUAL:
`HP=70`

RESULT:
`PASS`

## Level 5 — Integration

Trace subsystem chains.

Examples:
- Input -> Character -> Ability -> Damage -> Target
- Widget -> Controller -> Gameplay
- AI Perception -> Target -> Movement -> Attack
- SaveGame -> Load -> Apply
- Server RPC -> Authority -> Replicated State -> Client UI
- Anim Notify -> Gameplay Event
- DataTable -> Runtime Config -> Actor behavior

## Level 6 — Logs

Search relevant run for:
- `Blueprint Runtime Error`
- `Accessed None`
- `Infinite Loop`
- `Fatal Error`
- `Ensure condition failed`
- failed asset loads
- missing package
- RPC warnings
- network ownership warnings
- animation warnings
- PIE warnings related to audited feature

## Level 7 — Evidence

Every FAIL must include:
- asset;
- graph/function;
- input;
- expected;
- actual;
- evidence;
- required change;
- retest.

---

# 8. Blueprint-specific audit rules

## Actor / Pawn / Character

Check:
- correct parent;
- component hierarchy;
- collision;
- movement component;
- BeginPlay;
- possession;
- input ownership;
- Tick necessity;
- death/disable cleanup;
- child class overrides;
- Construction Script side effects.

For Character:
- controller ownership;
- movement mode;
- AddMovementInput flow;
- rotation policy;
- network authority if multiplayer.

## ActorComponent

Check:
- reusable behavior is not coupled to one concrete owner without contract;
- owner null protection;
- initialization order;
- dispatcher behavior;
- duplicate initialization;
- timer cleanup;
- BeginPlay/EndPlay behavior.

## GameMode / GameState / PlayerState / GameInstance

Check responsibilities:
- GameMode server-only assumptions;
- GameState replicated shared match state;
- PlayerState player-scoped replicated state;
- GameInstance cross-level local persistence;
- no client code depending on GameMode in networked games.

## PlayerController

Check:
- input mapping;
- possession;
- widget ownership;
- input modes;
- cursor;
- local-player-only behavior;
- RPC ownership.

## Blueprint Interface

Check:
- exact pin types/directions;
- implementing classes;
- no unnecessary hard casts replacing interface flow;
- interface calls handle non-implementers safely.

## Function Library

Check:
- no hidden world-state mutation in functions expected pure;
- world context pins where needed;
- no unsafe object assumptions;
- no circular dependencies.

## Macro Library

Check:
- latent/multi-exec behavior;
- hidden side effects;
- loop termination;
- duplicated logic risk.

## Level Blueprint

Flag excessive gameplay logic as architecture risk when equivalent reusable logic belongs in actors/components/managers.

Do not automatically fail unless project contract prohibits it.

## Construction Script

Check:
- idempotence;
- no uncontrolled spawning;
- no runtime-only assumptions;
- editor performance;
- deterministic result.

---

# 9. UMG audit

Audit:
- widget hierarchy;
- anchors;
- alignment;
- offsets;
- DPI behavior;
- SafeZone where needed;
- SizeBox constraints;
- input/focus;
- drag/drop;
- creation/destruction;
- event binding;
- duplicate widget creation;
- viewport Z order.

Performance checks:
- avoid runtime Property Bindings for high-frequency stats when event-driven path exists;
- avoid Widget Tick polling without necessity;
- avoid GetAllActors inside widgets;
- avoid repeatedly CreateWidget each update;
- avoid unbounded children growth.

Functional checks:
- open;
- close;
- focus;
- game/input mode;
- mouse/touch/gamepad navigation;
- state update;
- responsive resolutions.

---

# 10. Animation Blueprint audit

Check:
- owning pawn validity;
- cast caching;
- Event Blueprint Update Animation;
- state variables;
- transition rules;
- transition priority;
- dead-end states;
- montage slots;
- notifies;
- sync groups;
- locomotion blending;
- root motion assumptions;
- state exit;
- network animation variables if multiplayer.

Boundary tests:
- idle threshold;
- movement start;
- stop;
- jump/fall/land;
- attack montage;
- death state;
- revive if present.

---

# 11. AI audit

Check:
- target acquisition;
- perception;
- AIController possession;
- NavMesh availability;
- MoveTo result handling;
- attack range;
- cooldown;
- target invalidation;
- death cleanup;
- timer frequency;
- Behavior Tree/Blackboard key consistency;
- service/decorator conditions;
- EQS query result handling.

Performance flags:
- `GetAllActorsOfClass` every Tick;
- world overlaps every frame per AI;
- expensive path requests each frame;
- uncontrolled timers per actor.

---

# 12. Enhanced Input audit

Check:
- InputAction type;
- Mapping Context registration;
- priority;
- input trigger;
- Started/Triggered/Ongoing/Completed/Canceled semantics;
- duplicate context registration;
- local player subsystem validity;
- UI input capture;
- mobile touch mappings where required.

Functional test:
- action fires;
- correct value type;
- release/cancel behavior;
- no duplicate execution.

---

# 13. Networking audit

When project is multiplayer, add mandatory networking layer.

Check variables:
- Replicated;
- RepNotify;
- initial replication;
- owner-only relevance if expected.

Check RPC:
- Server RPC called by owning client only;
- authority validation;
- client RPC ownership;
- NetMulticast only for appropriate cosmetic/shared events;
- no client-authoritative health/ammo unless explicitly intended.

Required topologies when relevant:
- Standalone
- Listen Server + 1 client
- Dedicated Server + clients

Typical assertions:
- damage applied once on server;
- health replicates to clients;
- UI updates on owning client;
- no duplicate multicast VFX;
- respawn ownership correct.

If multiplayer behavior is required but only Standalone was tested:
`STATUS=BLOCKED` or `FAIL` depending on contract.

---

# 14. SaveGame audit

Check:
- slot naming;
- create/load fallback;
- versioning if present;
- persistent vs session fields;
- defaults;
- save trigger;
- load trigger;
- corrupt/missing save behavior;
- level travel behavior.

Functional:
1. change persistent value;
2. save;
3. reload/restart;
4. verify persistence;
5. verify run-only values do not incorrectly persist.

---

# 15. DataTable / DataAsset audit

Check:
- row struct;
- field types;
- required rows;
- duplicate IDs;
- invalid soft/hard references;
- missing classes/textures/sounds;
- default rows;
- lookup failure handling.

Functional:
- actual GetDataTableRow path;
- row found;
- values used by runtime.

Do not PASS a DataTable because rows look correct if runtime never reads them.

---

# 16. Performance audit

Report high-risk Blueprint patterns:

BLOCKING only if performance target/contract is violated.

Patterns:
- Tick enabled but unused;
- Tick doing expensive scans;
- repeated `GetAllActorsOfClass`;
- repeated casts per frame;
- repeated dynamic material creation;
- repeated widget creation;
- unbounded SpawnActor/DestroyActor;
- large ForLoops in frame path;
- recursive Blueprint calls;
- excessive latent actions;
- timers never cleared;
- delegate leaks;
- massive hard-reference chains.

Measure when requested:
- stat unit;
- stat game;
- stat gpu;
- Unreal Insights;
- memory;
- actor counts;
- draw calls;
- package/device FPS.

---

# 17. Audit severity

## BLOCKER
- project cannot open;
- Blueprint cannot compile;
- required asset cannot load;
- required plugin/module missing;
- broken required reference;
- PIE cannot execute;
- required multiplayer topology unavailable;
- required physical-device evidence unavailable.

## FAIL
- wrong parent/type/default;
- missing variable/function/dispatcher/interface;
- wrong graph behavior;
- wrong runtime result;
- duplicate event;
- unconditional PASS marker;
- broken integration;
- runtime Blueprint error;
- invalid replication behavior.

## WARN
- style/maintainability risk;
- unused variable;
- non-blocking editor warning;
- architecture smell not prohibited by contract;
- potential performance risk not yet violating budget.

PASS requires:
`BLOCKER=0 && FAIL=0`

---

# 18. Generic test design

For every feature derive tests from:

- normal case;
- zero/empty case;
- minimum boundary;
- maximum boundary;
- invalid input;
- repeated call;
- state transition;
- cleanup;
- destruction;
- level travel;
- replication if applicable.

Examples:

Health:
- 100 - 30 = 70
- overkill clamps to 0
- death event fires once
- heal does not exceed max
- invulnerable ignores damage

Cooldown:
- action available at t=0
- unavailable immediately after use
- available at exact cooldown boundary

Inventory:
- add
- consume valid
- consume insufficient
- count never negative

UI:
- open twice does not duplicate
- close unbinds if required
- data event updates exactly once

---

# 19. Project contract template

If a project has no audit contract, recommend creating:
`UE5_AUDIT_CONTRACT.json`

Schema is available at:
`contracts/UE5_AUDIT_CONTRACT_SCHEMA.json`

The skill can audit without it, but functional expected values are stronger with a contract.

---

# 20. Developer/Auditor separation

Preferred workflow:

Developer Agent
→ implements
→ stops

UE5 Blueprint Auditor
→ READ_ONLY_AUDIT
→ PASS / FAIL / BLOCKED

If FAIL:
→ generate exact fix handoff
→ developer fixes only stated defect
→ auditor re-tests failure + affected regression

Do not let previous developer claims influence audit.

---

# 21. Output format

Always end with:

```text
AUDIT_SCOPE=<asset/system/phase>
STATUS=PASS|FAIL|BLOCKED

ASSET=PASS|FAIL|N/A
STRUCTURE=PASS|FAIL|N/A
LOGIC=PASS|FAIL|N/A
FUNCTIONAL=PASS|FAIL|N/A
INTEGRATION=PASS|FAIL|N/A
NETWORK=PASS|FAIL|N/A
PERFORMANCE=PASS|FAIL|N/A
LOGS=PASS|FAIL|N/A
EVIDENCE=PASS|FAIL|N/A
PASS_MARKER_INTEGRITY=PASS|FAIL|N/A

BLOCKERS=<n>
FAILURES=<n>
WARNINGS=<n>

BLUEPRINT_RUNTIME_ERRORS=<n>
ACCESSED_NONE=<n>

RESULT_GATE=ALLOW|BLOCK|N/A
```

Before the status block include only:
- concise findings;
- failed expected-vs-actual assertions;
- evidence;
- exact developer handoff.

No generic tutorials during audit unless user asks.
