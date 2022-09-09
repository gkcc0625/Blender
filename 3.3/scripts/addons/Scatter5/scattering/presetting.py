
#####################################################################################################
#
# ooooooooo.                                             .       .    o8o
# `888   `Y88.                                         .o8     .o8    `"'
#  888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888     888   `888  `888P"Y88b  888' `88b
#  888          888     888ooo888 `"Y88b.  888ooo888   888     888    888   888   888  888   888
#  888          888     888    .o o.  )88b 888    .o   888 .   888 .  888   888   888  `88bod8P'
# o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.
#                                                                                      d"     YD
#                                                                                      "Y88888P'
#####################################################################################################


import bpy, os, json

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories 

from .. utils.extra_utils import dprint
from .. utils.str_utils import legal, is_illegal_string, word_wrap
from .. utils.import_utils import serialization 

from .. ui import templates

from . texture_datablock import export_texture_as_dict, paste_dict_to_texture, paste_legacy_beta_dict_to_texture


# oooooooooo.    o8o                .          .                     oooo
# `888'   `Y8b   `"'              .o8        .o8                     `888
#  888      888 oooo   .ooooo.  .o888oo    .o888oo  .ooooo.           888  .oooo.o  .ooooo.  ooo. .oo.
#  888      888 `888  d88' `"Y8   888        888   d88' `88b          888 d88(  "8 d88' `88b `888P"Y88b
#  888      888  888  888         888        888   888   888          888 `"Y88b.  888   888  888   888
#  888     d88'  888  888   .o8   888 .      888 . 888   888          888 o.  )88b 888   888  888   888
# o888bood8P'   o888o `Y8bod8P'   "888"      "888" `Y8bod8P'      .o. 88P 8""888P' `Y8bod8P' o888o o888o
#                                                                 `Y888P


def dict_to_json(d, path="", file_name="", extension=".json", ):
    """ dict > .json """
    #filename = w o extension!!!

    d = serialization(d)

    #write dict to json in disk
    json_path = os.path.join( path, f"{file_name}{extension}" )
    with open(json_path, 'w') as f:
        json.dump(d, f, indent=4)

    return 


#    oooo                                      .                  oooooooooo.    o8o                .
#    `888                                    .o8                  `888'   `Y8b   `"'              .o8
#     888  .oooo.o  .ooooo.  ooo. .oo.     .o888oo  .ooooo.        888      888 oooo   .ooooo.  .o888oo
#     888 d88(  "8 d88' `88b `888P"Y88b      888   d88' `88b       888      888 `888  d88' `"Y8   888
#     888 `"Y88b.  888   888  888   888      888   888   888       888      888  888  888         888
#     888 o.  )88b 888   888  888   888      888 . 888   888       888     d88'  888  888   .o8   888 .
# .o. 88P 8""888P' `Y8bod8P' o888o o888o     "888" `Y8bod8P'      o888bood8P'   o888o `Y8bod8P'   "888"
# `Y888P


def json_to_dict( path="", file_name=""):
    """ dict <- .json """
    #filename = with extension!!!

    json_path = os.path.join( path, file_name )

    if not os.path.exists(json_path):
        print(f"json_to_dict -> Hey it seems that the Json path don't exists? [{json_path}]")
        return {}

    with open(json_path) as f:
        d = json.load(f)
    return d


# oooooooooo.    o8o                .            .                   .oooooo..o               .       .    o8o
# `888'   `Y8b   `"'              .o8          .o8                  d8P'    `Y8             .o8     .o8    `"'
#  888      888 oooo   .ooooo.  .o888oo      .o888oo  .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  888      888 `888  d88' `"Y8   888          888   d88' `88b       `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#  888      888  888  888         888          888   888   888           `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
#  888     d88'  888  888   .o8   888 .        888 . 888   888      oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# o888bood8P'   o888o `Y8bod8P'   "888"        "888" `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                                           d"     YD
#                                                                                                                           "Y88888P'

def dict_to_settings( 
    d, 
    psy, 
    filter={
        "color":True,
        "distribution":True,
        "rot":True,
        "scale":True,
        "pattern":True,
        "push":True,
        "abiotic":True,
        "proximity":True,
        "ecosystem":True,
        "wind":True,
        "instances":True,
        },
    ):
    """ dict -> settings """

    scene      = bpy.context.scene
    scat_scene = scene.scatter5 
    emitter    = psy.id_data
    scat_mod   = psy.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
    keys       = d.keys()

    def settpsy_check(prop_name, only_if_true=False):
        if prop_name in keys: 
            if getattr(psy,prop_name)!=d[prop_name]:
                setattr(psy,prop_name,d[prop_name])
            if (only_if_true and d[prop_name]==False):
                return False
            return True 
        else: 
            return False

    def texture_ptr_to_settings(category_str=""):
        """helper funciton for scatter ng texure type, used a bit everywhere below"""

        scat_mod = psy.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
        keys = d.keys()

        ng_name = d[f"{category_str}_texture_ptr"]
        if (not ng_name.startswith(".TEXTURE ")):
            ng_name = f".TEXTURE {ng_name}"
        ng = bpy.data.node_groups.get(ng_name)

        if (ng is None) or (d[f"{category_str}_texture_is_unique"]==True): 

            if (f"{category_str}_texture_dict" in keys) or (f"{category_str}_texture_data" in keys):

                ng = scat_mod.node_group.nodes[f"TEXTURE_NODE {category_str}"].node_tree.copy()
                ng.scatter5.texture.user_name = ng_name.replace(".TEXTURE ","")

        if (ng is not None):

            if (f"{category_str}_texture_data" in keys):  
                   paste_legacy_beta_dict_to_texture(d[f"{category_str}_texture_data"], ng,)
            else:  paste_dict_to_texture(d[f"{category_str}_texture_dict"], ng,)

            setattr( psy, f"{category_str}_texture_ptr", ng.name)

        return None

    def u_mask_to_settings(category_str="",):
        """helper function to assign universal mask properties stored in dict"""

        keys = d.keys()

        if (f"{category_str}_mask_dict" not in keys):
            return None 

        mdi = d[f"{category_str}_mask_dict"]

        method = mdi[f"{category_str}_mask_method"]

        setattr(psy,f"{category_str}_mask_method", mdi[f"{category_str}_mask_method"],)
        setattr(psy,f"{category_str}_mask_ptr", mdi[f"{category_str}_mask_ptr"],)
        setattr(psy,f"{category_str}_mask_reverse", mdi[f"{category_str}_mask_reverse"],)
            
        if (method=="mask_vcol"):
            setattr(psy,f"{category_str}_mask_color_sample_method", mdi[f"{category_str}_mask_color_sample_method"],)
            setattr(psy,f"{category_str}_mask_id_color_ptr", mdi[f"{category_str}_mask_id_color_ptr"],)
        
        elif (method=="mask_noise"):
            setattr(psy,f"{category_str}_mask_noise_scale", mdi[f"{category_str}_mask_noise_scale"],)
            setattr(psy,f"{category_str}_mask_noise_brightness", mdi[f"{category_str}_mask_noise_brightness"],)
            setattr(psy,f"{category_str}_mask_noise_contrast", mdi[f"{category_str}_mask_noise_contrast"],)

        return None

    #Cancel out any user tweaking behavior when automating like this 
    old_factory_delay_allow , old_factory_event_listening_allow = scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow
    scat_scene.factory_delay_allow = scat_scene.factory_event_listening_allow = False

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INFORMATION

    if filter["color"]:
            
        settpsy_check("s_color")

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISTRIBUTION

    if filter["distribution"] and not psy.is_locked("s_distribution"):

        settpsy_check("s_distribution_space")     

        if settpsy_check("s_distribution_method"):
            
            #Radnom Dist 

            if (d["s_distribution_method"]=="random"):

                settpsy_check("s_distribution_density")
                settpsy_check("s_distribution_seed")
                settpsy_check("s_distribution_is_random_seed")

                if settpsy_check("s_distribution_limit_distance_allow", only_if_true=True): 
                    settpsy_check("s_distribution_limit_distance")

            #Clump Dist 

            elif (d["s_distribution_method"]=="clumping"):

                settpsy_check("s_distribution_clump_density")
                if settpsy_check("s_distribution_clump_limit_distance_allow", only_if_true=True):
                    settpsy_check("s_distribution_clump_limit_distance")

                settpsy_check("s_distribution_clump_max_distance")
                settpsy_check("s_distribution_clump_random_factor")
                settpsy_check("s_distribution_clump_falloff")
                settpsy_check("s_distribution_clump_seed")
                settpsy_check("s_distribution_clump_is_random_seed")

                settpsy_check("s_distribution_clump_children_density")

                if settpsy_check("s_distribution_clump_children_limit_distance_allow", only_if_true=True):
                    settpsy_check("s_distribution_clump_children_limit_distance")
 
                settpsy_check("s_distribution_clump_children_seed")
                settpsy_check("s_distribution_clump_children_is_random_seed")

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCALE

    if filter["scale"] and not psy.is_locked("s_scale"):

        #Default 

        if settpsy_check("s_scale_default_allow", only_if_true=True):

            settpsy_check("s_scale_default_space")
            settpsy_check("s_scale_default_value")

        #Random 

        if settpsy_check("s_scale_random_allow", only_if_true=True):

            settpsy_check("s_scale_random_factor")
            settpsy_check("s_scale_random_probability")
            settpsy_check("s_scale_random_method")
            settpsy_check("s_scale_random_seed")
            settpsy_check("s_scale_random_is_random_seed")

            u_mask_to_settings(category_str="s_scale_random",)
        
        #Shrink 

        if settpsy_check("s_scale_shrink_allow", only_if_true=True):

            settpsy_check("s_scale_shrink_factor")

            u_mask_to_settings(category_str="s_scale_shrink",)

        #Grow 

        if settpsy_check("s_scale_grow_allow", only_if_true=True):

            settpsy_check("s_scale_grow_factor")

            u_mask_to_settings(category_str="s_scale_grow",)

        #Mirror 

        if settpsy_check("s_scale_mirror_allow", only_if_true=True):  

            settpsy_check("s_scale_mirror_is_x")
            settpsy_check("s_scale_mirror_is_y")
            settpsy_check("s_scale_mirror_is_z")
            settpsy_check("s_scale_mirror_seed")
            settpsy_check("s_scale_mirror_is_random_seed")

            u_mask_to_settings(category_str="s_scale_mirror",)

        #Minimal Scale 

        if settpsy_check("s_scale_min_allow", only_if_true=True):

            settpsy_check("s_scale_min_method")
            settpsy_check("s_scale_min_value")

        #Clump Distribution Special 

        if (psy.s_distribution_method=="clumping"):

            if settpsy_check("s_scale_clump_allow", only_if_true=True):
                settpsy_check("s_scale_clump_value")

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ROTATION

    if filter["rot"] and not psy.is_locked("s_rot"):

        #Align Z 

        if settpsy_check("s_rot_align_z_allow", only_if_true=True):
                
            if settpsy_check("s_rot_align_z_method"):

                settpsy_check("s_rot_align_z_revert", only_if_true=True)

                if settpsy_check("s_rot_align_z_influence_allow", only_if_true=True):
                    settpsy_check("s_rot_align_z_influence_value")

                if (d["s_rot_align_z_method"]=="meth_align_z_object"):
                    if ("s_rot_align_z_object" in keys):
                        obj = scene.camera if (d["s_rot_align_z_object"]=="*CAMERA*") else bpy.data.collections.get(d["s_rot_align_z_object"])
                        psy.s_rot_align_z_object = obj

                # elif (psy.s_rot_align_z_method=="meth_align_z_random"):
                #     if ("s_rot_align_z_random_seed" in keys) :
                #         psy.s_rot_align_z_random_seed = d["s_rot_align_z_random_seed"]
                #     if ("s_rot_align_z_is_random_seed" in keys) :
                #         psy.s_rot_align_z_is_random_seed = d["s_rot_align_z_is_random_seed"]

                if settpsy_check("s_rot_align_z_clump_allow", only_if_true=True):
                    settpsy_check("s_rot_align_z_clump_value")

        #Align Y 

        if settpsy_check("s_rot_align_y_allow", only_if_true=True):

            if settpsy_check("s_rot_align_y_method"):

                settpsy_check("s_rot_align_y_revert", only_if_true=True)

                if (psy.s_rot_align_y_method=="meth_align_y_object"):
                    if ("s_rot_align_y_object" in keys) :
                        obj = scene.camera if (d["s_rot_align_y_object"]=="*CAMERA*") else bpy.data.collections.get(d["s_rot_align_y_object"])
                        psy.s_rot_align_y_object = obj

                elif (psy.s_rot_align_y_method=="meth_align_y_random"):

                    settpsy_check("s_rot_align_y_random_seed")
                    settpsy_check("s_rot_align_y_is_random_seed")

                elif (psy.s_rot_align_y_method=="meth_align_y_flow"):

                    settpsy_check("s_rot_align_y_flow_method")
                    settpsy_check("s_rot_align_y_flow_direction")

                    if (psy.s_rot_align_y_flow_method=="flow_vcol"):
                        settpsy_check("s_rot_align_y_vcol_ptr")

                    elif (psy.s_rot_align_y_flow_method=="flow_text"):
                        if ("s_rot_align_y_texture_ptr" in keys):
                            texture_ptr_to_settings(category_str="s_rot_align_y")

        #Random Rotation 

        if settpsy_check("s_rot_random_allow", only_if_true=True):

            settpsy_check("s_rot_random_tilt_value")
            settpsy_check("s_rot_random_yaw_value")
            settpsy_check("s_rot_random_seed")
            settpsy_check("s_rot_random_is_random_seed")

            u_mask_to_settings(category_str="s_rot_random",)

        #Rotate  

        if settpsy_check("s_rot_add_allow", only_if_true=True):

            settpsy_check("s_rot_add_default")
            settpsy_check("s_rot_add_random")
            settpsy_check("s_rot_add_seed")
            settpsy_check("s_rot_add_is_random_seed")
            settpsy_check("s_rot_add_snap")

            u_mask_to_settings(category_str="s_rot_add",)

        #Flowmap Tilting 

        if settpsy_check("s_rot_tilt_allow", only_if_true=True):

            settpsy_check("s_rot_tilt_method")
            settpsy_check("s_rot_tilt_force")
            settpsy_check("s_rot_tilt_direction")
            settpsy_check("s_rot_tilt_blue_is_strength")
            
            if (psy.s_rot_tilt_method=="tilt_vcol"):
                settpsy_check("s_rot_tilt_vcol_ptr")

            elif (psy.s_rot_tilt_method=="tilt_text"):
                if ("s_rot_tilt_texture_ptr" in keys):
                    texture_ptr_to_settings(category_str="s_rot_tilt")

            u_mask_to_settings(category_str="s_rot_tilt",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PATTERN

    if filter["pattern"] and not psy.is_locked(f"s_pattern"):

        for i in (1,2):
            pat = f"s_pattern{i}"
            
            if settpsy_check(f"{pat}_allow", only_if_true=True):

                if (f"{pat}_texture_ptr" in keys):
                    texture_ptr_to_settings(category_str=f"{pat}")

                settpsy_check(f"{pat}_dist_influence")
                settpsy_check(f"{pat}_dist_revert")
                settpsy_check(f"{pat}_scale_influence")
                settpsy_check(f"{pat}_scale_revert")
                settpsy_check(f"{pat}_color_sample_method")
                settpsy_check(f"{pat}_id_color_ptr")
                settpsy_check(f"{pat}_id_color_tolerence")

                #retro compatibility 
                if (f"{pat}_id_method" in keys):
                    if (f"{pat}_id_channel" in keys):
                        setattr( psy, f"{pat}_color_sample_method", "id_"+d[f"{pat}_id_channel"].lower())
                        setattr( psy, f"{pat}_dist_revert", not d[f"{pat}_dist_revert"])
                        setattr( psy, f"{pat}_scale_revert", not d[f"{pat}_scale_revert"])
                    elif (f"{pat}_id_color_ptr" in keys):
                        setattr( psy, f"{pat}_color_sample_method", "id_picker")
                        setattr( psy, f"{pat}_dist_revert", not d[f"{pat}_dist_revert"])
                        setattr( psy, f"{pat}_scale_revert", not d[f"{pat}_scale_revert"])

                u_mask_to_settings(category_str=pat,)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ABIOTIC 

    if filter["abiotic"] and not psy.is_locked("s_abiotic"):

        #Elevation 

        if settpsy_check("s_abiotic_elev_allow", only_if_true=True):

            if ("s_abiotic_elev_space" in keys):
                space = d["s_abiotic_elev_space"]
                psy.s_abiotic_elev_space = space
                settpsy_check(f"s_abiotic_elev_min_value_{space}")
                settpsy_check(f"s_abiotic_elev_min_falloff_{space}")
                settpsy_check(f"s_abiotic_elev_max_value_{space}")
                settpsy_check(f"s_abiotic_elev_max_falloff_{space}")

            settpsy_check("s_abiotic_elev_dist_influence")
            settpsy_check("s_abiotic_elev_dist_revert")
            settpsy_check("s_abiotic_elev_scale_influence")
            settpsy_check("s_abiotic_elev_scale_revert")

            u_mask_to_settings(category_str="s_abiotic_elev",)

        #Slope 

        if settpsy_check("s_abiotic_slope_allow", only_if_true=True):

            settpsy_check("s_abiotic_slope_space")
            settpsy_check("s_abiotic_slope_absolute")
            settpsy_check("s_abiotic_slope_min_value")
            settpsy_check("s_abiotic_slope_min_falloff")
            settpsy_check("s_abiotic_slope_max_value")
            settpsy_check("s_abiotic_slope_max_falloff")
            settpsy_check("s_abiotic_slope_dist_influence")
            settpsy_check("s_abiotic_slope_dist_revert")
            settpsy_check("s_abiotic_slope_scale_influence")
            settpsy_check("s_abiotic_slope_scale_revert")

            u_mask_to_settings(category_str="s_abiotic_slope",)

        #Orientation 

        if settpsy_check("s_abiotic_dir_allow", only_if_true=True):

            settpsy_check("s_abiotic_dir_space")
            settpsy_check("s_abiotic_dir_direction")
            settpsy_check("s_abiotic_dir_max")
            settpsy_check("s_abiotic_dir_treshold")
            settpsy_check("s_abiotic_dir_dist_influence")
            settpsy_check("s_abiotic_dir_dist_revert")
            settpsy_check("s_abiotic_dir_scale_influence")
            settpsy_check("s_abiotic_dir_scale_revert")

            u_mask_to_settings(category_str="s_abiotic_dir",)

        #Curvature

        if settpsy_check("s_abiotic_cur_allow", only_if_true=True):

            settpsy_check("s_abiotic_cur_type")
            settpsy_check("s_abiotic_cur_max")
            settpsy_check("s_abiotic_cur_treshold")
            settpsy_check("s_abiotic_cur_dist_influence")
            settpsy_check("s_abiotic_cur_dist_revert")
            settpsy_check("s_abiotic_cur_scale_influence")
            settpsy_check("s_abiotic_cur_scale_revert")

            u_mask_to_settings(category_str="s_abiotic_cur",)

        #Border

        if settpsy_check("s_abiotic_border_allow", only_if_true=True):

            settpsy_check("s_abiotic_border_max")
            settpsy_check("s_abiotic_border_treshold")
            settpsy_check("s_abiotic_border_dist_influence")
            settpsy_check("s_abiotic_border_dist_revert")
            settpsy_check("s_abiotic_border_scale_influence")
            settpsy_check("s_abiotic_border_scale_revert")

            u_mask_to_settings(category_str="s_abiotic_border",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PROXIMITY


    if filter["proximity"] and not psy.is_locked("s_proximity"):

        #Remove Near

        if settpsy_check("s_proximity_removenear_allow", only_if_true=True):

            settpsy_check("s_proximity_removenear_type")
            settpsy_check("s_proximity_removenear_max")
            settpsy_check("s_proximity_removenear_treshold")
            settpsy_check("s_proximity_removenear_dist_influence")
            settpsy_check("s_proximity_removenear_dist_revert")
            settpsy_check("s_proximity_removenear_scale_influence")
            settpsy_check("s_proximity_removenear_scale_revert")

            if ("s_proximity_removenear_coll_ptr" in keys):
                coll = bpy.data.collections.get(d["s_proximity_removenear_coll_ptr"])
                psy.s_proximity_removenear_coll_ptr = coll 

            u_mask_to_settings(category_str="s_proximity_removenear",)

        #Tilt Near

        if settpsy_check("s_proximity_leanover_allow", only_if_true=True):

            settpsy_check("s_proximity_leanover_type")
            settpsy_check("s_proximity_leanover_max")
            settpsy_check("s_proximity_leanover_treshold")
            settpsy_check("s_proximity_leanover_scale_influence")
            settpsy_check("s_proximity_leanover_tilt_influence")

            if ("s_proximity_leanover_coll_ptr" in keys):
                coll = bpy.data.collections.get(d["s_proximity_leanover_coll_ptr"])
                psy.s_proximity_leanover_coll_ptr = coll

            u_mask_to_settings(category_str="s_proximity_leanover",)

        #Outskirt

        if settpsy_check("s_proximity_outskirt_allow", only_if_true=True):

            settpsy_check("s_proximity_outskirt_treshold")
            settpsy_check("s_proximity_outskirt_limit")
            settpsy_check("s_proximity_outskirt_scale_influence")
            settpsy_check("s_proximity_outskirt_tilt_influence")

            u_mask_to_settings(category_str="s_proximity_outskirt",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ECOSYSTEM

    if filter["ecosystem"] and not psy.is_locked("s_ecosystem"):

        #Affinity

        if settpsy_check("s_ecosystem_affinity_allow", only_if_true=True):

            for i in (1,2,3):
                if settpsy_check(f"s_ecosystem_affinity_{i:02}_ptr"):
                    settpsy_check(f"s_ecosystem_affinity_{i:02}_type")
                    settpsy_check(f"s_ecosystem_affinity_{i:02}_max_value")
                    settpsy_check(f"s_ecosystem_affinity_{i:02}_max_falloff")
                    settpsy_check(f"s_ecosystem_affinity_{i:02}_limit_distance")

            settpsy_check("s_ecosystem_affinity_dist_influence")
            settpsy_check("s_ecosystem_affinity_scale_influence")

            u_mask_to_settings(category_str="s_ecosystem_affinity",)

        #Repulsion

        if settpsy_check("s_ecosystem_repulsion_allow", only_if_true=True):

            for i in (1,2,3):
                if settpsy_check(f"s_ecosystem_repulsion_{i:02}_ptr"):
                    settpsy_check(f"s_ecosystem_repulsion_{i:02}_type")
                    settpsy_check(f"s_ecosystem_repulsion_{i:02}_max_value")
                    settpsy_check(f"s_ecosystem_repulsion_{i:02}_max_falloff")

            settpsy_check("s_ecosystem_repulsion_dist_influence")
            settpsy_check("s_ecosystem_repulsion_scale_influence")

            u_mask_to_settings(category_str="s_ecosystem_repulsion",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> OFFSET

    if filter["push"] and not psy.is_locked("s_push"):    

        #Push Offset 

        if settpsy_check("s_push_offset_allow", only_if_true=True):

            settpsy_check("s_push_offset_add_value")
            settpsy_check("s_push_offset_add_random")
            settpsy_check("s_push_offset_scale_value")
            settpsy_check("s_push_offset_scale_random")

            u_mask_to_settings(category_str="s_push_offset",)

        #Push 

        if settpsy_check("s_push_dir_allow", only_if_true=True):

            settpsy_check("s_push_dir_method")
            settpsy_check("s_push_dir_add_value")
            settpsy_check("s_push_dir_add_random")

            u_mask_to_settings(category_str="s_push_dir",)

        #Noise 

        if settpsy_check("s_push_noise_allow", only_if_true=True):

            settpsy_check("s_push_noise_vector")
            settpsy_check("s_push_noise_speed")

            u_mask_to_settings(category_str="s_push_noise",)

        #Falling 

        if settpsy_check("s_push_fall_allow", only_if_true=True):
        
            settpsy_check("s_push_fall_height")
            settpsy_check("s_push_fall_key1_pos")
            settpsy_check("s_push_fall_key1_height")
            settpsy_check("s_push_fall_key2_pos")
            settpsy_check("s_push_fall_key2_height")
            settpsy_check("s_push_fall_stop_when_initial_z")
      
            if settpsy_check("s_push_fall_turbulence_allow", only_if_true=True):

                settpsy_check("s_push_fall_turbulence_spread")
                settpsy_check("s_push_fall_turbulence_speed")
                settpsy_check("s_push_fall_turbulence_rot_vector")
                settpsy_check("s_push_fall_turbulence_rot_factor")

            u_mask_to_settings(category_str="s_push_fall",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> WIND EFFECT

    if filter["wind"] and not psy.is_locked("s_wind"):

        #Wind Wave 

        if settpsy_check("s_wind_wave_allow", only_if_true=True):
                
            settpsy_check("s_wind_wave_speed")
            settpsy_check("s_wind_wave_force")
            settpsy_check("s_wind_wave_swinging")
            settpsy_check("s_wind_wave_scale_influence")
            settpsy_check("s_wind_wave_texture_scale")
            settpsy_check("s_wind_wave_texture_turbulence")
            settpsy_check("s_wind_wave_texture_brightness")
            settpsy_check("s_wind_wave_texture_contrast")

            settpsy_check("s_wind_wave_dir_method")

            if (d["s_wind_wave_dir_method"]=="vcol"):

                settpsy_check("s_wind_wave_flowmap_ptr")
                settpsy_check("s_wind_wave_direction")

            elif (d["s_wind_wave_dir_method"]=="fixed"):

                settpsy_check("s_wind_wave_direction")

            u_mask_to_settings(category_str="s_wind_wave",)
                    
        #Wind Noise
        
        if settpsy_check("s_wind_noise_allow", only_if_true=True):

            settpsy_check("s_wind_noise_force")
            settpsy_check("s_wind_noise_speed")

            u_mask_to_settings(category_str="s_wind_noise",)

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INSTANCING

    if filter["instances"] and not psy.is_locked("s_instances"):

        #instances method support

        if ("s_instances_method" in keys):

            #versioning of old .biome files
            if (d["s_instances_method"]=="ins_coll_random"):
                d["s_instances_method"]="ins_collection"

            #s_instances_coll_ptr never for presets, that's for biomes

            settpsy_check("s_instances_seed")
            settpsy_check("s_instances_is_random_seed")
            settpsy_check("s_instances_method")
            settpsy_check("s_instances_pick_method")

            pick_method = d.get("s_instances_pick_method")

            if (pick_method=="pick_rate"):

                for i in range(1,21):
                    settpsy_check(f"s_instances_id_{i:02}_rate")

            elif (pick_method=="pick_scale"):

                for i in range(1,21):
                    settpsy_check(f"s_instances_id_{i:02}_scale_min")
                    settpsy_check(f"s_instances_id_{i:02}_scale_max")

                settpsy_check("s_instances_id_scale_method")

            elif (pick_method=="pick_color"):

                for i in range(1,21):
                    settpsy_check(f"s_instances_id_{i:02}_color")

                settpsy_check("s_instances_id_color_tolerence")
                settpsy_check("s_instances_id_color_sample_method")

                sample_method = d["s_instances_id_color_sample_method"]
                if (sample_method=="vcol"):
                    settpsy_check("s_instances_vcol_ptr")
                elif (sample_method=="text"):
                    if (f"s_instances_texture_ptr" in keys):
                        texture_ptr_to_settings(category_str=f"s_instances")

            elif (pick_method=="pick_cluster"):

                settpsy_check("s_instances_pick_cluster_projection_method")
                settpsy_check("s_instances_pick_cluster_scale")
                settpsy_check("s_instances_pick_cluster_blur")
                settpsy_check("s_instances_pick_clump")

            # if psy.s_instances_method=="ins_volume": # currently unsuppoted
            #     if ("s_instances_volume_density" in keys):
            #         psy.s_instances_volume_density = d["s_instances_volume_density"]
            #     if ("s_instances_volume_voxel_ammount" in keys):
            #         psy.s_instances_volume_voxel_ammount = d["s_instances_volume_voxel_ammount"]

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    #restore habitual tweaking behavior
    scat_scene.factory_delay_allow , scat_scene.factory_event_listening_allow = old_factory_delay_allow , old_factory_event_listening_allow

    return 


#  .oooooo..o               .       .    o8o                                           .                  oooooooooo.    o8o                .
# d8P'    `Y8             .o8     .o8    `"'                                         .o8                  `888'   `Y8b   `"'              .o8
# Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o      .o888oo  .ooooo.        888      888 oooo   .ooooo.  .o888oo
#  `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8        888   d88' `88b       888      888 `888  d88' `"Y8   888
#      `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.         888   888   888       888      888  888  888         888
# oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b        888 . 888   888       888     d88'  888  888   .o8   888 .
# 8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'        "888" `Y8bod8P'      o888bood8P'   o888o `Y8bod8P'   "888"
#                                                         d"     YD
#                                                         "Y88888P'


def settings_to_dict(psy, 
    use_random_seed=True,
    texture_is_unique=True,
    texture_random_loc=True,
    get_estimated_density=True,
    ):
    """ dict <- settings """ 
    #extra care here, we save only what is being used
    
    d = {}

    def save_texture_ptr_in_dict(category_str="", texture_is_unique=False, texture_random_loc=False,):
        """helper funciton for scatter ng texure type, used a bit everywhere below"""

        #make sure texture_ptr is up to date 
        mod = psy.scatter_obj.modifiers["Scatter5 Geonode Engine MKI"]
        texture_node = mod.node_group.nodes[f"TEXTURE_NODE {category_str}"]
        ng_name = texture_node.node_tree.name 

        if (ng_name==".TEXTURE *DEFAULT*"): 
            ng_name=""

        setattr(psy, f"{category_str}_texture_ptr", ng_name)

        ng = bpy.data.node_groups.get(ng_name) 
        if (ng is not None):

            d[f"{category_str}_texture_ptr"] = ng_name
            d[f"{category_str}_texture_is_unique"] = texture_is_unique 
            d[f"{category_str}_texture_dict"] = export_texture_as_dict(ng, texture_random_loc=texture_random_loc,)

        return None 

    def save_u_mask_in_dict(category_str="",):

        try: 
            method = getattr(psy, f"{category_str}_mask_method")
        except: #perhaps property does not exists
            print("S5 LINE FAILED: getattr(psy, f'*category_str*_mask_method'). This should never happen")
            return None 

        if (method is None): 
            return None 

        if (method=="none"):
            return None 

        mdi = d[f"{category_str}_mask_dict"] = {}

        mdi[f"{category_str}_mask_method"] = getattr(psy,f"{category_str}_mask_method")
        mdi[f"{category_str}_mask_ptr"] = getattr(psy,f"{category_str}_mask_ptr")
        mdi[f"{category_str}_mask_reverse"] = getattr(psy,f"{category_str}_mask_reverse")
            
        if (method=="mask_vcol"):
            mdi[f"{category_str}_mask_color_sample_method"] = getattr(psy,f"{category_str}_mask_color_sample_method")
            mdi[f"{category_str}_mask_id_color_ptr"] = getattr(psy,f"{category_str}_mask_id_color_ptr")
        
        elif (method=="mask_noise"):
            mdi[f"{category_str}_mask_noise_scale"] = getattr(psy,f"{category_str}_mask_noise_scale")
            mdi[f"{category_str}_mask_noise_brightness"] = getattr(psy,f"{category_str}_mask_noise_brightness")
            mdi[f"{category_str}_mask_noise_contrast"] = getattr(psy,f"{category_str}_mask_noise_contrast")

        return None


    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INFORMATION"] = ""
    
    d["name"] = psy.name
    d["s_color"] = psy.s_color

    if get_estimated_density:
        d["estimated_density"] = psy.get_estimated_density()

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISTRIBUTION"] = ""

    d["s_distribution_method"] = psy.s_distribution_method
    d["s_distribution_space"] = psy.s_distribution_space

    #Random Distribution 

    if psy.s_distribution_method=="random":
        d["s_distribution_density"] = psy.s_distribution_density
        if use_random_seed:
              d["s_distribution_is_random_seed"] = True
        else: d["s_distribution_seed"] = psy.s_distribution_seed

        d["s_distribution_limit_distance_allow"] = psy.s_distribution_limit_distance_allow
        if psy.s_distribution_limit_distance_allow:
            d["s_distribution_limit_distance"] = psy.s_distribution_limit_distance

    #Clump Distribution 

    elif psy.s_distribution_method=="clumping":
        d["s_distribution_clump_density"] = psy.s_distribution_clump_density

        d["s_distribution_clump_limit_distance_allow"] = psy.s_distribution_clump_limit_distance_allow
        if psy.s_distribution_clump_limit_distance_allow:
            d["s_distribution_clump_limit_distance"] = psy.s_distribution_clump_limit_distance
            
        d["s_distribution_clump_max_distance"] = psy.s_distribution_clump_max_distance
        d["s_distribution_clump_random_factor"] = psy.s_distribution_clump_random_factor
        d["s_distribution_clump_falloff"] = psy.s_distribution_clump_falloff

        if use_random_seed:
              d["s_distribution_clump_is_random_seed"] = True
        else: d["s_distribution_clump_seed"] = psy.s_distribution_clump_seed

        d["s_distribution_clump_children_density"] = psy.s_distribution_clump_children_density
        
        d["s_distribution_clump_children_limit_distance_allow"] = psy.s_distribution_clump_children_limit_distance_allow
        if psy.s_distribution_clump_children_limit_distance_allow:
            d["s_distribution_clump_children_limit_distance"] = psy.s_distribution_clump_children_limit_distance

        if use_random_seed:
              d["s_distribution_clump_children_is_random_seed"] = True
        else: d["s_distribution_clump_children_seed"] = psy.s_distribution_clump_children_seed

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCALE"] = ""
    
    #Default Scale 

    d["s_scale_default_allow"] = psy.s_scale_default_allow
    if psy.s_scale_default_allow:

        d["s_scale_default_space"] = psy.s_scale_default_space
        d["s_scale_default_value"] = psy.s_scale_default_value

    #Random Scale 

    d["s_scale_random_allow"] = psy.s_scale_random_allow
    if psy.s_scale_random_allow:

        d["s_scale_random_factor"] = psy.s_scale_random_factor
        d["s_scale_random_probability"] = psy.s_scale_random_probability
        d["s_scale_random_method"] = psy.s_scale_random_method

        if use_random_seed:
              d["s_scale_random_is_random_seed"] = True
        else: d["s_scale_random_seed"] = psy.s_scale_random_seed

        save_u_mask_in_dict(category_str="s_scale_random",)
    
    #Shrink 

    d["s_scale_shrink_allow"] = psy.s_scale_shrink_allow
    if psy.s_scale_shrink_allow:

        d["s_scale_shrink_factor"] = psy.s_scale_shrink_factor

        save_u_mask_in_dict(category_str="s_scale_shrink",)

    #Grow 

    d["s_scale_grow_allow"] = psy.s_scale_grow_allow
    if psy.s_scale_grow_allow:

        d["s_scale_grow_factor"] = psy.s_scale_grow_factor

        save_u_mask_in_dict(category_str="s_scale_grow",)
    
    #Random Mirror

    d["s_scale_mirror_allow"] = psy.s_scale_mirror_allow
    if psy.s_scale_mirror_allow:

        d["s_scale_mirror_is_x"] = psy.s_scale_mirror_is_x
        d["s_scale_mirror_is_y"] = psy.s_scale_mirror_is_y
        d["s_scale_mirror_is_z"] = psy.s_scale_mirror_is_z

        if use_random_seed:
              d["s_scale_mirror_is_random_seed"] = True
        else: d["s_scale_mirror_seed"] = psy.s_scale_mirror_seed

        save_u_mask_in_dict(category_str="s_scale_mirror",)

    #Minimal Scale 

    d["s_scale_min_allow"] = psy.s_scale_min_allow
    if psy.s_scale_min_allow:

        d["s_scale_min_method"] = psy.s_scale_min_method
        d["s_scale_min_value"] = psy.s_scale_min_value

    #Clump Distribution Special 

    if (psy.s_distribution_method=="clumping"):
        d["s_scale_clump_allow"] = psy.s_scale_clump_allow
        if psy.s_scale_clump_allow:
            d["s_scale_clump_value"] = psy.s_scale_clump_value

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ROTATION"] = ""
    
    #Align Z 

    d["s_rot_align_z_allow"] = psy.s_rot_align_z_allow
    if psy.s_rot_align_z_allow:

        d["s_rot_align_z_method"] = psy.s_rot_align_z_method

        if psy.s_rot_align_z_influence_allow:

            d["s_rot_align_z_influence_allow"] = True
            d["s_rot_align_z_influence_value"] = psy.s_rot_align_z_influence_value

        if psy.s_rot_align_z_revert:

            d["s_rot_align_z_revert"] = True 

        if (psy.s_rot_align_z_method=="meth_align_z_object"):

            if (psy.s_rot_align_z_object is not None):
                d["s_rot_align_z_object"] = "*CAMERA*" if (psy.s_rot_align_z_object.type=="CAMERA") else psy.s_rot_align_z_object.name
    
        if (psy.s_distribution_method=="clumping"):

            d["s_rot_align_z_clump_allow"] = psy.s_rot_align_z_clump_allow
            if psy.s_rot_align_z_clump_allow:
                d["s_rot_align_z_clump_value"] = psy.s_rot_align_z_clump_value

    #Align Y

    d["s_rot_align_y_allow"] = psy.s_rot_align_y_allow
    if psy.s_rot_align_y_allow:

        d["s_rot_align_y_method"] = psy.s_rot_align_y_method

        if psy.s_rot_align_y_revert:
            d["s_rot_align_y_revert"] = True 

        if (psy.s_rot_align_y_method=="meth_align_y_object"):

            if (psy.s_rot_align_y_object is not None):
                d["s_rot_align_y_object"] = "*CAMERA*" if (psy.s_rot_align_y_object.type=="CAMERA") else psy.s_rot_align_z_object.name

        elif (psy.s_rot_align_y_method=="meth_align_y_random"):
            
            if use_random_seed:
                  d["s_rot_align_y_is_random_seed"] = True
            else: d["s_rot_align_y_random_seed"] = psy.s_rot_align_y_random_seed

        elif (psy.s_rot_align_y_method=="meth_align_y_flow"):

            d["s_rot_align_y_flow_method"] = psy.s_rot_align_y_flow_method
            d["s_rot_align_y_flow_direction"] = psy.s_rot_align_y_flow_direction

            if (psy.s_rot_align_y_flow_method=="flow_vcol"):

                d["s_rot_align_y_vcol_ptr"] = psy.s_rot_align_y_vcol_ptr

            elif (psy.s_rot_align_y_flow_method=="flow_text"):
                save_texture_ptr_in_dict(category_str=f"s_rot_align_y", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

    #Random Rotation 

    d["s_rot_random_allow"] = psy.s_rot_random_allow
    if psy.s_rot_random_allow:

        d["s_rot_random_tilt_value"] = psy.s_rot_random_tilt_value
        d["s_rot_random_yaw_value"] = psy.s_rot_random_yaw_value

        if use_random_seed:
              d["s_rot_random_is_random_seed"] = True
        else: d["s_rot_random_seed"] = psy.s_rot_random_seed

        save_u_mask_in_dict(category_str="s_rot_random",)

    #Rotation 

    d["s_rot_add_allow"] = psy.s_rot_add_allow
    if psy.s_rot_add_allow:

        d["s_rot_add_default"] = psy.s_rot_add_default
        d["s_rot_add_random"] = psy.s_rot_add_random

        if use_random_seed:
              d["s_rot_add_is_random_seed"] = True
        else: d["s_rot_add_seed"] = psy.s_rot_add_seed

        d["s_rot_add_snap"] = psy.s_rot_add_snap

        save_u_mask_in_dict(category_str="s_rot_add",)

    #Flowmap Tilting 

    d["s_rot_tilt_allow"] = psy.s_rot_tilt_allow
    if psy.s_rot_tilt_allow:

        d["s_rot_tilt_method"] = psy.s_rot_tilt_method
        d["s_rot_tilt_force"] = psy.s_rot_tilt_force
        d["s_rot_tilt_direction"] = psy.s_rot_tilt_direction
        d["s_rot_tilt_blue_is_strength"] = psy.s_rot_tilt_blue_is_strength

        if (psy.s_rot_tilt_method=="tilt_vcol"):
            d["s_rot_tilt_vcol_ptr"] = psy.s_rot_tilt_vcol_ptr

        elif (psy.s_rot_tilt_method=="tilt_text"):
            save_texture_ptr_in_dict(category_str=f"s_rot_tilt", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

        save_u_mask_in_dict(category_str="s_rot_tilt",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PATTERN"] = ""

    for i in (1,2):

        d[f"s_pattern{i}_allow"] = getattr(psy, f"s_pattern{i}_allow")
        if (getattr(psy, f"s_pattern{i}_allow")==True):

            save_texture_ptr_in_dict(category_str=f"s_pattern{i}", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

            d[f"s_pattern{i}_dist_influence"] = getattr(psy, f"s_pattern{i}_dist_influence")
            d[f"s_pattern{i}_dist_revert"] = getattr(psy, f"s_pattern{i}_dist_revert")
            d[f"s_pattern{i}_scale_influence"] = getattr(psy, f"s_pattern{i}_scale_influence")
            d[f"s_pattern{i}_scale_revert"] = getattr(psy, f"s_pattern{i}_scale_revert")

            d[f"s_pattern{i}_color_sample_method"] = getattr(psy, f"s_pattern{i}_color_sample_method") #will break if no versionning
            if d[f"s_pattern{i}_color_sample_method"]=="id_picker":
                d[f"s_pattern{i}_id_color_ptr"] = getattr(psy, f"s_pattern{i}_id_color_ptr")
                d[f"s_pattern{i}_id_color_tolerence"] = getattr(psy, f"s_pattern{i}_id_color_tolerence")

            save_u_mask_in_dict(category_str=f"s_pattern{i}",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ABIOTIC"] = ""

    #Elevation 

    d["s_abiotic_elev_allow"] = psy.s_abiotic_elev_allow
    if psy.s_abiotic_elev_allow:
                
        space = psy.s_abiotic_elev_space 

        d["s_abiotic_elev_space"] = space
        d[f"s_abiotic_elev_min_value_{space}"] = getattr(psy, f"s_abiotic_elev_min_value_{space}")
        d[f"s_abiotic_elev_min_falloff_{space}"] = getattr(psy, f"s_abiotic_elev_min_falloff_{space}")
        d[f"s_abiotic_elev_max_value_{space}"] = getattr(psy, f"s_abiotic_elev_max_value_{space}")
        d[f"s_abiotic_elev_max_falloff_{space}"] = getattr(psy, f"s_abiotic_elev_max_falloff_{space}")
        
        d["s_abiotic_elev_dist_influence"] = psy.s_abiotic_elev_dist_influence
        d["s_abiotic_elev_dist_revert"] = psy.s_abiotic_elev_dist_revert
        d["s_abiotic_elev_scale_influence"] = psy.s_abiotic_elev_scale_influence
        d["s_abiotic_elev_scale_revert"] = psy.s_abiotic_elev_scale_revert

        save_u_mask_in_dict(category_str="s_abiotic_elev",)

    #Slope 

    d["s_abiotic_slope_allow"] = psy.s_abiotic_slope_allow
    if psy.s_abiotic_slope_allow:

        d["s_abiotic_slope_space"] = psy.s_abiotic_slope_space
        d["s_abiotic_slope_absolute"] = psy.s_abiotic_slope_absolute

        d["s_abiotic_slope_min_value"] = psy.s_abiotic_slope_min_value
        d["s_abiotic_slope_min_falloff"] = psy.s_abiotic_slope_min_falloff
        d["s_abiotic_slope_max_value"] = psy.s_abiotic_slope_max_value
        d["s_abiotic_slope_max_falloff"] = psy.s_abiotic_slope_max_falloff

        d["s_abiotic_slope_dist_influence"] = psy.s_abiotic_slope_dist_influence
        d["s_abiotic_slope_dist_revert"] = psy.s_abiotic_slope_dist_revert
        d["s_abiotic_slope_scale_influence"] = psy.s_abiotic_slope_scale_influence
        d["s_abiotic_slope_scale_revert"] = psy.s_abiotic_slope_scale_revert

        save_u_mask_in_dict(category_str="s_abiotic_slope",)

    #Orientation 

    d["s_abiotic_dir_allow"] = psy.s_abiotic_dir_allow
    if psy.s_abiotic_dir_allow:

        d["s_abiotic_dir_space"] = psy.s_abiotic_dir_space

        d["s_abiotic_dir_direction"] = psy.s_abiotic_dir_direction
        d["s_abiotic_dir_max"] = psy.s_abiotic_dir_max
        d["s_abiotic_dir_treshold"] = psy.s_abiotic_dir_treshold

        d["s_abiotic_dir_dist_influence"] = psy.s_abiotic_dir_dist_influence
        d["s_abiotic_dir_dist_revert"] = psy.s_abiotic_dir_dist_revert
        d["s_abiotic_dir_scale_influence"] = psy.s_abiotic_dir_scale_influence
        d["s_abiotic_dir_scale_revert"] = psy.s_abiotic_dir_scale_revert

        save_u_mask_in_dict(category_str="s_abiotic_dir",)

    #Curvature

    d["s_abiotic_cur_allow"] = psy.s_abiotic_cur_allow
    if psy.s_abiotic_cur_allow:

        d["s_abiotic_cur_type"] = psy.s_abiotic_cur_allow
        d["s_abiotic_cur_max"] = psy.s_abiotic_cur_allow
        d["s_abiotic_cur_treshold"] = psy.s_abiotic_cur_allow

        d["s_abiotic_cur_dist_influence"] = psy.s_abiotic_cur_allow
        d["s_abiotic_cur_dist_revert"] = psy.s_abiotic_cur_allow
        d["s_abiotic_cur_scale_influence"] = psy.s_abiotic_cur_allow
        d["s_abiotic_cur_scale_revert"] = psy.s_abiotic_cur_allow

        save_u_mask_in_dict(category_str="s_abiotic_cur",)

    #Border

    d["s_abiotic_border_allow"] = psy.s_abiotic_border_allow
    if psy.s_abiotic_border_allow:

        d["s_abiotic_border_max"] = psy.s_abiotic_border_max
        d["s_abiotic_border_treshold"] = psy.s_abiotic_border_treshold

        d["s_abiotic_border_dist_influence"] = psy.s_abiotic_border_dist_influence
        d["s_abiotic_border_dist_revert"] = psy.s_abiotic_border_dist_revert
        d["s_abiotic_border_scale_influence"] = psy.s_abiotic_border_scale_influence
        d["s_abiotic_border_scale_revert"] = psy.s_abiotic_border_scale_revert

        save_u_mask_in_dict(category_str="s_abiotic_border",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PROXIMITY"] = ""

    #Remove Near

    d["s_proximity_removenear_allow"] = psy.s_proximity_removenear_allow
    if psy.s_proximity_removenear_allow:

        d["s_proximity_removenear_type"] = psy.s_proximity_removenear_type
        d["s_proximity_removenear_max"] = psy.s_proximity_removenear_max
        d["s_proximity_removenear_treshold"] = psy.s_proximity_removenear_treshold
        d["s_proximity_removenear_dist_influence"] = psy.s_proximity_removenear_dist_influence
        d["s_proximity_removenear_dist_revert"] = psy.s_proximity_removenear_dist_revert
        d["s_proximity_removenear_scale_influence"] = psy.s_proximity_removenear_scale_influence
        d["s_proximity_removenear_scale_revert"] = psy.s_proximity_removenear_scale_revert

        if (psy.s_proximity_removenear_coll_ptr is not None): 
            d["s_proximity_removenear_coll_ptr"] = psy.s_proximity_removenear_coll_ptr.name

        save_u_mask_in_dict(category_str="s_proximity_removenear",)

    #Tilt Near

    d["s_proximity_leanover_allow"] = psy.s_proximity_leanover_allow
    if psy.s_proximity_leanover_allow:

        d["s_proximity_leanover_type"] = psy.s_proximity_leanover_type
        d["s_proximity_leanover_max"] = psy.s_proximity_leanover_max
        d["s_proximity_leanover_treshold"] = psy.s_proximity_leanover_treshold
        d["s_proximity_leanover_scale_influence"] = psy.s_proximity_leanover_scale_influence
        d["s_proximity_leanover_tilt_influence"] = psy.s_proximity_leanover_tilt_influence

        if (psy.s_proximity_leanover_coll_ptr is not None): 
            d["s_proximity_leanover_coll_ptr"] = psy.s_proximity_leanover_coll_ptr.name

        save_u_mask_in_dict(category_str="s_proximity_leanover",)

    #Outskirt

    d["s_proximity_outskirt_allow"] = psy.s_proximity_outskirt_allow
    if psy.s_proximity_outskirt_allow:

        d["s_proximity_outskirt_treshold"] = psy.s_proximity_outskirt_treshold
        d["s_proximity_outskirt_limit"] = psy.s_proximity_outskirt_limit
        d["s_proximity_outskirt_scale_influence"] = psy.s_proximity_outskirt_scale_influence
        d["s_proximity_outskirt_tilt_influence"] = psy.s_proximity_outskirt_tilt_influence

        save_u_mask_in_dict(category_str="s_proximity_outskirt",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ECOSYSTEM"] = ""

    #Affinity

    d["s_ecosystem_affinity_allow"] = psy.s_ecosystem_affinity_allow
    if psy.s_ecosystem_affinity_allow:

        for i in (1,2,3):
                        
            d[f"s_ecosystem_affinity_{i:02}_ptr"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_ptr")
            if (getattr(psy, f"s_ecosystem_affinity_{i:02}_ptr")!=""):

                d[f"s_ecosystem_affinity_{i:02}_type"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_type")
                d[f"s_ecosystem_affinity_{i:02}_max_value"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_max_value")
                d[f"s_ecosystem_affinity_{i:02}_max_falloff"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_max_falloff")
                d[f"s_ecosystem_affinity_{i:02}_limit_distance"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_limit_distance")

        d["s_ecosystem_affinity_dist_influence"] = psy.s_ecosystem_affinity_dist_influence
        d["s_ecosystem_affinity_scale_influence"] = psy.s_ecosystem_affinity_scale_influence

        save_u_mask_in_dict(category_str="s_ecosystem_affinity",)

    #Repulsion

    d["s_ecosystem_repulsion_allow"] = psy.s_ecosystem_repulsion_allow
    if psy.s_ecosystem_repulsion_allow:

        for i in (1,2,3):
                        
            d[f"s_ecosystem_repulsion_{i:02}_ptr"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_ptr")
            if (getattr(psy, f"s_ecosystem_repulsion_{i:02}_ptr")!=""):

                d[f"s_ecosystem_repulsion_{i:02}_type"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_type")
                d[f"s_ecosystem_repulsion_{i:02}_max_value"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_max_value")
                d[f"s_ecosystem_repulsion_{i:02}_max_falloff"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_max_falloff")

        d["s_ecosystem_repulsion_dist_influence"] = psy.s_ecosystem_repulsion_dist_influence
        d["s_ecosystem_repulsion_scale_influence"] = psy.s_ecosystem_repulsion_scale_influence

        save_u_mask_in_dict(category_str="s_ecosystem_repulsion",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> OFFSET"] = ""

    #Push Offset 

    d["s_push_offset_allow"] = psy.s_push_offset_allow
    if psy.s_push_offset_allow:

        d["s_push_offset_add_value"] = psy.s_push_offset_add_value
        d["s_push_offset_add_random"] = psy.s_push_offset_add_random
        d["s_push_offset_scale_value"] = psy.s_push_offset_scale_value
        d["s_push_offset_scale_random"] = psy.s_push_offset_scale_random

        save_u_mask_in_dict(category_str="s_push_offset",)

    #Push

    d["s_push_dir_allow"] = psy.s_push_dir_allow
    if psy.s_push_dir_allow:

        d["s_push_dir_method"] = psy.s_push_dir_method
        d["s_push_dir_add_value"] = psy.s_push_dir_add_value
        d["s_push_dir_add_random"] = psy.s_push_dir_add_random

        save_u_mask_in_dict(category_str="s_push_dir",)

    #Noise
    
    d["s_push_noise_allow"] = psy.s_push_noise_allow
    if psy.s_push_noise_allow:

        d["s_push_noise_vector"] = psy.s_push_noise_vector
        d["s_push_noise_speed"] = psy.s_push_noise_speed

        save_u_mask_in_dict(category_str="s_push_noise",)

    #Falling
    
    d["s_push_fall_allow"] = psy.s_push_fall_allow
    if psy.s_push_fall_allow:
        
        d["s_push_fall_height"] = psy.s_push_fall_height
        d["s_push_fall_key1_pos"] = psy.s_push_fall_key1_pos
        d["s_push_fall_key1_height"] = psy.s_push_fall_key1_height
        d["s_push_fall_key2_pos"] = psy.s_push_fall_key2_pos
        d["s_push_fall_key2_height"] = psy.s_push_fall_key2_height
        d["s_push_fall_stop_when_initial_z"] = psy.s_push_fall_stop_when_initial_z
    
        d["s_push_fall_turbulence_allow"] = psy.s_push_fall_turbulence_allow
        if psy.s_push_fall_turbulence_allow:
            
            d["s_push_fall_turbulence_spread"] = psy.s_push_fall_turbulence_spread
            d["s_push_fall_turbulence_speed"] = psy.s_push_fall_turbulence_speed
            d["s_push_fall_turbulence_rot_vector"] = psy.s_push_fall_turbulence_rot_vector
            d["s_push_fall_turbulence_rot_factor"] = psy.s_push_fall_turbulence_rot_factor

        save_u_mask_in_dict(category_str="s_push_fall",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> WIND"] = ""

    #Wind Wave 

    d["s_wind_wave_allow"] = psy.s_wind_wave_allow
    if psy.s_wind_wave_allow:

        d["s_wind_wave_speed"] = psy.s_wind_wave_speed
        d["s_wind_wave_force"] = psy.s_wind_wave_force
        d["s_wind_wave_swinging"] = psy.s_wind_wave_swinging
        d["s_wind_wave_scale_influence"] = psy.s_wind_wave_scale_influence
        d["s_wind_wave_texture_scale"] = psy.s_wind_wave_texture_scale
        d["s_wind_wave_texture_turbulence"] = psy.s_wind_wave_texture_turbulence
        d["s_wind_wave_texture_brightness"] = psy.s_wind_wave_texture_brightness
        d["s_wind_wave_texture_contrast"] = psy.s_wind_wave_texture_contrast

        d["s_wind_wave_dir_method"] = psy.s_wind_wave_dir_method

        if (psy.s_wind_wave_dir_method=="vcol"):
            
            d["s_wind_wave_flowmap_ptr"] = psy.s_wind_wave_flowmap_ptr
            d["s_wind_wave_direction"] = psy.s_wind_wave_direction

        elif (psy.s_wind_wave_dir_method=="fixed"):

            d["s_wind_wave_direction"] = psy.s_wind_wave_direction
        
        save_u_mask_in_dict(category_str="s_wind_wave",)

    #Wind Noise 

    d["s_wind_noise_allow"] = psy.s_wind_noise_allow
    if psy.s_wind_noise_allow:

        d["s_wind_noise_force"] = psy.s_wind_noise_force
        d["s_wind_noise_speed"] = psy.s_wind_noise_speed

        save_u_mask_in_dict(category_str="s_wind_noise",)

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INSTANCING"] = ""

    d["s_instances_method"] = psy.s_instances_method

    #s_instances_coll_ptr never for presets, that's for biomes

    d["s_instances_seed"] = psy.s_instances_seed
    d["s_instances_is_random_seed"] = psy.s_instances_is_random_seed
    d["s_instances_method"] = psy.s_instances_method
    d["s_instances_pick_method"] = psy.s_instances_pick_method

    pick_method = psy.s_instances_pick_method

    if (pick_method=="pick_rate"):

        for i in range(1,21):
            d[f"s_instances_id_{i:02}_rate"] = getattr(psy,f"s_instances_id_{i:02}_rate")

    elif (pick_method=="pick_scale"):

        for i in range(1,21):
            d[f"s_instances_id_{i:02}_scale_min"] = getattr(psy,f"s_instances_id_{i:02}_scale_min")
            d[f"s_instances_id_{i:02}_scale_max"] = getattr(psy,f"s_instances_id_{i:02}_scale_max")
        d["s_instances_id_scale_method"] = psy.s_instances_id_scale_method

    elif (pick_method=="pick_color"):

        for i in range(1,21):
            d[f"s_instances_id_{i:02}_color"] = getattr(psy,f"s_instances_id_{i:02}_color")
        d["s_instances_id_color_tolerence"] = psy.s_instances_id_color_tolerence
        d["s_instances_id_color_sample_method"] = psy.s_instances_id_color_sample_method

        sample_method = d["s_instances_id_color_sample_method"]
        if (sample_method=="vcol"):
            d["s_instances_vcol_ptr"] = psy.s_instances_vcol_ptr
        elif (sample_method=="text"):
            save_texture_ptr_in_dict(category_str=f"s_instances", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

    elif (pick_method=="pick_cluster"):

        d["s_instances_pick_cluster_projection_method"] = psy.s_instances_pick_cluster_projection_method
        d["s_instances_pick_cluster_scale"] = psy.s_instances_pick_cluster_scale
        d["s_instances_pick_cluster_blur"] = psy.s_instances_pick_cluster_blur
        d["s_instances_pick_clump"] = psy.s_instances_pick_clump

    # not currently used 
    # if psy.s_instances_method=="ins_volume":
    #     d["s_instances_volume_density"] = psy.s_instances_volume_density
    #     d["s_instances_volume_voxel_ammount"] = psy.s_instances_volume_voxel_ammount

    return d


# ooooooooo.                          .                  ooooooooo.                                             .
# `888   `Y88.                      .o8                  `888   `Y88.                                         .o8
#  888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.        888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#  888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#  888          .oP"888  `"Y88b.    888   888ooo888       888          888     888ooo888 `"Y88b.  888ooo888   888
#  888         d8(  888  o.  )88b   888 . 888    .o       888          888     888    .o o.  )88b 888    .o   888 .
# o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"


class SCATTER5_OT_apply_preset_dialog(bpy.types.Operator):

    bl_idname  = "scatter5.apply_preset_dialog"
    bl_label   = translate("Paste the Preset to the Selected System(s)")
    bl_description = translate("Paste the Active Preset Settings to the Selected-System(s)")
    bl_options = {'REGISTER', 'INTERNAL'}

    single_category : bpy.props.StringProperty(default="")

    method : bpy.props.StringProperty(default="selection")


    @classmethod
    def poll(cls, context):
        return bpy.context.scene.scatter5.emitter is not None

    def execute(self, context):

        filter = {
            "color" : False,
            "distribution" : self.single_category=="s_distribution",
            "rot" : self.single_category=="s_rot",
            "scale" : self.single_category=="s_scale",
            "pattern" : self.single_category=="s_pattern",
            "proximity" : self.single_category=="s_proximity",
            "ecosystem" : self.single_category=="s_ecosystem",
            "push" : self.single_category=="s_push",
            "abiotic" : self.single_category=="s_abiotic",
            "wind" : self.single_category=="s_wind",
            "instances" : self.single_category=="s_instances",
            }

        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]

        for p in psys:

            #hide for optimization 
            hide_viewport = p.hide_viewport
            p.hide_viewport = True

            #apply preset to settings
            json_path = os.path.join( directories.lib_presets , bpy.context.window_manager.scatter5_preset_gallery + ".preset" )
            path = os.path.dirname(json_path)
            file_name = os.path.basename(json_path)
            d = json_to_dict( path=path, file_name=file_name)

            if (self.single_category=="all"):
                  dict_to_settings( d, p, )
            else: dict_to_settings( d, p, filter=filter )

            #then restore 
            p.hide_viewport = hide_viewport 
            
        bpy.ops.ed.undo_push(message=translate("Pasting Preset to Settings"))

        return {'FINISHED'}


#  .oooooo..o                                      ooooooooo.                                             .
# d8P'    `Y8                                      `888   `Y88.                                         .o8
# Y88bo.       .oooo.   oooo    ooo  .ooooo.        888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#  `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b       888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#      `"Y88b  .oP"888    `88..8'   888ooo888       888          888     888ooo888 `"Y88b.  888ooo888   888
# oo     .d8P d8(  888     `888'    888    .o       888          888     888    .o o.  )88b 888    .o   888 .
# 8""88888P'  `Y888""8o     `8'     `Y8bod8P'      o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"


class SCATTER5_OT_save_preset_to_disk_dialog(bpy.types.Operator):

    bl_idname      = "scatter5.save_preset_to_disk_dialog"
    bl_label       = translate("Export Selected System(s) as Preset(s)")
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
        return (bpy.context.scene.scatter5.emitter is not None) and (os.path.exists(directories.lib_presets))

    def invoke(self, context, event):
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout  = self.layout

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]

        box, is_open = templates.sub_panel(self, layout, 
            prop_str   = "add_preset_save", 
            icon       = "PRESET_NEW", 
            name       = "         " + translate("Export Selected System(s) as Preset(s)"),
            #description= "",
            #doc        = "I still need to write the docs, this plugin is currently in WIP and you are not using the final version ",
            )
        if is_open:

            sep = box.row()
            s1 = sep.separator(factor=0.2)
            s2 = sep.column()
            s3 = sep.separator(factor=0.2)

            txt = s2.column(align=True)
            txt.label(text=translate("Scatter will create the Following Presets :"))
            txt.scale_y = 0.8
            future_names = [ legal(p.name).lower().replace(" ","_") for p in psys]
            one_exists = False
            if future_names:
                for n in future_names: 
                    rtxt = txt.row()
                    rtxt.active = False
                    exists = os.path.exists(os.path.join( scat_scene.precrea_creation_directory, f"{n}.preset" ))
                    if exists: 
                        rtxt.alert = True
                        one_exists = True     
                    rtxt.label(text=f" - ''{n}.preset''")
            else:
                rtxt = txt.row()
                rtxt.active = False
                rtxt.label(text="   "+f"Nothing Found")
                
            s2.separator()

            word_wrap( string=translate("Note that not all properties can be exported in presets. A '.preset' file is only but a '.json' text file storing your settings."), layout=s2, alignment="LEFT", max_char=50,)

            s2.separator()

            sub = s2.row()
            sub.prop(scat_scene,"precrea_use_random_seed",)
            sub = s2.row()
            sub.prop(scat_scene,"precrea_texture_is_unique",)
            sub = s2.row()
            sub.prop(scat_scene,"precrea_texture_random_loc",)

            s2.separator()
            
            exp = s2.column(align=True)
            exp.label(text=translate("Export Directory")+":")
            exp.prop(scat_scene,"precrea_creation_directory",text="")

            txt = s2.column()
            txt.scale_y = 0.8
            txt.active = False
            txt.label(text=translate("Preset Gallery location is by default located in"))
            txt.operator("scatter5.open_directory", text=f"'{directories.lib_presets}", emboss=False,).folder = directories.lib_presets

            s2.separator()

            sub = s2.column()
            sub.alert = one_exists
            sub.prop(scat_scene,"precrea_overwrite",)
            sub = s2.row()
            sub.prop(scat_scene,"precrea_auto_render",)

            templates.sub_spacing(box)
            layout.separator()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psys    = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]
        
        for p in psys: 

            d = settings_to_dict(p,
                use_random_seed=scat_scene.precrea_use_random_seed,
                texture_is_unique=scat_scene.precrea_texture_is_unique,
                texture_random_loc=scat_scene.precrea_texture_random_loc,
                ) 

            file_name = legal(d["name"]).lower().replace(" ","_")

            preset_path = os.path.join( scat_scene.precrea_creation_directory, f"{file_name}.preset" )
            if os.path.exists(preset_path) and not scat_scene.precrea_overwrite:
                bpy.ops.scatter5.popup_menu(msgs=translate("File already exists! Overwriting not allowed."),title=translate("Preset Creation Skipped"),icon="ERROR",)
                continue 

            dict_to_json( d, path=scat_scene.precrea_creation_directory, file_name=file_name, extension=".preset",)
                

            if scat_scene.precrea_auto_render: 
                bpy.ops.scatter5.generate_thumbnail(json_path=preset_path, render_output=preset_path.replace(".preset",".jpg"))

        reload_gallery()

        return {'FINISHED'}


# oooooooooo.                                         oooooooooooo
# `888'   `Y8b                                        `888'     `8
#  888      888 oooo    ooo ooo. .oo.    .oooo.        888         ooo. .oo.   oooo  oooo  ooo. .oo.  .oo.
#  888      888  `88.  .8'  `888P"Y88b  `P  )88b       888oooo8    `888P"Y88b  `888  `888  `888P"Y88bP"Y88b
#  888      888   `88..8'    888   888   .oP"888       888    "     888   888   888   888   888   888   888
#  888     d88'    `888'     888   888  d8(  888       888       o  888   888   888   888   888   888   888
# o888bood8P'       .8'     o888o o888o `Y888""8o     o888ooooood8 o888o o888o  `V88V"V8P' o888o o888o o888o
#               .o..P'
#               `Y8P'


from .. resources.icons import get_previews_from_directory, remove_previews


#need to store bpy.utils.previews here
Gallery = {}


def gallery_register():
    """Dynamically create EnumProperty from custom loaded previews"""

    items = [ 
                (
                    translate("Nothing Found"), 
                    translate("Nothing Found"), 
                    "", 
                    cust_icon("W_DEFAULT_NO_PRESET_FOUND"), 
                    0, 
                )
            ]

    global Gallery 
    Gallery = get_previews_from_directory(directories.lib_presets, format=".jpg")

    listdir = [ file for file in os.listdir(directories.lib_presets) ]
    listpreset = [ file.replace(".preset","") for file in listdir if file.endswith(".preset") ]

    if (len(listpreset)!=0): 
        items = [ 
                    (
                        e, #enum value
                        e.title().replace("_"," "), #enum name
                        "", #enum description
                        Gallery[e].icon_id if e in Gallery else cust_icon("W_DEFAULT_PREVIEW"), #enum icon
                        i, #enumeration 
                    )  
                    for i,e in enumerate(listpreset)
                ]


    #gather properties from chosen preset

    def update_scatter5_preset_gallery(self, context):

        dprint("PROP_FCT: updating WindowManager.scatter5_preset_gallery")
        
        scat_scene = bpy.context.scene.scatter5
        scat_scene.preset_path = os.path.join( directories.lib_presets , bpy.context.window_manager.scatter5_preset_gallery + ".preset" )

        d = json_to_dict( path=directories.lib_presets, file_name=self.scatter5_preset_gallery + ".preset",)
            
        #Gather information from .preset file to display above operator

        #Get Name of the Preset

        if ("name" in d):
            scat_scene.preset_name = d["name"]

        #Color Information 

        if ("s_color" in d):
            scat_scene.preset_color = d["s_color"]

        #Density Estimation need to update when changing the preset 
        
        scat_scene.estimated_preset_density = d["estimated_density"] if ("estimated_density" in d) else 0

        scat_scene.estimated_preset_density_method = ""
        if ("s_distribution_space" in d):
            scat_scene.estimated_preset_density_method += " "+d["s_distribution_space"]
        if ("s_distribution_method" in d):
            scat_scene.estimated_preset_density_method += " "+d["s_distribution_method"]

        return None

    bpy.types.WindowManager.scatter5_preset_gallery = bpy.props.EnumProperty(
        items = items,
        update = update_scatter5_preset_gallery,
        )

    return None 


def gallery_unregister():

    del bpy.types.WindowManager.scatter5_preset_gallery

    global Gallery 
    remove_previews(Gallery)

    return None 


def reload_gallery():

    gallery_unregister()
    gallery_register()

    return None 


class SCATTER5_OT_reload_preset_gallery(bpy.types.Operator):

    bl_idname      = "scatter5.reload_preset_gallery"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):
        reload_gallery()
        return {'FINISHED'} 



class SCATTER5_OT_preset_enum_skip(bpy.types.Operator):

    bl_idname      = "scatter5.preset_enum_skip"
    bl_label       = translate("Skip Preset")
    bl_description = ""
    bl_options     = {'INTERNAL'}

    direction : bpy.props.StringProperty(default="LEFT") #LEFT/RIGHT

    def execute(self, context):
        wm = bpy.context.window_manager 
        enum_items = wm.bl_rna.properties["scatter5_preset_gallery"].enum_items

        if len(enum_items)<=1:
            return {'FINISHED'}
 
        def real_name(name):
            return name.lower().replace(" ","_")

        def get_enum_order_and_length(string_value):
            for e in enum_items:
                if ( string_value==real_name(e.name) ): #unfortunately no way to access it's value? 
                    return e.value , len(enum_items) 

        i,l = get_enum_order_and_length( wm.scatter5_preset_gallery )

        # Go Forward/Backward
        if (self.direction=="LEFT"):
            i -= 1
        elif (self.direction=="RIGHT"):
            i += 1

        #Loop over
        if (i==l):
            i = 0  
        if (i<0):
            i = l-1

        wm.scatter5_preset_gallery = real_name(enum_items[i].name)

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = [

    SCATTER5_OT_apply_preset_dialog,
    SCATTER5_OT_save_preset_to_disk_dialog,
    SCATTER5_OT_preset_enum_skip,
    SCATTER5_OT_reload_preset_gallery,

    ]

