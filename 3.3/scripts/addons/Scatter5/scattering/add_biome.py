

import bpy, os, json, time
from pathlib import Path

from .. resources.translate import translate
from .. resources import directories

from .. import utils
from .. utils.str_utils import legal, word_wrap

from .. ui import templates

from . presetting import settings_to_dict, dict_to_json, json_to_dict
from . add_psy import get_estimated_preset_particle_count



# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo  .oooo.o
#  888oooo8    d88' `"Y8   888   d88(  "8
#  888    "    888         888   `"Y88b.
#  888         888   .o8   888 . o.  )88b
# o888o        `Y8bod8P'   "888" 8""888P'



def add_biome_layer( #add a new biome_layer, will also import the assets
    _emitter_name="", #if left none, will find active
    _psy_name="",
    _psy_color=(3,3,3),
    _preset_path="", #==.preset file path we'll use to scatter the object
    _blend_path="", #==.blend we use to import 
    _instance_names=[], #list of object names that we'll import from given blend path
    
    _use_biome_display=False, #biome display on creation system
    _s_display_method="",
    _s_display_placeholder_type="",
    _s_display_placeholder_scale=(0,0,0),
    _s_display_custom_placeholder_ptr="",
    
    _add_vg_mask="", #add mask on creation option? 
    ):

    scat_scene = bpy.context.scene.scatter5
    
    #found files? 
    if not os.path.exists(_preset_path):
        raise Exception(f"Preset path ''{_preset_path}'' Not found!")
    if not os.path.exists(_blend_path):
        raise Exception(f"Blend path ''{_blend_path}'' Not found!")

    #Get Emitter 
    emitter = bpy.data.objects.get(_emitter_name)
    if emitter is None:
        emitter = scat_scene.emitter
    if emitter is None: 
        raise Exception("No Emitter found")

    #import instances from blend if not already in file
    if (_s_display_custom_placeholder_ptr != ""):
        _instance_names.append(_s_display_custom_placeholder_ptr)
    instance_name_list = utils.import_utils.import_objects( _blend_path, _instance_names, link=(scat_scene.opt_import_method=="LINK"), )
    if ( instance_name_list==[None] ) or ( len(instance_name_list)==0 ) :
        raise Exception("No Instances found")

    #do the scattering
    bpy.ops.scatter5.add_psy_preset(
        psy_name = _psy_name,
        psy_color = _psy_color,
        emitter_name = emitter.name,
        instance_names = "_!#!_".join( instance_name_list ),
        use_asset_browser = False,
        json_path = _preset_path, #=-> Preset path
        from_biome = True,
        pop_msg = False, #disable all messaging
        )

    #after creation, need extra settings care? 
    if (_use_biome_display):

        #be careful the two creation display settings will interact with each other here 
        psy = emitter.scatter5.particle_systems[-1]
        psy.s_display_allow = scat_scene.s_display_biome_placeholder or scat_scene.s_display_allow

        if (scat_scene.s_display_biome_placeholder):
            
            if (_s_display_method != ""):
                psy.s_display_method = _s_display_method

        if (_s_display_method == "placeholder"):

            if (_s_display_placeholder_type != ""):
                psy.s_display_placeholder_type = _s_display_placeholder_type

            if (_s_display_placeholder_scale != (0,0,0)):
                psy.s_display_placeholder_scale = _s_display_placeholder_scale

        elif (_s_display_method == "placeholder_custom"):

            if (_s_display_custom_placeholder_ptr != ""):
                psy.s_display_custom_placeholder_ptr = bpy.data.objects.get(_s_display_custom_placeholder_ptr)
        
    if (_add_vg_mask): #add mask:

        psy = emitter.scatter5.particle_systems[-1]
        psy.s_mask_vg_allow = True
        psy.s_mask_vg_ptr = _add_vg_mask
        psy.s_mask_vg_revert = True
        psy.hide_viewport = False #Unihide at last moment for optimization purpose

    return True 

def get_json_instance_name_list(d,):
    """get instance list information from json dict"""

    return  list(d["instances"]) if (d["instances"] is str) else d["instances"] #either store list of names or just name in json.

def search_for_dictpath_in_library(path_name="", biome_path="", is_blend=False, raise_exception=False, pop_msg=False, ):
    """search for the path of given basename from json dict"""

    if (is_blend) and (not path_name.endswith(".blend")):
        path_name = f"{path_name}.blend" 

    #using basename shortcut? 
    if ("BASENAME" in path_name):
        biome_basename = os.path.basename(biome_path).replace(".biome","") 
        path_name = path_name.replace("BASENAME", biome_basename,)
    
    #get extention
    path_ext = "."+path_name.split(".")[-1]

    #search everywhere, first in own directory
    search_first = os.path.dirname(biome_path) #Folder where json is, need to search for files first in here
    full_path = utils.path_utils.search_for_path( directories.lib_library, path_name, path_ext, search_first=search_first),   

    #somethime the function search_for_path() return tuple, i suspect that this is a python bug because it's extremely strange
    if type(full_path) is not str:
        full_path = full_path[0]

    #file don't exists?
    if not os.path.exists(full_path):
        if raise_exception:
            raise Exception(f"Missing File Error. We did not found '{path_name}' in your scatter library folder. did you change/misinstall some library files?")
        elif pop_msg:
            bpy.ops.scatter5.popup_dialog(('INVOKE_DEFAULT'),
                msg=f"We did not found\n'{path_name}'\nin your scatter library folder.\ndid you change something in your library?\ndid you install the library correctly?\n ", 
                header_title=translate("Missing File Error"),
                header_icon="LIBRARY_DATA_BROKEN",
                )
        return None, None

    return path_name, full_path


#       .o.             .o8        .o8       oooooooooo.   o8o
#      .888.           "888       "888       `888'   `Y8b  `"'
#     .8"888.      .oooo888   .oooo888        888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.
#    .8' `888.    d88' `888  d88' `888        888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b
#   .88ooo8888.   888   888  888   888        888    `88b  888  888   888  888   888   888  888ooo888
#  .8'     `888.  888   888  888   888        888    .88P  888  888   888  888   888   888  888    .o
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'


class SCATTER5_OT_add_biome(bpy.types.Operator): 
    """add a new biome file to given emitter object, prefer to use this operator when scripting, SCATTER5_OT_load_biome is for GUI only""" 

    bl_idname      = "scatter5.add_biome"
    bl_label       = "Add Biome from a .biome file" 
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    path : bpy.props.StringProperty()
    emitter_name : bpy.props.StringProperty() #override active emitter?

    def execute(self, context):

        #found files? 
        if not os.path.exists(self.path):
            raise Exception(f"Biome path ''{self.path}'' Not found!")

        scat_scene = bpy.context.scene.scatter5

        #Get Emitter 
        emitter    = bpy.data.objects.get(self.emitter_name)
        if emitter is None:
            emitter = scat_scene.emitter
        if emitter is None: 
            raise Exception("No Emitter found")

        #Read json info 
        with open(self.path) as f:
            d = json.load(f)

        #add biomes layers one by one
        for i, (key, value) in enumerate(d.items()):

            #ignore info dict
            if key=="info":
                continue 
                    
            #if is digit, that mean we got a layer dict
            if key.isdigit():
                
                #get layer preset path
                d_preset, json_preset_path = search_for_dictpath_in_library(path_name=value["preset"], biome_path=self.path, raise_exception=True,)

                #get layer blend path
                d_blend, json_blend_path = search_for_dictpath_in_library(path_name=value["asset_file"], is_blend=True, biome_path=self.path, raise_exception=True,)

                #get display settings 
                bdis = value.get("display")

                add_biome_layer(
                    _emitter_name = emitter.name,
                    _psy_name = value["name"],
                    _psy_color = value["color"],
                    _preset_path = json_preset_path,
                    _blend_path = json_blend_path,
                    _instance_names = get_json_instance_name_list(value),

                    _use_biome_display = bool(bdis),
                    _s_display_method = bdis["s_display_method"] if bool(bdis) else "",
                    _s_display_placeholder_type = bdis["s_display_placeholder_type"] if bool(bdis) and ("s_display_placeholder_type" in bdis) else "",
                    _s_display_placeholder_scale = bdis["s_display_placeholder_scale"] if bool(bdis) and ("s_display_placeholder_scale" in bdis) else (0,0,0),
                    _s_display_custom_placeholder_ptr = bdis["s_display_custom_placeholder_ptr"] if bool(bdis) and ("s_display_custom_placeholder_ptr" in bdis) else "",

                    _add_vg_mask = "",
                    )
                continue

            #apply material option? 
            if key.startswith("material"):

                #get blend path
                d_blend, material_blend_path = search_for_dictpath_in_library(path_name=value["material_file"], is_blend=True, biome_path=self.path, raise_exception=True,)

                #import material & import 
                mats = utils.import_utils.import_materials( material_blend_path, [value["material_name"]], link=(scat_scene.opt_import_method=="LINK"), )
                mat = bpy.data.materials.get(mats[0])
                if mat: 
                    if emitter.data.materials:
                          emitter.data.materials[0] = mat
                    else: emitter.data.materials.append(mat)

                continue

            # #if script, execute script
            # if key.startswith("script"):
            #     continue 

            continue 

        return {'FINISHED'}


# ooooo                                  .o8      oooooooooo.   o8o
# `888'                                 "888      `888'   `Y8b  `"'
#  888          .ooooo.   .oooo.    .oooo888       888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.
#  888         d88' `88b `P  )88b  d88' `888       888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b
#  888         888   888  .oP"888  888   888       888    `88b  888  888   888  888   888   888  888ooo888
#  888       o 888   888 d8(  888  888   888       888    .88P  888  888   888  888   888   888  888    .o
# o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P"     o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'
#                                                


class SCATTER5_OT_load_biome(bpy.types.Operator): 
    """same as 'add_biome()', with added layer of complexity for displaying ctrl menu and progress bar system""" 

    bl_idname      = "scatter5.load_biome"
    bl_label       = "Add Biome from a .biome file, this version use a modal method that give a progress feedback" 
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty()
    json_path : bpy.props.StringProperty() #=.biome path -> Mandatory arg
    single_layer : bpy.props.IntProperty(default=-1) #optional load single layer, set -1 to ignore 

    def __init__(self):
        self.Operations = None
        self.step = 0
        self.timer = None
        self.done = False
        self.max_step = None
        self.timer_count = 0

    @classmethod
    def description(cls, context, properties): 

        self=properties
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        e = bpy.context.window_manager.scatter5.library[self.json_path]
        description = '\n \u2022 '.join([ 
            translate("Information about this .biome file:"),
            #f'{translate("Name")} : {e.user_name}',
            f'{translate("Layers")} : {e.layercount}',
            f'{translate("Estimated Density")} : {round(e.estimated_density,1):,} P/m²',
            f'{translate("Estimated Count")} : {int(e.estimated_density*emitter.scatter5.estimated_square_area):,} P', #This is a naive estimation... what about per vertex/faces distribution method? ideally should use `get_estimated_preset_particle_count()` anyhow, might not be worth it, as 99.9% of users biomes will be compatible
            f'{translate("Author")} : {e.author}',
            f'{translate("Website")} : {e.website}',
            f'{translate("Keywords")} : {e.keywords}',
            f'{translate("Description")} : {e.description}',
            ])
        return description

    def invoke(self, context, event):
        
        scat_scene = bpy.context.scene.scatter5

        # Not likely to happend 
        if not os.path.exists(self.json_path):
            raise Exception("Json path don't exists?")

        ######### Prepare Step Separation 

        #Get Emitter 
        emitter = bpy.data.objects.get(self.emitter_name)
        if emitter is None:
            emitter = scat_scene.emitter
        if emitter is None: 
            return {'FINISHED'}
        psys = emitter.scatter5.particle_systems

        #Read json info 
        with open(self.json_path) as f:
            d = json.load(f)

        #Build all the different operations functions, 
        #then store them in a dictionary 'Operations'
        #==Same All steps 'add_biome()'' are segemnted into functions
        #https://blender.stackexchange.com/questions/3219/how-to-show-to-the-user-a-progression-in-a-script/231693#231693
            
        self.Operations = {}

        ######### Import all assets at once function, add_biome_layer() fct do this already per layer, but we need a faster solution 

        to_import = {} #key= blendpaths | values= list of asset names

        #this is an important optimization here, as we assemble all assets coming from same blend in one and only operation
        for key, value in d.items():

                if key.isdigit():

                    #get layer blend path
                    d_blend, json_blend_path = search_for_dictpath_in_library(path_name=value["asset_file"], is_blend=True, biome_path=self.json_path, pop_msg=True,)
                    if json_blend_path is None:
                        return {'FINISHED'} 

                    #generate import list if asset not found if current scene
                    for n in get_json_instance_name_list(value):
                        if n not in bpy.data.objects:
                            if json_blend_path not in to_import.keys():
                                to_import[json_blend_path] = []
                            to_import[json_blend_path].append(n)

                    #add display custom ptr to import list too
                    if (scat_scene.s_display_biome_placeholder):
                        if ("display" in value):
                            dptr = value["display"].get("s_display_custom_placeholder_ptr")
                            if bool(dptr):
                                if json_blend_path not in to_import.keys():
                                    to_import[json_blend_path] = []
                                to_import[json_blend_path].append(dptr)
                    continue
                     
                continue

        #store function in dict 

        def import_all_assets_fct(): 
            if to_import!={}:
                for blendpath,assets in to_import.items():
                    utils.import_utils.import_objects( blendpath, assets, link=(scat_scene.opt_import_method=="LINK"), )
            return None 
        self.Operations[f"Import"] = import_all_assets_fct

        #directly start painting?

        vg_name = ""
        if (scat_scene.opt_mask_assign_method=="paint"):
            vg = emitter.vertex_groups.new()
            vg_name = vg.name

        #Security check confirm?

        max_count = -1
        total_count = 0

        ######### Add new Layer Function   

        layer_count = 1
        for i, (key, value) in enumerate(d.items()):

            #ignore info dict
            if key=="info":
                continue 

            #single layer option? (ctrl-click menu)
            if (self.single_layer!=-1):
                if (i!=self.single_layer):
                    continue

            #biome layer dict
            if key.isdigit():

                #get layer preset path
                d_preset, json_preset_path = search_for_dictpath_in_library(path_name=value["preset"], biome_path=self.json_path, pop_msg=True)
                if not json_preset_path:
                    return {'FINISHED'}

                #get layer blend path
                d_blend, json_blend_path = search_for_dictpath_in_library(path_name=value["asset_file"], is_blend=True, biome_path=self.json_path, pop_msg=True)
                if not json_blend_path:
                    return {'FINISHED'}

                #store particle count information for message
                pres = json_to_dict( path=os.path.dirname(json_preset_path), file_name=os.path.basename(json_preset_path))
                count = get_estimated_preset_particle_count(emitter, d=pres, refresh_square_area=i==1)
                total_count += count
                if max_count<count:
                    max_count=count

                #store function in dict 

                def generate_add_layer_fct(value, json_preset_path, json_blend_path, ):
                    def fct():

                        #get display settings 
                        bdis = value.get("display")

                        add_biome_layer(
                            _emitter_name = emitter.name,
                            _psy_name = value["name"],
                            _psy_color = value["color"],
                            _preset_path = json_preset_path,
                            _blend_path = json_blend_path,
                            _instance_names = get_json_instance_name_list(value),

                            _use_biome_display = bool(bdis),
                            _s_display_method = bdis["s_display_method"] if bool(bdis) else "",
                            _s_display_placeholder_type = bdis["s_display_placeholder_type"] if bool(bdis) and ("s_display_placeholder_type" in bdis) else "", #bool(bdis) prevent key error in evaluation, otherwise would cause error
                            _s_display_placeholder_scale = bdis["s_display_placeholder_scale"] if bool(bdis) and ("s_display_placeholder_scale" in bdis) else (0,0,0),
                            _s_display_custom_placeholder_ptr = bdis["s_display_custom_placeholder_ptr"] if bool(bdis) and ("s_display_custom_placeholder_ptr" in bdis) else "",
                            
                            _add_vg_mask = vg_name,
                            )

                        return None
                    return fct

                self.Operations[f"Layer {int(layer_count)}"] = generate_add_layer_fct(value,json_preset_path,json_blend_path,)
                layer_count += 1
                continue 

            #apply material option? 
            if key.startswith("material"):

                #get blend path
                d_blend, material_blend_path = search_for_dictpath_in_library(path_name=value["material_file"], is_blend=True, biome_path=self.json_path, pop_msg=True,)
                if not json_blend_path:
                    return {'FINISHED'}

                def apply_material_fct():
                    #import material & apply dialog 
                    utils.import_utils.import_materials( material_blend_path, [value["material_name"]], link=(scat_scene.opt_import_method=="LINK"), )
                    default = ('INVOKE_DEFAULT') if value["confirm"] else ('EXEC_DEFAULT') 
                    bpy.ops.scatter5.material_confirm( default, obj_name=emitter.name, material_name=value["material_name"], )
                    return None
                self.Operations[f"Material"] = apply_material_fct
                continue

            # #if script, execute script
            # if key.startswith("script"):
            #     continue 

            continue

        #directly start painting?

        if vg_name:
            def start_painting_fct():
                bpy.ops.scatter5.vg_quick_paint(mode="vg",group_name=vg_name)
                return None 
            self.Operations[f"Start Painting"] = start_painting_fct

        #Security check confirm?

        if max_count>scat_scene.sec_emit_count:
            if scat_scene.sec_emit_count_allow:

                def warning_msg():
                    bpy.ops.scatter5.popup_dialog(("INVOKE_DEFAULT"),
                        header_title=translate("Security Treshold Reached"),
                        header_icon="FAKE_USER_ON",
                        msg="\n".join([
                            f"###ALERT###"+translate("Heavy Particle-Count Detected."), 
                            f"###ALERT###'{int(total_count):,}' "+translate("Particles Created in Total."), 
                            translate("Therefore Scatter5 automatically hide a scatter system. Please Be careful, displaying too many polygons in the viewport can freeze blender."),
                            "",
                            translate("Note that masks and optimization are not being taken into account during this estimation."),
                            "",
                            translate("You can change this behavior in the security treshold panel."),
                            "",
                            ]),
                        )                       
                    return None 

                self.Operations[f"Pop Message"] = warning_msg

        #We are ready to launch the modal mode

        #give context to progress bar 
        context.scene.scatter5.progress_context = self.json_path

        #set max step
        self.max_step = len(self.Operations.keys())        

        context.window_manager.modal_handler_add(self)
        
        #add timer to control running jobs activities 
        self.timer = context.window_manager.event_timer_add(0.01, window=context.window)

        return {'RUNNING_MODAL'}

    def restore(self, context):

        context.scene.scatter5.progress_bar = 0
        context.scene.scatter5.progress_label = ""
        context.scene.scatter5.progress_context = ""
        context.area.tag_redraw()

        context.window_manager.event_timer_remove(self.timer)
        
        self.done = False
        self.step = 0
        self.timer = None
        self.Operations = None

        return None 

    def update_progress(self,context):

        #update progess bar
        context.scene.scatter5.progress_bar = ((self.step+1)/(self.max_step+1))*100
        #update label
        context.scene.scatter5.progress_label = list(self.Operations.keys())[self.step] if (self.step<len(self.Operations.keys())) else translate("Done!")
        #send update signal
        context.area.tag_redraw()

        return None 

    def modal(self, context, event):

        #try except important here because restore() is essential to run
        try:

            #update gui as soon as we can
            self.update_progress(context)

            #by running a timer at the same time of our modal operator and catching timer event
            #we are guaranteed that update is done correctly in the interface, as timer event cannot occur when interface is frozen
            if (event.type != 'TIMER'):
                return {'RUNNING_MODAL'}
                
            #but wee need a little time off between timers to ensure that blender have time to breath
            #then are sure that interface has been drawn and unfrozen for user 
            self.timer_count +=1
            if self.timer_count!=10:
                return {'RUNNING_MODAL'}
            self.timer_count=0

            #if we are done, then make blender freeze a little so user can see final progress state
            #and very important, run restore function
            if (self.done):
                time.sleep(0.05)
                self.restore(context)
                return {'FINISHED'}
        
            if (self.step < self.max_step):
                #run step function
                list(self.Operations.values())[self.step]()
                #iterate over step, if last step, signal it
                self.step += 1
                if self.step==self.max_step:
                    self.done=True

                return {'RUNNING_MODAL'}

            return {'RUNNING_MODAL'}

        except Exception as e:
            self.restore(context)
            raise Exception(e)

        return {'FINISHED'}
 



class SCATTER5_OT_material_confirm(bpy.types.Operator):

    bl_idname = "scatter5.material_confirm"
    bl_label = translate("Would you want to apply a  new Material ?")
    bl_options = {'REGISTER', 'INTERNAL'}

    obj_name : bpy.props.StringProperty()
    material_name : bpy.props.StringProperty()

    def execute(self, context):

        emitter = bpy.data.objects.get(self.obj_name)
        mat = bpy.data.materials.get(self.material_name)

        if not emitter or not mat:
            return {'FINISHED'}    

        if emitter.data.materials:
              emitter.data.materials[0] = mat
        else: emitter.data.materials.append(mat)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=translate("There's a material associated with this ecosystem."))



#  .oooooo..o                                      oooooooooo.   o8o                                                                        oooo
# d8P'    `Y8                                      `888'   `Y8b  `"'                                                                        `888
# Y88bo.       .oooo.   oooo    ooo  .ooooo.        888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.        .oooo.    .oooo.o          888  .oooo.o  .ooooo.  ooo. .oo.
#  `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b       888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b      `P  )88b  d88(  "8          888 d88(  "8 d88' `88b `888P"Y88b
#      `"Y88b  .oP"888    `88..8'   888ooo888       888    `88b  888  888   888  888   888   888  888ooo888       .oP"888  `"Y88b.           888 `"Y88b.  888   888  888   888
# oo     .d8P d8(  888     `888'    888    .o       888    .88P  888  888   888  888   888   888  888    .o      d8(  888  o.  )88b          888 o.  )88b 888   888  888   888
# 8""88888P'  `Y888""8o     `8'     `Y8bod8P'      o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'      `Y888""8o 8""888P'      .o. 88P 8""888P' `Y8bod8P' o888o o888o
#                                                                                                                                        `Y888P


class SCATTER5_OT_save_biome_to_disk_dialog(bpy.types.Operator):

    bl_idname      = "scatter5.save_biome_to_disk_dialog"
    bl_label       = translate("Export Selected System(s) as Biome")
    bl_description = translate("")
    bl_options = {'REGISTER', 'INTERNAL'}

    method : bpy.props.EnumProperty( 
         default= "selection", 
         items= [ ("active",  translate("Active System"), "", 1 ),
                  ("selection",  translate("Selected System(s)"), "", 2 ),
                ],
         )

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter is not None)

    def invoke(self, context, event):
        bpy.context.scene.scatter5.biocrea_creation_steps=0
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout  = self.layout

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]

        bcol = layout.column(align=True)
        box, is_open = templates.sub_panel(self, bcol, 
            prop_str   = "add_preset_save", 
            icon       = "FILE_NEW", 
            name       = "         " + translate("Export Selected System(s) as Biome"),
            #description= "",
            #doc        = "I still need to write the docs, this plugin is currently in WIP and you are not using the final version ",
            )
        if is_open:

            sep = box.row()
            s1 = sep.separator(factor=0.2)
            s2 = sep.column()
            s3 = sep.separator(factor=0.2)

            s2.separator()

            steps = scat_scene.biocrea_creation_steps 
            BASENAME = legal(scat_scene.biocrea_biome_name.lower().replace(" ","_"))
            BLENDNAME = f"{BASENAME}.instances"

            def draw_steps(layout, smin=0,smax=2):

                lrow = layout.row()
                lrow1 = lrow.row()
                lrow2 = lrow.row()
                lrow3 = lrow.row()
                skip_prev = lrow2.row(align=True)
                
                op = skip_prev.row(align=True)
                op.enabled = steps!=smin
                operation = f"bpy.context.scene.scatter5.biocrea_creation_steps -=1"
                op.operator("scatter5.exec_line",text="",icon="REW",).api = operation
                
                if steps==smax:
                    txt = skip_prev.row(align=True)
                    txt.operator("scatter5.dummy",text=f"Step {smax+1}/{smax+1} - "+translate("Press 'OK'"),)
                else:
                    txt = skip_prev.row(align=True)
                    operation = f"bpy.context.scene.scatter5.biocrea_creation_steps +=1"
                    txt.operator("scatter5.exec_line",text=f"Step {steps+1}/{smax+1}",).api = operation
                   
                op = skip_prev.row(align=True)
                op.enabled = steps!=smax
                operation = f"bpy.context.scene.scatter5.biocrea_creation_steps +=1"
                op.operator("scatter5.exec_line",text="",icon="FF",).api = operation
                    
                layout.separator(factor=0.44)

                return 

            #step 1/3

            if steps==0:

                word_wrap(layout=s2, alignment="LEFT", max_char=55, string=translate("A Biome is a text file that bridge presets with assets.\nIn order to create a .biome file there's few steps we will need to follow.\nIf all steps are alreadyset-up for you, you can press 'OK' directly."),)

                s2.separator(factor=0.5)

                exp = s2.column(align=True)
                exp.label(text=translate("Biome Name")+":")
                exp.prop(scat_scene,"biocrea_biome_name",text="")

                s2.separator(factor=0.5)

                exp = s2.column(align=True)
                exp.label(text=translate("Export Directory")+":")
                exp.prop(scat_scene,"biocrea_creation_directory",text="")

                txt = s2.column()
                txt.scale_y = 0.8
                txt.active = False
                txt.separator(factor=1.5)
                txt.label(text="the scatter Biome Library is by default located in:")
                txt.operator("scatter5.open_directory", text=f"'{directories.lib_biomes}", emboss=False,).folder = directories.lib_biomes
                txt.label(text="You are free to create subfolders within this location.")

                s2.separator(factor=2.5)
                draw_steps(s2)

            #step 2/3

            elif steps==1:

                s2.prop(scat_scene,"biocrea_use_biome_display",)

                s2.prop(scat_scene,"biocrea_centralized_blend_allow",)
                if scat_scene.biocrea_centralized_blend_allow:
                    nr = s2.row()
                    nr1 = nr.row()
                    nr1.separator(factor=2)
                    nr2 = nr.row()
                    prp = nr2.column(align=True)

                    txt = prp.column(align=True)
                    txt.active = False
                    txt.label(text=translate("Name of your blend file:"))

                    prp.prop(scat_scene,"biocrea_centralized_blend",text="")

                    txt = prp.column(align=True)
                    txt.scale_y = 0.8
                    txt.separator()
                    txt.active = False
                    txt.label(text=translate("Don't forget to drop this file to your directory."))

                s2.separator()

                txt = s2.column(align=True)
                txt.scale_y = 0.8
                txt.label(text=translate("Scatter will create the Following Files :"))
                one_exists = False
                #biome file
                rtxt = txt.row()
                rtxt.active = False
                if os.path.exists(os.path.join(scat_scene.biocrea_creation_directory,f"{BASENAME}.biome")):
                    rtxt.alert = True
                    one_exists = True 
                rtxt.label(text=f" - ''{BASENAME}.biome''")
                #blend file
                if not scat_scene.biocrea_centralized_blend_allow:
                    rtxt = txt.row()
                    rtxt.active = False
                    if os.path.exists(os.path.join(scat_scene.biocrea_creation_directory,f"{BLENDNAME}.blend")):
                        rtxt.alert = True
                        one_exists = True 
                    rtxt.label(text=f" - ''{BLENDNAME}.blend''")
                for i,p in enumerate(psys):
                    PRESETNAME = f"{BASENAME}.layer{i:02}"
                    rtxt = txt.row()
                    rtxt.active = False
                    if os.path.exists(os.path.join(scat_scene.biocrea_creation_directory,f"{PRESETNAME}.preset")):
                        rtxt.alert = True
                        one_exists = True 
                    rtxt.label(text=f" - ''{PRESETNAME}.preset''")

                s2.separator()

                overw = s2.row()
                overw.alert = one_exists
                overw.prop(scat_scene,"biocrea_overwrite",)

                s2.separator()

                txt = s2.column(align=True)
                txt.scale_y = 0.8
                txt.label(text=translate("These Assets will be exported in new .blend :") if not scat_scene.biocrea_centralized_blend_allow else translate("These Assets needs to be in")+f" '{scat_scene.biocrea_centralized_blend}' :")
                blend_instance_obj_list = [o for p in psys for o in p.get_instances_obj()]
                blend_instance_obj_list = list(set(blend_instance_obj_list))
                for o in blend_instance_obj_list:
                    rtxt = txt.row()
                    rtxt.active = False
                    rtxt.label(text=f" - ''{o.name}''")

                if not scat_scene.biocrea_centralized_blend_allow:

                    s2.separator()
                    word_wrap(layout=s2, alignment="LEFT", max_char=55, string=translate("Please be aware that Scatter cannot export linked data!\nTo avoid problems, do not work with assets containing linked mesh/material/images/textures.. when creating your biome library."),)

                s2.separator()
                word_wrap(layout=s2, alignment="LEFT", max_char=55, string=translate("Note that it's best pack your image data in the .blend"))

                s2.separator(factor=2.5)
                draw_steps(s2)

            #step 3/3

            elif steps==2:

                txt = s2.column(align=True)
                txt.active = False
                txt.scale_y = 0.8
                txt.label(text=translate("Preset Generation Options :"))
                s2.separator(factor=0.5)

                s2.prop(scat_scene, "biocrea_use_random_seed",)
                s2.prop(scat_scene, "biocrea_texture_is_unique",)
                s2.prop(scat_scene, "biocrea_texture_random_loc",)

                s2.separator(factor=2)

                txt = s2.column(align=True)
                txt.active = False
                txt.scale_y = 0.8
                txt.label(text=translate("Biome Informations :"))
                s2.separator(factor=0.5)

                s2.prop(scat_scene,"biocrea_file_keywords")
                s2.prop(scat_scene,"biocrea_file_author")
                s2.prop(scat_scene,"biocrea_file_website")
                s2.prop(scat_scene,"biocrea_file_description")

                s2.separator(factor=2)
                                
                word_wrap(layout=s2, alignment="LEFT", max_char=55, string=translate("Icons can be generated afterwards with the thumbnail generator, available by CTRL clicking on a biome."))

                s2.separator(factor=1)

                s2.prop(scat_scene,"biocrea_auto_reload_all")

                s2.separator(factor=2.5)
                draw_steps(s2)


            templates.sub_spacing(box)
            layout.separator()

        return 


    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]
        
        #create biome directory if non existing
        if not os.path.exists(scat_scene.biocrea_creation_directory): 
            Path(scat_scene.biocrea_creation_directory).mkdir(parents=True, exist_ok=True)

        #get .biome file general info 
        biome_dict={}
        biome_dict["info"] = {}
        biome_dict["info"]["name"] = scat_scene.biocrea_biome_name
        biome_dict["info"]["type"] = "Biome"
        biome_dict["info"]["keywords"] = scat_scene.biocrea_file_keywords
        biome_dict["info"]["author"] = scat_scene.biocrea_file_author
        biome_dict["info"]["website"] = scat_scene.biocrea_file_website
        biome_dict["info"]["description"] = scat_scene.biocrea_file_description
        biome_dict["info"]["layercount"] = 0
        biome_dict["info"]["estimated_density"] = 0

        blend_instance_obj_list = []

        BASENAME = legal(scat_scene.biocrea_biome_name.lower().replace(" ","_"))
        BLENDNAME = f"{BASENAME}.instances"     #noted as "BASENAME.instances" within the text file -> no extension 
        
        #for all psys 
        for i,p in enumerate(psys): 

                #get file name
                PRESETNAME = f"{BASENAME}.layer{i:02}"  #noted as "BASENAME.layer00.preset" within the text file

                #gather instances
                psy_instance = p.get_instances_obj()
                #& add them to general list 
                if not scat_scene.biocrea_centralized_blend_allow:
                    blend_instance_obj_list += psy_instance

                #fill .biome file information
                ii = f"{i:02}"
                biome_dict[ii] = {}
                biome_dict[ii]["name"] = p.name
                biome_dict[ii]["color"] = tuple(p.s_color)[:3]
                biome_dict[ii]["preset"] = f"BASENAME.layer{i:02}.preset"
                biome_dict[ii]["instances"] = [o.name for o in psy_instance]
                biome_dict[ii]["asset_file"] = scat_scene.biocrea_centralized_blend.replace(".blend","") if (scat_scene.biocrea_centralized_blend_allow) else f"BASENAME.instances"

                #encode display placeholder? 
                if scat_scene.biocrea_use_biome_display:

                    biome_dict[ii]["display"] = {}
                    biome_dict[ii]["display"]["s_display_method"] = p.s_display_method
                    
                    if (p.s_display_method == "placeholder"):

                        biome_dict[ii]["display"]["s_display_placeholder_type"] = p.s_display_placeholder_type
                        biome_dict[ii]["display"]["s_display_placeholder_scale"] = tuple(p.s_display_placeholder_scale)
                    
                    elif (p.s_display_method == "placeholder_custom"):

                        if (p.s_display_custom_placeholder_ptr is not None):
                            biome_dict[ii]["display"]["s_display_custom_placeholder_ptr"] = p.s_display_custom_placeholder_ptr.name
                            if not scat_scene.biocrea_centralized_blend_allow:
                                blend_instance_obj_list.append(p.s_display_custom_placeholder_ptr)

                ######## WRITE PRESETS

                #export psy settings as new .preset 
                d = settings_to_dict(p,
                    use_random_seed=scat_scene.biocrea_use_random_seed,
                    texture_is_unique=scat_scene.biocrea_texture_is_unique,
                    texture_random_loc=scat_scene.biocrea_texture_random_loc,
                    ) 
                d["name"] = f""
                d["s_color"] = [0,0,0]

                #write psy settings a .preset file
                if os.path.exists( os.path.join(scat_scene.biocrea_creation_directory, f"{PRESETNAME}.preset")) and (not scat_scene.biocrea_overwrite):
                    bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Preset Creation Skipped"),icon="ERROR")
                    continue 
                dict_to_json( d, path=scat_scene.biocrea_creation_directory, file_name=PRESETNAME, extension=".preset",)

                #add to density information
                biome_dict["info"]["layercount"] +=1
                biome_dict["info"]["estimated_density"] += d["estimated_density"]

                continue

        ######## WRITE BLEND

        if not scat_scene.biocrea_centralized_blend_allow:
            #get .blend file path
            biome_blend_path = os.path.join( scat_scene.biocrea_creation_directory, f"{BLENDNAME}.blend",)
            #exists?
            if os.path.exists( biome_blend_path) and (not scat_scene.biocrea_overwrite):
                bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Biome Creation Skipped"),icon="ERROR")
                return {'FINISHED'} 
            blend_instance_obj_list = list(set(blend_instance_obj_list)) #remove double 
            
            utils.import_utils.export_objects( biome_blend_path, blend_instance_obj_list,)

        ######## WRITE BIOMES

        #get .biome file path
        biome_json_path = os.path.join( scat_scene.biocrea_creation_directory, f"{BASENAME}.biome",)
        #exists?
        if os.path.exists( biome_json_path) and (not scat_scene.biocrea_overwrite):
            bpy.ops.scatter5.popup_menu(msgs=translate("File already exists!\nOverwriting not allowed."),title=translate("Biome Creation Skipped"),icon="ERROR")
            return {'FINISHED'} 
        #write json file
        with open(biome_json_path, 'w') as f:
            json.dump(biome_dict, f, indent=4)

        #reload library
        if scat_scene.biocrea_auto_reload_all:
            bpy.ops.scatter5.reload_biome_library()

        return {'FINISHED'}



# oooooooooo.                                        .oo.          oooooooooo.
# `888'   `Y8b                                     .88' `8.        `888'   `Y8b
#  888      888 oooo d8b  .oooo.    .oooooooo      88.  .8'         888      888 oooo d8b  .ooooo.  oo.ooooo.
#  888      888 `888""8P `P  )88b  888' `88b       `88.8P           888      888 `888""8P d88' `88b  888' `88b
#  888      888  888      .oP"888  888   888        d888[.8'        888      888  888     888   888  888   888
#  888     d88'  888     d8(  888  `88bod8P'       88' `88.         888     d88'  888     888   888  888   888
# o888bood8P'   d888b    `Y888""8o `8oooooo.       `bodP'`88.      o888bood8P'   d888b    `Y8bod8P'  888bod8P'
#                                  d"     YD                                                         888
#                                  "Y88888P'                                                        o888o



# def add_jsonbiome_on_pointer_update(self, context):
#     return None 



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo.   ooo. .oo.  .oo.    .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88b  `P  )88b  `888P"Y88bP"Y88b  d88' `88b
#  888`88b.    888ooo888  888   888   .oP"888   888   888   888  888ooo888
#  888  `88b.  888    .o  888   888  d8(  888   888   888   888  888    .o
# o888o  o888o `Y8bod8P' o888o o888o `Y888""8o o888o o888o o888o `Y8bod8P'




class SCATTER5_OT_rename_biome(bpy.types.Operator): 
    """rename a biome json/files""" 

    bl_idname      = "scatter5.rename_biome"
    bl_label       = "Rename Operator" 
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    path : bpy.props.StringProperty()
    old_name : bpy.props.StringProperty()
    new_name : bpy.props.StringProperty(default="New Name")
    replace_files_names : bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        
        if not os.path.exists(self.path):
            raise Exception(f"Biome path ''{self.path}'' Not found!")   

        return bpy.context.window_manager.invoke_props_dialog(self)

    def get_linked_files(self):
        """return a list of all paths that scatter5 believe are linked with the given biome"""
            
        old_paths = []
        new_paths = []

        old_basename = os.path.basename(self.path).replace(".biome","")
        new_basename = self.new_name.replace(" ","_").lower()
        
        folder = os.path.dirname(self.path)

        for f in os.listdir(folder):
            if f.startswith(old_basename+"."):

                old_p = os.path.join(folder,f)
                old_paths.append(old_p)

                new_p_basename = f.replace(old_basename+".",new_basename+".")
                new_p = os.path.join(folder,new_p_basename)
                new_paths.append(new_p)

        return old_paths,new_paths

    def draw(self, context):
        layout  = self.layout

        box, is_open = templates.sub_panel(self, layout, 
            prop_str   = "add_preset_save", 
            icon       = "FONT_DATA", 
            name       = "         " + translate("Rename Biome"),
            description= "",
            )
        if is_open:

            prop = box.column(align=True)
            prop.label(text=translate("Old Name")+":")
            nm = prop.row()
            nm.enabled = False
            nm.prop(self,"old_name",text="",)

            prop = box.column(align=True)
            prop.label(text=translate("New Name")+":")
            prop.prop(self,"new_name",text="",)

            box.prop(self,"replace_files_names",text=translate("Also Replace Files Names"))

            lbl = box.column(align=True)
            lbl.scale_y = 0.8
            lbl.active = False
            lbl.label(text=" "+translate("Scatter5 will do the following operations:"))
            lbl.label(text="     \u2022 "+translate("Change the name information from:"))
            lbl.label(text=f"           '{os.path.basename(self.path)}'")

            if self.replace_files_names:
                for p in self.get_linked_files()[0]:
                    lbl.label(text=f"     \u2022 "+translate("Replace a file name."))
                    lbl.label(text=f"           '{os.path.basename(p)}'")

            lbl.separator()

            if self.replace_files_names:

                lbl = layout.column(align=True)
                lbl.active = False
                lbl.label(text=translate("Warning")+":",icon="ERROR")
                word_wrap( string=translate("Are you sure that this will not lead to dependencies issues?"), layout=layout, alignment="LEFT", max_char=50,)

        layout.separator()
        return 

    def execute(self, context):

        if (self.old_name.lower() == self.new_name.lower()) or (self.new_name==""):
            bpy.ops.scatter5.popup_menu(msgs=translate("Please choose a correct name"),title=translate("Renaming not possible"),icon="ERROR")
            return {'FINISHED'}      

        if self.replace_files_names:
            old_paths,new_paths = self.get_linked_files()
            
            for p in new_paths:
                if os.path.exists( p, ):
                    bpy.ops.scatter5.popup_menu(msgs=translate("There's already files with the following basename.")+f"\n {self.new_name.replace(' ','_').lower()}",title=translate("Renaming not possible"),icon="ERROR")
                    return {'FINISHED'}

        #Replace Biome Name 

        with open(self.path) as f:
            d = json.load(f)

        d["info"]["name"]=self.new_name.title()

        with open(self.path, 'w') as f:
            json.dump(d, f, indent=4)

        #change element name for live feedback

        bpy.context.window_manager.scatter5.library[self.path].user_name = self.new_name.title()

        #Replace File Names

        if self.replace_files_names:
            bpy.context.window_manager.scatter5.library[self.path].name = new_paths[0]
            for p,n in zip(old_paths,new_paths):
                os.rename(p,n)

        return {'FINISHED'}



classes = [
    
    SCATTER5_OT_add_biome,

    SCATTER5_OT_load_biome,
    SCATTER5_OT_material_confirm,
    
    SCATTER5_OT_save_biome_to_disk_dialog,
    
    SCATTER5_OT_rename_biome,

    ]