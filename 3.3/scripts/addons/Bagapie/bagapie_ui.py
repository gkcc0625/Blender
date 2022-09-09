from operator import index
from typing import Text
import bpy
import json
import addon_utils
from bpy.types import Menu, Panel, UIList, Operator
from bpy.props import StringProperty,EnumProperty,BoolProperty,IntProperty
from . presets import bagapieModifiers
import bpy.utils.previews

class BAGAPIE_MT_pie_menu(Menu):
    bl_label = "BagaPie"
    bl_idname = "BAGAPIE_MT_pie_menu"

    def draw(self, context):

        bagapie_pref = context.preferences.addons['Bagapie'].preferences
        # self.count_displayed = bagapie_pref.default_percent_display


        layout = self.layout
        target = bpy.context.active_object

        # BAGAPIE ASSETS
        addon_name = 'DevBagaPieAssets'
        success = addon_utils.check(addon_name)
        if success[0]:
            bp_assets = True
        else:
            bp_assets = False

        pie = layout.menu_pie()


    # PIE UI FOR ARRAY
        col = pie.column(align = False)
        row = col.row(align = False)
        row.label(text = "Array", icon = "MOD_ARRAY")
        row = col.row(align = True)
        col = row.column(align = True)
        col.scale_y = 1.1
        col.operator_enum("wm.array","array_type")
        if bp_assets:
            imp = col.operator("bagapieassets.callpieforimport", text="Draw Array Assets")
            imp.import_mode= 'DrawArray'
        col.separator(factor = 3)
        row.separator(factor = 1.5)

    # PIE UI FOR ARCHITECTURE
        col = pie.column(align = True)
        row = col.row(align = True)
        row.separator(factor = 1)
        col = row.column(align = True)
        col.label(text = "Architecture", icon = "HOME")
        col.scale_y = 1.2
        row = col.row(align = True)
        if bagapie_pref.wall:
            row.operator('bagapie.wall')
        if bagapie_pref.wallbrick:
            row.operator('bagapie.wallbrick')
        row = col.row(align = True)
        if bagapie_pref.window:
            row.operator("bagapie.window")
        if bagapie_pref.pipes:
            row.operator('bagapie.pipes')
        row = col.row(align = True)
        if bagapie_pref.column:
            row.operator('bagapie.column')
        if bagapie_pref.tiles:
            row.operator('bagapie.tiles')
        row = col.row(align = True)
        if bagapie_pref.beamwire:
            row.operator('bagapie.beamwire')
        if bagapie_pref.beam:
            row.operator('bagapie.beam')
        row = col.row(align = True)
        if bagapie_pref.linearstair:
            row.operator('bagapie.linearstair')
        if bagapie_pref.stairspiral:
            row.operator('bagapie.spiralstair')
        row = col.row(align = True)
        if bagapie_pref.floor:
            row.operator('bagapie.floor')
        if bagapie_pref.handrail:
            row.operator('bagapie.handrail')
        row = col.row(align = True)
        if bagapie_pref.cable:
            row.operator('bagapie.cable')
        if bagapie_pref.fence:
            row.operator('bagapie.fence')
        # row = col.row(align = True)
        if bagapie_pref.siding:
            row.operator('bagapie.siding')

    # PIE UI FOR BOOLEAN
        col = pie.column()
        col.label(text = "Boolean", icon = "MOD_BOOLEAN")
        split = col.split(align = True)
        split.scale_y = 1.2
        split.scale_x = 1.2
        split.operator_enum("wm.boolean", "operation_type")
        col.separator(factor = 14)

    # PIE UI FOR SCATTER
        col = pie.column(align = True)
        col.scale_y = 1.2
        col.label(text = "Scattering", icon = "OUTLINER_OB_CURVES")
        if bp_assets:
            if bagapie_pref.scatter:
                row = col.row(align=True)
                row.operator("wm.scatter").paint_mode = False
                imp = row.operator("bagapieassets.callpieforimport", text="Asset")
                imp.import_mode= 'Scatter'
            if bagapie_pref.scatterpaint:
                row = col.row(align=True)
                row.operator("wm.scatter",text = "Scatter Paint").paint_mode = True
                imp = row.operator("bagapieassets.callpieforimport", text="Asset")
                imp.import_mode= 'ScatterPaint'
            if bagapie_pref.pointsnapinstance:
                row = col.row(align=True)
                row.operator("bagapie.pointsnapinstance")
                imp = row.operator("bagapieassets.callpieforimport", text="Asset")
                imp.import_mode= 'PointSnapInstance'
        else:
            if bagapie_pref.scatter:
                col.operator("wm.scatter").paint_mode = False
            if bagapie_pref.scatterpaint:
                col.operator("wm.scatter",text = "Scatter Paint").paint_mode = True
            if bagapie_pref.pointsnapinstance:
                col.operator("bagapie.pointsnapinstance")
        if bagapie_pref.ivy:
            col.operator("bagapie.ivy")

    # PIE UI FOR DEFORM
        col = pie.column(align = True)
        row = col.row(align = True)
        col = row.column(align = True)
        col.label(text = "Deformation", icon = "MOD_DISPLACE")
        col.scale_y = 1.2
        if bagapie_pref.displace:
            col.operator("wm.displace")
        if bagapie_pref.instancesdisplace:
            col.operator("bagapie.instancesdisplace")
        if bagapie_pref.deform:
            col.operator('bagapie.deform')
        col.separator(factor = 14)
        row.separator(factor = 5)
        col.separator(factor = 6)

    # PIE UI FOR EFFECTOR
        col = pie.column(align = True)
        row = col.row(align = True)
        row.separator(factor = 5)
        col = row.column(align = True)
        col.label(text = "Effector", icon = "PARTICLES")
        col.scale_y = 1.2
        if target is not None:
            if "BagaPie_Scatter" in target.modifiers:
                if bagapie_pref.pointeffector:
                    col.operator("bagapie.pointeffector")
                if bagapie_pref.camculling:
                    col.operator('bagapie.camera')
                col.separator(factor = 18)
            else:
                col.label(text = "No Scatter available")
                col.separator(factor = 18)
        else:
            col.label(text = "No Scatter available")
            col.separator(factor = 18)

    # PIE UI FOR MANAGE
        col = pie.column(align = True)
        row = col.row(align = True)
        col = row.column(align = True)
        try:
            prop = target["bagapie"]
        except:
            prop = None
        # col.scale_x = 1.07
        # col.separator(factor = 14)
        if prop is not None and bagapie_pref.group:
            if target["bagapie_child"][0].hide_select == True:
                col.scale_x = 0.75
                col.separator(factor = 20)
            else:
                col.scale_x = 1.07
                col.separator(factor = 14)
        else:
            col.scale_x = 1.07
            col.separator(factor = 14)
        col.label(text = "Manage", icon = "PACKAGE")
        col.scale_y = 1.1
        if prop is not None and bagapie_pref.group:
            if bpy.context.object.type == 'EMPTY':
                col.operator("bagapie.makereal")
            if target["bagapie_child"][0].hide_select == True:
                col.operator("bagapie.editgroup")
            else:
                col.operator("bagapie.lockgroup")
            col.operator("bagapie.ungroup")
            col.operator("bagapie.instance")
        if bagapie_pref.proxy:
            col.operator("bagapie.proxy")
        if bagapie_pref.saveasasset:
            col.operator("bagapie.saveasset")
        if bagapie_pref.savematerial:
            col.operator("bagapie.savematerial")
        if bagapie_pref.group:
            col.operator("bagapie.group")
        row.separator(factor = 4.5)
        
    # PIE UI FOR CURVE
        col = pie.column(align = True)
        row = col.row(align = True)
        row.separator(factor = 4)
        col = row.column(align = True)
        col.separator(factor = 10)
        col.label(text = "Curves", icon = "MOD_CURVE")
        col.scale_y = 1.2
        if bp_assets:
            if bagapie_pref.autoarrayoncurve:
                row = col.row(align=True)
                row.operator("wm.curvearray")
                imp = row.operator("bagapieassets.callpieforimport", text="Asset")
                imp.import_mode= 'CurveArray'
        else:
            if bagapie_pref.autoarrayoncurve:
                col.operator("wm.curvearray")


class MY_UL_List(UIList):
    """BagaPie UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        val = json.loads(item.val)
        name = val['name']
        label = bagapieModifiers[name]['label']
        icon = bagapieModifiers[name]['icon']

        obj = context.object
        modifiers = val['modifiers']

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            mo_type = val['name']

            if mo_type == 'scatter':
                layout.label(text=modifiers[3], icon = icon)
            else:
                layout.label(text=label, icon = icon)
            row = layout.row(align=True)


            # List of modifier type to avoid dor apply/remove
            assets_type_list = ["stump","tree","grass","rock","plant"]
            avoid_list = ["pointeffector","pointsnapinstance","instancesdisplace","camera"]
            for a in assets_type_list:
                avoid_list.append(a)

            if mo_type not in avoid_list:
                row.operator("apply.modifier",text="", icon='CHECKMARK')

            if mo_type not in assets_type_list:
                row.operator('bagapie.'+ name +'_remove', text="", icon='REMOVE').index=index

            if mo_type == "scatter":

                scatter_modifier = obj.modifiers.get("BagaScatter")
                
                scatt_nde_visibility_op = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[22].default_value
                scatt_nde_visibility_bool = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[23].default_value

                if scatt_nde_visibility_op == False and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif scatt_nde_visibility_op == False and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "pointeffector":

                scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
                
                scatt_nde_visibility_op = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[5].default_value
                scatt_nde_visibility_bool = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[6].default_value

                if scatt_nde_visibility_op == False and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif scatt_nde_visibility_op == False and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "camera":
                scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
                
                scatt_nde_visibility_op = scatter_modifier.node_group.nodes[modifiers[1]].inputs[3].default_value
                scatt_nde_visibility_bool = scatter_modifier.node_group.nodes[modifiers[1]].inputs[4].default_value

                if scatt_nde_visibility_op == False and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == True:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op == True and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif scatt_nde_visibility_op == False and scatt_nde_visibility_bool == False:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "wallbrick":
                if obj.type == 'MESH':
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    if obj.modifiers[modifiers[0]].show_viewport == False:
                        viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'
                    if obj.modifiers[modifiers[0]].show_render == False:
                        render_icon = 'RESTRICT_RENDER_ON'
                else:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    if obj.modifiers[modifiers[1]].show_viewport == False:
                        viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'
                    if obj.modifiers[modifiers[1]].show_render == False:
                        render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type not in assets_type_list:
                viewport_icon = 'RESTRICT_VIEW_OFF'
                if obj.modifiers[modifiers[0]].show_viewport == False:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                render_icon = 'RESTRICT_RENDER_OFF'
                if obj.modifiers[modifiers[0]].show_render == False:
                    render_icon = 'RESTRICT_RENDER_ON'

            if mo_type not in assets_type_list:
                row.operator("hide.viewport",text="", icon=viewport_icon).index=index
                row.operator("hide.render",text="", icon=render_icon).index=index


class BAGAPIE_PT_modifier_panel(Panel):
    bl_idname = 'BAGAPIE_PT_modifier_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BagaPie"
    bl_label = "BagaPie Modifier"

    use_random: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH' or 'CURVE'
        )
        
    def draw(self, context):
        layout = self.layout

        obj = context.object
        obj_allowed_types = ["MESH","CURVE","EMPTY"]

        if obj and obj.type in obj_allowed_types:
            col = layout.column()

            # col.label(text="Modifier List :")

            col.template_list("MY_UL_List", "The_List", obj,
                            "bagapieList", obj, "bagapieIndex")
            
            try:
                prop = obj["bagapie_child"]
            except:
                prop = None

            if obj.bagapieIndex < len(obj.bagapieList):


                val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                type = val['name']
                modifiers = val['modifiers']
            
                label = bagapieModifiers[type]['label']
                icon = bagapieModifiers[type]['icon']

                if type == "wall":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text=label, icon=icon)

                    box.prop(obj.modifiers[modifiers[1]], 'screw_offset', text="Wall Height")
                    box.prop(obj.modifiers[modifiers[2]], 'thickness', text="Wall Thickness")
                    box.prop(obj.modifiers[modifiers[2]], 'offset', text="Wall Axis Offset")
                
                elif type == "wallbrick":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text=label, icon=icon)

                    if obj.type == 'MESH':
                        index = 0
                    else:
                        index = 1
                    box = box.column(align=True)
                    box.prop(obj.modifiers[modifiers[index]], '["Input_2"]', text="Height")
                    box.prop(obj.modifiers[modifiers[index]], '["Input_3"]', text="Thickness")
                    box.prop(obj.modifiers[modifiers[index]], '["Input_4"]', text="Length")
                    box = layout.box()
                    box = box.column(align=False)
                    box.prop(obj.modifiers[modifiers[index]], '["Input_5"]', text="Row Count")
                    box = box.column(align=True)
                    box.prop(obj.modifiers[modifiers[index]], '["Input_6"]', text="Row Offset")
                    box.prop(obj.modifiers[modifiers[index]], '["Input_7"]', text="Horizontal Offset")
                    box.prop(obj.modifiers[modifiers[index]], '["Input_8"]', text="Flip")
                    
                    box = layout.box()
                    row = box.row()
                    row.label(text="Random")
                    box = box.column(align=True)
                    row = box.row()
                    row.label(text="Position Min / Max")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_9"]', text="")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_10"]', text="")
                    row = box.row()
                    row.label(text="Rotation Min / Max")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_11"]', text="")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_12"]', text="")
                    row = box.row()
                    row.label(text="Scale Min / Max")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_13"]', text="")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_14"]', text="")
                    
                    box = layout.box()
                    row = box.row()
                    row.label(text="Deformation")
                    box = box.column(align=True)
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_15"]', text="")
                    row = box.row()
                    row.prop(obj.modifiers[modifiers[index]], '["Input_16"]', text="Scale")

                elif type == "pipes":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Pipe", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    row = box.row(align=True)
                    input_index = "Input_29"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    box.prop(modifier, '["Input_2"]', text="Radius")
                    box.prop(modifier, '["Input_10"]', text="Profile Resolution")
                    box.prop(modifier, '["Input_3"]', text="Offset")
                    box.prop(modifier, '["Input_4"]', text="Precision")
                    box.prop(modifier, '["Input_5"]', text="Resolution")
                    box.prop(modifier, '["Input_24"]', text="Bevel")
                    box.prop(modifier, '["Input_28"]', text="End Bevel")
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Junctions")
                    box.prop(modifier, '["Input_6"]', text="Density")
                    box.prop(modifier, '["Input_7"]', text="Depth")
                    box.label(text="Support")
                    box.prop(modifier, '["Input_8"]', text="Probability")
                    box.prop(modifier, '["Input_9"]', text="Radius")
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Random")
                    # USE parts
                    input_index = "Input_14"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Valve', depress = False)
                    else:
                        props = box.operator('switch.button', text='Use Valve', depress = True)
                    props.index = input_index
                    input_index = "Input_15"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Jonctions', depress = False)
                    else:
                        props = box.operator('switch.button', text='Use Jonctions', depress = True)
                    props.index = input_index
                    input_index = "Input_20"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Support', depress = False)
                    else:
                        props = box.operator('switch.button', text='Use Support', depress = True)
                    props.index = input_index
                    input_index = "Input_22"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Pipe End', depress = False)
                    else:
                        props = box.operator('switch.button', text='Use Pipe End', depress = True)
                    props.index = input_index
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Custom",  icon = "MESH_DATA")
                    box.label(text="Set in the modifier stack")
                    input_index = "Input_26"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Custom Valve', depress = True)
                    else:
                        props = box.operator('switch.button', text='Use Custom Valve', depress = False)
                    props.index = input_index
                    input_index = "Input_16"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Custom Jonctions', depress = True)
                    else:
                        props = box.operator('switch.button', text='Use Custom Jonctions', depress = False)
                    props.index = input_index
                    input_index = "Input_11"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Support Custom Profile', depress = True)
                    else:
                        props = box.operator('switch.button', text='Support Custom Profile', depress = False)
                    props.index = input_index



                    # MATERIAL
                    box.separator(factor = 3)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    if modifier["Input_18"] is None:
                        jonctions_mat = "None"
                    else:
                        jonctions_mat = modifier["Input_18"].name
                    box.label(text="Jonctions : "+jonctions_mat)
                    
                    if modifier["Input_19"] is None:
                        jonctions_mat = "None"
                    else:
                        jonctions_mat = modifier["Input_19"].name
                    box.label(text="Valve : "+jonctions_mat)
                    
                    if modifier["Input_21"] is None:
                        jonctions_mat = "None"
                    else:
                        jonctions_mat = modifier["Input_21"].name
                    box.label(text="Support : "+jonctions_mat)
                    
                    if modifier["Input_23"] is None:
                        jonctions_mat = "None"
                    else:
                        jonctions_mat = modifier["Input_23"].name
                    box.label(text="Pipe : "+jonctions_mat)
                    
                    box.separator(factor = 3)
                    box.label(text="Tips", icon = "INFO")
                    box.label(text="This modifier break UVs.")
                    box.label(text="You can still get UVs as an attribute")
                    box.label(text="Once the modifier is applied :")
                    box.label(text="Prop > Obj Data Prop > Attributes")

                elif type == "beamwire":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Pipe", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_2"]', text="Sides Count")
                    box.prop(modifier, '["Input_3"]', text="Radius")
                    box.prop(modifier, '["Input_4"]', text="Section Height")
                    box.prop(modifier, '["Input_5"]', text="Levels")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Diameter")
                    box.prop(modifier, '["Input_8"]', text="Diagonal")
                    box.prop(modifier, '["Input_7"]', text="Beam")
                    
                    box.label(text="Profile")
                    input_index = "Input_6"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Triangulate', depress = True, icon = "MOD_TRIANGULATE")
                    else:
                        props = box.operator('switch.button', text='Triangulate', depress = False,  icon = "MOD_TRIANGULATE")
                    props.index = input_index


                    row = box.row(align=True)
                    row.label(text="Diagonal")
                    input_index = "Input_11"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = "MESH_CIRCLE")
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = "MESH_CIRCLE")
                    props.index = input_index
                    input_index = "Input_11"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = False, icon = "MESH_PLANE")
                    else:
                        props = row.operator('switch.button', text='', depress = True, icon = "MESH_PLANE")
                    props.index = input_index
                    
                    row = box.row(align=True)
                    row.label(text="Beam")
                    input_index = "Input_9"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = "MESH_CIRCLE")
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = "MESH_CIRCLE")
                    props.index = input_index
                    input_index = "Input_9"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = False, icon = "MESH_PLANE")
                    else:
                        props = row.operator('switch.button', text='', depress = True, icon = "MESH_PLANE")
                    props.index = input_index



                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack :")
                    if modifier["Input_13"] is None:
                        jonctions_mat = "None"
                    else:
                        jonctions_mat = modifier["Input_13"].name
                    box.label(text=jonctions_mat)
                    
                elif type == "linearstair":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_3"]', text="Depth")
                    box.prop(modifier, '["Input_4"]', text="Step Height")
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_6"]', text="Width")
                    box.prop(modifier, '["Input_8"]', text="Thickness")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Properties")

                    row = box.row(align=True)
                    row.label(text="Type")
                    input_index = "Input_15"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = "MESH_PLANE")
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = "MESH_PLANE")
                    props.index = input_index
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = False, icon = "SNAP_FACE")
                    else:
                        props = row.operator('switch.button', text='', depress = True, icon = "SNAP_FACE")
                    props.index = input_index

                    row = box.row(align=True)
                    row.label(text="Use Handrail")
                    input_index = "Input_18"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = "X")
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = "X")
                    props.index = input_index
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = False, icon = "CHECKMARK")
                    else:
                        props = row.operator('switch.button', text='', depress = True, icon = "CHECKMARK")
                    props.index = input_index
                    
                    row = box.row(align=True)
                    row.label(text="Use Glass")
                    input_index = "Input_23"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = "X")
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = "X")
                    props.index = input_index
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = False, icon = "CHECKMARK")
                    else:
                        props = row.operator('switch.button', text='', depress = True, icon = "CHECKMARK")
                    props.index = input_index

                    input_index = "Input_15"
                    if modifier[input_index] == 1:
                        box = layout.box()
                        box.label(text="Stringers")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_16"]', text="Width")
                        box.prop(modifier, '["Input_17"]', text="Height")
                        box.prop(modifier, '["Input_19"]', text="Offset X")
                        box.prop(modifier, '["Input_20"]', text="Offset Y")

                    input_index = "Input_18"
                    if modifier[input_index] == 0:
                        box = layout.box()
                        box.label(text="Handrail")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_9"]', text="Offset")
                        box.prop(modifier, '["Input_10"]', text="Height")
                        box.prop(modifier, '["Input_11"]', text="Radius")
                        box.prop(modifier, '["Input_12"]', text="Balusters Radius")
                        box.prop(modifier, '["Input_13"]', text="Balusters Distance")
                        box.prop(modifier, '["Input_14"]', text="Handrail Resolution")
                        input_index = "Input_23"
                        if modifier[input_index] == 0:
                            box.prop(modifier, '["Input_21"]', text="Glass Size")
                            box.prop(modifier, '["Input_22"]', text="Glass Offset")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "tiles":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Tile", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    col = box.column(align=True)
                    row = col.row(align=True)
                    input_index = "Input_11"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Procedural', depress = False)
                    else:
                        props = row.operator('switch.button', text='Procedural', depress = True)
                    props.index = input_index
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='Custom', depress = False)
                    else:
                        props = row.operator('switch.button', text='Custom', depress = True)
                    props.index = input_index

                    if modifier[input_index] == 0:

                        col.prop(modifier, '["Input_6"]', text="Type")
                        col.prop(modifier, '["Input_2"]', text="Resolution")

                        col = box.column(align=True)
                        col.prop(modifier, '["Input_5"]', text="Length")
                        col.prop(modifier, '["Input_20"]', text="Height")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        col.prop(modifier, '["Input_4"]', text="Width Offset")
                        col.prop(modifier, '["Input_18"]', text="Thickness")

                        col = box.column(align=True)
                        col.prop(modifier, '["Input_7"]', text="Angle Tile")
                    else:
                        box.label(text="Set in the modifier stack")
                    

                    # REPARTITION

                    box = layout.box()
                    box.label(text="Repartition", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_8"]', text="Count X")
                    col.prop(modifier, '["Input_9"]', text="Count Y")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_23"]', text="Biais")
                    col.prop(modifier, '["Input_19"]', text="Superposition X")
                    col.prop(modifier, '["Input_10"]', text="Superposition Y")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_13"]', text="Triangulate")
                    col.prop(modifier, '["Input_14"]', text="Shift X")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_15"]', text="Angle")


                    box = layout.box()
                    box.label(text="Random", icon=icon)
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_16"]', text="Scale")
                    col.prop(modifier, '["Input_17"]', text="Rotation")
                    col.prop(modifier, '["Input_21"]', text="Seed")
                    


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "beam":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_2"]', text="Width")
                    box.prop(modifier, '["Input_3"]', text="Height")
                    box.prop(modifier, '["Input_8"]', text="Length")
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_4"]', text="Thickness")
                    box.prop(modifier, '["Input_5"]', text="Int Offset")
                    box.prop(modifier, '["Input_6"]', text="Bevel")
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_7"]', text="Bevel Count")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "column":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_6"]', text="Height")
                    input_index = "Input_7"
                    row = box.row(align=True)
                    row.label(text="Profile")
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='', depress = True, icon = 'MESH_PLANE')
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = 'MESH_PLANE')
                    props.index = input_index
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='', depress = True, icon = 'MESH_CIRCLE')
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = 'MESH_CIRCLE')
                    props.index = input_index

                    if modifier[input_index] == 0:
                        box.prop(modifier, '["Input_4"]', text="Width")
                        box.prop(modifier, '["Input_5"]', text="Depth")
                        box.separator(factor = 1)
                        box.label(text="Bevel")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_2"]', text="Size")
                        box.prop(modifier, '["Input_3"]', text="Count")
                    else:
                        box.prop(modifier, '["Input_9"]', text="Radius")
                        box.prop(modifier, '["Input_8"]', text="Resolution")
                    
                elif type == "deform":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)

                    box.label(text="Blend")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_2"]', text="X")
                    row.prop(modifier, '["Input_3"]', text="Y")
                    row.prop(modifier, '["Input_4"]', text="Z")
                    row = box.row(align=True)
                    input_index = "Input_8"
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='Flip', depress = True)
                    else:
                        props = row.operator('switch.button', text='Flip', depress = False)
                    props.index = input_index
                    box.separator(factor = 1)
                    box.label(text="Twist")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_5"]', text="X")
                    row.prop(modifier, '["Input_6"]', text="Y")
                    row.prop(modifier, '["Input_7"]', text="Z")
                    
                elif type == "floor":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    row = box.row(align=True)
                    row.label(text="X")
                    row.label(text="Y")
                    row.label(text="Z")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_3"]', text="")
                    row.prop(modifier, '["Input_4"]', text="")
                    row.prop(modifier, '["Input_5"]', text="")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_6"]', text="Vertices X")
                    box.prop(modifier, '["Input_7"]', text="Vertices Y")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_8"]', text="Offset X")
                    box.prop(modifier, '["Input_10"]', text="Offset Y")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_11"]', text="Random")
                    box.prop(modifier, '["Input_12"]', text="Offset")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")

                    # Custom mesh
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Custom", icon = "MESH_DATA")
                    input_index = "Input_14"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Custom Mesh', depress = True)
                        box.label(text="Set in the modifier stack")
                    else:
                        props = box.operator('switch.button', text='Use Custom Mesh', depress = False)
                    props.index = input_index
                    
                elif type == "spiralstair":
                    col.label(text="Modifier Properties :")
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_3"]', text="Radius")
                    box.prop(modifier, '["Input_2"]', text="Width")
                    box.prop(modifier, '["Input_7"]', text="Step Height")
                    box.prop(modifier, '["Input_6"]', text="Rotation")
                    box.prop(modifier, '["Input_8"]', text="Step Thickness")
                    input_index = "Input_9"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Invert', depress = True)
                    else:
                        props = box.operator('switch.button', text='Invert', depress = False)
                    props.index = input_index

                    # HANDRAIL
                    box = layout.box()
                    box.label(text="Handrail")
                    box = box.column()
                    row = box.row(align=True)
                    input_index = "Input_18"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Left', depress = False)
                    else:
                        props = row.operator('switch.button', text='Left', depress = True)
                    props.index = input_index
                    input_index = "Input_17"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Right', depress = False)
                    else:
                        props = row.operator('switch.button', text='Right', depress = True)
                    props.index = input_index
                    box = box.column(align=True)
                    if modifier["Input_17"] == 0 or modifier["Input_18"] == 0:
                        box.prop(modifier, '["Input_11"]', text="Height")
                        box.prop(modifier, '["Input_10"]', text="Offset")
                        box.prop(modifier, '["Input_14"]', text="Baluster Distance")
                        box.prop(modifier, '["Input_13"]', text="Resolution")
                        box = box.column()
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_12"]', text="Radius")
                        box.prop(modifier, '["Input_38"]', text="Profile Resolution")
                    
                    box.separator(factor = 1)
                    # GLASS
                    input_index = "Input_15"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Use Glass', depress = True)
                    else:
                        props = box.operator('switch.button', text='Use Glass', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        box.prop(modifier, '["Input_35"]', text="Glass Height")
                        box.prop(modifier, '["Input_40"]', text="Glass Width")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Support")
                    input_index = "Input_25"
                    if modifier[input_index] == 0:
                        props = box.operator('switch.button', text='Column', depress = False)
                    else:
                        props = box.operator('switch.button', text='Column', depress = True)
                    props.index = input_index
                    if modifier["Input_25"] == 1:
                        box.prop(modifier, '["Input_39"]', text="Resolution")

                    box.label(text="Stringer")
                    row = box.row(align=True)
                    input_index = "Input_21"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Left', depress = False)
                    else:
                        props = row.operator('switch.button', text='Left', depress = True)
                    props.index = input_index
                    input_index = "Input_22"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Right', depress = False)
                    else:
                        props = row.operator('switch.button', text='Right', depress = True)
                    props.index = input_index

                    box = box.column()
                    if modifier["Input_21"] == 0 or modifier["Input_22"] == 0:
                        box.label(text="Width")
                        row = box.row(align=True)
                        if modifier["Input_21"] == 0:
                            row.prop(modifier, '["Input_19"]', text="L")
                        if modifier["Input_22"] == 0:
                            row.prop(modifier, '["Input_20"]', text="R")
                        box.label(text="Offset")
                        row = box.row(align=True)
                        if modifier["Input_21"] == 0:
                            row.prop(modifier, '["Input_33"]', text="L")
                        if modifier["Input_22"] == 0:
                            row.prop(modifier, '["Input_34"]', text="R")
                        box.prop(modifier, '["Input_23"]', text="Thickness")
                        box.prop(modifier, '["Input_24"]', text="Offset Z")






                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "handrail":
                    col.label(text="Modifier Properties :")


                    # MAIN

                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_8"]', text="Height")
                    box.prop(modifier, '["Input_2"]', text="Module Length")
                    row = box.row(align=True)
                    input_index = "Input_32"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index



                    # GLASS

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_15"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='GLass', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='GLass', depress = False)
                    props.index = input_index

                    box = box.column(align=True)
                    if modifier[input_index] == 1:
                        box.prop(modifier, '["Input_4"]', text="Size")
                        box.prop(modifier, '["Input_9"]', text="Offset")
                        box.prop(modifier, '["Input_10"]', text="Thickness")
                        box.prop(modifier, '["Input_3"]', text="Proportion")
                        box.separator(factor = 1)
                            
                        input_index = "Input_14"
                        row = box.row()
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text='Use Connector', depress = True)
                        else:
                            row.scale_y = 1.5
                            props = row.operator('switch.button', text='Use Connector', depress = False)
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == 1:
                            box.prop(modifier, '["Input_5"]', text="Offset")
                            box.prop(modifier, '["Input_47"]', text="Length")
                            row = box.row(align=True)
                            row.prop(modifier, '["Input_6"]', text="X")
                            row.prop(modifier, '["Input_7"]', text="Y")




                    # BALUSTER

                    box = layout.box()
                    input_index = "Input_17"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Baluster', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Baluster', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_16"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        input_index = "Input_16"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == 1:
                            box.prop(modifier, '["Input_20"]', text="Width")
                            box.prop(modifier, '["Input_21"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_18"]', text="Radius")
                            box.prop(modifier, '["Input_19"]', text="Resolution")




                    # HANDRAIL

                    box = layout.box()
                    input_index = "Input_22"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Handrail', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Handrail', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_23"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == 1:
                            box.prop(modifier, '["Input_26"]', text="Width")
                            box.prop(modifier, '["Input_27"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_24"]', text="Radius")
                            box.prop(modifier, '["Input_25"]', text="Resolution")
                        box.prop(modifier, '["Input_28"]', text="Curve Resolution")




                    # HORIZONTAL BALUSTER

                    box = layout.box()
                    input_index = "Input_33"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Horizontal Baluster', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Horizontal Baluster', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_36"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == 1:
                            box.prop(modifier, '["Input_39"]', text="Width")
                            box.prop(modifier, '["Input_40"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_38"]', text="Radius")
                            box.prop(modifier, '["Input_37"]', text="Resolution")
                        box.prop(modifier, '["Input_35"]', text="Curve Resolution")
                        box.prop(modifier, '["Input_41"]', text="Offset Z")
                        box.prop(modifier, '["Input_42"]', text="Distance")
                        box.prop(modifier, '["Input_43"]', text="Count")
                        box.prop(modifier, '["Input_45"]', text="Offset")


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "fence":
                    col.label(text="Modifier Properties :")

                    # MAIN

                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_4"]', text="Fence Offset")
                    row = box.row(align=True)
                    input_index = "Input_54"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    if modifier[input_index] == 0:
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index

                    
                    # BASE WALL

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_35"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Wall', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='Wall', depress = False)
                    props.index = input_index

                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_2"]', text="Height")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        
                        input_index = "Input_51"
                        if modifier[input_index] == 1:
                            props = col.operator('switch.button', text='Even Thickness', depress = True)
                        else:
                            props = col.operator('switch.button', text='Even Thickness', depress = False)
                        props.index = input_index
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_44"
                        if modifier[input_index] == 1:
                            props = col.operator('switch.button', text='Cap Flashing', depress = True)
                        else:
                            props = col.operator('switch.button', text='Cap Flashing', depress = False)
                        props.index = input_index
                        if modifier[input_index] == 1:
                            col.prop(modifier, '["Input_37"]', text="Height")
                            col.prop(modifier, '["Input_38"]', text="Thickness")
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_53"
                        if modifier[input_index] == 1:
                            props = col.operator('switch.button', text='Auto Smooth', depress = True)
                        else:
                            props = col.operator('switch.button', text='Auto Smooth', depress = False)
                        props.index = input_index
                        if modifier[input_index] == 1:
                            col.prop(modifier, '["Input_52"]', text="Angle")
                        



                    # FENCE VERTICAL

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_42"
                    if modifier[input_index] == 1:
                        props = row.operator('switch.button', text='Fence Vertical', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='Fence Vertical', depress = False)
                    props.index = input_index

                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_14"]', text="Distance")
                        col.prop(modifier, '["Input_36"]', text="End Wall Offset")
                        col.prop(modifier, '["Input_55"]', text="Offset")
                        col.prop(modifier, '["Input_15"]', text="Scale")
                        col.prop(modifier, '["Input_16"]', text="Scale Random")
                        col.prop(modifier, '["Input_34"]', text="Scale Z Random")
                        
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_6"]', text="Rotation")
                        col.prop(modifier, '["Input_7"]', text="Random Tangent")
                        col.prop(modifier, '["Input_50"]', text="Random Axis")

                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_8"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        if modifier[input_index] == 1:
                            col.prop(modifier, '["Input_13"]', text="Radius")
                            col.prop(modifier, '["Input_12"]', text="Resolution")
                        else:
                            col.prop(modifier, '["Input_10"]', text="Width")
                            col.prop(modifier, '["Input_11"]', text="Height")
                        



                    # TIMBER POST

                    box = layout.box()
                    input_index = "Input_39"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Timber Post', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Timber Post', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_17"]', text="Spacing")
                        col.prop(modifier, '["Input_18"]', text="Height")
                        col.prop(modifier, '["Input_32"]', text="Offset")
                            
                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_19"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        if modifier[input_index] == 1:
                            col.prop(modifier, '["Input_23"]', text="Radius")
                            col.prop(modifier, '["Input_22"]', text="Resolution")
                        else:
                            col.prop(modifier, '["Input_20"]', text="Width")
                            col.prop(modifier, '["Input_21"]', text="Height")
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_40"
                        if modifier[input_index] == 1:
                            props = col.operator('switch.button', text='Fixation', depress = True)
                        else:
                            props = col.operator('switch.button', text='Fixation', depress = False)
                        props.index = input_index
                        if modifier[input_index] == 1:
                            col.prop(modifier, '["Input_33"]', text="Dimmensions")




                    # HORIZONTAL

                    box = layout.box()
                    input_index = "Input_43"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Horizontal', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Horizontal', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_29"]', text="Base Offset")
                        col.prop(modifier, '["Input_30"]', text="Top Offset")


                        row = col.row(align=True)
                        input_index = "Input_41"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text='Full', depress = True, icon = 'SNAP_FACE')
                        else:
                            props = row.operator('switch.button', text='Full', depress = False, icon = 'SNAP_FACE')
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text='Wire', depress = False, icon = 'ALIGN_JUSTIFY')
                        else:
                            props = row.operator('switch.button', text='Wire', depress = True, icon = 'ALIGN_JUSTIFY')
                        props.index = input_index
                        
                        if modifier[input_index] == 0:
                            col.prop(modifier, '["Input_31"]', text="Count")
                            
                            col = box.column(align=True)
                            row = col.row(align=True)
                            row.label(text="Profile")
                            input_index = "Input_24"
                            if modifier[input_index] == 1:
                                props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                            else:
                                props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                            props.index = input_index
                            if modifier[input_index] == 1:
                                props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                            else:
                                props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                            props.index = input_index

                            if modifier[input_index] == 1:
                                col.prop(modifier, '["Input_28"]', text="Radius")
                                col.prop(modifier, '["Input_27"]', text="Resolution")
                            else:
                                col.prop(modifier, '["Input_25"]', text="Width")
                                col.prop(modifier, '["Input_26"]', text="Height")





                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")

                    


                    # THANKS
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Thanks !", icon = "FUND")
                    box.label(text="Thanks to Zeroskilz.")
                    box.label(text="He created the Curve to Mesh")
                    box.label(text="Even Thickness node !")

                elif type == "siding":
                    col.label(text="Modifier Properties :")

                    box = layout.box()
                    box.label(text="Main", icon='FACESEL')
                    col = box.column(align=True)
                    col.scale_y = 2
                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_19"
                    if modifier[input_index] == 1:
                        props = col.operator('switch.button', text='Keep Original', depress = True)
                    else:
                        props = col.operator('switch.button', text='Keep Original', depress = False)
                    props.index = input_index

                    
                    # X

                    box = layout.box()
                    box.label(text="X", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_6"
                    if modifier[input_index] == 1:
                        props = col.operator('switch.button', text='X Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='X Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_10"]', text="Distance")
                        col.prop(modifier, '["Input_11"]', text="Width")
                        col.prop(modifier, '["Input_12"]', text="Thickness")
                        col.prop(modifier, '["Input_16"]', text="Angle")

                    
                    # Y

                    box = layout.box()
                    box.label(text="Y", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_7"
                    if modifier[input_index] == 1:
                        props = col.operator('switch.button', text='Y Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='Y Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_9"]', text="Distance")
                        col.prop(modifier, '["Input_13"]', text="Width")
                        col.prop(modifier, '["Input_14"]', text="Thickness")
                        col.prop(modifier, '["Input_17"]', text="Angle")

                    
                    # Z

                    box = layout.box()
                    box.label(text="Z", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_8"
                    if modifier[input_index] == 1:
                        props = col.operator('switch.button', text='Z Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='Z Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == 1:
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_4"]', text="Distance")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        col.prop(modifier, '["Input_2"]', text="Thickness")
                        col.prop(modifier, '["Input_15"]', text="Angle")
                        




                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")
                    
                elif type == "cable":
                    col.label(text="Modifier Properties :")
                    modifier = obj.modifiers[modifiers[0]]


                    # SHAPE

                    box = layout.box()
                    box.label(text="Shape", icon=icon)

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_2"]', text="Gravity")
                    col.prop(modifier, '["Input_29"]', text="Rigidity")
                    col.prop(modifier, '["Input_8"]', text="Resolution")
                    col.prop(modifier, '["Input_7"]', text="Smooth")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_4"]', text="Start Offset")
                    col.prop(modifier, '["Input_5"]', text="Start Rigidity")
                    col.prop(modifier, '["Input_9"]', text="Edge Collision")



                    # PROFIL

                    box = layout.box()
                    box.label(text="Profil", icon="PROP_OFF")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_11"]', text="Radius")
                    col.prop(modifier, '["Input_12"]', text="Cable Count")
                    col.prop(modifier, '["Input_6"]', text="Cable Radius")
                    col.prop(modifier, '["Input_13"]', text="Rotation")
                    col.prop(modifier, '["Input_10"]', text="Resolution")



                    # RANDOM

                    box = layout.box()
                    box.label(text="Randomize")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_14"]', text="Radius Noise")
                    col.prop(modifier, '["Input_18"]', text="Radius Noise Scale")
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_15"]', text="Radius per Curve")
                    col.prop(modifier, '["Input_16"]', text="Radius offset")
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_17"]', text="Tilt Noise")
                    col.prop(modifier, '["Input_19"]', text="Tilt Noise Scale")




                    # FIXATION

                    box = layout.box()
                    input_index = "Input_34"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Fixation', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Fixation', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                        row = box.row(align=True)
                        input_index = "Input_23"
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text='Procedural', depress = False)
                        else:
                            props = row.operator('switch.button', text='Procedural', depress = True)
                        props.index = input_index
                        if modifier[input_index] == 1:
                            props = row.operator('switch.button', text='Custom', depress = True)
                        else:
                            props = row.operator('switch.button', text='Custom', depress = False)
                        props.index = input_index
                        col = box.column(align=True)
                            
                        if modifier[input_index] == 0:
                            col.prop(modifier, '["Input_20"]', text="Thickness")
                            col.prop(modifier, '["Input_21"]', text="Radius")
                            col.prop(modifier, '["Input_22"]', text="Angle")
                        else:
                            col.label(text="Set object in modifier stack.")

                        
                        

                    # RINGS

                    box = layout.box()
                    input_index = "Input_30"
                    if modifier[input_index] == 1:
                        props = box.operator('switch.button', text='Rings', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Rings', depress = False)
                    props.index = input_index
                    if modifier[input_index] == 1:
                            col = box.column(align=True)
                            col.prop(modifier, '["Input_27"]', text="Spacing")
                            col.prop(modifier, '["Input_25"]', text="Length")
                            col.prop(modifier, '["Input_26"]', text="Thickness")
                        


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.label(text="Set in the modifier stack")

                elif type == "array":
                    col.label(text="Modifier Properties :")
                    array_modifier = obj.modifiers[modifiers[0]]
                    array_type = modifiers[1]

                    if array_type == 'LINE':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_4"]', text = "Count")
                        col.prop(array_modifier, '["Input_3"]', text = "Constant Offset")
                        col.prop(array_modifier, '["Input_5"]', text = "Relative Offset")

                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_6"]', text = "Position")
                        box.prop(array_modifier, '["Input_7"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_8"]', text = "Scale")
                        box.prop(array_modifier, '["Input_9"]', text = "Seed")

                    if array_type == 'GRID':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_2"]', text = "Count X")
                        col.prop(array_modifier, '["Input_9"]', text = "Count Y")
                        box = layout.box()
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_3"]', text = "Constant Offset X")
                        col.prop(array_modifier, '["Input_11"]', text = "Constant Offset Y")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_4"]', text = "Relative Offset X")
                        col.prop(array_modifier, '["Input_10"]', text = "Relative Offset Y")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_12"]', text = "Midlevel X")
                        col.prop(array_modifier, '["Input_13"]', text = "Midlevel Y")

                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_5"]', text = "Position")
                        box.prop(array_modifier, '["Input_6"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_8"]', text = "Scale")
                        box.prop(array_modifier, '["Input_7"]', text = "Seed")

                    if array_type == 'CIRCLE':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_2"]', text = "Count")
                        col.prop(array_modifier, '["Input_3"]', text = "Ring Count")
                        col.prop(array_modifier, '["Input_19"]', text = "Use Constant Distance")
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_4"]', text = "Radius")
                        col.prop(array_modifier, '["Input_8"]', text = "Ring Offset")
                        col.prop(array_modifier, '["Input_9"]', text = "Ring Offset Z")
                        col.prop(array_modifier, '["Input_20"]', text = "Constant Distance")

                        col.prop(array_modifier, '["Input_14"]', text = "Rotation")
                        col.prop(array_modifier, '["Input_10"]', text = "Align to Center")

                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_17"]', text = "Position")
                        box.prop(array_modifier, '["Input_15"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_16"]', text = "Scale")
                        box.prop(array_modifier, '["Input_18"]', text = "Seed")
                        
                    if array_type == 'CURVE':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_2"]', text = "Target")
                        col.label(text="Set target in Modifier Prop")
                        col.prop(array_modifier, '["Input_5"]', text = "Length")
                        # col.prop(array_modifier["Input_4"], 'default_value', text="Use Count")
                        col.prop(array_modifier, '["Input_4"]', text = "Use Count")
                        col.prop(array_modifier, '["Input_6"]', text = "Count")
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_3"]', text = "Rotation")
                        col.prop(array_modifier, '["Input_14"]', text = "Scale")
                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_7"]', text = "Random Position")
                        box.prop(array_modifier, '["Input_8"]', text = "Random Rotation")
                        box.prop(array_modifier, '["Input_9"]', text = "Random Scale")
                        box.prop(array_modifier, '["Input_12"]', text = "Seed")

                        box = layout.box()
                        box.prop(array_modifier, '["Input_10"]', text = "Align to Vector")
                        box = box.row(align=True)
                        box.prop(array_modifier, '["Input_11"]', text = "Vector")
        
                elif type == "scatter":
                    col.label(text="Modifier Properties :")
                    col.operator("rename.layer", text= "Rename Layer", icon = 'GREASEPENCIL')
                    scatter_modifier = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]]
                    
                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(scatter_modifier.inputs[2], 'default_value', text = "Distance Min")
                    row = col.row(align=True)
                    row.prop(scatter_modifier.inputs[3], 'default_value', text = "Density Max")
                    tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                    tips.message = 'Keep this value as low as possible to preserve performance.'
                    col.prop(scatter_modifier.inputs[4], 'default_value', text = "% Viewport Display")
                    col.prop(scatter_modifier.inputs[5], 'default_value', text = "Align Normal")
                    col.prop(scatter_modifier.inputs[6], 'default_value', text = "Seed")
 
                    
                    col = layout.column(align=True)
                    col.scale_y = 2
                    if bpy.context.object.mode == 'OBJECT':
                        row = col.row(align=True)
                        row.operator("add.asset", text= "Add Assets", icon = 'ADD')
                        row.operator("remove.asset", text= "Remove Assets", icon = 'REMOVE')
                        row = col.row(align=True)
                        row.operator("use.proxyonassets", text= "Proxy", icon = 'RESTRICT_VIEW_OFF').use_proxy = True
                        row.operator("use.proxyonassets", text= "Proxy", icon = 'RESTRICT_VIEW_ON').use_proxy = False
                        if obj.modifiers[modifiers[0]].node_group.nodes.get('BagaPie_Camera_Culling'):
                            row = col.row(align=True)
                            if len(scatter_modifier.inputs[24].links) > 0:
                                props = row.operator('use.cameracullingonlayer', text='Camera Culling', depress = True, icon = 'OUTLINER_OB_CAMERA')
                            else:
                                props = row.operator('use.cameracullingonlayer', text='Use Camera Culling', depress = False, icon = 'CAMERA_DATA')
                            props.index = 24

                    col = layout.column(align=True)
                    col.scale_y = 2
                    if bpy.context.object.mode == 'OBJECT':
                        row = col.row(align=True)
                        row.operator("switch.mode", text= "Paint !", icon = 'BRUSH_DATA')
                        if scatter_modifier.inputs[26].default_value == True:
                            props = row.operator('switch.boolnode', text='', depress = True, icon = 'ARROW_LEFTRIGHT')
                        else:
                            props = row.operator('switch.boolnode', text='', depress = False, icon = 'ARROW_LEFTRIGHT')
                        props.index = 26

                    if bpy.context.object.mode == 'WEIGHT_PAINT':

                        col.scale_y = 2
                        col.operator("clean.paint", text= "CLEAR PAINT", icon = 'FILE_REFRESH')
                        col.operator("invert.weight", text= "INVERT PAINT", icon = 'ARROW_LEFTRIGHT')
                        paint_invert_mode = False
                        if scatter_modifier.inputs[26].default_value == True:
                            paint_invert_mode = True
                        if paint_invert_mode == True:
                            if bpy.context.scene.tool_settings.unified_paint_settings.weight < 0.5: 
                                row = col.row(align=True)
                                row.operator("invert.paint", text="Add particles", depress = False, icon = 'ADD')
                                row.operator("invert.paint", text="Remove particles", depress = True, icon = 'REMOVE')
                            else:
                                row = col.row(align=True)
                                row.operator("invert.paint", text="Add particles", depress = True, icon = 'ADD')
                                row.operator("invert.paint", text="Remove particles", depress = False, icon = 'REMOVE')
                        else:
                            if bpy.context.scene.tool_settings.unified_paint_settings.weight < 0.5:
                                row = col.row(align=True)
                                row.operator("invert.paint", text="Add particles", depress = True, icon = 'ADD')
                                row.operator("invert.paint", text="Remove particles", depress = False, icon = 'REMOVE')
                            else:
                                row = col.row(align=True)
                                row.operator("invert.paint", text="Add particles", depress = False, icon = 'ADD')
                                row.operator("invert.paint", text="Remove particles", depress = True, icon = 'REMOVE')

                        col = layout.column()
                        col.scale_y = 2
                        col.operator("switch.mode", text="EXIT !", icon = 'FILE_PARENT')
                        
                        box = layout.box()
                        box = box.column(align=True)
                        box.label(text="Tips", icon = "INFO")
                        box.label(text="Paint resolution depend")
                        box.label(text="on your surface resolution !")
                        box.separator(factor = 2)
                        box.label(text="If necessary,")
                        box.label(text="subdivide your surface.")

                    box = layout.box()
                    box = box.column(align=True)
                    row = box.row()
                    row.label(text="Position")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[7], 'default_value', text = "")
                    row = box.row()
                    row.label(text="Rotation")
                    box = box.column(align=False)
                    row = box.row()
                    row.prop(scatter_modifier.inputs[8], 'default_value', text = "")
                    row = box.row()
                    row = box.column(align=True)
                    row.prop(scatter_modifier.inputs[9], 'default_value', text = "Scale Min")
                    row.prop(scatter_modifier.inputs[10], 'default_value', text = "Scale Max")

                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.label(text="Position Min / Max")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[11], 'default_value', text = "")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[12], 'default_value', text = "")
                    row = box.row()
                    row.label(text="Rotation Min / Max")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[13], 'default_value', text = "")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[14], 'default_value', text = "")
                    row = box.row()
                    row.label(text="Scale Min / Max")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[15], 'default_value', text = "")
                    row = box.row()
                    row.prop(scatter_modifier.inputs[16], 'default_value', text = "")

                    box = layout.box()
                    box.label(text="Texture Mask")
                    col = box.column(align=True)
                    col.prop(scatter_modifier.inputs[17], 'default_value', text = "Fac")
                    col.prop(scatter_modifier.inputs[18], 'default_value', text = "Scale")
                    col.prop(scatter_modifier.inputs[19], 'default_value', text = "Offset")
                    col.prop(scatter_modifier.inputs[20], 'default_value', text = "Smooth")
                    col.label(text="Position :")
                    row = col.row()
                    row.prop(scatter_modifier.inputs[27], 'default_value', text = "")
                    col.prop(scatter_modifier.inputs[28], 'default_value', text = "Invert Mask")

                    box = layout.box()
                    box.label(text="Tuto & Assets !")
                    col = box.column(align=True)
                    col.scale_y = 2
                    col.operator("wm.url_open", text="Scatter Tutorial", icon = 'PLAY').url = "https://youtu.be/51iRC0A4Nzw"
                    col.operator("wm.url_open", text="Get BagaPie Assets !", icon = 'FUND').url = "https://blendermarket.com/products/bagapie-assets"
                    col.operator("wm.url_open", text="Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"

                elif type == "displace":
                    col.label(text="Modifier Properties :")
                    displace_subdiv = obj.modifiers[modifiers[0]]
                    displace_disp = obj.modifiers[modifiers[1]]
                    texture = bpy.data.textures[modifiers[2]]

                    box = layout.box()# SUBDIVISION
                    box.label(text="Subdivision")
                    box.prop(displace_subdiv, 'subdivision_type', text="Type")
                    box = box.column(align=True)
                    box.prop(displace_subdiv, 'levels', text="Subdivision")
                    box.prop(displace_subdiv, 'render_levels', text="Subdivision Render")

                    box = layout.box()# DISPLACEMENT
                    box.label(text="Displace")
                    box.prop(displace_disp, 'direction', text="Direction")
                    box = box.column(align=True)
                    box.prop(displace_disp, 'strength', text="Strength")
                    box.prop(displace_disp, 'mid_level', text="Midlevel")
                    box = layout.box()

                    box.label(text="Texture")# TEXTURE
                    box.prop(texture, 'type', text="Type")
                    if texture.type == 'IMAGE':
                        box.label(text="Go in Texture tab.")
                    box.prop(displace_disp, 'texture_coords', text="Mapping")
                    if displace_disp.texture_coords == 'OBJECT':
                        box.prop(displace_disp, 'texture_coords_object', text="Object")
                    box = box.column(align=True)
                    box.prop(texture, 'noise_scale', text="Scale")
                    box.prop(texture, 'intensity', text="Brightness")
                    box.prop(texture.color_ramp.elements[0], 'position', text="Ramp Min")
                    box.prop(texture.color_ramp.elements[1], 'position', text="Ramp Max")

                elif type == "scatterpaint":
                    col.label(text="Modifier Properties :")

                    col = layout.column(align=True)
                    col.scale_y = 2.0

                    if bpy.context.object.mode == 'OBJECT':
                        col.operator("switch.mode", text= "Paint !")

                    if bpy.context.object.mode == 'WEIGHT_PAINT':
                        if bpy.context.scene.tool_settings.unified_paint_settings.weight < 1:
                            col.operator("invert.paint", text="ADD")
                        else:
                            col.operator("invert.paint", text="REMOVE")

                        col.scale_y = 1
                        col.operator("clean.paint", text= "CLEAN PAINT")
                        col.operator("invert.weight", text= "INVERT PAINT")

                        col = layout.column()
                        col.scale_y = 2
                        col.operator("switch.mode", text="EXIT !")

                    scatter_modifier = obj.modifiers.get("BagaScatter")
                    scatt_nde_group = scatter_modifier.node_group
                    scatterpaint_count = int(modifiers[2])
                    scatt_nde_main = scatt_nde_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(scatt_nde_main.inputs[1], 'default_value', text = "Source Collection")
                    col.prop(scatt_nde_main.inputs[2], 'default_value', text = "Distance Min")
                    col.prop(scatt_nde_main.inputs[3], 'default_value', text = "Density")
                    col.prop(scatt_nde_main.inputs[4], 'default_value', text = "% Viewport Display")


                    box = layout.box()
                    box = box.column(align=True)
                    box.prop(scatt_nde_main.inputs[7], 'default_value', text = "Random Position")
                    box.prop(scatt_nde_main.inputs[8], 'default_value', text = "Random Rotation")
                    box.prop(scatt_nde_main.inputs[11], 'default_value', text = "Align Z")
                    box.prop(scatt_nde_main.inputs[9], 'default_value', text = "Scale Min")
                    box.prop(scatt_nde_main.inputs[10], 'default_value', text = "Scale Max")
                    box.prop(scatt_nde_main.inputs[5], 'default_value', text = "Seed")

                    box.label(text="Current Layer :")
                    box.prop(obj.vertex_groups, 'active_index', text = obj.vertex_groups.active.name)

                elif type == "curvearray":
                    col.label(text="Modifier Properties :")
                    arraycurve_array = obj.modifiers[modifiers[0]]
                    arraycurve_curve = obj.modifiers[modifiers[1]]

                    col = layout.column()
                    col.prop(arraycurve_curve, 'deform_axis', text="Axis")
                    box = layout.box()
                    box.prop(arraycurve_array, 'use_relative_offset', text="Use Relative Offset")
                    box.prop(arraycurve_array, 'relative_offset_displace', text="Ralative Offset")
                    box = layout.box()
                    box.prop(arraycurve_array, 'use_constant_offset', text="Use Constant Offset")
                    box.prop(arraycurve_array, 'constant_offset_displace', text="Constant Offset")

                elif type == "window":
                    col.label(text="Modifier Properties :")

                    if modifiers[6] == "win":
                        window_weld = obj.modifiers[modifiers[0]]
                        window_disp = obj.modifiers[modifiers[1]]
                        window_wire = obj.modifiers[modifiers[2]]
                        window_bevel = obj.modifiers[modifiers[3]]

                        box = layout.box()
                        box.prop(window_disp, 'strength', text="Offset")
                        box.prop(window_wire, 'thickness', text="Window Size")
                        box.prop(window_wire, 'offset', text="Window Offset")
                        box.prop(window_bevel, 'width', text="Window Bevel")
                        box.prop(window_weld, 'merge_threshold', text="Merge by Distance")


                        col = layout.column()
                        col.scale_y = 1.5
                        active_ob = bpy.context.active_object
                        if bpy.context.object.mode == 'OBJECT' and active_ob == obj:
                            col.operator("bool.mode", text= "More Window !")
                        elif bpy.context.object.mode == 'EDIT' and active_ob == obj:
                            col.operator("bool.mode", text= "EXIT")
                        else:
                            col.label(text="Selects the bounding box of the window")



                        # col = layout.column()

                        # col = layout.column(align=True)
                        # col.separator(factor = 3)


                        # lines_x = obj["line_x"]-1
                        # lines_y = obj["line_y"]

                        # col.prop(obj, '["line_x"]', text="Horizontal", toggle = True, invert_checkbox = True)
                        # col.prop(obj, '["line_y"]', text="Vertical", toggle = False, invert_checkbox = False)
                        # # col.prop(obj, '["cut_prop"]', toggle=True, slider=False)
                        # col = col.box()
                        # col = col.column(align=True)
                        # # col.prop(obj, 'array_length', text="Length")

                        # # obj["line_bool_g"][array_length] = (lines_x+1)*lines_y
                        # # bpy.ops.wm.properties_edit(obj, property_name="line_bool_g",array_length=(lines_x+1)*lines_y)

                        # # line_bool_g
                        # # line_bool_m
                        # glass_statut = obj['line_bool_g']
                        # idx_glass = 0

                        # for line_y in range(lines_y):
                        #     row = col.row(align = True) # VITRAGES COLUMN
                        #     row.scale_y = (3.5/(lines_x+1))*2

                        #     if glass_statut[idx_glass] == 1:
                        #         emb = True
                        #     else:
                        #         emb = False
                        #     gl = row.operator("switch.glass", text= "", emboss=emb)
                        #     gl.index = idx_glass
                        #     idx_glass += 1

                        #     for line_x in range(lines_x):
                        #         if glass_statut[idx_glass] == 1:
                        #             emb = True
                        #         else:
                        #             emb = False
                        #         row.scale_x = 0.05
                        #         row.operator("switch.glass", text= "")
                        #         row.scale_x = 1
                        #         gl = row.operator("switch.glass", text= "", emboss=emb)
                        #         gl.index = idx_glass
                        #         idx_glass +=1
                        

                        #     if line_y+1 != lines_y: # MENEAU HORIZONTAUX
                        #         row = col.row(align = True)
                        #         row.scale_y = (0.7/(lines_x+1))*2
                        #         row.operator("switch.glass", text= "")
                        #         for line in range(lines_x):
                        #             row.scale_x = 0.05
                        #             row.operator("switch.glass", text= "")
                        #             row.scale_x = 1
                        #             row.operator("switch.glass", text= "")




                    elif modifiers[6] == "wall":

                        window = bpy.data.objects[modifiers[7]]

                        window_weld = window.modifiers[modifiers[1]]
                        window_disp = window.modifiers[modifiers[2]]
                        window_wire = window.modifiers[modifiers[3]]
                        window_bevel = window.modifiers[modifiers[4]]

                        box = layout.box()
                        box.prop(window_disp, 'strength', text="Offset")
                        box.prop(window_wire, 'thickness', text="Window Size")
                        box.prop(window_wire, 'offset', text="Window Offset")
                        box.prop(window_bevel, 'width', text="Window Bevel")
                        box.prop(window_weld, 'merge_threshold', text="Merge by Distance")
                        
                elif type == "pointeffector":
                    col.label(text="Modifier Properties :")
                    effector_modifier = obj.modifiers[modifiers[0]]
                    effector_nde = effector_modifier.node_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(effector_nde.inputs[1], 'default_value', text = "Distance Min")
                    col.prop(effector_nde.inputs[2], 'default_value', text = "Distance Max")
                    col.prop(effector_nde.inputs[3], 'default_value', text = "Density")

                elif type == "camera":
                    col.label(text="Modifier Properties :")
                    effector_modifier = obj.modifiers[modifiers[0]]
                    effector_nde = effector_modifier.node_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(effector_nde.inputs[1], 'default_value', text = "X Ratio")
                    col.prop(effector_nde.inputs[2], 'default_value', text = "Y Ratio")
                    col.prop(effector_nde.inputs[5], 'default_value', text = "Offset")
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Tips", icon = "INFO")
                    box.label(text="Culling resolution depend")
                    box.label(text="on your surface resolution !")
                    box.separator(factor = 2)
                    box.label(text="If necessary,")
                    box.label(text="subdivide your surface.")

                elif type == "boolean":
                    col.label(text="Modifier Properties :")
                    box = layout.box()

                    box.label(text="Boolean Type")
                    box.prop(obj.modifiers[modifiers[0]], 'operation', text="")
                    box.prop(obj.modifiers[modifiers[0]], 'solver', text="")
                    if obj.modifiers[modifiers[0]].solver == 'EXACT':
                        box = box.row(align = True)
                        box.prop(obj.modifiers[modifiers[0]], 'use_self', text="Use self")
                        box.prop(obj.modifiers[modifiers[0]], 'use_hole_tolerant', text="Hole Tolerant")

                    box = layout.box()
                    box.label(text="Boolean Target")
                    box = box.column(align = True)
                    box.prop(obj.modifiers[modifiers[1]], 'segments', text="Bevel Segments")
                    box.prop(obj.modifiers[modifiers[1]], 'width', text="Bevel Size")

                    bool_obj = bpy.data.objects[modifiers[5]]

                    box = layout.box()
                    box.label(text="Boolean Object")
                    box = box.column(align = True)
                    box.prop(bool_obj.modifiers[modifiers[3]], 'segments', text="Bevel Segments")
                    box.prop(bool_obj.modifiers[modifiers[3]], 'width', text="Bevel Size")
                    box.prop(bool_obj.modifiers[modifiers[6]], 'strength', text="Displace")

                    box = box.column(align = False)
                    col = box.column()
                    if bool_obj.modifiers[modifiers[4]].show_render == False:
                        box.operator("solidify.visibility", text= "Use Solidify")
                    else:
                        box.operator("solidify.visibility", text= "Disable Solidify")
                    box = box.column(align = True)  
                    box.prop(bool_obj.modifiers[modifiers[4]], 'thickness', text="Solidify")
                    box.prop(bool_obj.modifiers[modifiers[4]], 'offset', text="Solidify Offset")
                    box = box.row(align = True)
                    box.label(text="Mirror XYZ")
                    box.prop(bool_obj.modifiers[modifiers[2]], 'use_axis', text="")
                    
                    col = layout.column()
                    col.scale_y = 2.0
                    active_ob = bpy.context.active_object
                    if bpy.context.object.mode == 'OBJECT' and active_ob == obj:
                        col.operator("bool.mode", text= "More Boolean !")
                    elif bpy.context.object.mode == 'EDIT' and active_ob == obj:
                        col.operator("bool.mode", text= "EXIT")
                
                elif type == "ivy":
                    col.label(text="Modifier Properties :")
                    ivy_modifier = obj.modifiers[modifiers[0]]
                    box = layout.box()
                    box = box.column(align=True)
                    box.scale_y = 1.5
                    box.operator("bagapie.addvertcursor", text="Add Ivy to 3D Cursor")
                    row=box.row(align=True)
                    row.operator("bagapie.addobjecttarget", text="Target", icon = 'ADD')
                    row.operator("bagapie.removeobjecttarget", text="Target", icon = 'REMOVE')
                    box = layout.box()

                    box.label(text="Ivy")
                    box = box.column(align=True)
                    box.prop(ivy_modifier, '["Input_3"]', text = "Radius")
                    box.prop(ivy_modifier, '["Input_5"]', text = "Height")
                    box.prop(ivy_modifier, '["Input_6"]', text = "Loop")
                    box.prop(ivy_modifier, '["Input_2"]', text = "Resolution")

                    box = layout.box()
                    box = box.column(align=True)
                    box.prop(ivy_modifier, '["Input_13"]', text = "Distance Min")
                    box.prop(ivy_modifier, '["Input_10"]', text = "Density")

                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.prop(ivy_modifier, '["Input_7"]', text = "Random Position")
                    box.prop(ivy_modifier, '["Input_14"]', text = "Emission Area")
                    box.prop(ivy_modifier, '["Input_11"]', text = "Surface Offset")
                    box.prop(ivy_modifier, '["Input_8"]', text = "Scale")
                    box.label(text="Ivy Random Position")
                    box = box.row(align=True)
                    box.prop(ivy_modifier, '["Input_12"]', text = "")
                    
                    box = layout.box()
                    box.label(text="Source info", icon = "INFO")
                    box.prop(ivy_modifier, '["Input_9"]', text = "Target")
                    box.prop(ivy_modifier, '["Input_16"]', text = "Ivy Asset")
                    box.prop(ivy_modifier, '["Input_17"]', text = "Ivy Emitter")

                elif type == "pointsnapinstance":
                    col.label(text="Modifier Properties :")
                    psi_modifier = obj.modifiers[modifiers[0]]
                    col = layout.column(align=True)
                    col.scale_y=2
                    col.operator("bagapie.pointsnapinstance", text= "Add Instances")
                    col = layout.column(align=True)
                    col.label(text="ESC to Stop")

                    col = layout.column(align=True)
                    box = layout.box()
                    box.label(text="Main")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_9"]', text = "Offset Z")
                    box.prop(psi_modifier, '["Input_8"]', text = "Align Normal")
                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_5"]', text = "Random Rotation")
                    box.prop(psi_modifier, '["Input_6"]', text = "Scale Min")
                    box.prop(psi_modifier, '["Input_7"]', text = "Scale Max")
                    
                    box = layout.box()
                    box.label(text="Source info", icon = "INFO")
                    box.prop(psi_modifier, '["Input_3"]', text = "Target")
                    box.prop(psi_modifier, '["Input_4"]', text = "Instances")

                elif type == "grass":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Grass Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                            elif node.name == modifiers[1]:
                                shader_node = node
                            elif node.name == modifiers[2]:
                                shader_node = node

                        if shader_node.name.startswith('BagaPie_Moss'):
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[0], 'default_value', text = "Saturation")

                        elif shader_node.name.startswith('BagaPie_LP_Plant'):
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[2], 'default_value', text = "AO Distance")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[3], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[4], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[7], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[8], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Random Saturation")

                        else:
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Saison")
                            if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                box.label(text="Season value up to 0.9", icon = 'ERROR')
                                box.label(text="This value add transparency.")
                                box.label(text="May increase render time !")
                                box.label(text="Decrease Season or Random Season")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
              
                elif type == "plant":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Plant Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        disp = False
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[1]:
                                shader_node = node
                            elif node.name == modifiers[2]:
                                shader_node = node

                        if shader_node.name == "BagaPie_LP_Plant":
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "Color")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[2], 'default_value', text = "AO Distance")
                            if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                if bpy.context.scene.eevee.use_gtao == False:
                                    box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                            box.separator(factor = 1)
                            box.prop(shader_node.inputs[3], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[4], 'default_value', text = "")
                            box.separator(factor = 1)
                            box.prop(shader_node.inputs[6], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[7], 'default_value', text = "")
                            box.separator(factor = 1)                            
                            box.prop(shader_node.inputs[8], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Random Saturation")

                        elif shader_node.name.startswith("BagaPie_LP_Tree_Leaf"):
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[2], 'default_value', text = "Subsurface")
                            box.prop(shader_node.inputs[3], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[4], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[6], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[8], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Random Saturation")

                        
                        elif shader_node.name.startswith("BagaPie_V2"):
                            if "Desert" in shader_node.name:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    idx_input = 4
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 5
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 7
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 8
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 9
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 10
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 11
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 12
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                            elif "Bark" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                box = box.column(align=True)
                                idx_input = 4
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 5
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 11
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 12
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 9
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 10
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                            else: 
                                box = layout.box()
                                box.label(text="Material " + str(index))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                    box.label(text="Season value up to 0.9", icon = 'ERROR')
                                    box.label(text="This value add transparency.")
                                    box.label(text="May increase render time !")
                                    box.label(text="Decrease Season or Random Season")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                                box.prop(shader_node.inputs[12], 'default_value', text = "Alpha")

                        elif disp is True:
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                            if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                box.label(text="Season value up to 0.9", icon = 'ERROR')
                                box.label(text="This value add transparency.")
                                box.label(text="May increase render time !")
                                box.label(text="Decrease Season or Random Season")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                    
                elif type == "rock":
                    material_slots = obj.material_slots
                    col.label(text="Rock Shader :")
                    
                    for m in material_slots:
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                        
                        if shader_node.name.startswith("BagaPie_V2"):
                            if "Rock" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                inp = shader_node.inputs

                                idx_input = [13,14,15,16]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[17], 'default_value', text = "Tint")
                                box.prop(shader_node.inputs[18], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                idx_input = [4,5]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.label(text="Bump")
                                box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                                box.prop(shader_node.inputs[7], 'default_value', text = "Intensity")
                                box.label(text="Ambient Occlusion")
                                box.prop(shader_node.inputs[6], 'default_value', text = "AO (Map)")
                                if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                    if bpy.context.scene.eevee.use_gtao == False:
                                        box.label(text="AO disabled")
                                        box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                                box.prop(shader_node.inputs[10], 'default_value', text = "AO Distance")
                                box.prop(shader_node.inputs[11], 'default_value', text = "AO Intensity")
                        elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "AO")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                            box.prop(shader_node.inputs[8], 'default_value', text = "AO Tint")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[3], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")
                        else:
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Saturation")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Brightness")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[6], 'default_value', text = "Tint")
                            box.prop(shader_node.inputs[5], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[8], 'default_value', text = "Roughness")

                            box.label(text="Bump")
                            box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                            box.prop(shader_node.inputs[13], 'default_value', text = "Intensity")
                            box.label(text="Ambient Occlusion")
                            if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                if bpy.context.scene.eevee.use_gtao == False:
                                    box.label(text="AO disabled")
                                    box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                            box.prop(shader_node.inputs[14], 'default_value', text = "Intensity")
                            box.prop(shader_node.inputs[15], 'default_value', text = "Distance")
                    
                elif type == "tree":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Tree Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        disp = False
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[1] and modifiers[1] != "":
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[2] and modifiers[2] != "":
                                shader_node = node
                                disp = True
                        
                        # disp = DISPLAY !
                        if disp is True:
                            if shader_node.name.startswith("BagaPie_LP_Tree_Leaf"):
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                                box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[2], 'default_value', text = "Subsurface")
                                box.prop(shader_node.inputs[3], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[4], 'default_value', text = "Tint Intensity")
                                box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                                box.prop(shader_node.inputs[6], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[8], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[9], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Random Saturation")

                            elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                                box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                                box.prop(shader_node.inputs[3], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")

                            elif shader_node.name.startswith("BagaPie_V2"):
                                if "Bark" in shader_node.label:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    idx_input = 4
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 5
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 11
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 12
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                else:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                    box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                    box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                    box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                    box.separator(factor = 0.5)
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                    box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                    if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                        box.label(text="Season value up to 0.9", icon = 'ERROR')
                                        box.label(text="This value add transparency.")
                                        box.label(text="May increase render time !")
                                        box.label(text="Decrease Season or Random Season")
                                    box.separator(factor = 0.5)
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                    box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                    box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                                    box.prop(shader_node.inputs[12], 'default_value', text = "Disable Alpha")

                            else:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                    box.label(text="Season value up to 0.9", icon = 'ERROR')
                                    box.label(text="This value add transparency.")
                                    box.label(text="May increase render time !")
                                    box.label(text="Decrease Season or Random Season")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                   
                elif type == "stump":
                    material_slots = obj.material_slots
                    for m in material_slots:
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                        
                        if shader_node.name.startswith("BagaPie_V2"):
                            if "Wood" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                inp = shader_node.inputs

                                idx_input = [10,11,12,13]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[14], 'default_value', text = "Tint")
                                box.prop(shader_node.inputs[15], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                idx_input = [4,5]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.label(text="Bump")
                                box.prop(shader_node.inputs[7], 'default_value', text = "Threshold")
                                box.prop(shader_node.inputs[8], 'default_value', text = "Intensity")
                                box.label(text="Ambient Occlusion")
                                box.prop(shader_node.inputs[6], 'default_value', text = "AO (Map)")
                                if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                    if bpy.context.scene.eevee.use_gtao == False:
                                        box.label(text="AO disabled")
                                        box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                                box.prop(shader_node.inputs[16], 'default_value', text = "AO Intensity")
                                box.prop(shader_node.inputs[17], 'default_value', text = "AO Distance")
                                
                    if shader_node.name.startswith("BagaPie_V2"): 
                        pass
                    elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                        box = layout.box()
                        box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                        box = box.column(align=True)
                        box.prop(shader_node.inputs[0], 'default_value', text = "AO")
                        box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                        box.prop(shader_node.inputs[8], 'default_value', text = "AO Tint")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                        box.prop(shader_node.inputs[3], 'default_value', text = "")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                        box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")
                    else:
                        col.label(text="Stump Shader :")
                        box = layout.box()
                        box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                        box = box.column(align=True)
                        box.prop(shader_node.inputs[1], 'default_value', text = "Saturation")
                        box.prop(shader_node.inputs[2], 'default_value', text = "Random Saturation")
                        box.prop(shader_node.inputs[3], 'default_value', text = "Brightness")
                        box.prop(shader_node.inputs[4], 'default_value', text = "Random Brightness")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[6], 'default_value', text = "Tint")
                        box.prop(shader_node.inputs[5], 'default_value', text = "")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[7], 'default_value', text = "Specular")
                        box.prop(shader_node.inputs[8], 'default_value', text = "Roughness")

                        box.label(text="Bump")
                        box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                        box.prop(shader_node.inputs[13], 'default_value', text = "Intensity")
                        box.label(text="Ambient Occlusion")
                        box.prop(shader_node.inputs[14], 'default_value', text = "Intensity")
                        box.prop(shader_node.inputs[15], 'default_value', text = "Distance")

                elif type == "instancesdisplace":
                    col.label(text="Modifier Properties :")
                    psi_modifier = obj.modifiers[modifiers[0]]

                    col = layout.column(align=True)
                    box = layout.box()
                    box.label(text="Displace Instances")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_3"]', text = "Scale")
                    box.prop(psi_modifier, '["Input_4"]', text = "Noise")
                    box = layout.box()
                    box.label(text="Orientation")
                    row = box.row(align=True)
                    row.prop(psi_modifier, '["Input_2"]', text = "")
                    box.label(text="Position")
                    row = box.row(align=True)
                    row.prop(psi_modifier, '["Input_5"]', text = "")

                else:
                    col = layout.column()
                    col.scale_y = 1.5
                    col.label(text="Press J !")
                    col.operator("wm.url_open", text="Youtube Tutorial", icon = 'PLAY').url = "https://www.youtube.com/watch?v=51iRC0A4Nzw&list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu&index=3"
                    col.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
                    col.operator("wm.url_open", text="Get BagaPie Assets !", icon = 'FUND').url = "https://blendermarket.com/products/bagapie-assets"

            elif prop is not None and obj is not None:
                
                box = layout.box()

                box.label(text="Duplicate : Alt + J")
                box.label(text="Duplicate Linked : Alt + N")

                col = layout.column()
                col.scale_y = 1.2

                col.operator("bagapie.deletegroup", text= "Delete Group")
                if obj["bagapie_child"][0].hide_select == True:
                    col.operator("bagapie.editgroup")
                else:
                    col.operator("bagapie.lockgroup")
                col.operator("bagapie.ungroup", text= "Ungroup")
                col.operator("bagapie.instance", text= "Instance")


            else:
                if bpy.context.object.mode == 'EDIT':
                    col = layout.column()
                    col.scale_y = 2.0
                    col.operator("bool.mode", text= "EXIT")
                else:
                    col = layout.column()
                    col.scale_y = 1.5
                    col.label(text="Press J !")
                    col.operator("wm.url_open", text="Youtube Tutorial", icon = 'PLAY').url = "https://www.youtube.com/watch?v=51iRC0A4Nzw&list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu&index=3"
                    col.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
                    col.operator("wm.url_open", text="Get BagaPie Assets !", icon = 'FUND').url = "https://blendermarket.com/products/bagapie-assets"

        # In case nothing is selected
        elif obj and obj.type not in obj_allowed_types:
            box = layout.box()
            box = box.column(align=True)
            box.label(text="This object is not supported")
            box.label(text="Mesh or Curve Only")

        else:
            box = layout.box()
            box = box.column(align=True)
            row = box.row()
            row.label(text="No Object Selected")


class BAGAPIE_OP_modifierDisplay(Operator):
    """Hide modifier in viewport"""
    bl_idname = "hide.viewport"
    bl_label = "Hide Viewport"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        mo_type = val['name']
        avoid_string = "BagaPie_Texture"

        if mo_type == "scatter":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            scatter_node = scatt_nde_group.nodes[modifiers[1]]
            scatter_node_input_value = scatter_node.inputs[22].default_value

            if scatter_node_input_value == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[22].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[22].default_value = True

        elif mo_type == "pointeffector":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_op = scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value

            if scatt_nde_visibility_op == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value = True

        elif mo_type == "camera":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_op = scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value

            if scatt_nde_visibility_op == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value = True

        elif mo_type == "boolean":
            if obj.modifiers[modifiers[0]].show_viewport == True:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_viewport = False
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode == True and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = False
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = False

            else:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_viewport = True
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode == True and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = True
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = True

        elif mo_type == "window":

            if modifiers[6] == "win":
                wall = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_viewport == True:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_viewport = False
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_viewport = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_viewport = True
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_viewport = True

            elif modifiers[6] == "wall":
                window = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_viewport == True:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_viewport = False
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_viewport = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_viewport = True
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_viewport = True

        elif mo_type == "wallbrick":
            if obj.type=='MESH':
                mo = modifiers[0]
                if obj.modifiers[modifiers[0]].show_viewport == True:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True
            else:
                mo = modifiers[1]
                if obj.modifiers[modifiers[1]].show_viewport == True:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True

        elif mo_type == "ivy":
            if obj.modifiers[modifiers[0]].show_viewport == True:
                mo = modifiers[0]
                obj.modifiers[mo].show_viewport = False
            else:
                mo = modifiers[0]
                obj.modifiers[mo].show_viewport = True

        else:
            if obj.modifiers[modifiers[0]].show_viewport == True:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
            else:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True

        return {'FINISHED'}


class BAGAPIE_OP_modifierDisplayRender(Operator):
    """Hide modifier in render"""
    bl_idname = "hide.render"
    bl_label = "Hide Render"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        mo_type = val['name']
        avoid_string = "BagaPie_Texture"

        if mo_type == "scatter":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            scatter_node = scatt_nde_group.nodes[modifiers[1]]
            scatter_node_input_value = scatter_node.inputs[23].default_value

            if scatter_node_input_value == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[23].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[23].default_value = True

        elif mo_type == "pointeffector":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_bool = scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value

            if scatt_nde_visibility_bool == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value = True

        elif mo_type == "camera":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_bool = scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value

            if scatt_nde_visibility_bool == True:
                scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value = True

        elif mo_type == "boolean":
            if obj.modifiers[modifiers[0]].show_render == True:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_render = False
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode == True and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = False
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = False

            else:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_render = True
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode == True and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = True
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = True

        elif mo_type == "window":

            if modifiers[6] == "win":
                wall = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_render == True:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_render = False
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_render = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_render = True
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_render = True

            elif modifiers[6] == "wall":
                window = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_render == True:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_render = False
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_render = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_render = True
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_render = True

        elif mo_type == "wallbrick":
            if obj.type=='MESH':
                mo = modifiers[0]
                if obj.modifiers[modifiers[0]].show_render == True:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True
            else:
                mo = modifiers[1]
                if obj.modifiers[modifiers[1]].show_render == True:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True

        else:
            if obj.modifiers[modifiers[0]].show_render == True:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
            else:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True

        return {'FINISHED'}


class BAGAPIE_OP_modifierApply(Operator):
    """Apply all related modifier"""
    bl_idname = "apply.modifier"
    bl_label = "apply.modifier"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        obj = context.object
        obj.select_set(True)
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        avoid_string = "BagaPie_Texture"
        mo_type = val['name']

        if mo_type == "window":
            obj.data = obj.data.copy()
        
        for mo in modifiers:
            if mo.startswith("Baga") and mo.startswith(avoid_string) == False:

                if mo_type == 'wallbrick':
                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'array':
                    mo_name = obj.modifiers[mo].node_group.name

                    if "Line" in mo_name:
                        obj.modifiers[mo]["Input_10"] = 1
                    elif "Grid" in mo_name:
                        obj.modifiers[mo]["Input_14"] = 1
                    elif "Circle" in mo_name:
                        obj.modifiers[mo]["Input_21"] = 1
                    elif "Curve" in mo_name:
                        obj.modifiers[mo]["Input_13"] = 1

                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'pipes':
                    mo_name = obj.modifiers[mo].node_group.name
                
                    obj.modifiers[mo]["Input_27"] = 1

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]
                    coll = modifier["Input_13"]

                    bpy.ops.object.convert(target='MESH')
                    RemoveOBJandDeleteColl(self,context, coll)

                elif mo_type == 'cable':
                    mo_name = obj.modifiers[mo].node_group.name

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]
                    coll = modifier["Input_28"]

                    bpy.ops.object.convert(target='MESH')
                    RemoveOBJandDeleteColl(self,context, coll)

                elif mo_type == 'fence':
                    mo_name = obj.modifiers[mo].node_group.name

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]

                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'handrail':
                    
                    bpy.ops.object.convert(target='MESH')
                    
                elif mo_type == 'beamwire':
                    mo_name = obj.modifiers[mo].node_group.name
                
                    obj.modifiers[mo]["Input_12"] = 1
                    obj.modifiers[mo].show_viewport = False # Just a way to update model
                    obj.modifiers[mo].show_viewport = True

                    bpy.ops.object.modifier_apply(modifier=mo)

                elif mo_type == 'scatter':
                    
                    bpy.ops.use.applyscatter('INVOKE_DEFAULT')

                    return {'FINISHED'}
                
                elif mo_type == "window":
                    
                    if modifiers[6] == "win":
                        if mo =="BagaWindow_Displace":
                            if obj.modifiers[mo].strength == 0.0:
                                obj.modifiers[mo].strength = 0.001

                    elif modifiers[6] == "wall":
                        win = bpy.data.objects[modifiers[7]]
                        if mo =="BagaWindow_Displace":
                            if win.modifiers[mo].strength == 0.0:
                                win.modifiers[mo].strength = 0.001

                elif mo_type == "boolean":
                    if mo =="BagaBevel":
                        if obj.modifiers[mo].width == 0.0:
                            bpy.ops.object.modifier_remove(modifier=mo)
                    elif mo =="BagaBool":
                        bpy.ops.object.modifier_apply(modifier=mo)
                
                else:
                    try:
                        bpy.ops.object.modifier_apply(modifier=mo)
                    except:
                        bpy.ops.object.modifier_remove(modifier=mo)

        if mo_type == "boolean":
            bool_obj = bpy.data.objects[modifiers[5]]
            bpy.data.objects.remove(bool_obj)

        elif mo_type == "window":
            for mod in modifiers:
                print(mod)

            if modifiers[6] == "win":############################################
                win_bool = bpy.data.objects[modifiers[4]]
                win = obj
                wall = bpy.data.objects[modifiers[7]]

                # applique le modifier sur le mur
                bpy.context.view_layer.objects.active = wall
                try:
                    bpy.ops.object.modifier_apply(modifier=modifiers[5])
                except:
                    bpy.ops.object.modifier_remove(modifier=modifiers[5])

                # delete boolean
                bpy.data.objects.remove(win_bool)

                # applique le modifier de la vitre
                bpy.context.view_layer.objects.active = win
                for mo in win.modifiers:
                    m = mo.name
                    if m.startswith("BagaWindow") and not m.startswith("BagaWindow_Bool"):
                        try:
                            bpy.ops.object.modifier_apply(modifier=m)
                        except:
                            bpy.ops.object.modifier_remove(modifier=m)

                # relève le modifier de la liste
                index = 0
                for i in range(len(wall.bagapieList)):
                    index = index + i
                    val = json.loads(wall.bagapieList[index]['val'])
                    modifiers = val['modifiers']
                    mo_type = val['name']
                    if mo_type == "window":
                        wall.bagapieList.remove(index)
                        index -=1
                        # wall.bagapieIndex = wall.bagapieIndex -1
                bpy.context.view_layer.objects.active = obj




            elif modifiers[6] == "wall":############################################
                win_bool = bpy.data.objects[modifiers[5]]
                win = bpy.data.objects[modifiers[7]]
                wall = obj


                # applique le modifier sur le mur
                bpy.context.view_layer.objects.active = wall
                try:
                    bpy.ops.object.modifier_apply(modifier=modifiers[0])
                except:
                    bpy.ops.object.modifier_remove(modifier=modifiers[0])

                # delete boolean
                bpy.data.objects.remove(win_bool)

                # applique le modifier de la vitre
                bpy.context.view_layer.objects.active = win
                for mo in win.modifiers:
                    m = mo.name
                    if m.startswith("BagaWindow") and not m.startswith("BagaWindow_Bool"):
                        try:
                            bpy.ops.object.modifier_apply(modifier=m)
                        except:
                            bpy.ops.object.modifier_remove(modifier=m)

                # relève le modifier de la liste
                index = 0
                for i in range(len(win.bagapieList)):
                    index = index + i
                    val = json.loads(win.bagapieList[index]['val'])
                    modifiers = val['modifiers']
                    mo_type = val['name']
                    if mo_type == "window":
                        win.bagapieList.remove(index)
                        index -=1
                        # obj.bagapieIndex = obj.bagapieIndex -1
                bpy.context.view_layer.objects.active = obj


        obj.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OP_addparttype(Operator):
    """WIP"""
    bl_idname = "switch.glass"
    bl_label = "switch.glass"

    index: IntProperty(
        name="G",
        description="Import or link",
        default = 1
        )

    part_type: StringProperty(
        name="G",
        description="Import or link",
        default = "GLASS"
        )

    current_state: BoolProperty(
        name="M",
        description="World or Cursor",
        default = False
        )  

    def execute(self, context):
        
        obj = context.object
        glass_statut = obj['line_bool_g']
        stat =glass_statut[self.index]

        if stat == 1:
            glass_statut[self.index] = 0
        else:
            glass_statut[self.index] = 1


        return {'FINISHED'}


###################################################################################
# UI SWITCH BUTON
###################################################################################

class BAGAPIE_OP_switchinput(Operator):
    """Switch GN input"""
    bl_idname = "switch.button"
    bl_label = "switch.button"

    index: bpy.props.StringProperty(name="None")

    def execute(self, context):

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = obj.modifiers[modifiers[0]]
        if modifier[self.index] == 1:
            modifier[self.index] = 0
        else:
            modifier[self.index] = 1
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}

###################################################################################
# UI SWITCH BOOL NODE
###################################################################################

class BAGAPIE_OP_switchboolnode(Operator):
    """Switch Node Bool input"""
    bl_idname = "switch.boolnode"
    bl_label = "switch.boolnode"

    index: bpy.props.IntProperty(name="None")

    def execute(self, context):

        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = obj.modifiers[modifiers[0]]

        scatter_node = modifier.node_group.nodes.get(modifiers[1])
        if scatter_node.inputs[self.index].default_value == 1:
            scatter_node.inputs[self.index].default_value = 0
        else:
            scatter_node.inputs[self.index].default_value = 1
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}

###################################################################################
# DISPLAY TOOLTIPS
###################################################################################
class BagaPie_tooltips(Operator):
    """Display a tooltips"""
    bl_idname = "bagapie.tooltips"
    bl_label = "Tips"

    message: bpy.props.StringProperty(default="None")
    title: bpy.props.StringProperty(default="Tooltip")
    icon: bpy.props.StringProperty(default="INFO")

    def execute(self, context):
        Warning(self.message, self.title, self.icon) 
        return {'FINISHED'}


def Warning(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def RemoveOBJandDeleteColl(self, context, collection):

    for obj in collection.all_objects:
        collection.objects.unlink(obj)

    bpy.data.collections.remove(collection)