# -*- coding: utf-8 -*-
"""Machine-Authoritative Art Registry Validator"""
import os, sys, yaml, json
from pathlib import Path

workspace = Path(__file__).resolve().parents[1]
registry_path = workspace / "ProjectState" / "art_registry.yaml"

print(f"=== Validating Art Registry: {registry_path} ===")

if not registry_path.exists():
    print("FATAL: art_registry.yaml does not exist!")
    sys.exit(1)

with open(registry_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

assets = data.get("assets", [])
summary = data.get("summary", {})
total = data.get("total_registered_assets", 0)

errors = []
warnings = []

# 1. Validate Total Count & Summary Integrity
if len(assets) != total:
    errors.append(f"Total count mismatch: declared={total}, actual={len(assets)}")

actual_approved = len([x for x in assets if x["approval"]["status"] == "APPROVED"])
actual_candidate = len([x for x in assets if x["approval"]["status"] == "CANDIDATE"])
actual_placeholder = len([x for x in assets if x["approval"]["status"] == "PLACEHOLDER"])
actual_legacy = len([x for x in assets if x["approval"]["status"] == "LEGACY"])

if actual_approved != summary.get("approved_count"):
    errors.append(f"Approved count mismatch: declared={summary.get('approved_count')}, actual={actual_approved}")
if actual_candidate != summary.get("candidate_count"):
    errors.append(f"Candidate count mismatch: declared={summary.get('candidate_count')}, actual={actual_candidate}")
if actual_placeholder != summary.get("placeholder_count"):
    errors.append(f"Placeholder count mismatch: declared={summary.get('placeholder_count')}, actual={actual_placeholder}")
if actual_legacy != summary.get("legacy_count"):
    errors.append(f"Legacy count mismatch: declared={summary.get('legacy_count')}, actual={actual_legacy}")

# 2. Validate Semantic ID Uniqueness
seen_ids = set()
for idx, a in enumerate(assets):
    sem_id = a.get("semantic_id")
    if not sem_id:
        errors.append(f"Asset #{idx} missing semantic_id")
    elif sem_id in seen_ids:
        errors.append(f"Duplicate semantic_id: {sem_id}")
    else:
        seen_ids.add(sem_id)

    status = a.get("approval", {}).get("status")
    flags = a.get("flags", {})
    pres = a.get("presentation", {})
    source = a.get("source", {})
    runtime = a.get("runtime", {})
    app = a.get("approval", {})

    # 3. Approved Asset Rules
    if status == "APPROVED":
        if not app.get("approval_evidence"):
            errors.append(f"APPROVED asset {sem_id} missing approval_evidence")
        if not app.get("approved_source_hash"):
            errors.append(f"APPROVED asset {sem_id} missing approved_source_hash")
        if not app.get("approved_runtime_hash"):
            errors.append(f"APPROVED asset {sem_id} missing approved_runtime_hash")
        if not app.get("approved_contract_hash"):
            errors.append(f"APPROVED asset {sem_id} missing approved_contract_hash")
        if flags.get("placeholder"):
            errors.append(f"Placeholder asset {sem_id} cannot be marked APPROVED")

    # 4. Placeholder Rules
    if flags.get("placeholder"):
        if status != "PLACEHOLDER":
            errors.append(f"Flagged placeholder {sem_id} must have status=PLACEHOLDER")
        if not flags.get("release_blocking"):
            errors.append(f"Placeholder {sem_id} must be marked release_blocking=true")

    # 5. Presentation Validation
    frame_count = pres.get("frame_count", 1)
    if "Sheet" in source.get("path", "") and frame_count < 2:
        errors.append(f"SpriteSheet {sem_id} has invalid frame_count={frame_count}")

    # 6. Directional Validation
    direction = pres.get("direction")
    if a.get("feature_id") == "Player.Medic" and status == "APPROVED" and direction == "OMNI":
        errors.append(f"Approved directional character asset {sem_id} cannot have direction=OMNI")

# Print Results
print(f"Total Assets Validated: {len(assets)}")
print(f"Approved: {actual_approved} | Candidate: {actual_candidate} | Placeholder: {actual_placeholder} | Legacy: {actual_legacy}")

if errors:
    print(f"\nFAILED with {len(errors)} errors:")
    for e in errors[:20]:
        print(f"  [ERROR] {e}")
    sys.exit(1)
else:
    print("\n[SCHEMA PASS] Registry fields are consistent; asset hashes and visual approval are NOT verified.")

