
#bunch of function that i store here because i do not know where to store them 

import bpy 
from .. resources.translate import translate


def dprint(string, depsgraph=False,):
    """debug print"""

    addon_prefs=bpy.context.preferences.addons["Scatter5"].preferences 

    if (not addon_prefs.debug_depsgraph) and depsgraph:  
        return
    if addon_prefs.debug:
        print(string)

    return None


def timer(fct):
    """timer decorator"""

    def wrapper(*args,**kwargs): 
        #get modules
        import time, datetime
        #launch timer
        _t = time.time()
        #exec fct
        print(f"@timer: launching '{fct.__name__}'")
        fct(*args,**kwargs) 
        #print timer
        _d = datetime.timedelta(seconds=time.time()-_t)
        print(f"@timer: '{fct.__name__}' executed in {_d}")
        return
    
    return wrapper


def all_3d_viewports():
    """return generator of all 3d view space"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        yield space


def all_3d_viewports_shading_type():
    """return generator of all shading type str"""

    for space in all_3d_viewports():
        yield space.shading.type


def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""

    return 'RENDERED' in all_3d_viewports_shading_type()


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_property_toggle(bpy.types.Operator):
    """useful for custom gui, as blender will register simple boolean toggle to undo history, this will fill user with tons of useless actions"""

    bl_idname      = "scatter5.property_toggle"
    bl_label       = ""
    bl_description = ""
    #DO NOT REGISTER TO UNDO HERE!!!

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="")

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        if self.api != "":
            addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
            exec(f'{self.api} = not {self.api}')

        return {'FINISHED'}


class SCATTER5_OT_dummy(bpy.types.Operator):
    """dummy place holder"""

    bl_idname      = "scatter5.dummy"
    bl_label       = ""
    bl_description = ""

    description : bpy.props.StringProperty(default="")

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):
        return {'FINISHED'}

        
class SCATTER5_OT_exec_line(bpy.types.Operator):
    """quickly execute simple line of code, witouth needing to create a new operator"""

    bl_idname      = "scatter5.exec_line"
    bl_label       = ""
    bl_description = ""

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="")

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 
        
        exec(self.api)

        return {'FINISHED'}


class SCATTER5_OT_set_solid_and_object_color(bpy.types.Operator):

    bl_idname      = "scatter5.set_solid_and_object_color"
    bl_label       = ""
    bl_description = translate("Set the context viewport shading type to solid/object to see the particle systems colors")

    mode : bpy.props.StringProperty() #"set"/"restore"
    
    restore_dict = {}

    def execute(self, context):

        space_data = bpy.context.space_data 
        spc_hash   = space_data.__hash__()
        shading    = space_data.shading

        if (self.mode=="set"):

            self.restore_dict[spc_hash] = {"type":shading.type, "color_type":shading.color_type}
            shading.type = 'SOLID'
            shading.color_type = 'OBJECT'

        elif (self.mode=="restore") and (spc_hash in self.restore_dict):

            shading.type = self.restore_dict[spc_hash]["type"]
            shading.color_type = self.restore_dict[spc_hash]["color_type"]
            del self.restore_dict[spc_hash]

        return {'FINISHED'}


class SCATTER5_OT_image_utils(bpy.types.Operator):

    bl_idname      = "scatter5.image_utils"
    bl_label       = translate("Create a New Image")
    bl_options = {'REGISTER', 'INTERNAL'}

    option : bpy.props.StringProperty() #enum in "open"/"new"/"paint"

    img_name : bpy.props.StringProperty(name=translate("Image Name"),)    
    api : bpy.props.StringProperty()
    paint_color : bpy.props.FloatVectorProperty()
    uv_ptr : bpy.props.StringProperty()

    #new dialog 
    res_x : bpy.props.IntProperty(default=1080, name=translate("resolution X"),)
    res_y : bpy.props.IntProperty(default=1080, name=translate("resolution Y"),)

    quitandopen : bpy.props.BoolProperty(default=False,name=translate("Open From Explorer"),)
    
    #open dialog
    filepath : bpy.props.StringProperty(subtype="DIR_PATH")

    @classmethod
    def description(cls, context, properties): 

        if (properties.option=="paint"):
            return translate("Start Painting")

        if (properties.option=="open"):
            return translate("Load Image File from Explorer")

        if (properties.option=="new"):
            return translate("Create Image Data")

        return ""

    def invoke(self, context, event):

        if (self.option=="paint"):
            self.execute(context)
            return {'FINISHED'}

        if (self.option=="open"):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}  

        if (self.option=="new"):
            self.img_name="ImageMask"
            return context.window_manager.invoke_props_dialog(self)

        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout
        
        layout.use_property_split = True
        layout.prop(self,"res_x")
        layout.prop(self,"res_x")
        layout.prop(self,"img_name")
        layout.prop(self,"quitandopen")     

        return None 

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter 
            
        if (self.option=="paint"):
            img = bpy.data.images.get(self.img_name)
            if img is None: 
                return {'FINISHED'}    
            bpy.context.view_layer.objects.active = emitter
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
            bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
            bpy.context.scene.tool_settings.image_paint.canvas = img
            bpy.context.scene.tool_settings.unified_paint_settings.color = self.paint_color
            uv_layer = bpy.context.object.data.uv_layers.get(self.uv_ptr)
            if uv_layer is None:
                return {'FINISHED'}
            bpy.context.object.data.uv_layers.active = uv_layer
            return {'FINISHED'}

        if (self.quitandopen):
            bpy.ops.scatter5.image_utils(('INVOKE_DEFAULT'),option="open", img_name=self.img_name, api=self.api,)
            return {'FINISHED'}

        if (self.option=="open"):
            img = bpy.data.images.load(filepath=self.filepath)
            exec( f"{self.api}=img.name" )
            return {'FINISHED'}

        if (self.option=="new"):
            img = bpy.data.images.new(self.img_name, self.res_x, self.res_y,)
            exec( f"{self.api}=img.name" )
            return {'FINISHED'}

        return {'FINISHED'}


class SCATTER5_OT_list_move(bpy.types.Operator):

    bl_idname      = "scatter5.list_move"
    bl_label       = translate("Move Item")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    direction : bpy.props.StringProperty(default="UP") #UP/DOWN
    target_idx : bpy.props.IntProperty(default=0)

    api_propgroup  : bpy.props.StringProperty(default="emitter.scatter5.mask_systems")
    api_propgroup_idx : bpy.props.StringProperty(default="emitter.scatter5.mask_systems_idx")

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter

        target_idx = self.target_idx
        current_idx = eval(f"{self.api_propgroup_idx}")
        len_propgroup = eval(f"len({self.api_propgroup})")

        if (self.direction=="UP") and (current_idx!=0):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}-1)")
            exec(f"{self.api_propgroup_idx} -=1")
            return {'FINISHED'}

        if (self.direction=="DOWN") and (current_idx!=len_propgroup-1):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}+1)")
            exec(f"{self.api_propgroup_idx} +=1")
            return {'FINISHED'}

        return {'FINISHED'}


classes = [
        
    SCATTER5_OT_property_toggle,
    SCATTER5_OT_dummy,
    SCATTER5_OT_exec_line,

    SCATTER5_OT_set_solid_and_object_color,
    SCATTER5_OT_image_utils,

    SCATTER5_OT_list_move,

    ]