import bpy, os

#website adress:
#@https://twitter.com/dorianborremans?lang=en

# ##########################################################################################################################

bpy.ops.scatter.execute_layer(

objects  =  "Sc Snowpile Medium",
preset   =  "scatter_#_winter_snowpile_medium.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Snowpile Medium",
display  =  100,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Snowpile Small",
preset   =  "scatter_#_winter_snowpile_small.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Snowpile Small",
display  =  100,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Snowy Grass",
preset   =  "scatter_#_winter_snowy_grass.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Snowy Grass",
display  =  3,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Snowy Grass Clump",
preset   =  "scatter_#_winter_snowy_grass_clump.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Snowy Grass Clump",
display  =  5,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Snowy Leaves",
preset   =  "scatter_#_winter_snowy_leaves.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Snowy Leaves",
display  =  10,
)


# ##########################################################################################################################

"""#DESCRIPTION_START
Winter ecosystem with some piles of snow, snowy leaves and grass
"""#DESCRIPTION_STOP

