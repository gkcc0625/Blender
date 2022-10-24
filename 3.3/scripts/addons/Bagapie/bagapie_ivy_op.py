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
            if ivy_coll in ob.users_collection:
                print(ob.name + " is already set as target")
            else:
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

###################################################################################
# APPLY MODIFIER IVY
###################################################################################
class Apply_Ivy_OP(Operator):
    """Apply Ivy Modifier"""
    bl_idname = "use.applyivy"
    bl_label = "Apply Ivy"
    bl_options = {'REGISTER', 'UNDO'}

    instances_count: bpy.props.IntProperty(default=0)
    instances_polygon_count: bpy.props.IntProperty(default=0)
    index: bpy.props.IntProperty(default=0)

    def invoke(self, context, event):
        wm = context.window_manager
        
        return wm.invoke_props_dialog(self)


    def draw(self, context):
        obj = context.object
        self.instances_polygon_count = 0
        self.instances_count = 0

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval = obj.evaluated_get(depsgraph)
        instA = [inst for inst in depsgraph.object_instances if inst.is_instance and inst.parent == eval]

        coll_assets=bpy.data.collections['BagaPie_Ivy_Assets']
        for ob in coll_assets.objects:
            self.instances_polygon_count += len(ob.data.polygons)


        self.instances_count = int(len(instA)*(self.instances_polygon_count/len(coll_assets.objects)))

        layout = self.layout
        col = layout.column(align=True)
        col.label(text = "About {} polygons will be created.".format(str(self.instances_count)))
        col.label(text = "Continue ?")


    def execute(self, context):
    
        target = bpy.context.active_object
        val = json.loads(target.bagapieList[target.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = target.modifiers[modifiers[0]]

        # REALIZE INSTANCES
        ivy_node_group = modifier.node_group
        nodes = ivy_node_group.nodes
        ivy_node_output = nodes.get("Group Output")
        ivy_nde_ri = nodes.get("EndNode")
        link = ivy_nde_ri.outputs[0].links[0]
        ivy_node_group.links.remove(link)
        ivy_nde_release = nodes.new(type='GeometryNodeRealizeInstances')

        # LINK NODES
        new_link = ivy_node_group.links
        new_link.new(ivy_nde_ri.outputs[0], ivy_nde_release.inputs[0])
        new_link.new(ivy_nde_release.outputs[0], ivy_node_output.inputs[0])
            
        target_coll = modifier['Input_9']
        asset_coll = modifier['Input_16']
        empty_coll = modifier['Input_17']
            
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        for ob in target_coll.objects:
            target_coll.objects.unlink(ob) 
        bpy.data.collections.remove(target_coll)

        for ob in asset_coll.objects:
            asset_coll.objects.unlink(ob) 
        bpy.data.collections.remove(asset_coll)

        for ob in empty_coll.objects:
            empty_coll.objects.unlink(ob) 
        bpy.data.collections.remove(empty_coll)
        
        target.data.attributes.active_index = 0

        for at in target.data.attributes:
            
            if at.name == "Leaves":
                bpy.ops.geometry.attribute_convert(mode="UV_MAP")
            else:
                target.data.attributes.active_index += 1

        # for at in target.data.attributes:
        #     bpy.ops.geometry.attribute_remove()

        
        context.object.bagapieList.remove(self.index)
        
        return {'FINISHED'}

###################################################################################
# Get OBJ children
###################################################################################
def get_children(ob):
    return [ob_child for ob_child in bpy.data.objects if ob_child.parent == ob and ob_child.name.startswith("BagaPie_Ivy")]

###################################################################################
# ADD OBJECT TARGET
###################################################################################
class BAGAPIE_OT_RemoveSingleIvy(Operator):
    """Remove ivy based on his parent (Empty Object)."""
    bl_idname = "bagapie.removesingleivy"
    bl_label = "Remove Single Ivy"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'EMPTY'
        )

    def execute(self, context):
        parent_ivy = context.object
        ivy = get_children(parent_ivy)[0]
        coll_source = None

        for coll in ivy.users_collection:
            if coll.name.startswith("BagaPie_Ivy_Source_"):
                coll_source = coll

        bpy.ops.object.select_all(action='DESELECT')
        if coll_source is not None:
            for ob in coll_source.objects:
                if ivy == ob:
                    ivy.select_set(True)
                    parent_ivy.select_set(True)
                    bpy.ops.object.delete()

        else:
            Warning(message = "Select Ivy, then delete it via the BagaPie panel. The selected Ivy will be deleted.", title = "Main Ivy Detected", icon = 'INFO')
        

        return {'FINISHED'}


###################################################################################
# DISPLAY WARNING MESSAGE
###################################################################################
def Warning(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


classes = [
    BAGAPIE_OT_ivy_remove,
    BAGAPIE_OT_ivy,
    BAGAPIE_OT_AddVertOBJ,
    BAGAPIE_OT_AddObjectTarget,
    BAGAPIE_OT_RemoveObjectTarget,
    Apply_Ivy_OP,
    BAGAPIE_OT_RemoveSingleIvy,
]