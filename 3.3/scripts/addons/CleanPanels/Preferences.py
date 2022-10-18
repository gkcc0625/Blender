import os
import bpy
import rna_keymap_ui

import bpy.utils.previews
from bpy.types import (PropertyGroup,Menu)
from bpy_extras.io_utils import ExportHelper,ImportHelper
from .utils import *

def tab_name_updated(self,context):
    pass
class AddonInfo(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    addons: bpy.props.StringProperty()
    ordered: bpy.props.StringProperty()
class AddonInfoRename(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    tab_name: bpy.props.StringProperty(update=tab_name_updated)


def draw_before_editor_menu(self, context):
    if preferences().draw_side=='LEFT':
        self.layout.operator("cp.settings",icon='PREFERENCES',text="")
    if preferences().use_dropdowns and len(preferences().dropdown_categories)>0:
        self.layout.prop(context.scene,'pap_active_dropdown_category',text="")
    row=self.layout.row(align=True)
    if preferences().draw_side=='LEFT':
        if not preferences().filtering_method=="Use N-Panel Filtering":
            row.prop(context.workspace.category_indices,'filter_enabled',text="",icon='FILTER',toggle=True)
        else:
            row.prop(preferences().categories,'filter_enabled',text="",icon='FILTER',toggle=True)
    row.separator(factor=1)
    pcoll=icon_collection["icons"]
    for index,a in enumerate(preferences().workspace_categories):
        #print(getattr(context.workspace,f'enabled_{index}'))
        if not preferences().filtering_method=="Use N-Panel Filtering":
            if context.workspace.category_indices.filter_enabled:
                if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                    row.operator("cp.enablecategory",text=a.name if a.icon=='NONE' else "",icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                else:
                    row.operator("cp.enablecategory",text=a.name if a.icon=='NONE' else "",icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                #row.prop(context.workspace.category_indices,f'enabled_{index}',text=a.name if a.icon=='NONE' else "",icon=a.icon)
        else:
            if preferences().categories.filter_enabled:
                if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                    row.operator("cp.enablecategory",text=a.name if a.icon=='NONE' else "",icon=a.icon,depress=getattr(preferences().categories,f'enabled_{index}')).index=index
                else:
                    row.operator("cp.enablecategory",text=a.name if a.icon=='NONE' else "",icon_value=pcoll[a.icon].icon_id,depress=getattr(preferences().categories,f'enabled_{index}')).index=index
    row.separator(factor=1)
    if preferences().draw_side=='RIGHT':
        if not preferences().filtering_method=="Use N-Panel Filtering":
            row.prop(context.workspace.category_indices,'filter_enabled',text="",icon='FILTER',toggle=True)
        else:
            row.prop(preferences().categories,'filter_enabled',text="",icon='FILTER',toggle=True)
        row.separator(factor=1)
        row.operator("cp.settings",icon='PREFERENCES',text="")
def draw_side_changed(self, context):
    if self.draw_side=='RIGHT':
        try:
            bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
        except:
            pass
        bpy.types.VIEW3D_HT_tool_header.remove(draw_before_editor_menu)
        
        bpy.types.VIEW3D_HT_header.append(draw_dropdowns)
        bpy.types.VIEW3D_HT_tool_header.append(draw_before_editor_menu)
    else:
        try:
            bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
        except:
            pass
        bpy.types.VIEW3D_HT_tool_header.remove(draw_before_editor_menu)
        bpy.types.VIEW3D_MT_editor_menus.append(draw_dropdowns)
        bpy.types.VIEW3D_HT_tool_header.prepend(draw_before_editor_menu)
    savePreferences()
def exclusion_list_changed(self, context):
    for w in self.workspace_categories:
        for a in self.addons_to_exclude.split(","):
            #print(a,w.panels.split(","))
            if a in w.panels.split(","):
                w.panels=",".join([b for b in w.panels.split(",") if b!=a])
    savePreferences()
def check_if_old_injection_exists(filename):
    with open(filename, 'r') as f:
        text=f.read()
        if "config_path" in text:
            return True
    return False
def inject_tracking_code(filename):
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config")):
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config"))
    if check_if_old_injection_exists(filename):
        data=[]
        with open(filename, 'r',newline='\n') as f:
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-PanelOrder.txt")
            
            for line in f.readlines():
                
                if "config_path=r" in line:
                    data.append(f"config_path=r'{path}'\n")
                else:
                    data.append(line)
        with open(filename, 'w',newline='\n') as f:
            if data:
                f.writelines(data)
    else:
        with open(filename, 'r') as f:
            
            text = f.read()
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-PanelOrder.txt")
            text = text.replace("""system_resource,
)""",f"""system_resource,
)
import inspect
import os
import time
config_path=r'{path}'
try:
    mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0
    if time.time()-mtime>10:
        with open(config_path, mode='w', newline='\\n', encoding='utf-8') as file:
            print('Creating Blank CP-PanelOrder file..')
except Exception as e:
    print(e)
panels=[]
scripts_directory=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),"startup")
def register_class(cl,write_to_file=True):
    try:
        if write_to_file and issubclass(cl,_bpy.types.Panel) and scripts_directory not in getattr(inspect.getmodule(cl),'__file__',""):
            with open(config_path, mode='a', newline='\\n', encoding='utf-8') as file:
                panels.append(cl.__name__)
                file.write(cl.__name__+'\\n')
    except Exception as e:
        print(e)
    register_class_og(cl)""")
            text=text.replace("""register_class,
    resource_path,""","""register_class as register_class_og,
    resource_path,""")

        with open(filename, 'w') as f:
            f.write(text)
def inject_code(filename):
    if check_if_old_injection_exists(filename):
        data=[]
        with open(filename, 'r',newline='\n') as f:
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")
            
            for line in f.readlines():
                
                if "config_path=r" in line:
                    data.append(f"    config_path=r'{path}'\n")
                else:
                    data.append(line)
        with open(filename, 'w',newline='\n') as f:
            if data:
                f.writelines(data)
    else:
        with open(filename, 'r') as f:
            
            text = f.read()
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")
            text = text.replace("for addon in _preferences.addons:","import os")
            text = text.replace("    enable(addon.module)",f"config_path=r'{path}'")
            text1=text[:text.index(f"config_path=r'{path}'")+len(f"config_path=r'{path}'")]
            text2=text[text.index(f"config_path=r'{path}'")+len(f"config_path=r'{path}'"):]
            final_text=text1+"""
    order_of_addons=[]
    if os.path.isfile(config_path):
        with open(config_path, mode='r', newline='\\n', encoding='utf-8') as file:
            prefs = file.readlines()
            for p in prefs:
                try:
                    attr = p[:p.index("=>")]
                    type = p[p.index("=>")+2:p.index("===")]
                    value = p[p.index("===")+3:]
                    value = value.replace("\\n", "")
                    if attr =='addon_order' and type=='order':
                        panels=value[value.index(">>")+2:]
                        order_of_addons=panels.split(',')
                except:
                    pass
        
    for addon in order_of_addons:
        if addon in [a.module for a in _preferences.addons]:
            enable(addon)
    
    for addon in _preferences.addons:
        if addon.module not in order_of_addons:
            enable(addon.module)"""+text2

        with open(filename, 'w') as f:
            f.write(final_text)
kmaps_object_mode = ["cp.callcategoriespie","cp.togglefiltering","cp.callwspie" ,"cp.callpanelslist"]
def draw_addons_list(layout,context):
    layout.label(text="N-Panel Order")
    column = layout.column()
    column = column.split(factor=0.9)
    column.template_list("CP_UL_Addons_Order_List", "", preferences(), "addon_info",
                                preferences(), "addon_info_index" ,item_dyntip_propname='name')
    column = column.column(align=True)
    column.operator("cp.loadaddons",
                    text="", icon="FILE_REFRESH")
    column.separator()
    column.operator("cp.moveaddon", text="", icon="SORT_DESC").direction='UP'
    column.operator("cp.moveaddon", text="", icon="SORT_ASC").direction='DOWN'
def draw_addons_list_for_renaming(layout,context):
    layout.label(text="N-Panel Renaming")
    column = layout.column()
    column = column.split(factor=0.9)
    column.template_list("CP_UL_Addons_Order_List_For_Renaming", "", preferences(), "addon_info_for_renaming",
                                preferences(), "addon_info_for_renaming_index" ,item_dyntip_propname='name')
    column = column.column(align=True)
    column.operator("cp.loadaddonsforrenaming",
                    text="", icon="FILE_REFRESH")



def draw_hotkeys(col,km_name):
    kc = bpy.context.window_manager.keyconfigs.user
    for kmi in kmaps_object_mode:
        km2=kc.keymaps[km_name]
        kmi2=[]
        for a,b in km2.keymap_items.items():
            if a==kmi:
                kmi2.append(b)
        if kmi2:
            for a in kmi2:
                col.context_pointer_set("keymap", km2)
                rna_keymap_ui.draw_kmi([], kc, km2, a, col, 0)
def draw_settings(instance,self, context,is_preferences=True):
        layout = instance.layout
        
        if is_preferences:
            layout.prop(self,'show_advanced',toggle=True)
            if self.show_advanced:
                self.layout.label(text="Clean Up method for N-Panel (Restart Blender after changing this):")
                self.layout.row().prop(self,'filtering_method',expand=True)
        if self.show_advanced:
            if is_preferences:
                layout.prop(self,'experimental')
                if self.experimental:
                    layout.label(text="Make sure you backup your addon directory before using Experimental Features!",icon='ERROR')
                    layout.prop(self,'auto_backup_addons')
        if is_preferences:
            draw_hotkeys(layout, "3D View")
        layout.prop(self,'draw_side')
        if is_preferences:
            layout.prop(self,'use_sticky_popup')
            
        layout2 = layout
        if self.show_advanced:  
            if is_preferences:
                layout3 = layout2.box()
                row = layout3.row(align=True)
                row.alignment = 'LEFT'
                
                
                row.prop(self, "show_npanel_ordering", emboss=False,
                        icon="TRIA_DOWN" if self.show_npanel_ordering else "TRIA_RIGHT")
                
                if self.show_npanel_ordering:
                    row = layout3.column()
                    if  self.filtering_method=="Use N-Panel Filtering":
                        row.prop(self, "sort_per_category",toggle=True)
                    if not self.injected_code and not self.filtering_method=="Use N-Panel Filtering":
                        row.label(text="Click this button before reordering the tabs!" if not self.filtering_method=="Use N-Panel Filtering" else 'Click this button for proper ordering of sub-panels in a Tab!',icon='ERROR')
                        row.operator("cp.injectcode")
                    if  not self.injected_code_tracking and self.filtering_method=="Use N-Panel Filtering":
                        row.label(text="Click this button before reordering the tabs!" if not self.filtering_method=="Use N-Panel Filtering" else 'Click this button for proper ordering of sub-panels in a Tab!',icon='ERROR')
                        row.operator("cp.injecttrackingcode")
                    draw_addons_list(row,context)
                    if not self.filtering_method=="Use N-Panel Filtering":
                        row.operator("cp.clearforcedorders")
                    else:
                        row.operator("cp.changecategory",text="Confirm" if preferences().filtering_method=="Use N-Panel Filtering" else "Confirm (This will change category in the source file)")
                    
                if self.experimental or self.filtering_method=="Use N-Panel Filtering":
                    layout3 = layout2.box()
                    row = layout3.row(align=True)
                    row.alignment = 'LEFT'
                    
                    
                    row.prop(self, "show_npanel_renaming", emboss=False,
                        icon="TRIA_DOWN" if self.show_npanel_renaming else "TRIA_RIGHT")
                    if self.show_npanel_renaming:
                        row = layout3.column()
                        draw_addons_list_for_renaming(row,context)
                        row.operator("cp.changecategory",text="Confirm" if preferences().filtering_method=="Use N-Panel Filtering" else "Confirm (This will change category in the source file)")
        layout3 = layout2.box()
        row = layout3.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "show_panel_categories", emboss=False,
                icon="TRIA_DOWN" if self.show_panel_categories else "TRIA_RIGHT")
        if self.show_panel_categories:
            row = layout3.column()
            for index,a in enumerate(self.panel_categories):
                row.separator(factor=1)
                row.separator(factor=1)
                box=row.box()
                row1=box.row()
                row1=row1.split(factor=0.7)
                
                row1.prop(a,'name',text="")
                row2=row1.split(factor=0.75)
                op = row2.operator('cp.remove_category', text='',
                                icon='PANEL_CLOSE')
                op.index = index
                
                op = row2.operator('cp.movecategory', text='',
                                icon='TRIA_UP')
                op.index = index
                op.category = 'Pie'
                op.direction='UP'
                row1=box.row()
                row1=row1.split(factor=0.7)
                row2=row1.row()
                row1=row1.split(factor=0.75)
                row2.prop(a,'panels')
                if not a.panels:
                    row2.enabled=False
                row1.operator("cp.search_popup",text="",icon="ADD",depress=True).index=index
                op = row1.operator('cp.movecategory', text='',
                                icon='TRIA_DOWN')
                op.index = index
                op.category = 'Pie'
                op.direction='DOWN'
                if is_preferences:
                    grid=box.grid_flow(columns=4,row_major=True)
                    for panel in a.panels.split(","):
                        if panel:
                            op=grid.operator("cp.remove_panel",text=panel,icon='PANEL_CLOSE')
                            op.index=index
                            op.panel=panel
                            op.category="Pie"
                
            row.separator(factor=1)
            row.separator(factor=1)
            row.operator("cp.add_category").to="Pie"
            
            row.prop(self,'pop_out_style')
            if self.pop_out_style=='DropDown':
                row.prop(self,'columm_layout_for_popup')
            row.prop(self,'use_verticle_menu')
        layout3 = layout2.box()
        row = layout3.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "show_dropdown_categories", emboss=False,
                icon="TRIA_DOWN" if self.show_dropdown_categories else "TRIA_RIGHT")
        
        if self.show_dropdown_categories:    
            
            row=layout3.column()
            if is_preferences:
                row.prop(self,'use_dropdowns',toggle=True)
            for index,a in enumerate(self.dropdown_categories):
                row.separator(factor=1)
                row.separator(factor=1)
                box=row.box()
                row1=box.row()
                row1=row1.split(factor=0.7)
                
                row1.prop(a,'name',text="")
                row2=row1.split(factor=0.75)
                op = row2.operator('cp.remove_category_from_dropdown', text='',
                                icon='PANEL_CLOSE')
                op.index = index
                
                op = row2.operator('cp.movecategory', text='',
                                icon='TRIA_UP')
                op.index = index
                op.category = 'DropDown'
                op.direction='UP'
                
                row1=box.row()
                row1=row1.split(factor=0.7)
                row2=row1.row()
                row1=row1.split(factor=0.75)
                row2.prop(a,'panels')
                if not a.panels:
                    row2.enabled=False
                row1.operator("cp.search_popup_for_dropdown",text="",icon="ADD",depress=True).index=index
                op = row1.operator('cp.movecategory', text='',
                                icon='TRIA_DOWN')
                op.index = index
                op.category = 'DropDown'
                op.direction='DOWN'
                if is_preferences:
                    grid=box.grid_flow(columns=4,row_major=True)
                    for panel in a.panels.split(","):
                        if panel:
                            op=grid.operator("cp.remove_panel",text=panel,icon='PANEL_CLOSE')
                            op.index=index
                            op.panel=panel
                            op.category="DropDown"
            row.separator(factor=1)
            row.separator(factor=1)
            row.operator("cp.add_category").to="DropDown"
            row.separator(factor=1)
            row.prop(self,'dropdown_width')
            row.prop(self,'show_dropdown_search')
        pcoll=icon_collection["icons"]

        layout3 = layout2.box()
        row = layout3.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, "show_workspace_categories", emboss=False,text="Workspace Addon Categories" if self.filtering_method!="Use N-Panel Filtering" else "N-Panel Categories",
                icon="TRIA_DOWN" if self.show_workspace_categories else "TRIA_RIGHT")
        if self.show_workspace_categories:    
            row=layout3.column()
            for index,a in enumerate(self.workspace_categories):
                row.separator(factor=1)
                row.separator(factor=1)
                box=row.box()
                row1=box.row()
                row1=row1.split(factor=0.7)
                
                row1.prop(a,'name',text="")
                row2=row1.split(factor=0.5)
                if a.icon in ALL_ICONS:
                    row2.operator("cp.change_icon",text="Icon",icon=a.icon if a.icon else None).index=index
                else:
                    row2.operator("cp.change_icon",text="Icon",icon_value=pcoll[a.icon].icon_id).index=index
                row2=row2.split(factor=0.5)
                op = row2.operator('cp.remove_category_from_workspace', text='',
                                icon='PANEL_CLOSE')
                op.index = index
                
                op = row2.operator('cp.movecategory', text='',
                                icon='TRIA_UP')
                op.index = index
                op.category = 'Workspace'
                op.direction='UP'
                
                row1=box.row()
                row1=row1.split(factor=0.7)
                row2=row1.row()
                row1=row1.split(factor=0.77)
                row2.prop(a,'panels')
                if not a.panels:
                    row2.enabled=False
                if is_preferences:
                    row3=row1.split(factor=0.72)
                    row3.operator("cp.search_popup_for_workspace",text="",icon="ADD",depress=True).index=index
                    op=row3.operator('cp.reordercategory', text='',icon_value=icon_collection["icons"]['reorder'].icon_id)
                    op.index= index
                    op.exclusion_list= False
                else:
                    row1.operator("cp.search_popup_for_workspace",text="",icon="ADD",depress=True).index=index
                op = row1.operator('cp.movecategory', text='',
                                icon='TRIA_DOWN')
                op.index = index
                op.category = 'Workspace'
                op.direction='DOWN'
                
                if is_preferences:
                    grid=box.grid_flow(columns=4,row_major=True)
                    for panel in a.panels.split(","):
                        if panel:
                            op=grid.operator("cp.remove_panel",text=panel,icon='PANEL_CLOSE')
                            op.index=index
                            op.panel=panel
                            op.category="Workspace"
            row.separator(factor=1)
            row.operator("cp.add_category").to="Workspace"
            row.separator(factor=1)
            row.separator(factor=1)
            row1=row.row()
            row1=row1.split(factor=0.9)
            row2=row1.row()
            row2.prop(self,'addons_to_exclude')
            
            if not self.addons_to_exclude:
                row2.enabled=False
            row1.operator("cp.search_popup_for_exclude_list",text="",icon="ADD",depress=True)
            op=row1.operator('cp.reordercategory', text='',icon_value=icon_collection["icons"]['reorder'].icon_id)
            op.exclusion_list= True
            row.separator(factor=1)
            if is_preferences:
                grid=row.grid_flow(columns=4,row_major=True)
                for panel in self.addons_to_exclude.split(","):
                    if panel:
                        op=grid.operator("cp.remove_panel",text=panel,icon='PANEL_CLOSE')
                        op.panel=panel
                        op.category="ExclusionList"
            
            
            if is_preferences:
                row.separator(factor=1)
                row.label(text="Tab name for filtered out panels")
                row.prop(self,'holder_tab_name',text="")
            row.separator(factor=1)
            row.operator("cp.importworkspaces")
        return layout2
class CP_UL_Addons_Order_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data

        obj = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if obj:
                row = layout.row()
                row.label(text=obj.name)
                row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')

        elif self.layout_type in {'GRID'}:
            row = layout.row()
            row.label(text=obj.name)
            row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')
class CP_UL_Category_Order_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data

        obj = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if obj:
                row = layout.row()
                row.label(text=obj.name)

        elif self.layout_type in {'GRID'}:
            row = layout.row()
            row.label(text=obj.name)
class CP_UL_Addons_Order_List_For_Renaming(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data

        obj = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if obj:
                row = layout.row()
                row.label(text=obj.name)
                row.prop(obj,'tab_name',text="",emboss=False)

        elif self.layout_type in {'GRID'}:
            row = layout.row()
            row.label(text=obj.name)
            row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')
class PAP_OT_Add_Category(bpy.types.Operator):
    bl_idname = 'cp.add_category'
    bl_label = 'Add New Category'
    bl_description="Create a new Category for this section"
    bl_property='name'
    name: bpy.props.StringProperty(default="Category",name="Name")
    to: bpy.props.StringProperty(default="Pie")
    def draw(self, context):
        self.layout.prop(self,'name')
    def execute(self, context):
        if self.to=='Pie':
            t=preferences().panel_categories.add()
            t.name=self.name
        elif self.to=='Workspace':
            if len(preferences().workspace_categories)<50:
                t=preferences().workspace_categories.add()
                t.name=self.name
            else:
                self.report({'WARNING'},"Workspace are limited to 50!")
        else:
            t=preferences().dropdown_categories.add()
            t.name=self.name
        savePreferences()
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
class PAP_OT_Remove_Panel(bpy.types.Operator):
    bl_idname = 'cp.remove_panel'
    bl_label = 'Remove this addon/panel'
    bl_description="Remove this Addon/Panel from this category"
    index: bpy.props.IntProperty()
    panel: bpy.props.StringProperty()
    category: bpy.props.StringProperty(default="Pie")
    def execute(self, context):
        if self.category=="Pie":
            preferences().panel_categories[self.index].panels=",".join([a for a in preferences().panel_categories[self.index].panels.split(",") if a and a!=self.panel])
        elif self.category=="DropDown":
            preferences().dropdown_categories[self.index].panels=",".join([a for a in preferences().dropdown_categories[self.index].panels.split(",") if a and a!=self.panel])
        elif self.category=="Workspace":
            preferences().workspace_categories[self.index].panels=",".join([a for a in preferences().workspace_categories[self.index].panels.split(",") if a and a!=self.panel])
        else:
            preferences().addons_to_exclude=",".join([a for a in preferences().addons_to_exclude.split(",") if a and a!=self.panel])
        savePreferences()
        return {'FINISHED'}
class PAP_OT_Remove_Category(bpy.types.Operator):
    bl_idname = 'cp.remove_category'
    bl_label = 'Remove this Category'
    bl_description="Remove this Category"
    index: bpy.props.IntProperty()

    def execute(self, context):
        preferences().panel_categories.remove(
            self.index)
        savePreferences()
        return {'FINISHED'}
class PAP_OT_CP(bpy.types.Operator):
    bl_idname = 'cp.settings'
    bl_label = "Clean Panels"
    bl_description="Open Clean Panels quick settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Clean Panels"

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x=25
        layout.operator("cp.openpreferences",icon='TOOL_SETTINGS')
        draw_settings(self,preferences(), context,False)
        
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
class PAP_OT_Remove_Category_Dropdown(bpy.types.Operator):
    bl_idname = 'cp.remove_category_from_dropdown'
    bl_label = 'Remove this Category'
    index: bpy.props.IntProperty()
    bl_description="Remove this Category from Dropdowns section"
    def execute(self, context):
        preferences().dropdown_categories.remove(
            self.index)
        savePreferences()
        return {'FINISHED'}
class PAP_OT_Remove_Category_Workspace(bpy.types.Operator):
    bl_idname = 'cp.remove_category_from_workspace'
    bl_label = 'Remove this Category'
    bl_description="Remove this category from workspace filtering"
    index: bpy.props.IntProperty()

    def execute(self, context):
        preferences().workspace_categories.remove(
            self.index)
        savePreferences()
        return {'FINISHED'}
class PAP_OT_Reorder_Category(bpy.types.Operator):
    bl_idname = 'cp.reordercategory'
    bl_label = 'Reorder'
    bl_description="Change the order of Panels.\nUseful when using per category sorting(with N-Panel Filtering method)"
    index: bpy.props.IntProperty()
    exclusion_list: bpy.props.BoolProperty(default=False,options={'SKIP_SAVE','HIDDEN'})
    def draw(self, context):
        layout=self.layout
        column = layout.column()
        column = column.split(factor=0.9)
        column.template_list("CP_UL_Category_Order_List", "", context.scene, "addon_info",
                                    context.scene, "addon_info_index" ,item_dyntip_propname='name')
        column = column.column(align=True)
        column.operator("cp.moveaddonincategory", text="", icon="SORT_DESC").direction='UP'
        column.operator("cp.moveaddonincategory", text="", icon="SORT_ASC").direction='DOWN'
    def execute(self, context):
        if self.exclusion_list:
            preferences().addons_to_exclude=",".join([a.name for a in context.scene.addon_info])
        else:
            preferences().workspace_categories[self.index].panels=",".join([a.name for a in context.scene.addon_info])
        bpy.ops.cp.togglefiltering('INVOKE_DEFAULT')
        bpy.ops.cp.togglefiltering('INVOKE_DEFAULT')
        savePreferences()
        return {'FINISHED'}
    def invoke(self, context, event):
        context.scene.addon_info.clear()
        if self.exclusion_list:
            for a in preferences().addons_to_exclude.split(","):
                t=context.scene.addon_info.add()
                t.name=a
        else:
            for a in preferences().workspace_categories[self.index].panels.split(","):
                t=context.scene.addon_info.add()
                t.name=a
            
        return context.window_manager.invoke_props_dialog(self)
class CP_OT_Remove_Panel(bpy.types.Operator):
    bl_idname="cp.removedropdownpanel"
    bl_label="Remove this Dropdown"
    bl_options = {'REGISTER', 'UNDO'}
    name: bpy.props.StringProperty()
    def execute(self, context):
        for a in preferences().dropdown_categories:
            a.panels=",".join([b for b in a.panels.split(",") if b!=self.name and b])
        savePreferences()
        return {'FINISHED'}
class PAP_OT_searchPopup(bpy.types.Operator):
    
    bl_idname = "cp.search_popup"
    bl_label = "Add Panel"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_panel_categories)
    category: bpy.props.StringProperty(default="Pie")
    index: bpy.props.IntProperty(default=0)
    def execute(self, context):
        index=self.index
        #index=preferences().panel_categories.find(self.category)
        if index>=0:
            preferences().panel_categories[index].panels=(preferences().panel_categories[index].panels+","+self.my_enum) if preferences().panel_categories[index].panels else self.my_enum
        savePreferences()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}
class PAP_OT_searchPopupForExclusion(bpy.types.Operator):
    
    bl_idname = "cp.search_popup_for_exclude_list"
    bl_label = "Add Addon"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_all_addons)
    def execute(self, context):
        if self.my_enum=='All':
            all_addons=",".join(get_all_addon_names(self,context))
            preferences().addons_to_exclude=all_addons
        elif self.my_enum=='Unfiltered':
            used_addons=[]
            for a in preferences().workspace_categories:
                used_addons.extend(a.panels.split(","))
            all_addons=get_all_addon_names(self,context)
            addons_to_add=[b for b in all_addons if b not in used_addons]
            current_addons=preferences().addons_to_exclude.split(",")
            final_list=",".join(list(set(current_addons+addons_to_add)))
            preferences().addons_to_exclude=final_list
        else:
        
            preferences().addons_to_exclude=(preferences().addons_to_exclude+","+self.my_enum) if preferences().addons_to_exclude else self.my_enum
        savePreferences()
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}
class PAP_OT_searchPopupForDropDown(bpy.types.Operator):
    
    bl_idname = "cp.search_popup_for_dropdown"
    bl_label = "Add Panel"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Dropdown")
    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_panel_categories)
    index: bpy.props.IntProperty(default=0)
    def execute(self, context):
        index=self.index
        #index=preferences().dropdown_categories.find(self.category)
        if index>=0:
            preferences().dropdown_categories[index].panels=(preferences().dropdown_categories[index].panels+","+self.my_enum) if preferences().dropdown_categories[index].panels else self.my_enum
        savePreferences()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}

class PAP_OT_Icon_Picker(bpy.types.Operator):
    
    bl_idname = "cp.change_icon"
    bl_label = "Icon"
    bl_description = "Change the icon displayed on the viewport and the pie menu"

    index: bpy.props.IntProperty(default=0)
    category: bpy.props.StringProperty(default="Pie")
    search: bpy.props.StringProperty(default="",options={'SKIP_SAVE'})
    #my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_icons)
    
    def draw(self, context):
        #self.layout.ui_units_x=
        self.layout.prop(self,'search',icon="VIEWZOOM",text="")
        grid=self.layout.grid_flow(columns=12,even_rows=True,even_columns=True,row_major=True)
        pcoll = icon_collection["icons"]
        custom_icons=pcoll.keys()
        blender_icons=ALL_ICONS
        for a in custom_icons:
            if self.search.lower() in a.lower():
                op=grid.operator("cp.set_icon",text="",icon_value=pcoll[a].icon_id,emboss=False)
                op.my_enum=a
                op.index=self.index
                op.category=self.category
        for a in blender_icons:
            if self.search.lower() in a.lower():
                op=grid.operator("cp.set_icon",text="",icon=a,emboss=False)
                op.my_enum=a
                op.index=self.index
                op.category=self.category
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
class PAP_OT_Change_Icon(bpy.types.Operator):
    bl_idname = "cp.set_icon"
    bl_label = "Icon"
    bl_description="Use this icon"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Pie")
    my_enum: bpy.props.StringProperty(default="NONE")
    index: bpy.props.IntProperty(default=0)
    def invoke(self, context,event):
        x,y=event.mouse_x,event.mouse_y
        context.window.cursor_warp(-10000,-10000)
        low_left_x=max(0,context.window.x)
        low_left_y=context.window.y
        reset_cursor=lambda : context.window.cursor_warp(x+(low_left_x),y+(low_left_y)-60)
        bpy.app.timers.register(reset_cursor,first_interval=0.00000001)
        index=self.index
        if index>=0:
            preferences().workspace_categories[index].icon=self.my_enum
            
        context.area.tag_redraw()
        savePreferences()
        return {'FINISHED'}

class PAP_OT_searchPopupForWorkspace(bpy.types.Operator):
    
    bl_idname = "cp.search_popup_for_workspace"
    bl_label = "Add Addon"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Workspace")
    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_installed_addons)
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        index=self.index
        if index>=0:
            if self.my_enum=='All':
                all_addons=",".join(get_installed_addon_names(self,context)+preferences().workspace_categories[index].panels.split(","))

                preferences().workspace_categories[index].panels=all_addons
            elif self.my_enum=='Unfiltered':
                used_addons=[]
                for a in preferences().workspace_categories:
                    used_addons.extend(a.panels.split(","))
                all_addons=get_installed_addon_names(self,context)
                addons_to_add=[b for b in all_addons if b not in used_addons]
                current_addons=preferences().workspace_categories[index].panels.split(",")
                final_list=",".join(list(set(current_addons+addons_to_add)))
                preferences().workspace_categories[index].panels=final_list
            else:
                preferences().workspace_categories[index].panels=(preferences().workspace_categories[index].panels+","+self.my_enum) if preferences().workspace_categories[index].panels else self.my_enum
        savePreferences()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}
class PAP_OT_Search_Dropdown(bpy.types.Operator):
    
    bl_idname = "cp.search_dropdown"
    bl_label = "Search Dropdown"
    bl_description="Quickly search for any panel to display it as dropdown"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Workspace")
    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_all_panel_categories)
    
    def execute(self, context):
        bpy.ops.cp.popupcompletepanel('INVOKE_DEFAULT',name=self.my_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


import inspect

class CP_OT_Load_Addons_List_For_Renaming(bpy.types.Operator):
    bl_idname = "cp.loadaddonsforrenaming"
    bl_label = "Load Addons"
    bl_description="Reload the list"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        # preferences().addon_info_for_renaming.clear()
        load_renaming_list(context)
        return {'FINISHED'}

class CP_OT_Load_Addons_List(bpy.types.Operator):
    bl_idname = "cp.loadaddons"
    bl_label = "Load Addons"
    bl_description="Reload the list"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        load_reordering_list(context)
        return {'FINISHED'}
class CP_OT_Open_Preferences(bpy.types.Operator):
    bl_idname = "cp.openpreferences"
    bl_label = "Open Addon Preferences"
    bl_description="Open Addon Preferences"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context,event):
        bpy.ops.screen.userpref_show()
        bpy.context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = "CleanPanels"
        return {'FINISHED'}
class CP_OT_Inject_Tracking_Code(bpy.types.Operator):
    bl_idname = "cp.injecttrackingcode"
    bl_label = "Click this button for proper ordering of Sub-Panels"
    bl_description="Pressing this button will insert a few lines of code in the utils module of blender which will enable Clean Panels to work correctly"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context,event):
        
        version=bpy.app.version
        if sys.platform=='darwin':
            util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
        else:
            util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
        try:
            inject_tracking_code(util_file_path)
            savePreferences()
        except Exception as e:
            self.report({'WARNING'},'Please start blender as administrator/superuser (Only required Once)')
            print("Error:",e)
        return {'FINISHED'}
class CP_OT_Inject_Code(bpy.types.Operator):
    bl_idname = "cp.injectcode"
    bl_label = "Enable Ordering"
    bl_description="Pressing this button will insert a few lines of code in the addon_utils module of blender which will enable Clean Panels to work correctly"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls,context):
        return not preferences().injected_code
    def invoke(self, context,event):
        
        version=bpy.app.version
        if sys.platform=='darwin':
            util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
        else:
            util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
        try:
            inject_code(util_file_path)
            preferences().injected_code=True
            savePreferences()
        except Exception as e:
            self.report({'WARNING'},'Please start blender as administrator/superuser (Only required Once)')
            print("Error:",e)
        return {'FINISHED'}
class CP_OT_Save_Config(bpy.types.Operator):
    bl_idname = "cp.saveconfig"
    bl_label = "Save Config"
    bl_description="Save Clean Panels Configuration"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        savePreferences()
        self.report({'INFO'},'Configuration Saved!')
        return {'FINISHED'}
class CP_OT_Export_Config(bpy.types.Operator,ExportHelper):
    bl_idname = "cp.exportconfig"
    bl_label = "Export Config"
    bl_description="Export Config File"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        subtype='FILE_PATH',
    )
    filename_ext:bpy.props.StringProperty(default=".txt",options={'SKIP_SAVE','HIDDEN'})
    def execute(self, context):
        savePreferences()
        path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")
        if os.path.isfile(path):
            shutil.copy(path,self.filepath)
        return {'FINISHED'}
class CP_OT_Import_Config(bpy.types.Operator,ImportHelper):
    bl_idname = "cp.importconfig"
    bl_label = "Import Config"
    bl_description="Import Config File"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = '.txt'
    
    filter_glob: bpy.props.StringProperty(
        default='*.txt',
        options={'HIDDEN'}
    )
    def execute(self, context):
        path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")
        if os.path.isfile(self.filepath):
            data=None
            with open(self.filepath,mode='r',encoding='utf8',newline='\n') as f:
                data=f.readlines()
            if data:
                with open(path,mode='w',encoding='utf8',newline='\n') as f:
                    f.writelines(data)
        loadPreferences()
        return {'FINISHED'}
class CP_OT_Clear_Order(bpy.types.Operator):
    bl_idname = "cp.clearforcedorders"
    bl_label = "Clear Forced Order (Experimental)"
    bl_description="Clear Forced N-Panel orders\nCTRL+LMB:Reset"
    bl_options = {'REGISTER', 'UNDO'}
    # @classmethod
    # def poll(cls,context):
    #     return preferences().addon_info and preferences().addon_info[preferences().addon_info_index] and preferences().addon_info[preferences().addon_info_index].ordered
    def invoke(self, context,event):
        if event.ctrl:
            clean_all_python_files(remove=True)
        else:
            if preferences().addon_info and preferences().addon_info[preferences().addon_info_index] and preferences().addon_info[preferences().addon_info_index].ordered:
                clean_all_python_files(remove=False)
                
                
        #reorder_addons(None)
        savePreferences()
        return {'FINISHED'}
class CP_OT_Change_Category(bpy.types.Operator):
    bl_idname = "cp.changecategory"
    bl_label = "Update Category in source file"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def description(self, context,properties):
        if preferences().filtering_method=="Use N-Panel Filtering":
            return "Confirm New Tab Names"
        else:
            return "Set new Tab(This will edit the python files of the addon and replace the panel names with the new name)\nCTRL+LMB:Reset\nSHIFT+LMB:Set for All"
    # @classmethod
    # def poll(cls,context):
    #     return preferences().addon_info and preferences().addon_info[preferences().addon_info_index] and preferences().addon_info[preferences().addon_info_index].ordered
    def invoke(self, context,event):
        if not preferences().filtering_method=="Use N-Panel Filtering":
            if event.ctrl:
                if event.shift:
                    for i in range(len(preferences().addon_info_for_renaming)):
                        change_category(i,True)   
                else:
                    change_category(preferences().addon_info_for_renaming_index,True)
            else:
                if event.shift:
                    for i in range(len(preferences().addon_info_for_renaming)):
                        change_category(i,False)   
                else:
                    change_category(preferences().addon_info_for_renaming_index,False)  
        else:
            workspace_category_enabled(preferences().categories,context)                
        #reorder_addons(None)
        savePreferences()
        return {'FINISHED'}
class CP_OT_Move_Category(bpy.types.Operator):
    bl_idname = "cp.movecategory"
    bl_label = ""
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    direction: bpy.props.StringProperty(default="UP",options={'SKIP_SAVE','HIDDEN'})
    index: bpy.props.IntProperty()
    category: bpy.props.StringProperty()
    @classmethod
    def description(cls,context,properties):
        if properties.direction=='UP':
            return "Move Up\nCTRL+LMB:Move to Top"
        else:
            return "Move Down\nCTRL+LMB:Move to Bottom"
    def invoke(self, context,event):
        if self.direction=='UP':
            if self.index==0:
                return {'CANCELLED'}
        else:
            if self.category=='Pie':
                if self.index+1>=len(preferences().panel_categories):
                    return {'CANCELLED'}
            elif self.category=='DropDown':
                if self.index+1>=len(preferences().dropdown_categories):
                    return {'CANCELLED'}
            else:
                if self.index+1>=len(preferences().workspace_categories):
                    return {'CANCELLED'}
        if self.category=='Pie':
             
            
            if self.direction=='UP':
                for index in range(self.index,0 if event.ctrl else self.index-1,-1):
                    temp_name=preferences().panel_categories[index-1].name
                    temp_panels=preferences().panel_categories[index-1].panels
                    preferences().panel_categories[index-1].name=preferences().panel_categories[index].name
                    preferences().panel_categories[index-1].panels=preferences().panel_categories[index].panels
                    preferences().panel_categories[index].name=temp_name
                    preferences().panel_categories[index].panels=temp_panels
            else:
                for index in range(self.index,len(preferences().panel_categories)-1 if event.ctrl else self.index+1):
                    temp_name=preferences().panel_categories[index+1].name
                    temp_panels=preferences().panel_categories[index+1].panels
                    preferences().panel_categories[index+1].name=preferences().panel_categories[index].name
                    preferences().panel_categories[index+1].panels=preferences().panel_categories[index].panels
                    preferences().panel_categories[index].name=temp_name
                    preferences().panel_categories[index].panels=temp_panels
        elif self.category=='DropDown':
            if self.direction=='UP':
                for index in range(self.index,0 if event.ctrl else self.index-1,-1):
                    temp_name=preferences().dropdown_categories[index-1].name
                    temp_panels=preferences().dropdown_categories[index-1].panels
                    preferences().dropdown_categories[index-1].name=preferences().dropdown_categories[index].name
                    preferences().dropdown_categories[index-1].panels=preferences().dropdown_categories[index].panels
                    preferences().dropdown_categories[index].name=temp_name
                    preferences().dropdown_categories[index].panels=temp_panels
            else:
                for index in range(self.index,len(preferences().dropdown_categories)-1 if event.ctrl else self.index+1):
                    temp_name=preferences().dropdown_categories[index+1].name
                    temp_panels=preferences().dropdown_categories[index+1].panels
                    preferences().dropdown_categories[index+1].name=preferences().dropdown_categories[index].name
                    preferences().dropdown_categories[index+1].panels=preferences().dropdown_categories[index].panels
                    preferences().dropdown_categories[index].name=temp_name
                    preferences().dropdown_categories[index].panels=temp_panels
        else:
            if self.direction=='UP':
                for index in range(self.index,0 if event.ctrl else self.index-1,-1):
                    temp_name=preferences().workspace_categories[index-1].name
                    temp_panels=preferences().workspace_categories[index-1].panels
                    temp_icon=preferences().workspace_categories[index-1].icon
                    preferences().workspace_categories[index-1].name=preferences().workspace_categories[index].name
                    preferences().workspace_categories[index-1].panels=preferences().workspace_categories[index].panels
                    preferences().workspace_categories[index-1].icon=preferences().workspace_categories[index].icon
                    preferences().workspace_categories[index].name=temp_name
                    preferences().workspace_categories[index].panels=temp_panels
                    preferences().workspace_categories[index].icon=temp_icon
            else:
                for index in range(self.index,len(preferences().workspace_categories)-1 if event.ctrl else self.index+1):
                    temp_name=preferences().workspace_categories[index+1].name
                    temp_panels=preferences().workspace_categories[index+1].panels
                    temp_icon=preferences().workspace_categories[index+1].icon
                    preferences().workspace_categories[index+1].name=preferences().workspace_categories[index].name
                    preferences().workspace_categories[index+1].panels=preferences().workspace_categories[index].panels
                    preferences().workspace_categories[index+1].icon=preferences().workspace_categories[index].icon
                    preferences().workspace_categories[index].name=temp_name
                    preferences().workspace_categories[index].panels=temp_panels
                    preferences().workspace_categories[index].icon=temp_icon
        savePreferences()
        return {'FINISHED'}
class CP_OT_Move_Addon_In_Category(bpy.types.Operator):
    bl_idname = "cp.moveaddonincategory"
    bl_label = "Move"
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    direction: bpy.props.StringProperty(default="UP",options={'SKIP_SAVE','HIDDEN'})
    
    def invoke(self, context,event):
        scene= context.scene
        
        index=scene.addon_info_index
        if self.direction=='UP':
            if scene.addon_info_index>0:
                temp_name=scene.addon_info[index-1].name
                temp_addons=scene.addon_info[index-1].addons
                temp_ordered=scene.addon_info[index-1].ordered
                scene.addon_info[index-1].name=scene.addon_info[index].name
                scene.addon_info[index-1].addons=scene.addon_info[index].addons
                scene.addon_info[index-1].ordered=scene.addon_info[index].ordered
                scene.addon_info[index].name=temp_name
                scene.addon_info[index].addons=temp_addons
                scene.addon_info[index].ordered=temp_ordered
                scene.addon_info_index-=1
        else:
            if scene.addon_info_index<len(scene.addon_info)-1:
                temp_name=scene.addon_info[index+1].name
                temp_addons=scene.addon_info[index+1].addons
                temp_ordered=scene.addon_info[index+1].ordered
                scene.addon_info[index+1].name=scene.addon_info[index].name
                scene.addon_info[index+1].addons=scene.addon_info[index].addons
                scene.addon_info[index+1].ordered=scene.addon_info[index].ordered
                scene.addon_info[index].name=temp_name
                scene.addon_info[index].addons=temp_addons
                scene.addon_info[index].ordered=temp_ordered
                scene.addon_info_index+=1
        savePreferences()
        return {'FINISHED'}
class CP_OT_Move_Addon(bpy.types.Operator):
    bl_idname = "cp.moveaddon"
    bl_label = "Move"
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    direction: bpy.props.StringProperty(default="UP",options={'SKIP_SAVE','HIDDEN'})
    
    def invoke(self, context,event):
        index=preferences().addon_info_index
        if self.direction=='UP':
            if preferences().addon_info_index>0:
                temp_name=preferences().addon_info[index-1].name
                temp_addons=preferences().addon_info[index-1].addons
                temp_ordered=preferences().addon_info[index-1].ordered
                preferences().addon_info[index-1].name=preferences().addon_info[index].name
                preferences().addon_info[index-1].addons=preferences().addon_info[index].addons
                preferences().addon_info[index-1].ordered=preferences().addon_info[index].ordered
                preferences().addon_info[index].name=temp_name
                preferences().addon_info[index].addons=temp_addons
                preferences().addon_info[index].ordered=temp_ordered
                preferences().addon_info_index-=1
        else:
            if preferences().addon_info_index<len(preferences().addon_info)-1:
                temp_name=preferences().addon_info[index+1].name
                temp_addons=preferences().addon_info[index+1].addons
                temp_ordered=preferences().addon_info[index+1].ordered
                preferences().addon_info[index+1].name=preferences().addon_info[index].name
                preferences().addon_info[index+1].addons=preferences().addon_info[index].addons
                preferences().addon_info[index+1].ordered=preferences().addon_info[index].ordered
                preferences().addon_info[index].name=temp_name
                preferences().addon_info[index].addons=temp_addons
                preferences().addon_info[index].ordered=temp_ordered
                preferences().addon_info_index+=1
        savePreferences()
        return {'FINISHED'}
class PAP_Panel_Category(PropertyGroup):
    #enabled: bpy.props.BoolProperty(default=False,update=workspace_category_enabled)
    icon: bpy.props.StringProperty(default="COLLAPSEMENU",update=savePreferences)
    panels: bpy.props.StringProperty(default="",name="Panels",update=savePreferences)
    name: bpy.props.StringProperty(default="Category",name="Name",update=savePreferences)



    #change_category(preferences().addon_info_for_renaming_index)

class Category_Indices(PropertyGroup):
    filter_enabled: bpy.props.BoolProperty(default=False,update=workspace_category_enabled,name="Filter")
    enabled_0: bpy.props.BoolProperty(default=False)
    enabled_1: bpy.props.BoolProperty(default=False)
    enabled_2: bpy.props.BoolProperty(default=False)
    enabled_3: bpy.props.BoolProperty(default=False)
    enabled_4: bpy.props.BoolProperty(default=False)
    enabled_5: bpy.props.BoolProperty(default=False)
    enabled_6: bpy.props.BoolProperty(default=False)
    enabled_7: bpy.props.BoolProperty(default=False)
    enabled_8: bpy.props.BoolProperty(default=False)
    enabled_9: bpy.props.BoolProperty(default=False)
    enabled_10: bpy.props.BoolProperty(default=False)
    enabled_11: bpy.props.BoolProperty(default=False)
    enabled_12: bpy.props.BoolProperty(default=False)
    enabled_13: bpy.props.BoolProperty(default=False)
    enabled_14: bpy.props.BoolProperty(default=False)
    enabled_15: bpy.props.BoolProperty(default=False)
    enabled_16: bpy.props.BoolProperty(default=False)
    enabled_17: bpy.props.BoolProperty(default=False)
    enabled_18: bpy.props.BoolProperty(default=False)
    enabled_19: bpy.props.BoolProperty(default=False)
    enabled_20: bpy.props.BoolProperty(default=False)
    enabled_21: bpy.props.BoolProperty(default=False)
    enabled_22: bpy.props.BoolProperty(default=False)
    enabled_23: bpy.props.BoolProperty(default=False)
    enabled_24: bpy.props.BoolProperty(default=False)
    enabled_25: bpy.props.BoolProperty(default=False)
    enabled_26: bpy.props.BoolProperty(default=False)
    enabled_27: bpy.props.BoolProperty(default=False)
    enabled_28: bpy.props.BoolProperty(default=False)
    enabled_29: bpy.props.BoolProperty(default=False)
    enabled_30: bpy.props.BoolProperty(default=False)
    enabled_31: bpy.props.BoolProperty(default=False)
    enabled_32: bpy.props.BoolProperty(default=False)
    enabled_33: bpy.props.BoolProperty(default=False)
    enabled_34: bpy.props.BoolProperty(default=False)
    enabled_35: bpy.props.BoolProperty(default=False)
    enabled_36: bpy.props.BoolProperty(default=False)
    enabled_37: bpy.props.BoolProperty(default=False)
    enabled_38: bpy.props.BoolProperty(default=False)
    enabled_39: bpy.props.BoolProperty(default=False)
    enabled_40: bpy.props.BoolProperty(default=False)
    enabled_41: bpy.props.BoolProperty(default=False)
    enabled_42: bpy.props.BoolProperty(default=False)
    enabled_43: bpy.props.BoolProperty(default=False)
    enabled_44: bpy.props.BoolProperty(default=False)
    enabled_45: bpy.props.BoolProperty(default=False)
    enabled_46: bpy.props.BoolProperty(default=False)
    enabled_47: bpy.props.BoolProperty(default=False)
    enabled_48: bpy.props.BoolProperty(default=False)
    enabled_49: bpy.props.BoolProperty(default=False)
class PAPPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__
    auto_backup_addons: bpy.props.BoolProperty(default=False,name="Automatically Backup addons before making changes",description=f"Create automatic backups while editing the addon files (for N-Panel renaming and clearing forced orders)\n Stored at: {os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'Addon-Backups-CleanPanels')}")
    show_panel_pies: bpy.props.BoolProperty(default=False, name="Panels and Pies")
    pop_out_style:bpy.props.EnumProperty(items=(("Pie-PopUp","Pie-PopUp","Pie-PopUp"),("DropDown","DropDown","DropDown")),default=0,name="PopUp Panel Style",update=savePreferences)
    panel_categories : bpy.props.CollectionProperty(type=PAP_Panel_Category)
    dropdown_categories : bpy.props.CollectionProperty(type=PAP_Panel_Category)
    workspace_categories: bpy.props.CollectionProperty(type=PAP_Panel_Category)
    show_panel_categories: bpy.props.BoolProperty(default=False,name="Pie Panels")
    show_dropdown_categories: bpy.props.BoolProperty(default=False,name="Dropdown Panels")
    show_workspace_categories: bpy.props.BoolProperty(default=False, name="Workspace Addon Categories")
    show_npanel_ordering: bpy.props.BoolProperty(default=False,name="N-Panel ReOrdering")
    show_npanel_renaming: bpy.props.BoolProperty(default=False,name="N-Panel Renaming")
    draw_side: bpy.props.EnumProperty(name="Direction",items=(("LEFT",'Left','Left'),("RIGHT",'Right','Right')),update=draw_side_changed)
    addons_to_exclude: bpy.props.StringProperty(default="",name="Addons To Exclude (Will always be available)",update=exclusion_list_changed)
    experimental:bpy.props.BoolProperty(default=False,name="Experimental Features",update=savePreferences)
    addon_info:bpy.props.CollectionProperty(type=AddonInfo)
    addon_info_for_renaming:bpy.props.CollectionProperty(type=AddonInfoRename)
    use_sticky_popup: bpy.props.BoolProperty(default=True,name="Use Sticky Popups",update=savePreferences)
    addon_info_index: bpy.props.IntProperty(default=0,name="Selected Tab")
    addon_info_for_renaming_index: bpy.props.IntProperty(default=0,name="Selected Addon")
    injected_code: bpy.props.BoolProperty(default=check_for_injection())
    injected_code_tracking: bpy.props.BoolProperty(default=check_for_tracking_injection())
    columm_layout_for_popup: bpy.props.BoolProperty(default=True,name="Use Column Layout (Dropdowns will be stacked)",update=savePreferences)
    use_verticle_menu: bpy.props.BoolProperty(default=True,name="Use list instead of 2nd pie menu")
    dropdown_width: bpy.props.IntProperty(default=16,name="Dropdown Width",min=5,max=50)
    show_dropdown_search: bpy.props.BoolProperty(default=False,name="Show Dropdown search button")
    categories:bpy.props.PointerProperty(type=Category_Indices)
    #filtering_method: bpy.props.BoolProperty(default=False,name="Use Unregister/Reregister Method for filtering (Restart after changing this)")
    filtering_method: bpy.props.EnumProperty(items=(("Use Workspace Filtering","Use Workspace Filtering","Use Workspace Filtering"),("Use N-Panel Filtering","Use N-Panel Filtering","Use N-Panel Filtering")),default=1,name="How to clean the N-Panel (Restart after changing this)")
    show_advanced: bpy.props.BoolProperty(default=False,name='Show Advanced Options')
    use_dropdowns: bpy.props.BoolProperty(default=True,name="Show Dropdowns")
    sort_per_category:bpy.props.BoolProperty(default=False,name="Sort Panels per Category",description="Sort Panels based on the order specified in the categories")
    holder_tab_name: bpy.props.StringProperty(default="DUMP",name="Tab name for filtered out addons")
    def draw(self, context):
        
        layout2 = draw_settings(self,self,context)
        layout3=layout2.box()
        #layout3.operator("cp.saveconfig",icon='FILE_TICK')
        row= layout3.row(align=True)

        row.operator("cp.exportconfig",icon='EXPORT')
        row.operator("cp.importconfig",icon='IMPORT')
        pcoll = icon_collection["icons"]
        youtube_icon = pcoll["youtube"]
        discord_icon=pcoll["discord"]
        green=pcoll["updategreen"]
        red=pcoll["updatered"]
        box=layout2.box()
        box.label(text=context.scene.cp_update_status,icon_value=green.icon_id if 'Clean Panels is Up To Date!' in context.scene.cp_update_status  else red.icon_id)
        row=box.row()
        row.operator('wm.url_open',text="Documentation",icon="HELP").url="https://cleanpanels.notion.site/Clean-Panels-Wiki-487866054aa54ac583c1ece88a7c6f0c"
        row=box.row(align=True)
        row.operator('wm.url_open',text="Chat Support",icon_value=discord_icon.icon_id).url="https://discord.gg/Ta4P3uJXtQ"
        row.operator('wm.url_open',text="Youtube",icon_value=youtube_icon.icon_id).url="https://www.youtube.com/channel/UCKgXKh-_kOgzdV8Q12kraHA"
class PAP_Import_Workspaces(bpy.types.Operator):
    bl_idname = "cp.importworkspaces"
    bl_label = "Import Workspaces as Categories"
    bl_description="Create categories from all available workspaces which have filtering enabled"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()
    def invoke(self, context, event):
        for w in bpy.data.workspaces:
            if w.use_filter_by_owner:
                t=preferences().workspace_categories.add()
                t.name=w.name
                t.panels=",".join([c.name for c in w.owner_ids if c.name not in preferences().addons_to_exclude.split(',')+addons_to_exclude])
        savePreferences()
        return {"FINISHED"}
    