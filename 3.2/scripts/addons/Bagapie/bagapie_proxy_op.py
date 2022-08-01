import bpy
import json
import os
import addon_utils
from bpy.types import Operator
from . presets import bagapieModifiers
from random import random

class BAGAPIE_OT_proxy_remove(Operator):
    """ Remove Bagapie Proxy modifiers """
    bl_idname = "bagapie.proxy_remove"
    bl_label = 'Remove Bagapie Proxy'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            for mod in modifiers:
                obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Proxy modifier is missing")
            
        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OT_proxy(Operator):
    """Create convex hull visible only in the viewport"""
    bl_idname = 'bagapie.proxy'
    bl_label = bagapieModifiers['proxy']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object
        l = ['MESH','CURVE']
        return (
            o is not None and 
            o.type in l
        )

    def execute(self, context):
        targets = bpy.context.selected_objects
        for target in targets:
            new = bpy.data.objects[target.name].modifiers.new

            nodegroup = "BagaPie_Proxy" # GROUP NAME

            modifier = new(name=nodegroup, type='NODES')
            Add_NodeGroup(self,context,modifier, nodegroup)
            target.modifiers[nodegroup].show_render = False

            mat_proxy = bpy.data.materials.new(name="BagaPie_Proxy")
            mat_proxy.diffuse_color = (random(), random(), random(), 1)

            #Assign material        
            modifier["Input_6"] = mat_proxy
            
            val = {
                'name': 'proxy', # MODIFIER TYPE
                'modifiers':[
                    nodegroup, #Modifier Name
                ]
            }

            item = target.bagapieList.add()
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
    # file_path = r"C:\Users\antoi\Desktop\BagaPie Archive\Dev\Bagapie\BagaPie_Nodes.blend"

    bpy.ops.wm.append(
        filepath=os.path.join(file_path, inner_path, nodes_name),
        directory=os.path.join(file_path, inner_path),
        filename=nodes_name
        )
    
    return {'FINISHED'}