import bpy
from bpy.app.handlers import persistent
from . import camera

@persistent
def update_render_camera(scene,depsgraph):
    if scene.camera:
        camera_ob = scene.camera
        camera_ob_eval = camera_ob.evaluated_get(depsgraph)
        # Dictionary of Photographer Camera properties
        for key in camera.PhotographerCameraSettings.__annotations__.keys() and camera_ob.data.photographer.keys():
            if key not in {'light_threshold_warning', 'preview_color_tint', 'preview_color_temp', 'ev'}:
                key_eval = camera_ob_eval.data.photographer[key]
                camera_ob.data.photographer[key] = key_eval

        # EV needs to be evaluated after manual settings
        camera_ob.data.photographer.ev = camera_ob_eval.data.photographer.ev

def register():
    bpy.app.handlers.frame_change_post.append(update_render_camera)

def unregister():
    bpy.app.handlers.frame_change_post.remove(update_render_camera)
