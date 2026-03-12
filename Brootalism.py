from random import randint
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

statuePalette = (
    2*[Block("quartz_block")] + 
    2*[Block("polished_andesite"), Block("air")]
)

# this places the top and bottom edges, using placeblock to get random block at each thing.
def buildStructurePerimeter():
    # floor first
    placeCuboid(editor, (x,y,z), (x+width-1, y, z+depth-1), blockPalette)
    # then raise the walls 
    for i in range(0, width):
        for j in range(0, depth):
            for k in range(0, height-1):
                if((i == 0) or (i==width-1)):
                    editor.placeBlock((x + i, y + k, z + j), blockPalette)
                if((j == 0)) or (j == depth-1):
                    editor.placeBlock((x + i, y + k, z + j), blockPalette)

    # now we add windows, replacing some blocks with glass or wall blocks at random heights and positions on the walls
    for i in range(0, width):
        for j in range(0, depth):
            for k in range(0, height-1):
                if((i == 0) or (i==width-1) or (j == 0) or (j == depth-1)):
                    if(randint(0,100) < 5): # 5% chance to replace
                        if(randint(0,100) < 20): # 20% chance to place a window, otherwise put a brick wall to just add texture
                            editor.placeBlock((x + i, y + k, z + j), Block("glass_pane"))
                        else:
                            editor.placeBlock((x + i, y + k, z + j), Block("stone_brick_wall"))
    
    # now we add a archway entrance
    entranceWidth = randint(3, 5)
    entranceHeight = randint(4, 6)
    # placing on the west wall, in the middle 
    placeCuboid(editor, (x, y+1, z+(depth//2)-(entranceWidth//2)), (x, y+entranceHeight, z+(depth//2)+(entranceWidth//2)), Block("air"))
    # stairs on top of the entrance to make it look like an archway, using stone bricks stairs, and placing them in a way that they face towards the entrance (always east)
    for i in range(0, entranceWidth):
        editor.placeBlock((x-1, y+1+entranceHeight, z+(depth//2)-(entranceWidth//2)+i), Block("stone_brick_stairs", {"facing": "east"}))


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
            # and then the lights under this platform
            for j in range(0, staircaseVector, randint(1,3)):
                editor.placeBlock((x+1+j, y+1+i-1, z + staircaseVector -i), Block("pearlescent_froglight"))
                editor.placeBlock((x+1+j, y+1+i-1, z + 1+staircaseVector), Block("pearlescent_froglight"))
            
            
floorsize = randint((width//4), (width//2))

def buildStructureFloor():
    #print(floorsize)
    placeCuboid(editor, (x+2+(staircaseVector*2),y+(staircaseVector*2),z+1), (x+2+(staircaseVector*2)+floorsize,y+(staircaseVector*2),z+1+(staircaseVector*2)+floorsize), blockPalette)
    # END SPOT OF THE SECOND FLOOR:
    # (x+1+(staircaseVector*2)+floorsize,y+(staircaseVector*2),z+1+(staircaseVector*2)+floorsize)

    # now adding froglights under the second floor for some lighting
    for i in range(0, floorsize, randint(2,4)):
        for j in range(0, floorsize+staircaseVector):
            editor.placeBlock((x+2+(staircaseVector*2)+i,y+(staircaseVector*2)-1,z+1+(staircaseVector)+j), Block("pearlescent_froglight"))

    
        

def buildStatue():
    statueWidth = randint(3, floorsize//2)
    statueHeight = randint(10, staircaseVector*2)
    statueDepth = randint(3, floorsize//2)

    statueX = x + 2 + (staircaseVector*2) + (floorsize//2) - (statueWidth//2)
    statueY = y + 1 + (staircaseVector*2)
    statueZ = z + 1 + (staircaseVector*2) + (floorsize//2) - (statueDepth//2)

    # now to place blocks at the correct spot to make it look like a person
    for i in range(0, statueHeight):
        for j in range(0, statueWidth):
            for k in range(0, statueDepth):
                # place blocks for the body
                if(i < statueHeight//2):
                    editor.placeBlock((statueX + j, statueY + i, statueZ + k), statuePalette)
                # place blocks for the head
                elif(i < (statueHeight//2) + (statueHeight//4)):
                    if(j > 0 and j < statueWidth-1 and k > 0 and k < statueDepth-1):
                        editor.placeBlock((statueX + j, statueY + i, statueZ + k), statuePalette)
                # place blocks for the arms
                else:
                    if(j == 0 or j == statueWidth-1):
                        editor.placeBlock((statueX + j, statueY + i, statueZ + k), statuePalette)

def buildPillars():
    # add some random small, but chunky pillars in the interior for decoration, maybe with some vines hanging from them
    numPillars = randint(8, 16)
    

    for i in range(0, numPillars):
        pillarHeight = randint(5, staircaseVector*2)
        # prevent them from spawning on top of the stairs or the statue by adding a buffer around those as well
        pillarX = randint(x+2+(staircaseVector*2)+1, x+2+(staircaseVector*2)+floorsize-1)
        pillarZ = randint(z+1+(staircaseVector*2)+1, z+1+(staircaseVector*2)+floorsize-1)
        placeCuboid(editor, (pillarX, y+1, pillarZ), (pillarX+1, y+pillarHeight, pillarZ+1), blockPalette)
        # add vines hanging from the pillars
        for j in range(0, pillarHeight):
            if(randint(0,100) < 20): 
                editor.placeBlock((pillarX, y+1+j, pillarZ), Block("vine"))
    
    



buildStructurePerimeter()
buildStructureRoof()
cleanInterior()
buildStructureStairs()
buildStructureFloor()
buildStatue()
buildPillars()

            
        


    

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
