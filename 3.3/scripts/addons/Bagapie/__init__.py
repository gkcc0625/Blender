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
    "version": (0, 8, 1, 0),
    "description": "Use a pie menu to add modifier and Geometry Nodes preset.",
    "blender": (3, 2, 0),
    "cathegory": "3D view",
    "location": "Pie Menu > Shortcut : J | Addon panel in 3d view (N key)",
}

from re import T
import bpy
import bpy.utils.previews
import os
import addon_utils
from bl_keymap_utils.io import keyconfig_merge
from bpy.types import Menu, Operator, Panel


class BagapieSettings(bpy.types.PropertyGroup):
    val: bpy.props.StringProperty()

class bagapie_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    general_preferences: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    scatter_preferences: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    asset_browser: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    pie_custom: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    how_it_works: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    nodes_to_addon: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    our_addon: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    help_support: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    issues: bpy.props.BoolProperty(name="Scattering Preferences", default=False)
    
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
        
        ###################################################################################
        # GENERAL PREFERENCES
        ###################################################################################
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

        ###################################################################################
        # ASSET BROWSER
        ###################################################################################
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

        ###################################################################################
        # SCATTER PREFERENCES
        ###################################################################################
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
                col.prop(pref, 'use_camera_culling', text="Use Camera Culling if available.")

        ###################################################################################
        # HOW IT WORKS
        ###################################################################################
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
            box.label(text="What's new in BagaPie Modifier V8 ?")
            box.separator(factor = 1)
            box.label(text="     - Ivy Generator Rewrite (Gravity, projection mode, collision, ...")
            box.label(text="     - Apply Ivy")
            box.label(text="     - Geometry Nodes Modifier to Panel")
            box.label(text="     - Shader Node Group to Panel")
            box.label(text="     - Pref Improvment")
            box.separator(factor = 2)
            box.label(text="What's new in BagaPie Assets V4 ?")
            box.separator(factor = 1)
            box.label(text="     - +70 new assets")
            box.label(text="     - The names of the plant species are correctly referenced.")
            box.label(text="     - Scatter5 partenarship")
            box.label(text="     - Fixed thumbnail display")
            box.separator(factor = 2)
            col = box.column(align=True)
            col.scale_y = 2
            col.operator("wm.url_open", text="Youtube Tutorial", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"

        ###################################################################################
        # PIE MENU CUSTOMIZATION
        ###################################################################################
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
            
            # row = box.row(align=True)
            # row.prop(self, 'line', text = "Line", emboss = self.line, icon="BLANK1")
            # row.label(text=" One object | type mesh or curve")
            
            # row = box.row(align=True)
            # row.prop(self, 'grid', text = "Grid", emboss = self.grid, icon="BLANK1")
            # row.label(text=" One object | type mesh or curve")
            
            # row = box.row(align=True)
            # row.prop(self, 'circle', text = "Circle", emboss = self.circle, icon="BLANK1")
            # row.label(text=" One object | type mesh or curve")
            
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

            # # BOOLEAN
            # box.label(text="Boolean :", icon = "MOD_BOOLEAN")
            
            # row = box.row(align=True)
            # row.prop(self, 'union', text = "Union", emboss = self.union, icon="BLANK1")
            # row.label(text=" One object | type mesh")
            
            # row = box.row(align=True)
            # row.prop(self, 'difference', text = "Difference", emboss = self.difference, icon="BLANK1")
            # row.label(text=" One object | type mesh")
            # box.separator(factor = 1)

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

        ###################################################################################
        # NODES TO PANEL
        ###################################################################################
        box = layout.box()
        box.prop(self, 'nodes_to_addon', text = "Nodes to Panel", emboss = False, icon = "NODETREE")
        if self.nodes_to_addon == True:
            box.label(text="BagaPie can tranlate your geometry nodes modifier and shader nodes group into a nice user-freindly interface.")
            row = box.row(align=True)
            row.scale_y = 1.5
            row.operator("wm.url_open", text="Documentation", icon = 'HELP').url = "https://www.f12studio.fr/bagapiev6"
            row.operator("wm.url_open", text="Node To Panel Quick Demo", icon = 'PLAY').url = "https://youtu.be/LWdByXpfTLY?t=20"
            col = box.column()
            col.scale_y = 0.7
            col.label(text="This feature allows you to easily organize your Geometry Nodes Modifier.")
            col.label(text="It also allows you to share complex node tree (lot of inputs), users just need to have BagaPie Modifier.")
            box = box.column(align=True)
            box.separator(factor = 2)
            box.scale_y = 0.8
            box.label(text="Prefix list :")
            box.separator(factor = 1)
            box.label(text="B_   >    Create a new box")
            box.label(text="B    >    Add in the previous box")
            box.label(text="R_   >    Create a new row")
            box.label(text="R    >    Add in the previous row")
            box.label(text="2_   >    Scale button/input")

            box.separator(factor = 2)
            box.label(text="L    >    Displayed as Label")
            box.label(text="V    >    Displayed as Value (any types)")
            box.label(text="P    >    Displayed as a Button (must be a bool)")
            box.label(text="P2   >    Displayed as a Button with identifier 2 (must be between 0 - 9). Can control other values display.")
            box.label(text="S    >    Displayed as Separator")
            box.label(text="_    >    End of prefix, then add the name of your Value/Label/Button")
            box.label(text="URL  >    External link (for Tutorials, Documentation, ...")

            
            box.separator(factor = 4)
            box.label(text="Exemples :")

            box.separator(factor = 2)
            box.label(text="New Box with label :")
            box.label(text="B_L_MyLabelName")

            box.separator(factor = 2)
            box.label(text="Button :")
            box.label(text="P_MyButtonName")

            box.separator(factor = 2)
            box.label(text="Big Row Button :")
            box.label(text="R_P_4_MyButtonName")
            
        ###################################################################################
        # OUR ADDONS
        ###################################################################################
        box = layout.box()
        box.prop(self, 'our_addon', text = "Our Addons !", emboss = False, icon = "FUND")
        if self.our_addon == True:
            col = box.column(align=True)
            row = col.row(align=True)
            row.scale_y = 1.5
            row.operator("wm.url_open", text="BagaPie Assets", icon = 'FUND').url = "https://abaga.gumroad.com/l/GcYmPC"
            row.scale_x = 2
            row.operator("wm.url_open", text="", icon = 'PLAY').url = "https://youtu.be/uK7t_qDjm_0?t=50"
            row = box.row(align=True)
            row.scale_y = 1.5
            row.operator("wm.url_open", text="Quick Compo", icon = 'FUND').url = "https://abaga.gumroad.com/l/QCompo"
            row.scale_x = 2
            row.operator("wm.url_open", text="", icon = 'PLAY').url = "https://youtu.be/ZGN9YxvqXgM"

            col = box.column(align=True)
            col.label(text="Generators / Little Addons / Files :")
            row = col.row(align=True)
            row.scale_x = 1.2
            row.operator("wm.url_open", text="Symbiote Generator").url = "https://abaga.gumroad.com/l/SkyIVq"
            row.operator("wm.url_open", text="Rain Generator").url = "https://abaga.gumroad.com/l/rain"
            row.operator("wm.url_open", text="Blender and Print SpongeBob").url = "https://laura3dcraft.gumroad.com/l/bcvfa"
            row = col.row(align=True)
            row.scale_x = 1.2
            row.operator("wm.url_open", text="Ivy Generator").url = "https://abaga.gumroad.com/l/ivygen"
            row.operator("wm.url_open", text="Arch Generator").url = "https://abaga.gumroad.com/l/UlIvj"
            row.operator("wm.url_open", text="BagaPassesSaver").url = "https://abaga.gumroad.com/l/MQcAd"
            row = col.row(align=True)
            row.scale_x = 1.2
            row.operator("wm.url_open", text="Render Device Switcher").url = "https://abaga.gumroad.com/l/AKNdXX"
            row.operator("wm.url_open", text="Lego Generator").url = "https://abaga.gumroad.com/l/zlcrs"
            row.operator("wm.url_open", text="Fantasy Gate Generator").url = "https://abaga.gumroad.com/l/hcvvq"
        ###################################################################################
        # HELP SUPPORT BUGS
        ###################################################################################
        box = layout.box()
        box.prop(self, 'help_support', text = "Help - Support - Issues - Documentation", emboss = False, icon = "COMMUNITY")
        if self.help_support == True:
            box = box.column(align=True)
            box.separator(factor = 2)
            box.scale_y = 1.5
            box.operator("wm.url_open", text="BagaPie Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
            box.operator("wm.url_open", text="Help - Support - Bug Report on Discord", icon = 'COMMUNITY').url = "https://discord.gg/YtagqdPW6G"
            box.operator("wm.url_open", text="Help - Support - Bug Report on BlenderArtists", icon = 'COMMUNITY').url = "https://blenderartists.org/t/bagapie-modifier-free-addon/1310959"
            box.operator("wm.url_open", text="Youtube Tutorials", icon = 'PLAY').url = "https://www.youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"

        ###################################################################################
        # COMMON ISSUES
        ###################################################################################
        box = layout.box()
        box.prop(self, 'issues', text = "Common Issues !", emboss = False, icon = "ERROR")
        if self.issues == True:
            col = box.column(align=True)
            col.label(text=" 1| When I apply my modifier, everything disappears.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         You must apply the BagaPie modifiers via the addon's panel. (N key)")
            col.label(text="         On top of the BagaPie panel press the apply Button : ✓")
            col.label(text="         Keep in mind that modifiers have an order, apply the ones before your modifier first.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="2| My Scattering/Ivy isn't stabble during my animation.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         The scattering/ivy is based on the surface (area) of the object to calculate the position of the instances.")
            col.label(text="         As your object is animated, the surface (area) may be modified/distorted.")
            col.label(text="         There are currently no solutions for this issue in BagaPie.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="3| My Scattering/Ivy is different when rendered.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         The scattering/ivy is based on the surface (area) of the object to calculate the position of the instances.")
            col.label(text="         Check that your surface does not change at the time of rendering (Ex: Modify Subdivision).")
            col.label(text="         OR")
            col.label(text="         It is possible that the number of particles displayed in the viewport and in the rendering is different.")
            col.label(text="         Check the % Displayed parameter.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="4| The Pie Menu is missing some tools.")
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text="         Check that you are in object mode.")
            col.label(text="         Check that the version of BagaPie is compatible with your Blender version.")
            box.separator(factor = 2)
            
            col = box.column(align=True)
            col.label(text="Still get an issue ?")
            row = box.row(align=True)
            row.operator("wm.url_open", text="Contact us on Discord", icon = 'COMMUNITY').url = "https://discord.gg/YtagqdPW6G"
            row.operator("wm.url_open", text="Or on BlenderArtists", icon = 'COMMUNITY').url = "https://blenderartists.org/t/bagapie-modifier-free-addon/1310959"
            



addon_keymaps = []
classes = [bagapie_Preferences, BagapieSettings]

for script in [
                "bagapie_ui",
                "bagapie_ui_op",
                "bagapie_boolean_op",
                "bagapie_wall_op",
                "bagapie_array_op",
                "bagapie_scatter_op",
                "bagapie_scatterpaint_op",
                "bagapie_displace_op",
                "bagapie_curvearray_op",
                "bagapie_window_op",
                "bagapie_group_op",
                "bagapie_instance_op",
                "bagapie_pointeffector_op",
                "bagapie_import_op",
                "bagapie_proxy_op",
                "bagapie_wallbrick_op",
                "bagapie_ivy_op",
                "bagapie_pointsnapinstance",
                "bagapie_instancesdisplace_op",
                "bagapie_saveasset_op",
                "bagapie_pipes_op",
                "bagapie_beamwire_op",
                "bagapie_stairlinear_op",
                "bagapie_stairspiral_op",
                "bagapie_beam_op",
                "bagapie_floor_op",
                "bagapie_handrail_op",
                "bagapie_column_op",
                "bagapie_twist_op",
                "bagapie_camera_op",
                "bagapie_cable_op",
                "bagapie_fence_op",
                "bagapie_siding_op",
                "bagapie_tiles_op",
            ]:
    exec(f"from . import {script}")
    exec(f"for cls in {script}.classes: classes.append(cls)")
    

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
        addon_keymaps.append((dupli,dupli_id))
        # Duplicate linked
        dupli_link = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        dupli_id_link = km.keymap_items.new("bagapie.duplicatelinkedgroup", type='N', alt=True, value='PRESS')
        addon_keymaps.append((dupli_link,dupli_id_link))

    bpy.types.Scene.bagapieValue = bpy.props.StringProperty(
        name="My List",
        default="none"
    )

    bpy.types.Object.bagapieList = bpy.props.CollectionProperty(type=BagapieSettings)
    bpy.types.Object.bagapieIndex = bpy.props.IntProperty(name="Index", default=0)



def unregister():
    for km,kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
        #bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()


    for cls in classes:
        bpy.utils.unregister_class(cls)
    
        

if __name__ == "__main__":
    register()