import bpy
from bpy.app.handlers import persistent
from mathutils.geometry import distance_point_to_plane
from mathutils import Vector


def distance_to_plane(cam_matrix,tracker_matrix):
    cam_dir = cam_matrix.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    dist = abs(distance_point_to_plane(cam_matrix.translation, tracker_matrix.translation, cam_dir))
    return -dist

@persistent
def load_handler(dummy):
    # register your drivers
    bpy.app.driver_namespace['distance_to_plane'] = distance_to_plane

def register():
    load_handler(None)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
