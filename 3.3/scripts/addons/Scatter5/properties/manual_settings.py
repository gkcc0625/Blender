



# ooo        ooooo                                             oooo        .oooooo..o               .       .    o8o
# `88.       .888'                                             `888       d8P'    `Y8             .o8     .o8    `"'
#  888b     d'888   .oooo.   ooo. .oo.   oooo  oooo   .oooo.    888       Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  8 Y88. .P  888  `P  )88b  `888P"Y88b  `888  `888  `P  )88b   888        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#  8  `888'   888   .oP"888   888   888   888   888   .oP"888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
#  8    Y     888  d8(  888   888   888   888   888  d8(  888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# o8o        o888o `Y888""8o o888o o888o  `V88V"V8P' `Y888""8o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                                                 d"     YD
#                                                                                                                                 "Y88888P'


import math

import bpy
from .. resources.translate import translate

from bpy.props import PointerProperty, BoolProperty, StringProperty, FloatProperty, IntProperty, FloatVectorProperty, EnumProperty, CollectionProperty, IntVectorProperty
from bpy.types import PropertyGroup


# 88""Yb 88""Yb 88   88 .dP"Y8 88  88 888888 .dP"Y8
# 88__dP 88__dP 88   88 `Ybo." 88  88 88__   `Ybo."
# 88""Yb 88"Yb  Y8   8P o.`Y8b 888888 88""   o.`Y8b
# 88oodP 88  Yb `YbodP' 8bodP' 88  88 888888 8bodP'

class SCATTER5_manual_common(PropertyGroup, ):
    # hidden
    # cursor: StringProperty(default='CROSS', )
    cursor: StringProperty(
        default='RETICLE', 
        )
    radius: FloatProperty(
        default=1.0, 
        )
    # hidden? or not?
    radius_increment: FloatProperty(
        name=translate("Increment"), 
        default=1.0 / 30, 
        precision=3, 
        description=translate(""), 
        )
    # user accessible, but have to be set explicitly in ui code
    radius_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""),
        )
    # timer interval for timer brushes
    interval: FloatProperty(
        name=translate("Interval"), 
        default=0.1, 
        min=0.001, max=1.0,  precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    # some brushes can draw on timer or on mouse move or both
    draw_on: EnumProperty(
        name=translate("Draw On"), 
        default='TIMER', 
        items=[ ('TIMER', translate("Timer"), "",), 
                ('MOUSEMOVE', translate("Mouse Move"), "",), 
                ('BOTH', translate("Both"), "", ), 
              ], 
        description=translate(""), 
        )
    # area brushes falloff inside radius, at 0, effect is scaled from brush center, at 1, effect is the same on whole area
    
    # NOTE: falloff if read only and hidden from ui.. see todo in brushes.py
    def _falloff_distance_get(self, ):
        return 0.0
    
    # def _falloff_distance_set(self, v, ):
    #     pass
    
    falloff_distance: FloatProperty(
        name=translate("Falloff"), 
        default=0.0, min=0.0, max=1.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        get=_falloff_distance_get,
        # set=_falloff_distance_set,
        )
    
    affect_portion: FloatProperty(
        name=translate("Probability"), 
        default=1 / 2, 
        min=0.001, max=1.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    affect_portion_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""), 
        )


class SCATTER5_manual_create(PropertyGroup, ):
    # always visible for create brushes
    
    # some defaults..
    instance_index: IntProperty(
        name=translate("Instance Index"), 
        default=0, 
        min=0, 
        max=99, 
        description=translate(""), 
        )
    
    # rotation base properties
    rotation_align: EnumProperty(
        name=translate("Align Z"), 
        default='SURFACE_NORMAL', 
        items=[('SURFACE_NORMAL', translate("toward Mesh Normals"), "", "NORMALS_FACE",1),
               ('LOCAL_Z_AXIS', translate("toward Local Z"), "","ORIENTATION_LOCAL",32),
               ('GLOBAL_Z_AXIS', translate("toward Global Z"), "", "WORLD",3),
              ], 
        description=translate(""), 
        )
    rotation_up: EnumProperty(
        name=translate("Align Y"), 
        default='GLOBAL_Y_AXIS', 
        items=[('GLOBAL_Y_AXIS', translate("toward Global Y"), "","WORLD",2 ),
               ('LOCAL_Y_AXIS', translate("toward Local Y"), "", "ORIENTATION_LOCAL", 1),
              ],
        description=translate(""),
        )
    rotation_base: FloatVectorProperty(
        name=translate("Rotation Values"), 
        default=(0.0, 0.0, 0.0, ), 
        precision=3, subtype='EULER', size=3, 
        description=translate(""), 
        )
    rotation_random: FloatVectorProperty(
        name=translate("Random Addition"), 
        default=(0.0, 0.0, 0.0, ), 
        precision=3, subtype='EULER', size=3, 
        description=translate(""), 
        )
    
    # # scale base properties
    # use_scale_uniform: BoolProperty(name=translate("Randomization Type"), default=False, description=translate(""), )
    # scale_uniform_base: FloatProperty(name=translate("Scale"), default=1.0, precision=3, subtype='NONE', description=translate(""), )
    # scale_base: FloatVectorProperty(name=translate("Base"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate(""), )
    # use_scale_random: BoolProperty(name=translate("Random"), default=False, description=translate(""), )
    # scale_uniform_random: FloatProperty(name=translate("Random"), default=1.0, precision=3, subtype='NONE', description=translate(""), )
    # scale_random: FloatVectorProperty(name=translate("Random"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate(""), )
    
    # scale base properties
    scale_default: FloatVectorProperty(
        name=translate("Default Scale"), 
        default=(1.0, 1.0, 1.0, ), 
        precision=3, 
        subtype='XYZ', 
        size=3, 
        description=translate(""), 
        )
    scale_default_use_pressure: BoolProperty(
        name=translate("Use Pressure"),
        default=False,
        )
    scale_random_factor: FloatVectorProperty(
        name=translate("Random Factor"), 
        default=(1.0, 1.0, 1.0, ), 
        precision=3, 
        subtype='XYZ', 
        size=3, 
        description=translate(""), 
        )
    scale_random_type: EnumProperty(
        name=translate("Randomization Type"), 
        default='UNIFORM', 
        items=[('UNIFORM', translate("Uniform"), "", ), 
               ('VECTORIAL', translate("Vectorial"), "", ), 
              ], 
        description=translate(""), 
        )


class SCATTER5_manual_modify(PropertyGroup, ):
    # always visible for modify brushes
    pass


class SCATTER5_manual_default_brush(SCATTER5_manual_common, SCATTER5_manual_create, SCATTER5_manual_modify, ):
    # this can be read for default values for transformation if need to be. it is used only by base brush and not anywhere else
    pass


class SCATTER5_manual_default_brush_2d(SCATTER5_manual_common, SCATTER5_manual_create, SCATTER5_manual_modify, ):
    # # this can be read for default values for transformation if need to be. it is used only by base brush and not anywhere else
    # cursor: StringProperty(default='CIRCLE', )
    # radius: FloatProperty(name=translate("Radius"), default=100.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    # radius_increment: FloatProperty(name=translate("Increment"), default=5.0, precision=0, description=translate(""), )
    pass


class SCATTER5_manual_dot_brush(SCATTER5_manual_common, SCATTER5_manual_create, ):
    pass


class SCATTER5_manual_spatter_brush(SCATTER5_manual_common, SCATTER5_manual_create, ):
    # overrides
    cursor: StringProperty(default='CROSS', )
    radius: FloatProperty(name=translate("Radius"), default=1.0, min=0.001, soft_max=3.0, precision=3, subtype='FACTOR', description=translate(""), )
    interval: FloatProperty(name=translate("Interval"), default=0.1, min=0.001, max=1.0,  precision=3, subtype='FACTOR', description=translate(""), )
    draw_on: EnumProperty(
        name=translate("Draw On"),
        default='BOTH',
        items=[('TIMER', translate("Timer"), "",), 
               ('MOUSEMOVE', translate("Mouse Move"), "",), 
               ('BOTH', translate("Both"), "", ), ],
        description=translate(""),
    )
    
    random_location: FloatProperty(name=translate("Random Location"), default=0.333, min=0.0, max=100.0, precision=5, subtype='DISTANCE', description=translate(""), )
    random_location_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate(""), )
    align: BoolProperty(name=translate("Align Y to Stroke Direction"), default=False, description=translate(""), )
    

class SCATTER5_manual_pose_brush(SCATTER5_manual_common, SCATTER5_manual_create, ):
    # # 2d type
    # cursor: StringProperty(default='COMPASS', )
    # cursor: StringProperty(default='RETICLE', )
    # radius: FloatProperty(name=translate("Radius"), default=100.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    # radius_increment: FloatProperty(name=translate("Increment"), default=5.0, precision=0, description=translate(""), )
    # cursor_2d: StringProperty(default='COMPASS', )
    # cursor_2d: StringProperty(default='ARROW', )
    # cursor_2d: StringProperty(default='ARROW_TO', )
    cursor_2d: StringProperty(default='ARROW_FROM_TO', )
    # radius_2d: FloatProperty(name=translate("Radius"), default=100.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    radius_2d: FloatProperty(name=translate("Radius"), default=200.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    
    # 3d type
    # cursor: StringProperty(default='RETICLE', )
    # cursor: StringProperty(default='COMPASS', )
    cursor: StringProperty(default='RETICLE', )
    radius: FloatProperty(default=1.0, )
    
    # common
    scale_multiplier: FloatProperty(name=translate("Scale Multiplier"), default=0.1, min=0.001, soft_max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    scale_default: FloatVectorProperty(
        name=translate("Initial Scale"), 
        default=(0.3, 0.3, 0.3, ), 
        precision=3, 
        subtype='XYZ', 
        size=3, 
        description=translate(""), 
        )


class SCATTER5_manual_path_brush(SCATTER5_manual_common, SCATTER5_manual_create, ):
    # brush properties
    path_distance: FloatProperty(
        name=translate("Dot Distance"),
        default=1.0,
        min=0.00001, max=100.0, precision=5, subtype='DISTANCE', 
        description=translate(""), 
        )
    path_distance_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""), 
        )
    # path_distance_random: BoolProperty(
    #     name=translate("Randomize Dot Distance"),
    #     default=False,
    #     description=translate(""),
    #     )
    align: BoolProperty(
        name=translate("Align Y to Stroke Direction"),  #Actually, it should be within the rotation align Y enum but well it might be annoying to have a special enum just for this option 
        default=False, 
        description=translate(""), 
        )
    chain: BoolProperty(
        name=translate("Chain"), 
        default=False, 
        description=translate(""), 
        )
    divergence_distance: FloatProperty(
        name=translate("Divergence Distance"),
        default=0.0,
        min=0.0, max=100.0, precision=5, subtype='DISTANCE', 
        description=translate(""), 
        )
    divergence_distance_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""), 
        )


class SCATTER5_manual_spray_brush(SCATTER5_manual_common, SCATTER5_manual_create, ):
    # overrides
    cursor: StringProperty(
        default='SPRAY',
        )
    radius: FloatProperty(
        name=translate("Radius"),
        default=1.0,
        min=0.001, soft_max=3.0, precision=3, subtype='FACTOR', 
        description=translate(""), 
        )
    
    # brush properties
    num_dots: IntProperty(
        name=translate("Points Per Interval"), 
        default=50, 
        min=1, 
        soft_max=250,
        max=5000,
        description=translate(""), 
        )
    num_dots_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""), 
        )
    jet: FloatProperty(
        name=translate("Spray Distance"),
        default=1,
        min=0.001,
        soft_max=3.0,
        precision=3,
        subtype='NONE',
        description=translate("Spray Distance, Factor Relative to Radius"),
        )
    reach: FloatProperty(
        name=translate("Spray Reach"),
        default=1.0,
        min=0.001,
        precision=3,
        soft_max=4,
        subtype='DISTANCE',
        description=translate(""),
        )
    use_minimal_distance: BoolProperty(
        name=translate("Use Minimal Distance"), 
        default=False, 
        description=translate(""), 
        )
    minimal_distance: FloatProperty(
        name=translate("Points Minimal Distance"), 
        default=0.25, 
        min=0.0,
        # max=1.0,
        precision=3, subtype='DISTANCE', 
        description=translate(""), 
        )
    minimal_distance_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""), 
        )
    
    align: BoolProperty(
        name=translate("Align Y to Stroke Direction"), 
        default=False, 
        description=translate(""), 
        )


class SCATTER5_manual_move_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE',
        )
    radius: FloatProperty(
        name=translate("Radius"), 
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    
    # brush properties
    affect_portion: FloatProperty(
        name=translate("Probability"), 
        default=1.0, 
        min=0.001, 
        max=1.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    use_align_surface: BoolProperty(
        name=translate("Align Z To Surface Normal"),
        default=True,
        description=translate(""),
        )


class SCATTER5_manual_eraser_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE', 
        )
    radius: FloatProperty(
        name=translate("Radius"), 
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    draw_on: EnumProperty(
        name=translate("Draw On"), 
        default='BOTH', 
        items=[('TIMER', translate("Timer"), "", ), 
               ('MOUSEMOVE', translate("Mouse Move"), "", ), 
               ('BOTH', translate("Both"), "", ), ], 
        description=translate(""), 
        )
    
    # brush properties
    affect_portion: FloatProperty(
        name=translate("Probability"), 
        # default=1 / 10, 
        default=1.0, 
        min=0.001, max=1.0, precision=3, subtype='FACTOR', 
        description=translate(""), 
        )


class SCATTER5_manual_dilute_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE', 
        )
    radius: FloatProperty(
        name=translate("Radius"),
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""),
        )
    draw_on: EnumProperty(
        name=translate("Draw On"),
        default='BOTH', 
        items=[('TIMER', translate("Timer"), "", ), 
               ('MOUSEMOVE', translate("Mouse Move"), "", ), 
               ('BOTH', translate("Both"), "", ), 
              ], 
        description=translate(""),
        )
    
    # brush properties
    affect_portion: FloatProperty(
        name=translate("Probability"), 
        default=1 / 10, 
        min=0.001, max=1.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""),
        )
    minimal_distance: FloatProperty(
        name=translate("Points Minimal Distance"), 
        default=0.25, 
        min=0.0,
        # max=1.0,
        precision=3, 
        subtype='DISTANCE', 
        description=translate(""),
        )


class SCATTER5_manual_rotation_base_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE',
        )
    radius: FloatProperty(
        name=translate("Radius"),
        default=1.0, min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    
    # brush properties
    mode: EnumProperty(
        name=translate("Mode"), 
        default='SET', 
        items=[('SET', translate("Set Rotation"), "", ),
               # NOTE: there is no change mode implemented..
               # ('CHANGE', translate("Change Rotation"), "", ),
              ], 
        description=translate(""), 
        ) 
    # NOTE: there is no change mode implemented..
    change_mode: EnumProperty(
        name=translate("Mode"),
        default='ADD', 
        items=[('ADD', translate("Add"), "", ),
               ('SUBTRACT', translate("Subtract"), "", ),
              ], 
        description=translate(""),
        )
    
    use_rotation_align: BoolProperty(name=translate("Enabled"), default=False, description=translate(""), )
    rotation_align: EnumProperty(
        name=translate("Align Z"), 
        default='SURFACE_NORMAL', 
        items=[('SURFACE_NORMAL', translate("toward Mesh Normals"), "", "NORMALS_FACE",1),
               ('LOCAL_Z_AXIS', translate("toward Local Z"), "","ORIENTATION_LOCAL",32),
               ('GLOBAL_Z_AXIS', translate("toward Global Z"), "", "WORLD",3),
              ], 
        description=translate(""), 
        )
    rotation_up: EnumProperty(
        name=translate("Align Y"), 
        default='GLOBAL_Y_AXIS', 
        items=[('LOCAL_Y_AXIS', translate("toward Local Y"), "", "ORIENTATION_LOCAL", 1),
               ('GLOBAL_Y_AXIS', translate("toward Global Y"), "","WORLD",2 ),
              ], 
        description=translate(""), 
        )
    use_rotation_base: BoolProperty(name=translate("Enabled"), default=False, description=translate(""), )
    rotation_base: FloatVectorProperty(
        name=translate("Rotation Values"), 
        default=(0.0, 0.0, 0.0, ), 
        precision=3, subtype='EULER', size=3, 
        description=translate(""),
        )
    use_rotation_random: BoolProperty(name=translate("Enabled"), default=False, description=translate(""), )
    rotation_random: FloatVectorProperty(
        name=translate("Random Addition"), 
        default=(0.0, 0.0, 0.0, ), 
        precision=3, subtype='EULER', size=3, 
        description=translate(""),
        )


'''
class SCATTER5_manual_rotation_align_brush(SCATTER5_manual_rotation_base_brush, ):
    # NOTE: hide props in ui
    pass


class SCATTER5_manual_rotation_set_brush(SCATTER5_manual_rotation_base_brush, ):
    # NOTE: hide props in ui
    pass


class SCATTER5_manual_rotation_random_brush(SCATTER5_manual_rotation_base_brush, ):
    # NOTE: hide props in ui
    pass
'''


class SCATTER5_manual_rotation_brush(SCATTER5_manual_rotation_base_brush, ):
    # NOTE: hide props in ui
    pass


class SCATTER5_manual_scale_base_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE', 
        )
    radius: FloatProperty(
        name=translate("Radius"), 
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    
    # brush properties
    mode: EnumProperty(
        name=translate("Mode"), 
        default='RANDOM', 
        items=[('SET', translate("Set Scale"), "", ),
               ('CHANGE', translate("Change Scale"), "", ),
               ('RANDOM', translate("Random Scale"), "", ),
              ], 
        description=translate(""), 
        )
    # TODO: this is unused i think, better check that..
    base: FloatVectorProperty(name=
        translate("Base"), 
        default=(1.0, 1.0, 1.0, ), 
        precision=3,  subtype='XYZ', size=3, 
        description=translate(""), 
        )
    change_mode: EnumProperty(
        name=translate("Mode"), 
        default='ADD', 
        items=[('ADD', translate("Add"), "", ),
               ('SUBTRACT', translate("Subtract"), "", ),
              ], 
        description=translate(""), 
        )
    change: FloatVectorProperty(
        name=translate("Value"), 
        default=(0.1, 0.1, 0.1, ), 
        precision=3, subtype='XYZ', size=3, 
        description=translate(""), 
        )
    use_limits: BoolProperty(
        name=translate("Use Limits"),
        default=False, 
        description=translate(""),
        )
    limits: FloatVectorProperty(
        name=translate("Limits"), 
        default=(0.0, 1.0, ), 
        precision=3, 
        size=2, 
        description=translate(""), 
        )
    
    # rnd_use_scale_uniform: BoolProperty(name=translate("Randomization Type"), default=False, description=translate(""), )
    # rnd_scale_uniform_base: FloatProperty(name=translate("Scale"), default=1.0, precision=3, subtype='NONE', description=translate(""), )
    # rnd_scale_base: FloatVectorProperty(name=translate("Base"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate(""), )
    # rnd_use_scale_random: BoolProperty(name=translate("Random"), default=True, description=translate(""), )
    # rnd_scale_uniform_random: FloatProperty(name=translate("Random"), default=1.0, precision=3, subtype='NONE', description=translate(""), )
    # rnd_scale_random: FloatVectorProperty(name=translate("Random"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate(""), )
    
    # scale base properties (the same as in create brush type)
    use_scale_default: BoolProperty(name=translate("Enabled"), default=False, description=translate(""), )
    scale_default: FloatVectorProperty(
        name=translate("Default Scale"), 
        default=(1.0, 1.0, 1.0, ), 
        precision=3, subtype='XYZ', size=3, 
        description=translate(""), 
        )
    
    use_scale_random_factor: BoolProperty(name=translate("Enabled"), default=False, description=translate(""), )
    scale_random_factor: FloatVectorProperty(
        name=translate("Random Factor"), 
        default=(1.0, 1.0, 1.0, ), 
        precision=3, subtype='XYZ', size=3, 
        description=translate(""), 
        )
    scale_random_type: EnumProperty(
        name=translate("Randomization Type"), 
        default='UNIFORM', 
        items=[('UNIFORM', translate("Uniform"), "", ), 
               ('VECTORIAL', translate("Vectorial"), "", ), 
              ], 
        description=translate(""), 
        )

    #if mode=="CHANGE":
    change_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""),
        )


'''
class SCATTER5_manual_scale_set_brush(SCATTER5_manual_scale_base_brush, ):
    # NOTE: overrides, hidden from user so it locked in mode
    mode: EnumProperty(name=translate("Mode"), default='SET', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )


class SCATTER5_manual_scale_random_brush(SCATTER5_manual_scale_base_brush, ):
    # NOTE: overrides, hidden from user so it locked in mode
    mode: EnumProperty(name=translate("Mode"), default='RANDOM', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )
'''


class SCATTER5_manual_scale_brush(SCATTER5_manual_scale_base_brush, ):
    # # NOTE: overrides, hidden from user so it locked in mode
    # mode: EnumProperty(name=translate("Mode"), default='SET', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )
    pass


'''
class SCATTER5_manual_scale_grow_brush(SCATTER5_manual_scale_base_brush, ):
    # NOTE: overrides, hidden from user so it locked in mode
    mode: EnumProperty(name=translate("Mode"), default='CHANGE', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )
    change_mode: EnumProperty(name=translate("Mode"), default='ADD', items=[('ADD', translate("Add"), "", ), ('SUBTRACT', translate("Subtract"), "", ), ], description=translate(""), )


class SCATTER5_manual_scale_shrink_brush(SCATTER5_manual_scale_base_brush, ):
    # NOTE: overrides, hidden from user so it locked in mode
    mode: EnumProperty(name=translate("Mode"), default='CHANGE', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )
    change_mode: EnumProperty(name=translate("Mode"), default='SUBTRACT', items=[('ADD', translate("Add"), "", ), ('SUBTRACT', translate("Subtract"), "", ), ], description=translate(""), )
'''


class SCATTER5_manual_scale_grow_shrink_brush(SCATTER5_manual_scale_base_brush, ):
    # NOTE: overrides, hidden from user so it locked in mode
    mode: EnumProperty(name=translate("Mode"), default='CHANGE', items=[('SET', translate("Set Scale"), "", ), ('CHANGE', translate("Change Scale"), "", ), ('RANDOM', translate("Random Scale"), "", ), ], description=translate(""), )
    change_mode: EnumProperty(name=translate("Mode"), default='ADD', items=[('ADD', translate("Add"), "", ), ('SUBTRACT', translate("Subtract"), "", ), ], description=translate(""), )
    
    # user options
    use_change_random: BoolProperty(
        name=translate("Random"),
        default=False,
        description=translate(""),
        )
    # hidden.. just to use factors bigger than 0.5, so scaling is not too slow, will be still random, but not that much..
    change_random_range: FloatVectorProperty(
        name=translate("Random Range"), 
        # default=(0.0, 0.5, ),
        default=(0.5, 1.0, ), 
        precision=3, subtype='NONE', size=2, 
        soft_min=0.0, soft_max=1.0, 
        description=translate(""), 
        )


class SCATTER5_manual_comb_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE',
        )
    radius: FloatProperty(
        name=translate("Radius"), 
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    # draw_on: EnumProperty(name="Draw On", items=[('TIMER', "Timer", "", ), ('MOUSEMOVE', translate("Mouse Move"), "", ), ('BOTH', "Both", "", ), ], default='MOUSEMOVE', description=translate(""), )
    # NOTE: only mouse move, it does not work with timers..
    draw_on: EnumProperty(
        name=translate("Draw On"), 
        default='MOUSEMOVE', 
        items=[('MOUSEMOVE', translate("Mouse Move"), "", ), ], 
        description=translate(""), 
        )
    
    # brush properties
    mode: EnumProperty(
        name=translate("Mode"),
        default='DIRECTION', 
        items=[('DIRECTION', translate("Direction"), "", ),], 
        description=translate(""), 
        )
    strength: FloatProperty(
        name=translate("Strength"),
        default=1.0,
        min=0.0, max=1.0, precision=3, subtype='FACTOR', 
        description=translate(""), 
        )
    strength_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""),
        )
    strength_random: BoolProperty(
        name=translate("Random Strength"),
        default=False,
        description=translate(""),
        )
    strength_random_range: FloatVectorProperty(
        name=translate("Random Strength Range"), 
        # default=(0.0, 0.5, ),
        default=(0.0, 1.0, ), 
        precision=3, subtype='NONE', size=2, 
        soft_min=-1.0, soft_max=1.0, 
        description=translate(""), 
        )
    direction_smoothing_steps: IntProperty(
        name=translate("Direction Smoothing Steps"), 
        default=10, 
        min=0, 
        max=50,
        description=translate(""), 
        subtype='FACTOR',
        )
    
    # remove_randomization: BoolProperty(
    #     name=translate("Remove Randomization"),
    #     default=True,
    #     description=translate(""),
    #     )
    
    # use_axis: BoolProperty(
    #     name=translate("Use Axis"),
    #     default=False,
    #     description=translate(""),
    #     )
    
    mode: EnumProperty(
        name=translate("Mode"), 
        default='COMB', 
        items=[('COMB', translate("Comb"), "", ),
               ('SPIN', translate("Spin"), "", ), ], 
        description=translate(""),
    )
    axis: EnumProperty(
        name=translate("Axis"), 
        default='SURFACE_NORMAL', 
        items=[('SURFACE_NORMAL', translate("Mesh Normal"), "", "NORMALS_FACE", 1, ),
               ('LOCAL_Z_AXIS', translate("Emitter Local Z"), "", "ORIENTATION_LOCAL", 2, ),
               ('GLOBAL_Z_AXIS', translate("Global Z"), "", "WORLD", 3, ),
               ('PARTICLE_Z', translate("Particle Z"), "", "SNAP_NORMAL", 4, ),
              ], 
        description=translate(""), 
        )
    
    speed: FloatProperty(
        name=translate("Angle"),
        default=math.radians(5),
        min=-math.pi, max=math.pi, precision=3, subtype='ANGLE', 
        description=translate(""), 
        )
    speed_pressure: BoolProperty(
        name=translate("Use Pressure"), 
        default=False, 
        description=translate(""),
        )
    speed_random: BoolProperty(
        name=translate("Random Angle"),
        default=False,
        description=translate(""),
        )
    speed_random_range: FloatVectorProperty(
        name=translate("Random Angle Range"), 
        default=(-1.0, 1.0, ), 
        precision=3, subtype='NONE', size=2, 
        soft_min=-1.0, soft_max=1.0, 
        description=translate(""), 
        )
    
    # overrides
    # use_rotation_align: BoolProperty(
    #     name=translate("Enabled"),
    #     default=False,
    #     description=translate(""),
    #     )
    rotation_align: EnumProperty(
        name=translate("Align Z"), 
        default='SURFACE_NORMAL', 
        items=[('SURFACE_NORMAL', translate("toward Mesh Normals"), "", "NORMALS_FACE",1),
               ('LOCAL_Z_AXIS', translate("toward Local Z"), "", "ORIENTATION_LOCAL",2),
               ('GLOBAL_Z_AXIS', translate("toward Global Z"), "", "WORLD",3),
              ], 
        description=translate(""), 
        )
    rotation_up: EnumProperty(
        name=translate("Align Y"), 
        default='GLOBAL_Y_AXIS', 
        items=[('LOCAL_Y_AXIS', translate("toward Local Y"), "", "ORIENTATION_LOCAL", 1), 
               ('GLOBAL_Y_AXIS', translate("toward Global Y"), "", "WORLD",2), 
              ], 
        description=translate(""), 
        )
    rotation_base: FloatVectorProperty(
        name=translate("Rotation Values"), 
        default=(0.0, 0.0, 0.0, ), 
        precision=3, subtype='EULER', size=3, 
        description=translate(""), 
        )
    rotation_random: FloatVectorProperty(
        name=translate("Random Addition"), 
        default=(0.0, 0.0, 0.0, ),
        precision=3, subtype='EULER', size=3, 
        description=translate(""), 
        )


class SCATTER5_manual_object_brush(SCATTER5_manual_common, SCATTER5_manual_modify, ):
    # overrides
    cursor: StringProperty(
        default='CIRCLE', 
        )
    radius: FloatProperty(
        name=translate("Radius"), 
        default=1.0, 
        min=0.001, soft_max=3.0, precision=3, subtype='FACTOR', 
        description=translate(""), 
        )
    
    # brush properties
    index: IntProperty(
        name=translate("Instance Index"), 
        default=0, 
        min=0, max=99, 
        description=translate(""), 
        )


class SCATTER5_manual_random_rotation_brush(SCATTER5_manual_rotation_base_brush, ):
    interval: FloatProperty(
        name=translate("Interval"), 
        # default=0.1,
        default=0.1 / 2, 
        min=0.001, max=1.0,  precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    affect_portion: FloatProperty(
        name=translate("Probability"), 
        # default=1 / 2,
        default=1.0, 
        min=0.001, max=1.0, precision=3, 
        subtype='FACTOR', 
        description=translate(""), 
        )
    
    speed: FloatProperty(
        name=translate("Speed"),
        # default=0.02,
        default=0.015,
        min=-1.0, max=1.0, precision=3, subtype='NONE', 
        description=translate(""), 
        )
    speed_pressure: BoolProperty(
        name=translate("Use Pressure"),
        default=False,
        )
    angle: FloatProperty(
        name=translate("Max Angle"),
        # default=0.02,
        default=math.radians(30),
        min=math.radians(1), max=math.radians(179), precision=3, subtype='ANGLE', 
        description=translate(""), 
        )
    # speed_pressure: BoolProperty(
    #     name=translate("Use Pressure"),
    #     default=False,
    #     description=translate(""),
    #     )
    # speed_random: BoolProperty(
    #     name=translate("Random Speed"),
    #     default=False,
    #     description=translate(""),
    #     )
    # speed_random_range: FloatVectorProperty(
    #     name=translate("Random Speed Range"),
    #     default=(-1.0, 1.0, ),
    #     precision=3, subtype='NONE', size=2,
    #     soft_min=-1.0, soft_max=1.0,
    #     description=translate(""),
    #     )


'''
class SCATTER5_manual_debug_brush_2d(SCATTER5_manual_default_brush_2d, ):
    cursor: StringProperty(default='CIRCLE', )
    radius: FloatProperty(name=translate("Radius"), default=100.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    radius_increment: FloatProperty(name=translate("Increment"), default=5.0, precision=0, description=translate(""), )
    draw_on: EnumProperty(name=translate("Draw On"), default='MOUSEMOVE', items=[ ('TIMER', translate("Timer"), "",), ('MOUSEMOVE', translate("Mouse Move"), "",), ('BOTH', translate("Both"), "", ), ], description=translate(""), )
    affect_portion: FloatProperty(name=translate("Probability"), default=1.0, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    
    strength: FloatProperty(name=translate("Strength"), default=1.0, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    count: IntProperty(name=translate("Count"), default=50, min=1, soft_max=250, max=5000, description=translate(""), )
    length: FloatProperty(name=translate("Length"), default=100, min=1, max=300, precision=5, subtype='DISTANCE', description=translate(""), )
'''


class SCATTER5_manual_z_align_brush(SCATTER5_manual_default_brush_2d, ):
    cursor: StringProperty(default='CIRCLE', )
    radius: FloatProperty(name=translate("Radius"), default=100.0 * 2.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate(""), )
    radius_increment: FloatProperty(name=translate("Increment"), default=5.0, precision=0, description=translate(""), )
    draw_on: EnumProperty(name=translate("Draw On"), default='MOUSEMOVE', items=[ ('TIMER', translate("Timer"), "",), ('MOUSEMOVE', translate("Mouse Move"), "",), ('BOTH', translate("Both"), "", ), ], description=translate(""), )
    affect_portion: FloatProperty(name=translate("Probability"), default=1.0, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    
    strength: FloatProperty(name=translate("Strength"), default=0.2, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    strength_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate(""), )
    falloff: BoolProperty(name=translate("Distance Falloff"), default=True, description=translate(""), )


class SCATTER5_manual_gizmo_brush(SCATTER5_manual_common, SCATTER5_manual_create, SCATTER5_manual_modify, ):
    cursor: StringProperty(default='CROSS', )
    radius: FloatProperty(default=1.0, )


# .dP"Y8  dP""b8 888888 88b 88 888888
# `Ybo." dP   `" 88__   88Yb88 88__
# o.`Y8b Yb      88""   88 Y88 88""
# 8bodP'  YboodP 888888 88  Y8 888888

class SCATTER5_PROP_scene_manual(bpy.types.PropertyGroup):  #registered in .properties
    """bpy.context.scene.scatter5.manual"""
    # brushes..
    default_brush: PointerProperty(type=SCATTER5_manual_default_brush, )
    default_brush_2d: PointerProperty(type=SCATTER5_manual_default_brush_2d, )
    
    dot_brush: PointerProperty(type=SCATTER5_manual_dot_brush, )
    spatter_brush: PointerProperty(type=SCATTER5_manual_spatter_brush, )
    pose_brush: PointerProperty(type=SCATTER5_manual_pose_brush, )
    path_brush: PointerProperty(type=SCATTER5_manual_path_brush, )
    spray_brush: PointerProperty(type=SCATTER5_manual_spray_brush, )
    move_brush: PointerProperty(type=SCATTER5_manual_move_brush, )
    eraser_brush: PointerProperty(type=SCATTER5_manual_eraser_brush, )
    dilute_brush: PointerProperty(type=SCATTER5_manual_dilute_brush, )
    # rotation_align_brush: PointerProperty(type=SCATTER5_manual_rotation_align_brush, )
    # rotation_set_brush: PointerProperty(type=SCATTER5_manual_rotation_set_brush, )
    # rotation_random_brush: PointerProperty(type=SCATTER5_manual_rotation_random_brush, )
    rotation_brush: PointerProperty(type=SCATTER5_manual_rotation_brush, )
    # scale_set_brush: PointerProperty(type=SCATTER5_manual_scale_set_brush, )
    # scale_random_brush: PointerProperty(type=SCATTER5_manual_scale_random_brush, )
    scale_brush: PointerProperty(type=SCATTER5_manual_scale_brush, )
    # scale_grow_brush: PointerProperty(type=SCATTER5_manual_scale_grow_brush, )
    # scale_shrink_brush: PointerProperty(type=SCATTER5_manual_scale_shrink_brush, )
    scale_grow_shrink_brush: PointerProperty(type=SCATTER5_manual_scale_grow_shrink_brush, )
    comb_brush: PointerProperty(type=SCATTER5_manual_comb_brush, )
    object_brush: PointerProperty(type=SCATTER5_manual_object_brush, )
    random_rotation_brush: PointerProperty(type=SCATTER5_manual_random_rotation_brush, )
    z_align_brush: PointerProperty(type=SCATTER5_manual_z_align_brush, )
    gizmo_brush: PointerProperty(type=SCATTER5_manual_gizmo_brush, )
    
    # debug_brush_2d: PointerProperty(type=SCATTER5_manual_debug_brush_2d, )
