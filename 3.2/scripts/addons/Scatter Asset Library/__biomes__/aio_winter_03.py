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

objects  =  "Sc Frozen Grass",
preset   =  "scatter_#_winter_frozen_grass.py",
blend    =  "scatter_#_part1.blend",
namee    =  'Frozen Grass',
display  =  3,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Frozen Grass Wild",
preset   =  "scatter_#_winter_frozen_grass_wild.py",
blend    =  "scatter_#_part1.blend",
namee    =  'Frozen Grass Wild',
display  =  30,
)

bpy.ops.scatter.execute_layer(

objects  =  "Sc Frozen Nettle",
preset   =  "scatter_#_winter_frozen_nettle.py",
blend    =  "scatter_#_part1.blend",
namee    =  "Frozen Nettle",
display  =  30,
)


# ##########################################################################################################################

"""#DESCRIPTION_START
Winter ecosystem with some piles of snow, frozen nettles and high herbs
"""#DESCRIPTION_STOP

