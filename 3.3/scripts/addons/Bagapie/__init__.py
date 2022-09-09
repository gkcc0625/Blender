# Blender Adoon BagaPie Modifier
# Created by Antoine Bagattini

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


# _______________________________________________ HELLO !

# This addon is free, you can use it for any purpose, modify it and share it.

# Special thanks to Franck Demongin and Clovis Flayols which greatly contributed to this addon.

# Also thanks to all the people who support the development of this addon.
# Thanks to Sybren A. Stüvel (Scripting for artist on Blender Cloud), this addon exist because of him.

# I'm not a programmer, just Python hobbyist. Some part of this code suck but it works well.
# If you have any idea/advice to improve this addon, do not hesitate to contact me !

# _______________________________________________ USER INTERFACE / OP PANEL AND N PANEL

bl_info = {
    "name": "BagaPie Modifier",
    "author": "Antoine Bagattini",
    "version": (0, 7, 2, 1),
    "description": "Use a pie menu to add modifier and Geometry Nodes preset.",
    "blender": (3, 2, 0),
    "cathegory": "3D view",
    "location": "Pie Menue, shortcut : J"
}

from re import T
import bpy
import bpy.utils.previews
import os
import addon_utils
from bl_keymap_utils.io import keyconfig_merge
from bpy.types import Menu, Operator, Panel

from . bagapie_ui import (
    BAGAPIE_MT_pie_menu,
    BAGAPIE_PT_modifier_panel, 
    MY_UL_List,
    BAGAPIE_OP_modifierDisplay,
    BAGAPIE_OP_modifierDisplayRender,
    BAGAPIE_OP_modifierApply,
    BAGAPIE_OP_addparttype,
    BAGAPIE_OP_switchinput,
    BAGAPIE_OP_switchboolnode,
    BagaPie_tooltips,
)
from . bagapie_ui_op import ( 
    SwitchMode,
    EditMode,
    UseSolidify,
    InvertPaint,
    CleanWPaint,
    InvertWeight,
    ADD_Assets,
    REMOVE_Assets,
    Rename_Layer,
    SetupAssetBrowser,
    SetupAssetBrowserForAssets,
)
from . bagapie_boolean_op import BAGAPIE_OT_boolean, BAGAPIE_OT_boolean_remove
from . bagapie_wall_op import BAGAPIE_OT_wall_remove, BAGAPIE_OT_wall
from . bagapie_array_op import BAGAPIE_OT_array_remove, BAGAPIE_OT_array, BAGAPIE_OT_drawarray
from . bagapie_scatter_op import BAGAPIE_OT_scatter_remove, BAGAPIE_OT_scatter, UseProperty, Use_Proxy_On_Assets, Use_Camera_Culling_On_Layer, Apply_Scatter_OP
from . bagapie_scatterpaint_op import BAGAPIE_OT_scatterpaint_remove, BAGAPIE_OT_scatterpaint
from . bagapie_displace_op import BAGAPIE_OT_displace_remove, BAGAPIE_OT_displace
from . bagapie_curvearray_op import BAGAPIE_OT_curvearray_remove, BAGAPIE_OT_curvearray
from . bagapie_window_op import BAGAPIE_OT_window_remove, BAGAPIE_OT_window
from . bagapie_group_op import BAGAPIE_OT_ungroup, BAGAPIE_OT_group, BAGAPIE_OT_editgroup, BAGAPIE_OT_lockgroup, BAGAPIE_OT_duplicategroup, BAGAPIE_OT_duplicatelinkedgroup, BAGAPIE_OT_deletegroup
from . bagapie_instance_op import BAGAPIE_OT_makereal, BAGAPIE_OT_instance
from . bagapie_pointeffector_op import BAGAPIE_OT_pointeffector_remove, BAGAPIE_OT_pointeffector
from . bagapie_import_op import BAGAPIE_OT_importnodes
from . bagapie_proxy_op import BAGAPIE_OT_proxy, BAGAPIE_OT_proxy_remove
from . bagapie_wallbrick_op import BAGAPIE_OT_wallbrick, BAGAPIE_OT_wallbrick_remove
from . bagapie_ivy_op import BAGAPIE_OT_ivy, BAGAPIE_OT_ivy_remove, BAGAPIE_OT_AddVertOBJ, BAGAPIE_OT_AddObjectTarget, BAGAPIE_OT_RemoveObjectTarget
from . bagapie_pointsnapinstance import BAGAPIE_OT_pointsnapinstance, BAGAPIE_OT_pointsnapinstance_remove
from . bagapie_instancesdisplace_op import BAGAPIE_OT_instancesdisplace, BAGAPIE_OT_instancesdisplace_remove
from . bagapie_saveasset_op import BAGAPIE_OT_saveasset, BAGAPIE_OT_saveasset_list, BAGAPIE_OT_savematerial, UseLibrary
from . bagapie_pipes_op import BAGAPIE_OT_pipes, BAGAPIE_OT_pipes_remove
from . bagapie_beamwire_op import BAGAPIE_OT_beamwire, BAGAPIE_OT_beamwire_remove
from . bagapie_stairlinear_op import BAGAPIE_OT_stairlinear,BAGAPIE_OT_stairlinear_remove
from . bagapie_stairspiral_op import BAGAPIE_OT_stairspiral, BAGAPIE_OT_stairspiral_remove
from . bagapie_beam_op import BAGAPIE_OT_beam, BAGAPIE_OT_beam_remove
from . bagapie_floor_op import BAGAPIE_OT_floor, BAGAPIE_OT_floor_remove
from . bagapie_handrail_op import BAGAPIE_OT_handrail, BAGAPIE_OT_handrail_remove
from . bagapie_column_op import BAGAPIE_OT_column, BAGAPIE_OT_column_remove
from . bagapie_twist_op import BAGAPIE_OT_deform, BAGAPIE_OT_deform_remove
from . bagapie_camera_op import BAGAPIE_OT_camera, BAGAPIE_OT_camera_remove
from . bagapie_cable_op import BAGAPIE_OT_cable, BAGAPIE_OT_cable_remove
from . bagapie_fence_op import BAGAPIE_OT_fence, BAGAPIE_OT_fence_remove
from . bagapie_siding_op import BAGAPIE_OT_siding, BAGAPIE_OT_siding_remove
from . bagapie_tiles_op import BAGAPIE_OT_tiles, BAGAPIE_OT_tiles_remove

# _______________________________________________ REGISTER / UNREGISTER

class BagapieSettings(bpy.types.PropertyGroup):
    val: bpy.props.StringProperty()

class bagapie_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    general_preferences: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    scatter_preferences: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    asset_browser: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    pie_custom: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    how_it_works: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    
    security_features: bpy.props.BoolProperty(name="Security Features", default=True)
    use_default_proxy: bpy.props.BoolProperty(name="Use Default Proxy", default=True)
    apply_scale_default: bpy.props.BoolProperty(name="Apply Scale Default", default=True)
    use_camera_culling: bpy.props.BoolProperty(name="Apply Scale Default", default=True)
    maximum_polycount: bpy.props.IntProperty(name="Maximum Polycount", default=10000000, min = 0)
    polycount_for_proxy: bpy.props.IntProperty(name="Minimum Polycount", default=100000, min = 0)
    default_percent_display: bpy.props.IntProperty(name="Display percentage", default=100, min = 0, max = 100)

    #ENABLE TOOLS
    displace: bpy.props.BoolProperty(name="displace", default=True)
    instancesdisplace: bpy.props.BoolProperty(name="instancesdisplace", default=True)
    deform: bpy.props.BoolProperty(name="deform", default=True)

    line: bpy.props.BoolProperty(name="line", default=True)
    grid: bpy.props.BoolProperty(name="grid", default=True)
    circle: bpy.props.BoolProperty(name="circle", default=True)
    curve: bpy.props.BoolProperty(name="curve", default=True)

    proxy: bpy.props.BoolProperty(name="proxy", default=True)
    saveasasset: bpy.props.BoolProperty(name="saveasasset", default=True)
    savematerial: bpy.props.BoolProperty(name="savematerial", default=True)
    group: bpy.props.BoolProperty(name="group", default=True)

    scatter: bpy.props.BoolProperty(name="scatter", default=True)
    scatterpaint: bpy.props.BoolProperty(name="scatterpaint", default=True)
    pointsnapinstance: bpy.props.BoolProperty(name="pointsnapinstance", default=True)
    ivy: bpy.props.BoolProperty(name="ivy", default=True)

    union: bpy.props.BoolProperty(name="union", default=True)
    difference: bpy.props.BoolProperty(name="difference", default=True)

    pointeffector: bpy.props.BoolProperty(name="pointeffector", default=True)
    camculling: bpy.props.BoolProperty(name="camculling", default=True)

    wall: bpy.props.BoolProperty(name="wall", default=True)
    wallbrick: bpy.props.BoolProperty(name="wallbrick", default=True)
    window: bpy.props.BoolProperty(name="window", default=True)
    pipes: bpy.props.BoolProperty(name="pipes", default=True)
    beamwire: bpy.props.BoolProperty(name="beamwire", default=True)
    beam: bpy.props.BoolProperty(name="beam", default=True)
    linearstair: bpy.props.BoolProperty(name="linearstair", default=True)
    stairspiral: bpy.props.BoolProperty(name="stairspiral", default=True)
    floor: bpy.props.BoolProperty(name="floor", default=True)
    handrail: bpy.props.BoolProperty(name="handrail", default=True)
    column: bpy.props.BoolProperty(name="column", default=True)
    cable: bpy.props.BoolProperty(name="cable", default=True)
    tiles: bpy.props.BoolProperty(name="tiles", default=True)
    fence: bpy.props.BoolProperty(name="fence", default=True)
    siding: bpy.props.BoolProperty(name="siding", default=True)
    
    autoarrayoncurve: bpy.props.BoolProperty(name="autoarrayoncurve", default=True)


    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        pref = context.preferences.addons['Bagapie'].preferences
        

        # GENERAL PREFERENCES
        box = layout.box()
        box.prop(self, 'general_preferences', text = "Preferences", emboss = False, icon = "PREFERENCES")
        if self.general_preferences == True:
            wm = context.window_manager
            kc_user = wm.keyconfigs.user
            display_keymaps = keyconfig_merge(kc_user, kc_user)
            box.label(text="Shortcut :")
            done_a = True
            done_b = True
            for km, kc in display_keymaps:
                for kmi in km.keymap_items:
                    if kmi.name == 'BagaPie':
                        row = box.row(align=False)
                        row.prop(kmi, "type", text="Pie Menu", full_event=True) 
                    if kmi.name == 'Duplicate Group' and done_a == True:
                        row = box.row(align=False)
                        done_a = False
                        row.prop(kmi, "type", text="Duplicate Group", full_event=True) 
                    if kmi.name == 'Duplicate Linked Group' and done_b == True:
                        row = box.row(align=False)
                        done_b = False
                        row.prop(kmi, "type", text="Duplicate Group Linked", full_event=True) 

        # ASSET BROWSER
        box = layout.box()
        box.prop(self, 'asset_browser', text = "Asset Browser", emboss = False, icon = "ASSET_MANAGER")
        if self.asset_browser == True:
            col = box.column(align=True)
            col.scale_y = 2
            col.operator('bagapie.parametricpresets', icon = "ASSET_MANAGER")
            

            addon_name = 'DevBagaPieAssets'
            success = addon_utils.check(addon_name)
            if success[0]:
                col.scale_y = 2
                col.operator('bagapie.assetsdatabase', icon = "ASSET_MANAGER")

        # SCATTER PREFERENCES
        box = layout.box()
        box.prop(self, 'scatter_preferences', text = "Scattering Preferences", emboss = False, icon = "OUTLINER_OB_CURVES")
        if self.scatter_preferences == True:

            box.label(text="Scatter from BagaPie V5.0 and previous versions aren't compatible with this version.", icon = "INFO")
            box.prop(pref, 'use_default_proxy', text="Enable proxy by default.")
            if pref.use_default_proxy == True:
                box.prop(pref, 'polycount_for_proxy', text="Minimum polycount for proxy.")
                
            box.prop(pref, 'security_features', text="Use security features for scattering :", icon = "LOCKED")
            if pref.security_features == True:
                row = box.row()
                col = row.column()
                col.separator(factor = 2)

                col = row.column()
                col.prop(pref, 'maximum_polycount', text="Maximum polycount to trigger security features.")
                col.label(text="(Total of average polycount instances * instances count)")
                col.separator(factor = 1)
                col.prop(pref, 'default_percent_display', text="Percentage of instances displayed in the viewport")
                col.prop(pref, 'apply_scale_default', text="Proposes to apply the scale of the target if it is not at 1,1,1.")
                col.prop(pref, 'use_camera_culling', text="Use Camera Culling if it's present.")

        # HOW IT WORKS
        box = layout.box()
        box.prop(self, 'how_it_works', text = "How it works ?", emboss = False, icon = "QUESTION")
        if self.how_it_works == True:
            box = box.column(align=True)
            box.label(text="How to use BagaPie Modifier :")
            box.separator(factor = 2)
            box.scale_y = 0.8
            box.label(text="BagaPie is a bundle of nodes tree made with Geometry Nodes and modifier.")
            box.label(text="Depending on the tool you choose, you must select one or more objects (list below).")
            box.separator(factor = 2)
            box.label(text="After selecting your object(s), press J key.")
            box.label(text="You can then choose a modifier in the pie menu (scatter, boolean, displace, ...).")
            box.label(text="Then access the BagaPie panel (aka N panel [N key]) where all the parameters are organized.")
            box.separator(factor = 2)
            box.label(text="What's new in BagaPie Modifier V7 ?")
            box.separator(factor = 1)
            box.label(text="     - Apply Scatter (Convert to mesh or release instances)")
            box.label(text="     - Asset Browser integration (+100 parametric presets)")
            box.label(text="     - Cable Generator")
            box.label(text="     - Tiles Generator")
            box.label(text="     - Siding Generator")
            box.label(text="     - Fence Generator")
            box.label(text="     - Custom Shortcut")
            box.label(text="     - Pie menu customisation")
            box.separator(factor = 2)
            box.label(text="What's new in BagaPie Assets V3 ?")
            box.separator(factor = 1)
            box.label(text="     - 110 new assets")
            box.label(text="     - Asset Browser integration")
            box.label(text="     - New thumbnails with faster loading.")
            box.separator(factor = 2)
            col = box.column(align=True)
            col.scale_y = 2
            col.operator("wm.url_open", text="Youtube Tutorial", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"


        # PIE MENU CUSTOMIZATION
        box = layout.box()
        box.prop(self, 'pie_custom', text = "Pie Menu Customization", emboss = False, icon = "MODIFIER")
        if self.pie_custom == True:
            
            box = box.column(align=True)
            box.scale_y = 1.2
            box.label(text="Enable/Disable tools | What should be selected | Type of the selected object")
            box.separator(factor = 2)

            # DEFORMATION
            box.label(text="Deformation :", icon ='MOD_DISPLACE')
            
            row = box.row(align=True)
            row.prop(self, 'displace', text = "Displace", emboss = self.displace, icon="BLANK1")
            row.label(text=" One object | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'instancesdisplace', text = "Instances Displace", emboss = self.instancesdisplace, icon="BLANK1")
            row.label(text=" One object with instances on it | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'deform', text = "Deform", emboss = self.deform, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            box.separator(factor = 1)

            # ARRAY
            box.label(text="Array :", icon = "MOD_ARRAY")
            
            row = box.row(align=True)
            row.prop(self, 'line', text = "Line", emboss = self.line, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'grid', text = "Grid", emboss = self.grid, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'circle', text = "Circle", emboss = self.circle, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'curve', text = "Curve", emboss = self.curve, icon="BLANK1")
            row.label(text=" Multiple objects & Curve as active object | type mesh and Curve")
            box.separator(factor = 1)

            # MANAGE
            box.label(text="Manage :", icon = "PACKAGE")
            
            row = box.row(align=True)
            row.prop(self, 'proxy', text = "Proxy", emboss = self.proxy, icon="BLANK1")
            row.label(text=" One or multiple object(s) | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'saveasasset', text = "Save as Asset", emboss = self.saveasasset, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'savematerial', text = "Save Material", emboss = self.savematerial, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")
            
            row = box.row(align=True)
            row.prop(self, 'group', text = "Group", emboss = self.group, icon="BLANK1")
            row.label(text=" One or multiple object(s) | type mesh or curve")
            box.separator(factor = 1)

            # SCATTERING
            box.label(text="Scattering :", icon = "OUTLINER_OB_CURVES")
            
            row = box.row(align=True)
            row.prop(self, 'scatter', text = "Scatter", emboss = self.scatter, icon="BLANK1")
            row.label(text=" Multiple object(s) | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'scatterpaint', text = "Scatter Paint", emboss = self.scatterpaint, icon="BLANK1")
            row.label(text=" Multiple object(s) | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'pointsnapinstance', text = "Point Snap Instance", emboss = self.pointsnapinstance, icon="BLANK1")
            row.label(text=" Multiple object(s) | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'ivy', text = "Ivy", emboss = self.ivy, icon="BLANK1")
            row.label(text=" One or multiple object(s) | type mesh")
            box.separator(factor = 1)

            # BOOLEAN
            box.label(text="Boolean :", icon = "MOD_BOOLEAN")
            
            row = box.row(align=True)
            row.prop(self, 'union', text = "Union", emboss = self.union, icon="BLANK1")
            row.label(text=" One object | type mesh")
            
            row = box.row(align=True)
            row.prop(self, 'difference', text = "Difference", emboss = self.difference, icon="BLANK1")
            row.label(text=" One object | type mesh")
            box.separator(factor = 1)

            # EFFECTOR
            box.label(text="Effector :", icon = "PARTICLES")

            row = box.row(align=True)
            row.prop(self, 'pointeffector', text = "Point Effector", emboss = self.pointeffector, icon="BLANK1")
            row.label(text=" One or multiple object(s) and target | type mesh")

            row = box.row(align=True)
            row.prop(self, 'camculling', text = "CamCulling", emboss = self.camculling, icon="BLANK1")
            row.label(text=" Camera and target | type camera or empty")
            box.separator(factor = 1)

            # ARCHITECTURE
            box.label(text="Architecture :", icon = "HOME")

            row = box.row(align=True)
            row.prop(self, 'wall', text = "Wall", emboss = self.wall, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")

            row = box.row(align=True)
            row.prop(self, 'wallbrick', text = "Wall Brick", emboss = self.wallbrick, icon="BLANK1")
            row.label(text=" One object | type mesh or curve")

            row = box.row(align=True)
            row.prop(self, 'window', text = "Window", emboss = self.window, icon="BLANK1")
            row.label(text=" One object | type mesh")

            row = box.row(align=True)
            row.prop(self, 'pipes', text = "Pipes", emboss = self.pipes, icon="BLANK1")
            row.label(text=" One or multiple object(s) | type mesh")

            row = box.row(align=True)
            row.prop(self, 'beamwire', text = "Beam Wire", emboss = self.beamwire, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'beam', text = "Beam", emboss = self.beam, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'linearstair', text = "Stair Linear", emboss = self.linearstair, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'stairspiral', text = "Stair Spiral", emboss = self.stairspiral, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'floor', text = "Floor", emboss = self.floor, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'handrail', text = "Handrail", emboss = self.handrail, icon="BLANK1")
            row.label(text=" One object or Nothing | type curve")

            row = box.row(align=True)
            row.prop(self, 'column', text = "Column", emboss = self.column, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'cable', text = "Cable", emboss = self.cable, icon="BLANK1")
            row.label(text=" One or multiple object(s) | type mesh")

            row = box.row(align=True)
            row.prop(self, 'tiles', text = "Tiles", emboss = self.tiles, icon="BLANK1")
            row.label(text=" Nothing | No selection")

            row = box.row(align=True)
            row.prop(self, 'fence', text = "Fence", emboss = self.fence, icon="BLANK1")
            row.label(text=" One object or Nothing | type curve")

            row = box.row(align=True)
            row.prop(self, 'siding', text = "Siding", emboss = self.siding, icon="BLANK1")
            row.label(text=" One object | type mesh")

            # CURVES
            box.separator(factor = 1)
            box.label(text="Curves :", icon = "MOD_CURVE")

            row = box.row(align=True)
            row.prop(self, 'autoarrayoncurve', text = "Auto Array on Curve", emboss = self.autoarrayoncurve, icon="BLANK1")
            row.label(text="    Auto Array on Curve : Two object | type mesh and curve")


        col = layout.column(align=True)
        col.separator(factor = 2)
        col.scale_y = 1.5
        col.operator("wm.url_open", text="Get BagaPie Assets !", icon = 'FUND').url = "https://blendermarket.com/products/bagapie-assets"
        col.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
        col.operator("wm.url_open", text="Help - Support - Bug Report on Discord", icon = 'COMMUNITY').url = "https://discord.gg/YtagqdPW6G"
        col.operator("wm.url_open", text="Help - Support - Bug Report on BlenderArtists", icon = 'COMMUNITY').url = "https://blenderartists.org/t/bagapie-modifier-free-addon/1310959"
        col.operator("wm.url_open", text="Youtube Tutorial", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"


bpy.utils.register_class(BagapieSettings)

addon_keymaps = []
addon_keymaps_group = []
addon_keymaps_grouplink = []
classes = [
    bagapie_Preferences,
    BAGAPIE_MT_pie_menu,
    BAGAPIE_PT_modifier_panel,
    MY_UL_List,
    BAGAPIE_OP_switchboolnode,
    SwitchMode,
    EditMode,
    UseSolidify,
    InvertPaint,
    CleanWPaint,
    ADD_Assets,
    UseProperty,
    REMOVE_Assets,
    Rename_Layer,
    Use_Camera_Culling_On_Layer,
    Use_Proxy_On_Assets,
    InvertWeight,
    SetupAssetBrowserForAssets,
    BAGAPIE_OT_wall_remove,
    BAGAPIE_OT_array_remove,
    BAGAPIE_OT_scatter_remove,
    BAGAPIE_OT_scatterpaint_remove,
    BAGAPIE_OT_displace_remove,
    BAGAPIE_OT_curvearray_remove,
    BAGAPIE_OT_window_remove,
    BAGAPIE_OT_ungroup,
    BAGAPIE_OT_makereal,
    BAGAPIE_OT_pointeffector_remove,
    BAGAPIE_OT_boolean,
    BAGAPIE_OT_boolean_remove,
    BAGAPIE_OT_wall,
    BAGAPIE_OT_array,
    BAGAPIE_OT_drawarray,
    BAGAPIE_OT_scatter,
    BAGAPIE_OT_scatterpaint,
    Apply_Scatter_OP,
    BAGAPIE_OT_displace,
    BAGAPIE_OT_curvearray,
    BAGAPIE_OT_window,
    BAGAPIE_OP_addparttype,
    BAGAPIE_OT_group,
    BAGAPIE_OT_editgroup,
    BAGAPIE_OT_lockgroup,
    BAGAPIE_OT_duplicategroup,
    BAGAPIE_OT_duplicatelinkedgroup,
    BAGAPIE_OT_deletegroup,
    BAGAPIE_OP_modifierDisplay,
    BAGAPIE_OP_modifierDisplayRender,
    BAGAPIE_OP_modifierApply,
    BAGAPIE_OT_instance,
    BAGAPIE_OT_pointeffector,
    BAGAPIE_OT_importnodes,
    BAGAPIE_OT_proxy_remove,
    BAGAPIE_OT_proxy,
    BAGAPIE_OT_wallbrick,
    BAGAPIE_OT_wallbrick_remove,
    BAGAPIE_OT_ivy,
    BAGAPIE_OT_ivy_remove,
    BAGAPIE_OT_AddObjectTarget,
    BAGAPIE_OT_RemoveObjectTarget,
    BAGAPIE_OT_AddVertOBJ,
    BAGAPIE_OT_pointsnapinstance,
    BAGAPIE_OT_pointsnapinstance_remove,
    BAGAPIE_OT_instancesdisplace,
    BAGAPIE_OT_instancesdisplace_remove,
    BAGAPIE_OT_saveasset,
    BAGAPIE_OT_saveasset_list,
    BAGAPIE_OT_savematerial,
    UseLibrary,
    BAGAPIE_OT_pipes,
    BAGAPIE_OT_pipes_remove,
    BAGAPIE_OP_switchinput,
    BAGAPIE_OT_beamwire,
    BAGAPIE_OT_beamwire_remove,
    BAGAPIE_OT_stairlinear,
    BAGAPIE_OT_stairlinear_remove,
    BAGAPIE_OT_stairspiral,
    BAGAPIE_OT_stairspiral_remove,
    BAGAPIE_OT_beam,
    BAGAPIE_OT_beam_remove,
    BAGAPIE_OT_floor,
    BAGAPIE_OT_floor_remove,
    BAGAPIE_OT_handrail,
    BAGAPIE_OT_handrail_remove,
    BAGAPIE_OT_column,
    BAGAPIE_OT_column_remove,
    BAGAPIE_OT_deform,
    BAGAPIE_OT_deform_remove,
    BAGAPIE_OT_camera,
    BAGAPIE_OT_camera_remove,
    BagaPie_tooltips,
    SetupAssetBrowser,
    BAGAPIE_OT_cable,
    BAGAPIE_OT_cable_remove,
    BAGAPIE_OT_fence,
    BAGAPIE_OT_fence_remove,
    BAGAPIE_OT_siding,
    BAGAPIE_OT_siding_remove,
    BAGAPIE_OT_tiles,
    BAGAPIE_OT_tiles_remove,
    ]
    

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS')
        kmi.properties.name = "BAGAPIE_MT_pie_menu"
        addon_keymaps.append((km,kmi))

        # Group Shortcut
        # Duplicate
        dupli = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        dupli_id = km.keymap_items.new("bagapie.duplicategroup", type='J', alt=True, value='PRESS')
        addon_keymaps_group.append((dupli,dupli_id))
        # Duplicate linked
        dupli_link = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        dupli_id_link = km.keymap_items.new("bagapie.duplicatelinkedgroup", type='N', alt=True, value='PRESS')
        addon_keymaps_grouplink.append((dupli_link,dupli_id_link))

    bpy.types.Scene.bagapieValue = bpy.props.StringProperty(
        name="My List",
        default="none"
    )

    bpy.types.Object.bagapieList = bpy.props.CollectionProperty(type=BagapieSettings)
    bpy.types.Object.bagapieIndex = bpy.props.IntProperty(name="Index", default=0)



def unregister():
    for km,kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    for dupli,dupli_id in addon_keymaps_group:
        dupli.keymap_items.remove(dupli_id)
    for dupli_link,dupli_id_link in addon_keymaps_grouplink:
        dupli_link.keymap_items.remove(dupli_id_link)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
    
        

if __name__ == "__main__":
    register()