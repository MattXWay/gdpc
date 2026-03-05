# IMPORTS
from random import randint
from gdpc import Editor, Block
from gdpc.geometry import placeCuboid, placeCuboidHollow

# EDITOR  OBJECT
# we need this to be able to edit the world
editor = Editor(buffering=False)

# save build area in a variable so that we can use it to make stuff happen
buildArea = editor.getBuildArea()

# Load world slice of the build area
editor.loadWorldSlice(cache=True)

# Get heightmap
heightmap = editor.worldSlice._heightmaps["MOTION_BLOCKING_NO_LEAVES"]

# now use heightmap to find the ground; -1 is there to make it the ground (otherwise it's the NEXT value) 
y = heightmap[3,3]
x = buildArea.offset.x + 1
z = buildArea.offset.z + 1


# Build main shape
placeCuboidHollow(editor, (x, y, z), (x+4, y+4, z+4), Block("oak_planks"))
placeCuboid(editor, (x, y, z), (x+4, y, z+4), Block("cobblestone"))

# Build roof: loop through distance from the middle
for dx in range(1, 4):
    yy = y + 6 - dx

    # Build row of stairs blocks
    leftBlock  = Block("birch_stairs", {"facing": "east"})
    rightBlock = Block("birch_stairs", {"facing": "west"})
    placeCuboid(editor, (x+2-dx, yy, z-1), (x+2-dx, yy, z+5), leftBlock)
    placeCuboid(editor, (x+2+dx, yy, z-1), (x+2+dx, yy, z+5), rightBlock)

# build the top row of the roof
placeCuboid(editor, (x+2, y+5, z-1), (x+2, y+5, z+5), Block("spruce_planks"))
