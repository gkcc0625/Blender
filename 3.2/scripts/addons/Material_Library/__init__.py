# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Realtime Materials",
    "author" : "Joshua Blömer, Ducky 3D",
    "description" : "100+ procedural materials for Eevee & Cycles",
    "blender" : (2, 83, 0),
    "version" : (1, 0, 0),
    "location" : "Shift + A > Realtime Materials, Object > Realtime Materials",
    "warning" : "",
    "category" : "Material"
}

import bpy.utils.previews
import json
from threading import Timer
import bpy
import os
from bpy.app.handlers import persistent
from bpy.types import (
    Operator,
    Menu,
)
from bpy.props import StringProperty, EnumProperty


def realtime_materials_menu(self, context):
    self.layout.menu('MATERIAL_MT_realtime_materials_menu', text="Realtime Materials", icon="SHADING_RENDERED")


cat_list = []
# function to generate menu classes
def cat_generator():
    global cat_list

    with open(os.path.join(os.path.dirname(__file__), "material_categories.json"), 'r') as f:
        material_categories = json.loads(f.read())

    cat_list = []
    for item in material_categories.items():
        def custom_draw(self,context):
            layout = self.layout
            for group_name in material_categories[self.bl_label]:
                pcoll = preview_collections["main"]
                icon =pcoll[group_name + '.png']
                props = layout.operator(
                    MATERIAL_OT_add.bl_idname,
                    text=group_name,
                    icon_value=icon.icon_id                    
                )
                props.material_name = group_name

        menu_type = type("MATERIAL_MT_category_" + item[0], (bpy.types.Menu,), {
            "bl_idname": "MATERIAL_MT_category_" + item[0].replace(" ", "_"),   # replace whitespace with uderscore to avoid alpha-numeric suffix warning 
            "bl_space_type": 'NODE_EDITOR',
            "bl_label": item[0],
            "draw": custom_draw,
        })
        if menu_type not in cat_list:
            cat_list.append(menu_type)
            bpy.utils.register_class(menu_type)

class MATERIAL_MT_realtime_materials_menu(Menu):
    bl_label = "Realtime Materials"
    bl_idname = 'MATERIAL_MT_realtime_materials_menu'


    def draw(self, context):
        layout = self.layout
        for cat in cat_list:
            layout.menu(cat.bl_idname)


class MATERIAL_OT_add(Operator):
    bl_idname = "rtm.template_add"
    bl_label = "Add node group template"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty()

    @classmethod
    def poll(cls,context):
        return context.selected_objects

    def execute(self, context):
        test = self.material_name in bpy.data.materials
        filepath = os.path.join(os.path.dirname(__file__),"Realtime_Materials.blend")
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            if test:
                bpy.ops.rtm.confirm("INVOKE_DEFAULT",material_name = self.material_name)
            else:
                data_to.materials.append(self.material_name)

        if not test:
            for obj in context.selected_objects:
                obj.active_material = bpy.data.materials[self.material_name]
        return {'FINISHED'}


class ConfirmOP(Operator):
    bl_idname = "rtm.confirm"
    bl_label = "Material already exists in File"
    bl_options = {'REGISTER', 'UNDO'}
    material_name: StringProperty()
    confirm : EnumProperty(name="test",items=(('0','Create duplicate','Create duplicate'),('1','Use existing','Use existing')))

    def draw(self,context):
        self.layout.prop(self, 'confirm', expand=True)

    def execute(self,context):
        if self.confirm == "0":
            materials_cache = set(bpy.data.materials)
            filepath = os.path.join(os.path.dirname(__file__),"Realtime_Materials.blend")
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                data_to.materials.append(self.material_name)
            dif = set(bpy.data.materials) - materials_cache
            for obj in context.selected_objects:
                obj.active_material = next(iter(dif))
        else:
            for obj in context.selected_objects:
                obj.active_material = bpy.data.materials[self.material_name]
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


classes = (
    MATERIAL_MT_realtime_materials_menu,
    MATERIAL_OT_add, 
    ConfirmOP, 
)

preview_collections = {}


def register():
    pcoll = bpy.utils.previews.new()
    for cls in classes:
        bpy.utils.register_class(cls)
    icons_dir = os.path.join(os.path.dirname(__file__), "Icons")
    for icon in os.listdir(icons_dir):
        pcoll.load(icon, os.path.join(icons_dir, icon), 'IMAGE')
    preview_collections["main"] = pcoll

    bpy.types.VIEW3D_MT_add.append(realtime_materials_menu)
    bpy.types.VIEW3D_MT_object.append(realtime_materials_menu)
    cat_generator()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for cat in cat_list:
        bpy.utils.unregister_class(cat)
    
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    bpy.types.VIEW3D_MT_add.remove(realtime_materials_menu)
    bpy.types.VIEW3D_MT_object.remove(realtime_materials_menu)


if __name__ == "__main__":
    register()