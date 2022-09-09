
#####################################################################################################
#
# ooo        ooooo            o8o                    .oooooo..o               .       .    o8o
# `88.       .888'            `"'                   d8P'    `Y8             .o8     .o8    `"'
#  888b     d'888   .oooo.   oooo  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#  8  `888'   888   .oP"888   888   888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
#  8    Y     888  d8(  888   888   888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# o8o        o888o `Y888""8o o888o o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                           d"     YD
#                                                                                                           "Y88888P'
#
######################################################################################################


import bpy
import os 

from .. resources.translate import translate
from .. resources import directories


#####################################################################################################
#
#   .oooooo.    .o8           o8o                         .
#  d8P'  `Y8b  "888           `"'                       .o8
# 888      888  888oooo.     oooo  .ooooo.   .ooooo.  .o888oo
# 888      888  d88' `88b    `888 d88' `88b d88' `"Y8   888
# 888      888  888   888     888 888ooo888 888         888
# `88b    d88'  888   888     888 888    .o 888   .o8   888 .
#  `Y8bood8P'   `Y8bod8P'     888 `Y8bod8P' `Y8bod8P'   "888"
#                          888888
#
#####################################################################################################


from . particle_settings import SCATTER5_PROP_particle_systems
from . mask_settings import SCATTER5_PROP_procedural_vg
from .. scattering.selection import idx_active_update


class SCATTER5_PROP_Object(bpy.types.PropertyGroup): 
    """scat_object = bpy.context.object.scatter5"""
    
    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8 .dP"Y8
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88 `Ybo."
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88 o.`Y8b
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88 8bodP'

    particle_systems : bpy.props.CollectionProperty(type=SCATTER5_PROP_particle_systems) #Children Collection
    
    particle_systems_idx : bpy.props.IntProperty(
        update=idx_active_update,
        )

    def get_psy_active(self):
        """return the active particle system of this emitter, will return bpy.types.Object or None"""

        if len(self.particle_systems)==0:
            return None 
        l = [p for p in self.particle_systems if p.active]
        if len(l)==0:
            return None
        return l[0]

    def get_psys_selected(self): 
        """return the selected particle systems of this emitter, note that active psy is not considered as selected, will return a list"""

        if len(self.particle_systems)==0:
            return [] 
        l = [p for p in self.particle_systems if p.sel]

        return l

    def add_virgin_psy(self, psy_name="", psy_color=(3,3,3), psy_hide_viewport=True, instances=[], deselect_all=False,):
        """create virgin psy with default settings"""

        from .. import utils 

        emitter = self.id_data
        psys = emitter.scatter5.particle_systems

        #create scatter default collection

        utils.coll_utils.create_scatter5_collections()

        #deselect everything but new psys

        if deselect_all:
            for p in psys: 
                p.sel=False

        #create new scatter obj,

        scatter_obj_original_name = f"scatter_obj : {psy_name}"
        scatter_obj = bpy.data.objects.new(scatter_obj_original_name, bpy.data.meshes.new(scatter_obj_original_name), )
        scatter_obj.hide_select = True
        scatter_obj.scatter5.original_emitter = emitter  #Leave trace of original emitter, in case of dupplication we need this data,cannot put it per object data, because in case of dupplication pointers will also be dupplicated for some strange reasons
        utils.create_utils.lock_transform(scatter_obj)

        #get psy name, prefix will be done automatically by blender 

        psy_name = scatter_obj.name.split("scatter_obj : ")[1]

        #put it in new collection

        geonode_coll = utils.coll_utils.create_new_collection(f"psy : {psy_name}", parent_name="Scatter5 Geonode", prefix=True)
        geonode_coll.objects.link(scatter_obj)

        #add new psy & assign important properties

        p = psys.add() 
        p.scatter_obj = scatter_obj #==point scattering
        p.name = psy_name
        p.name_bis = psy_name

        #update color

        if psy_color[0]!=3:
            p.s_color = psy_color

        #update particle list idx 

        emitter.scatter5.particle_systems_idx = len(emitter.scatter5.particle_systems)-1 #will also set .active & .sel property correctly

        #hide by default? better for performance, unhide after if needed

        p.scatter_obj.hide_viewport = psy_hide_viewport
        p.hide_viewport = psy_hide_viewport 

        #add geonode Scattering Modifier to scatter object

        m = utils.import_utils.import_and_add_geonode( p.scatter_obj, mod_name="Scatter5 Geonode Engine MKI", node_name=".Scatter5 Geonode Engine MKI", blend_path=directories.addon_engine, copy=True,)

        #assign initial emitter value

        m.node_group.nodes["s_emitter"].inputs[0].default_value = emitter

        #because of utterly awful named attribute design we are forced to pass all named attr in modifiers...

        #assign named attr considered as "builtin" in nodetree
        m["Input_6_use_attribute"] = True
        m["Input_6_attribute_name"] = "edge_border"
        m["Input_7_use_attribute"] = True
        m["Input_7_attribute_name"] = "edge_curvature"
        m["Input_8_use_attribute"] = True
        m["Input_8_attribute_name"] = "manual_index"
        m["Input_9_use_attribute"] = True
        m["Input_9_attribute_name"] = "manual_normal" 
        #m["Input_10_use_attribute"] = True
        #m["Input_10_attribute_name"] = "manual_id" #this is done with legacy node
        m["Input_12_use_attribute"] = True
        m["Input_12_attribute_name"] = "manual_scale"
        m["Input_13_use_attribute"] = True
        m["Input_13_attribute_name"] = "manual_align_z"
        m["Input_14_use_attribute"] = True
        m["Input_14_attribute_name"] = "manual_align_y"
            
        #patterns uv ptr
        m["Input_15_use_attribute"] = True #s_pattern1.texture_node.uv_ptr
        m["Input_16_use_attribute"] = True #s_pattern2.texture_node.uv_ptr

        #universal masks
        m["Input_17_use_attribute"] = True #umask s_rot_add
        m["Input_18_use_attribute"] = True #umask s_rot_random
        m["Input_22_use_attribute"] = True #umask s_rot_tilt
        
        m["Input_23_use_attribute"] = True #umask s_scale_random
        m["Input_26_use_attribute"] = True #umask s_scale_shrink
        m["Input_24_use_attribute"] = True #umask s_scale_grow
        m["Input_25_use_attribute"] = True #umask s_scale_mirror

        m["Input_27_use_attribute"] = True #umask s_pattern1
        m["Input_28_use_attribute"] = True #umask s_pattern2

        m["Input_29_use_attribute"] = True #umask s_abiotic_elev
        m["Input_30_use_attribute"] = True #umask s_abiotic_slope
        m["Input_31_use_attribute"] = True #umask s_abiotic_dir
        m["Input_32_use_attribute"] = True #umask s_abiotic_cur
        m["Input_33_use_attribute"] = True #umask s_abiotic_border

        m["Input_34_use_attribute"] = True #umask s_proximity_removenear
        m["Input_35_use_attribute"] = True #umask s_proximity_leanover
        m["Input_37_use_attribute"] = True #umask s_proximity_outskirt

        m["Input_36_use_attribute"] = True #umask s_ecosystem_affinity
        m["Input_48_use_attribute"] = True #umask s_ecosystem_repulsion

        m["Input_38_use_attribute"] = True #umask s_wind_wave
        m["Input_39_use_attribute"] = True #umask s_wind_noise

        m["Input_40_use_attribute"] = True #umask s_push_offset
        m["Input_41_use_attribute"] = True #umask s_push_dir
        m["Input_42_use_attribute"] = True #umask s_push_noise
        m["Input_43_use_attribute"] = True #umask s_push_fall

        m["Input_44_use_attribute"] = True #s_rot_tilt.texture_node.uv_ptr
        m["Input_45_use_attribute"] = True #s_rot_tilt_vcol_ptr

        m["Input_46_use_attribute"] = True #s_rot_align_y.texture_node.uv_ptr
        m["Input_47_use_attribute"] = True #s_rot_align_y.vcol_ptr

        m["Input_49_use_attribute"] = True #s_wind_wave_flowmap_ptr

        m["Input_50_use_attribute"] = True #s_instances.texture_node.uv_ptr       
        m["Input_51_use_attribute"] = True #s_instances.vcol_ptr       

        m["Input_52_use_attribute"] = True #dens mask vg
        m["Input_53_use_attribute"] = True #dens mask vcol
        m["Input_55_use_attribute"] = True #dens mask bitmap uv

        #create new instance collection

        instance_coll = utils.coll_utils.create_new_collection(f"ins_col : {p.name}", parent_name="Scatter5 Ins Col", prefix=True)
        p.s_instances_coll_ptr = instance_coll

        #add instances in collection

        if (len(instances)!=0):
            for inst in instances:                
                if (inst.name not in instance_coll.objects): 
                    instance_coll.objects.link(inst)

        #if nothing is found, show placegolders
        
        else:
            p.s_display_allow = True

        return p

    # .dP"Y8  dP"Yb  88   88    db    88""Yb 888888        db    88""Yb 888888    db
    # `Ybo." dP   Yb 88   88   dPYb   88__dP 88__         dPYb   88__dP 88__     dPYb
    # o.`Y8b Yb b dP Y8   8P  dP__Yb  88"Yb  88""        dP__Yb  88"Yb  88""    dP__Yb
    # 8bodP'  `"YoYo `YbodP' dP""""Yb 88  Yb 888888     dP""""Yb 88  Yb 888888 dP""""Yb

    estimated_square_area : bpy.props.FloatProperty(default=-1) #used in statistics

    def get_estimated_square_area(self, eval_modifiers=True):
        """get the m² of this object mesh (mods not evaluated) -- CARREFUL MIGHT BE SLOW -- DO NOT RUN IN REAL TIME""" 

        o = self.id_data #TODO will need to support multi surfaces
        square_area = 0 

        if eval_modifiers:
              depsgraph = bpy.context.evaluated_depsgraph_get()
              eo = o.evaluated_get(depsgraph)
              ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        else: ob = o.data

        # bmesh method?
        # import bmesh
        # bm = bmesh.new()
        # bm.from_mesh(ob)
        # square_area = sum(f.calc_area() for f in bm.faces)
        # bm.free()

        ob.calc_loop_triangles()
        
        import numpy as np 
        tri_area = np.zeros(len(ob.loop_triangles), dtype=np.float, )
        ob.loop_triangles.foreach_get('area', tri_area, )
        square_area = np.sum(tri_area)

        self.estimated_square_area = square_area
        return square_area

    # 88""Yb 88""Yb  dP"Yb   dP""b8 888888 8888b.  88   88 88""Yb    db    88         8b    d8    db    .dP"Y8 88  dP
    # 88__dP 88__dP dP   Yb dP   `" 88__    8I  Yb 88   88 88__dP   dPYb   88         88b  d88   dPYb   `Ybo." 88odP
    # 88"""  88"Yb  Yb   dP Yb      88""    8I  dY Y8   8P 88"Yb   dP__Yb  88  .o     88YbdP88  dP__Yb  o.`Y8b 88"Yb
    # 88     88  Yb  YbodP   YboodP 888888 8888Y"  `YbodP' 88  Yb dP""""Yb 88ood8     88 YY 88 dP""""Yb 8bodP' 88  Yb

    mask_systems : bpy.props.CollectionProperty(type=SCATTER5_PROP_procedural_vg) #Children Collection
    mask_systems_idx : bpy.props.IntProperty()

    # .dP"Y8  dP""b8    db    888888 888888 888888 88""Yb      dP"Yb  88""Yb  88888
    # `Ybo." dP   `"   dPYb     88     88   88__   88__dP     dP   Yb 88__dP     88
    # o.`Y8b Yb       dP__Yb    88     88   88""   88"Yb      Yb   dP 88""Yb o.  88
    # 8bodP'  YboodP dP""""Yb   88     88   888888 88  Yb      YbodP  88oodP "bodP'

    original_emitter : bpy.props.PointerProperty( #Keep Track of original emitter, in case of user dupplicating object data, it might cause BS 
        description="is needed when dupplicating an object, it will dupplicate also every object properties and we need to procedurally check by checking if obj==emitter_ptr from scatter_obj",
        type=bpy.types.Object, 
        ) 


#####################################################################################################
#
#  .oooooo..o
# d8P'    `Y8
# Y88bo.       .ooooo.   .ooooo.  ooo. .oo.    .ooooo.
#  `"Y8888o.  d88' `"Y8 d88' `88b `888P"Y88b  d88' `88b
#      `"Y88b 888       888ooo888  888   888  888ooo888
# oo     .d8P 888   .o8 888    .o  888   888  888    .o
# 8""88888P'  `Y8bod8P' `Y8bod8P' o888o o888o `Y8bod8P'
#
#####################################################################################################


from . gui_settings import SCATTER5_PROP_ui
from . manual_settings import SCATTER5_PROP_scene_manual
from .. scattering.emitter import poll_emitter
from .. scattering.synchronize import SCATTER5_PROP_sync_channels
from .. scattering.update_factory import generate_edge_curvature_attr, generate_edge_border_attr


def upd_emitter(self,context):
    if self.emitter is not None:
        self.emitter.scatter5.get_estimated_square_area()
        #generate_edge_curvature_attr(self.emitter)
        #generate_edge_border_attr(self.emitter)
    return None

def upd_unsel_all(self,context):
    if not self.update_auto_set_scatter_obj_active:
        for o in bpy.data.objects:
            if o.name.startswith("scatter_obj"):
                o.hide_select = True
    return None

def is_closed_curve(self, object):
   return (object.splines[0].use_cyclic_u == True)


class SCATTER5_PROP_Scene(bpy.types.PropertyGroup): 
    """scat_scene = bpy.context.scene.scatter5"""

    # 888888 8b    d8 88 888888 888888 888888 88""Yb
    # 88__   88b  d88 88   88     88   88__   88__dP
    # 88""   88YbdP88 88   88     88   88""   88"Yb
    # 888888 88 YY 88 88   88     88   888888 88  Yb

    #emitter terrain target workflow

    emitter : bpy.props.PointerProperty( 
        type        = bpy.types.Object, 
        poll        = poll_emitter,
        description = translate("Emitter target object, where you will Scatter your Particles. Note that the target type need to be a mesh, and cannot be an instance of another particle_system"),
        update = upd_emitter, #estimate square area when changing active object
        )
    
    emitter_pinned : bpy.props.BoolProperty( #pinned mode
        default=False, 
        description=translate("pin emitter object"),
        )

    #  dP""b8 88   88 88
    # dP   `" 88   88 88
    # Yb  "88 Y8   8P 88
    #  YboodP `YbodP' 88

    ui : bpy.props.PointerProperty(type=SCATTER5_PROP_ui) 
    ui_enabled : bpy.props.BoolProperty(default=True)

    # 8b    d8    db    88b 88 88   88    db    88
    # 88b  d88   dPYb   88Yb88 88   88   dPYb   88
    # 88YbdP88  dP__Yb  88 Y88 Y8   8P  dP__Yb  88  .o
    # 88 YY 88 dP""""Yb 88  Y8 `YbodP' dP""""Yb 88ood8

    manual : bpy.props.PointerProperty(type=SCATTER5_PROP_scene_manual)

    # .dP"Y8 Yb  dP 88b 88  dP""b8
    # `Ybo."  YbdP  88Yb88 dP   `"
    # o.`Y8b   8P   88 Y88 Yb
    # 8bodP'  dP    88  Y8  YboodP

    sync_channels      : bpy.props.CollectionProperty(type=SCATTER5_PROP_sync_channels) #Children Collection
    sync_channels_idx  : bpy.props.IntProperty()

    # 88   88 88""Yb 8888b.     db    888888 888888
    # 88   88 88__dP  8I  Yb   dPYb     88   88__
    # Y8   8P 88"""   8I  dY  dP__Yb    88   88""
    # `YbodP' 88     8888Y"  dP""""Yb   88   888888

    factory_delay_allow : bpy.props.BoolProperty( #global control over event listening and tweaking delay, only for dev 
        default=False,
        )
    factory_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default= "update_on_release",
        description= translate("Change how the active particle system refresh the viewport when you are tweaking the settings"),
        items= [ ("update_delayed" ,translate("Delayed"), translate("refresh viewport every x miliseconds"), 1),
                 ("update_on_release" ,translate("On Mouse Release") ,translate("refresh viewport when the mouse"), 2),
                 #("update_apply" ,translate("Apply") ,translate("refresh viewport when using the apply function"), 3),
               ],
        )
    factory_update_delay : bpy.props.FloatProperty(
        name=translate("Seconds of Delay"),
        default=0.2,
        max=1,
        min=0,
        step=3,
        precision=3,
        subtype="TIME",
        unit="TIME",
        description=translate("Delay of the update when tweaking the system(s) settings"),
        )
    factory_cam_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default= "auto",
        description= translate("Change how the camera clipping features update"),
        items= [ ("auto", translate("Automatic") ,translate("Refresh automatically when camera move or rotate"),0 ),
                 ("limit", translate("Timer Limit") ,translate("Refresh only when camera stop moving"),1 ),
                 ("toggle", translate("Manual") ,translate("Refresh only when enabling a camera clipping/culling feature or clicking on the refresh button"),2 ),
               ],
        )
    factory_alt_allow : bpy.props.BoolProperty( #global control over event listening and tweaking delay, only for dev 
        default=True,
        description= translate("When pressing ALT while changing a particle-system property, Scatter5 will automatically apply the value to all selected particle-system"),
        )
    factory_alt_selection_method : bpy.props.EnumProperty(
        name=translate("Selection"),
        default= "active",
        description= translate("Change how the active particle system refresh the viewport when you are tweaking the settings"),
        items= [ ("active", translate("Active Emitter"), translate("apply value to selected particle-system from active emitter"), 1),
                 ("all", translate("All Emitters"), translate("apply value to all selected particle-system of this scene"), 2),
               ],
        ) 
    factory_synchronization_allow : bpy.props.BoolProperty( #Not available in interface tho 
        default=True,
        )
    factory_event_listening_allow : bpy.props.BoolProperty(
        default=True,
        description= translate("The plugin is still in WIP, description will be added upon final release"),
        )
    update_auto_set_scatter_obj_active : bpy.props.BoolProperty(
        default=False,
        update=upd_unsel_all,
        description= translate("Perhaps you'd like to see that outline of the active particle-system? Enable this option to do so, but be aware that drawing such overlay is bad for the viewport performance."),
        )
    update_auto_overlay_rendered : bpy.props.BoolProperty(
        default=False,
        description= translate("The plugin is still in WIP, description will be added upon final release"),
        )

    # 88""Yb 88""Yb 888888 .dP"Y8 888888 888888      dP"Yb  88""Yb 888888
    # 88__dP 88__dP 88__   `Ybo." 88__     88       dP   Yb 88__dP   88
    # 88"""  88"Yb  88""   o.`Y8b 88""     88       Yb   dP 88"""    88
    # 88     88  Yb 888888 8bodP' 888888   88        YbodP  88       88

    preset_path : bpy.props.StringProperty(
        default="Please Choose a Preset",
        subtype="FILE_PATH",
        ) 
    preset_name : bpy.props.StringProperty(
        name=translate("Display Name"),
        description=translate("Future name of your particle system."),
        default="Default Preset",
        )
    preset_color : bpy.props.FloatVectorProperty( #default color used for preset_find_color if nothing found. only used for GUI
        name=translate("Display Color"),
        description=translate("Future color of your particle system."),
        default=(1,1,1),
        subtype="COLOR",
        )
    #will exec on preset preview enul update function
    preset_find_name : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the name of the first selected instance object as the name of your future particle-system, instead of the preset name"),
        )
    preset_find_color : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the first material display color of your fist selected instance object as the color of your future particle-system, instead of the preset color"),
        )

    # 888888 .dP"Y8 888888 88 8b    d8    db    888888 888888
    # 88__   `Ybo."   88   88 88b  d88   dPYb     88   88__
    # 88""   o.`Y8b   88   88 88YbdP88  dP__Yb    88   88""
    # 888888 8bodP'   88   88 88 YY 88 dP""""Yb   88   888888

    estimated_preset_density : bpy.props.FloatProperty( #Of Estimated Active Preset
        name=translate("Estimated Particles /m²"),
        default=0,
        )
    estimated_preset_density_method : bpy.props.StringProperty() #to estimate density, might need extra info, such as, global Space ? Distribution Method? use keywords ""/"vert"/"face"/"unavailable"/else..

    #  dP""b8 88""Yb 888888    db    888888 88  dP"Yb  88b 88     .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
    # dP   `" 88__dP 88__     dPYb     88   88 dP   Yb 88Yb88     `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
    # Yb      88"Yb  88""    dP__Yb    88   88 Yb   dP 88 Y88     o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
    #  YboodP 88  Yb 888888 dP""""Yb   88   88  YbodP  88  Y8     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'

    add_psy_selection_method : bpy.props.EnumProperty(
        name=translate("Scattered Item(s) Selection Method"),
        default= "viewport", 
        items= [ ("viewport", translate("Selected Object(s)"), translate("Scatter the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                 ("browser", translate("Selected Asset(s)"), translate("Scatter the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
               ],
        )
    add_psy_allocation_method : bpy.props.EnumProperty(
        name=translate("Scattered Item(s) Allocation Method"),
        default= "group", 
        items= [ ("group", translate("New System"), translate("Scatter the compatible objects in a newly created particle system"), "PARTICLES",1 ),
                 ("individual", translate("New System per Object"), translate("Scatter each compatible object in their own newly created particle system"), "MOD_PARTICLE_INSTANCE",2 ),
               ],
        )

    #Visibility

    s_visibility_hide_viewport : bpy.props.BoolProperty(
        default=False,
        )
    s_visibility_view_allow: bpy.props.BoolProperty(
        default=False,
        )
    s_visibility_view_percentage: bpy.props.FloatProperty(
        name=translate("Removal"),
        default=80,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        )
    s_visibility_cam_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Camera Optimizations"),
        )
    s_visibility_camclip_allow: bpy.props.BoolProperty(
        default=True,
        name=translate("Frustrum Culling"),
        description=translate("Only show particles inside the active-camera frustrum volume"),
        )
    s_visibility_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Distance Culling"),
        description=translate("Only show close to the camera"),
        )
    s_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Falloff Min"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )
    s_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("Falloff Max"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )

    #Display on Creation
    
    s_display_allow : bpy.props.BoolProperty(
        default=False,
        )
    s_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        default= "placeholder", 
        items= [ ("bb", translate("Bounding-Box"), translate(""), "CUBE",1 ),
                 ("convexhull", translate("Convex-Hull"), translate(""), "CON_PIVOT",2 ),
                 ("placeholder", translate("Placeholder"), translate(""), "MOD_CLOTH",3 ),
                 ("placeholder_custom", translate("Custom Placeholder"), translate(""), "MOD_CLOTH",4 ),
                 ("point", translate("Point"), translate(""), "STICKY_UVS_DISABLE",5 ), #TODO Dorian, once we got a proper mesh point instancing support you might want to work a little more on this, and add radius option +  store it on biome so biomes have proper radius too ? 
                 #("cloud", translate("Point-Cloud"), translate(""), "POINTCLOUD_DATA",7 ), #TODO Carbon! 
               ],
        )
    s_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        )
    s_display_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Reveal Near Instance Camera"),
        description=translate("Disable the particle display method for points closed to the camera"),
        )

    #Other 

    s_display_biome_placeholder : bpy.props.BoolProperty(
        default=False,
        )
    s_display_bounding_box : bpy.props.BoolProperty(
        default=False,
        )
    s_display_enable_lodify : bpy.props.BoolProperty(
        default=False,
        )

    #Asign Special Method

    opt_mask_assign_method : bpy.props.EnumProperty(
        name=translate("Assignment Action"),
        default= "none", 
        items= [ ("none",translate("No Further Action"),"","PANEL_CLOSE",1),
                 ("paint",translate("Paint VGroup Density Mask"),"","WPAINT_HLT",2),
                 #("curve",translate("Assign in Given Bezier-Area"),"","",3),
                 ("vg",translate("Assign VGroup Density Mask"),"","GROUP_VERTEX",4),
                 ("manual",translate("Use Manual Distribution"),"","BRUSHES_ALL",5),
               ],
        )
    opt_vg_assign_slot : bpy.props.StringProperty()

    opt_mask_curve_area_ptr : bpy.props.PointerProperty(
        type=bpy.types.Curve, 
        poll=is_closed_curve,
        )

    #Link on creation?
    opt_import_method : bpy.props.EnumProperty(
        name=translate("Import Method"),
        default= "APPEND", 
        items= [ ("APPEND",translate("Append Imports"),"","APPEND_BLEND",1),
                 ("LINK",translate("Link Imports"),"","LINK_BLEND",2),
               ],
        )

    # opt_sync_settings : bpy.props.BoolProperty(
    #     default=False,
    #     description="",
    #     )

    # .dP"Y8 888888  dP""b8 88   88 88""Yb 88 888888 Yb  dP
    # `Ybo." 88__   dP   `" 88   88 88__dP 88   88    YbdP
    # o.`Y8b 88""   Yb      Y8   8P 88"Yb  88   88     8P
    # 8bodP' 888888  YboodP `YbodP' 88  Yb 88   88    dP

    sec_emit_count_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("This thresold value represents the maximal visible particle count. If threshold reached on scattering operation, Scatter will automatically hide your particle system.")
        )
    sec_emit_count : bpy.props.IntProperty(
        default=199_000, 
        min=9_000, 
        name=translate("Treshold :"),
        description=translate("This thresold value represents the maximal visible particle count. If threshold reached on scattering operation, Scatter will automatically hide your particle system.")
        )

    sec_inst_verts_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("This thresold value represents the maximal allowed vertex count of an instance. If threshold reached on scattering operation, Scatter will automatically set youe instance display as bounding box.")
        )
    sec_inst_verts : bpy.props.IntProperty(
        default=199_000,  
        min=9_000, 
        name=translate("Treshold :"),
        description=translate("This thresold value represents the maximal allowed vertex count of an instance. If threshold reached on scattering operation, Scatter will automatically set youe instance display as bounding box.")
        )

    #for masks mainly, because some users don't understand that terrain vertex count can have an impact on performance or quality of vertex paint drawing 
    
    sec_emit_verts_min_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("This thresold value represents the emitter minimal vertex-count. If threshold reached, Scatter will tell you that your terrain might be too low poly and this might affect masks precision, as they rely on vertex-groups to highlight areas."),
        )
    sec_emit_verts_min : bpy.props.IntProperty(
        default=999,   
        min=64,     
        name=translate("Treshold :"),
        description=translate("This thresold value represents the emitter minimal vertex-count. If threshold reached, Scatter will tell you that your terrain might be too low poly and this might affect masks precision, as they rely on vertex-groups to highlight areas."),
        )
    
    sec_emit_verts_max_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("This thresold value represents an emitter maximal vertex-count. If threshold reached, Scatter will tell you that your terrain might be too high poly and this might affect masks calculation speed."),
        )
    sec_emit_verts_max : bpy.props.IntProperty(
        default=175_000, 
        min=9_000, 
        name=translate("Treshold :"),
        description=translate("This thresold value represents an emitter maximal vertex-count. If threshold reached, Scatter will tell you that your terrain might be too high poly and this might affect masks calculation speed.")
        )    

    # 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP
    # 88     88 88__dP 88__dP   dPYb   88__dP  YbdP
    # 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P
    # 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP

    library_item_size : bpy.props.FloatProperty(
        default=7.0,
        min=5,
        max=15,
        name=translate("Item Size")
        )
    library_typo_limit : bpy.props.IntProperty(
        default=40,
        min=4,
        max=100,
        name=translate("Typo Limit"),
        )
    library_adaptive_columns : bpy.props.BoolProperty(
        name=translate("Adaptive Columns"),
        default=True,
        )
    library_columns : bpy.props.IntProperty(
        default=4,
        min=1,
        max=40,
        soft_max=10,
        name=translate("Number of Columns"),
        )
    library_search : bpy.props.StringProperty(
        default="",
        )
    
    # 8888b.  88 .dP"Y8 88""Yb 88        db     dP""b8 888888
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb   dP   `" 88__
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb  Yb      88""
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  YboodP 888888

    displace_img : bpy.props.PointerProperty(
        type=bpy.types.Image,
        )

    #  dP""b8 88""Yb 888888    db    888888 88  dP"Yb  88b 88
    # dP   `" 88__dP 88__     dPYb     88   88 dP   Yb 88Yb88
    # Yb      88"Yb  88""    dP__Yb    88   88 Yb   dP 88 Y88
    #  YboodP 88  Yb 888888 dP""""Yb   88   88  YbodP  88  Y8

    #Directory
    precrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    precrea_creation_directory : bpy.props.StringProperty(
        name=translate("Overwrite if already exists"),
        default=directories.lib_presets, 
        )

    #preset related
    precrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use Random Seed Values"),
        description=translate("automatically randomize the seed values of all seed properties"),
        default=True, 
        )
    precrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create Unique Textures"),
        description=translate("When creating a texture data, scatter will always create a new texture data, if this option is set to False, Scatter will use the same texture data if found in .blend."),
        default=True, 
        )
    precrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random Textures Translation"),
        description=translate("When creating a texture data, scatter will randomize the location vector, useful to guarantee patch uniqueness location. Disable this option if you are using a texture that have an influence on multiple particle systems."),
        default=True, 
        )
    precrea_auto_render : bpy.props.BoolProperty(
        name=translate("Render thumbnail"),
        description=translate("automatically render the thumbnail of the preset afterwards"),
        default=False, 
        )

    # 88""Yb 88  dP"Yb  8b    d8 888888      dP""b8 88""Yb 888888    db    888888 88  dP"Yb  88b 88
    # 88__dP 88 dP   Yb 88b  d88 88__       dP   `" 88__dP 88__     dPYb     88   88 dP   Yb 88Yb88
    # 88""Yb 88 Yb   dP 88YbdP88 88""       Yb      88"Yb  88""    dP__Yb    88   88 Yb   dP 88 Y88
    # 88oodP 88  YbodP  88 YY 88 888888      YboodP 88  Yb 888888 dP""""Yb   88   88  YbodP  88  Y8

    #Directory
    biocrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    biocrea_creation_directory : bpy.props.StringProperty(
        default=os.path.join(directories.lib_biomes,"MyBiomes"),
        )

    #preset related
    biocrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use Random Seed Values"),
        description=translate("automatically randomize the seed values of all seed properties"),
        default=True,
        )
    biocrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create Unique Textures"),
        description=translate("When creating a texture data, scatter will always create a new texture data, if this option is set to False, Scatter will use the same texture data if found in .blend."),
        default=True,
        )
    biocrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random Textures Translation"),
        description=translate("When creating a texture data, scatter will randomize the location vector, useful to guarantee patch uniqueness location. Disable this option if you are using a texture that have an influence on multiple particle systems."),
        default=True,
        )

    #use biome display
    biocrea_use_biome_display : bpy.props.BoolProperty(
        name=translate("Export Placeholder Display Settings"),
        description=translate("In Scatter5 You can replace your instances with placeholders, by toggling this option, Scatter5 will also encode the placeholder settings. (If using custom placeholder, scatter5 will automatically export the object for you, note that if you decide to use your own .blend file you will need to make sure tha tthe placeholder object is present in your .blend)."),
        default=True,
        )

    #biome information
    biocrea_biome_name : bpy.props.StringProperty(
        name=translate("Name"),
        default="My Biome",
        )
    biocrea_file_keywords : bpy.props.StringProperty(
        name=translate("Keywords"),
        default="Some, Examples, Of, Keywords, Use, Coma,",
        )
    biocrea_file_author : bpy.props.StringProperty(
        name=translate("Author"),
        default="BD3D",
        )
    biocrea_file_website : bpy.props.StringProperty(
        name=translate("Website"),
        default="https://twitter.com/_BD3D",
        )
    biocrea_file_description : bpy.props.StringProperty(
        name=translate("Description"),
        default="this is a custom biome i made! :-)",
        )
    
    #biome instance export 
    biocrea_centralized_blend_allow : bpy.props.BoolProperty(
        name=translate("Use your own .blend?"),
        description=translate("Sometimes you don't want to systematically save the assets in new.blend files, because perhaps you are creating biomes for a whole library already stored inside a centralized .blend file, if this is the case, you can enter the name of your .blend file here."),
        default=False,
        )
    biocrea_centralized_blend : bpy.props.StringProperty(
        default="central.blend",
        )
    biocrea_auto_reload_all  : bpy.props.BoolProperty(
        default=True,
        name=translate("Reload Library Afterwards"),
        )

    #biocrea_centralized_blend_search_from_addon_directory : bpy.props.BoolProperty(
    #    name=translate(".Blend located in addon Directory?"),
    #    description=translate("Perhaps your centralized .blend is located within an addon? if it is the case, toggle this option, scatter will search for a .blend with such name in the addon folder."),
    #    default=False,
    #    )

    #gui steps
    biocrea_creation_steps : bpy.props.IntProperty(
        default=0,
        )

    # 88""Yb 88""Yb  dP"Yb   dP""b8 88""Yb 888888 .dP"Y8 .dP"Y8     88""Yb    db    88""Yb
    # 88__dP 88__dP dP   Yb dP   `" 88__dP 88__   `Ybo." `Ybo."     88__dP   dPYb   88__dP
    # 88"""  88"Yb  Yb   dP Yb  "88 88"Yb  88""   o.`Y8b o.`Y8b     88""Yb  dP__Yb  88"Yb
    # 88     88  Yb  YbodP   YboodP 88  Yb 888888 8bodP' 8bodP'     88oodP dP""""Yb 88  Yb

    #used by : scatter5.load_biome and scatter5.add_psy_individual

    progress_bar : bpy.props.FloatProperty(
        default=0,
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=0,
        )
    progress_label : bpy.props.StringProperty(
        default="",
        )
    progress_context : bpy.props.StringProperty(
        default="",
        )

    # 888888 88  88 88   88 8b    d8 88""Yb 88b 88    db    88 88          dP""b8 888888 88b 88 888888 88""Yb    db    888888 88  dP"Yb  88b 88
    #   88   88  88 88   88 88b  d88 88__dP 88Yb88   dPYb   88 88         dP   `" 88__   88Yb88 88__   88__dP   dPYb     88   88 dP   Yb 88Yb88
    #   88   888888 Y8   8P 88YbdP88 88""Yb 88 Y88  dP__Yb  88 88  .o     Yb  "88 88""   88 Y88 88""   88"Yb   dP__Yb    88   88 Yb   dP 88 Y88
    #   88   88  88 `YbodP' 88 YY 88 88oodP 88  Y8 dP""""Yb 88 88ood8      YboodP 888888 88  Y8 888888 88  Yb dP""""Yb   88   88  YbodP  88  Y8

    s_thumb_camera_type : bpy.props.EnumProperty(
        name=translate("Cam Distance"),
        default= "cam_small", 
        items= [ ("cam_forest" ,translate("Far") ,""),
                 ("cam_plant" ,translate("Medium") ,""),
                 ("cam_small" ,translate("Near") ,""),
               ],
        )
    s_thumb_placeholder_type : bpy.props.EnumProperty(
        name=translate("Instance"),
        default= "SCATTER5_placeholder_extruded_square", 
        items= [("SCATTER5_placeholder_extruded_triangle",     translate("Extruded Triangle") ,""     ,"MESH_CUBE", 1 ),
                ("SCATTER5_placeholder_extruded_square",       translate("Extruded Square") ,""       ,"MESH_CUBE", 2 ),
                ("SCATTER5_placeholder_extruded_pentagon",     translate("Extruded Pentagon") ,""     ,"MESH_CUBE", 3 ),
                ("SCATTER5_placeholder_extruded_hexagon",      translate("Extruded Hexagon") ,""      ,"MESH_CUBE", 4 ),
                ("SCATTER5_placeholder_extruded_decagon",      translate("Extruded Decagon") ,""      ,"MESH_CUBE", 5 ),
                ("SCATTER5_placeholder_pyramidal_triangle",    translate("Pyramidal Triangle") ,""    ,"MESH_CONE", 6 ),
                ("SCATTER5_placeholder_pyramidal_square",      translate("Pyramidal Square") ,""      ,"MESH_CONE", 7 ),
                ("SCATTER5_placeholder_pyramidal_pentagon",    translate("Pyramidal Pentagon") ,""    ,"MESH_CONE", 8 ),
                ("SCATTER5_placeholder_pyramidal_hexagon",     translate("Pyramidal Hexagon") ,""     ,"MESH_CONE", 9 ),
                ("SCATTER5_placeholder_pyramidal_decagon",     translate("Pyramidal Decagon") ,""     ,"MESH_CONE", 10 ),
                ("SCATTER5_placeholder_flat_triangle",         translate("Flat Triangle") ,""         ,"SNAP_FACE", 11 ),
                ("SCATTER5_placeholder_flat_square",           translate("Flat Square") ,""           ,"SNAP_FACE", 12 ),
                ("SCATTER5_placeholder_flat_pentagon",         translate("Flat Pentagon") ,""         ,"SNAP_FACE", 13 ),
                ("SCATTER5_placeholder_flat_hexagon",          translate("Flat Hexagon") ,""          ,"SNAP_FACE", 14 ),
                ("SCATTER5_placeholder_flat_decagon",          translate("Flat Decagon") ,""          ,"SNAP_FACE", 15 ),
                ("SCATTER5_placeholder_card_triangle",         translate("Card Triangle") ,""         ,"MESH_PLANE", 16 ),
                ("SCATTER5_placeholder_card_square",           translate("Card Square") ,""           ,"MESH_PLANE", 17 ),
                ("SCATTER5_placeholder_card_pentagon",         translate("Card Pentagon") ,""         ,"MESH_PLANE", 18 ),
                ("SCATTER5_placeholder_hemisphere_01",         translate("Hemisphere 01") ,""         ,"MESH_ICOSPHERE", 19 ),
                ("SCATTER5_placeholder_hemisphere_02",         translate("Hemisphere 02") ,""         ,"MESH_ICOSPHERE", 20 ),
                ("SCATTER5_placeholder_hemisphere_03",         translate("Hemisphere 03") ,""         ,"MESH_ICOSPHERE", 21 ),
                ("SCATTER5_placeholder_hemisphere_04",         translate("Hemisphere 04") ,""         ,"MESH_ICOSPHERE", 22 ),
                ("SCATTER5_placeholder_lowpoly_pine_01",       translate("Lowpoly Pine 01") ,""       ,"LIGHT_POINT", 23 ),
                ("SCATTER5_placeholder_lowpoly_pine_02",       translate("Lowpoly Pine 02") ,""       ,"LIGHT_POINT", 24 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_01", translate("Lowpoly Coniferous 01") ,"" ,"LIGHT_POINT", 25 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_02", translate("Lowpoly Coniferous 02") ,"" ,"LIGHT_POINT", 26 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_03", translate("Lowpoly Coniferous 03") ,"" ,"LIGHT_POINT", 27 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_04", translate("Lowpoly Coniferous 04") ,"" ,"LIGHT_POINT", 28 ),
                #("SCATTER5_placeholder_lowpoly_sapling_01",    translate("Lowpoly Sapling 01"),""     ,"LIGHT_POINT", 29 ), #Do not make sense to render all this below
                #("SCATTER5_placeholder_lowpoly_sapling_02",    translate("Lowpoly Sapling 02"),""     ,"LIGHT_POINT", 30 ),
                #("SCATTER5_placeholder_lowpoly_cluster_01",    translate("Lowpoly Cluster 01") ,""    ,"STICKY_UVS_LOC", 31 ),
                #("SCATTER5_placeholder_lowpoly_cluster_02",    translate("Lowpoly Cluster 02") ,""    ,"STICKY_UVS_LOC", 32 ),
                #("SCATTER5_placeholder_lowpoly_cluster_03",    translate("Lowpoly Cluster 03") ,""    ,"STICKY_UVS_LOC", 33 ),
                #("SCATTER5_placeholder_lowpoly_cluster_04",    translate("Lowpoly Cluster 04") ,""    ,"STICKY_UVS_LOC", 34 ),
                #("SCATTER5_placeholder_lowpoly_plant_01",      translate("Lowpoly Plant 01") ,""      ,"OUTLINER_OB_HAIR", 35 ),
                #("SCATTER5_placeholder_lowpoly_plant_02",      translate("Lowpoly Plant 02") ,""      ,"OUTLINER_OB_HAIR", 36 ),
                #("SCATTER5_placeholder_lowpoly_plant_03",      translate("Lowpoly Plant 03") ,""      ,"OUTLINER_OB_HAIR", 38 ),
                #("SCATTER5_placeholder_lowpoly_flower_01",     translate("Lowpoly Flower 01"),""      ,"OUTLINER_OB_HAIR", 39 ),
                #("SCATTER5_placeholder_lowpoly_flower_02",     translate("Lowpoly Flower 02"),""      ,"OUTLINER_OB_HAIR", 40 ),
                #("SCATTER5_placeholder_helper_empty_stick",    translate("Helper Empty Stick") ,""    ,"EMPTY_ARROWS", 41 ),
                #("SCATTER5_placeholder_helper_empty_arrow",    translate("Helper Empty Arrow") ,""    ,"EMPTY_ARROWS", 42 ),
                #("SCATTER5_placeholder_helper_empty_axis",     translate("Helper Empty Axis") ,""     ,"EMPTY_ARROWS", 43 ),
                #("SCATTER5_placeholder_helper_colored_axis",   translate("Helper Colored Axis") ,""   ,"EMPTY_ARROWS", 44 ),
                #("SCATTER5_placeholder_helper_colored_cube",   translate("Helper Colored Cube") ,""   ,"EMPTY_ARROWS", 45 ),
                ("SCATTER5_placeholder_helper_y_arrow",        translate("Helper Tangent Arrow") ,""  ,"EMPTY_ARROWS", 46 ),
               ],
        )
    s_thumb_placeholder_color : bpy.props.FloatVectorProperty( 
        name=translate("Color"),
        default=(1,0,0.5),
        min=0,
        max=1,
        subtype="COLOR",
        )
    s_thumb_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        subtype="XYZ", 
        default=(0.25,0.25,0.25), 
        )
    s_thumb_use_custom_blend_path : bpy.props.BoolProperty(
        default=True,
        name=translate("render preview from custom .blend?"),
        )
    s_thumb_custom_blend_path : bpy.props.StringProperty(
        name=translate("Blend Path"),
        description=translate("Scatter will open this .blend add the biome on the emitter named below then launch a render."),
        default=os.path.join(directories.addon_thumbnail,"custom_biome_icons.blend"),
        )
    s_thumb_custom_blend_emitter : bpy.props.StringProperty(
        name=translate("Emit. Name"),
        description=translate("Enter the emitter name from the blend above please."),
        default="Ground",
        )
    s_thumb_render_iconless : bpy.props.BoolProperty(
        default=False,
        name=translate("Render all Biomes with no Preview"),
        )
    s_thumb_auto_reload_all : bpy.props.BoolProperty(
        default=True,
        name=translate("Reload Library Afterwards"),
        )


#####################################################################################################
#
# oooooo   oooooo     oooo  o8o                    .o8
#  `888.    `888.     .8'   `"'                   "888
#   `888.   .8888.   .8'   oooo  ooo. .oo.    .oooo888   .ooooo.  oooo oooo    ooo
#    `888  .8'`888. .8'    `888  `888P"Y88b  d88' `888  d88' `88b  `88. `88.  .8'
#     `888.8'  `888.8'      888   888   888  888   888  888   888   `88..]88..8'
#      `888'    `888'       888   888   888  888   888  888   888    `888'`888'
#       `8'      `8'       o888o o888o o888o `Y8bod88P" `Y8bod8P'     `8'  `8'
#
#####################################################################################################


from .. ui.biome_library import SCATTER5_PROP_library
from .. ui.biome_library import SCATTER5_PROP_folder_navigation


class SCATTER5_PROP_Window(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5 ( will reset on each session, automatic default values ) """

    library : bpy.props.CollectionProperty(type=SCATTER5_PROP_library) #Children Collection

    folder_navigation : bpy.props.CollectionProperty(type=SCATTER5_PROP_folder_navigation) #Children Collection
    folder_navigation_idx : bpy.props.IntProperty()


#####################################################################################################
#
# ooooo      ooo                 .o8              .oooooo.
# `888b.     `8'                "888             d8P'  `Y8b
#  8 `88b.    8   .ooooo.   .oooo888   .ooooo.  888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.
#  8   `88b.  8  d88' `88b d88' `888  d88' `88b 888           `888""8P d88' `88b `888  `888   888' `88b
#  8     `88b.8  888   888 888   888  888ooo888 888     ooooo  888     888   888  888   888   888   888
#  8       `888  888   888 888   888  888    .o `88.    .88'   888     888   888  888   888   888   888
# o8o        `8  `Y8bod8P' `Y8bod88P" `Y8bod8P'  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'
#                                                                                             888
#                                                                                            o888o
#####################################################################################################


from ..scattering.texture_datablock import SCATTER5_PROP_node_texture


class SCATTER5_PROP_node_group(bpy.types.PropertyGroup): 
    """bpy.data.node_groups[i].scatter5"""

    texture : bpy.props.PointerProperty(type=SCATTER5_PROP_node_texture)