from typing import Text
import bpy
import os
from bpy.types import Operator

class BAGAPIE_OT_importnodes(bpy.types.Operator):
    """ NONE """
    bl_idname = "bagapieassets.importnodes"
    bl_label = 'Import Nodes'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        for mod in addon_utils.modules():
            if mod.bl_info['name'] == "BagaPie Modifier":
                filepath = mod.__file__
                file_path = filepath.replace("__init__.py","BagaPie_Nodes.blend")
            else:
                pass
        inner_path = "NodeTree"
        object_name = "BagaPie_Array_Line"
        file_path = r"C:\Users\antoi\Desktop\BagaPie Archive\Dev\Bagapie\BagaPie_Nodes.blend"

        bpy.ops.wm.append(
            filepath=os.path.join(file_path, inner_path, object_name),
            directory=os.path.join(file_path, inner_path),
            filename=object_name
            )
        
        return {'FINISHED'}


def Get_Type_Library(self,context):

    file_path = os.path.dirname(os.path.abspath(__file__)) + "\Bagapieassets_database.blend"
    inner_path = 'NodeTree'
    object_name = "BagaPie_Array_Line"

    return file_path, inner_path, object_name


def Assets_Collection(self, context):

    try:
        bpy.context.scene.view_layers[bpy.context.view_layer.name].layer_collection.children['BagaPie'].children['BagaPie_Assets'].exclude = False
    except:
        pass

    if bpy.data.collections.get("BagaPie") is None:
        main_coll = bpy.data.collections.new("BagaPie")
        bpy.context.scene.collection.children.link(main_coll)
        asset_coll = bpy.data.collections.new("BagaPie_Assets")
        main_coll.children.link(asset_coll)
    elif bpy.data.collections.get("BagaPie_Assets") is None:
        asset_coll = bpy.data.collections.new("BagaPie_Assets")
        main_coll = bpy.data.collections["BagaPie"]
        main_coll.children.link(asset_coll)
    asset_coll = bpy.data.collections['BagaPie_Assets']

    return asset_coll