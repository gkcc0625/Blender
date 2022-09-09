import bpy
import json
import addon_utils
import os
from bpy.types import Operator
from . presets import bagapieModifiers

class BAGAPIE_OT_ivy_remove(Operator):
    """ Remove Bagapie Ivy """
    bl_idname = "bagapie.ivy_remove"
    bl_label = 'Remove Bagapie Ivy'

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
        modifiers = val['modifiers']
        obj.modifiers.remove(obj.modifiers[modifiers[0]])

        coll_target=bpy.data.collections[modifiers[1]]
        coll_assets=bpy.data.collections['BagaPie_Ivy_Assets']
        coll_source=bpy.data.collections[modifiers[3]]
        coll_main=bpy.data.collections['BagaPie_Ivy']

        for ob in coll_target.objects:
            coll_target.objects.unlink(ob)
        bpy.data.collections.remove(coll_target)
        

        bpy.ops.object.select_all(action='DESELECT')
        for ob in coll_source.objects:
            ob.select_set(True)
        source_obj = bpy.context.scene.objects[modifiers[2]]
        source_obj.select_set(True)
        bpy.ops.object.delete()
        bpy.data.collections.remove(coll_source)

        scene_coll = bpy.data.collections
        remove_all_ivy = True
        for coll in scene_coll:
            coll_name = coll.name
            if coll_name.startswith("BagaPie_Ivy_") and coll_name != 'BagaPie_Ivy_Assets':
                remove_all_ivy = False

        if remove_all_ivy == True:
            for ob in coll_assets.objects:
                ob.select_set(True)
            bpy.ops.object.delete()
            bpy.data.collections.remove(coll_assets)

            bpy.ops.object.select_all(action='DESELECT')
            for ob in coll_main.objects:
                ob.select_set(True)
            bpy.ops.object.delete()
            bpy.data.collections.remove(coll_main)
        else:
            obj.select_set(True)
            bpy.ops.object.delete()

        return {'FINISHED'}


class BAGAPIE_OT_ivy(Operator):
    """Create Ivy. Each vertices generate a new ivy."""
    bl_idname = 'bagapie.ivy'
    bl_label = bagapieModifiers['ivy']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):
        target = bpy.context.selected_objects

        # if bpy.data.collections.get("BagaPie_Ivy_Source") is None:

        # CREATE SUPPORT FOR IVY
        me = bpy.data.meshes.new("BagaPie_Ivy")
        ivy = bpy.data.objects.new("BagaPie_Ivy", me)

        coords = []
        coords.append((0,0,0))
        edges=[]
        faces=[]
        # Make a mesh from a list of vertices/edges/faces
        me.from_pydata(coords, edges, faces)
        me.update()

        ivy_coll = Collection_Setup(self,context,target)
        for ob in target:
            ivy_coll.objects.link(ob)

        # ADD MODIFIER AND NODES
        new = bpy.data.objects[ivy.name].modifiers.new
        nodegroup = "BagaPie_Ivy_Generator" # GROUP NAME
        modifier = new(name=nodegroup, type='NODES')
        Add_NodeGroup(self,context,modifier, nodegroup)

        # IMPORT ASSETS
        Import_Assets(self,context,"BagaPie_Ivy_1")
        ivy_assets = [bpy.context.selected_objects]
        Import_Assets(self,context,"BagaPie_Ivy_2")
        ivy_assets.append(bpy.context.selected_objects)
        ivy_assets_coll = Collection_Setup_Assets(self,context,ivy_assets)
        for ob in ivy_assets:
            for coll in ob[0].users_collection:
                coll.objects.unlink(ob[0])
        for ob in ivy_assets:
            try:
                ivy_assets_coll.objects.link(ob[0])
            except:
                pass

        modifier["Input_9"] = ivy_coll
        modifier["Input_16"] = ivy_assets_coll
        coll_emit = Collection_Setup_Emiter(self,context,ivy)
        modifier["Input_17"] = coll_emit
        
        # coll_emit.objects.link(ivy)

        bpy.ops.object.empty_add(type='SPHERE', location=bpy.context.scene.cursor.location)
        empty = bpy.context.active_object
        empty.name = "Ivy_Parent"
        for coll in empty.users_collection:
            coll.objects.unlink(empty)
        coll_emit.objects.link(empty)
        ivy.parent = empty

        val = {
            'name': 'ivy', # MODIFIER TYPE
            'modifiers':[
                nodegroup, # Modifier Name
                ivy_coll.name,  # this collection contains meshes for snapping
                empty.name,     # Parent Empty of the Ivy
                coll_emit.name, # Collection that handle every new ivy (related to this one)
            ]
        }

        item = ivy.bagapieList.add()
        item.val = json.dumps(val)
        
    # else:


        #     bpy.ops.object.empty_add(type='SPHERE', location=bpy.context.scene.cursor.location)
        #     empty = bpy.context.active_object
        #     empty.name = "Ivy_Parent"

        #     # Create new mesh and a new object
        #     me = bpy.data.meshes.new("Ivy")
        #     ob = bpy.data.objects.new("Ivy", me)

        #     coords = []
        #     coords.append((0,0,0))
        #     edges=[]
        #     faces=[]
        #     # Make a mesh from a list of vertices/edges/faces
        #     me.from_pydata(coords, edges, faces)
        #     me.update()
            
        #     coll_emit = Collection_Setup_Emiter(self,context,None)
        #     coll_emit.objects.link(ob)
        #     for coll in empty.users_collection:
        #         coll.objects.unlink(empty)
        #     coll_emit.objects.link(empty)

        #     target_coll = bpy.data.collections["BagaPie_Ivy_Target"]
        #     for obj in target:
        #         if obj.name not in target_coll.objects:
        #             target_coll.objects.link(obj)
    # ob.parent = empty
            
        return {'FINISHED'}


###################################################################################
# ADD VERTICE OBJECT
###################################################################################
class BAGAPIE_OT_AddVertOBJ(Operator):
    """Create a new ivy source in the selected ivy. Target and serrtings will be shared"""
    bl_idname = "bagapie.addvertcursor"
    bl_label = "Simple Modal Operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):
        current_ivy = context.object
        parent_current_ivy = current_ivy.parent
        coll_parent_current_ivy = parent_current_ivy.users_collection[0]
        
        bpy.ops.object.empty_add(type='SPHERE', location=bpy.context.scene.cursor.location)
        empty = bpy.context.active_object
        empty.name = "Ivy_Parent"

        # Create new mesh and a new object
        me = bpy.data.meshes.new("BagaPie_Ivy")
        ob = bpy.data.objects.new("BagaPie_Ivy", me)

        coords = []
        coords.append((0,0,0))
        edges=[]
        faces=[]
        # Make a mesh from a list of vertices/edges/faces
        me.from_pydata(coords, edges, faces)
        me.update()
        
        coll_parent_current_ivy.objects.link(ob)
        for col in empty.users_collection:
            col.objects.unlink(empty)
        coll_parent_current_ivy.objects.link(empty)

        ob.parent = empty

        return {'FINISHED'}


###################################################################################
# ADD OBJECT TARGET
###################################################################################
class BAGAPIE_OT_AddObjectTarget(Operator):
    """Add selected object in target collection. Select Target Object then Ivy"""
    bl_idname = "bagapie.addobjecttarget"
    bl_label = "Add Object Target"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    def execute(self, context):
        current_ivy = context.object
        target = bpy.context.selected_objects
        target.remove(current_ivy)
        ivy_modifier = current_ivy.modifiers["BagaPie_Ivy_Generator"]
        target_coll = ivy_modifier["Input_9"]
        for ob in target:
            if ob not in target_coll.objects[:]:
                target_coll.objects.link(ob)


        return {'FINISHED'}


###################################################################################
# REMOVE OBJECT TARGET
###################################################################################
class BAGAPIE_OT_RemoveObjectTarget(Operator):
    """Remove selected object from target collection. Select Target Object then Ivy"""
    bl_idname = "bagapie.removeobjecttarget"
    bl_label = "Remove Object Target"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    def execute(self, context):
        current_ivy = context.object
        target = bpy.context.selected_objects
        target.remove(current_ivy)
        ivy_modifier = current_ivy.modifiers["BagaPie_Ivy_Generator"]
        target_coll = ivy_modifier["Input_9"]
        for ob in target:
            if ob in target_coll.objects[:]:
                target_coll.objects.unlink(ob)

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
# MANAGE COLLECTION
###################################################################################
def Collection_Setup(self,context,target):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_"+target[0].name)
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Ivy") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_"+target[0].name)
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie_Scatter already exist
    elif bpy.data.collections.get("BagaPie_Ivy_"+target[0].name) is None:
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_"+target[0].name)
        scatter_master_coll = bpy.data.collections["BagaPie_Ivy"]
        scatter_master_coll.children.link(ivy_coll)
    else:
        ivy_coll = bpy.data.collections["BagaPie_Ivy_"+target[0].name]
    
    return ivy_coll

###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Setup_Assets(self,context,target):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Assets")
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Ivy") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Assets")
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie_Scatter already exist
    elif bpy.data.collections.get("BagaPie_Ivy_Assets") is None:
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Assets")
        scatter_master_coll = bpy.data.collections["BagaPie_Ivy"]
        scatter_master_coll.children.link(ivy_coll)
    else:
        ivy_coll = bpy.data.collections["BagaPie_Ivy_Assets"]
    
    return ivy_coll

###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Setup_Emiter(self,context,target):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Source_"+target.name)
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Ivy") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Ivy")
        main_coll.children.link(scatter_master_coll)
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Source_"+target.name)
        scatter_master_coll.children.link(ivy_coll)
    # If the main collection Bagapie_Scatter already exist
    elif bpy.data.collections.get("BagaPie_Ivy_Source_"+target.name) is None:
        ivy_coll = bpy.data.collections.new("BagaPie_Ivy_Source_"+target.name)
        scatter_master_coll = bpy.data.collections["BagaPie_Ivy"]
        scatter_master_coll.children.link(ivy_coll)
    else:
        scatter_master_coll = bpy.data.collections["BagaPie_Ivy"]
        ivy_coll = bpy.data.collections["BagaPie_Ivy_Source_"+target.name]

    if target is not None: 
        scatter_master_coll.objects.link(target)
    
    return ivy_coll

###################################################################################
# IMPORT NODE GROUP
###################################################################################
def Import_Nodes(self,context,nodes_name):

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "BagaPie Modifier":
            filepath = mod.__file__
            file_path = filepath.replace("__init__.py","BagaPie_IvyGenerator.blend")
        else:
            pass
    inner_path = "NodeTree"
    # file_path = r"C:\Users\antoi\Desktop\BagaPie Archive\Dev\Bagapie\BagaPie_IvyGenerator.blend"

    bpy.ops.wm.append(
        filepath=os.path.join(file_path, inner_path, nodes_name),
        directory=os.path.join(file_path, inner_path),
        filename=nodes_name
        )
    
    return {'FINISHED'}

###################################################################################
# IMPORT NODE GROUP
###################################################################################
def Import_Assets(self,context,object_name):

    try:
        assets = bpy.data.objects[object_name]
        bpy.ops.object.select_all(action='DESELECT')
        assets.select_set(True)
    except:
        for mod in addon_utils.modules():
            if mod.bl_info['name'] == "BagaPie Modifier":
                filepath = mod.__file__
                file_path = filepath.replace("__init__.py","BagaPie_IvyGenerator.blend")
            else:
                pass
        inner_path = "Object"
        # file_path = r"C:\Users\antoi\Desktop\BagaPie Archive\Dev\Bagapie\BagaPie_IvyGenerator.blend"

        assets = bpy.ops.wm.append(
            filepath=os.path.join(file_path, inner_path, object_name),
            directory=os.path.join(file_path, inner_path),
            filename=object_name
            )
    return assets
    # return {'FINISHED'}