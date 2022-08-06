
#bunch of fuctions i use when working with vertex-groups

import bpy 
import numpy as np
from mathutils.kdtree import KDTree

from . import override_utils
from . str_utils import word_wrap


def get_weight(o, vg_name, eval_modifiers=True):
    """get weight dict"""
    
    #eval modifiers
    if eval_modifiers == True:
           depsgraph = bpy.context.evaluated_depsgraph_get()
           eo = o.evaluated_get(depsgraph)
           ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else:  ob = o.data    

    #forced to loop, as we cannot foreach_get vertex weight in blender...
    w = {}
    for v in ob.vertices:
        w[v.index] = 0.0 
        #if vert have weight, then fill dict
        for g in v.groups:
            if o.vertex_groups[vg_name].index == g.group:
                w[v.index] = g.weight
    return w


def fill_vg(o, vg, fill, method="REPLACE", ):
    """fill vg from given values (can be int,float,list,np array,dict)"""

    #type is float/int/bool ? 
    if (type(fill) is int) or (type(fill) is float) or (type(fill) is bool):

        verts = [i for i,v in enumerate(o.data.vertices)]
        vg.add(verts, fill, method)

        return None 

    #type is array ? numpy ?
    elif (type(fill) is list) or (type(fill).__module__ == np.__name__):

        for i,v in enumerate(fill):
            vg.add([i], v, method) #TODO importve with for_each set method, now available perhaps?

        return None 

    #type is dict ? 
    elif (type(fill) is dict):

        for k,v in fill.items():
            vg.add([k], v, method)

        return None 

    return None 


def create_vg(o, vg_name, fill=None, method="REPLACE", set_active=True):
    """create or refresh vg with given value(s) if not None"""

    vg = o.vertex_groups.get(vg_name)
    if (not vg):
        vg = o.vertex_groups.new(name=vg_name)

    fill_vg(o, vg, fill, method=method)

    if set_active:
        o.vertex_groups.active_index = vg.index

    return vg 


def set_vg_active_by_name(o, group_name, mode="vg"):
    """Set vg active if exist"""

    if mode=="vg":
          groups = o.vertex_groups 
    else: groups = o.data.vertex_colors 

    if len(groups)==0 or (group_name not in groups):
        return None

    old_active_name = groups[groups.active_index].name

    for i,g in enumerate(groups):
        if (g.name == group_name):
            groups.active_index = i 

    return old_active_name


def reverse_vg(o,vg):
    """reverse vg with ops.vertex_group_invert()"""

    #override
    act,sel = override_utils.set_active_and_selection(o,[o])
    oan = set_vg_active_by_name(o,vg.name)

    bpy.ops.object.vertex_group_invert()

    #restore
    set_vg_active_by_name(o,oan)
    override_utils.set_active_and_selection(act,sel)

    return None


def smooth_vg(o, vg, intensity):
    """reverse vg with ops.vertex_group_invert()"""

    if not intensity:
        return None 

    #override
    act,sel = override_utils.set_active_and_selection(o,[o])
    rm, ro, rs = override_utils.set_mode(mode="PAINT_WEIGHT")
    oan = set_vg_active_by_name(o,vg.name)

    bpy.ops.object.vertex_group_smooth(factor=0.2,repeat=intensity)

    #restore
    set_vg_active_by_name(o,oan)
    override_utils.set_mode(mode=rm, active=ro, selection=rs, )
    override_utils.set_active_and_selection(act,sel)

    return None


def expand_weights(o, vg, iter=2):
    """expand given weight"""

    for i in range(iter):
        
        o.vertex_groups.active_index = vg.index
        me = o.data

        weights = [0.0] * len(me.vertices)
        for f in me.polygons:
            flag = False
            for vi in f.vertices:
                w = vg.weight(vi)
                if(w > 0.0):
                    flag = True
                    break
            if(flag):
                for vi in f.vertices:
                    weights[vi] = 1.0

        for i, w in enumerate(weights):
            vg.add([i], w, 'ADD', )

    return None 


def kd_trees_rays(ob, verts_idx=None, distance=1, offset=0):

    vert_len = len(ob.vertices)
    non_target = []
    w = [0.0] * vert_len
    Tree = KDTree(vert_len)

    for v in ob.vertices:
        if v.index in verts_idx:
            Tree.insert(v.co, v.index)
            w[v.index] = 1.0
        else:
            non_target.append(v)

    Tree.balance()

    for nb in non_target:
        fvs = Tree.find_range(nb.co, offset + distance)
        ds = []
        for fv, fi, fd in fvs:
            ds.append(fd)
        val = 0.0
        if(len(ds)):
            delta = (distance - offset)
            if delta!=0:
                val = 1.0 - ((min(ds) - offset) / delta)
        w[nb.index] = val

    return w


def is_vg_active(o, vg_name):

    if vg_name=="":
        return False
    
    if bpy.context.mode=="PAINT_WEIGHT":

        if vg_name not in o.vertex_groups:
            return False

        for i,vg in enumerate(o.vertex_groups):
            if (vg.name == vg_name):
                return i==o.vertex_groups.active_index 

    elif bpy.context.mode=="PAINT_VERTEX":

        if vg_name not in o.data.vertex_colors:
            return False

        for i,vg in enumerate(o.data.vertex_colors):
            if (vg.name == vg_name):
                return i==o.data.vertex_colors.active_index 

    return False


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P'


from .. resources.translate import translate


class SCATTER_OP_vg_transfer(bpy.types.Operator):

    bl_idname  = "scatter5.vg_transfer"
    bl_label   = translate("Transfer Weight from source to destination")
    bl_options = {'REGISTER', 'INTERNAL'}


    obj_name : bpy.props.StringProperty()
    vg_source : bpy.props.StringProperty()
    vg_destination : bpy.props.StringProperty()
    display_des : bpy.props.BoolProperty()
    method : bpy.props.EnumProperty(
        items=[('ADD',translate('Add'),''),('SUBTRACT',translate('Substract'),''),('REPLACE',translate('Replace'),''),],
        default='REPLACE')
    eval_mod : bpy.props.BoolProperty(
        description=translate("Try to evaluate modifiers that might affect vertex-group when transferring data from source to destination"),
        )

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return bpy.context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        if self.vg_source == "":
            return {'FINISHED'}
        if self.vg_destination == "":
            return {'FINISHED'}

        if self.obj_name:
              obj = bpy.data.objects[self.obj_name]
        else: obj = bpy.context.object

        w = get_weight(obj, self.vg_source, eval_modifiers=self.eval_mod )
        create_vg(obj, self.vg_destination, fill=w, method=self.method )

        #UNDO_PUSH 
        bpy.ops.ed.undo_push(message=translate("Transfer Weight"))

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        if self.obj_name:
              obj = bpy.data.objects[self.obj_name]
        else: obj = bpy.context.object

        layout.prop_search(self, "vg_source", obj, "vertex_groups", text=translate("source"))
        if self.display_des:
            layout.prop_search(self, "vg_destination", obj, "vertex_groups", text=translate("description"))

        layout.prop(self,"method",text=translate("Mix Mode"))
        layout.prop(self,"eval_mod",text=translate("Try to Evaluale Modifiers"))

        return 


class SCATTER_OP_vg_quick_paint(bpy.types.Operator):

    bl_idname  = "scatter5.vg_quick_paint"
    bl_label   = translate("Create a New Vertex-Data")
    bl_options = {'REGISTER', 'INTERNAL'}

    group_name : bpy.props.StringProperty()
    mode       : bpy.props.StringProperty() #vg/vcol
    api        : bpy.props.StringProperty()
    set_color  : bpy.props.FloatVectorProperty()
    
    new_name : bpy.props.StringProperty(name=translate("Name"),)

    def invoke(self, context, event):

        emitter = bpy.context.scene.scatter5.emitter

        if (self.mode =="vcol"):
              group = emitter.data.vertex_colors
        else: group = emitter.vertex_groups

        if (self.group_name==""):
            self.new_name="Vcol" if (self.mode =="vcol") else "Vgroup"
            return bpy.context.window_manager.invoke_props_dialog(self)
        else:
            self.execute(context)
            return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        
        scat_scene = bpy.context.scene.scatter5
        
        if (self.mode =="vcol") and len(scat_scene.emitter.data.vertex_colors)>8:
            col = layout.column()
            col.alert=True
            word_wrap(layout=col, active=True, alignment="CENTER", max_char=50, string=translate("Unfortunately, Blender do not allow creating more than 8 vertex-colors slot. If you find this annoying please inform the devs about this limitation."),)
            return None

        layout.use_property_split = True
        layout.prop(self,"new_name",)

        if (scat_scene.sec_emit_verts_max_allow and (len(scat_scene.emitter.data.vertices)>scat_scene.sec_emit_verts_max)):
            word_wrap(layout=layout, string=translate("This emitter mesh is too high poly!\nYou may experience slowdowns"), max_char=50,)
            layout.separator(factor=0.7)

        return None

    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter

        if (self.mode =="vcol"):
              group = emitter.data.vertex_colors
        else: group = emitter.vertex_groups

        #create new
        if (self.group_name==""):
            
            new = group.new(name=self.new_name)
            exec(f"{self.api}='{new.name}'")

            return {'FINISHED'}
        
        #or find & set active 
        set_vg_active_by_name(emitter, self.group_name, mode=self.mode)

        #set active obj
        bpy.context.view_layer.objects.active = emitter

        #go in paint mode
        if (bpy.context.mode=="OBJECT") or (self.mode=="vcol" and bpy.context.mode!="PAINT_VERTEX") or (self.mode=="vg" and bpy.context.mode!="PAINT_WEIGHT"):

            if (self.mode =="vcol"):
                bpy.ops.object.mode_set(mode="VERTEX_PAINT")
            elif (self.mode =="vg"):
                bpy.ops.object.mode_set(mode="WEIGHT_PAINT")

        #set color
        if (self.set_color!=(-1,-1,-1)):
            bpy.context.scene.tool_settings.unified_paint_settings.use_unified_color = True
            bpy.context.scene.tool_settings.unified_paint_settings.color = self.set_color
            self.set_color = (-1,-1,-1) #reset after use

        return {'FINISHED'}


classes = [

    SCATTER_OP_vg_transfer,
    SCATTER_OP_vg_quick_paint,

    ]