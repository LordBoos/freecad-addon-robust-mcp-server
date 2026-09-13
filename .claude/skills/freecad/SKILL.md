---
name: freecad
description: Create and iterate on 3D models in FreeCAD using the FreeCAD MCP tools or headless via freecadcmd.exe. Use this skill whenever the user asks to design, model, or create any 3D object in FreeCAD, or when they provide a reference image, an existing STL, or a 3D scan and want a model built to match or extend it. Also trigger when the user mentions FreeCAD, freecadcmd, parametric modeling, PartDesign, or wants to create mechanical parts, enclosures, brackets, or any CAD geometry — even when the FreeCAD MCP server is not connected. Handles prompt-based modeling, reference-image matching, modifying/extending existing STL models, and scan reverse engineering through iterative comparison.
---

# FreeCAD 3D Modeling Skill

Create parametric 3D models in FreeCAD via the FreeCAD MCP server (`execute_python` + selected MCP tools). **All dimensions are in millimeters.**

## Golden Rules

1. **Parametric-first.** Every model is a PartDesign Body with a chain of Sketch → Feature operations. The user must be able to double-click any feature in the tree and edit it. Target tree: `Body > BaseSketch > BasePad > HollowSketch > HollowPocket > TopFillet`.
2. **Python creates *features*, never raw shapes.** `body.newObject("PartDesign::Pad", ...)` in `execute_python` is the approved parametric path. `Part.makeBox/makeLoft/extrude`, `Part::Feature`, `body.BaseFeature` are forbidden — they produce dead, uneditable blobs. Avoid datum planes too (unreliable, clutter the GUI) — use `AttachmentOffset` instead.
3. **Never assume a call worked.** Every `execute_python` response has `success` and `error_traceback` — check them. Every feature gets a numeric verification (Block F) before you build on top of it.
4. **Verify dimensions with `BoundBox` numbers, not screenshots.** Screenshots confirm shape and catch gross errors; `Shape.BoundBox` / `Shape.Volume` confirm dimensions.
5. **Select faces and edges by geometric predicate, never by guessed index.** Face/edge numbering shifts whenever the tree changes. Compute the right one from geometry (Blocks A2, D). For a point on an edge use `e.valueAt((e.FirstParameter + e.LastParameter) / 2)` — never `e.CenterOfMass`, which for an arc lies OFF the curve and silently fails distance predicates.
6. **Name everything descriptively.** `MountingHolesSketch`, `VentSlotPocket` — not `Sketch003`, `Pocket`.
7. **One feature per logical operation.** A bolt-hole pattern is one feature; a vent slot and a cable channel are two.
8. **Fillets and chamfers last**, after all structural features.

---

## Step 0 — Mode Decision, Connect and Probe

First determine which mode the session is in:

1. **`mcp__freecad__*` tools are entirely absent from the session** (one ToolSearch finds none) → the MCP server didn't connect. Don't repeat ToolSearch and don't dig through `~/.claude.json` — go straight to **Headless Mode** below. It's a fully capable path, not a degraded one; no need to ask the user to reconnect via `/mcp` first.
2. **Tools exist** → probe the connection:

```
get_connection_status()     # connected: true? If false → auto-start FreeCAD (below), don't ask the user
get_freecad_version()       # decides the compatibility path below
```

### Auto-start FreeCAD when not connected

If `get_connection_status()` returns `connected: false`, start FreeCAD with the MCP bridge yourself:

```powershell
Start-Process -FilePath "<repo>\start-mcp-and-freecad.cmd" -WorkingDirectory "<repo>"
```

The script launches the FreeCAD GUI detached with the bridge startup script (`just freecad::run-gui-custom`; requires `just` on PATH — installed via winget). Then poll `get_connection_status()` every ~5 s until `connected: true` — typical GUI startup is 10–30 s. If still not connected after ~90 s, check for a stray process (`Get-Process FreeCAD*`) and report to the user instead of retrying forever.

Fallback if the script or `just` is missing — launch directly, same effect:

```powershell
Start-Process -FilePath "C:\Program Files\FreeCAD 1.1\bin\freecad.exe" -ArgumentList '"<repo>\freecad\RobustMCPBridge\freecad_mcp_bridge\startup_bridge.py"'
```

Never auto-start when already connected — a second FreeCAD instance would fight over the bridge port.

Caveats learned the hard way (2026-07-10):

- **Never `Stop-Process -Name "FreeCAD*"`** — the wildcard also matches `freecad-mcp.exe` (the MCP server spawned by Claude Code) and kills it. A dead stdio MCP server is NOT respawned mid-session; the user must reconnect via `/mcp` or start a new session. If you must kill FreeCAD, use the exact name: `Stop-Process -Name "freecad"`.
- Auto-start only helps when the MCP *tools* still respond (server alive, `connected: false`). If the `mcp__freecad__*` tools themselves are gone from the session, the MCP server is down — starting FreeCAD won't bring them back; switch to **Headless Mode** below (don't block on asking the user to run `/mcp`).

On this machine FreeCAD is **1.1.x** — assume the broken-tools matrix below applies. On FreeCAD ≤ 1.0 more MCP tools happen to work, but the Python building blocks are version-safe everywhere, so using them unconditionally is always correct.

Then set up the document:

```
create_document(name="ModelName")          # or get_active_document() / list_documents() to continue existing work
create_partdesign_body(name="Body")        # works on all versions
```

---

## Headless Mode (freecadcmd.exe)

When the MCP tools are absent (or the user asks for a scripted build), model fully headless: write one complete build script into the session scratchpad and run

```bash
"/c/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" build_model.py 2>&1 | grep -E "DBG|VERIFY|EXPORTED|Exception"
```

(the grep drops the `Recompute... (10 %)...` progress spam that otherwise floods the output).

The script follows the SAME rules as the MCP path — PartDesign Body, Blocks A–G logic, `hasattr(sk, "AttachmentSupport")` version fallback, `AttachmentOffset` instead of datum planes, predicate edge selection — plus these headless specifics:

- **Every `assert` carries a message.** freecadcmd prints no traceback; a failure surfaces ONLY as `Exception while processing file: build_model.py [<assert message>]`. A bare assert yields `[]` and you'll burn a whole run finding out where it died. Pattern: `assert pad.Shape.isValid(), "BasePlatePad invalid"`.
- **Print a `DBG` line (name + bbox) after every feature** — it's your only per-feature diagnostic when a later assert fails.
- **Structure: build → asserts → `VERIFY` print → save/export last.** On a failing run the script's output can appear twice (the file is apparently evaluated again on exception), so keep side effects (`doc.saveAs`, `mesh.write`) at the very end behind all asserts, and idempotent.
- **End with markers**: `print("VERIFY", {...Block F dict...})` and `print("EXPORTED", path, "facets", n)` — parse those, not the raw log.
- **After a crash, never inspect the saved `.FCStd`** — the script died before `saveAs`, so the file on disk is the *previous successful* run. Diagnose from the DBG prints; for a stubborn geometry anomaly write a minimal standalone reproducer script.
- Origin planes: `body.Origin.OriginFeatures` + name prefix match (`o.Name.startswith("XY_Plane")`) is the tested lookup in headless docs.
- **Visual verification without GUI**: Block E is unavailable — use `references/stl_toolkit.py` (`render` / `sections` / `overlay`) on the exported STL instead, then Read the PNG. Dimension truth comes from the mesh bbox (see Block G).

A complete worked example of this pattern (L-shaped plate, 3 fillet stages, mesh-bbox verification) ran successfully on 2026-08-05; the structure above is distilled from it.

---

## Tool Reliability Matrix

Verified against the `freecad-mcp` server source **and live-tested 2026-07-02** against FreeCAD 1.1.0 with the `FreecadRobustMCPBridge` addon. **Use the safe tools freely; never call the broken ones — go straight to the Python building block.**

Two traps beyond outright failures:

- **Success ≠ valid geometry.** Some tools report success while leaving an Invalid feature in the tree, and `get_screenshot` returns transport-success with `"success": false` inside the payload. Always check the payload and run Block F.
- **The bridge exec namespace contains only `FreeCAD`, `App`, `FreeCADGui`, `Gui`.** Every `execute_python` snippet must explicitly `import Part`, `import Sketcher`, `import math`, etc. (This is also why `add_sketch_rectangle` broke — it uses `Sketcher` without importing it.)

### Safe MCP tools (live-verified)

| Area | Tools |
|---|---|
| Documents | `create_document`, `list_documents`, `get_active_document`, `save_document`, `open_document` |
| Body & sketch geometry | `create_partdesign_body`, `add_sketch_circle`, `add_sketch_line`, `add_sketch_arc`, `add_sketch_point` |
| Features | `pocket_sketch`, `loft_sketches`, `linear_pattern`, `polar_pattern`, `mirrored_feature`, `fillet_edges`/`chamfer_edges` **with explicit `edges`** |
| Inspection & editing | `list_objects`, `inspect_object`, `edit_object`, `delete_object`, `set_placement`, `rotate_object`, `get_console_log`, `undo`, `redo` |
| Display | `set_object_visibility`, `set_object_color`, `set_display_mode`, `fit_all` |
| I/O | `export_step`, `import_step`, `import_stl`, `execute_python` |

### Broken or risky — use the building block instead

| Tool | Failure (live-verified) | Replacement |
|---|---|---|
| `create_sketch` (with `body_name`) | `'Sketcher.SketchObject' object has no attribute 'Support'` (FC 1.1 renamed it to `AttachmentSupport`) | **Block A** |
| `pad_sketch` | `'PartDesign.Feature' object has no attribute 'Symmetric'` (real property is `Midplane`) — broken on all versions | **Block B** |
| `revolution_sketch`, `groove_sketch` | same `.Symmetric` bug | **Block C** |
| `add_sketch_rectangle` | `NameError: name 'Sketcher' is not defined` in the bridge — **and it adds the 4 lines before failing**, so a retry duplicates geometry | rectangle helper in Sketch Geometry below |
| `fillet_edges` / `chamfer_edges` **without** explicit `edges` | **false PASS**: reports success but creates an Invalid feature with `Base=(feat, ['None'])` and a null shape — silent tree corruption | **Block D**, or the MCP tool with an explicit `edges` list |
| `create_hole` with `threaded=True` | `ThreadType="ISO"` invalid enum (plain holes work with a **fresh** point sketch; reusing an already-consumed sketch fails with `Base feature's TopoShape is invalid`) | circles + `pocket_sketch`; don't model threads for FDM (tap or heat-set inserts) |
| `get_screenshot` | **false PASS**: payload contains `"success": false` with `'dict' object has no attribute '__name__'` | **Block E** |
| `recompute` (MCP tool) | calls `touch()` on **every** object → full-tree rebuild: slow, can surface unrelated errors | plain `doc.recompute()` inside snippets; MCP `recompute()` only as a deliberate force-rebuild diagnostic |
| `export_stl` | works, but coarse fixed tessellation | **Block G** for print-quality meshes |

**Fixed server (dev repo):** this repository (`<repo>` = checkout root, i.e. the Claude Code working directory) contains the server with ALL of the above fixed (verified live 2026-07-02): `create_sketch`, `add_sketch_rectangle`, `pad_sketch`/`revolution_sketch`/`groove_sketch` (incl. `symmetric` → `Midplane`), `fillet_edges`/`chamfer_edges` with no `edges` (fillets all edges, validly), threaded `create_hole` ("ISO"+"M6" auto-resolve to `ISOMetricProfile`/`M6x1.0`), `get_screenshot`, plus a doc-wide invalid-object check after every transactional recompute — failed operations now raise (`Recompute left invalid objects: ...`) and roll back instead of false-PASSing. Quick probe at session start: call `create_sketch` once on the test body — if it succeeds, the fixed server is installed and the MCP tools may be used directly; on the `'Support'` AttributeError the old 0.6.1 server is running, so use this matrix and the blocks. The Python building blocks work identically on both versions — when in doubt, use the blocks.

---

## Building Blocks (`execute_python`)

Conventions for every block:

- End with `_result_ = {...}` containing diagnostics; check `success`/`error_traceback` in the response.
- **Import everything you use**: only `FreeCAD`/`App`/`FreeCADGui`/`Gui` are predefined — `import Part`, `import Sketcher`, `import math` explicitly.
- Don't use `'''` inside the code string (it delimits the outer literal).
- For heavy operations (many fillets, dense patterns, meshing) pass `timeout_ms=120000`.
- Batch one *logical feature* per call (sketch + geometry + operation + verify) — each call has ~2 s bridge latency, and batching keeps failures isolated.

### Block A — Create a sketch (version-safe attach)

**A1 — on an origin plane, with optional height offset.** Preferred: immune to face renumbering (topological naming problem).

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
sk = body.newObject("Sketcher::SketchObject", "BaseSketch")
plane = body.Origin.getObject("XY_Plane")        # XY_Plane / XZ_Plane / YZ_Plane
if hasattr(sk, "AttachmentSupport"):             # FreeCAD >= 1.1
    sk.AttachmentSupport = [(plane, "")]
else:                                            # FreeCAD <= 1.0
    sk.Support = [(plane, "")]
sk.MapMode = "FlatFace"
# Sketch "on top of" a 10mm pad WITHOUT touching faces — just offset the plane:
sk.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, 0, 10), FreeCAD.Rotation())
doc.recompute()
_result_ = {"sketch": sk.Name}
```

With an origin plane + `AttachmentOffset`, sketch coordinates stay in the global XY system — no surprises.

**A2 — on a solid face, found by predicate** (only when a face is genuinely needed, e.g. sketching on a slanted face):

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
feat = body.Tip                                  # last solid feature
shape = feat.Shape
zmax = shape.BoundBox.ZMax
face_name = None
for i, f in enumerate(shape.Faces):              # planar face lying at ZMax = the top face
    bb = f.BoundBox
    if abs(bb.ZMin - zmax) < 1e-6 and abs(bb.ZMax - zmax) < 1e-6:
        face_name = "Face%d" % (i + 1)
        break
if face_name is None:
    raise ValueError("Top planar face not found")
sk = body.newObject("Sketcher::SketchObject", "TopSketch")
if hasattr(sk, "AttachmentSupport"):
    sk.AttachmentSupport = [(feat, face_name)]
else:
    sk.Support = [(feat, face_name)]
sk.MapMode = "FlatFace"
doc.recompute()
_result_ = {"sketch": sk.Name, "face": face_name,
            "placement": str(sk.Placement)}      # NOTE: local origin/axes may differ from global!
```

Adapt the predicate for other faces (e.g. front face: `abs(bb.YMin - shape.BoundBox.YMin) < 1e-6` and zero Y-thickness). After attaching to a face, **check `sk.Placement`** — the sketch's local coordinate system is generally not the global one.

After either variant, populate the sketch with the safe MCP geometry tools (`add_sketch_circle`, `add_sketch_line`, ...) or inline Python in the same call (see Sketch Geometry below — rectangles must go through the helper, not the broken `add_sketch_rectangle`).

### Block B — Pad (extrude)

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
sk = doc.getObject("BaseSketch")
pad = body.newObject("PartDesign::Pad", "BasePad")
pad.Profile = sk
pad.Length = 10
pad.Midplane = False       # True = symmetric extrude (this is what 'Symmetric' should have been)
pad.Reversed = False       # True = extrude the other way
sk.Visibility = False
doc.recompute()
bb = pad.Shape.BoundBox
_result_ = {"pad": pad.Name, "valid": pad.Shape.isValid(), "volume": round(pad.Shape.Volume, 2),
            "size": [round(bb.XLength, 2), round(bb.YLength, 2), round(bb.ZLength, 2)],
            "z": [round(bb.ZMin, 2), round(bb.ZMax, 2)]}
```

For pockets, the MCP `pocket_sketch(sketch_name, length, type="Length"|"ThroughAll", name=...)` works fine.

### Block C — Revolution / Groove

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
sk = doc.getObject("KnobProfileSketch")
rev = body.newObject("PartDesign::Revolution", "KnobRevolution")   # or "PartDesign::Groove" (subtractive)
rev.Profile = sk
rev.ReferenceAxis = (body.Origin.getObject("Y_Axis"), [""])        # X_Axis / Y_Axis / Z_Axis
# or a sketch axis: rev.ReferenceAxis = (sk, ["V_Axis"])           # V_Axis / H_Axis
rev.Angle = 360
rev.Midplane = False
rev.Reversed = False
sk.Visibility = False
doc.recompute()
_result_ = {"name": rev.Name, "valid": rev.Shape.isValid(), "volume": round(rev.Shape.Volume, 2)}
```

The profile must be a closed wire entirely on one side of the axis.

### Block D — Fillet / Chamfer with predicate edge selection

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
feat = body.Tip
shape = feat.Shape
zmax = shape.BoundBox.ZMax
edges = []
for i, e in enumerate(shape.Edges):              # all edges lying in the ZMax plane = top rim
    if e.Vertexes and all(abs(v.Point.z - zmax) < 1e-6 for v in e.Vertexes):
        edges.append("Edge%d" % (i + 1))
if not edges:
    raise ValueError("No matching edges found")
fil = body.newObject("PartDesign::Fillet", "TopFillet")   # or "PartDesign::Chamfer" + .Size
fil.Base = (feat, edges)
fil.Radius = 2.0
doc.recompute()
_result_ = {"name": fil.Name, "edges": edges, "valid": fil.Shape.isValid()}
```

Other useful predicates: vertical edges (`abs(v1.Point.z - v2.Point.z) > 1` and same x,y), edges of a specific face (`face.Edges` and match by `e.isSame(...)` or midpoint proximity). When a predicate needs a point *on* the edge (distance to an outline, inside-region tests), use the curve midpoint `e.valueAt((e.FirstParameter + e.LastParameter) / 2)` — `e.CenterOfMass` of an arc is the chord centroid off the curve and will reject exactly the arc edges you wanted (live-hit 2026-08-05: predicate found 20/40 edges). If a fillet fails: reduce radius, or fillet fewer edges per feature.

### Block E — Screenshot (visual check)

```python
import FreeCADGui
view = FreeCADGui.activeDocument().activeView()
if hasattr(view, "setAnimationEnabled"):
    view.setAnimationEnabled(False)              # prevents saving mid-animation (tilted renders)
view.viewIsometric()                             # viewTop() / viewFront() / viewRight() / viewAxonometric()
view.fitAll()
FreeCADGui.updateGui()
path = r"C:\Users\lordb\AppData\Local\Temp\claude\iso.png"   # use the session scratchpad dir
view.saveImage(path, 1000, 750, "White")
_result_ = {"path": path}
```

Then **Read the PNG file**. Notes:

- Even with animation disabled, if a render looks tilted mid-turn, only `viewTop()` is guaranteed perfectly straight; treat other views as approximate 3/4 views.
- Do **not** call `setCameraType("Orthographic")` before `viewTop()` — it derails the view.
- Hide reference meshes/scans first (`set_object_visibility`) if they obscure the model.

### Block F — Verify geometry (run after every feature)

```python
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
tip = body.Tip
bb = tip.Shape.BoundBox
bad = [o.Name for o in doc.Objects if "Invalid" in [str(s) for s in o.State]]
_result_ = {
    "tip": tip.Name,
    "valid": tip.Shape.isValid(),
    "solids": len(tip.Shape.Solids),
    "volume": round(tip.Shape.Volume, 3),
    "size": [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
    "z": [round(bb.ZMin, 3), round(bb.ZMax, 3)],
    "invalid_objects": bad,
}
```

Expected after every feature: `valid: true`, `solids: 1`, `invalid_objects: []`, volume moved in the expected direction (pad ↑, pocket ↓), and `size` matches the intended dimensions to ±0.01. **If any check fails, stop — `undo()`, diagnose via `get_console_log()`, fix, retry.** Never build on a broken base.

**`Shape.BoundBox` caveat:** after a fillet runs over another fillet (e.g. a vertical corner fillet meeting a top round-over), the shape bbox can overshoot the real surface by ~0.5–0.7 mm — it's the loose control-point bbox of the corner NURBS patches, not the geometry (live-hit 2026-08-05: +0.659 mm at R8+R2 corners). Treat Block F's `size` as approximate near such corners; the authoritative final dimension check is the **exported mesh's bbox** (Block G). Don't hard-assert exact shape-bbox equality on filleted models.

Worse: **cutting a revolved cylinder/cone face leaves a trimmed periodic surface whose bbox can report the FULL untrimmed extent** — a collar cut flat to x=88.14 still reported `XMax=94.50` (the whole original radius) even though the cut was complete and the volume drop exact. Two rules follow:

- `feature.Shape` is the **whole body result**, not the added/removed tool — bbox asserts on a small feature see the body's extremes.
- Assert cuts and small features with **`Shape.isInside(FreeCAD.Vector(x, y, z), 1e-6, True)` point checks + volume deltas**, never with bbox, whenever curved faces are involved.

### Block G — Export & save

```python
import MeshPart
doc = FreeCAD.ActiveDocument
body = doc.getObject("Body")
mesh = MeshPart.meshFromShape(Shape=body.Tip.Shape, LinearDeflection=0.04,
                              AngularDeflection=0.25, Relative=False)
mb = mesh.BoundBox                                   # authoritative dimensions (see Block F caveat)
path = r"D:\3D tisk\FreeCAD\model.stl"
mesh.write(path)
_result_ = {"path": path, "facets": mesh.CountFacets,
            "mesh_size": [round(mb.XLength, 3), round(mb.YLength, 3), round(mb.ZLength, 3)]}
```

Check `mesh_size` against the intended dimensions (±0.05) — the mesh bbox is exact where `Shape.BoundBox` overshoots on fillet-over-fillet corners.

- Multi-part models: one STL per Body (loop over bodies, export `body.Tip.Shape` each).
- STEP: `body.Tip.Shape.exportStep(path)` or the MCP `export_step` tool.
- Save the document periodically: `save_document(file_path="D:/3D tisk/FreeCAD/model.FCStd")` or `doc.saveAs(path)`.
- Always absolute paths; default output directory is `D:\3D tisk\FreeCAD`.

---

## Sketch Geometry

The MCP geometry tools below are safe and work on sketches created by Block A. **`add_sketch_rectangle` is broken** (see matrix) — use the rectangle helper instead.

| Tool | Usage |
|---|---|
| `add_sketch_circle` | `(sketch_name, center_x, center_y, radius)` |
| `add_sketch_arc` | `(sketch_name, center_x, center_y, radius, start_angle, end_angle)` — degrees |
| `add_sketch_line` | `(sketch_name, x1, y1, x2, y2, construction=False)` |
| `add_sketch_point` | `(sketch_name, x, y)` |

**Rectangle helper** — paste into the same `execute_python` call that creates the sketch (Block A):

```python
import Part, Sketcher
def add_rect(sk, x, y, w, h):
    g = sk.GeometryCount
    p = [FreeCAD.Vector(x, y, 0), FreeCAD.Vector(x + w, y, 0),
         FreeCAD.Vector(x + w, y + h, 0), FreeCAD.Vector(x, y + h, 0)]
    for j in range(4):
        sk.addGeometry(Part.LineSegment(p[j], p[(j + 1) % 4]))
    for j in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", g + j, 2, g + (j + 1) % 4, 1))

add_rect(sk, -20, -10, 40, 20)      # x,y = bottom-left corner
```

**Full constraint via exact coordinates:** the tools don't expose dimensional constraints, so position and size everything with explicit numbers (rectangle centered on origin: `x=-w/2, y=-h/2`). No free-floating geometry.

**Complex outlines** (stadium, perimeter slot arrays) — populate the sketch inline in the same `execute_python` call using `sketch.addGeometry(Part.LineSegment/ArcOfCircle/Circle(...))` and close wires with `Sketcher.Constraint("Coincident", i, 2, j, 1)`. Full worked examples: [references/recipes.md](references/recipes.md).

**Rounded corners: sharp polygon + 3D fillet, NOT sketch arcs.** For any outline that is "a polygon with rounded corners" (rounded rectangle, rounded L-shape), draw the corners SHARP in the sketch, pad, then round the resulting vertical edges with a `PartDesign::Fillet` (Block D). Hand-computing corner `ArcOfCircle` geometry is error-prone, and the tangent line–arc junctions break downstream fillets (`ChFi3d_Builder:only 2 faces`, `Standard_NullObject ... NULL shape` — live-hit 2026-08-05, forced a full rebuild). Sketch arcs are right only where the arc IS the wall: stadium half-circle ends, full circles, revolution profiles.

**Construction lines** (`construction=True`): centerlines, guides — visible in sketch, ignored by Pad/Pocket.

---

## Patterns

`linear_pattern`, `polar_pattern`, `mirrored_feature` work reliably:

```
linear_pattern(feature_name="VentSlotPocket", direction="X", length=50, occurrences=5, name="VentSlotPattern")
polar_pattern(feature_name="BoltHolePocket", axis="Z", angle=360, occurrences=6, name="BoltCircle")
mirrored_feature(feature_name="LeftBoss", plane="YZ", name="BossMirrored")
```

Limits — switch to Python when you hit them:

- Linear = straight axis only; polar = circular only. Features distributed along a **non-circular perimeter** (stadium, rounded rect): compute positions in Python and put all cutout rectangles into **one sketch → one pocket** (see recipes).
- A pattern that only partially appears in the screenshot = the pattern tool is wrong for the shape. Undo, use the one-sketch approach.

**When creating transform features in Python (`body.newObject("PartDesign::PolarPattern"/"Mirrored"/...)`), set `body.Tip = pattern` afterwards.** Transform features do NOT advance the Tip — the next feature silently chains off the PRE-pattern state (its `BaseFeature` points before the pattern), and its recompute can even no-op and keep the base shape while `isValid()` stays true (live-hit 2026-08-05: pocket after PolarPattern "un-did" 39 of 40 slots). Assert the chain: `feat.BaseFeature.Name == previous_feature.Name`.

---

## Editing Existing Features

`edit_object` works — use it during iteration instead of rebuilding:

```
edit_object(object_name="BasePad", properties={"Length": 15})
edit_object(object_name="TopFillet", properties={"Radius": 3})
edit_object(object_name="VentSlotPattern", properties={"Occurrences": 10})
```

Then `execute_python("FreeCAD.ActiveDocument.recompute()")` + Block F. Sketch geometry edits go through `execute_python` (e.g. `sk.setDatum`, or delete + re-add geometry). If an edit breaks downstream features, Block F's `invalid_objects` names the first casualty — fix forward from there.

---

## Standard Workflow

1. **Step 0** — connect, probe version, create document + body.
2. **Per feature**: Block A (sketch) → geometry tools → Block B/C or `pocket_sketch` → **Block F verify**.
3. **Milestones**: Block E screenshot, compare against intent/reference.
4. **Surface treatments last**: Block D fillets/chamfers.
5. **Final check**: feature tree audit (`list_objects()` — descriptive names, no orphaned sketches, logical order), Block F, Block E from 2-3 angles.
6. **Export**: Block G. Save the `.FCStd`.

**Broken-geometry signs in screenshots** — stop and undo, don't build on top:

- scattered dots / stray lines = failed boolean or pattern
- features on some faces but missing on others = pattern hit its limits
- gaps in walls = unclosed sketch wire or pocket cut through an adjacent wall
- flickering surfaces (z-fighting) = duplicate coplanar faces
- looks right from one angle, wrong from another = partially failed operation

---

## 3D Printing Rules

**In the project `D:\3D tisk\FreeCAD`, models are for FDM printing — apply the FDM rules automatically, don't ask.** Elsewhere: if the user mentions printing, apply them; if genuinely ambiguous, ask once and remember.

### FDM

- **Orientation**: flattest/largest face down on the bed; design so overhangs stay ≤45° from vertical. Chamfer the underside of lips/ledges (45°) instead of relying on supports.
- **Horizontal holes**: sag at the top — make them teardrop (circle + triangle apex at 12 o'clock) or add a 45° bridging chamfer. Vertical holes are fine as circles.
- **Walls**: ≥1.2 mm (3 perimeters of a 0.4 mm nozzle). Pins/tabs <2 mm dia are fragile.
- **Clearances**: mating parts 0.2–0.4 mm per side; tight fits on holes +0.1–0.2 mm on diameter.
- **Bridges**: ≤50–60 mm flat spans; longer → add a pillar or redesign.
- **Threads**: don't model them — size the hole for a heat-set insert or self-tapping screw.

Briefly note print-driven decisions as you make them (*"teardrop hole for horizontal printability"*).

### Verifying print time & supports (Bambu Studio CLI)

When print time or support volume matters, don't estimate — slice. Bambu Studio (`C:\Program Files\Bambu Studio\bambu-studio.exe`) slices headless:

```bash
bambu-studio.exe --slice 1 --debug 2 --outputdir OUTDIR project.3mf   # plate 1; 0 = all plates
```

- Estimate: gcode header `; model printing time: ...`; per-feature breakdown (Support/Travel/Outer wall/...) and filament grams in `OUTDIR/result.json` → `sliced_plates[0].feature_type_times`.
- A user's project `.3mf` carries their full profile (`Metadata/project_settings.config` JSON) — slicing a redesign inside a COPY of their project compares apples to apples: write the new mesh over `3D/Objects/object_N.model` (vertices/triangles XML) in FILE coordinates (apply the inverse of the `<build><item>` transform in `3D/3dmodel.model`, which holds scale/rotation/bed placement), patch `face_count` in `Metadata/model_settings.config`.
- **`support_threshold_angle` counts from the HORIZONTAL: faces FLATTER than the threshold get supported** (default 30 → a 45°-from-horizontal cone is self-supporting; raising the threshold to 46 ADDS supports under 45° faces — live-hit 2026-08-05, +4.8 h). Flat cantilevers always need support built from the bed/body below — the cheap fix is geometry (45° transitions), not settings.

### SLA / resin (only when the user mentions resin/SLA/MSLA/DLP)

Minimize flat cross-sections parallel to the plate (peel force); tilt 15–45°; hollow big volumes (1.5–2 mm walls) with ≥2 drain holes of 2–3 mm; min walls 0.8–1 mm; min holes 0.5 mm; no teardrops needed; clearances 0.1–0.15 mm; expect 0.5–1% post-cure shrinkage.

---

## Matching a Reference Image

1. **Analyze before modeling**: overall form → decompose into features → estimate proportion ratios → map each feature to a PartDesign operation → plan build order (structural → details).
2. **Build the base shape**, screenshot (Block E) from the reference's angle, compare.
3. **Refinement loop** (aim for 5–8 iterations, don't stop at "close enough"):
   - screenshot → list SPECIFIC differences ("base too tall ~20%", "missing top fillet", "hole pattern offset left")
   - fix the most impactful difference first (`edit_object` where possible)
   - Block F + screenshot → compare again
4. **Multi-angle verification** against all provided references (Front/Right/Top/Isometric).
5. For complex models work in phases — structure → major features → patterns → surface treatments → fine-tuning — verifying at each phase boundary.

## Reverse-Engineering an Existing STL (clean mesh)

For extending/modifying a clean STL (an earlier print model, a vendor part), measure it headlessly with **[references/stl_toolkit.py](references/stl_toolkit.py)** (system python, needs numpy+matplotlib; run `--help` for subcommands):

1. `analyze` — bbox, facet count, dominant-plane histogram along z. **The histogram is a hypothesis, never a measurement**: a round-over or fillet tessellates into a smear of near-planes and reads as a false step (live-hit 2026-08-05: a 9 mm plate with an R2 top round-over was misread as a 7 mm plate with a base fillet, costing a full correction round with the user).
2. `sections` with a **vertical cut through a feature midline** (`--y <mid>` / `--x <mid>`) — the printed (u,v) extents and the profile plot are what CONFIRM plate thickness, step heights, and where a radius actually sits. Do this BEFORE committing any dimension.
3. Horizontal `--z` cuts give outlines, wall positions and corner radii.
4. Model parametrically per this skill (MCP or headless).
5. **Acceptance test**: `overlay NEW.stl REF.stl out.png --profile-y <mid> --top-z <h>` — reference profile (red) and new profile (blue) must coincide everywhere the geometry is shared. Read the PNG and check the printed extents.

## Rebuilding from a Rough 3D Scan (PLY/mesh)

Scan meshes are noisy and misaligned — align first, then measure (via `execute_python` + numpy, or headless):

1. Load `Mesh.Mesh(path)`, points to numpy: `np.array([[p.x, p.y, p.z] for p in m.Points])`.
2. **PCA-align** to XY: `w, v = np.linalg.eigh(np.cov((pts - c).T))` — smallest eigenvector = flat-plate normal → rotate it onto Z; keep the rotation right-handed (`det(R) > 0`).
3. If the part is symmetric, **refine the rotation by silhouette symmetry**: find θ minimizing the asymmetry of a 2D occupancy histogram vs. its mirror about x=0 (PCA axes are often a few degrees off).
4. Extract profiles by **z-band slabs** (bin by y, cluster x per band → wall positions); the bottom envelope (min y per x) traces tips/hooks. Beware residual tilt (±2°) — take dimensions from **BoundBox / plane fits**, not the visual.
5. Model parametrically per this skill.
6. **Verify by overlay**: import the scan into the model document with the alignment placement, make it transparent, render top view (Block E, `viewTop()` only) — dark protrusions show mismatches. Headless: export the model STL and use `stl_toolkit.py overlay` instead. Iterate.

---

## Common Errors & Recovery

| Error | Likely cause | Fix |
|---|---|---|
| `'Sketcher.SketchObject' object has no attribute 'Support'` | called broken `create_sketch` on FC 1.1 | Block A |
| `'PartDesign.Feature' object has no attribute 'Symmetric'` | called broken `pad_sketch`/`revolution_sketch`/`groove_sketch` | Block B / C |
| `NameError: name 'Sketcher' is not defined` (or `Part`, `math`) | missing import — bridge predefines only `FreeCAD`/`App`/`FreeCADGui`/`Gui`; also raised by broken `add_sketch_rectangle` | add the import; rectangle helper |
| Tool reported success but tree has an Invalid feature | false PASS (e.g. fillet without `edges`) — tools don't check recompute results | Block F after every feature; delete the Invalid feature, redo properly |
| Fillet/chamfer fails | radius too large for adjacent geometry | reduce radius; fewer edges per feature |
| Pocket fails / cuts nothing | depth exceeds solid, or sketch not over material | `type="ThroughAll"`, or check sketch position vs. solid (Block F bbox) |
| Revolution/Groove fails | profile crosses the axis or isn't a closed wire | keep profile on one side; close the wire (Coincident constraints) |
| Loft fails | sketches on the same plane, or wire-count mismatch | separate parallel planes via Block A1 `AttachmentOffset`; same number of wires per profile |
| Feature `invalid` in tree | broken dependency after an edit | Block F names it; fix from the first invalid feature forward; worst case `undo()` |
| `solids > 1` in Block F | disjoint geometry (pad not touching the body) | fix sketch position; PartDesign requires a single connected solid |
| Sketch on face has wrong coordinates | face-local coordinate system | check `sk.Placement` (Block A2), or prefer Block A1 with `AttachmentOffset` |
| `execute_python` timeout | heavy meshing/patterns | pass `timeout_ms=120000+`; split the work |
| `ChFi3d_Builder:only 2 faces` / `Standard_NullObject ... BRepCheck_Analyzer::Init() - NULL shape` | fillet chained onto hand-built tangent sketch arcs (rounded corners drawn in the sketch) | redraw the outline as a sharp polygon; do the rounding as a 3D fillet on vertical edges (Sketch Geometry rule) |
| Edge predicate silently misses arc edges | `e.CenterOfMass` of an arc lies off the curve | use `e.valueAt((e.FirstParameter + e.LastParameter) / 2)` |
| Final bbox ~0.5–0.7 mm too big, geometry looks right | `Shape.BoundBox` NURBS control-point overshoot at fillet-over-fillet corners | verify on the exported mesh bbox (Block G) |
| Headless: `Exception while processing file: ... []` | a bare `assert` fired — freecadcmd shows only the assert message, and `[]` means there was none | give EVERY assert a message; add per-feature DBG prints |
| Feature after a pattern/mirror ignores the pattern's cuts | transform features don't advance `body.Tip` — next feature chains off the pre-pattern state | `body.Tip = pattern` right after creating it; assert `BaseFeature` chain |
| Cut reports success, volume drops, but bbox unchanged | trimmed cylinder/cone face bbox = full untrimmed surface extent | assert with `Shape.isInside(point)` + volume delta, not bbox |

**Recovery routine:** `get_console_log()` → `undo()` → Block F on the last valid state → fix → retry. Don't leave broken features in the tree.

---

## Recipes

Full version-safe recipes (rounded box, hollow enclosure, mounting plate, container + lid, knob revolution, O-ring groove, vent-slot array, bolt circle, stadium tray with perimeter ribs, tapered/lofted walls, multi-body assembly): **[references/recipes.md](references/recipes.md)** — read it before building any of those shapes.
