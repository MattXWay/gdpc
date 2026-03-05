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

def buildHouse(startX, startZ):
        # Random floor palette
        floorPalette = [
            Block("stone_bricks"),
            Block("cracked_stone_bricks"),
            Block("cobblestone"),
        ]

        # Choose wall material
        wallBlock = choice([
            Block("oak_planks"),
            Block("spruce_planks"),
            Block("white_terracotta"),
            Block("green_terracotta"),
            Block("red_concrete")
        ])
        
        y = heightmap[3,3]
        # Build main shape
        placeCuboidHollow(editor, (startX, y, startZ), (startX+4, y+height, startZ+depth), wallBlock)
        placeCuboid(editor, (startX, y, z), (startX+4, y, startZ+depth), floorPalette)

        # Build roof: loop through distance from the middle
        for dx in range(1, 4):
            yy = y + height + 2 - dx

            # Build row of stairs blocks
            leftBlock  = Block("oak_stairs", {"facing": "east"})
            rightBlock = Block("oak_stairs", {"facing": "west"})
            placeCuboid(editor, (startX+2-dx, yy, startZ-1), (startX+2-dx, yy, startZ+depth+1), leftBlock)
            placeCuboid(editor, (startX+2+dx, yy, startZ-1), (startX+2+dx, yy, startZ+depth+1), rightBlock)

        # build the top row of the roof
        yy = y + height + 1
        placeCuboid(editor, (startX+2, yy, startZ-1), (startX+2, yy, startZ+depth+1), wallBlock)
        
        
        y = heightmap[3,1] - 1

        # Add a door
        doorBlock = Block("oak_door", {"facing": "north", "hinge": "left"})
        editor.placeBlock((startX+2, y+1, startZ), doorBlock)

        # Clear some space in front of the door
        placeCuboid(editor, (startX+1, y+1, startZ-1), (startX+3, y+3, startZ-1), Block("air"))


index = randint(20, 22)
for i in range(0, index):
    for j in range (0, index):
        buildHouse(x + i * 8, z + j * 12)

