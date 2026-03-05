from random import randint, choice
from gdpc import Editor, Block
from gdpc.geometry import placeCuboid, placeCuboidHollow

editor = Editor(buffering=True)

buildArea = editor.getBuildArea()

# Load world slice of the build area
editor.loadWorldSlice(cache=True)

# Get heightmap
heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

x = buildArea.offset.x + 1
z = buildArea.offset.z + 1

y = heightmap[3,3] - 1

width = randint(20, 25)
height = randint(18, 20)
depth  = randint(20, 25)

# Random floor palette
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


# this places the top and bottom edges, using placeblock to get random block at each thing.
def buildStructurePerimeter():
    # floor first
    placeCuboid(editor, (x,y,z), (x+width-1, y, z+depth-1), blockPalette)
    # then raise the walls 
    for i in range(0, width):
        for j in range(0, depth):
            for h in range(0, height-1):
                if((i == 0) or (i==width-1)):
                    editor.placeBlock((x + i, y + h, z + j), blockPalette)
                if((j == 0)) or (j == depth-1):
                    editor.placeBlock((x + i, y + h, z + j), blockPalette)

roofWidthOffset = randint(2, 10)
roofDepthOffset = randint(0, 10)

roofWidth = width + roofWidthOffset
roofDepth = depth + roofDepthOffset

def buildStructureRoof():
    for i in range(0, roofWidth):
        for j in range(0, roofDepth):
            editor.placeBlock((x-(roofWidthOffset//2) + i, y+height-1, z-(roofDepthOffset//2) + j), roofPalette)
            
def cleanInterior():
    placeCuboid(editor, (x+1, y+1, z+1), (x+width-2, y+height-2, z+depth-2), Block("air"))

staircaseWidth = randint(3,5)
staircaseVector = randint(5,7)

stairPalette = [
    Block("polished_diorite_stairs", {"facing": "north"}),
    Block("stone_brick_stairs", {"facing": "north"}),
    Block("mossy_stone_brick_stairs", {"facing": "north"}),
    Block("smooth_quartz_stairs", {"facing": "north"}),
]

def buildStructureStairs():
    for i in range(0, staircaseVector):
        placeCuboid(editor, (x+1+staircaseWidth,y+1+i,z+1+staircaseVector-i), (x+1, y+1+i, z+1+staircaseVector+i), stairPalette)
        # add here another cuboid, with solid blokcs, so that it's not just a floating staircase


buildStructurePerimeter()
buildStructureRoof()
cleanInterior()
buildStructureStairs()
            #placeCuboidHollow(editor, (x, y, z), (x+width, y+height, z+depth), blockPalette)
        


    

# Build roof: loop through distance from the middle
# for dx in range(1, 4):
#     yy = y + height + 2 - dx

#     # Build row of stairs blocks
#     leftBlock  = Block("oak_stairs", {"facing": "east"})
#     rightBlock = Block("oak_stairs", {"facing": "west"})
#     placeCuboid(editor, (x+2-dx, yy, z-1), (x+2-dx, yy, z+depth+1), leftBlock)
#     placeCuboid(editor, (x+2+dx, yy, z-1), (x+2+dx, yy, z+depth+1), rightBlock)

# build the top row of the roof
# yy = y + height + 1
# placeCuboid(editor, (x+2, yy, z-1), (x+2, yy, z+depth+1), Block("oak_planks"))
