
######################################################################################
#
#   .oooooo.                                  oooo             ooooooooo.
#  d8P'  `Y8b                                 `888             `888   `Y88.
# 888           oooo d8b  .oooo.   oo.ooooo.   888 .oo.         888   .d88'  .ooooo.  ooo. .oo.  .oo.    .oooo.   oo.ooooo.
# 888           `888""8P `P  )88b   888' `88b  888P"Y88b        888ooo88P'  d88' `88b `888P"Y88bP"Y88b  `P  )88b   888' `88b
# 888     ooooo  888      .oP"888   888   888  888   888        888`88b.    888ooo888  888   888   888   .oP"888   888   888
# `88.    .88'   888     d8(  888   888   888  888   888        888  `88b.  888    .o  888   888   888  d8(  888   888   888
#  `Y8bood8P'   d888b    `Y888""8o  888bod8P' o888o o888o      o888o  o888o `Y8bod8P' o888o o888o o888o `Y888""8o  888bod8P'
#                                   888                                                                            888
#                                  o888o   
######################################################################################

# This module will handle map curve data
# map curve data supported so far are map curve in vgedit modifiers AND map curve in geometry nodes.
# meaning that this module is an universal Scatter5 map curve data manager.

#in order to work with such data we first need to identify them correctly :
# - source_api : mod api str for modifiers, sometimes need refresh
# - mapping_api : curve api str 


import bpy, random
from mathutils import Vector

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. import utils 



# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo
#  888oooo8    d88' `"Y8   888
#  888    "    888         888
#  888         888   .o8   888 .
# o888o        `Y8bod8P'   "888"



def apply_matrix(curve,matrix):
    """create graph from given location matrix"""   

    for i,p in enumerate(matrix):
        x,y,*h = p
        try: 
            curve.points[i].location = [x,y]
            if h: #handle support, only "VECTOR" or "AUTO"
                curve.points[i].handle_type = h[0]
        except:
            curve.points.new(x,y)

    return None

def get_matrix(curve,handle=False):
    """get points coord matrix from mod"""

    matrix=[]

    for p in curve.points:
        x = p.location.x
        y = p.location.y
        if handle: #handle support, only "VECTOR" or "AUTO"
              h = "VECTOR" if p.handle_type=="VECTOR" else "AUTO"
              matrix.append([x,y,h])
        else: matrix.append([x,y])

    return matrix

def clean_all_points(curve):
    """only left 2 points in the graph"""
        
    iter = 0
    while len(curve.points) > 2: #(seam that cannot got lower and start from 0 ?)

        for p in curve.points:
            try:
                curve.points.remove(p)
                break
            except: #unable to remove  points for some reasons
                pass

        #emergency break
        iter+=1
        if iter==999:
            break

    return None

def move_graph_back_to_origin(curve):
    """move graph abscissa back to origin"""

    first_point = curve.points[0].location.x 

    if first_point==0:
        return None

    step = 0-first_point

    for p in curve.points:
        p.select = False
        p.location.x = p.location.x + step

    return None 

def move_whole_graph(curve, direction="RIGHT",step=0.03, frame_coherence=False,):
    """move graph abscissa left/right by given step value, anchor point with first point"""

    for p in curve.points:
        p.select = False
    
    if frame_coherence:
        #back to origin
        move_graph_back_to_origin(curve)
        #move depending on frame 
        frame_current = bpy.context.scene.frame_current
        delta = step*frame_current
        for p in curve.points:
            p.location.x = p.location.x - delta

    else:
        if direction=="LEFT":
            step = -step
        for p in curve.points:
            p.location.x = p.location.x + step

    return None 

def graph_max_falloff(curve, perc, falloff,):
    """graph from percentage/falloff"""

    def bool_round(x):
        if not 1>x>0:
            if x>1: x=1
            if x<0: x=0
        return x

    #if custom graph then no update
    if len(curve.points)!= 2:
        clean_all_points(curve)

    p1 = curve.points[0]
    p2 = curve.points[1]

    value = perc/100

    #set values

    p1_value = value - falloff
    p1_value = bool_round(p1_value)
    p1.location = [p1_value  ,0.0]

    p2_value = value + falloff
    p2_value = bool_round(p2_value)
    p2.location = [p2_value  ,1.0]

    return None

def graph_min_max(curve, v1, v2,):
    """graph from min max value"""

    minv = None 

    #re-evaluate min and max as user may be dummy 
    if v1>=v2:
        maxv,minv = v1/100,v2/100
    elif v1<=v2:
        maxv,minv = v2/100,v1/100

    if minv == 0:

        if len(curve.points)>2:
            clean_all_points(curve)

        max1,max2 = maxv-0.001,maxv+0.001
        matrix    = ([max1,0],[max2,1])

    else:

        if len(curve.points)>4:
            clean_all_points(curve)

        max1,max2 = maxv-0.001,maxv+0.001
        min1,min2 = minv-0.001,minv+0.001
        matrix    = ([max1,0],[max2,1],[min1,1],[min2,0])

    apply_matrix(curve ,matrix)

    return None

def graph_update(map_curve=None, remap_modifier=None, show_viewport_refresh=True):

    if (map_curve is None): 
        return None 

    if (remap_modifier is not None) and show_viewport_refresh:
        remap_modifier.show_viewport = not remap_modifier.show_viewport
        remap_modifier.show_viewport = not remap_modifier.show_viewport
    
    map_curve.update()

    return None 



#       .o.             .o8        .o8       oooooo     oooo                 oooooooooooo       .o8   o8o      .
#      .888.           "888       "888        `888.     .8'                  `888'     `8      "888   `"'    .o8
#     .8"888.      .oooo888   .oooo888         `888.   .8'    .oooooooo       888          .oooo888  oooo  .o888oo
#    .8' `888.    d88' `888  d88' `888          `888. .8'    888' `88b        888oooo8    d88' `888  `888    888
#   .88ooo8888.   888   888  888   888           `888.8'     888   888        888    "    888   888   888    888
#  .8'     `888.  888   888  888   888            `888'      `88bod8P'        888       o 888   888   888    888 .
# o88o     o8888o `Y8bod88P" `Y8bod88P"            `8'       `8oooooo.       o888ooooood8 `Y8bod88P" o888o   "888"
#                                                            d"     YD
#                                                            "Y88888P'


class SCATTER5_OT_add_vg_edit(bpy.types.Operator): 
    """add vg edit, == map curve graph for vg, OPERATOR FOR PROCEDURAL MASK VG ONLY"""

    bl_idname = "scatter5.add_vg_edit"
    bl_label = translate("Add Weight Remap")
    bl_description = ""
    bl_options = {'INTERNAL','UNDO'}

    mask_name : bpy.props.StringProperty()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 
        masks = emitter.scatter5.mask_systems
        mod_name = f"Scatter5 Remapping {self.mask_name}"

        if (mod_name in emitter.modifiers) or (self.mask_name not in masks) or (self.mask_name not in emitter.vertex_groups):
            return {'FINISHED'}
                    
        m = emitter.modifiers.new(name=mod_name, type="VERTEX_WEIGHT_EDIT" )
        m.falloff_type  = "CURVE"
        m.vertex_group  = self.mask_name
        m.show_expanded = False

        #add newly created modifier to mask mod_list
        masks[self.mask_name].mod_list += mod_name+"_!#!_"
            
        return {'FINISHED'}



# oooooooooo.    o8o            oooo
# `888'   `Y8b   `"'            `888
#  888      888 oooo   .oooo.    888   .ooooo.   .oooooooo
#  888      888 `888  `P  )88b   888  d88' `88b 888' `88b
#  888      888  888   .oP"888   888  888   888 888   888
#  888     d88'  888  d8(  888   888  888   888 `88bod8P'
# o888bood8P'   o888o `Y888""8o o888o `Y8bod8P' `8oooooo.
#                                               d"     YD
#                                               "Y88888P'


from .. ui import templates

class SCATTER5_OT_graph_dialog(bpy.types.Operator):

    bl_idname  = "scatter5.graph_dialog"
    bl_label   = translate("Values Remapping Graph")
    bl_options = {'REGISTER', 'INTERNAL'}

    #Dialog Properties 

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()
    mask_name : bpy.props.StringProperty()

    #perhaps it's best to pass the data below directly as an object? ex: SCATTER5_OT_graph_dialog.modifier = mod

    def min_max_upd(self, context):
        """min/max  Update function"""

        graph_min_max(eval(f"{self.mapping_api}.curves[0]"), self.min, self.max)

        m = None 
        if (".node_group.nodes['" not in self.source_api):
            m = eval(self.source_api)
            m.falloff_type = "CURVE"
        graph_update(map_curve=eval(self.mapping_api),remap_modifier=m, show_viewport_refresh=False)

        return None

    min : bpy.props.FloatProperty(
        name=translate("Min Value"),
        default=0,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        update= min_max_upd, 
        ) 

    def max_fall_upd(self, context):
        """val/fal  Update function"""

        graph_max_falloff(eval(f"{self.mapping_api}.curves[0]"), self.val, self.fal)

        m = None
        if (".node_group.nodes['" not in self.source_api):
            m = eval(self.source_api)
            m.falloff_type = "CURVE"
        graph_update(map_curve=eval(self.mapping_api),remap_modifier=m, show_viewport_refresh=False)

        return None    

    max : bpy.props.FloatProperty(
        name=translate("Max Value"),
        default=50,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        update= min_max_upd,
        )

    val : bpy.props.FloatProperty(
        name=translate("Max Value"),
        default=50,
        min=-20,
        max=120,
        subtype='PERCENTAGE',
        update= max_fall_upd,
        )

    fal : bpy.props.FloatProperty(
        name=translate("Falloff"),
        default=0.05,
        min=-0.50,
        max=0.50,                    
        update= max_fall_upd,
        )

    preset : bpy.props.EnumProperty(
        name = translate("Curve Mapping Preset Operations"), 
        default = "preset_linear",
        items = [
            ( "preset_linear"  ,translate("Linear")                ,"",),
            ( "preset_soft"    ,translate("Soft")                  ,"",),
            ( "preset_parabola",translate("Parabola")              ,"",),
            ( "preset_central" ,translate("Central")               ,"",),
            ( "preset_frame"   ,translate("Frame")                 ,"",),
            ( "preset_circle"  ,translate("Circle")                ,"",),
            ( "random"         ,translate("Random (parametric)")   ,"",),
            ( "sinus"          ,translate("Sinus (parametric)")    ,"",),
            ( "stratas"        ,translate("Quantize (parametric)") ,"",),
            ],
        )

    random : bpy.props.IntProperty(
        name=translate("Points"),
        default=10, 
        min=2, 
        soft_max=20, 
        max=300,
        )

    sinus : bpy.props.IntProperty(
        name=translate("Cycles"),
        default=2,
        min=1,
        soft_max=20,
        max=100,
        )

    stratas : bpy.props.IntProperty(
        name=translate("Steps"),
        default=7, 
        min=2, 
        soft_max=20, 
        max=100,
        )

    op_move : bpy.props.FloatProperty(
        default=0.03,
        min=0,
        soft_max=1,
        )
    
    op_size : bpy.props.FloatProperty(
        default=1.1,
        min=0,
        soft_max=10,
        )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):

        #set vg active if mask here
        if self.mask_name:
            utils.vg_utils.set_vg_active_by_name(bpy.context.scene.scatter5.emitter, self.mask_name)
        
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        layout = self.layout
        
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 

        mod = eval(self.source_api)

        box, is_open = templates.sub_panel(self, layout,         
            prop_str   = "masks_f_sub1", 
            icon       = "FCURVE", 
            name       = translate("Values Graph"), 
            panel      = "SCATTER5_PT_graph_subpanel",
            context_pointer_set = [["dialog",self],], 
            )
        if is_open:

                row = box.row()
                tr = row.row()
                app = row.row().column(align=True)
                t = tr.column()

                #draw main graph template, depending if is from map curve modifier or geometry float remap node 
                if (".node_group.nodes['" in self.source_api):
                      t.template_curve_mapping(mod, "mapping")
                else: t.template_curve_mapping(mod, "map_curve")

                t.separator(factor=0.5)

                app.scale_y = 0.8
                app.separator(factor=3)
                
                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_MOVE_LEFT"))
                op.description = translate("move the graph on the x axis by step value on chosen direction")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "move_left"    
                op.op_move = self.op_move  
                #   
                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_MOVE_RIGHT"))
                op.description = translate("move the graph on the x axis by step value on chosen direction")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "move_right"    
                op.op_move = self.op_move  

                app.separator()
                
                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_SIZE_UP"))
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_upsize"    
                op.op_size = self.op_size  
                #
                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_SIZE_DOWN"))
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_downsize"    
                op.op_size = self.op_size  

                app.separator()

                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_REVERSE_X"))
                op.description = translate("reverse the graph on given axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_reverse"    
                #
                op= app.operator("scatter5.graph_operations",text="",icon_value=cust_icon("W_REVERSE_Y"))
                op.description = translate("reverse the graph on given axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "y_reverse"    

                app.separator()

                op= app.operator("scatter5.graph_operations",text="",icon="MOD_MIRROR")
                op.description = translate("everything that is on the left of the axis X=0.5 will be mirrored on the other side")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "x_symetry"    

                op= app.operator("scatter5.graph_operations",text="",icon="COMMUNITY")
                op.description = translate("Will make a copy of the graph and put it right behind itself on +x axis")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "conga"   

                app.separator()

                op= app.operator("scatter5.graph_operations",text="",icon="HANDLE_VECTOR")
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "handle_vector"    
                #
                op= app.operator("scatter5.graph_operations",text="",icon="HANDLE_ALIGNED")
                op.description = translate("resize the graph with given factor")
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset  = "handle_bezier"    

                #Set Up Preset/Apply Preset 

                col = box.column(align=True)
                
                lbl = col.row()
                lbl.active = False
                lbl.label(text=translate("Set-Up Graph Presets :"))

                #
                col.scale_y = 0.85
                row = col.row(align=True)
                row1 = row.row(align=True)
                row1.scale_x = 0.6
                row1.prop(self,"preset",text='')
                #
                row2 = row.row(align=True)
                row2.scale_x = 0.4
                op = row2.operator("scatter5.graph_apply_preset", text=translate("apply"))
                op.source_api = self.source_api
                op.mapping_api = self.mapping_api
                op.preset = self.preset
                op.random = self.random
                op.sinus = self.sinus
                op.stratas = self.stratas

                if self.preset=="random":
                    col.prop(self,"random")
                elif self.preset=="stratas":
                    col.prop(self,"stratas")
                elif self.preset=="sinus":
                    col.prop(self,"sinus")

                #Set Up Min/Max

                col = box.column(align=True)
                
                lbl = col.row()
                lbl.active = False
                lbl.label(text=translate("Set-Up Graph from Min/Max values"))

                col.scale_y = 0.85
                col.prop(self,"min",slider=True)
                col.prop(self,"max",slider=True)

                #Set Up Max/Falloff

                col = box.column(align=True)

                lbl = col.row()
                lbl.active = False
                lbl.label(text=translate("Set-Up Graph from Max/Falloff values"))

                col.scale_y = 0.85
                col.prop(self,"val",slider=True)
                col.prop(self,"fal",slider=True)

                box.separator(factor=0.5)

        layout.separator()
        
        return 



#       .o.                             oooo                   ooooooooo.                                             .
#      .888.                            `888                   `888   `Y88.                                         .o8
#     .8"888.     oo.ooooo.  oo.ooooo.   888  oooo    ooo       888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#    .8' `888.     888' `88b  888' `88b  888   `88.  .8'        888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#   .88ooo8888.    888   888  888   888  888    `88..8'         888          888     888ooo888 `"Y88b.  888ooo888   888
#  .8'     `888.   888   888  888   888  888     `888'          888          888     888    .o o.  )88b 888    .o   888 .
# o88o     o8888o  888bod8P'  888bod8P' o888o     .8'          o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"
#                  888        888             .o..P'
#                 o888o      o888o            `Y8P'



preset_linear     = ([0.000,0.000], [1.000,1.000], )
preset_soft       = ([0.000,0.000], [0.450,0.800], [0.950,1.000], )
preset_parabola   = ([0.250,0.500], [0.500,0.250], [0.750,0.500], )
preset_central    = ([0.025,1.000], [0.250,0.000], [0.500,1.000], [0.750,0.000], [0.975,1.000], )
preset_sinusoidal = ([0.000,0.000], [0.250,1.000], [0.750,0.000], [1.000,1.000], )
preset_frame      = ([0.053,0.453], [0.124,0.000], [0.478,0.667], [1.000,1.000], )
preset_plateau    = ([0.011,0.000], [0.257,0.000], [0.263,1.000], [0.739,1.000], [0.743,0.000], [1.000,0.000], )
preset_circle     = ([0.000,0.000], [0.500,0.900], [1.000,0.000], )
preset_hacksaw    = ([0.000,0.803], [0.150,0.000], [0.250,1.000], [0.375,0.000], [0.500,1.000], [0.633,0.000], [0.750,0.983], [0.880,0.000], [0.989,1.000], )


def apply_given_preset(curve, preset, arg=None):
    """update modifier edit curve with custom preset matrix, note that it"""

    #clean points 

    if (len(curve.points)!=2):
        clean_all_points(curve)

    #execute preset 

    if preset.startswith("preset_"):

        exec(f'global {preset} ; apply_matrix(curve, {preset})')

        for p in curve.points:
            p.handle_type = 'AUTO'


    elif (preset=='random'):


        def get_random_matrix(ran):
            """ create rando graph"""

            matrix = []
            for _ in range(0,ran):
                x = round(random.uniform(0,1),3)
                y = round(random.uniform(0,1),3)
                matrix.append([x,y,'AUTO'])

            return matrix

        apply_matrix(curve, get_random_matrix(arg))


    elif (preset=='sinus'):


        def get_sinus_matrix(division):
            """create sinus graph"""

            steps_length = 1.0/division
            matrix  = []
            _ys = [0.5, 1, 0.5, 0,]* (division*4)
            _x  = 0

            parts = (division*4)+1
            #create matrix
            for i in range(parts):
                y = _ys[i]
                x = _x

                if not (i not in [0,parts-1] and y==0.5):
                    matrix.append([x,y,'AUTO'])

                _x += steps_length/4
                continue

            return matrix

        apply_matrix(curve, get_sinus_matrix(arg))


    elif (preset=='stratas'):


        def get_strata_matrix(steps):
            """create stratas (Linear Discretization)"""
            seg_x = 1.0/steps
            seg_y = 1.0/(steps-1)
            move    = 0.00001
            matrix  = []

            #create matrix
            for i in range(steps):

                _x = seg_x*i
                _y = seg_y*(i-1)
                if _y<0 or _x<0: continue 
                matrix.append([_x,_y,"VECTOR"])

                _x = (seg_x+move)*i  
                _y = seg_y*i
                if _y<0 or _x<0: continue 
                matrix.append([_x,_y,"VECTOR"])

            return matrix

        apply_matrix(curve, get_strata_matrix(arg))

        for p in curve.points:
            p.handle_type = 'VECTOR'

    #deselect all points 

    for p in curve.points:
        p.select = False

    return None


class SCATTER5_OT_graph_apply_preset(bpy.types.Operator):

    bl_idname = "scatter5.graph_apply_preset"
    bl_label = translate("Map-Curve Preset")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    preset : bpy.props.StringProperty()
    random : bpy.props.IntProperty()
    sinus : bpy.props.IntProperty()
    stratas : bpy.props.IntProperty()

    def execute(self, context):

        curve = eval(f"{self.mapping_api}.curves[0]")

        arg = None if self.preset.startswith("preset_") else self.random if (self.preset=="random") else self.sinus if (self.preset=="sinus") else self.stratas
        apply_given_preset(curve, self.preset, arg=arg)

        m = None 
        if (".node_group.nodes['" not in self.source_api):
            m = eval(self.source_api)
            m.falloff_type = 'CURVE'
        graph_update(map_curve=eval(self.mapping_api),remap_modifier=m)

        return {'FINISHED'}


#   .oooooo.                                         ooooooooo.                                             .
#  d8P'  `Y8b                                        `888   `Y88.                                         .o8
# 888           .ooooo.  oo.ooooo.  oooo    ooo       888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
# 888          d88' `88b  888' `88b  `88.  .8'        888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
# 888          888   888  888   888   `88..8'         888          888     888ooo888 `"Y88b.  888ooo888   888
# `88b    ooo  888   888  888   888    `888'          888          888     888    .o o.  )88b 888    .o   888 .
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'          o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"
#                         888       .o..P'
#                        o888o      `Y8P'


preset_buffer = None


class SCATTER5_OT_graph_copy_preset(bpy.types.Operator):

    bl_idname = "scatter5.graph_copy_preset"
    bl_label = translate("Copy/Paste Buffer")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    copy : bpy.props.BoolProperty()
    paste : bpy.props.BoolProperty()

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    def execute(self, context):

        global preset_buffer

        curve = eval(f"{self.mapping_api}.curves[0]")

        #copy

        if self.copy: 
            preset_buffer = get_matrix(curve)

        #paste 

        elif self.paste:

            if preset_buffer is None:
                return {'FINISHED'}

            clean_all_points(curve)
            apply_matrix(curve, preset_buffer)

            #update
            for p in curve.points:
                p.select = False

            m = None 
            if (".node_group.nodes['" not in self.source_api):
                m = eval(self.source_api)
            graph_update(map_curve=eval(self.mapping_api),remap_modifier=m)

        return {'FINISHED'}


#   .oooooo.                                  oooo               .oooooo.                                               .    o8o
#  d8P'  `Y8b                                 `888              d8P'  `Y8b                                            .o8    `"'
# 888           oooo d8b  .oooo.   oo.ooooo.   888 .oo.        888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
# 888           `888""8P `P  )88b   888' `88b  888P"Y88b       888      888  888' `88b d88' `88b `888""8P `P  )88b    888   `888  d88' `88b `888P"Y88b  d88(  "8
# 888     ooooo  888      .oP"888   888   888  888   888       888      888  888   888 888ooo888  888      .oP"888    888    888  888   888  888   888  `"Y88b.
# `88.    .88'   888     d8(  888   888   888  888   888       `88b    d88'  888   888 888    .o  888     d8(  888    888 .  888  888   888  888   888  o.  )88b
#  `Y8bood8P'   d888b    `Y888""8o  888bod8P' o888o o888o       `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" o888o `Y8bod8P' o888o o888o 8""888P'
#                                   888                                      888
#                                  o888o                                    o888o


class SCATTER5_OT_graph_operations(bpy.types.Operator):

    bl_idname = "scatter5.graph_operations"
    bl_label = translate("Graph Operations")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO_GROUPED'}

    source_api : bpy.props.StringProperty()
    mapping_api : bpy.props.StringProperty()

    preset : bpy.props.StringProperty()
    description : bpy.props.StringProperty()

    op_move : bpy.props.FloatProperty()
    op_size : bpy.props.FloatProperty()

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        curve = eval(f"{self.mapping_api}.curves[0]")

        for p in curve.points:
            p.select = False

        #operations:
        
        if self.preset == 'move_left':
            move_whole_graph(curve, direction="LEFT", step=self.op_move)

        elif self.preset == 'move_right':
            move_whole_graph(curve, direction="RIGHT", step=self.op_move)

        elif self.preset == 'x_reverse':
            for p in curve.points:
                p.location.x = 1-p.location.x

        elif self.preset == 'y_reverse':
            for p in curve.points:
                p.location.y = 1-p.location.y

        elif self.preset == 'x_upsize':
            for p in curve.points:
                p.location.x = p.location.x*self.op_size

        elif self.preset == 'x_downsize':
            for p in curve.points:
                p.location.x = p.location.x/self.op_size

        elif self.preset == 'handle_bezier':
            for p in curve.points:
                p.handle_type = 'AUTO'

        elif self.preset == 'handle_vector':
            for p in curve.points:
                p.handle_type = 'VECTOR'

        elif self.preset == 'conga':
            mA = get_matrix(curve)
            mA_length = abs(mA[-1][0]-mA[0][0])
            mB = [[ m[0] + mA_length ,m[1] ] for m in mA]
            mC = mA + mB
            #avoid doubles
            matrix = []
            for p in mC:
                if p not in matrix:
                    matrix.append(p)
            apply_matrix(curve, matrix)

        elif self.preset == 'x_symetry':
            matrix = get_matrix(curve)
            half=[]
            for x,y in matrix:
                if x<0.5:
                    half.append([x,y])
            new=[]
            new+=half
            for x,y in half:
                _x = 1-x
                new.append([_x,y])
            clean_all_points(curve)
            apply_matrix(curve, new)

        #update
        for p in curve.points:
            p.select = False

        m = None 
        if (".node_group.nodes['" not in self.source_api):
            m = eval(self.source_api)
        graph_update(map_curve=eval(self.mapping_api),remap_modifier=m)

        return {'FINISHED'}




#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


classes = [
            SCATTER5_OT_graph_apply_preset,
            SCATTER5_OT_graph_copy_preset,
            SCATTER5_OT_graph_operations,
            SCATTER5_OT_graph_dialog,
            SCATTER5_OT_add_vg_edit,
          ]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    return 



#if __name__ == "__main__":
#    register()