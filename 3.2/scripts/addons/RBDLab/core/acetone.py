import bpy
from bpy.types import Operator
import bmesh
from mathutils.bvhtree import BVHTree
from .functions import get_first_and_last_keyframe_frame, set_active_object, unhide_collection_in_viewport, hide_collection_in_viewport


def intersection_check(dummy):
    objects = []
    for obj in bpy.data.collections[bpy.context.scene.rbdlab_props.target_collection].objects:
        if obj.type == 'MESH' and obj.visible_get():
            objects.append(obj.name)

    # para evitar entrar en loop al hacer play:
    all_max = []
    for acetone_object in bpy.context.scene["acetone_objects"]:
        all_max.append(acetone_object["min_max_keyframnes"][1])

    # if bpy.context.scene.frame_current == bpy.context.scene.frame_end:
    if bpy.context.scene.frame_current == max(all_max): # las frame with keyframes in acetone object
        bpy.ops.screen.animation_cancel(restore_frame=True)
        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        # quitar
        if intersection_check in bpy.app.handlers.frame_change_post:
            bpy.context.scene.rigidbody_world.enabled = True
            bpy.app.handlers.frame_change_post.remove(intersection_check)

    obj_now = bpy.data.objects['Sphere_Helper'].name
    # for ob in objects:
    #    ob.animation_data_clear()
    for obj_next in objects:
        # print(obj_next)
        #
        # create bmesh objects
        bm1 = bmesh.new()
        bm2 = bmesh.new()
        #
        # fill bmesh data from objects
        bm1.from_mesh(bpy.context.scene.objects[obj_now].data)
        bm2.from_mesh(bpy.context.scene.objects[obj_next].data)
        #
        # fixed it here:
        bm1.transform(bpy.context.scene.objects[obj_now].matrix_world)
        bm2.transform(bpy.context.scene.objects[obj_next].matrix_world)
        #
        # make BVH tree from BMesh of objects
        obj_now_BVHtree = BVHTree.FromBMesh(bm1)
        obj_next_BVHtree = BVHTree.FromBMesh(bm2)
        #
        # get intersecting pairs
        inter = obj_now_BVHtree.overlap(obj_next_BVHtree)
        #
        # print("i got this far 1")
        #
        # if list is empty, no objects are touching
        # print(bpy.context.scene.frame_current)
        if inter != []:
            # print(obj_now + " and " + obj_next + " are touching!")

            # dynamic:
            # if not bpy.context.scene.objects[obj_next].rigid_body.enabled:
            #     bpy.context.scene.objects[obj_next].keyframe_insert(
            #                                                         data_path="rigid_body.enabled",
            #                                                         frame=(bpy.context.scene.frame_current - 1)
            #     )
            #     bpy.context.scene.objects[obj_next].rigid_body.enabled = True
            #     bpy.context.scene.objects[obj_next].keyframe_insert(
            #                                                         data_path="rigid_body.enabled",
            #                                                         frame=(bpy.context.scene.frame_current)
            #     )

            # deactivation:
            if bpy.context.scene.objects[obj_next].rigid_body.use_deactivation:
                bpy.context.scene.objects[obj_next].keyframe_insert(
                                                                    data_path="rigid_body.use_deactivation",
                                                                    frame=(bpy.context.scene.frame_current - 1)
                                                                    )
                bpy.context.scene.objects[obj_next].rigid_body.use_deactivation = False
                bpy.context.scene.objects[obj_next].keyframe_insert(
                                                                    data_path="rigid_body.use_deactivation",
                                                                    frame=(bpy.context.scene.frame_current)
                                                                    )

            # break constraints:
            for const in bpy.context.scene.objects[obj_next]['rbdlab_constraints'].split():
                if bpy.context.scene.objects[const].rigid_body_constraint.enabled:
                    bpy.context.scene.objects[const].keyframe_insert(
                                                                    data_path="rigid_body_constraint.enabled",
                                                                    frame=(bpy.context.scene.frame_current-1)
                                                                    )
                    bpy.context.scene.objects[const].rigid_body_constraint.enabled = False
                    bpy.context.scene.objects[const].keyframe_insert(
                                                                    data_path="rigid_body_constraint.enabled",
                                                                    frame=bpy.context.scene.frame_current
                                                                    )
                    # print(scene.objects[const].name, scene.objects[const].rigid_body_constraint.enabled)
        # else:
        # for const in scene.objects[obj_next]['rbdlab_constraints'].split():
        #    scene.objects[const].keyframe_insert(data_path="rigid_body_constraint.enabled", frame=bpy.context.scene.frame_current-1)
        #    scene.objects[const].rigid_body_constraint.enabled = True
        #    scene.objects[const].keyframe_insert(data_path="rigid_body_constraint.enabled", frame=bpy.context.scene.frame_current)


class ACETONE_OT_recording(Operator):
    bl_idname = "acetone.record"
    bl_label = "Recording"
    bl_options = {'REGISTER', 'UNDO'}

    # acetone_objects = bpy.data.objects['Sphere_Helper']

    def execute(self, context):
        if bpy.context.scene.rbdlab_props.target_collection:

            all_min = []
            bpy.context.scene["acetone_objects"] = [bpy.data.objects['Sphere_Helper']]
            for acetone_object in bpy.context.scene["acetone_objects"]:
                acetone_object["min_max_keyframnes"] = get_first_and_last_keyframe_frame(acetone_object)
                all_min.append(acetone_object["min_max_keyframnes"][0])

            bpy.context.scene.rigidbody_world.enabled = False
            bpy.app.handlers.frame_change_post.append(intersection_check)

            # first frame with keyframes in acetone object:
            bpy.context.scene.frame_current = min(all_min)

            bpy.ops.screen.animation_play()
        else:
            self.report({'WARNING'}, 'Target Collection is Empty!')
            return {'CANCELLED'}

        return {'FINISHED'}


class ACETONE_OT_add_helper(Operator):
    bl_idname = "acetone.addhelper"
    bl_label = "Add Helper"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.2, 0.2, 0.2))
        bpy.context.object.display_type = 'WIRE'
        bpy.context.object.name = "Sphere_Helper"
        return {'FINISHED'}


class ACETONE_OT_clean(Operator):
    bl_idname = "acetone.clean"
    bl_label = "Clean Acetone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # remove all keyframes to chunks in collection
        coll_name = bpy.context.scene.rbdlab_props.target_collection
        coll_const_name = coll_name + '_GlueConstraints'
        if coll_name:
            # unhide_collection_in_viewport(coll_const_name)

            for obj in bpy.data.collections[coll_name].objects:
                if obj.type == 'MESH' and obj.visible_get():
                    set_active_object(obj)
                    bpy.context.active_object.animation_data_clear()

            for obj in bpy.data.collections[coll_const_name].objects:
                if obj.type == 'EMPTY':
                    set_active_object(obj)
                    bpy.context.active_object.animation_data_clear()

            # hide_collection_in_viewport(coll_const_name)
            bpy.ops.rbd.update()
            bpy.ops.const.update()
        return {'FINISHED'}