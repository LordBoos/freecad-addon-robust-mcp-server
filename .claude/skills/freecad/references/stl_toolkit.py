# STL verification toolkit for the freecad skill — headless analysis of STL files
# without FreeCAD GUI. Needs only numpy + matplotlib (run with system python / py -3.11).
#
# Subcommands:
#   analyze  MODEL.stl                         bbox, facet count, dominant-plane histogram
#   render   MODEL.stl OUT.png                 top view (height-colored) + shaded isometric
#   sections MODEL.stl OUT.png --z 3.5 --y 46  cross-sections; prints numeric extents
#   overlay  NEW.stl REF.stl OUT.png           compare two STLs (top outlines / profiles)
#
# Typical verification flow (reverse-engineering an existing STL):
#   1. analyze          -> plate/step heights from the plane histogram (HYPOTHESIS ONLY)
#   2. sections --y mid -> vertical profile through a feature midline (CONFIRMS geometry)
#   3. build the model, then: overlay --profile-y mid  -> ref (red) vs new (blue) must coincide
import argparse
import struct
import sys
from collections import Counter

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

AXES = {"x": 0, "y": 1, "z": 2}


def load_stl(path):
    """Return (triangles[n,3,3], normals[n,3]) from a binary or ASCII STL."""
    with open(path, "rb") as f:
        header = f.read(80)
        count_bytes = f.read(4)
        if len(count_bytes) == 4:
            n = struct.unpack("<I", count_bytes)[0]
            data = f.read()
            if len(data) >= n * 50:  # size check: genuine binary STL
                raw = np.frombuffer(data[: n * 50], dtype=np.uint8).reshape(n, 50)
                tri = raw[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(float)
                nor = raw[:, 0:12].copy().view("<f4").reshape(n, 3).astype(float)
                return tri, nor
    # ASCII fallback
    tris, nors = [], []
    cur = []
    with open(path, errors="replace") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "facet" and t[1] == "normal":
                nors.append([float(v) for v in t[2:5]])
            elif t[0] == "vertex":
                cur.append([float(v) for v in t[1:4]])
                if len(cur) == 3:
                    tris.append(cur)
                    cur = []
    if not tris:
        raise ValueError("%s: neither binary nor ASCII STL" % path)
    return np.array(tris, dtype=float), np.array(nors, dtype=float)


def bbox_str(tri):
    v = tri.reshape(-1, 3)
    lo, hi = v.min(axis=0), v.max(axis=0)
    return "x[%.3f..%.3f] y[%.3f..%.3f] z[%.3f..%.3f]  size %.3f x %.3f x %.3f" % (
        lo[0],
        hi[0],
        lo[1],
        hi[1],
        lo[2],
        hi[2],
        *(hi - lo),
    )


def dominant_planes(tri, axis, min_share=0.005):
    """Histogram of vertex coordinates along an axis — candidate feature planes.
    WARNING: a plane histogram alone is a hypothesis, not a measurement — a fillet
    tessellates into many near-planes. Confirm with a vertical section (sections --y/--x).
    """
    v = tri.reshape(-1, 3)[:, AXES[axis]]
    cnt = Counter(np.round(v, 2))
    thresh = max(1, int(len(v) * min_share))
    return sorted(float(val) for val, c in cnt.items() if c >= thresh)


def section(tri, axis, value):
    """Intersect the mesh with the plane axis=value. Returns line segments as
    (n,2,2) array in the plane's remaining two coordinates (order: the other axes).
    """
    k = AXES[axis]
    keep = [i for i in range(3) if i != k]
    a = tri[:, [0, 1, 2], :]
    b = tri[:, [1, 2, 0], :]
    da = a[:, :, k] - value
    db = b[:, :, k] - value
    cross = (da * db) < 0
    segs = []
    for ti in np.nonzero(cross.sum(axis=1) == 2)[0]:
        pts = []
        for ei in range(3):
            if cross[ti, ei]:
                f = (value - a[ti, ei, k]) / (b[ti, ei, k] - a[ti, ei, k])
                p = a[ti, ei] + f * (b[ti, ei] - a[ti, ei])
                pts.append(p[keep])
        segs.append(pts)
    return np.array(segs) if segs else np.zeros((0, 2, 2))


def print_section_extents(label, segs):
    if len(segs) == 0:
        print("%s: EMPTY (plane misses the solid)" % label)
        return
    pts = segs.reshape(-1, 2)
    print(
        "%s: u %.3f..%.3f  v %.3f..%.3f  (%d segments)"
        % (
            label,
            pts[:, 0].min(),
            pts[:, 0].max(),
            pts[:, 1].min(),
            pts[:, 1].max(),
            len(segs),
        )
    )


def subsample(tri, nor, max_faces):
    if len(tri) <= max_faces:
        return tri, nor
    idx = np.random.default_rng(0).choice(len(tri), max_faces, replace=False)
    return tri[idx], nor[idx]


def draw_top(ax, tri, title):
    zmean = tri[:, :, 2].mean(axis=1)
    order = np.argsort(zmean)  # painter's algorithm
    rng = zmean.max() - zmean.min() or 1.0
    colors = plt.cm.viridis((zmean[order] - zmean.min()) / rng)
    ax.add_collection(
        PolyCollection(tri[order][:, :, :2], facecolors=colors, edgecolors="none")
    )
    v = tri.reshape(-1, 3)
    ax.set_xlim(v[:, 0].min() - 5, v[:, 0].max() + 5)
    ax.set_ylim(v[:, 1].min() - 5, v[:, 1].max() + 5)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)


def draw_iso(ax3, tri, nor, title):
    light = np.array([0.3, 0.3, 0.9])
    norm = np.linalg.norm(nor, axis=1)
    nor = np.where(norm[:, None] > 1e-12, nor / np.maximum(norm, 1e-12)[:, None], nor)
    lam = np.clip((nor * light).sum(axis=1), 0.1, 1)
    ax3.add_collection3d(
        Poly3DCollection(
            tri, facecolors=plt.cm.Greys(0.3 + 0.6 * lam), edgecolors="none"
        )
    )
    v = tri.reshape(-1, 3)
    lo, hi = v.min(axis=0), v.max(axis=0)
    span = (hi - lo).max()
    mid = (lo + hi) / 2
    ax3.set_xlim(mid[0] - span / 2, mid[0] + span / 2)
    ax3.set_ylim(mid[1] - span / 2, mid[1] + span / 2)
    ax3.set_zlim(lo[2], lo[2] + span)
    ax3.view_init(elev=45, azim=-60)
    ax3.set_title(title)


def cmd_analyze(args):
    tri, _ = load_stl(args.model)
    print("facets:", len(tri))
    print("bbox:", bbox_str(tri))
    for axis in args.planes_axis:
        print("%s dominant planes: %s" % (axis, dominant_planes(tri, axis)))
    print(
        "NOTE: confirm feature heights with a vertical section "
        "(sections --y <feature midline>), not from the histogram alone."
    )


def cmd_render(args):
    tri, nor = load_stl(args.model)
    tri, nor = subsample(tri, nor, args.max_faces)
    fig = plt.figure(figsize=(20, 10))
    draw_top(fig.add_subplot(1, 2, 1), tri, "Top view (color = height)")
    draw_iso(fig.add_subplot(1, 2, 2, projection="3d"), tri, nor, "Isometric")
    plt.tight_layout()
    plt.savefig(args.out, dpi=80)
    print(args.out)


def cmd_sections(args):
    tri, _ = load_stl(args.model)
    cuts = (
        [("z", v) for v in args.z]
        + [("y", v) for v in args.y]
        + [("x", v) for v in args.x]
    )
    if not cuts:
        sys.exit("sections: give at least one --z/--y/--x")
    fig, axes = plt.subplots(1, len(cuts), figsize=(11 * len(cuts), 11), squeeze=False)
    for ax, (axis, val) in zip(axes[0], cuts):
        segs = section(tri, axis, val)
        for s in segs:
            ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], "b-", lw=0.8)
        keep = [a for a in "xyz" if a != axis]
        ax.set_xlabel(keep[0])
        ax.set_ylabel(keep[1])
        ax.set_aspect("equal")
        ax.set_title("section %s=%g" % (axis, val))
        ax.grid(True, alpha=0.3)
        print_section_extents("%s=%g" % (axis, val), segs)
    plt.tight_layout()
    plt.savefig(args.out, dpi=70)
    print(args.out)


def cmd_overlay(args):
    new, nnor = load_stl(args.new)
    ref, _ = load_stl(args.ref)
    ncols = (1 if args.top_z else 0) + len(args.profile_y) + len(args.profile_x)
    if ncols == 0:
        sys.exit("overlay: give --top-z and/or --profile-y/--profile-x")
    fig = plt.figure(figsize=(11 * ncols, 10))
    col = 1
    if args.top_z:
        ax = fig.add_subplot(1, ncols, col)
        col += 1
        t, n = subsample(new, nnor, args.max_faces)
        draw_top(ax, t, "NEW top view + REF outlines (red) at z=%s" % args.top_z)
        for z in args.top_z:
            for s in section(ref, "z", z):
                ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], "r-", lw=1.2)
    for axis, values in (("y", args.profile_y), ("x", args.profile_x)):
        for val in values:
            ax = fig.add_subplot(1, ncols, col)
            col += 1
            rs = section(ref, axis, val)
            ns = section(new, axis, val)
            for s in rs:
                ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], "r-", lw=1.6, alpha=0.8)
            for s in ns:
                ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], "b-", lw=0.9)
            ax.set_aspect("equal")
            ax.set_title(
                "profile %s=%g: REF red vs NEW blue (must coincide)" % (axis, val)
            )
            ax.grid(True, alpha=0.3)
            print_section_extents("REF %s=%g" % (axis, val), rs)
            print_section_extents("NEW %s=%g" % (axis, val), ns)
    plt.tight_layout()
    plt.savefig(args.out, dpi=70)
    print(args.out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze")
    a.add_argument("model")
    a.add_argument("--planes-axis", action="append", choices=list(AXES), default=None)
    a.set_defaults(func=cmd_analyze)

    r = sub.add_parser("render")
    r.add_argument("model")
    r.add_argument("out")
    r.add_argument("--max-faces", type=int, default=80000)
    r.set_defaults(func=cmd_render)

    s = sub.add_parser("sections")
    s.add_argument("model")
    s.add_argument("out")
    s.add_argument("--z", type=float, action="append", default=[])
    s.add_argument("--y", type=float, action="append", default=[])
    s.add_argument("--x", type=float, action="append", default=[])
    s.set_defaults(func=cmd_sections)

    o = sub.add_parser("overlay")
    o.add_argument("new")
    o.add_argument("ref")
    o.add_argument("out")
    o.add_argument("--top-z", type=float, action="append", default=[])
    o.add_argument("--profile-y", type=float, action="append", default=[])
    o.add_argument("--profile-x", type=float, action="append", default=[])
    o.add_argument("--max-faces", type=int, default=80000)
    o.set_defaults(func=cmd_overlay)

    args = p.parse_args()
    if args.cmd == "analyze" and args.planes_axis is None:
        args.planes_axis = ["z"]
    args.func(args)


if __name__ == "__main__":
    main()
