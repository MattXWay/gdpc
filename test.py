"""
shinto_shrine.py
================
MGAIA Retake Assignment 1 — Procedural Content Generation
Leiden University, 2026

Procedurally generates a Shinto-inspired shrine complex in a Minecraft
world using the GDPC library.  The script:

  1. Analyses the build-area heightmap to find the flattest, driest
     sub-region that fits the shrine footprint.
  2. Levels and back-fills the chosen plot so the structure sits on
     natural-looking ground, not in a hole or on stilts.
  3. Randomly varies orientation (N/S/E/W facing), overall scale,
     material weathering, decoration density, and the presence of
     optional elements (stone lanterns, offering box, torii approach
     count, fence circuit).
  4. Builds the complex in layers: torii gate(s) → stone path →
     shrine fencing → main hall (honden) → interior altar → lanterns.

Run with:
    python shinto_shrine.py

Requirements: gdpc (install from GitHub), numpy, matplotlib
"""

import sys
import math
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless – saves PNGs without a display
import matplotlib.pyplot as plt

from gdpc import Editor, Block
from gdpc.geometry import placeCuboid

# ---------------------------------------------------------------------------
# Editor setup
# ---------------------------------------------------------------------------
editor = Editor(buffering=True)
buildArea = editor.getBuildArea()
editor.loadWorldSlice(cache=True)

BAX = buildArea.offset.x
BAZ = buildArea.offset.z
BAW = buildArea.size.x        # width  (x direction)
BAD = buildArea.size.z        # depth  (z direction)

heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
# water surface: use OCEAN_FLOOR to detect water bodies
ocean_floor = editor.worldSlice.heightmaps["OCEAN_FLOOR"]

RNG = random.Random()          # seeded from system entropy each run

# ---------------------------------------------------------------------------
# Terrain analysis helpers
# ---------------------------------------------------------------------------

def get_height(local_x: int, local_z: int) -> int:
    """Return the surface height at a local (build-area) coordinate."""
    lx = max(0, min(local_x, BAW - 1))
    lz = max(0, min(local_z, BAD - 1))
    return int(heightmap[lx, lz])


def has_water(local_x: int, local_z: int) -> bool:
    """Return True when the column contains water (ocean floor < surface)."""
    lx = max(0, min(local_x, BAW - 1))
    lz = max(0, min(local_z, BAD - 1))
    return int(ocean_floor[lx, lz]) < int(heightmap[lx, lz])


def terrain_flatness(lx0: int, lz0: int, w: int, d: int) -> float:
    """
    Flatness score for a rectangle [lx0, lx0+w) x [lz0, lz0+d).
    Returns 1/(1 + std_dev) so higher = flatter.
    """
    hs = [get_height(lx0 + i, lz0 + j)
          for i in range(w) for j in range(d)]
    return 1.0 / (1.0 + float(np.std(hs)))


def terrain_dryness(lx0: int, lz0: int, w: int, d: int) -> float:
    """
    Dryness score: fraction of columns that contain no water.
    1.0 = fully dry, 0.0 = fully wet.
    """
    total = w * d
    wet = sum(
        1 for i in range(w) for j in range(d)
        if has_water(lx0 + i, lz0 + j)
    )
    return 1.0 - wet / total


def scan_build_site(footprint_w: int, footprint_d: int,
                    stride: int = 3) -> tuple:
    """
    Slide a window over the build area and score every candidate origin.
    Returns:
        best_lx, best_lz   – local origin of the best site
        quality_grid       – 2-D numpy array of combined quality scores
        flatness_grid      – 2-D numpy array of flatness scores
        dryness_grid       – 2-D numpy array of dryness scores
    """
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
            # Weighted combination: flatness matters more
            q = 0.65 * f + 0.35 * d
            flatness_grid[gi, gj] = f
            dryness_grid[gi, gj]  = d
            quality_grid[gi, gj]  = q
            if q > best_score:
                best_score = q
                best_lx, best_lz = lx, lz

    return best_lx, best_lz, quality_grid, flatness_grid, dryness_grid


def save_terrain_plots(quality_grid, flatness_grid, dryness_grid,
                       best_lx, best_lz, footprint_w, footprint_d,
                       stride: int = 3):
    """Save three matplotlib figures that visualise terrain evaluation."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    grids   = [flatness_grid, dryness_grid, quality_grid]
    titles  = ["Flatness score", "Dryness score", "Combined quality $Q_{total}$"]
    cmaps   = ["YlOrRd", "Blues_r", "hot"]

    for ax, grid, title, cmap in zip(axes, grids, titles, cmaps):
        gw, gd = grid.shape
        extent = [0, gw * stride, 0, gd * stride]
        im = ax.imshow(grid.T, origin="upper", cmap=cmap,
                       extent=extent, aspect="auto")
        plt.colorbar(im, ax=ax)
        ax.set_title(title)
        ax.set_xlabel("x (build area)")
        ax.set_ylabel("z (build area)")

    # Mark chosen site on the quality plot
    ax = axes[2]
    rect = plt.Rectangle(
        (best_lx, best_lz), footprint_w, footprint_d,
        linewidth=2, edgecolor="cyan", facecolor="none", label="Chosen site"
    )
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

WOOD_PALETTE_RED = [
    Block("stripped_spruce_wood"),
]

PILLAR_BLOCK = Block("stripped_spruce_log")
BEAM_BLOCK   = Block("dark_oak_log", {"axis": "x"})
BEAM_BLOCK_Z = Block("dark_oak_log", {"axis": "z"})
ROOF_BLOCK   = Block("dark_oak_slab", {"type": "bottom"})
ROOF_TOP     = Block("dark_oak_slab", {"type": "top"})
ROOF_STAIR_W = lambda f: Block("dark_oak_stairs", {"facing": f, "half": "bottom"})
LANTERN      = Block("lantern", {"hanging": "false"})
HANGING_LANTERN = Block("lantern", {"hanging": "true"})
GRAVEL       = Block("gravel")
SAND         = Block("sand")
COARSE_DIRT  = Block("coarse_dirt")
AIR          = Block("air")
WATER        = Block("water")
GLOWSTONE    = Block("glowstone")
RED_CONCRETE = Block("red_concrete")
WHITE_WOOL   = Block("white_wool")
STONE_SLAB   = Block("stone_brick_slab", {"type": "bottom"})
CHAIN        = Block("chain")


def rand_stone():
    return RNG.choice(STONE_PALETTE)


# ---------------------------------------------------------------------------
# Low-level placement helpers
# ---------------------------------------------------------------------------

def place(wx: int, wy: int, wz: int, block: Block):
    """Place a single block at world coordinates."""
    editor.placeBlock((wx, wy, wz), block)


def fill(wx0, wy0, wz0, wx1, wy1, wz1, block: Block):
    """Fill a cuboid with a single block type."""
    placeCuboid(editor, (wx0, wy0, wz0), (wx1, wy1, wz1), block)


def fill_palette(wx0, wy0, wz0, wx1, wy1, wz1, palette: list):
    """Fill a cuboid sampling randomly from a palette."""
    for gx in range(min(wx0, wx1), max(wx0, wx1) + 1):
        for gy in range(min(wy0, wy1), max(wy0, wy1) + 1):
            for gz in range(min(wz0, wz1), max(wz0, wz1) + 1):
                editor.placeBlock((gx, gy, gz), RNG.choice(palette))


# ---------------------------------------------------------------------------
# Terrain levelling
# ---------------------------------------------------------------------------

def level_ground(wx0: int, wz0: int, w: int, d: int, target_y: int):
    """
    Flatten the footprint to target_y.
    - Above target_y: remove blocks (air).
    - Below target_y: fill with stone to avoid floating structures.
    """
    for ix in range(w):
        for iz in range(d):
            col_x = wx0 + ix
            col_z = wz0 + iz
            surf = get_height(col_x - BAX, col_z - BAZ)
            if surf > target_y:
                # Carve downward
                for ky in range(target_y, surf + 2):
                    place(col_x, ky, col_z, AIR)
            elif surf < target_y:
                # Fill upward with stone/dirt blend
                for ky in range(surf, target_y):
                    place(col_x, ky, col_z, rand_stone())
            # Place a solid top layer (foundation)
            place(col_x, target_y - 1, col_z, rand_stone())


# ---------------------------------------------------------------------------
# Orientation helpers
# ---------------------------------------------------------------------------
# Facing strings and rotation matrices for four cardinal orientations.
# "facing" is the direction the shrine ENTRANCE faces.

ORIENTATIONS = ["north", "south", "east", "west"]

def rotate_offset(dx: int, dz: int, facing: str) -> tuple:
    """
    Rotate a local (dx, dz) offset so that +z is "forward" (into the
    building) and +x is "right" when facing the given direction.

    Local convention:
        +dz = forward (into shrine from torii)
        +dx = right
    """
    if facing == "south":   return  dx,  dz
    if facing == "north":   return -dx, -dz
    if facing == "east":    return  dz, -dx
    if facing == "west":    return -dz,  dx
    return dx, dz


def opposite(facing: str) -> str:
    return {"north": "south", "south": "north",
            "east": "west",   "west": "east"}[facing]


def left_of(facing: str) -> str:
    return {"north": "west", "south": "east",
            "east": "north", "west": "south"}[facing]


def right_of(facing: str) -> str:
    return {"north": "east", "south": "west",
            "east": "south", "west": "north"}[facing]


# ---------------------------------------------------------------------------
# Shrine components
# ---------------------------------------------------------------------------

class ShrineBuilder:
    """
    Builds a Shinto shrine complex.

    Parameters
    ----------
    cx, cy, cz : int
        World coordinates of the shrine centre (front of honden, ground level).
    facing : str
        Cardinal direction the entrance faces.
    scale : int
        Base scale (1–3).  Controls width / depth / height offsets.
    """

    def __init__(self, cx: int, cy: int, cz: int,
                 facing: str, scale: int):
        self.cx = cx
        self.cy = cy          # ground surface y (top of foundation)
        self.cz = cz
        self.facing = facing
        self.scale = scale    # 1, 2, or 3

        # Derived dimensions (all in blocks)
        s = scale
        self.hall_w  = 7 + s * 2          # honden interior width
        self.hall_d  = 9 + s * 2          # honden depth (front to back)
        self.hall_h  = 7 + s              # wall height (floor to eave)
        self.path_len = 12 + s * 4        # length of stone path before honden
        self.torii_count = RNG.randint(1, 2 + s)  # how many torii on the path

        # Variation flags
        self.has_lanterns = RNG.random() < 0.85
        self.has_fence    = RNG.random() < 0.70
        self.has_offering = RNG.random() < 0.60
        self.lantern_spacing = RNG.randint(3, 6)

    # ---- coordinate helper ------------------------------------------------

    def w(self, dx: int, dz: int, dy: int = 0):
        """Convert local (dx, dz, dy) to world coords using self.facing."""
        rdx, rdz = rotate_offset(dx, dz, self.facing)
        return self.cx + rdx, self.cy + dy, self.cz + rdz

    # ---- torii gate -------------------------------------------------------

    def build_torii(self, fwd_offset: int, gate_w: int = 5, gate_h: int = 6):
        """
        Build a torii gate at fwd_offset blocks forward of (cx, cz).
        gate_w : width of the gate opening (including pillars)
        gate_h : height from ground to top of kasagi (top beam)
        """
        half = gate_w // 2
        y0   = self.cy
        # Two pillars
        for side in (-half, half):
            for dy in range(gate_h):
                bx, by, bz = self.w(side, fwd_offset, dy)
                place(bx, by, bz, RED_CONCRETE)

        # Nuki (lower cross-beam, 1 block below kasagi)
        for dx in range(-half - 1, half + 2):
            bx, by, bz = self.w(dx, fwd_offset, gate_h - 2)
            place(bx, by, bz, RED_CONCRETE)

        # Kasagi (upper curved beam) — slightly wider, one block higher
        for dx in range(-half - 1, half + 2):
            bx, by, bz = self.w(dx, fwd_offset, gate_h - 1)
            place(bx, by, bz, AIR)
            #we only want to place the left and right most blocks of the kasagi, so we can place the red concrete on the left and right most blocks
            if dx == -half - 1 or dx == half + 1:
                place(bx, by, bz, RED_CONCRETE)

        # Shimagi (top capping layer)
        for dx in range(-half - 2, half + 3):
            bx, by, bz = self.w(dx, fwd_offset, gate_h)
            place(bx, by, bz, RED_CONCRETE) 

        # Hanging lanterns under the kasagi
        for side in (-half + 1, half - 1):
            bx, by, bz = self.w(side, fwd_offset, gate_h - 3)
            place(bx, by, bz, CHAIN)
            bx2, by2, bz2 = self.w(side, fwd_offset, gate_h - 4)
            place(bx2, by2, bz2, HANGING_LANTERN)

    # ---- stone path -------------------------------------------------------

    def build_path(self):
        """Lay a gravel path from the first torii to the honden entrance."""
        path_w = 3
        for fwd in range(-1, self.path_len + 1):
            for side in range(-path_w // 2, path_w // 2 + 1):
                bx, by, bz = self.w(side, fwd, 0)
                place(bx, by - 1, bz, GRAVEL)
                place(bx, by,     bz, AIR)   # clear any leftover blocks

    # ---- stone lanterns ---------------------------------------------------

    def build_lanterns(self):
        """
        Place stone lanterns (chochin-style) along the path at
        self.lantern_spacing intervals.
        """
        spacing = self.lantern_spacing
        for fwd in range(spacing, self.path_len, spacing):
            for side in (-2, 2):
                base_x, base_y, base_z = self.w(side, fwd, 0)
                # Post
                place(base_x, base_y,     base_z, Block("stone_brick_wall"))
                place(base_x, base_y + 1, base_z, Block("stone_brick_wall"))
                # Cap slab
                place(base_x, base_y + 2, base_z, STONE_SLAB)
                # Light
                place(base_x, base_y + 3, base_z, LANTERN)

    # ---- perimeter fence --------------------------------------------------

    def build_fence(self):
        """
        Build a low stone-brick-wall fence around the honden,
        with a gate opening on the path side.
        """
        hw = self.hall_w // 2 + 2
        gate_half = 1

        # Front fence (entrance side), leave opening for path
        for side in range(-hw, hw + 1):
            if abs(side) > gate_half:
                bx, by, bz = self.w(side, 0, 0)
                place(bx, by,     bz, Block("stone_brick_wall"))

        # Back fence
        back = self.hall_d + 3
        for side in range(-hw, hw + 1):
            bx, by, bz = self.w(side, back, 0)
            place(bx, by, bz, Block("stone_brick_wall"))

        # Side fences
        for fwd in range(1, back):
            bx, by, bz = self.w(-hw, fwd, 0)
            place(bx, by, bz, Block("stone_brick_wall"))
            bx, by, bz = self.w( hw, fwd, 0)
            place(bx, by, bz, Block("stone_brick_wall"))

    # ---- main honden (hall) -----------------------------------------------

    def build_honden(self):
        """Build the main shrine hall (honden)."""
        hw  = self.hall_w // 2
        d   = self.hall_d
        h   = self.hall_h
        fwd_start = 2    # gap between fence/path and hall

        # --- Foundation platform ---
        fill_palette(
            *self.w(-hw - 1, fwd_start,       -1),
            *self.w( hw + 1, fwd_start + d,   -1),
            STONE_PALETTE
        )

        # --- Walls (hollow) ---
        # Front wall with entrance opening
        for dy in range(h):
            for side in range(-hw, hw + 1):
                bx, by, bz = self.w(side, fwd_start, dy)
                # Entrance opening (centre 3 wide, up to h-3 high)
                if abs(side) <= 1 and dy < h - 3:
                    place(bx, by, bz, AIR)
                else:
                    place(bx, by, bz, rand_stone())

        # Back wall
        for dy in range(h):
            for side in range(-hw, hw + 1):
                bx, by, bz = self.w(side, fwd_start + d, dy)
                place(bx, by, bz, rand_stone())

        # Side walls
        for fwd in range(fwd_start, fwd_start + d + 1):
            for dy in range(h):
                for side in (-hw, hw):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, rand_stone())

        # --- Corner pillars ---
        for side in (-hw, hw):
            for fwd in (fwd_start, fwd_start + d):
                for dy in range(h + 1):
                    bx, by, bz = self.w(side, fwd, dy)
                    place(bx, by, bz, PILLAR_BLOCK)

        # --- Interior: clean air + floor ---
        fill(
            *self.w(-hw + 1, fwd_start + 1, 0),
            *self.w( hw - 1, fwd_start + d - 1, h - 1),
            AIR
        )
        fill_palette(
            *self.w(-hw + 1, fwd_start + 1, -1),
            *self.w( hw - 1, fwd_start + d - 1, -1),
            STONE_PALETTE
        )

        # --- Windows: shoji-style glass panes on side walls ---
        win_height_lo = h // 3
        win_height_hi = (h * 2) // 3
        for fwd in range(fwd_start + 2, fwd_start + d - 1):
            for side in (-hw, hw):
                for dy in range(win_height_lo, win_height_hi):
                    if fwd % 2 == 0:   # only every other block for slits
                        bx, by, bz = self.w(side, fwd, dy)
                        place(bx, by, bz, Block("glass_pane"))

        # --- Eave beams along the top of walls ---
        for side in range(-hw - 1, hw + 2):
            bx, by, bz = self.w(side, fwd_start,     h)
            place(bx, by, bz, BEAM_BLOCK)
            bx, by, bz = self.w(side, fwd_start + d, h)
            place(bx, by, bz, BEAM_BLOCK)
        for fwd in range(fwd_start, fwd_start + d + 1):
            bx, by, bz = self.w(-hw - 1, fwd, h)
            place(bx, by, bz, BEAM_BLOCK_Z)
            bx, by, bz = self.w( hw + 1, fwd, h)
            place(bx, by, bz, BEAM_BLOCK_Z)

        # --- Roof ---
        self._build_roof(hw, fwd_start, d, h)

        # --- Interior altar ---
        self._build_altar(hw, fwd_start, d, h)

    def _build_roof(self, hw: int, fwd_start: int, d: int, h: int):
        """
        Build a simple hip-style roof with dark oak.
        The roof rises one block per step inward from each side,
        creating a tiered look reminiscent of a Japanese irimoya.
        """
        facing_in  = self.facing
        facing_opp = opposite(self.facing)

        max_rise = hw + 1
        for rise in range(max_rise + 1):
            span_x = hw + 1 - rise
            y_off  = h + rise

            for side in range(-span_x, span_x + 1):
                for fwd in range(fwd_start - 1, fwd_start + d + 2):
                    bx, by, bz = self.w(side, fwd, y_off)
                    place(bx, by, bz, ROOF_BLOCK if rise < max_rise else Block("dark_oak_slab", {"type": "bottom"}))

            # Slanted edge slabs on each rise layer
            for fwd in range(fwd_start - 1, fwd_start + d + 2):
                bx, by, bz = self.w(-span_x - 1, fwd, y_off - 1)
                place(bx, by, bz, ROOF_TOP)
                bx, by, bz = self.w( span_x + 1, fwd, y_off - 1)
                place(bx, by, bz, ROOF_TOP)

        # Ridge beam along the top
        ridge_y = h + max_rise
        for fwd in range(fwd_start - 1, fwd_start + d + 2):
            bx, by, bz = self.w(0, fwd, ridge_y + 1)
            place(bx, by, bz, Block("dark_oak_fence"))

        # Decorative finials (shachi) at ridge ends
        bx, by, bz = self.w(0, fwd_start - 1,     ridge_y + 2)
        place(bx, by, bz, Block("lightning_rod"))
        bx, by, bz = self.w(0, fwd_start + d + 1, ridge_y + 2)
        place(bx, by, bz, Block("lightning_rod"))

    def _build_altar(self, hw: int, fwd_start: int, d: int, h: int):
        """
        Build a simple altar (gohonzon) inside the honden at the far end.
        Contains an item frame on the back wall, candles, and an offering block.
        """
        altar_fwd = fwd_start + d - 2
        altar_mid = 0          # centre x

        # Altar dais (two-step platform)
        fill_palette(
            *self.w(-2, altar_fwd,     0),
            *self.w( 2, altar_fwd + 1, 0),
            STONE_PALETTE
        )
        fill_palette(
            *self.w(-1, altar_fwd,     1),
            *self.w( 1, altar_fwd + 1, 1),
            STONE_PALETTE
        )

        # Central shrine object (note block as "drum" / altar piece)
        bx, by, bz = self.w(0, altar_fwd, 2)
        place(bx, by, bz, Block("chiseled_stone_bricks"))

        # Candles on either side of altar
        for side in (-2, 2):
            bx, by, bz = self.w(side, altar_fwd, 1)
            place(bx, by, bz, Block("candle", {"candles": "1", "lit": "true"}))

        # Glowstone hidden under dais for ambient light
        for side in range(-2, 3):
            bx, by, bz = self.w(side, altar_fwd, -1)
            place(bx, by, bz, GLOWSTONE)

        # Offering box (chest) in front of altar
        if self.has_offering:
            offer_facing = opposite(self.facing)
            bx, by, bz = self.w(0, altar_fwd - 2, 0)
            place(bx, by, bz, Block("chest", {"facing": offer_facing}))

        # Ceiling lanterns
        ceil_y = self.hall_h - 1
        for fwd_off in range(fwd_start + 2, fwd_start + d - 1, 4):
            bx, by, bz = self.w(0, fwd_off, ceil_y)
            place(bx, by, bz, CHAIN)
            bx, by, bz = self.w(0, fwd_off, ceil_y - 1)
            place(bx, by, bz, HANGING_LANTERN)

    # ---- main build call --------------------------------------------------

    def build(self):
        print(f"[INFO] Building shrine: facing={self.facing}, scale={self.scale}, "
              f"hall={self.hall_w}x{self.hall_d}x{self.hall_h}, "
              f"torii={self.torii_count}, lanterns={self.has_lanterns}, "
              f"fence={self.has_fence}")

        # Torii gates along the approach path
        approach_step = self.path_len // (self.torii_count + 1)
        for k in range(self.torii_count):
            fwd_pos = approach_step * (k + 1) - self.path_len
            gate_w  = 5 + RNG.randint(0, 2) * 2
            gate_h  = 5 + RNG.randint(0, 2)
            self.build_torii(fwd_pos, gate_w=gate_w, gate_h=gate_h)

        self.build_path()

        if self.has_lanterns:
            self.build_lanterns()

        if self.has_fence:
            self.build_fence()

        self.build_honden()

        print("[INFO] Shrine complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # ---- Randomise scale and determine required footprint -----------------
    scale   = RNG.randint(1, 3)
    facing  = RNG.choice(ORIENTATIONS)

    # Estimate footprint needed for site-finding (conservative)
    est_w = 15 + scale * 4
    est_d = 30 + scale * 6

    # Align footprint to the facing direction
    if facing in ("east", "west"):
        fp_w, fp_d = est_d, est_w
    else:
        fp_w, fp_d = est_w, est_d

    fp_w = min(fp_w, BAW - 4)
    fp_d = min(fp_d, BAD - 4)

    print(f"[INFO] Scanning build area ({BAW}x{BAD}) for best site "
          f"(footprint {fp_w}x{fp_d}, facing={facing}, scale={scale})")

    # ---- Terrain analysis -------------------------------------------------
    best_lx, best_lz, q_grid, f_grid, d_grid = scan_build_site(fp_w, fp_d, stride=2)
    save_terrain_plots(q_grid, f_grid, d_grid, best_lx, best_lz, fp_w, fp_d, stride=2)

    # ---- Determine target ground height at the chosen site ----------------
    site_heights = [
        get_height(best_lx + i, best_lz + j)
        for i in range(fp_w) for j in range(fp_d)
    ]
    target_y = int(np.median(site_heights))   # median is robust to outliers

    print(f"[INFO] Best site local=({best_lx},{best_lz}), "
          f"world=({BAX+best_lx},{BAZ+best_lz}), target_y={target_y}")

    # ---- Level the terrain ------------------------------------------------
    world_x0 = BAX + best_lx
    world_z0 = BAZ + best_lz
    print("[INFO] Levelling terrain…")
    level_ground(world_x0, world_z0, fp_w, fp_d, target_y)

    # ---- Place shrine centre (cx, cz = centre of footprint) ---------------
    cx = world_x0 + fp_w // 2
    cz = world_z0 + fp_d // 2
    cy = target_y

    builder = ShrineBuilder(cx, cy, cz, facing=facing, scale=scale)
    builder.build()

    print("[INFO] Done. Check terrain_evaluation.png for the suitability heatmaps.")


if __name__ == "__main__":
    main()
