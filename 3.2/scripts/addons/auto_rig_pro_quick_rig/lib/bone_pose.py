import bpy


def get_pose_bone(name):
    return bpy.context.active_object.pose.bones.get(name)