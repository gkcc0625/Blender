import bpy
import json
from bpy.types import Operator
from mathutils import Vector

class BAGAPIE_OT_ungroup(Operator):
    """ Ungroup the selected group """
    bl_idname = "bagapie.ungroup"
    bl_label = 'Ungroup'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    def execute(self, context):

        target = bpy.context.active_object
        
        if target["bagapie"] == "bound_box":

            for child in target["bagapie_child"]:

                child.hide_select = False
                matrixcopy = child.matrix_world.copy()
                if child.parent == target:
                    child.parent = None
                child.matrix_world = matrixcopy
        
            bpy.data.objects.remove(target)


        return {'FINISHED'}

class BAGAPIE_OT_group(Operator):
    """Group selected objects. A bounding box is created and the objects are no longer selectable. Use Edit to make them selectable."""
    bl_idname = 'bagapie.group'
    bl_label = 'Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None
        )

    def execute(self, context):
        
    # COLLECTION BagaPie_Manage
        if bpy.data.collections.get("BagaPie") is None:  
            main_coll = bpy.data.collections.new("BagaPie")
            bpy.context.scene.collection.children.link(main_coll)
            manage_coll = bpy.data.collections.new("BagaPie_Manage")
            main_coll.children.link(manage_coll)
            group_coll = bpy.data.collections.new("BagaPie_Group")
            manage_coll.children.link(group_coll)
        # create sub collection if it does not exist for array object
        elif bpy.data.collections.get("BagaPie_Manage") is None:
            manage_coll = bpy.data.collections.new("BagaPie_Manage")
            bpy.data.collections.get("BagaPie").children.link(manage_coll)
            group_coll = bpy.data.collections.new("BagaPie_Group")
            manage_coll.children.link(group_coll)
        elif bpy.data.collections.get("BagaPie_Group") is None:
            group_coll = bpy.data.collections.new("BagaPie_Group")
            bpy.data.collections.get("BagaPie_Manage").children.link(group_coll)
        # if all the collection already exist, the array object is stored in the existant one.
        else:
            group_coll = bpy.data.collections.get("BagaPie_Group")

        ob = bpy.context.active_object
        objs = bpy.context.selected_objects
        bpy.ops.mesh.primitive_cube_add()
        target = bpy.context.active_object
        target.location=(0, 0, 0)
        target.name = "BagaPie_Group_BoundBox"
        target.display_type = 'WIRE'
        target.visible_camera = False
        target.visible_diffuse = False
        target.visible_glossy = False
        target.visible_transmission = False
        target.visible_volume_scatter = False
        target.visible_shadow = False
        target.hide_render = True
        target["bagapie"] = str("bound_box")
        target["bagapie_child"] = objs

        # Move Bounding Box from Coll A to B
        current_coll = target.users_collection
        current_coll[0].objects.unlink(target)
        group_coll.objects.link(target)

        current_bound_box = [ob.matrix_world @ Vector(corner) for corner in ob.bound_box]
        obj_bound_box = current_bound_box

        for obj in objs:

            # There is probably a beter way to do that ...

            obj_bound_box = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            index = 0
            if obj_bound_box[index][0] < current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] < current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] < current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 1
            if obj_bound_box[index][0] < current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] < current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] > current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 2
            if obj_bound_box[index][0] < current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] > current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] > current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 3
            if obj_bound_box[index][0] < current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] > current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] < current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 4
            if obj_bound_box[index][0] > current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] < current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] < current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 5
            if obj_bound_box[index][0] > current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] < current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] > current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 6
            if obj_bound_box[index][0] > current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] > current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] > current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]
            index = 7
            if obj_bound_box[index][0] > current_bound_box[index][0]:
                current_bound_box[index][0] = obj_bound_box[index][0]
            if obj_bound_box[index][1] > current_bound_box[index][1]:
                current_bound_box[index][1] = obj_bound_box[index][1]
            if obj_bound_box[index][2] < current_bound_box[index][2]:
                current_bound_box[index][2] = obj_bound_box[index][2]

        id = [0,1,3,2,4,5,7,6]

        for verts in target.data.vertices:
            verts.co  = current_bound_box[target.data.vertices[id[verts.index]].index]
    
        for obj in objs:
            if obj.parent == None:
                obj.parent = target
            obj.hide_select = True

        bpy.context.view_layer.objects.active = target
        target.display_type = 'BOUNDS'
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
        
        return {'FINISHED'}

class BAGAPIE_OT_editgroup(Operator):
    """Edit selected group"""
    bl_idname = 'bagapie.editgroup'
    bl_label = 'Edit Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        target = bpy.context.active_object
        for obj in target["bagapie_child"]:
                obj.hide_select = False

        return {'FINISHED'}

class BAGAPIE_OT_lockgroup(Operator):
    """Make group objects non selectable"""
    bl_idname = 'bagapie.lockgroup'
    bl_label = 'Lock Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        target = bpy.context.active_object
        for obj in target["bagapie_child"]:
                obj.hide_select = True

        return {'FINISHED'}

class BAGAPIE_OT_duplicategroup(Operator):
    """Duplicate Group"""
    bl_idname = 'bagapie.duplicategroup'
    bl_label = 'Duplicate Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        target = bpy.context.active_object
        locked = False
        if target["bagapie_child"]:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in target["bagapie_child"]:
                    if obj.hide_select == True:
                        locked = True
                    obj.hide_select = False
                    obj.select_set(True)
            target.select_set(True)
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
            if locked == True:
                for obj in target["bagapie_child"]:
                        obj.hide_select = True
                target = bpy.context.active_object
                for obj in target["bagapie_child"]:
                        obj.hide_select = True
            else:
                target = bpy.context.active_object
            bpy.ops.transform.translate("INVOKE_DEFAULT")


        return {'FINISHED'}

class BAGAPIE_OT_duplicatelinkedgroup(Operator):
    """Duplicate Group witk link"""
    bl_idname = 'bagapie.duplicatelinkedgroup'
    bl_label = 'Duplicate Linked Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        target = bpy.context.active_object
        locked = False
        if target["bagapie_child"]:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in target["bagapie_child"]:
                    if obj.hide_select == True:
                        locked = True
                    obj.hide_select = False
                    obj.select_set(True)
            target.select_set(True)
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'})
            if locked == True:
                for obj in target["bagapie_child"]:
                        obj.hide_select = True
                target = bpy.context.active_object
                for obj in target["bagapie_child"]:
                        obj.hide_select = True
            else:
                target = bpy.context.active_object
            bpy.ops.transform.translate("INVOKE_DEFAULT")


        return {'FINISHED'}

class BAGAPIE_OT_deletegroup(Operator):
    """Delete group and it's content"""
    bl_idname = 'bagapie.deletegroup'
    bl_label = 'Delete Group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute (self, context):
        
        target = bpy.context.active_object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in target["bagapie_child"]:
                obj.hide_select = False
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.view_layer.objects.active = target
        target.select_set(True)
        bpy.ops.object.delete()

        return {'FINISHED'}

