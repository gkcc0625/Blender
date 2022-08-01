import bpy
import json
import os
import addon_utils
from bpy.types import Operator
from . presets import bagapieModifiers
import random

###################################################################################
# REMOVE SCATTER PAINT
###################################################################################
class BAGAPIE_OT_scatterpaint_remove(Operator):
    """ Remove Bagapie Scatter Paint modifiers """
    bl_idname = "bagapie.scatterpaint_remove"
    bl_label = 'Remove Bagapie Scatter Paint'

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
        scatter_modifier = obj.modifiers.get("BagaScatter")
        scatt_nde_group = scatter_modifier.node_group
        scatt_nde_inp = scatt_nde_group.nodes.get("Scatter Group Input")

        # GET NODES AND COUNT
        scatt_nde = scatt_nde_group.nodes
        scattpaint_count_real = 0

        for node in scatt_nde:                
            # Count how many scatter/scatter paint/effector are present
            if node.label == "BagaPie_ScatterPaint":
                scattpaint_count_real += 1

        if scattpaint_count_real == 1 and scatt_nde.get("BagaPie_Scatter") is None:

            scatt_coll = scatt_nde_group.nodes.get(modifiers[1]).inputs[1].default_value
            # remove obj from coll and coll
            for ob in scatt_coll.objects:
                scatt_coll.objects.unlink(ob) 
            bpy.data.collections.remove(scatt_coll)
            
            # Remove modifier
            obj.modifiers.remove(scatter_modifier)
            

        else:
            # DELETE NODES
            scatt_nde_main = scatt_nde_group.nodes.get(modifiers[1])
            scatt_coll = scatt_nde_group.nodes.get(modifiers[1]).inputs[1].default_value
            # remove obj from coll and coll
            for ob in scatt_coll.objects:
                scatt_coll.objects.unlink(ob) 
            bpy.data.collections.remove(scatt_coll)

            nde_position = scatt_nde_main.location
            
            for node in scatt_nde_group.nodes:    
                if node.location[0] > nde_position:
                    node.location[0] -= 200   
                if node.location[1] > nde_position:
                    node.location[1] += 100

            scatt_nde_group.nodes.remove(scatt_nde_main)

            # REMOVE UNUSED GROUP INPUT
            for output in scatt_nde_inp.outputs:
                if output.is_linked:
                    pass
                else:
                    for i in scatt_nde_group.inputs:
                        if i.identifier == output.identifier:
                            scatt_nde_group.inputs.remove(i)

        # REMOVE UNUSED VERTEX GROUP
        obj.vertex_groups.remove(obj.vertex_groups[modifiers[3]])
                                

            # REMOVE COLLECTION

        context.object.bagapieList.remove(self.index)

        return {'FINISHED'}

###################################################################################
# ADD SCATTER PAINT
###################################################################################
class BAGAPIE_OT_scatterpaint(Operator):
    """Instantiates selected objects by painting them on the active object (the last selected). The precision of this function depends on the density of the mesh"""
    bl_idname = "wm.scatter_paint"
    bl_label = bagapieModifiers['scatterpaint']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and
            o.type == 'MESH'
        )

 # UI PANEL INPUTS

    distance_min: bpy.props.FloatProperty(
        name="Distance Min",
        default=0.2,
        min=0,
    )
    density: bpy.props.FloatProperty(
        name="Density",
        default=10,
        min=0,
    )
    scale_min: bpy.props.FloatProperty(
        name="Scale Min",
        default=1,
        min=0,
        soft_max=100,
    )
    scale_max: bpy.props.FloatProperty(
        name="Scale Max",
        default=1,
        min=0,
        soft_max=100,
    )
    random_rot: bpy.props.FloatVectorProperty(
        name="Randomize Rotation",
        default=[0, 0, 0],
    )
    align_to_normal: bpy.props.FloatProperty(
        name="Align to Normal",
        default=0,
        min=0,
        max=1,
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        default=1,
        min=0
    )

 # EXE
    def execute(self, context):
        
        target = bpy.context.active_object
        obj = bpy.context.selected_objects
        obj.remove(target)
        # check if selection is correct
        go_scatter = False
        for ob in obj:
            if ob.type == 'MESH':
                go_scatter = True
            else:
                obj.remove(ob)
        if go_scatter == False:
            Warning(message="No selected meshes for scattering.", title='WARNING', icon='ERROR')
            return {'FINISHED'}
        else:

            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

            #                                IF SCATTER IS PRESENT

            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            if target.modifiers.get("BagaScatter"):

                scatt = target.modifiers.get("BagaScatter")
                scatt_nde_group = scatt.node_group

             # COLLECTION
                scatt_coll = Collection_Setup(self,context,target)

                for ob in obj:
                    scatt_coll.objects.link(ob)

            # Get instance dimensions and scale
                scale = OBJ_Scale(self,context,obj,target)
                dimmension = OBJ_Dimension(self,context,obj,target)
                use_bagapie_assets = BagaPie_Assets_Check(self,context,obj)

             # Count how many scatter/scatter paint/effector are present

                # GET NODES AND COUNT
                scatt_nde = scatt_nde_group.nodes
                scattpaint_nde_count = scatt_nde.get("Join Layer")
                scattpaint_count = int(scattpaint_nde_count.label)+1
                scattpaint_count_real = 1

                for node in scatt_nde:
                    # Count how many scatter paint are present
                    if node.label == "BagaPie_ScatterPaint":
                        scattpaint_count_real += 1

                # INCREMENT COUNT
                scattpaint_nde_count.label = str(scattpaint_count)

             # ADD SCATTER PAINT

              #CREATE VERTEX GROUP
                scatt_vertex_grp = target.vertex_groups.new(name="BagaVertGrp")

              # GET IN AND OUT NODES
                scatt_nde_inp = scatt_nde_group.nodes.get("Scatter Group Input")
                scatt_nde_out = scatt_nde_group.nodes.get("Scatter Group Output")
                scatt_nde_join = scatt_nde_group.nodes.get("Join Layer")
                
              # ADD NODES
                Import_Nodes(self,context,"BagaPie_ScatterPaint")
                scatt_nde_main = scatt_nde_group.nodes.new(type='GeometryNodeGroup')
                scatt_nde_main.node_tree = bpy.data.node_groups['BagaPie_ScatterPaint']
                scatt_nde_main.name = "BagaPie_ScatterPaint"
                scatt_nde_main.label = "BagaPie_ScatterPaint"

              # POSITION NODES
                scatt_nde_main.location = (600+200*scattpaint_count_real, 100-(100*scattpaint_count_real))
                scatt_nde_join.location = (800+scatt_nde_join.location[1]+(200*scattpaint_count_real), 0)
                scatt_nde_out.location = (1000+scatt_nde_out.location[1]+(200*scattpaint_count_real), 0)

              # Config Nodes
                scatt_nde_main.inputs[1].default_value = scatt_coll
                scatt_nde_main.inputs[2].default_value = dimmension/2
                if use_bagapie_assets:
                    scatt_nde_main.inputs[3].default_value = 20
                    scatt_nde_main.inputs[8].default_value[2] = 100
                    scatt_nde_main.inputs[9].default_value = scale*0.8
                    scatt_nde_main.inputs[10].default_value = scale*1.2
                else:
                    scatt_nde_main.inputs[9].default_value = scale
                    scatt_nde_main.inputs[10].default_value = scale

              # UI geometry node, add inputs
                scatt_nde_group.inputs.new(type="NodeSocketFloat", name="Vertex Group")

              # LINK NODES
                
                new_link = scatt_nde_group.links
               # Geometry path
                new_link.new(scatt_nde_inp.outputs[0], scatt_nde_main.inputs[0])
                new_link.new(scatt_nde_main.outputs[0], scatt_nde_join.inputs[0])

               # Link nodes to group input node
                new_link.new(scatt_nde_inp.outputs[scattpaint_count_real], scatt_nde_main.inputs[6])

                bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_{}_use_attribute\"]".format(str(1+scattpaint_count)), modifier_name="BagaScatter")
                # scatt.Input_2_attribute_name = vertex_group
                # Switch to weight paint
                bpy.ops.paint.weight_paint_toggle()

              # SCATTER MODIFIER SET VALUE
                scatt_modifier = bpy.context.object.modifiers[scatt.name]
                scatt_modifier["Input_{}_attribute_name".format(str(1+scattpaint_count))] = scatt_vertex_grp.name

              # CUSTOM PROPERTY
                val = {
                    'name': 'scatterpaint',
                    'modifiers':[
                                scatt.name,             # MODIFIER NAME
                                scatt_nde_main.name,    # SCATTER PAINT NODE NAME
                                str(scattpaint_count),  # SCATTER PAINT COUNT
                                scatt_vertex_grp.name,
                                ]
                }
                item = target.bagapieList.add()
                item.val = json.dumps(val)
                
                target.bagapieIndex = len(target.bagapieList)-1

            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

            #                              IF SCATTER IS NOT PRESENT

            # 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
            else:

             # COLLECTION
                scatt_coll = Collection_Setup(self,context,target)

                for ob in obj:
                    scatt_coll.objects.link(ob)

            # Get instance dimensions and scale
                scale = OBJ_Scale(self,context,obj,target)
                dimmension = OBJ_Dimension(self,context,obj,target)
                use_bagapie_assets = BagaPie_Assets_Check(self,context,obj)

             # CREATE SCATTER MODIFIER

              # ADD MODIFIER
                new = bpy.data.objects[target.name].modifiers.new
                scatt = new(name='BagaScatter', type='NODES')
                scatt_nde_group = scatt.node_group
                scatt_nde_group.name = "BagaScatter"

                # GET IN AND OUT NODES
                scatt_nde = scatt_nde_group.nodes
                scatt_nde_inp = scatt_nde[0]
                scatt_nde_inp.name = "Scatter Group Input"
                scatt_nde_out = scatt_nde[1]
                scatt_nde_out.name = "Scatter Group Output"
                
              # ADD NODES
                scatt_nde_join = scatt_nde_group.nodes.new('GeometryNodeJoinGeometry')     # ADD JOIN GEOMETRY
                scatt_nde_join.label = "0"
                scatt_nde_join.name = "Join Layer"


                # POSITION NODES
                scatt_nde_inp.location = (0, 0)              # Group input
                scatt_nde_out.location = (1000, 0)           # Group output
                scatt_nde_join.location = (800,0)            # Join Geometry

              # CONFIGURATION NODES

              # LINK NODES
                new_link = scatt_nde_group.links
                # Geometry path
                new_link.new(scatt_nde_inp.outputs[0], scatt_nde_join.inputs[0])
                new_link.new(scatt_nde_join.outputs[0], scatt_nde_out.inputs[0])

             # ADD SCATTER PAINT

              #CREATE VERTEX GROUP
                scatt_vertex_grp = target.vertex_groups.new(name="BagaVertGrp")
                
              # ADD NODES
                Import_Nodes(self,context,"BagaPie_ScatterPaint")
                scatt_nde_main = scatt_nde_group.nodes.new(type='GeometryNodeGroup')
                scatt_nde_main.node_tree = bpy.data.node_groups['BagaPie_ScatterPaint']
                scatt_nde_main.name = "BagaPie_ScatterPaint"
                scatt_nde_main.label = "BagaPie_ScatterPaint"


                # GET NODES
                scatt_nde = scatt_nde_group.nodes
                scattpaint_nde_count = scatt_nde_join
                scattpaint_count = int(scattpaint_nde_count.label)+1
                scattpaint_count_real = 0

                # Count how many scatter/scatter paint/effector are present
                for node in scatt_nde:
                    # Count how many scatter paint are present
                    if node.label == "BagaPie_ScatterPaint":
                        scattpaint_count_real += 1

                # INCREMENT COUNT
                scattpaint_nde_count.label = str(scattpaint_count)


              # POSITION NODES
                scatt_nde_main.location = (600+200*scattpaint_count_real, 100-(100*scattpaint_count_real))
                scatt_nde_join.location = (800+scatt_nde_join.location[1]+(200*scattpaint_count_real), 0)
                scatt_nde_out.location = (1000+scatt_nde_out.location[1]+(200*scattpaint_count_real), 0)

              # Config Nodes
                scatt_nde_main.inputs[1].default_value = scatt_coll
                scatt_nde_main.inputs[2].default_value = dimmension/2
                if use_bagapie_assets:
                    scatt_nde_main.inputs[3].default_value = 20
                    scatt_nde_main.inputs[8].default_value[2] = 100
                    scatt_nde_main.inputs[9].default_value = scale*0.8
                    scatt_nde_main.inputs[10].default_value = scale*1.2
                else:
                    scatt_nde_main.inputs[9].default_value = scale
                    scatt_nde_main.inputs[10].default_value = scale

              # UI geometry node, add inputs
                scatt_nde_group.inputs.new(type="NodeSocketFloat", name="Vertex Group")

              # LINK NODES
                
                new_link = scatt_nde_group.links
               # Geometry path
                new_link.new(scatt_nde_inp.outputs[0], scatt_nde_main.inputs[0])
                new_link.new(scatt_nde_main.outputs[0], scatt_nde_join.inputs[0])

               # Link nodes to group input node
                new_link.new(scatt_nde_inp.outputs[scattpaint_count_real], scatt_nde_main.inputs[6])

                bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_{}_use_attribute\"]".format(str(1+scattpaint_count)), modifier_name="BagaScatter")
                # Switch to weight paint
                bpy.ops.paint.weight_paint_toggle()

              # SCATTER MODIFIER SET VALUE
                scatt_modifier = bpy.context.object.modifiers[scatt.name]
                scatt_modifier["Input_{}_attribute_name".format(str(1+scattpaint_count))] = scatt_vertex_grp.name

              # CUSTOM PROPERTY
                val = {
                    'name': 'scatterpaint',
                    'modifiers':[
                                scatt.name,             # MODIFIER NAME
                                scatt_nde_main.name,    # SCATTER PAINT NODE NAME
                                str(scattpaint_count),  # SCATTER PAINT COUNT
                                scatt_vertex_grp.name,
                                ]
                }
                item = target.bagapieList.add()
                item.val = json.dumps(val)
                
                target.bagapieIndex = len(target.bagapieList)-1


            return {'FINISHED'}



###################################################################################
# DISPLAY WARNING MESSAGE
###################################################################################
def Warning(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

###################################################################################
# GET OBJECTS SCALE
###################################################################################
def OBJ_Scale(self,context,obj,target):
    instances_visual_scale = 0
    for ob in obj:
        instances_visual_scale += ob.scale[0]
        instances_visual_scale += ob.scale[1]
        instances_visual_scale += ob.scale[2]
    instances_visual_scale = instances_visual_scale/(len(obj)*3)

    target_scale = (target.scale[0] + target.scale[0] + target.scale[0])/3
    
    scale = instances_visual_scale / target_scale
    
    return scale
    
###################################################################################
# GET OBJECTS SCALE
###################################################################################
def OBJ_Dimension(self,context,obj,target):
    instances_max_dimensions = 0
    for ob in obj:  # Get instance max dimensions
        if ob.dimensions.x > instances_max_dimensions:
            instances_max_dimensions = ob.dimensions.x
            if ob.dimensions.x < ob.dimensions.y:
                instances_max_dimensions = ob.dimensions.y
        if ob.name.startswith("BagaPie_Grass"):
            inc_dim = 0.5
        else:
            inc_dim = 1

    target_scale = (target.scale[0] + target.scale[0] + target.scale[0])/3

    dimmension = ((instances_max_dimensions / target_scale)*0.65)*inc_dim #0.65 because it looks good
    
    return dimmension

###################################################################################
# MANAGE COLLECTION
###################################################################################
def Collection_Setup(self,context,target):
    # Create collection and check if the main "Baga Collection" does not already exist
    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        scatt_coll = bpy.data.collections.new("BagaPie_ScatterPaint_" + target.name)
        scatter_master_coll.children.link(scatt_coll)
    # If the main collection Bagapie already exist
    elif bpy.data.collections.get("BagaPie_Scatter") is None:
        main_coll = bpy.data.collections["BagaPie"]
        scatter_master_coll = bpy.data.collections.new("BagaPie_Scatter")
        main_coll.children.link(scatter_master_coll)
        scatt_coll = bpy.data.collections.new("BagaPie_ScatterPaint_" + target.name)
        scatter_master_coll.children.link(scatt_coll)
    # If the main collection Bagapie_Scatter already exist
    else:
        scatt_coll = bpy.data.collections.new("BagaPie_ScatterPaint_" + target.name)
        scatter_master_coll = bpy.data.collections["BagaPie_Scatter"]
        scatter_master_coll.children.link(scatt_coll)

    return scatt_coll

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

###################################################################################
# CHECK IF BAGAPIE ASSETS ARE PRESENT
###################################################################################
def BagaPie_Assets_Check(self,context,obj):
    # Check if it's a BagaPie Assets OBJ
    use_bagapie_assets = False
    for ob in obj:
        try:
            if "BagaPie" in ob.name:
                use_bagapie_assets = True
        except:
            pass
    return use_bagapie_assets