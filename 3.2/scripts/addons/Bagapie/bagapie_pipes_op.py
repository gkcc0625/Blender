import bpy
import json
import os
import addon_utils
from bpy.types import Operator
from . presets import bagapieModifiers
from random import random

class BAGAPIE_OT_pipes_remove(Operator):
    """ Remove Bagapie Pipes modifiers """
    bl_idname = "bagapie.pipes_remove"
    bl_label = 'Remove Bagapie Pipes'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'CURVE'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            modifier = obj.modifiers[modifiers[0]]
            
            coll = modifier["Input_13"]
            RemoveOBJandDeleteColl(self, context, coll)

            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Pipes modifier is missing")
        
        context.object.bagapieList.remove(self.index)


        return {'FINISHED'}


class BAGAPIE_OT_pipes(Operator):
    """Add Pipes"""
    bl_idname = 'bagapie.pipes'
    bl_label = bagapieModifiers['pipes']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):

        # FIRST STEP

        curve = bpy.data.curves.new('BagaPie_Pipes', 'CURVE')
        curve_obj = bpy.data.objects.new(curve.name, curve)
        curve_obj.data.dimensions = '3D'

        targets = bpy.context.selected_objects

        new = curve_obj.modifiers.new

        nodegroup = "BagaPie_Pipes" # GROUP NAME

        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)

        coll_target, coll_pipes = Collection_Instancer(self,context,targets[0].name)

        for target in targets:
            coll_pipes.objects.link(target)
        coll_target.objects.link(curve_obj)

        # SET VALUES
        modifier["Input_13"] = coll_pipes

        bpy.context.view_layer.objects.active = curve_obj
        bpy.ops.object.editmode_toggle()
        bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        

        val = {
            'name': 'pipes', # MODIFIER TYPE
            'modifiers':[
                nodegroup, #Modifier Name
            ]
        }

        item = curve_obj.bagapieList.add()
        item.val = json.dumps(val)
        
        return {'FINISHED'}


###################################################################################
# ADD NODEGROUP TO THE MODIFIER
###################################################################################
def Add_NodeGroup(self,context,modifier, nodegroup_name):
    try:
        modifier.node_group = bpy.data.node_groups[nodegroup_name]
    except:
        Import_Nodes(self,context,nodegroup_name)
        modifier.node_group = bpy.data.node_groups[nodegroup_name]


###################################################################################
# IMPORT NODE GROUP
###################################################################################
def Import_Nodes(self,context,nodes_name):

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "BagaPie Modifier":
            filepath = mod.__file__
            file_path = filepath.replace("__init__.py","BagaPie_Nodes.blend")
        else:
            pass
    inner_path = "NodeTree"

    bpy.ops.wm.append(
        filepath=os.path.join(file_path, inner_path, nodes_name),
        directory=os.path.join(file_path, inner_path),
        filename=nodes_name
        )
    
    return {'FINISHED'}


###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Instancer(self,context,name):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        pipes_coll = bpy.data.collections.new("BagaPie_Pipes")
        main_coll.children.link(pipes_coll)
        pipes_coll_target = bpy.data.collections.new("BagaPie_Pipes_"+name)
        pipes_coll.children.link(pipes_coll_target)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Pipes") is None:
        main_coll = bpy.data.collections["BagaPie"]
        pipes_coll = bpy.data.collections.new("BagaPie_Pipes")
        main_coll.children.link(pipes_coll)
        pipes_coll_target = bpy.data.collections.new("BagaPie_Pipes_"+name)
        pipes_coll.children.link(pipes_coll_target)
    # If the main collection Bagapie_Scatter already exist
    else:
        pipes_coll = bpy.data.collections.get("BagaPie_Pipes")
        pipes_coll_target = bpy.data.collections.new("BagaPie_Pipes_"+name)
        pipes_coll.children.link(pipes_coll_target) 

    return [pipes_coll, pipes_coll_target]


###################################################################################
# Remove obj and delete collection
###################################################################################
def RemoveOBJandDeleteColl(self, context, collection):

    for obj in collection.all_objects:
        collection.objects.unlink(obj)

    bpy.data.collections.remove(collection)