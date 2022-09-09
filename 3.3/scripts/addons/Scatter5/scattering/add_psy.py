
#####################################################################################################
#
#       .o.             .o8        .o8       ooooooooo.
#      .888.           "888       "888       `888   `Y88.
#     .8"888.      .oooo888   .oooo888        888   .d88'  .oooo.o oooo    ooo
#    .8' `888.    d88' `888  d88' `888        888ooo88P'  d88(  "8  `88.  .8'
#   .88ooo8888.   888   888  888   888        888         `"Y88b.    `88..8'
#  .8'     `888.  888   888  888   888        888         o.  )88b    `888'
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o        8""888P'     .8'
#                                                                  .o..P'
#                                                                  `Y8P'
#####################################################################################################


import bpy, os, time, random

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.import_utils import import_selected_assets

from . import presetting
from . instances import find_compatible_instances

from .. ui.ui_creation import find_preset_name, find_preset_color


#       .o.             .o8        .o8       ooooooooo.                              .oooooo..o  o8o                               oooo
#      .888.           "888       "888       `888   `Y88.                           d8P'    `Y8  `"'                               `888
#     .8"888.      .oooo888   .oooo888        888   .d88'  .oooo.o oooo    ooo      Y88bo.      oooo  ooo. .oo.  .oo.   oo.ooooo.   888   .ooooo.
#    .8' `888.    d88' `888  d88' `888        888ooo88P'  d88(  "8  `88.  .8'        `"Y8888o.  `888  `888P"Y88bP"Y88b   888' `88b  888  d88' `88b
#   .88ooo8888.   888   888  888   888        888         `"Y88b.    `88..8'             `"Y88b  888   888   888   888   888   888  888  888ooo888
#  .8'     `888.  888   888  888   888        888         o.  )88b    `888'         oo     .d8P  888   888   888   888   888   888  888  888    .o
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o        8""888P'     .8'          8""88888P'  o888o o888o o888o o888o  888bod8P' o888o `Y8bod8P'
#                                                                  .o..P'                                                888
#                                                                  `Y8P'                                                o888o


class SCATTER5_OT_add_psy_simple(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_simple"
    bl_label       = translate("Add a Simple Particle-System")
    bl_description = translate("This operator will add a simple Particle-System, if objects are selected they will be your future instances, otherwise we will display a placeholder. Please use the scattering operator in the Creation panel for more options")
    bl_options     = {'INTERNAL','UNDO'}

    psy_name : bpy.props.StringProperty(default="Simple")
    psy_color : bpy.props.FloatVectorProperty(default=(1,1,1))
    psy_color_random : bpy.props.BoolProperty(default=False)
    emitter_name : bpy.props.StringProperty()
    instance_names : bpy.props.StringProperty()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5

        #Get Emitter 
        emitter = bpy.data.objects.get(self.emitter_name)
        if emitter is None: 
            emitter = scat_scene.emitter
        if emitter is None: 
            return {'FINISHED'}   

        #Correct if no name or empty name
        if (self.psy_name in [""," ","  ","   ","    "]): #meh
            self.psy_name = "No Name"

        #Get instances
        if self.instance_names:
              obj_list = [ bpy.data.objects[n] for n in self.instance_names.split("_!#!_") if n in bpy.data.objects ]
        else: obj_list = []
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))

        #random color 
        if self.psy_color_random:
            self.psy_color = [random.uniform(0, 1),random.uniform(0, 1),random.uniform(0, 1),]

        #create virgin psy
        p = emitter.scatter5.add_virgin_psy( psy_name=self.psy_name, psy_color=self.psy_color, instances=instances, deselect_all=True, )

        #ignore any tweaking behavior, such as update delay or hotkeys 
        old_factory_delay_allow , old_factory_event_listening_allow = scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow
        scat_scene.factory_delay_allow = scat_scene.factory_event_listening_allow = False

        p.s_distribution_density = 0.222
        p.s_distribution_is_random_seed = True
        p.hide_viewport = False

        #restore users tweaking behavior
        scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow 

        return {'FINISHED'}


#       .o.             .o8        .o8       ooooooooo.                             ooooooooo.                                             .
#      .888.           "888       "888       `888   `Y88.                           `888   `Y88.                                         .o8
#     .8"888.      .oooo888   .oooo888        888   .d88'  .oooo.o oooo    ooo       888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#    .8' `888.    d88' `888  d88' `888        888ooo88P'  d88(  "8  `88.  .8'        888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#   .88ooo8888.   888   888  888   888        888         `"Y88b.    `88..8'         888          888     888ooo888 `"Y88b.  888ooo888   888
#  .8'     `888.  888   888  888   888        888         o.  )88b    `888'          888          888     888    .o o.  )88b 888    .o   888 .
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o        8""888P'     .8'          o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"
#                                                                  .o..P'
#                                                                  `Y8P'

#Example 

# bpy.ops.scatter5.add_psy_preset(
#     psy_name="New Psy Test",
#     psy_color = (1,1,1),
#     emitter_name="Plane",
#     instance_names="Instance Cube_!#!_Suzanne_!#!_Cube",
#     use_asset_browser=False,
#     json_path="C:/Users/Dude/Desktop/testing.json",
#     from_biome = False,
#     pop_msg = False,
#     )


class SCATTER5_OT_add_psy_preset(bpy.types.Operator):
    """main scattering operator for user in 'Creation>Scatter' if running this from script, note that there are a few globals parameters that could have an influence over this operation, such as the security features"""

    bl_idname      = "scatter5.add_psy_preset"
    bl_label       = translate("Add a Particle-System from Chosen Preset")
    bl_description = translate("Scatter the selected mesh-objects with the active preset settings on the chosen emitter target object. A dialog box will pop-up with more creation options. Scatter will create a new particle-data that can have multiple emitter users.")
    bl_options     = {'INTERNAL','UNDO'}

    psy_name : bpy.props.StringProperty() #use "*AUTO*" to automatically find name and color
    psy_color : bpy.props.FloatVectorProperty(default=(1,1,1))
    emitter_name : bpy.props.StringProperty()
    instance_names : bpy.props.StringProperty() # list of object names separated with "_!#!_"
    use_asset_browser : bpy.props.BoolProperty() #use active asset #use active asset from asset browser instead of instance list?
    json_path : bpy.props.StringProperty() #string = json preset path, if not will use active preset
    from_biome : bpy.props.BoolProperty(default=False) #Some features/options cannot be used from here directly, but need to be called afterward
    pop_msg : bpy.props.BoolProperty(default=True)

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5

        #Get Emitter 

        emitter = bpy.data.objects.get(self.emitter_name)
        if emitter is None: 
            emitter = scat_scene.emitter
        if emitter is None: 
            return {'FINISHED'}          

        #Correct if no name or empty name

        if (self.psy_name in [""," ","  ","   ","    "]): #meh
            self.psy_name = "No Name"

        #Get instances

        if self.use_asset_browser:
              obj_list = import_selected_assets(link=(scat_scene.opt_import_method=="LINK"),)
        elif self.instance_names:
              obj_list = [ bpy.data.objects[n] for n in self.instance_names.split("_!#!_") if n in bpy.data.objects ]
        else: obj_list = []
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))

        #ERROR if no instances found 

        if (len(instances)==0):
            if self.pop_msg:
                msg = translate("No valid Object(s) found in Selection.") if (not self.use_asset_browser) else translate("No Asset(s) found in Asset-Browser.")
                bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        #automatic find name

        if (self.psy_name=="*AUTO*"):
            self.psy_name = find_preset_name(instances)
            self.psy_color = find_preset_color(instances)[0]

        #create virgin psy

        p = emitter.scatter5.add_virgin_psy( psy_name=self.psy_name, psy_color=self.psy_color, instances=instances, deselect_all=True, )

        #ignore any tweaking behavior, such as update delay or hotkeys 

        old_factory_delay_allow , old_factory_event_listening_allow = scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow
        scat_scene.factory_delay_allow = scat_scene.factory_event_listening_allow = False

        #load json preset to settings
        
        d = {}
        if not os.path.exists(self.json_path):

            #if not exists, inform users that no preset found 
            if self.pop_msg:
                bpy.ops.scatter5.popup_menu(msgs=translate("No Valid Preset Path Detected, We Scattered With Default Values")+f"\n {self.json_path}", title=translate("Warning"),icon="ERROR",)
        
        #else scatter with preset

        else:

            if (scat_scene.opt_mask_assign_method!="manual"):

                #paste preset to settings 

                path = os.path.dirname(self.json_path)
                file_name = os.path.basename(self.json_path)
                d = presetting.json_to_dict( path=path, file_name=file_name,)
                presetting.dict_to_settings( d, p,
                    filter={
                        "color":False,
                        "distribution":True,
                        "rot":True,
                        "scale":True,
                        "pattern":True,
                        "abiotic":True,
                        "proximity":True,
                        "ecosystem":True,
                        "push":True,
                        "wind":True,
                        "instances":True,
                        },
                    )

                #search and refresh ecosystem dependency if needed

                for ps in emitter.scatter5.particle_systems:

                    if ps.s_ecosystem_affinity_allow:

                        for i in (1,2,3):
                            ps_ptr = getattr(ps,f"s_ecosystem_affinity_{i:02}_ptr")
                            if (ps_ptr==p.name):
                                setattr(ps,f"s_ecosystem_affinity_{i:02}_ptr",ps_ptr)

                    if ps.s_ecosystem_repulsion_allow:

                        for i in (1,2,3):
                            ps_ptr = getattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr")
                            if (ps_ptr==p.name):
                                setattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr",ps_ptr)

        #Creation Settings Visibility/Display options

        #Viewport % Optimization
        if (scat_scene.s_visibility_view_allow):
            p.s_visibility_view_allow = True
            p.s_visibility_view_percentage = scat_scene.s_visibility_view_percentage
            
        #Camera Optimization
        if (scat_scene.s_visibility_cam_allow):
            p.s_visibility_cam_allow = True
            p.s_visibility_camclip_allow = scat_scene.s_visibility_camclip_allow
            p.s_visibility_camdist_allow = scat_scene.s_visibility_camdist_allow

            if p.s_visibility_camdist_allow:
                p.s_visibility_camdist_min = scat_scene.s_visibility_camdist_min 
                p.s_visibility_camdist_max = scat_scene.s_visibility_camdist_max 

        #Display as Optimization
        if (scat_scene.s_display_allow ):
            p.s_display_allow = True
            p.s_display_method = scat_scene.s_display_method
            if (p.s_display_method == "placeholder_custom"):
                p.s_display_custom_placeholder_ptr = scat_scene.s_display_custom_placeholder_ptr
            p.s_display_camdist_allow = scat_scene.s_display_camdist_allow

        #BoundingBox Display
        if (scat_scene.s_display_bounding_box):
            for o in instances:
                o.display_type="BOUNDS"

        #Lodify Display 
        if (scat_scene.s_display_enable_lodify):
            from..external import enable_lodify
            enable_lodify(instances, status= self.display_type=="LODIFY_ENABLE")

        #Creation Settings Synchronize (not used)
        #
        # if scat_scene.opt_sync_settings:
        #     if (p.name[-4]==".") and (p.name[-3:].isdigit()):
        #         #find if original particle system exists?
        #         initial_name = p.name[:-4]
        #         initial_emitter = None 
        #         for o in bpy.data.objects:
        #             if len(o.scatter5.particle_systems)!=0:
        #                 for p in o.scatter5.particle_systems:
        #                     if p.name == initial_name:
        #                         initial_emitter = p.id_data
        #         #if original psy system found 
        #         if initial_emitter is not None:
        #             #create new channel
        #             sync_channels= bpy.context.scene.scatter5.sync_channels
        #             if initial_name not in sync_channels:
        #                   ch = bpy.context.scene.scatter5.sync_channels.add()
        #                   ch.name= initial_name
        #             else: ch = sync_channels[initial_name]
        #             #add new members to channel
        #             if not ch.psy_in_channel(initial_emitter, initial_name):
        #                 mem = ch.members.add()
        #                 mem.psy_name = initial_name
        #                 mem.m_emitter = initial_emitter
        #             #add new members to channel
        #             if not ch.psy_in_channel(emitter.name, p.name):
        #                 mem = ch.members.add()
        #                 mem.psy_name = p.name
        #                 mem.m_emitter = emitter

        #Creation Settings Mask

        if (scat_scene.opt_mask_assign_method!="none"):

            #Assign selected masks on creation
            if (scat_scene.opt_mask_assign_method=="vg"):
                #find vg
                vg_name = scat_scene.opt_vg_assign_slot
                if (vg_name in emitter.vertex_groups):
                    #set vg pointer 
                    p.s_mask_vg_allow = True
                    p.s_mask_vg_ptr = vg_name
                    #special revert case for some parametric masks, camera ray by default need to be reverted
                    if vg_name.startswith("Camera Ray"):
                        p.s_mask_vg_revert = True

            #Directly Paint on creation
            elif (scat_scene.opt_mask_assign_method=="paint") and (not self.from_biome): #-> Biomes won't be supported, they need their own implementation
                vg = emitter.vertex_groups.new()
                p.s_mask_vg_allow = True
                p.s_mask_vg_ptr = vg.name
                p.s_mask_vg_revert = True
                bpy.context.view_layer.objects.active = emitter
                bpy.ops.paint.weight_paint_toggle()

            #Assign in new curve area mask on creation
            elif (scat_scene.opt_mask_assign_method=="curve") and (scat_scene.opt_mask_curve_area_ptr):          
                p.s_mask_curve_allow = True
                pass

            #Assign in manual, will be on virgin psy by default, with few rotation settings to adjust 
            elif (scat_scene.opt_mask_assign_method=="manual"):
                p.s_distribution_method = "manual_all"
                p.s_rot_align_z_allow = False
                p.s_rot_align_y_allow = False
                pass

        #Unhide at the end for Optimization + Control with Optimization Features

        is_visible = True
        
        #Visibility option Hide Viewport

        if is_visible and scat_scene.s_visibility_hide_viewport:
            is_visible = False

        #Special case if from_biome + paint mode, optimization required 

        elif (is_visible and self.from_biome and (scat_scene.opt_mask_assign_method=="paint")):
            is_visible = False            

        #Security Treshold Estimated Particle Count 

        if d!={} and (scat_scene.sec_emit_count_allow):

            particle_count = get_estimated_preset_particle_count(emitter, d=d, refresh_square_area=True)
            if particle_count > scat_scene.sec_emit_count:
                is_visible = False

                if self.pop_msg:
                    bpy.ops.scatter5.popup_dialog(("INVOKE_DEFAULT"),
                        header_title=translate("Security Treshold Reached"),
                        header_icon="FAKE_USER_ON",
                        msg="\n".join([
                            f"###ALERT###"+translate("Heavy Particle-Count Detected."), 
                            f"###ALERT###'{int(particle_count):,}' "+translate("Particles Created."), 
                            translate("Therefore Scatter5 automatically hide a scatter system. Please Be careful, displaying too many polygons in the viewport can freeze blender."),
                            "",
                            translate("Note that masks and optimization are not being taken into account during this estimation."),
                            "",
                            translate("You can change this behavior in the security treshold panel."),
                            "",
                            ]),
                        )

        #Security Treshold Instance Polycount 

        if scat_scene.sec_inst_verts_allow:

            too_high_poly = [ o for o in instances if (
                (o.type=="MESH")
                and (o.display_type != "BOUNDS")
                and (len(o.data.vertices)>=scat_scene.sec_inst_verts)
                )]

            if len(too_high_poly):

                max_poly = 0
                for o in too_high_poly:
                    polycount = len(o.data.vertices) 
                    if polycount>max_poly:
                        max_poly = polycount
                    o.display_type = "BOUNDS"
                    continue 

                #Note that this msg is not supported by biomes

                if self.pop_msg:
                    bpy.ops.scatter5.popup_dialog(("INVOKE_DEFAULT"),
                        header_title=translate("Security Treshold Reached"),
                        header_icon="FAKE_USER_ON",
                        msg="\n".join([
                            f"###ALERT###"+translate("Heavy Assets Detected."), 
                            f"###ALERT###"+translate("Some Assets reached")+f" {max_poly:,} verts",
                            translate("Therefore Scatter5 switched automatically the display type of your instances to 'Bounding Box' for you."),
                            "",
                            translate("Please Be careful, displaying too many polygons in the viewport can freeze blender."),
                            "",
                            translate("You can change this behavior in the security treshold panel."),
                            "",
                            ]),
                        )

        if is_visible:
            p.hide_viewport = False

        #restore users tweaking behavior
        scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow 

        return {'FINISHED'}


#       .o.             .o8        .o8       ooooo                   .o8   o8o               o8o        .o8                        oooo  oooo
#      .888.           "888       "888       `888'                  "888   `"'               `"'       "888                        `888  `888
#     .8"888.      .oooo888   .oooo888        888  ooo. .oo.    .oooo888  oooo  oooo    ooo oooo   .oooo888  oooo  oooo   .oooo.    888   888  oooo    ooo
#    .8' `888.    d88' `888  d88' `888        888  `888P"Y88b  d88' `888  `888   `88.  .8'  `888  d88' `888  `888  `888  `P  )88b   888   888   `88.  .8'
#   .88ooo8888.   888   888  888   888        888   888   888  888   888   888    `88..8'    888  888   888   888   888   .oP"888   888   888    `88..8'
#  .8'     `888.  888   888  888   888        888   888   888  888   888   888     `888'     888  888   888   888   888  d8(  888   888   888     `888'
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o o888o o888o `Y8bod88P" o888o     `8'     o888o `Y8bod88P"  `V88V"V8P' `Y888""8o o888o o888o     .8'
#                                                                                                                                              .o..P'
#                                                                                                                                              `Y8P'


class SCATTER5_OT_add_psy_individual(bpy.types.Operator): #same implentation as applied in load_biome
    """wrapper of `add_psy_preset()`"""

    bl_idname      = "scatter5.add_psy_individual"
    bl_label       = translate("Add Particle-System Individually")
    bl_description = translate("Scatter the selected objects Individually in new particle-systems")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty()
    instance_names : bpy.props.StringProperty() # list of object names separated with "_!#!_"
    use_asset_browser : bpy.props.BoolProperty() #use active asset from asset browser instead of instance list?
    json_path : bpy.props.StringProperty() #string = json preset path, if not will use active preset

    def __init__(self):
        self.Operations = None
        self.step = 0
        self.timer = None
        self.done = False
        self.max_step = None
        self.timer_count = 0

    def invoke(self, context, event, ):

        scat_scene = bpy.context.scene.scatter5

        #Get Emitter 

        emitter = bpy.data.objects.get(self.emitter_name)
        if emitter is None: 
            emitter = scat_scene.emitter
        if emitter is None: 
            return {'FINISHED'}

        #Get instances

        if self.use_asset_browser:
              obj_list = import_selected_assets(link=(scat_scene.opt_import_method=="LINK"),)
        elif self.instance_names:
              obj_list = [ bpy.data.objects[n] for n in self.instance_names.split("_!#!_") if n in bpy.data.objects ]
        else: obj_list = []
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))
        
        #ERROR if no instances found 

        if (len(instances)==0):
            msg = translate("No valid Object(s) found in Selection.") if (not self.use_asset_browser) else translate("No Asset(s) found in Asset-Browser.")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        #Prepare operations steps

        self.Operations = {}

        #directly start painting?

        vg_name = ""
        if (scat_scene.opt_mask_assign_method=="paint"):
            vg = emitter.vertex_groups.new()
            vg_name = vg.name

        for i,o in enumerate(instances):

            #store scattering function in dict 

            def generate_operation(o):
                def fct():
                    bpy.ops.scatter5.add_psy_preset(
                        psy_name = "*AUTO*",
                        emitter_name = emitter.name,
                        instance_names = o.name,
                        use_asset_browser = False,
                        json_path = self.json_path,
                        from_biome  = True,
                        pop_msg = True,
                        )

                    #directly start painting?

                    if vg_name:
                        psy = emitter.scatter5.particle_systems[-1]
                        psy.s_mask_vg_allow = True
                        psy.s_mask_vg_ptr = vg_name
                        psy.s_mask_vg_revert = True
                        psy.hide_viewport = False 

                    return None
                return fct

            self.Operations[f"System {i+1}/{len(instances)}"] = generate_operation(o)
            continue

        #directly start painting?

        if vg_name:
            def start_painting():
                bpy.ops.scatter5.vg_quick_paint(mode="vg",group_name=vg_name)
                return None 
            self.Operations[f"Start Painting"] = start_painting

        #We are ready to launch the modal mode

        #give context to progress bar 
        context.scene.scatter5.progress_context = "individual"

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
        context.scene.scatter5.progress_label = list(self.Operations.keys())[self.step] if (self.step<len(self.Operations.keys())) else translate("Done!") #f"{self.chrono_end-self.chrono_start:0.1f}s"
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


# oooooooooooo              .    o8o                                  .    o8o
# `888'     `8            .o8    `"'                                .o8    `"'
#  888          .oooo.o .o888oo oooo  ooo. .oo.  .oo.    .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
#  888oooo8    d88(  "8   888   `888  `888P"Y88bP"Y88b  `P  )88b    888   `888  d88' `88b `888P"Y88b
#  888    "    `"Y88b.    888    888   888   888   888   .oP"888    888    888  888   888  888   888
#  888       o o.  )88b   888 .  888   888   888   888  d8(  888    888 .  888  888   888  888   888
# o888ooooood8 8""888P'   "888" o888o o888o o888o o888o `Y888""8o   "888" o888o `Y8bod8P' o888o o888o



def get_estimated_preset_particle_count(emitter, d=None, preset_density=None, preset_density_method="", refresh_square_area=True):
    """estimate a future particle system particle count before it's created by looking at preset and emitter surface
    parameters: either pass settings_dict or pass preset_density + preset_density_method"""

    # Note that this estimation calculation is also done in double, 
    # in the ui_creation.draw_scattering(self,layout) for GUI prupose...

    #WARNING ON CREATION FEATURES ARE AFFECTING ESTIMATION

    scat_scene = bpy.context.scene.scatter5
    particle_count = 0

    if refresh_square_area:
        emitter.scatter5.get_estimated_square_area()

    if d is not None: #doing same steps in presetting
        preset_density = d["estimated_density"] if ("estimated_density" in d) else 0
        preset_density_method = ""
        if ("s_distribution_space" in d):
            preset_density_method += " "+d["s_distribution_space"]
        if ("s_distribution_method" in d):
            preset_density_method += " "+d["s_distribution_method"]

    if preset_density_method=="":

        #Should not be possible
        particle_count = -1
          
    elif ("random" in preset_density_method) or ("clumping" in preset_density_method):
            
        is_random = ("random" in preset_density_method)

        #Surface
        estimated_square_area = emitter.scatter5.estimated_square_area
        if ("global" in preset_density_method):
            estimated_square_area *= sum(emitter.scale)/len(emitter.scale)

        #Particle-Count
        particle_count = int(estimated_square_area*preset_density)

        #viewport % reduction
        if scat_scene.s_visibility_view_allow:
            particle_count = (particle_count/100)*(100-scat_scene.s_visibility_view_percentage)

    elif ("verts" in preset_density_method) or ("faces" in preset_density_method):

        particle_count = len(emitter.data.polygons) if ("faces" in preset_density_method) else len(emitter.data.vertices)

    elif ("manual_all" in preset_density_method):

        particle_count = 0

    if scat_scene.s_visibility_hide_viewport:
        particle_count = 0

    if (scat_scene.opt_mask_assign_method=="paint"):
        particle_count = 0

    return particle_count


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = [

    SCATTER5_OT_add_psy_simple,
    SCATTER5_OT_add_psy_preset,
    SCATTER5_OT_add_psy_individual,
    
    ]



#if __name__ == "__main__":
#    register()