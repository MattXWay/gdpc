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

width = randint(35, 55)
height = randint(30, 50)
depth  = randint(40, 60)

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
                    if(i==int((width/2))):
                        placeCuboid(editor, (x + i - 3, y+1, z + j), (x + i + 3 , y+3, z + j), Block("Air"))
                        placeCuboid(editor, (x + i - 1, y+4, z + j), (x + i - 2, y+4, z + j), Block("oak_leaves"))
                        print("making window")
                        

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

staircaseVector = randint(5,7)

stairPaletteFirst = [
    Block("polished_diorite_stairs", {"facing": "north"}),
    Block("stone_brick_stairs", {"facing": "north"}),
    Block("mossy_stone_brick_stairs", {"facing": "north"}),
]

stairPaletteSecond = [
    Block("polished_diorite_stairs", {"facing": "east"}),
    Block("stone_brick_stairs", {"facing": "east"}),
    Block("mossy_stone_brick_stairs", {"facing": "east"}),
]

def buildStructureStairs():
    for i in range(0, staircaseVector):
        # first we place the stairs that connect to the ground
        placeCuboid(editor, (x+1,y+1+i,z+1+(staircaseVector*2)-i), (x+1+staircaseVector, y+1+i, z+1+(staircaseVector*2)-i), stairPaletteFirst)
        # add here another cuboid, with solid blocks, so that it's not just a floating staircase
        placeCuboid(editor, (x+1,y+1+i,z+(staircaseVector*2)-i), (x+1+staircaseVector, y+1+i, z+(staircaseVector*2)-i), blockPalette)

        #and then, we place the other stairs going to the actual second floor.
        placeCuboid(editor, (x+2+staircaseVector+i, y+1+staircaseVector+i, z+1+staircaseVector), (x+2+staircaseVector+i,y+1+staircaseVector+i, z+1), stairPaletteSecond)
        #and then, the connecting solid blocks
        placeCuboid(editor, (x+3+staircaseVector+i, y+1+staircaseVector+i, z+1+staircaseVector), (x+3+staircaseVector+i,y+1+staircaseVector+i, z+1), blockPalette)


        # now, we place the "intermediate" platform
        if(i == staircaseVector-1):
            placeCuboid(editor, (x+1, y+1+i, z + staircaseVector -i), (x+1+staircaseVector, y+1+i, z+1+staircaseVector), blockPalette)
            

def buildStructureFloor():
    floorsize = randint(width//2, width//4)
    placeCuboid(editor, (x+1+(staircaseVector*2),y,z+1+(staircaseVector*2)), (x+1+staircaseVector+floorsize,y+staircaseVector*2,z+1+(staircaseVector*2)+floorsize), blockPalette)

buildStructurePerimeter()
buildStructureRoof()
cleanInterior()
buildStructureStairs()
buildStructureFloor()
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
