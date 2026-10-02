#!/usr/bin/env python3
"""Isometric block renderer for The Digimod block models.

Reads the mod's real Blockbench/vanilla model JSON (from/to + per-face uv)
and the real block texture, then renders a true-isometric 3-quarter view
PNG with simple directional shading - the same kind of "block photo" you'd
see on a wiki, without needing a running Minecraft client.

Only handles the 3 model shapes actually used by The Digimod's blocks:
cube_all (ores), a Blockbench custom box element (Digitama eggs), and
cross/crop planes (LED Shroom, Digimeat Crop). Extend FACE_CORNERS/NORMALS
if a future block uses a genuinely different shape (slabs, stairs, etc).

Before running, fetch the block model JSON from the mod's public repo into
MODEL_DIR, e.g.:
  BASE="https://raw.githubusercontent.com/themodderg/The-Digimod/main/src/main/resources/assets/thedigimod/models/block"
  curl -s -o "$MODEL_DIR/<name>.json" "$BASE/<name>.json"
Textures (TEX_DIR) come from the same repo's textures/block/ folder and are
already checked into src/assets/images/the_digimod/blocks/flat/ - the flat
originals kept there so blocks can be re-rendered without re-fetching.

Usage: python3 render_td_blocks.py
"""
import json
import math
import os

import numpy as np
from PIL import Image

MODEL_DIR = "/tmp/td_blockmodels"
TEX_DIR = "/home/codderg/raid/webs/codderg/src/assets/images/the_digimod/blocks/flat"
OUT_DIR = "/home/codderg/raid/webs/codderg/src/assets/images/the_digimod/blocks"
SCALE = 9.2  # pixels per Minecraft model unit (0-16 box -> ~147px before margin)

os.makedirs(OUT_DIR, exist_ok=True)

# True isometric angles (matches the classic MC wiki block-icon look).
YAW = math.radians(45)
PITCH = math.radians(35.264)

# Outward face normals in model space, used for analytic front/back-face
# culling (dot with the rotated view axis) - far more robust than testing
# the sign of the projected 2D polygon area.
NORMALS = {
    "up": (0, 1, 0), "down": (0, -1, 0),
    "north": (0, 0, -1), "south": (0, 0, 1),
    "east": (1, 0, 0), "west": (-1, 0, 0),
}

# Shading per axis-aligned face, approximating Minecraft's directional light.
SHADE = {
    "up": 1.0, "down": 0.45,
    "north": 0.7, "south": 0.7,
    "east": 0.55, "west": 0.85,
}

FACE_CORNERS = {
    # each face: 4 corners (x,y,z) in winding order, outward-facing
    "up":    lambda x0,y0,z0,x1,y1,z1: [(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
    "down":  lambda x0,y0,z0,x1,y1,z1: [(x0,y0,z1),(x1,y0,z1),(x1,y0,z0),(x0,y0,z0)],
    "north": lambda x0,y0,z0,x1,y1,z1: [(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
    "south": lambda x0,y0,z0,x1,y1,z1: [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
    "east":  lambda x0,y0,z0,x1,y1,z1: [(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],
    "west":  lambda x0,y0,z0,x1,y1,z1: [(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
}


def rot_matrix():
    cy, sy = math.cos(YAW), math.sin(YAW)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    cx, sx = math.cos(PITCH), math.sin(PITCH)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return rx @ ry


R = rot_matrix()


def face_visible(face_name):
    """Analytic front/back-face test: visible if the rotated outward
    normal points toward the camera (camera sits at +Z looking toward
    -Z after our rotation)."""
    n = NORMALS.get(face_name)
    if n is None:
        return True
    rn = R @ np.array(n)
    return rn[2] > 0


def project(p):
    """Rotate a model-space point (0-16 cube coords, centered) and drop Z."""
    v = np.array(p) - 8.0
    v = R @ v
    return v  # keep z for depth sort; caller picks x,y for screen


def to_screen(v, ox, oy):
    return (ox + v[0] * SCALE, oy - v[1] * SCALE)


def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def draw_quad(canvas, texture, uv_px, tex_w, tex_h, screen_pts, shade):
    """Paste `texture` cropped at uv_px (x0,y0,x1,y1 in texture pixels)
    warped onto the parallelogram screen_pts (4 points, matching face
    winding: top-left, top-right/first-adjacent, bottom-right, bottom-left
    in *texture* space order)."""
    x0, y0, x1, y1 = uv_px
    crop = texture.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    if cw <= 0 or ch <= 0:
        return
    if shade != 1.0:
        arr = np.array(crop).astype(np.float32)
        arr[..., :3] *= shade
        crop = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # Screen-space bounding box for the destination
    xs = [p[0] for p in screen_pts]
    ys = [p[1] for p in screen_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    dw, dh = max(1, int(maxx - minx) + 2), max(1, int(maxy - miny) + 2)

    # Map source rect corners (0,0),(cw,0),(cw,ch),(0,ch) -> dest corners
    # (screen_pts, shifted into local dw/dh space) via a full 3x3 affine
    # solve (parallelogram-safe: uses 3 points then checks the 4th).
    dst = [(p[0] - minx, p[1] - miny) for p in screen_pts]
    src = [(0, 0), (cw, 0), (cw, ch), (0, ch)]

    # Solve affine x' = a*x + b*y + c, y' = d*x + e*y + f from first 3 pts
    (sx0, sy0), (sx1, sy1), (sx2, sy2) = src[0], src[1], src[3]
    (dx0, dy0), (dx1, dy1), (dx2, dy2) = dst[0], dst[1], dst[3]
    A = np.array([[sx0, sy0, 1], [sx1, sy1, 1], [sx2, sy2, 1]])
    Bx = np.array([dx0, dx1, dx2])
    By = np.array([dy0, dy1, dy2])
    try:
        coefx = np.linalg.solve(A, Bx)
        coefy = np.linalg.solve(A, By)
    except np.linalg.LinAlgError:
        return
    # PIL AFFINE transform wants dest->src coefficients (inverse map)
    fwd = np.array([[coefx[0], coefx[1], coefx[2]],
                     [coefy[0], coefy[1], coefy[2]],
                     [0, 0, 1]])
    try:
        inv = np.linalg.inv(fwd)
    except np.linalg.LinAlgError:
        return
    coeffs = (inv[0, 0], inv[0, 1], inv[0, 2], inv[1, 0], inv[1, 1], inv[1, 2])
    # NEAREST, not BICUBIC: these are pixel-art block textures - smooth
    # resampling blurs every edge. Supersample the crop first so the warp
    # still has enough source resolution to avoid obvious jaggies.
    SS = 4
    big_crop = crop.resize((cw * SS, ch * SS), Image.NEAREST)
    big_coeffs = (inv[0, 0] * SS, inv[0, 1] * SS, inv[0, 2] * SS,
                  inv[1, 0] * SS, inv[1, 1] * SS, inv[1, 2] * SS)
    warped = big_crop.transform((dw, dh), Image.AFFINE, big_coeffs, resample=Image.NEAREST)
    canvas.alpha_composite(warped, (int(round(minx)), int(round(miny))))


def render_quads(quads, out_path, label=""):
    """Common finishing pass: quads is a list of (depth, screen_pts, uv_px,
    tex, shade), with screen_pts computed against an arbitrary (0,0) origin
    (to_screen(v, 0, 0)). Sizing the canvas to a fixed guess clipped real
    geometry (the front-bottom vertex of a cube legitimately projects well
    below the block's own footprint at this camera angle) - so instead the
    canvas is sized exactly to whatever the projected geometry needs, with a
    small pad, computed from the actual screen coordinates."""
    all_pts = [p for _, screen, *_ in quads for p in screen]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    pad = 6
    minx, miny = min(xs) - pad, min(ys) - pad
    maxx, maxy = max(xs) + pad, max(ys) + pad
    width, height = int(math.ceil(maxx - minx)), int(math.ceil(maxy - miny))

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    quads = sorted(quads, key=lambda q: q[0])  # far first (painter's algorithm)
    for depth, screen, uv_px, tex, shade in quads:
        shifted = [(p[0] - minx, p[1] - miny) for p in screen]
        draw_quad(canvas, tex, uv_px, tex.width, tex.height, shifted, shade)

    canvas.save(out_path)
    print("wrote", out_path, canvas.size, label)


def render_box(elements, texture_paths, tex_size, out_path, label=""):
    quads = []  # (depth, screen_pts, uv_px, tex, shade)

    for el in elements:
        x0, y0, z0 = el["from"]
        x1, y1, z1 = el["to"]
        faces = el["faces"]
        for face_name, spec in faces.items():
            if face_name not in FACE_CORNERS:
                continue
            if not face_visible(face_name):
                continue  # back-facing, cull (analytic normal test)
            corners3d = FACE_CORNERS[face_name](x0, y0, z0, x1, y1, z1)
            rotated = [project(c) for c in corners3d]
            depth = sum(v[2] for v in rotated) / 4.0
            screen = [to_screen(v, 0, 0) for v in rotated]
            uv = spec["uv"]
            tw, th = tex_size
            uv_px = (uv[0] / 16 * tw, uv[1] / 16 * th, uv[2] / 16 * tw, uv[3] / 16 * th)
            tex_key = spec.get("texture", "#0").lstrip("#")
            tex = texture_paths.get(tex_key, texture_paths.get("0"))
            quads.append((depth, screen, uv_px, tex, SHADE.get(face_name, 1.0)))

    render_quads(quads, out_path, label)


def rotate_y(p, angle_deg, pivot=(8, 8, 8)):
    a = math.radians(angle_deg)
    x, y, z = p
    px, py, pz = pivot
    x, z = x - px, z - pz
    xr = x * math.cos(a) - z * math.sin(a)
    zr = x * math.sin(a) + z * math.cos(a)
    return (xr + px, y, zr + pz)


def render_cross(texture, out_path):
    """Cross/crop model (LED Shroom, Digimeat Crop) - the same two crossing
    planes Minecraft itself uses in-world (assets/minecraft/models/block/
    cross.json): a plane at z=8 and one at x=8, each 14.4 units wide,
    rotated +-45 degrees about the Y axis through the block center. Both
    are double-sided/unshaded in-game (shade: false), so we draw one
    consistent winding per plane with no shading and paint far-to-near."""
    tw, th = texture.width, texture.height
    uv_px = (0, 0, tw, th)
    plane_a = [rotate_y(p, 45) for p in
               [(0.8, 16, 8), (15.2, 16, 8), (15.2, 0, 8), (0.8, 0, 8)]]
    plane_b = [rotate_y(p, -45) for p in
               [(8, 16, 0.8), (8, 16, 15.2), (8, 0, 15.2), (8, 0, 0.8)]]

    quads = []
    for plane in (plane_a, plane_b):
        rotated = [project(c) for c in plane]
        depth = sum(v[2] for v in rotated) / 4.0
        screen = [to_screen(v, 0, 0) for v in rotated]
        quads.append((depth, screen, uv_px, texture, 1.0))
    render_quads(quads, out_path)


CUBE_ELEMENTS = [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": {
    f: {"uv": [0, 0, 16, 16], "texture": "#0"} for f in FACE_CORNERS
}}]

CUBES = ["digi_card_ore", "digi_card_deepslate_ore", "huanglong_deepslate_ore"]
CROSSES = ["led_shroom", "digimeat_crop"]
BOXES = ["digitama_dragon", "digitama_beast", "digitama_holy", "digitama_plantinsect",
         "digitama_nightmare", "digitama_wind", "digitama_earth", "digitama_aquan",
         "digitama_machine"]

ITEMS_DIR = "/home/codderg/raid/webs/codderg/src/assets/images/the_digimod/items"


def main():
    for name in CUBES:
        tex_path = os.path.join(TEX_DIR, f"{name}.png")
        if not os.path.exists(tex_path):
            tex_path = os.path.join(ITEMS_DIR, f"{name}.png")
        tex = Image.open(tex_path).convert("RGBA")
        render_box(CUBE_ELEMENTS, {"0": tex}, (tex.width, tex.height),
                   os.path.join(OUT_DIR, f"{name}.png"), name)

    for name in CROSSES:
        tex_name = "digimeat_crop" if name == "digimeat_crop" else name
        tex = Image.open(os.path.join(TEX_DIR, f"{tex_name}.png")).convert("RGBA")
        render_cross(tex, os.path.join(OUT_DIR, f"{name}.png"))

    for name in BOXES:
        model = json.load(open(os.path.join(MODEL_DIR, f"{name}.json")))
        tex = Image.open(os.path.join(TEX_DIR, f"{name}.png")).convert("RGBA")
        render_box(model["elements"], {"0": tex}, tuple(model.get("texture_size", [tex.width, tex.height])),
                   os.path.join(OUT_DIR, f"{name}.png"), name)

    print("done")


if __name__ == "__main__":
    main()
