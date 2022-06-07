import bpy

from bl_operators.presets import AddPresetBase
from bl_ui.utils import PresetPanel
from bpy.types import Panel, Menu, Operator


# Camera Presets
class PHOTOGRAPHER_MT_CameraPresets(Menu):
    bl_label = 'Camera Presets'
    preset_subdir = 'photographer/camera'
    preset_operator = 'script.execute_preset'
    draw = Menu.draw_preset

class PHOTOGRAPHER_OT_AddCameraPreset(AddPresetBase, Operator):
    """Saves Camera Preset file into Scripts>Presets>Photographer"""
    bl_idname = 'photographer.camera_add_preset'
    bl_label = 'Save Camera preset'
    preset_menu = 'PHOTOGRAPHER_MT_CameraPresets'

    # Common variable used for all preset values
    preset_defines = [
        'camera = bpy.context.scene.camera.data',
        'photographer = bpy.context.scene.camera.data.photographer',
    ]

    preset_values = [
        'photographer.sensor_type',
        'camera.sensor_width',
        'camera.sensor_height',
        'camera.clip_start',
        'camera.clip_end',
        'camera.show_passepartout',
        'camera.passepartout_alpha',
    ]

    # Directory to store the presets
    preset_subdir = 'photographer/camera'

class PHOTOGRAPHER_PT_CameraPresets(PresetPanel, Panel):
    bl_label = 'Camera Presets'
    preset_subdir = 'photographer/camera'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'photographer.camera_add_preset'

    @classmethod
    def poll(cls,context):
        return bpy.context.scene.camera

# Lens Presets
class PHOTOGRAPHER_MT_LensPresets(Menu):
    bl_label = 'Lens Presets'
    preset_subdir = 'photographer/lens'
    preset_operator = 'script.execute_preset'
    draw = Menu.draw_preset

class PHOTOGRAPHER_OT_AddLensPreset(AddPresetBase, Operator):
    """Saves Lens Preset file into Scripts>Presets>Photographer"""
    bl_idname = 'photographer.lens_add_preset'
    bl_label = 'Save Lens preset'
    preset_menu = 'PHOTOGRAPHER_MT_LensPresets'

    # Common variable used for all preset values
    preset_defines = [
        'camera = bpy.context.scene.camera.data',
        'photographer = bpy.context.scene.camera.data.photographer',
        'luxcore = bpy.context.scene.camera.data.luxcore'
    ]

    preset_values = [
        'photographer.focal',
        'photographer.fisheye',
        'photographer.lens_shift',
        'photographer.aperture',
        'photographer.aperture_preset',
        'photographer.aperture_slider_enable',
        'photographer.focus_plane_color',
        'photographer.lock_vertical_fov',
        'camera.dof.focus_distance',
        'camera.dof.aperture_ratio',
        'camera.dof.aperture_blades',
        'camera.dof.aperture_rotation',
        # 'luxcore.bokeh.non_uniform',
        # 'luxcore.bokeh.blades',
        # 'luxcore.bokeh.anisotropy',
    ]

    # Directory to store the presets
    preset_subdir = 'photographer/lens'

class PHOTOGRAPHER_PT_LensPresets(PresetPanel, Panel):
    bl_label = 'Lens Presets'
    preset_subdir = 'photographer/lens'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'photographer.lens_add_preset'

    @classmethod
    def poll(cls,context):
        return bpy.context.scene.camera

# Exposure Presets
class PHOTOGRAPHER_MT_ExposurePresets(Menu):
    bl_label = 'Exposure Presets'
    preset_subdir = 'photographer/exposure'
    preset_operator = 'script.execute_preset'
    draw = Menu.draw_preset

class PHOTOGRAPHER_OT_AddExposurePreset(AddPresetBase, Operator):
    """Saves Camera Preset file into Scripts>Presets>Photographer"""
    bl_idname = 'photographer.exposure_add_preset'
    bl_label = 'Save Exposure preset'
    preset_menu = 'PHOTOGRAPHER_MT_ExposurePresets'

    # Common variable used for all preset values
    preset_defines = [
        'camera = bpy.context.scene.camera.data',
        'photographer = bpy.context.scene.camera.data.photographer',
    ]

    preset_values = [
        'photographer.exposure_mode',
        'photographer.ev',
        'photographer.exposure_compensation',
        'photographer.center_weight',
        'photographer.ae_speed',
        'photographer.shutter_speed_slider_enable',
        'photographer.shutter_mode',
        'photographer.shutter_speed_preset',
        'photographer.shutter_angle_preset',
        'photographer.shutter_speed',
        'photographer.shutter_angle',
        'photographer.aperture_slider_enable',
        'photographer.aperture',
        'photographer.aperture_preset',
        'photographer.iso_slider_enable',
        'photographer.iso',
        'photographer.iso_preset',
        'photographer.motionblur_enabled',
        'photographer.falsecolor_enabled',
    ]

    # Directory to store the presets
    preset_subdir = 'photographer/exposure'

class PHOTOGRAPHER_PT_ExposurePresets(PresetPanel, Panel):
    bl_label = 'Exposure Presets'
    preset_subdir = 'photographer/exposure'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'photographer.exposure_add_preset'

    @classmethod
    def poll(cls,context):
        return bpy.context.scene.camera

# Resolution Presets
class PHOTOGRAPHER_MT_ResolutionPresets(Menu):
    bl_label = 'Resolution Presets'
    preset_subdir = 'photographer/resolution'
    preset_operator = 'script.execute_preset'
    draw = Menu.draw_preset

class PHOTOGRAPHER_OT_AddResolutionPreset(AddPresetBase, Operator):
    """Saves Camera Preset file into Scripts>Presets>Photographer"""
    bl_idname = 'photographer.resolution_add_preset'
    bl_label = 'Save Resolution preset'
    preset_menu = 'PHOTOGRAPHER_MT_ResolutionPresets'

    # Common variable used for all preset values
    preset_defines = [
        'render = bpy.context.scene.render',
        'photographer = bpy.context.scene.camera.data.photographer',
    ]

    preset_values = [
        'photographer.resolution_mode',
        'photographer.resolution_x',
        'photographer.resolution_y',
        'photographer.ratio_x',
        'photographer.ratio_y',
        'photographer.resolution_rotation',
        'photographer.longedge',
        'render.resolution_percentage',
    ]

    # Directory to store the presets
    preset_subdir = 'photographer/resolution'

class PHOTOGRAPHER_PT_ResolutionPresets(PresetPanel, Panel):
    bl_label = 'Resolution Presets'
    preset_subdir = 'photographer/resolution'
    preset_operator = 'script.execute_preset'
    preset_add_operator = 'photographer.resolution_add_preset'

    @classmethod
    def poll(cls,context):
        return bpy.context.scene.camera
