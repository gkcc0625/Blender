import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers

class BAGAPIE_OT_makereal(Operator):
    """ Remove Bagapie Wall modifiers """
    bl_idname = "bagapie.makereal"
    bl_label = 'Make Real'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'EMPTY'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        empty_name = bpy.context.active_object.name
        bpy.ops.object.duplicates_make_real()
        target = bpy.context.selected_objects
        for targ in target:
            try:
                targ["bagapie"]
            except:
                targ["bagapie"] = None

            if targ["bagapie"] is not None:
                bpy.data.objects.remove(targ)
            else:
                del targ["bagapie"]

        empty = bpy.data.objects[empty_name]
        bpy.data.objects.remove(empty)

        return {'FINISHED'}

class BAGAPIE_OT_instance(Operator):
    """Creates walls from the edges of the selected object or from curves"""
    bl_idname = 'bagapie.instance'
    bl_label = bagapieModifiers['instance']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    #PROPERTY VISIBLE IN THE POPUP PANEL
    wall_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Placement du mur vis à vis de son axe.",
        default=0,
        min=0,
        soft_max=1,
    )

    # EXECUTED SCRIPT
    def execute(self, context):
        target = bpy.context.active_object
        if target["bagapie"] == "bound_box":
        # COLLECTION
            if bpy.data.collections.get("BagaPie") is None:  
                main_coll = bpy.data.collections.new("BagaPie")
                bpy.context.scene.collection.children.link(main_coll)
                manage_coll = bpy.data.collections.new("BagaPie_Manage")
                main_coll.children.link(manage_coll)
                instances_coll = bpy.data.collections.new("BagaPie_Instances")
                manage_coll.children.link(instances_coll)
                insta_coll = bpy.data.collections.new("BagaPie_Instance_Group")
                instances_coll.children.link(insta_coll)

            elif bpy.data.collections.get("BagaPie_Manage") is None:
                manage_coll = bpy.data.collections.new("BagaPie_Manage")
                bpy.data.collections.get("BagaPie").children.link(manage_coll)
                instances_coll = bpy.data.collections.new("BagaPie_Instances")
                manage_coll.children.link(instances_coll)
                insta_coll = bpy.data.collections.new("BagaPie_Instance_Group")
                instances_coll.children.link(insta_coll)

            elif bpy.data.collections.get("BagaPie_Instances") is None:
                instances_coll = bpy.data.collections.new("BagaPie_Instances")
                bpy.data.collections.get("BagaPie_Manage").children.link(instances_coll)
                insta_coll = bpy.data.collections.new("BagaPie_Instance_Group")
                instances_coll.children.link(insta_coll)

            else:
                instances_coll = bpy.data.collections.get("BagaPie_Instances")
                insta_coll = bpy.data.collections.new("BagaPie_Instance_Group")
                bpy.data.collections.get("BagaPie_Instances").children.link(insta_coll)

            # Move Bounding Box from Coll A to B
            current_coll = target.users_collection
            current_coll[0].objects.unlink(target)
            insta_coll.objects.link(target)

            for obj in target["bagapie_child"]:
                obj.hide_select = False
                insta_coll.objects.link(obj)
                try:
                    if obj["bagapie"] == "bound_box":
                        while obj["bagapie"] == "bound_box":
                            loop_repeat = False
                            for ob in obj["bagapie_child"]:
                                insta_coll.objects.link(ob)
                                try:
                                    if ob["bagapie"] == "bound_box":
                                        obj = ob
                                        loop_repeat = True
                                except:
                                    pass
                            if loop_repeat == False:
                                break
                except:
                    pass





            # bpy.data.collections.remove(current_coll[0])
            bpy.ops.object.collection_instance_add(collection= insta_coll.name , align='WORLD', location=target.location, scale=(1, 1, 1))
            target.location = (0, 0, 0)

            # Move instance to bagapie collections
            instance = bpy.context.active_object
            current_coll = instance.users_collection
            current_coll[0].objects.unlink(instance)
            instances_coll.objects.link(instance)

        return {'FINISHED'}

classes = [
    BAGAPIE_OT_makereal,
    BAGAPIE_OT_instance
]