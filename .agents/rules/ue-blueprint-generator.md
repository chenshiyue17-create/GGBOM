---
description: Force UE5.8 Blueprint requests to become editable connected .uasset graphs, never C++
---

# UE5.8 editable Blueprint automatic handoff

This rule has priority whenever the user requests a UE5.8 Blueprint, Blueprint logic, Event Graph, node connection, Blueprint function, visual scripting, code-to-Blueprint conversion, or anything that must remain editable in the UE Blueprint Editor.

## Non-negotiable output contract

The deliverable is a real `.uasset` Blueprint whose nodes, Pin connections, defaults, variables, components, functions, and events can be opened and edited in UE5.8. Text source code is not a substitute.

For an in-scope Blueprint request, NEVER:

- create or edit `Source/**`, `*.cpp`, `*.h`, `*.Build.cs`, or `*.Target.cs`;
- add a native module to the `.uproject`;
- use a C++ class, Live Coding, compilation, or native plugin as the implementation fallback;
- give the user code to paste manually into Unreal;
- claim success because code was generated or because disconnected nodes exist.

If a requested node or component is not supported by the generator, extend the Blueprint generator/schema and retry. Do not silently change the implementation to C++.

## Required workflow

1. Call `ue_status` to bind this conversation to the live matching UE5.8 project. Do not infer live state from a screenshot.
2. Create or update `BlueprintSpecs/<descriptive-name>.ueblueprint.json`.
3. Follow the schema registered for `*.ueblueprint.json` and use `BlueprintSpecs/connected_begin_play.ueblueprint.json` as a structural example when available.
4. Every execution and data flow must be present in `connections`; creating disconnected nodes is never complete.
5. Use stable node IDs and Unreal internal event names such as `ReceiveBeginPlay`.
6. If a Pin or Unreal function path is uncertain, put the uncertainty in `unresolved` instead of guessing. Remove `unresolved` only after resolving it.
7. Call `ue_generate_blueprint` with that spec. Treat its structured result as the next observation in the conversation.
8. If needed, call `ue_read_blueprint_report`. Success requires `success=true`, `compile_success=true`, and `connections_requested == connections_verified`.
9. Confirm the report's asset path ends in the requested `.uasset` Blueprint and that it opens in the UE5.8 Blueprint Editor.
10. If the tool reports failure, reason from the returned error, fix the spec or generator capability, and call the tool again.

Do not ask the user to manually run the converter when automatic mode is enabled.

## Direct UE Python execution

When a task genuinely requires UE Editor Python instead of a Blueprint graph:

1. Create or modify an ordinary `<project>/Content/Python/<descriptive-name>.py` file, or reuse an existing `<project>/Tools/*.py` file.
2. Call `ue_run_project_python` with that project-relative path. This is the primary execution path; do not wait for a filename watcher and do not show a terminal command to the user.
3. Read the structured tool result as a live observation. If it fails, fix the file and call the tool again.
4. `*.uelive.py` save-listening exists only as a compatibility fallback and must not be presented as the normal workflow.

NEVER respond with instructions asking the user to copy code or a script path into UE's Python console, Output Log, clipboard, or editor input box. The IDE must edit the project file and execute it through the live bridge itself. Arbitrary scripts outside the project `Content/Python` and `Tools` directories are intentionally rejected.

## Real-time verification policy

Use the MCP tools' structured live responses as the default source of truth. `ue_status`, tool results, and the JSON acceptance report provide the current project, engine version, process, node/connection counts, compiler errors, and save result.

Do not ask the user to capture, crop, or upload screenshots merely to determine whether a Blueprint was generated, connected, compiled, or saved. Do not use OCR or screen recognition as a substitute for the live bridge or report. A screenshot is appropriate only when the requested acceptance criterion is inherently visual, such as viewport composition, rendered appearance, animation pose, material appearance, or in-game HUD visibility.
