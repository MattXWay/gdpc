"""
shinto_shrine.py  —  MGAIA Retake Assignment 1, Leiden University 2026
Procedurally generates a Shinto shrine complex using GDPC.
"""

#if you want to make a the width of the shrine grounds smaller, you can use

import sys
import math
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gdpc import Editor, Block
from gdpc.geometry import placeCuboid

editor = Editor(buffering=True)
buildArea = editor.getBuildArea()
editor.loadWorldSlice(cache=True)

BAX = buildArea.offset.x
BAZ = buildArea.offset.z
BAW = buildArea.size.x
BAD = buildArea.size.z

heightmap   = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
ocean_floor = editor.worldSlice.heightmaps["OCEAN_FLOOR"]

RNG = random.Random()

# ---------------------------------------------------------------------------
# Terrain helpers
# ---------------------------------------------------------------------------

def get_height(local_x, local_z):
    lx = max(0, min(local_x, BAW - 1))
    lz = max(0, min(local_z, BAD - 1))
    return int(heightmap[lx, lz])

def has_water(local_x, local_z):
    lx = max(0, min(local_x, BAW - 1))
    lz = max(0, min(local_z, BAD - 1))
    return int(ocean_floor[lx, lz]) < int(heightmap[lx, lz])

def terrain_flatness(lx0, lz0, w, d):
    hs = [get_height(lx0 + i, lz0 + j) for i in range(w) for j in range(d)]
    return 1.0 / (1.0 + float(np.std(hs)))

def terrain_dryness(lx0, lz0, w, d):
    total = w * d
    wet = sum(1 for i in range(w) for j in range(d) if has_water(lx0+i, lz0+j))
    return 1.0 - wet / total

def scan_build_site(footprint_w, footprint_d, stride=3):
    cols = range(0, BAW - footprint_w, stride)
    rows = range(0, BAD - footprint_d, stride)
    grid_w = len(list(cols))
    grid_d = len(list(rows))
    flatness_grid = np.zeros((grid_w, grid_d))
    dryness_grid  = np.zeros((grid_w, grid_d))
    quality_grid  = np.zeros((grid_w, grid_d))
    best_score = -1.0
    best_lx, best_lz = 0, 0
    for gi, lx in enumerate(range(0, BAW - footprint_w, stride)):
        for gj, lz in enumerate(range(0, BAD - footprint_d, stride)):
            f = terrain_flatness(lx, lz, footprint_w, footprint_d)
            d = terrain_dryness(lx, lz, footprint_w, footprint_d)
            q = 0.65 * f + 0.35 * d
            flatness_grid[gi, gj] = f
            dryness_grid[gi, gj]  = d
            quality_grid[gi, gj]  = q
            if q > best_score:
                best_score = q
                best_lx, best_lz = lx, lz
    return best_lx, best_lz, quality_grid, flatness_grid, dryness_grid

def save_terrain_plots(quality_grid, flatness_grid, dryness_grid,
                       best_lx, best_lz, footprint_w, footprint_d, stride=3):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    grids  = [flatness_grid, dryness_grid, quality_grid]
    titles = ["Flatness score", "Dryness score", "Combined quality $Q_{total}$"]
    cmaps  = ["YlOrRd", "Blues_r", "hot"]
    for ax, grid, title, cmap in zip(axes, grids, titles, cmaps):
        gw, gd = grid.shape
        extent = [0, gw * stride, 0, gd * stride]
        im = ax.imshow(grid.T, origin="upper", cmap=cmap, extent=extent, aspect="auto")
        plt.colorbar(im, ax=ax)
        ax.set_title(title)
        ax.set_xlabel("x (build area)")
        ax.set_ylabel("z (build area)")
    ax = axes[2]
    rect = plt.Rectangle((best_lx, best_lz), footprint_w, footprint_d,
                          linewidth=2, edgecolor="cyan", facecolor="none",
                          label="Chosen site")
    ax.add_patch(rect)
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig("terrain_evaluation.png", dpi=150)
    plt.close()
    print("[INFO] Saved terrain_evaluation.png")

# ---------------------------------------------------------------------------
# Block palettes
# ---------------------------------------------------------------------------

STONE_PALETTE = [
    Block("stone_bricks"),
    Block("stone_bricks"),
    Block("cracked_stone_bricks"),
    Block("mossy_stone_bricks"),
]
WOOD_PALETTE = [
    3*[Block("spruce_planks")],
    Block("acacia_planks"),
    Block("mangrove_planks"),
    Block("pale_oak_planks"),
]

PILLAR_BLOCK    = Block("red_concrete")              # red structural pillars
BEAM_BLOCK      = Block("red_concrete")              # red eave beams
BEAM_BLOCK_Z    = Block("red_concrete")              # red eave beams (z)
ROOF_BLOCK      = Block("warped_planks")             # dark teal roof body
ROOF_SLAB_B     = Block("oxidized_cut_copper_slab", {"type": "bottom"})  # copper eave overhang
ROOF_TOP        = Block("oxidized_cut_copper_slab", {"type": "top"})     # copper eave top
# Wall materials
WALL_BLOCK      = Block("white_concrete")            # white plaster panels
WALL_TRIM       = Block("red_concrete")              # red base/top trim
RAILING_BLOCK   = Block("crimson_fence")             # red nether fence railings
LANTERN         = Block("lantern", {"hanging": "false"})
HANGING_LANTERN = Block("lantern", {"hanging": "true"})
GRAVEL          = Block("gravel")
COARSE_DIRT     = Block("coarse_dirt")
AIR             = Block("air")
GLOWSTONE       = Block("glowstone")
RED_CONCRETE    = Block("red_concrete")
STONE_SLAB      = Block("stone_brick_slab", {"type": "bottom"})
CHAIN           = Block("iron_chain")

def rand_stone():
    return RNG.choice(STONE_PALETTE)

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def place(wx, wy, wz, block):
    editor.placeBlock((wx, wy, wz), block)

def fill(wx0, wy0, wz0, wx1, wy1, wz1, block):
    placeCuboid(editor, (wx0, wy0, wz0), (wx1, wy1, wz1), block)

def fill_palette(wx0, wy0, wz0, wx1, wy1, wz1, palette):
    for gx in range(min(wx0,wx1), max(wx0,wx1)+1):
        for gy in range(min(wy0,wy1), max(wy0,wy1)+1):
            for gz in range(min(wz0,wz1), max(wz0,wz1)+1):
                editor.placeBlock((gx, gy, gz), RNG.choice(palette))

# ---------------------------------------------------------------------------
# Terrain levelling
# ---------------------------------------------------------------------------

def level_ground(wx0, wz0, w, d, target_y):
    for ix in range(w):
        for iz in range(d):
            col_x = wx0 + ix
            col_z = wz0 + iz
            s = get_height(col_x - BAX, col_z - BAZ)
            if s > target_y:
                for ky in range(target_y, s + 2):
                    place(col_x, ky, col_z, AIR)
            elif s < target_y:
                for ky in range(s, target_y):
                    place(col_x, ky, col_z, rand_stone())
            place(col_x, target_y - 1, col_z, rand_stone())

# ---------------------------------------------------------------------------
# Orientation helpers
# ---------------------------------------------------------------------------

ORIENTATIONS = ["north", "south", "east", "west"]

def rotate_offset(dx, dz, facing):
    if facing == "south": return  dx,  dz
    if facing == "north": return -dx, -dz
    if facing == "east":  return  dz, -dx
    if facing == "west":  return -dz,  dx
    return dx, dz

def opposite(facing):
    return {"north":"south","south":"north","east":"west","west":"east"}[facing]

# ---------------------------------------------------------------------------
# ShrineBuilder
# ---------------------------------------------------------------------------

class ShrineBuilder:

    def __init__(self, cx, cy, cz, facing, scale):
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.facing = facing
        self.scale  = scale
        s = scale

        # ── Honden (main hall) ──────────────────────────────────────────────
        self.hall_w  = 7 + s * 2          # total width
        self.hall_d  = 9 + s * 2          # depth front→back
        self.hall_h  = 7 + s

        # ── Haiden (prayer hall) ────────────────────────────────────────────
        self.hd_w    = self.hall_w + 6    # wider than honden
        self.hd_d    = 7 + s              # depth
        self.hd_h    = self.hall_h - 1

        # ── Explicit linear layout (dz = forward from origin) ───────────────
        # origin (dz=0) = entrance face of haiden (where players walk in)
        # everything forward of origin is positive dz.
        GAP          = 10                   # gap between haiden back and honden front
        self.haiden_fwd_front = 0          # haiden entrance face
        self.haiden_fwd_back  = self.hd_d  # haiden back wall
        self.honden_fwd_start = self.hd_d + GAP          # honden front wall
        self.honden_fwd_end   = self.honden_fwd_start + self.hall_d  # honden back wall

        # ── Path & torii (negative dz = in front of haiden entrance) ───────
        self.path_len    = 20 + s * 4     # path from origin back to first torii
        self.torii_count = RNG.randint(1, 2 + s)

        # ── Variation ───────────────────────────────────────────────────────
        self.has_lanterns    = RNG.random() < 0.85
        self.has_fence       = RNG.random() < 0.70
        self.has_offering    = RNG.random() < 0.60
        self.lantern_spacing = RNG.randint(3, 6)

    def w(self, dx, dz, dy=0):
        rdx, rdz = rotate_offset(dx, dz, self.facing)
        return self.cx + rdx, self.cy + dy, self.cz + rdz

    # -----------------------------------------------------------------------
    # Torii gate
    # -----------------------------------------------------------------------

    def build_torii(self, fwd_offset, gate_w=5, gate_h=6):
        """
        Torii layout (dy from ground):
          0 .. gate_h-1   pillars (red concrete, both sides)
          gate_h - 3      nuki  — lower beam, pillar-width only
          gate_h - 2      GAP   — empty row (the signature open space)
          gate_h - 1      kasagi — upper beam, +1 wider each side
          gate_h          shimagi — cap, +1 wider again

        Each beam is placed at fwd_offset AND fwd_offset+1 (2 blocks deep).
        """
        half = gate_w // 2

        nuki_y    = gate_h - 3   # lower beam
        kasagi_y  = gate_h - 1   # upper beam (gap row = gate_h-2 between them)
        shimagi_y = gate_h        # cap

        for depth in (fwd_offset, fwd_offset + 1):
            # Pillars run the FULL height from ground to just below kasagi,
            # so the gap row still has a pillar block on each side — no floating.
            for side in (-half, half):
                for dy in range(0, kasagi_y):
                    bx, by, bz = self.w(side, depth, dy)
                    place(bx, by, bz, RED_CONCRETE)

            # Nuki (lower beam) — spans pillar-to-pillar only
            for dx in range(-half, half + 1):
                bx, by, bz = self.w(dx, depth, nuki_y)
                place(bx, by, bz, RED_CONCRETE)

            # dy = gate_h-2 : pillars continue here (placed above), beam is absent
            # This is the visible gap between nuki and kasagi

            # Kasagi (upper beam) — 1 wider each side
            for dx in range(-half - 1, half + 2):
                bx, by, bz = self.w(dx, depth, kasagi_y)
                place(bx, by, bz, RED_CONCRETE)

            # Shimagi (cap) — 1 wider again
            for dx in range(-half - 2, half + 3):
                bx, by, bz = self.w(dx, depth, shimagi_y)
                place(bx, by, bz, RED_CONCRETE)

        # Hanging lanterns below nuki (front face only)
        for side in (-half + 1, half - 1):
            bx, by, bz = self.w(side, fwd_offset, nuki_y - 1)
            place(bx, by, bz, CHAIN)
            bx2, by2, bz2 = self.w(side, fwd_offset, nuki_y - 2)
            place(bx2, by2, bz2, HANGING_LANTERN)

    # -----------------------------------------------------------------------
    # Path
    # -----------------------------------------------------------------------

    def build_path(self):
        # Path runs from -path_len (torii approach) to honden back wall
        path_w    = 3
        fwd_start = -self.path_len
        fwd_end   = self.honden_fwd_end
        for fwd in range(fwd_start, fwd_end + 1):
            for side in range(-path_w // 2+1, path_w // 2+1):
                bx, by, bz = self.w(side, fwd, 0)
                place(bx, by - 1, bz, Block("spruce_planks"))
                place(bx, by,     bz, AIR)

    # -----------------------------------------------------------------------
    # Stone lanterns
    # -----------------------------------------------------------------------

    def build_lanterns(self):
        # Lanterns line the approach path (negative fwd) and the courtyard
        spacing = self.lantern_spacing
        for fwd in range(-self.path_len + spacing, self.haiden_fwd_front, spacing):
            for side in (-2, 2):
                bx, by, bz = self.w(side, fwd, 0)
                place(bx, by,     bz, Block("stone_brick_wall"))
                place(bx, by + 1, bz, Block("stone_brick_wall"))
                place(bx, by + 2, bz, Block("stone_bricks"))
                place(bx, by + 3, bz, LANTERN)

    # -----------------------------------------------------------------------
    # Perimeter fence
    # -----------------------------------------------------------------------

    def build_fence(self):
        # Fence wraps only the honden block (not haiden)
        hw   = self.hall_w // 2 + 2
        f0   = self.honden_fwd_start - 1   # just in front of honden
        f1   = self.honden_fwd_end   + 1   # just behind honden
        # Front fence (leave 3-wide opening for path)
        for side in range(-hw, hw + 1):
            if abs(side) > 1:
                bx, by, bz = self.w(side, f0, 0)
                place(bx, by, bz, Block("stone_brick_wall"))
        # Back fence
        for side in range(-hw, hw + 1):
            bx, by, bz = self.w(side, f1, 0)
            place(bx, by, bz, Block("stone_brick_wall"))
        # Side fences
        for fwd in range(f0, f1 + 1):
            bx, by, bz = self.w(-hw, fwd, 0)
            place(bx, by, bz, Block("stone_brick_wall"))
            bx, by, bz = self.w( hw, fwd, 0)
            place(bx, by, bz, Block("stone_brick_wall"))

    # -----------------------------------------------------------------------
    # Honden
    # -----------------------------------------------------------------------

    def build_honden(self):
        hw        = self.hall_w // 2
        d         = self.hall_d
        h         = self.hall_h
        fwd_start = self.honden_fwd_start

        # Stone foundation under hall
        fill_palette(*self.w(-hw - 1, fwd_start,     -1),
                     *self.w( hw + 1, fwd_start + d, -1),
                     STONE_PALETTE)

        # Raised stone plinth (dy=0 layer the hall sits on)
        fill_palette(*self.w(-hw - 1, fwd_start,     0),
                     *self.w( hw + 1, fwd_start + d, 0),
                     STONE_PALETTE)

        # Wide front stairs: 2 steps leading up to plinth (5 blocks wide, centred)
        for step in range(2):
            for dx in range(-2, 3):
                bx, by, bz = self.w(dx, fwd_start - 1 - step, -step)
                place(bx, by, bz, rand_stone())

        # Corner pillars: red concrete, full wall height
        for side in (-hw, hw):
            for fwd in (fwd_start, fwd_start + d):
                for dy in range(1, h + 1):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, PILLAR_BLOCK)

        # All four walls
        for dy in range(1, h):
            for side in range(-hw, hw + 1):
                bx, by, bz = self.w(side, fwd_start, dy)
                if abs(side) <= 1 and 1 <= dy <= h - 3:
                    place(bx, by, bz, AIR)
                else:
                    place(bx, by, bz, self._wall_mat(dy, h))
                bx, by, bz = self.w(side, fwd_start + d, dy)
                place(bx, by, bz, self._wall_mat(dy, h))
            for fwd in range(fwd_start + 1, fwd_start + d):
                for side in (-hw, hw):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, self._wall_mat(dy, h))

        # Red crimson fence railing across front plinth edge
        for dx in range(-hw, hw + 1):
            if abs(dx) > 1:
                bx, by, bz = self.w(dx, fwd_start - 1, 1)
                place(bx, by, bz, RAILING_BLOCK)
        for fwd in range(fwd_start - 1, fwd_start + 1):
            for side in (-hw, hw):
                bx, by, bz = self.w(side, fwd, 1)
                place(bx, by, bz, RAILING_BLOCK)

        # Interior: clear air + stone floor
        fill(*self.w(-hw + 1, fwd_start + 1, 1),
             *self.w( hw - 1, fwd_start + d - 1, h),
             AIR)
        fill_palette(*self.w(-hw + 1, fwd_start + 1, 0),
                     *self.w( hw - 1, fwd_start + d - 1, 0),
                     WOOD_PALETTE)

        # Shoji glass pane windows in the white middle band
        for fwd in range(fwd_start + 1, fwd_start + d):
            for side in (-hw, hw):
                for dy in range(2, h - 1):
                    if fwd % 2 == 0:
                        bx, by, bz = self.w(side, fwd, dy)
                        place(bx, by, bz, Block("glass_pane"))

        # Red eave beam ring at wall top
        eave_y = h + 1
        for dx in range(-hw - 1, hw + 2):
            bx, by, bz = self.w(dx, fwd_start, eave_y)
            place(bx, by, bz, BEAM_BLOCK)
            bx, by, bz = self.w(dx, fwd_start + d, eave_y)
            place(bx, by, bz, BEAM_BLOCK)
        for fwd in range(fwd_start, fwd_start + d + 1):
            bx, by, bz = self.w(-hw - 1, fwd, eave_y)
            place(bx, by, bz, BEAM_BLOCK_Z)
            bx, by, bz = self.w( hw + 1, fwd, eave_y)
            place(bx, by, bz, BEAM_BLOCK_Z)

        self._build_roof(hw, fwd_start, d, h)
        self._build_altar(hw, fwd_start, d, h)

    def _wall_mat(self, dy, h):
        if dy == 1 or dy >= h - 1:
            return WALL_TRIM
        return WALL_BLOCK

    def _build_roof(self, hw, fwd_start, d, h):
        """
        True pyramid roof: every rise step shrinks BOTH the left/right span
        AND the front/back span by 1, so all four sides slope inward at the
        same rate and converge to a single peak block.

        Base layer starts 'overhang' blocks wider/deeper than the hall walls.
        Body = warped_planks; outer eave edge = oxidised copper slabs.
        """
        eave_y   = h + 1
        overhang = 2

        # Half-depth of hall (distance from centre to front/back wall)
        hd = d // 2

        # The pyramid must converge — max_rise is whichever half-dimension
        # is larger so the smaller dimension reaches 0 first and we stop.
        max_rise = hw + overhang   # left/right span starts at hw+overhang, hits 0

        # Centre of hall in the forward direction (local coords)
        fwd_centre = fwd_start + hd

        for rise in range(max_rise + 1):
            span_x = hw + overhang - rise          # half-width remaining
            span_z = hd + overhang - rise          # half-depth remaining
            if span_x < 0 and span_z < 0:
                break
            span_x = max(span_x, 0)
            span_z = max(span_z, 0)
            y = eave_y + rise

            fwd_lo = fwd_centre - span_z
            fwd_hi = fwd_centre + span_z

            # Solid warped plank fill for this layer
            for dx in range(-span_x, span_x + 1):
                for fwd in range(fwd_lo, fwd_hi + 1):
                    bx, by, bz = self.w(dx, fwd, y)
                    place(bx, by, bz, ROOF_BLOCK)

            # Copper slab overhang on all four outer edges (skip base layer)
            if rise > 0:
                for fwd in range(fwd_lo, fwd_hi + 1):
                    bx, by, bz = self.w(-span_x - 1, fwd, y)
                    place(bx, by, bz, ROOF_SLAB_B)
                    bx, by, bz = self.w( span_x + 1, fwd, y)
                    place(bx, by, bz, ROOF_SLAB_B)
                for dx in range(-span_x, span_x + 1):
                    bx, by, bz = self.w(dx, fwd_lo - 1, y)
                    place(bx, by, bz, ROOF_SLAB_B)
                    bx, by, bz = self.w(dx, fwd_hi + 1, y)
                    place(bx, by, bz, ROOF_SLAB_B)

        # Single peak block + lightning rod finial
        peak_y = eave_y + max_rise
        bx, by, bz = self.w(0, fwd_centre, peak_y + 1)
        place(bx, by, bz, Block("lightning_rod"))

    def _build_altar(self, hw, fwd_start, d, h):
        altar_fwd = fwd_start + d - 2
        fill_palette(*self.w(-2, altar_fwd,   1),
                     *self.w( 2, altar_fwd+1, 1), STONE_PALETTE)
        fill_palette(*self.w(-1, altar_fwd,   2),
                     *self.w( 1, altar_fwd+1, 2), STONE_PALETTE)
        bx, by, bz = self.w(0, altar_fwd, 3)
        place(bx, by, bz, Block("chiseled_stone_bricks"))
        for side in (-2, 2):
            bx, by, bz = self.w(side, altar_fwd, 2)
            place(bx, by, bz, Block("candle", {"candles": "1", "lit": "true"}))
        for dx in range(-2, 3):
            bx, by, bz = self.w(dx, altar_fwd, 0)
            place(bx, by, bz, GLOWSTONE)
        if self.has_offering:
            bx, by, bz = self.w(0, altar_fwd - 2, 1)
            place(bx, by, bz, Block("chest", {"facing": opposite(self.facing)}))
        # Roof underside is at h (eave beam at h+1), so anchor chain there.
        # Two chain blocks so the lantern hangs visibly below the ceiling.
        ceil_y = h
        for fwd_off in range(fwd_start + 2, fwd_start + d - 1, 4):
            bx, by, bz = self.w(0, fwd_off, ceil_y)
            place(bx, by, bz, CHAIN)
            bx, by, bz = self.w(0, fwd_off, ceil_y - 1)
            place(bx, by, bz, CHAIN)
            bx, by, bz = self.w(0, fwd_off, ceil_y - 2)
            place(bx, by, bz, HANGING_LANTERN)

    # -----------------------------------------------------------------------
    # Haiden — offering / prayer hall in front of the honden
    # -----------------------------------------------------------------------

    def build_haiden(self):
        """
        The haiden sits directly in front of the honden, separated by a
        short gap, and faces the same direction.  It is wider and more open
        than the honden: the front face is entirely open (no wall), the side
        walls are only knee-height railings, and a thick shimenawa rope
        (chain + bell) hangs from the ceiling centre so worshippers can ring
        it while praying.

        Layout (local coords, dz < 0 = in front of honden):
          fwd 0          = honden front wall
          fwd -gap       = haiden back wall
          fwd -gap-hd_d  = haiden front (open)

        The haiden shares the same red/white aesthetic: red concrete pillars
        at corners, white concrete side walls (low, 2 blocks), red eave beam,
        warped plank roof (flat single layer), copper slab overhang.
        """
        hd_hw     = self.hd_w // 2
        hd_h      = self.hd_h
        fwd_front = self.haiden_fwd_front    # entrance face (open)
        fwd_back  = self.haiden_fwd_back     # back wall (faces honden)

        # --- Stone plinth ---
        fill_palette(*self.w(-hd_hw - 1, fwd_front,  0),
                     *self.w( hd_hw + 1, fwd_back,   0),
                     STONE_PALETTE)

        # --- Front stairs (open face — 3 steps, full width) ---
        for step in range(3):
            for dx in range(-hd_hw, hd_hw + 1):
                bx, by, bz = self.w(dx, fwd_front - step, -step)
                place(bx, by, bz, rand_stone())

        # --- Corner pillars ---
        for side in (-hd_hw, hd_hw):
            for fwd in (fwd_front, fwd_back):
                for dy in range(1, hd_h + 1):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, PILLAR_BLOCK)

        # --- Back wall (solid, faces honden) ---
        for dy in range(1, hd_h):
            for dx in range(-hd_hw, hd_hw + 1):
                bx, by, bz = self.w(dx, fwd_back, dy)
                place(bx, by, bz, self._wall_mat(dy, hd_h))

        # --- Side walls: low railing only (3 blocks tall, open above) ---
        for fwd in range(fwd_front + 1, fwd_back):
            for dy in range(1, 3):
                for side in (-hd_hw, hd_hw):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, self._wall_mat(dy, hd_h))
            # Red crimson fence on top of the low wall as railing
            for side in (-hd_hw, hd_hw):
                bx, by, bz = self.w(side, fwd, 3)
                place(bx, by, bz, RAILING_BLOCK)

        # --- Front face: open — only corner pillar and a fence railing ---
        for dx in range(-hd_hw, hd_hw + 1):
            if abs(dx) > 1:
                bx, by, bz = self.w(dx, fwd_front, 1)
                place(bx, by, bz, RAILING_BLOCK)

        # --- Interior floor ---
        fill_palette(*self.w(-hd_hw + 1, fwd_front + 1, 0),
                     *self.w( hd_hw - 1, fwd_back  - 1, 0),
                     WOOD_PALETTE)

        # --- Eave beam ring ---
        eave_y = hd_h + 1
        for dx in range(-hd_hw - 1, hd_hw + 2):
            bx, by, bz = self.w(dx, fwd_front, eave_y)
            place(bx, by, bz, BEAM_BLOCK)
            bx, by, bz = self.w(dx, fwd_back, eave_y)
            place(bx, by, bz, BEAM_BLOCK)
        for fwd in range(fwd_front, fwd_back + 1):
            bx, by, bz = self.w(-hd_hw - 1, fwd, eave_y)
            place(bx, by, bz, BEAM_BLOCK_Z)
            bx, by, bz = self.w( hd_hw + 1, fwd, eave_y)
            place(bx, by, bz, BEAM_BLOCK_Z)

        # --- Flat warped plank roof with copper slab overhang ---
        overhang = 2
        for dx in range(-hd_hw - overhang, hd_hw + overhang + 1):
            for fwd in range(fwd_front - overhang, fwd_back + overhang + 1):
                bx, by, bz = self.w(dx, fwd, eave_y)
                place(bx, by, bz, ROOF_BLOCK)
        # Copper slab overhang on all four edges
        for fwd in range(fwd_front - overhang, fwd_back + overhang + 1):
            bx, by, bz = self.w(-hd_hw - overhang - 1, fwd, eave_y)
            place(bx, by, bz, ROOF_SLAB_B)
            bx, by, bz = self.w( hd_hw + overhang + 1, fwd, eave_y)
            place(bx, by, bz, ROOF_SLAB_B)
        for dx in range(-hd_hw - overhang, hd_hw + overhang + 1):
            bx, by, bz = self.w(dx, fwd_front - overhang - 1, eave_y)
            place(bx, by, bz, ROOF_SLAB_B)
            bx, by, bz = self.w(dx, fwd_back  + overhang + 1, eave_y)
            place(bx, by, bz, ROOF_SLAB_B)

        # --- Shimenawa: chain + bell hanging from ceiling centre ---
        centre_fwd = (fwd_front + fwd_back) // 2
        rope_y     = eave_y - 1
        for drop in range(3):
            bx, by, bz = self.w(0, centre_fwd, rope_y - drop)
            place(bx, by, bz, CHAIN)
        # Bell block at the bottom of the rope
        bx, by, bz = self.w(0, centre_fwd, rope_y - 3)
        place(bx, by, bz, Block("bell", {"attachment": "ceiling",
                                          "facing":     "north"}))

        # --- Prayer lanterns flanking the bell ---
        for side in (-2, 2):
            bx, by, bz = self.w(side, centre_fwd, rope_y - 1)
            place(bx, by, bz, CHAIN)
            bx, by, bz = self.w(side, centre_fwd, rope_y - 2)
            place(bx, by, bz, HANGING_LANTERN)

        # --- Offering table in front of the back wall ---
        for dx in range(-2, 3):
            bx, by, bz = self.w(dx, fwd_back - 1, 1)
            place(bx, by, bz, rand_stone())
        # Candles on the table
        for side in (-2, 0, 2):
            bx, by, bz = self.w(side, fwd_back - 1, 2)
            place(bx, by, bz, Block("candle", {"candles": "1", "lit": "true"}))

    def build(self):
        print(f"[INFO] Shrine: facing={self.facing}, scale={self.scale}, "
              f"hall={self.hall_w}x{self.hall_d}x{self.hall_h}, "
              f"torii={self.torii_count}")

        # Torii gates spread evenly along the negative-fwd approach path
        # so the sequence is: torii(s) → haiden entrance (dz=0) → haiden → honden
        approach_step = self.path_len // (self.torii_count + 1)
        for k in range(self.torii_count):
            fwd_pos = -(self.path_len - approach_step * (k + 1))
            gate_w  = 5 + RNG.randint(0, 2) * 2
            gate_h  = 8 + RNG.randint(0, 2)
            self.build_torii(fwd_pos, gate_w=gate_w, gate_h=gate_h)

        self.build_path()
        if self.has_lanterns:
            self.build_lanterns()
        if self.has_fence:
            self.build_fence()
        self.build_honden()
        self.build_haiden()
        print("[INFO] Shrine complete.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    scale  = RNG.randint(1, 3)
    facing = RNG.choice(ORIENTATIONS)

    # Footprint must cover: path_len approach + haiden + gap + honden
    # path_len = 20+scale*4, haiden_d = 7+scale, gap=4, honden_d = 9+scale*2
    # total depth ≈ path_len + haiden_d + 4 + honden_d + 6 margin
    est_d = (20 + scale * 4) + (7 + scale) + 4 + (9 + scale * 2) + 10
    # width must cover honden 
    est_w = 15 + scale * 4
    if facing in ("east", "west"):
        fp_w, fp_d = est_d, est_w
    else:
        fp_w, fp_d = est_w, est_d
    fp_w = min(fp_w, BAW - 4)
    fp_d = min(fp_d, BAD - 4)

    print(f"[INFO] Scanning build area ({BAW}x{BAD}), footprint {fp_w}x{fp_d}, "
          f"facing={facing}, scale={scale}")

    best_lx, best_lz, q_grid, f_grid, d_grid = scan_build_site(fp_w, fp_d, stride=2)
    save_terrain_plots(q_grid, f_grid, d_grid, best_lx, best_lz, fp_w, fp_d, stride=2)

    site_heights = [get_height(best_lx+i, best_lz+j)
                    for i in range(fp_w) for j in range(fp_d)]
    target_y = int(np.median(site_heights))

    world_x0 = BAX + best_lx
    world_z0 = BAZ + best_lz
    print(f"[INFO] Site world=({world_x0},{world_z0}), target_y={target_y}")
    print("[INFO] Levelling terrain...")
    level_ground(world_x0, world_z0, fp_w, fp_d, target_y)

    # The shrine origin (dz=0) is the haiden entrance face.
    # path_len blocks extend in the NEGATIVE-dz direction (torii approach).
    # So we place the origin path_len + margin from the near edge of the footprint,
    # and centre on x (width axis).
    path_len_est = 20 + scale * 4
    margin       = 4

    if facing == "south":
        # forward = +z, near edge = world_z0, origin offset from near edge
        cx = world_x0 + fp_w // 2
        cz = world_z0 + path_len_est + margin
    elif facing == "north":
        # forward = -z, near edge = world_z0 + fp_d
        cx = world_x0 + fp_w // 2
        cz = world_z0 + fp_d - path_len_est - margin
    elif facing == "east":
        # forward = +x
        cx = world_x0 + path_len_est + margin
        cz = world_z0 + fp_d // 2
    else:  # west
        # forward = -x
        cx = world_x0 + fp_w - path_len_est - margin
        cz = world_z0 + fp_d // 2

    ShrineBuilder(cx, target_y, cz, facing=facing, scale=scale).build()
    print("[INFO] Done. See terrain_evaluation.png for heatmaps.")

if __name__ == "__main__":
    main()