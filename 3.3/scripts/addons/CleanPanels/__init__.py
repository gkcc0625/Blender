
import os
import bpy
import re
import sys
import rna_keymap_ui
import importlib
from bpy.types import (PropertyGroup,Menu)
from bpy.app.handlers import persistent
import addon_utils
from bpy_extras.io_utils import ExportHelper,ImportHelper
from datetime import datetime
import bpy.utils.previews
from bpy.app.handlers import persistent
from .utils import *
from .DropDownsAndPie import *
from .workspace_filtering import *
from .Preferences import *
import inspect

bl_info = {
    "name": "CleanPanels",
    "author": "Amandeep and Vectorr66",
    "description": "by vfxmed.com Panels and Workspace Manager",
    "blender": (3, 0 , 0),
    "version": (3, 0, 4),
    "warning": "",
    "category": "Object",
}

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






    #self.layout.prop(context.workspace,'pap_active_workspace_category',text="")



    # column.separator()
    # column.operator("cp.confirmorder", text="", icon="CHECKMARK")

class PAP_Opened_Panels(PropertyGroup):
    name: bpy.props.StringProperty()
    pap_opened_panels:bpy.props.StringProperty()
    opened_before: bpy.props.BoolProperty(default=False)
class PAP_Call_Panels_Sub_Pie(bpy.types.Operator):
    bl_idname = "cp.callpanelssubpie"
    bl_label = "Clean Panels"
    bl_description= "Open Panels Sub Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()
    def invoke(self, context, event):
        context.scene.pap_last_panel_subcategory=self.name
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Sub_Pie_Menu")
        return {"FINISHED"}


class PAP_MT_Panels_Sub_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        category=context.scene.pap_last_panel_subcategory
        base_type = bpy.types.Panel
        count=0
        # op=pieMenu.operator("cp.popuppanel",text=bl_type.bl_label)
                                            # op.name=bl_type.__name__
                                            # op.call_panel=True
                                            # count+=1
        panels_to_draw=[]
        panels_with_parents=[]
        base_type = bpy.types.Panel
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,"bl_category","None")==category or getattr(bl_type,"backup_category","None")==category or get_module_name(bl_type)==get_module_name_from_addon_name(category):
                        
                        if "." not in getattr(bl_type,"bl_context","None") and getattr(bl_type,"bl_parent_id","None")=="None":
                            if (getattr(bl_type,"bl_context","")=="" or getattr(bl_type,"bl_context","None")==get_current_context(context)) and getattr(bl_type,"bl_region_type","None")=='UI'  and getattr(bl_type,'bl_space_type',"None")==context.space_data.type:
                                if getattr(bl_type,'poll',None):
                                    if bl_type.poll(context):
                                        if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw):
                                            
                                            panels_to_draw.append((bl_type,False))
                                else:
                                    if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw):
                                            
                                            panels_to_draw.append((bl_type,False))
                    if getattr(bl_type,"bl_parent_id","None")!="None":
                        #print(bl_type)
                        panels_with_parents.append(bl_type)
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
                    #print(str(e))
        panels_to_draw=sorted(panels_to_draw,key=lambda x: getattr(x[0],'bl_order',0))
        panels_with_parents=sorted(panels_with_parents,key=lambda x: getattr(x,'bl_order',0))
        #print(panels_to_draw,panels_with_parents)
        for bl_type in panels_with_parents:
            try:
                #print(getattr(bl_type,"bl_parent_id","None"))
                # print([getattr(a,"bl_idname","None") for a,b in panels_to_draw]+[getattr(a,"__name__","None") for a,b in panels_to_draw])
                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                    
                    if getattr(bl_type,'poll',None):
                        if bl_type.poll(context):
                            if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw)  or "draw" in inspect.getsource(bl_type._original_draw) :
                                
                                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                                    panels_to_draw.insert([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw].index(getattr(bl_type,"bl_parent_id","None"))+1,(bl_type,True))
                                else:
                                    #print([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a in panels_to_draw],bl_type,getattr(bl_type,"bl_parent_id","None"))
                                    panels_to_draw.append((bl_type,True))
                    else:
                        if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw)  or "draw" in inspect.getsource(bl_type._original_draw) :
                                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                                    panels_to_draw.insert([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw].index(getattr(bl_type,"bl_parent_id","None"))+1,(bl_type,True))
                                else:
                                    #print([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a in panels_to_draw],bl_type,getattr(bl_type,"bl_parent_id","None"))
                                    panels_to_draw.append((bl_type,True))
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
        if len(panels_to_draw)>8:
            for p,has_parent in panels_to_draw[:2]:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            column=pieMenu.column()
            for p,has_parent in panels_to_draw[7:]:
                op=column.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            for p,has_parent in panels_to_draw[2:7]:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
        else:
            for p,has_parent in panels_to_draw:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            #pieMenu.popover(a.bl_idname, text=a.bl_label)
class PAP_MT_Panels_List(Menu):
    bl_label = "Focus Panel"

    def draw(self, context):
        categories=set([])
        registered_panels=[]
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, bpy.types.Panel):
                    if getattr(bl_type,"bl_space_type","None")=='VIEW_3D' and getattr(bl_type,'bl_category',None) :
                        if hasattr(bl_type,'poll'):
                            if bl_type.poll(context):
                                registered_panels.append(bl_type)
                        else:
                            registered_panels.append(bl_type)
            except:
                pass
        # print(registered_panels)
        
        for a in registered_panels:
            # print(a,getattr(a,'bl_category',"Unknown"))
            if getattr(a,'bl_category',"Unknown")!=preferences().holder_tab_name:
                categories.add(getattr(a,'bl_category',"Unknown"))
            else:
                if getattr(a,'renamed_category',None):

                    categories.add(getattr(a,'renamed_category',"Unknown"))
                else:
                    if getattr(a,'backup_category',None):
                        categories.add(getattr(a,'backup_category',"Unknown"))
                
        layout = self.layout
        count=0
        row=layout.row()
        for a in sorted(list(categories),key=str.casefold):
            if a not in ["Item",'Tool','View','Focused','Unknown']:
                
                if count%10==0:

                    col=row.column()
                if count==0:
                    col.operator_context = "INVOKE_DEFAULT"
                    col.operator("cp.focuspanel",text="Turn OFF").name="Turn OFF"
                    count+=1
                col.operator("cp.focuspanel",text=a).name=a
                count+=1
class PAP_MT_Panels_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        panel_list={}
        #categories_string=sentence = ''.join(preferences().panel_categories.split())
        #categories=categories_string.split(",")
        name=context.scene.pap_last_panel_subcategory
        categories=[]
        for a in preferences().panel_categories:
            if a.name==name:
                #categories_string= ''.join(a.panels.split())
                categories=a.panels.split(",")
                categories=[a.strip() for a in categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie() if not preferences().use_verticle_menu else layout
        count=0
        for a in categories:
            count+=1
            #print(a)
            #pieMenu.popover(a.bl_idname, text=a.bl_label)
            pieMenu.operator("cp.popuppanel",text=a).name=a
            if count==8:
                break
            #pieMenu.operator("cp.callpanelssubpie",text=a).name=a
class PAP_MT_Panel_Categories_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        categories=[a.name for a in preferences().panel_categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        count=0
        for a in categories:
            count+=1
            pieMenu.operator("cp.callpanelspie",text=a).name=a
            if count==8:
                break

import pkgutil
class PAP_Call_Panels_Pie(bpy.types.Operator):
    bl_idname = "cp.callpanelspie"
    bl_label = "Clean Panels"
    bl_description="Open Panels Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name:bpy.props.StringProperty()
    def invoke(self, context, event):
        
        context.scene.pap_last_panel_subcategory=self.name
        count=0
        single_name=None
        name=context.scene.pap_last_panel_subcategory
        categories=[]
        for a in preferences().panel_categories:
            if a.name==name:
                #categories_string= ''.join(a.panels.split())
                categories=a.panels.split(",")
                categories=[a.strip() for a in categories]
        count=0
        for a in categories:
            single_name=a
            count+=1
            if count==8:
                break
        if count>1:
            if preferences().use_verticle_menu:
                bpy.ops.wm.call_menu(name="PAP_MT_Panels_Pie_Menu")
            else:
                bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Pie_Menu")
        else:
            if single_name:
                if preferences().pop_out_style=='Pie-PopUp':
                    context.scene.pap_last_panel_subcategory=single_name
                    bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Sub_Pie_Menu")
                else:
                    bpy.ops.cp.popuppanel('INVOKE_DEFAULT',name=single_name,call_panel=False)
        return {"FINISHED"}
class PAP_Toggle_Filter(bpy.types.Operator):
    bl_idname = "cp.togglefiltering"
    bl_label = "Toggle Filter"
    bl_description="Toggle Filtering ON/OFF"
    def invoke(self, context, event):
        if not preferences().filtering_method=="Use N-Panel Filtering":
            context.workspace.category_indices.filter_enabled=not context.workspace.category_indices.filter_enabled
        else:
            preferences().categories.filter_enabled=not preferences().categories.filter_enabled
        context.area.tag_redraw()
        return {"FINISHED"}
class PAP_Call_Panels_Categories_Pie(bpy.types.Operator):
    bl_idname = "cp.callcategoriespie"
    bl_label = "Panels Pie Menu"
    bl_description="Open Panels Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Panel_Categories_Pie_Menu")
        return {"FINISHED"}
class PAP_MT_Workspace_Categories_Pie_Menu(Menu):
    bl_label = "Workspace Filters"

    def draw(self, context):
        categories=[a.name for a in preferences().panel_categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        pcoll= icon_collection["icons"]
        if len(preferences().workspace_categories)>8:
            for index,a in enumerate(preferences().workspace_categories[:2]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
            column=pieMenu.column()
            for index,a in enumerate(preferences().workspace_categories[7:]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        column.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index+7}')).index=index+7
                    else:
                        column.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index+7}')).index=index+7
            for index,a in enumerate(preferences().workspace_categories[2:7]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index+2}')).index=index+2
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index+2}')).index=index+2
        else:
            for index,a in enumerate(preferences().workspace_categories):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
            #row.prop(context.workspace.category_indices,f'enabled_{index}',text=a.name if a.icon=='NONE' else "",icon=a.icon)
class PAP_Call_Workspace_Categories_Pie(bpy.types.Operator):
    bl_idname = "cp.callwspie"
    bl_label = "Workspace Pie Menu"
    bl_description="Open Filtering Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        context.workspace.category_indices.filter_enabled=True
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Workspace_Categories_Pie_Menu")
        return {"FINISHED"}
class PAP_Call_Panels_List(bpy.types.Operator):
    bl_idname = "cp.callpanelslist"
    bl_label = "Focused Panels"
    bl_description="Open Panels List and choose which panel to display in the Focused Tab"
    def invoke(self, context, event):
        # old_areas= context.screen.areas[:]
        # context.workspace.asset_library_ref = 'True-Assets (Worlds)'
        # bpy.ops.screen.area_split(direction='HORIZONTAL', cursor=(1583, 880))
        # new_area=[a for a in context.screen.areas if a not in old_areas][0]
        # new_area.ui_type='FILES'
        # new_area.ui_type='ASSETS'
        
        # print(new_area.spaces.active)
        # #context.workspace.asset_library_ref='True-Assets (Worlds)'
        # for r in new_area.regions:
        #     if r.type=='WINDOW':
        #         region=r
        # if getattr(new_area.spaces.active,'params',None):
        #     try:
        #         new_area.spaces.active.params.asset_library_ref = 'True-Assets (Worlds)'
        #         print()
        #     except:
        #         pass
        # print(region)
        # bpy.ops.cp.changeassetcategory({'area':new_area,'region':region,'space':new_area.spaces.active},'INVOKE_DEFAULT')
        # # for a in new_area.spaces:
        # #     if SpaceAssetInfo.is_asset_browser(a):
        # #         print(inspect.getmembers(a),)
        # #         a.show_region_ui=False
        # #         a.params.asset_library_ref = 'True-Assets (Worlds)'

        # # print(context.workspace.screens[:])
        bpy.ops.wm.call_menu(name="PAP_MT_Panels_List")
        return {"FINISHED"}
    
classes = (#CP_PT_Custom_Panel,
    PAP_Call_Panels_List,PAP_MT_Panels_List,PAP_OT_Open_Focused_Panel,
    CP_OT_Move_Addon_In_Category,CP_UL_Category_Order_List,PAP_OT_Reorder_Category,CP_OT_Inject_Tracking_Code,CP_OT_Change_Category,CP_OT_Load_Addons_List_For_Renaming,CP_UL_Addons_Order_List_For_Renaming,AddonInfoRename,PAP_OT_Search_Dropdown,CP_OT_Open_Preferences,CP_OT_Remove_Panel,CP_OT_Move_Category,PAP_OT_Remove_Panel,PAP_OT_Icon_Picker,CP_OT_Save_Config,CP_OT_Export_Config,CP_OT_Import_Config,AddonInfo,CP_OT_Inject_Code,CP_OT_Clear_Order,CP_OT_Move_Addon,CP_OT_Load_Addons_List,CP_UL_Addons_Order_List,Category_Indices,PAP_Opened_Panels,PAP_Panel_Category,PAPPrefs,PAP_OT_PopUp,PAP_MT_Panels_Pie_Menu,PAP_Call_Panels_Pie,PAP_Toggle_Filter,PAP_OT_CP,PAP_OT_searchPopupForExclusion
    ,PAP_Call_Panels_Sub_Pie,PAP_MT_Panels_Sub_Pie_Menu,PAP_OT_Add_Category,PAP_OT_Remove_Category,PAP_MT_Panel_Categories_Pie_Menu,PAP_Call_Panels_Categories_Pie,PAP_Import_Workspaces,
    PAP_OT_searchPopup,PAP_OT_PopUp_Full_Panel,PAP_OT_searchPopupForDropDown,PAP_OT_Remove_Category_Dropdown,PAP_OT_Remove_Category_Workspace,PAP_OT_searchPopupForWorkspace,PAP_OT_Change_Icon,
    PAP_Enable_Category,PAP_Call_Workspace_Categories_Pie,PAP_MT_Workspace_Categories_Pie_Menu
           )
addon_keymaps = []
def get_dropdown_categories(self, context):
    return [("None","No Dropdowns","None")]+[(a.name,a.name,a.name) for a in preferences().dropdown_categories]
def get_workspace_categories(self, context):
    return [("None","None","None")]+[(a.name,a.name,a.name) for a in preferences().workspace_categories]



def pap_active_dropdown_category_changed(self, context):
    categories=[]
    for b in bpy.context.preferences.addons.keys():
        try:
            #print(sys.modules[b])
            mod=sys.modules[b].__name__
            #print(mod)
            module=importlib.import_module(mod)
            mods=[module]
            try:
                for loader, module_name, is_pkg in pkgutil.walk_packages(module.__path__):
                    _module = loader.find_module(module_name).load_module(module_name)
                    mods.append(_module)
            except:
                pass
            #print("Mods",mods)
            for m in mods:
                #print(m)
                for name, cls in inspect.getmembers(m, inspect.isclass):
                    if issubclass(cls,bpy.types.Panel):
                        if mod=='PowerSave':
                            print(cls.__name__)
                        if cls.is_registered:
                            print(b,cls.__name__)
        except Exception as e:
            print(e)
    for a in preferences().dropdown_categories:
            if a.name==context.scene.pap_active_dropdown_category:
                categories=a.panels.split(",")
                categories=[a.strip() for a in categories]
    base_type = bpy.types.Panel
    for category in categories:
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,"bl_category","None")==category:
                        #bpy.utils.unregister_class(bl_type)
                        bl_type.bl_context="None"
                        #bpy.utils.register_class(bl_type)
            except:
                pass

def pap_active_workspace_category_changed(self, context):
    if context.workspace.pap_active_workspace_category=="None":
        context.workspace.use_filter_by_owner = False
    else:
        context.workspace.use_filter_by_owner = True
        categories=[]
        for a in preferences().workspace_categories:
                if a.name==context.workspace.pap_active_workspace_category:
                    #categories_string= ''.join(a.panels.split())
                    categories=a.panels.split(",")
                    categories=[a.strip() for a in categories]
        for a in [__package__] + categories[:]:
            try:
                a=sys.modules[a].__name__
                if a not in [c.name for c in context.workspace.owner_ids] and a in bpy.context.preferences.addons.keys():
                    bpy.ops.wm.owner_enable(owner_id=a)
            except:
                pass
        for a in preferences().addons_to_exclude.split(",")+addons_to_exclude:
            try:
                if a not in [c.name for c in context.workspace.owner_ids] and a in bpy.context.preferences.addons.keys():
                    
                    bpy.ops.wm.owner_enable(owner_id=a)
            except:
                pass
        for b in bpy.context.preferences.addons.keys():
            try:
                #print(b)
                mod = sys.modules[b]
                if mod.__name__ not in categories+[__package__] and mod.__name__ in [a.name for a in context.workspace.owner_ids]:
                    if mod.__name__ not in preferences().addons_to_exclude.split(",")+addons_to_exclude:
                        #print("Disable",mod.__name__)
                        bpy.ops.wm.owner_disable(owner_id=mod.__name__)
            except:
                    pass
import requests
def getCurrentVersion():
    try:
        response = requests.get(
            "https://github.com/rantools/clean-panels/blob/main/README.md", timeout=4)
        response = str(response.content)
        brokenResponse = response[response.index("Current Version")+17:]
        version = brokenResponse[:5]
        brokenResponse = response[response.index("Custom Message")+16:]
        message = brokenResponse[:brokenResponse.index("]")]

        return version, message
    except:
        return "Disconnected", "Disconnected"
@persistent
def setupdatestatus(scene):
    current_version="".join([s for s in str(sys.modules['CleanPanels'].bl_info['version']) if s.isdigit()])
    #current_version=str(sys.modules['Clean Panels'].bl_info['version']).replace("(","").replace(")","").replace(", ","")
    og_online_version,message=getCurrentVersion()
    online_version=og_online_version.replace(".","")
    if online_version!="Disconnected":
        if int(online_version)<int(current_version):
            bpy.context.scene.cp_update_status ="Clean Panels is Up To Date! (Beta)" 
        elif int(online_version)==int(current_version):
            bpy.context.scene.cp_update_status ="Clean Panels is Up To Date!" 
        else:
            bpy.context.scene.cp_update_status=f"Update Available! (v{og_online_version})"
    else:
        print("Couldn't check for Updates")

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    load_icons()
    bpy.types.Scene.pap_last_panel_category = bpy.props.StringProperty(default="")
    bpy.types.Scene.pap_last_panel_subcategory = bpy.props.StringProperty(default="Item")
    bpy.types.Scene.pap_opened_panels= bpy.props.CollectionProperty(type=PAP_Opened_Panels)
    bpy.types.Scene.pap_active_dropdown_category=bpy.props.EnumProperty(items=get_dropdown_categories,name="Dropdowns")
    bpy.types.WorkSpace.pap_active_workspace_category=bpy.props.EnumProperty(items=get_workspace_categories,name="Dropdowns",update=pap_active_workspace_category_changed)
    bpy.types.WorkSpace.category_indices=bpy.props.PointerProperty(type=Category_Indices)
    bpy.types.VIEW3D_MT_editor_menus.append(draw_dropdowns)
    bpy.types.VIEW3D_HT_tool_header.prepend(draw_before_editor_menu)
    bpy.types.Scene.cp_update_status=bpy.props.StringProperty(default="Clean Panels is Up To Date!")
    bpy.types.Scene.addon_info=bpy.props.CollectionProperty(type=AddonInfo)
    bpy.types.Scene.addon_info_index= bpy.props.IntProperty(default=0,name="Selected Tab")
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        

        kmi = km.keymap_items.new(
            "cp.callcategoriespie",
            type='R',
            value="PRESS",alt=True
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.togglefiltering",
            type='F',
            value="PRESS"
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.callwspie",
            type='F',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.callpanelslist",
            type='J',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
        
    bpy.app.handlers.load_post.append(loadPreferences)
    bpy.app.handlers.load_post.append(setupdatestatus)
    loadPreferences()
    # if not bpy.app.timers.is_registered(toggle_filtering_OnOff):
    #toggle_filtering_OnOff()
    if not bpy.app.timers.is_registered(toggle_filtering_OnOff):
        bpy.app.timers.register(toggle_filtering_OnOff, first_interval=5,persistent=True)

def unregister():
    savePreferences()
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    try:
            bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
    except:
        pass
    try:
        bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
    except:
        pass
    bpy.types.VIEW3D_HT_tool_header.remove(draw_before_editor_menu)
#inject_code(os.path.join(os.path.dirname(__file__),'test.py'))
    try:
        bpy.app.handlers.load_post.remove(loadPreferences)
        bpy.app.handlers.version_update.remove(toggle_filtering_OnOff)
        
    except:
        pass
    try:
        bpy.app.handlers.load_post.remove(setupdatestatus)
    except:
        pass
    if bpy.app.timers.is_registered(toggle_filtering_OnOff):
        bpy.app.timers.unregister(toggle_filtering_OnOff)
if __name__ == "__main__":
    register()
    
