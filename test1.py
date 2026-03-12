from random import randint, choice
from gdpc import Editor, Block
from gdpc.geometry import placeCuboid, placeCuboidHollow, placeRectOutline

editor = Editor(buffering=True)

buildArea = editor.getBuildArea()

#show boundary
placeRectOutline(editor, buildArea.toRect(), buildArea.offset.y, Block("red_concrete"))

# Load world slice of the build area
editor.loadWorldSlice(cache=True)

# Get heightmap
heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

x = buildArea.offset.x + 1
z = buildArea.offset.z + 1

y = heightmap[3,3]

height = randint(3, 7)
depth  = randint(3, 10)

# now we are going to be building a building that looks like the Slovak Radio building, which is a brutalist building in Bratislava, Slovakia. It has a very distinctive shape, with a wide top and a narrow base, like an upside down pyramid. and lots of windows. We will be building a non-simplified version of this building, using random blocks from the palette for the walls and windows.
if(randint(0,1) == 0):
    blockPalette = [
        Block("stone_bricks"),
        Block("cracked_stone_bricks"),
        Block("mossy_stone_bricks"),
        Block("chiseled_stone_bricks"),
    ]

    roofPalette = [
        Block("stone_bricks"),
        Block("mossy_stone_bricks"),
        Block("oak_leaves"),
        Block("air")
    ]
else:
    blockPalette = [
        Block("polished_andesite"),
        Block("andesite"),
        Block("cobbled_deepslate"),
        Block("cobbled_deepslate_slab"),
    ]

    roofPalette = [
        Block("polished_andesite"),
        Block("andesite"),
        Block("cobbled_deepslate"),
        Block("cobbled_deepslate_slab"),
        Block("air")
    ]

width = randint(35, 55)
height = randint(30, 50)
depth  = randint(40, 60)
# now to build the structure
for i in range(0, height):
    placeCuboid(editor, (x+i,y+i,z+i), (x+width-1-i, y+i, z+depth-1-i), blockPalette)
    # now we add windows, replacing some blocks with glass or wall blocks at random heights and positions on the walls
    for j in range(0, width):
        for k in range(0, depth):
            if(randint(0,10) < 2): # 20% chance to place a window block
                if((j == 0) or (j==width-1) or (k == 0) or (k == depth-1)):
                    editor.placeBlock((x + j, y + i, z + k), choice([Block("glass"), Block("air")]))

