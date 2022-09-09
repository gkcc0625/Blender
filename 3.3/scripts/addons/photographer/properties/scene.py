import bpy
from .. import world as wd
from ..constants import addon_name
from ..ui import library
from bpy.props import (BoolProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       StringProperty,
                       )

def update_comp_exposure(self,context):
    if self.comp_exposure:
        bpy.ops.photographer.add_exposure_node()
    else:
        bpy.ops.photographer.disable_exposure_node()

class SceneSettings(bpy.types.PropertyGroup):
    cam_list_sorting : EnumProperty(
        name = "Sorting options for Camera list",
        items = [('ALPHA','Sort Alphabetically','','SORTALPHA',0),
                ('COLLECTION','Group by Collection','','OUTLINER_OB_GROUP_INSTANCE',1)],
        options = {'HIDDEN'},
        # default = bpy.context.preferences.addons[addon_name].preferences.default_cam_list_sorting,
    )
    comp_exposure : BoolProperty(
        name = "Apply at Compositing",
        description = ("Apply Exposure during Compositing. \nExposure won't be "
                        "visible in viewport, but will be applied to EXR files"),
        default = False,
        options = {'HIDDEN'},
        update = update_comp_exposure,
    )

class LightMixerSettings(bpy.types.PropertyGroup):
    solo_active: BoolProperty(
        name="Solo",
        default=False,
        options = {'HIDDEN'},
    )
    world_show_more: BoolProperty(
        name="Expand World settings",
        default=True,
        options = {'HIDDEN'},
    )
    hdri_tex: EnumProperty(
        name="HDRI Texture",
        items=wd.enum_previews_hdri_tex,
        update=wd.update_hdri_tex,
    )
    hdri_category: EnumProperty(
        name="HDRI Category",
        items=library.subfolders_return,
        description="HDRI Subfolder category",
        update=wd.update_hdri_tex,
    )
    hdri_rotation: FloatProperty(
        name="Rotation",
        default=0, soft_min=-3.141593, soft_max=3.141593, unit='ROTATION',
        get=wd.get_hdri_rotation,
        set=wd.set_hdri_rotation,
    )
    hdri_use_temperature: BoolProperty(
        name="Use Color Temperature",
        default=True,
        options = {'HIDDEN'},
        update = wd.update_hdri_use_temperature,
    )
    hdri_temperature: FloatProperty(
        name="Temperature",
        default=6500, min=0, soft_min=1100, soft_max=13000,
        get=wd.get_hdri_temperature,
        set=wd.set_hdri_temperature,
    )
    hdri_tint: FloatProperty(
        name="Tint",
        default=0, min=-100, max=100,
        get=wd.get_hdri_tint,
        set=wd.set_hdri_tint,
    )
    hdri_color: FloatVectorProperty(
        name="Color Multiplier",
        subtype='COLOR',
        min=0.0, max=1.0, size=4,
        default=(1.0,1.0,1.0,1.0),
        get=wd.get_hdri_color,
        set=wd.set_hdri_color,
    )
    hdri_blur: FloatProperty(
        name="Blur",
        default=0, min=0, soft_max=1,
        get=wd.get_hdri_blur,
        set=wd.set_hdri_blur,
    )
