# FreeCAD Modeling Recipes (version-safe)

All recipes assume Step 0 is done (document + `create_partdesign_body(name="...")`) and use the
building blocks from SKILL.md: sketches and pads/revolutions/fillets via `execute_python`
(Blocks A–D), pockets/patterns via the safe MCP tools. Run **Block F verification
after every feature**. Never use `Part.makeXXX` / `Part::Feature`.

Recipe code shows the *contents* of `execute_python(code=...)` calls; plain lines are MCP tool
calls. `add_rect(sk, x, y, w, h)` is the rectangle helper from SKILL.md (Sketch Geometry) —
paste its definition into any snippet that calls it. Remember: `import Part, Sketcher` in every
snippet that uses them (the bridge predefines only FreeCAD/App/FreeCADGui/Gui).

In headless mode (freecadcmd.exe, see SKILL.md) the same recipes apply — the snippets run as-is
inside the build script, MCP-tool lines translate to their Block equivalents, and every recipe's
Block F check becomes an `assert` with a message.

---

## 1. Box with rounded edges

```python
# execute_python — sketch + rectangle + pad in one call
import Part, Sketcher
doc = FreeCAD.ActiveDocument
body = doc.getObject("RoundedBox")
sk = body.newObject("Sketcher::SketchObject", "BoxBaseSketch")
plane = body.Origin.getObject("XY_Plane")
if hasattr(sk, "AttachmentSupport"): sk.AttachmentSupport = [(plane, "")]
else: sk.Support = [(plane, "")]
sk.MapMode = "FlatFace"
# ... add_rect helper from SKILL.md ...
add_rect(sk, -20, -10, 40, 20)
pad = body.newObject("PartDesign::Pad", "BoxBasePad")
pad.Profile = sk
pad.Length = 10
pad.Midplane = False
sk.Visibility = False
doc.recompute()
_result_ = {"valid": pad.Shape.isValid(), "volume": round(pad.Shape.Volume, 2)}
```

```python
# execute_python — fillet vertical edges only (Block D variant)
doc = FreeCAD.ActiveDocument
body = doc.getObject("RoundedBox")
feat = body.Tip
edges = []
for i, e in enumerate(feat.Shape.Edges):
    vs = e.Vertexes
    if len(vs) == 2 and abs(vs[0].Point.z - vs[1].Point.z) > 1e-6 \
       and abs(vs[0].Point.x - vs[1].Point.x) < 1e-6 and abs(vs[0].Point.y - vs[1].Point.y) < 1e-6:
        edges.append("Edge%d" % (i + 1))
fil = body.newObject("PartDesign::Fillet", "BoxEdgeFillet")
fil.Base = (feat, edges)
fil.Radius = 2.0
doc.recompute()
_result_ = {"edges": edges, "valid": fil.Shape.isValid()}
```

Tree: `RoundedBox > BoxBaseSketch > BoxBasePad > BoxEdgeFillet`

---

## 2. Hollow box (enclosure)

Outer shell: as recipe 1 — Block A1 sketch on XY_Plane + `add_rect(sk, -20, -10, 40, 20)` + Block B pad (length 10).

Hollow — sketch **on the XY plane offset to the top** (no face dependency):

```python
# execute_python — hollow sketch at z=10 via AttachmentOffset (Block A1)
import Part, Sketcher
doc = FreeCAD.ActiveDocument
body = doc.getObject("Enclosure")
sk = body.newObject("Sketcher::SketchObject", "HollowSketch")
plane = body.Origin.getObject("XY_Plane")
if hasattr(sk, "AttachmentSupport"): sk.AttachmentSupport = [(plane, "")]
else: sk.Support = [(plane, "")]
sk.MapMode = "FlatFace"
sk.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, 0, 10), FreeCAD.Rotation())
# ... add_rect helper from SKILL.md ...
add_rect(sk, -18, -8, 36, 16)
doc.recompute()
_result_ = {"sketch": sk.Name}
```

```
pocket_sketch(sketch_name="HollowSketch", length=8, name="HollowPocket")
```

Wall = 2 mm sides (40−36)/2, floor = 2 mm (10−8). FDM minimum 1.2 mm respected.
Tree: `Enclosure > OuterSketch > OuterPad > HollowSketch > HollowPocket`

---

## 3. Plate with mounting holes

Base: Block A1 sketch + `add_rect(sk, -30, -20, 60, 40)` + Block B pad (length 3).

Holes — one sketch, four circles, one pocket:

```
add_sketch_circle(sketch_name="MountingHolesSketch", center_x=-22, center_y=-12, radius=2.5)
add_sketch_circle(sketch_name="MountingHolesSketch", center_x=22,  center_y=-12, radius=2.5)
add_sketch_circle(sketch_name="MountingHolesSketch", center_x=-22, center_y=12,  radius=2.5)
add_sketch_circle(sketch_name="MountingHolesSketch", center_x=22,  center_y=12,  radius=2.5)
pocket_sketch(sketch_name="MountingHolesSketch", type="ThroughAll", length=3, name="MountingHolesPocket")
```

(FDM: for M5 screws use radius 2.6–2.7 — +0.1–0.2 mm diametral clearance. Vertical holes print fine as circles.)

---

## 4. Cylindrical container with lid (two bodies)

```
create_partdesign_body(name="Container")
```

- `ContainerOuterSketch` (Block A1, XY): circle r=15 → Block B pad, length 30
- `ContainerHollowSketch` (Block A1, `AttachmentOffset` z=30): circle r=13 → `pocket_sketch(length=28)` → 2 mm walls and floor

```
create_partdesign_body(name="Lid")
```

- `LidCapSketch` (Block A1, XY): circle r=15.5 → Block B pad, length 3
- `LidInsertSketch` (Block A1, `AttachmentOffset` z=3): circle r=12.7 → Block B pad, length 5

Insert r=12.7 vs. hollow r=13 → 0.3 mm radial clearance (FDM slip fit).

```
set_placement(object_name="Lid", position=[0, 0, 35])      # park above for viewing/export
set_object_color(object_name="Lid", color=[0.9, 0.5, 0.2])
```

Export each body as its own STL (Block G per body).

---

## 5. Knob / handle (revolution)

Profile sketch on XZ_Plane (Block A1 with `plane = body.Origin.getObject("XZ_Plane")`), closed
half-profile right of the axis:

```
add_sketch_line(sketch_name="KnobProfileSketch", x1=0,  y1=0, x2=10, y2=0)
add_sketch_line(sketch_name="KnobProfileSketch", x1=10, y1=0, x2=10, y2=5)
add_sketch_line(sketch_name="KnobProfileSketch", x1=10, y1=5, x2=8,  y2=8)
add_sketch_line(sketch_name="KnobProfileSketch", x1=8,  y1=8, x2=0,  y2=8)
add_sketch_line(sketch_name="KnobProfileSketch", x1=0,  y1=8, x2=0,  y2=0)
```

Then Block C revolution around the sketch **V_Axis** (`rev.ReferenceAxis = (sk, ["V_Axis"])`, angle 360).
On the XZ plane the sketch V axis = global Z, so the knob stands upright.

---

## 6. O-ring groove

Plug built first (revolution or pad of a circle). Groove profile: small rectangle sketch on
XZ_Plane at the groove's radial position, then Block C with `"PartDesign::Groove"` around Z:

```python
groove = body.newObject("PartDesign::Groove", "OringGroove")
groove.Profile = doc.getObject("GrooveProfileSketch")
groove.ReferenceAxis = (body.Origin.getObject("Z_Axis"), [""])
groove.Angle = 360
```

---

## 7. Vent slot array (linear pattern)

One slot through a wall, then pattern. Sketch the slot on the appropriate origin plane offset to
the wall (Block A1) or on the wall face (Block A2 with a predicate), adding
`add_rect(sk, -1, -8, 2, 16)` in the same `execute_python` call, then:

```
pocket_sketch(sketch_name="VentSlotSketch", length=2, name="VentSlotPocket")
linear_pattern(feature_name="VentSlotPocket", direction="X", length=40, occurrences=8, name="VentSlotPattern")
```

`length` is the **total** span (first to last occurrence). Verify with Block F + screenshot —
partial patterns mean the direction or span is wrong.

---

## 8. Bolt circle (polar pattern)

Single hole as circle + pocket (threaded `create_hole` is broken; FDM shouldn't model threads anyway):

```
add_sketch_circle(sketch_name="BoltHoleSketch", center_x=20, center_y=0, radius=2.6)
pocket_sketch(sketch_name="BoltHoleSketch", type="ThroughAll", length=8, name="BoltHolePocket")
polar_pattern(feature_name="BoltHolePocket", axis="Z", angle=360, occurrences=6, name="BoltCirclePattern")
```

---

## 9. Stadium tray with perimeter ribs

Target tree: `TrayBody > OuterProfileSketch > OuterPad > HollowSketch > HollowPocket > RibSlotsSketch > RibPocket > TopFillet`

**Stadium outline** (populate an A1 sketch inline — same `execute_python` call as sketch creation):

```python
import Part, Sketcher, math
doc = FreeCAD.ActiveDocument
body = doc.getObject("TrayBody")
sk = body.newObject("Sketcher::SketchObject", "OuterProfileSketch")
plane = body.Origin.getObject("XY_Plane")
if hasattr(sk, "AttachmentSupport"): sk.AttachmentSupport = [(plane, "")]
else: sk.Support = [(plane, "")]
sk.MapMode = "FlatFace"
L, W = 120, 60
R = W / 2.0
s = L - W                      # straight section length
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(-s/2, -R, 0), FreeCAD.Vector(s/2, -R, 0)))
sk.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(s/2, 0, 0), FreeCAD.Vector(0,0,1), R), -math.pi/2, math.pi/2))
sk.addGeometry(Part.LineSegment(FreeCAD.Vector(s/2, R, 0), FreeCAD.Vector(-s/2, R, 0)))
sk.addGeometry(Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(-s/2, 0, 0), FreeCAD.Vector(0,0,1), R), math.pi/2, 3*math.pi/2))
for i in range(4):
    sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i+1) % 4, 1))
doc.recompute()
_result_ = {"geometry": sk.GeometryCount}
```

Pad 15 mm (Block B). Hollow: same stadium shrunk by wall thickness (`R -= 2.5`, same `s`) on a
sketch with `AttachmentOffset` z=15, then `pocket_sketch(length=12)`.

**Ribs around the perimeter** — linear/polar patterns can't follow a stadium. Put ALL slots into
one sketch and pocket once. For slots wrapping the curved ends, compute positions along the
perimeter parametrically; for the straight sides a flat sketch offset to the wall works:

```python
import Part, Sketcher
doc = FreeCAD.ActiveDocument
body = doc.getObject("TrayBody")
sk = body.newObject("Sketcher::SketchObject", "RibSlotsSketch")
plane = body.Origin.getObject("XZ_Plane")            # vertical plane facing the long side
if hasattr(sk, "AttachmentSupport"): sk.AttachmentSupport = [(plane, "")]
else: sk.Support = [(plane, "")]
sk.MapMode = "FlatFace"
sk.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, 0, -30), FreeCAD.Rotation())  # at y=-30 wall
doc.recompute()
slot_w, slot_h, spacing, n = 1.0, 10.0, 2.5, 24
x0 = -(n - 1) * spacing / 2.0
g = 0
for i in range(n):
    x = x0 + i * spacing - slot_w / 2.0
    p = [FreeCAD.Vector(x, 3, 0), FreeCAD.Vector(x + slot_w, 3, 0),
         FreeCAD.Vector(x + slot_w, 3 + slot_h, 0), FreeCAD.Vector(x, 3 + slot_h, 0)]
    for j in range(4):
        sk.addGeometry(Part.LineSegment(p[j], p[(j + 1) % 4]))
    for j in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", g + j, 2, g + (j + 1) % 4, 1))
    g += 4
doc.recompute()
_result_ = {"slots": n, "geometry": sk.GeometryCount}
```

Then `pocket_sketch(sketch_name="RibSlotsSketch", length=1.5, name="RibPocket")` (pocket cuts
toward the solid; use `reversed` via `edit_object` if it cuts away from it). Repeat for the
opposite wall (offset +30, or `mirrored_feature` on the pocket). Top rim fillet: Block D.

**Rounded rectangle / rounded polygon outline — do NOT draw the corner arcs in the sketch.**
Draw the outline as a SHARP polygon (`add_rect` or the polygon helper), pad, then round the
vertical corner edges with a `PartDesign::Fillet` (Block D, vertical-edge predicate). Hand-built
corner `ArcOfCircle` geometry breaks downstream fillets at the tangent line–arc junctions
(`ChFi3d_Builder:only 2 faces`, `Standard_NullObject ... NULL shape`). Sketch arcs belong only
where the arc IS the wall — the stadium's half-circle ends above, full circles, revolution
profiles.

---

## 10. Tapered / curved walls

**Stacked pads** (simple taper): pad bottom profile, next sketch slightly larger with
`AttachmentOffset` at the pad top, pad again. Every step editable.

**Loft** (smooth taper): create 2+ profile sketches on XY_Plane with increasing
`AttachmentOffset` z values (do NOT pad them first), then:

```
loft_sketches(sketch_names=["BottomSketch", "TopSketch"], ruled=False, name="WallLoft")
```

Wire counts must match between profiles. `ruled=True` gives straight (conical) walls,
`False` smooth interpolation.

**Rotationally symmetric bulge**: draw the wall cross-section as a closed half-profile and use
Block C revolution instead.

---

## 11. Multi-part assembly (bracket + base plate)

- One `create_partdesign_body` per part; each body independently editable.
- Build each part at the global origin in its natural print orientation, then position with
  `set_placement(object_name=..., position=[x, y, z], rotation=[yaw, pitch, roll])`.
- Check mating clearances numerically: Block F bbox per body, or
  `shape1.distToShape(shape2)[0]` in `execute_python` (expect 0.2–0.4 mm for FDM fits).
- `set_object_color` per body for readable screenshots.
- Export one STL per body (Block G with that body's `Tip.Shape`).
