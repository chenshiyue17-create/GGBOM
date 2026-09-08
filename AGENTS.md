# GGBOM repository instructions

- The production project is `xxxx/xxxx.uproject`, UE5.8, pure Blueprint/Paper2D. Do not introduce runtime C++ modules as an unannounced fallback.
- Read `ProjectState/verification.yaml` before trusting historical PASS claims. `Docs/MULTI_DEVICE_DEVELOPMENT.md` defines the supported tool entry points and current limitations.
- Use `python3 tools/dev.py test` and `python3 tools/dev.py validate` for source/tool changes. These are not UE runtime gates. On Windows use `py -3`.
- Paths must derive from the repository, Unreal project context, or ignored `.ggbom.local.json` / `GGBOM_UE_ROOT` / `GGBOM_UE_BIN`. Never commit an individual machine's absolute UE/project path in a new supported entry.
- Do not infer Blueprint parent, components, variables or connections from names/file sizes. Inspect them through the matching live UE editor. If unavailable, report BLOCKED/NOT_RUN; never fabricate zero runtime errors or PASS.
- Only rewrite production `.uasset` / `.umap` after reading the active graph and scoped asset dependencies in UE, and retain actual compilation/readback and functional evidence. Do not perform automatic archive/full rebuilds for numeric changes.
- Source JSON save, editor default application, disk reload and gameplay consumption are separate results. The existing numeric enemy importer does not validate runtime behavior or apply weapons/waves/art.
- Every change needs a scoped `Changes/` record listing edits, validation and remaining gates. Do not change approved art, camera or map while fixing unrelated tooling.
- Multiple devices synchronize using normal Git commits; never force-push to overwrite another device. Binary asset conflicts require choosing/validating the intended asset revision, not a text merge.
- Whenever any Blueprint logic or graph is created or modified, you MUST generate or update the 1:1 UE-style interactive H5 visual audit page (`Docs/blueprint_audit.html`) with complete Chinese node names, pin parameters, and comments, and open/present it to the user for review and sign-off before concluding the change.

