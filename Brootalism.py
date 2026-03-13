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

terrain = [[0,0]]


for i in range(0, buildArea.size.x):
    for j in range(0, buildArea.size.z):
        terrain.append(heightmap[i,j])


y = terrain[len(terrain)-1]


#y = heightmap[3,3] - 1

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

balconyRailPalette = [
    Block("stone_brick_wall"),
    Block("mossy_stone_brick_wall"),
    Block("stone_brick_wall"),
]

ornamentPalette = (
    5*[Block("copper_block")] +
    5*[Block("exposed_copper")] +
    [Block("weathered_copper")] +
    [Block("oxidized_copper")] +
    [Block("air")]
    
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

staircaseVector = randint(5,width//6)

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
            
            
floorsize = randint((width//4), ((width//2) - (staircaseVector)))

def buildStructureFloor():
    #print(floorsize)
    placeCuboid(editor, (x+2+(staircaseVector*2),y+(staircaseVector*2),z+1), (x+2+(staircaseVector*2)+floorsize,y+(staircaseVector*2),z+1+(staircaseVector*2)+floorsize), blockPalette)
    # END SPOT OF THE SECOND FLOOR:
    # (x+1+(staircaseVector*2)+floorsize,y+(staircaseVector*2),z+1+(staircaseVector*2)+floorsize)

    # now adding froglights under the second floor for some lighting
    for i in range(0, floorsize, randint(2,4)):
        for j in range(0, floorsize+staircaseVector):
            editor.placeBlock((x+2+(staircaseVector*2)+i,y+(staircaseVector*2)-1,z+1+(staircaseVector)+j), Block("pearlescent_froglight"))

    
        

def decorate():
    # statue parameters
    statueWidth = randint(3, floorsize//2)
    statueHeight = randint(10, staircaseVector*2)
    statueDepth = randint(3, floorsize//2)

    statueX = x + 2 + (staircaseVector*2) + (floorsize//2) - (statueWidth//2)
    statueY = y + 1 + (staircaseVector*2)
    statueZ = z + 1 + (staircaseVector*2) + (floorsize//2) - (statueDepth//2)

    # build the statue
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


    # add some random small, but chunky pillars. Randomized decoration - could be more intentional later.
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

    # balcony time! - 70% chance to spawn
    if(randint(0,100) < 70):
        balconyLength = randint(3,5)
        balconyWidth = randint(5, floorsize//2)
        for i in range(0, balconyWidth):
            for j in range(0, balconyLength):
                if (j == 0):
                    # implementing this to have empty spaces in the stairs 
                    if (i != 0 and i != balconyWidth-1):
                        # there could be a separate value here for balconyX to not use the same, as sometimes it can be one block off being centered. Due to time constrain I don't solve this right now
                        editor.placeBlock((statueX+statueWidth//2-(balconyWidth//2)+i, statueY, z+1+(staircaseVector*2)+floorsize+j), Block("stone_brick_stairs", {"facing": "south"}))
                        
                # make stairs leading to the balcony
                else:
                    editor.placeBlock((statueX+statueWidth//2-(balconyWidth//2)+i, statueY, z+1+(staircaseVector*2)+floorsize+j), blockPalette)
                
                # then at the edges (gotta calculate), make a ledge of sorts to make it look nicer than just blocks
                if (((i >= 0 and i <= balconyWidth-1) and (j == balconyLength-1)) or ((i == 0 or i == balconyWidth-1) and (j >= 1 and j < balconyLength-1))):
                    editor.placeBlock(((statueX+statueWidth//2-(balconyWidth//2)+i, statueY+1, z+1+(staircaseVector*2)+floorsize+j)), balconyRailPalette)
    
def hang_ornament():
    if(randint(0,100) < 50):
        ornamentSize = randint(3, 7)

        # center point of ornament
        cx = x + width - 2 - ornamentSize*2
        cz = z + depth - 2 - ornamentSize*2

        # random chain length - long enough to reach the roof, but not too long to look weird. Also adds some variation in the hanging ornaments.
        chain_length = randint(5, ornamentSize + 2)

        # place slightly random chain
        for k in range(chain_length):
            editor.placeBlock(
                (cx, y + height - k, cz), Block("iron_chain")
            )

        # starting Y for pyramid
        base_y = y + height - chain_length

        # upside-down pyramid converging to center
        for level in range(ornamentSize):
            size = ornamentSize - level

            for dx in range(-size, size + 1):
                for dz in range(-size, size + 1):
                    editor.placeBlock((cx - dx, base_y - level, cz - dz), ornamentPalette)

def buildRooms():
    # small rooms on the ground level, with a 50% chance to generate each room, and random sizes and positions. They will be hollowed out of the main structure, so they will be empty inside. but have doors and windows. They will be placed on the perimeter of the structure, so they will have at least one wall that is also a wall of the main structure. This is to make them look more integrated into the main structure, rather than just being attached to it.
    numRooms = randint(2, 5)
    for i in range(0, numRooms):
        roomWidth = randint(5, width//3)
        roomDepth = randint(5, depth//3)
        roomHeight = randint(4, staircaseVector*2 - 2)

        # random position for the room
        wall = randint(0, 1) # 0 = east, 1 = south; noth and west are skipped because we have the staircase and entrance there.
        if wall == 0: # east wall
            roomX = x + width - roomWidth - 1
            roomZ = randint(z + 2, z + depth - roomDepth - 2)
        else: # south wall
            roomX = randint(x + 2, x + width - roomWidth - 2)
            roomZ = z + depth - roomDepth - 1

        # build the room as a hollow cuboid
        placeCuboidHollow(editor, (roomX, y, roomZ), (roomX + roomWidth, y + roomHeight, roomZ + roomDepth), blockPalette)
        # and add lightning at random spots on the ceiling of the room, with a 30% chance to place a light block at each position, to make it look more lived in and less like a dungeon. Using froglights for the lighting, and placing them randomly on the ceiling of the room.
        for j in range(0, roomWidth):
            for k in range(0, roomDepth):
                if(randint(0,100) < 30):
                    editor.placeBlock((roomX + j, y + roomHeight - 1, roomZ + k), Block("pearlescent_froglight"))

        # and then add some windows and a door to the room, with a 50% chance for each wall to have a window, and a 50% chance for the room to have a door. The door will be placed on the wall that is not shared with the main structure, to make it look more natural.
        for j in range(0, roomWidth):
            for k in range(0, roomHeight):
                if wall == 0: # east wall
                    editor.placeBlock((roomX + roomWidth, y + 1 + k, roomZ + j), Block("glass_pane"))
                else: # south wall
                    editor.placeBlock((roomX + j, y + 1 + k, roomZ + roomDepth), Block("glass_pane"))
        
        
        doorHeight = 2
        doorWidth = 1

        if wall == 0: # east wall
            placeCuboid(editor, (roomX, y + 1, roomZ + roomDepth//2 - doorWidth//2), (roomX, y + 1 + doorHeight, roomZ + roomDepth//2 + doorWidth//2), Block("air"))
            editor.placeBlock((roomX, y + 1, roomZ + roomDepth//2), Block("oak_door", {"facing": "east", "half": "lower"}))
            editor.placeBlock((roomX, y + 2, roomZ + roomDepth//2), Block("oak_door", {"facing": "east", "half": "upper"}))
        else: # south wall
            placeCuboid(editor, (roomX + roomWidth//2 - doorWidth//2, y + 1, roomZ), (roomX + roomWidth//2 + doorWidth//2, y  + doorHeight, roomZ), Block("air"))
            editor.placeBlock((roomX + roomWidth//2, y + 1, roomZ), Block("oak_door", {"facing": "south", "half": "lower"}))
            editor.placeBlock((roomX + roomWidth//2, y + 2, roomZ), Block("oak_door", {"facing": "south", "half": "upper"}))

buildStructurePerimeter()
buildStructureRoof()
cleanInterior()
buildStructureStairs()
buildStructureFloor()
decorate()
hang_ornament()
buildRooms()
