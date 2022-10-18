import os
import bpy
import re
import sys
import addon_utils
from datetime import datetime
import bpy.utils.previews
import inspect
from bpy.app.handlers import persistent
exceptional_names={'gui':'blender-osm','ape':'blender-osm'}
LOGGING=True
def log(*args):
    if LOGGING:
        print(*args)
def preferences():
    return bpy.context.preferences.addons[__package__].preferences
regex=re.compile("^\s*bl_category\s*=\s*.+")
def change_category(index,remove=False):
    #directory=os.path.dirname(os.path.dirname(__file__))
    directories=[]
    addons=[]
    a=preferences().addon_info_for_renaming[index]
    
    #print(addons)
    addons=[a.name,]
    new_category=a.tab_name
    #print(a.name,a.tab_name)
    for mod in addon_utils.modules():
        if mod.__name__ in addons:
            version=bpy.app.version
            addon_dir_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","addons")
            directories.append(os.path.dirname(mod.__file__) if os.path.dirname(mod.__file__)!=os.path.dirname(os.path.dirname(__file__)) and os.path.dirname(mod.__file__)!=addon_dir_path else mod.__file__)
            
        else:
            pass
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels"))
    for directory in directories:
        if os.path.isfile(directory):
            if not remove and preferences().auto_backup_addons:
                shutil.copy(directory, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
                print("Creating Backup....\n", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
            f=directory
            #print(f)
            try:
                data=[]
                with open(f,mode='r') as file:
                    replaced=False
                    while True:
                        line=file.readline()
                        if not line:
                            break
                        if remove:
                            if not "#--changed-by-CleanPanels--" in line:
                                replaced=True
                                data.append(line.replace("#--category-editied-by-CleanPanels--",""))
                            
                        else:
                            
                            match=regex.search(line)
                            if  ("bl_category" in line and new_category in line):
                                data.append(line)
                            else:
                                if "#--changed-by-CleanPanels--" not in line:
                                    
                                    if match:
                                        replaced=True
                                        data.append(line.replace("bl_category","#--category-editied-by-CleanPanels--bl_category"))
                                    else:
                                        data.append(line)
                            if match and not  ("bl_category" in line and new_category in line):
                                print("Replacing :",line)
                                replaced=True
                                data.append(line[:line.index("bl_category")]+f"bl_category='{new_category}'#--changed-by-CleanPanels--\n")
                if data:
                    if replaced:
                        with open(f,mode='w') as file:
                                file.writelines(data)
            except Exception as e:
                log("Error in file",f,'\n',e)
        else:
            #print(directory,os.path.dirname(os.path.dirname(__file__)))
            if directory!=os.path.dirname(os.path.dirname(__file__)):
                
                if not remove and preferences().auto_backup_addons:
                    dest_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.basename(directory)+str(datetime.now().strftime(r' %d-%m-%Y %H %M')))
                    if not os.path.isdir(dest_path):
                        shutil.copytree(directory, dest_path)
                        print("Creating Backup....\n", dest_path)
                for f in get_all_python_files(directory):
                    #print(f)
                    try:
                        data=[]
                        with open(f,mode='r') as file:
                            replaced=False
                            while True:
                                line=file.readline()
                                if not line:
                                    break
                                if remove:
                                    if not "#--changed-by-CleanPanels--" in line:
                                        replaced=True
                                        data.append(line.replace("#--category-editied-by-CleanPanels--",""))
                                    
                                else:
                                    match=regex.search(line)
                                    if  ("bl_category" in line and new_category in line):
                                        data.append(line)
                                    else:
                                        if "#--changed-by-CleanPanels--" not in line:
                                            
                                            if match:
                                                replaced=True
                                                data.append(line.replace("bl_category","#--category-editied-by-CleanPanels--bl_category"))
                                            else:
                                                data.append(line)
                                    if match and not  ("bl_category" in line and new_category in line):
                                        print("Replacing :",line)
                                        replaced=True
                                        data.append(line[:line.index("bl_category")]+f"bl_category='{new_category}'#--changed-by-CleanPanels--\n")
                        if data:
                            if replaced:
                                with open(f,mode='w') as file:
                                        file.writelines(data)
                    except Exception as e:
                        log("Error in file",f,'\n',e)
def get_installed_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in preferences().addons_to_exclude.split(",")+addons_to_exclude and a not in preferences().workspace_categories[self.index].panels.split(","):
                mod = sys.modules[a]
                addons.append(mod.bl_info.get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def get_all_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in preferences().addons_to_exclude.split(",")+addons_to_exclude:
                mod = sys.modules[a]
                addons.append(mod.bl_info.get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def get_all_addons(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in preferences().addons_to_exclude.split(",")+addons_to_exclude:
                mod = sys.modules[a]
                addons.append((mod.bl_info.get('name', "Unknown"),mod.bl_info.get('description', "")))
        except:
            pass
    addons=sorted(addons,key=lambda x:x[0].lower())
    return [(a,f"{a}",a) for a,b in addons]+[("Unfiltered","Unfiltered","Unfiltered"),]
def get_installed_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in preferences().addons_to_exclude.split(",")+addons_to_exclude and a not in preferences().workspace_categories[self.index].panels.split(","):
                mod = sys.modules[a]
                addons.append(mod.bl_info.get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def get_installed_addons(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            mod = sys.modules[a]
            a=mod.bl_info.get('name', "Unknown")
            if a not in preferences().addons_to_exclude.split(",")+addons_to_exclude and a not in preferences().workspace_categories[self.index].panels.split(","):
                
                addons.append(a)
                #addons.append(a)
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return [(a,a,a) for a in addons]+[("All",'All','All'),("Unfiltered","Unfiltered","Unfiltered")]
def get_module_name_from_addon_name(name):
    for a in bpy.context.preferences.addons.keys():
        try:
            if name==a:
                return a
            mod = sys.modules[a]
            if mod.bl_info.get('name', "Unknown")==name:
                return a
        except:
            pass
    return "--Unknown--"
def get_all_panel_categories(self, context):
    cat=set()
    base_type = bpy.types.Panel
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                    if getattr(bl_type,'backup_category',None):
                        cat.add(getattr(bl_type,'backup_category',None))
                    if getattr(bl_type,'bl_category',None):
                        cat.add(getattr(bl_type,'bl_category',None))
                    #cat.add(getattr(bl_type,'backup_category',None) if getattr(bl_type,'backup_category',None) else getattr(bl_type,'bl_category',"None"))
        except:
            pass
    cat=[a for a in cat if a!=preferences().holder_tab_name and a!='None']
    cat=sorted(cat)
    return [(a,a,a) for a in cat]
def get_panel_categories(self, context):
    cat=set()
    base_type = bpy.types.Panel
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if self.category=='Dropdown':
                    if getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                        if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in preferences().dropdown_categories[self.index].panels.split(","):
                            cat.add(getattr(bl_type,'bl_category',"None"))
                        if getattr(bl_type,'backup_category',None) and  getattr(bl_type,'backup_category',"None") not in preferences().dropdown_categories[self.index].panels.split(","):
                            
                            cat.add(getattr(bl_type,'backup_category',"None"))
                elif self.category =='Pie':
                    if getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                        if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in preferences().panel_categories[self.index].panels.split(","):
                            cat.add(getattr(bl_type,'bl_category',"None"))
                        
                        if getattr(bl_type,'backup_category',None) and getattr(bl_type,'backup_category',"None") not in preferences().panel_categories[self.index].panels.split(","):
                            cat.add(getattr(bl_type,'backup_category',"None"))
        except:
            pass
    cat=sorted(cat)
    return [(a,a,a) for a in cat]
#addons_to_exclude=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'pose_library','node_wrangler', 'node_arrange', 'node_presets','mesh_looptools', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator']
addons_to_exclude=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'pose_library','node_wrangler', 'node_arrange', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs', 'add_curve_ivygen','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'Align And Distribute', 'blender_id,btrace', 'curve_tools', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'mesh_tools', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'Modifier Shortcut Keys', 'object_fracture_cell', 'object_edit_linked', 'object_scatter', 'object_skinify', 'object_boolean_tools', 'render_copy_settings', 'space_view3d_stored_views', 'space_view3d_3d_navigation', 'space_view3d_align_tools', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']

def get_all_python_files(dir_path):
    pyfiles = []
    for path, subdirs, files in os.walk(dir_path):
        for name in files:
            if name.endswith('.py') and os.path.join(path, name)!=__file__:
                pyfiles.append(os.path.join(path, name))
                #print(os.path.join(path, name))
    return pyfiles
import shutil
def get_icons(self, context):
    icons=bpy.types.UILayout.bl_rna.functions[
                "prop"].parameters["icon"].enum_items.keys()
    return [(a,a,a,a,i) for i,a in enumerate(icons)] 
ALL_ICONS_ENUM=get_icons(None,None)
ALL_ICONS=[a for a,_,_,_,_ in get_icons(None,None)]
def clean_all_python_files(remove=False):
    #directory=os.path.dirname(os.path.dirname(__file__))
    directories=[]
    addons=[]
    a=preferences().addon_info[preferences().addon_info_index]
    if remove:
        if a.addons:
            addons.extend(a.addons.split(","))
    else:
        if a.ordered:
            addons.extend(a.ordered.split(","))
    #print(addons)
    for mod in addon_utils.modules():
        if mod.__name__ in addons:
            directories.append(os.path.dirname(mod.__file__) if os.path.dirname(mod.__file__)!=os.path.dirname(os.path.dirname(__file__)) else mod.__file__)
            
        else:
            pass
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels"))
    for directory in directories:
        if os.path.isfile(directory):
            if not remove and preferences().auto_backup_addons:
                shutil.copy(directory, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
                print("Creating Backup....\n", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
            f=directory
            #print(f)
            try:
                data=[]
                with open(f,mode='r') as file:
                    while True:
                        line=file.readline()
                        if not line:
                            break
                        if remove:
                            data.append(line.replace("#--editied-by-CleanPanels--",""))
                        else:
                            data.append(line.replace("bl_order","#--editied-by-CleanPanels--bl_order"))
                if data:
                    with open(f,mode='w') as file:
                            file.writelines(data)
            except Exception as e:
                log("Error in file",f,'\n',e)
        else:
            #print(directory,os.path.dirname(os.path.dirname(__file__)))
            if directory!=os.path.dirname(os.path.dirname(__file__)):
                if not remove and preferences().auto_backup_addons:
                    dest_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.basename(directory)+str(datetime.now().strftime(r' %d-%m-%Y %H %M')))
                    if not os.path.isdir(dest_path):
                        shutil.copytree(directory, dest_path)
                        print("Creating Backup....\n", dest_path)
                for f in get_all_python_files(directory):
                    #print(f)
                    try:
                        data=[]
                        with open(f,mode='r') as file:
                            while True:
                                line=file.readline()
                                if not line:
                                    break
                                if remove:
                                    data.append(line.replace("#--editied-by-CleanPanels--",""))
                                else:
                                    data.append(line.replace("bl_order","#--editied-by-CleanPanels--bl_order"))
                        if data:
                            with open(f,mode='w') as file:
                                    file.writelines(data)
                    except Exception as e:
                        log("Error in file",f,'\n',e)
import time
import numpy as np
def sort_panels2(panels,order):
    # st=time.time()
    sorted=[]
    used=[]
    bl_types=[a[1] for a in panels]
    order=[a.replace("\n","") for a in order if a in bl_types]
    for o in order:
        for b,p in panels:
            if p.__name__==o and p not in used:
                used.append(p)
                sorted.append((b,p))
                break
    for b,p in panels:
        if p not in used:
            sorted.append((b,p))
    # print(time.time()-st)        
    return sorted
def sort_by_another_list(source_list,ordered_list):
    keys = { ordered_list[i]: i for i in range(len(ordered_list)) }
    sorted_list = sorted(source_list, key=lambda x: keys[x] if x in keys else len(source_list)+1)   
    return sorted_list
def sort_panels(panels,order):
    # names=[a[0] for a in panels]
    # bl_types=[a[1] for a in panels]
    st=time.time()
    
    
    # sorted=[a for a in cleaned_order if a in bl_types]
    
    keys = { order[i]: i for i in range(len(order)) }
    sorted_panels = sorted(panels, key=lambda x: keys[x[1].__name__] if x[1].__name__ in keys else len(panels)+1)   
    # print(time.time()-st)
    # used=[]
    # for o in order:
    #     for b,p in panels:
    #         if p.__name__==o.replace("\n","") and p not in used:
    #             used.append(p)
    #             sorted.append((b,p))
    #             break
    # for b,p in panels:
    #     if p not in used:
    #         sorted.append((b,p))
    return sorted_panels
def register_panel(c):
    try: 
        bpy.utils.register_class(c,False)
    except:
        bpy.utils.register_class(c)
def draw_dropdowns(self, context):
    if preferences().use_dropdowns:
        categories=[]
        layout=self.layout.row()
        layout.separator()
        if preferences().show_dropdown_search:
            layout.operator("cp.search_dropdown",icon='VIEWZOOM',text='Search')
        for a in preferences().dropdown_categories:
                if a.name==context.scene.pap_active_dropdown_category:
                    categories=a.panels.split(",")
                    categories=[a.strip() for a in categories]
        for a in categories:
            if a:

                layout.emboss='PULLDOWN_MENU'
                layout.operator("cp.popupcompletepanel",text=a,icon="DOWNARROW_HLT").name=a
def panel_opened(self, context):
    if context.scene.pap_opened_panels.find(self.name)>=0:
        t=context.scene.pap_opened_panels[context.scene.pap_opened_panels.find(self.name)]
    else:
        t=context.scene.pap_opened_panels.add()
        t.name=self.name
    t.opened_before=True
    t.pap_opened_panels=""
    for i in range(1,39):
        if getattr(self,f"show_panel_{i}",False):
            t.pap_opened_panels=t.pap_opened_panels+","+str(i) if t.pap_opened_panels else str(i)

def get_current_context(context):
    if context.mode=='OBJECT':
        return "objectmode"
    elif context.mode =='EDIT_MESH':
        return "mesh_edit"
    elif context.mode =='EDIT_CURVE':
        return "curve_edit"
    elif context.mode =='EDIT_SURFACE':
        return "surface_edit"
    elif context.mode =='EDIT_TEXT':
        return "text_edit"
    elif context.mode =='SCULPT':
        return "sculpt_mode"
    elif context.mode =='EDIT_ARMATURE':
        return "armature_edit"
    elif context.mode =='EDIT_METABALL':
        return "mball_edit"
    elif context.mode =='EDIT_LATTICE':
        return "lattice_edit"
    elif context.mode =='POSE':
        return "posemode"
    elif context.mode =='PAINT_WEIGHT':
        return "weightpaint"
    elif context.mode =='PAINT_VERTEX':
        return "vertexpaint"
    elif context.mode =='PAINT_TEXTURE':
        return "imagepaint"
    elif context.mode =='PARTICLE':
        return "particlemode"
    else:
        return "None1"
def check_for_injection():
    version=bpy.app.version
    if sys.platform=='darwin':
        util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    else:
        util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    if os.path.isfile(util_file_path):
        with open(util_file_path,mode='r') as f:
            text=f.read()
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")
            if path in text:
                return True
    return False
def check_for_tracking_injection():
    version=bpy.app.version
    if sys.platform=='darwin':
        util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
    else:
        util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
    if os.path.isfile(util_file_path):
        with open(util_file_path,mode='r') as f:
            text=f.read()
            path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-PanelOrder.txt")
            if path in text:
                return True
    return False
def get_module_name(bl_type):
    package_name=inspect.getmodule(bl_type).__name__
    if "." in package_name:
        name=package_name[:package_name.index(".")]
    else:
        name=package_name
    if name in exceptional_names.keys():
        name=exceptional_names[name]
    return name

def change_panel_category(old_name,new_name):
    registered_panels=[]
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, bpy.types.Panel):
                registered_panels.append(bl_type)
                if not getattr(bl_type,'backup_category',None) and getattr(bl_type,'bl_category'):
                    bl_type.backup_category=bl_type.bl_category
        except:
            pass
    config_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config","CP-PanelOrder.txt")
    order_of_panels=[]
    if os.path.isfile(config_path):
        with open(config_path, mode='r', newline='\n', encoding='utf-8') as file:
            order_of_panels=file.readlines()
    cleaned_order=[]

    if hasattr(bpy.utils,'panels'):
        if len(getattr(bpy.utils,'panels',[]))>len(order_of_panels):
            order_of_panels=getattr(bpy.utils,'panels',[])
    for o in order_of_panels:
        if o.replace("\n","") not in cleaned_order:
            cleaned_order.append(o.replace("\n",""))
    order_of_panels=cleaned_order
    categories=[]
    for a in preferences().addons_to_exclude.split(",")+addons_to_exclude:
        try:
            if get_module_name_from_addon_name(a)!='--Unknown--':
                categories.append(get_module_name_from_addon_name(a))
        except:
            pass
    for index,a in enumerate(preferences().workspace_categories):
        if getattr(preferences().categories,f'enabled_{index}',False):
            #if a.name==context.workspace.pap_active_workspace_category:
                #categories_string= ''.join(a.panels.split())
                categories_string=a.panels.split(",")
                #categories.extend([a.strip() for a in categories_string])
                categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
    panels_to_reregister=[]
    parents=[]
    children=[]
    parents_to_move_back=[]
    children_to_move_back=[]
    panels_to_move_back=[]
    for bl_type in registered_panels:
        try:
            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
            if "." in package_name:
                name=package_name[:package_name.index(".")]
            else:
                name=package_name
            if name in exceptional_names.keys():
                name=exceptional_names[name]
            try:
                is_panel=False
                try:
                    is_panel=issubclass(bl_type, bpy.types.Panel)
                except:
                    pass                    
                if bl_type and is_panel:
                    if (getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)=='VIEW_3D' and getattr(bl_type,"bl_region_type","None")=='UI' ) and not getattr(bl_type,'bl_parent_id',None):
                        package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                        if "." in package_name:
                            name=package_name[:package_name.index(".")]
                        else:
                            name=package_name
                        if name in exceptional_names.keys():
                            name=exceptional_names[name]
                        if name!="bl_ui":
                            
                            if getattr(bl_type,'bl_category',None)==old_name or(getattr(bl_type,'bl_category',None)==preferences().holder_tab_name and getattr(bl_type,'renamed_category',None)==old_name):
                                #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                
                                #print(bl_type,getattr(bl_type,'backup_category',None))
                                panels_to_reregister.append((name,bl_type))
                                
                            else:
                                if  getattr(bl_type,'bl_category',None)=='Focused':
                                    panels_to_move_back.append((name,bl_type))
                            # bpy.utils.unregister_class(bl_type)  
                            # bpy.utils.register_class(bl_type)
                    else:
                        if bl_type and getattr(bl_type,'bl_parent_id',None):
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=package_name[:package_name.index(".")]
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                            if name!="bl_ui":
                                if getattr(bl_type,'bl_category',None)==old_name or(getattr(bl_type,'renamed_category',None)==old_name):
                                    pass
                                    #print(bl_type.bl_category)
                                    #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    #print(bl_type,getattr(bl_type,'backup_category',None))
                                    parents.append(bl_type.bl_parent_id)
                                    children.append((name,bl_type))
                                    # bpy.utils.unregister_class(bl_type)  
                                    # bpy.utils.register_class(bl_type)
                                else:
                                    if getattr(bl_type,'bl_category',None)=='Focused' :
                                        parents_to_move_back.append(bl_type.bl_parent_id)
                                        children_to_move_back.append((name,bl_type))
            except Exception as e:
                #pass
                print(e)
        except:
            pass
    panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
    children=sort_panels(children,order_of_panels)
    # print(panels_to_reregister)
    # print("")
    # print("")
    # print("")
    # print("")
    # print(children,"Children")
    # print("")
    # print("")
    
    # print(panels_to_move_back)
    for name,p in panels_to_reregister:
        
        if not getattr(p,'backup_category',None):
            p.backup_category=p.bl_category
        p.bl_category=new_name
        try:
            bpy.utils.unregister_class(p)  
            register_panel(p)
        except Exception as e:
            print(e)
    for name,c in children:
        if getattr(c,'bl_category',None):
            if not getattr(c,'backup_category',None):
                c.backup_category=c.bl_category
            c.bl_category=new_name
        try:
            if c.bl_parent_id in parents:
                bpy.utils.unregister_class(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
    for name,c in children:
        if getattr(c,'bl_category',None):
            if not getattr(c,'backup_category',None):
                c.backup_category=c.bl_category
            c.bl_category=new_name
        try:
            if c.bl_parent_id not in parents:
                bpy.utils.unregister_class(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
    for name,p in panels_to_move_back:
        if name in categories:
            if preferences().addon_info_for_renaming.find(name)>=0:
                if getattr(p,'bl_category'):
                    if not getattr(p,'backup_category',None):
                        p.backup_category=p.bl_category
                p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                p.renamed_category=p.bl_category
            else:
                if getattr(p,'backup_category',None):   
                    p.bl_category=getattr(p,'backup_category',None)
        else:
            p.bl_category=preferences().holder_tab_name
            
        try:
            bpy.utils.unregister_class(p)  
            register_panel(p)
        except Exception as e:
            print(e)
    for name,c in children_to_move_back:
                if preferences().addon_info_for_renaming.find(name)>=0:
                    if getattr(c,'bl_category',None):
                        if not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                else:
                    if getattr(c,'backup_category',None):   
                        c.bl_category=getattr(c,'backup_category',None)
                try:
                    if c.bl_parent_id in parents_to_move_back:
                        bpy.utils.unregister_class(c)  
                        register_panel(c)
                except Exception as e:
                            print(e)

    for name,c in children_to_move_back:
        if preferences().addon_info_for_renaming.find(name)>=0:
            if getattr(c,'bl_category',None):
                if not getattr(c,'backup_category',None):
                    c.backup_category=c.bl_category
            c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
            c.renamed_category=c.bl_category
        else:
                if getattr(c,'backup_category',None):   
                    c.bl_category=getattr(c,'backup_category',None)
        try:
            if c.bl_parent_id not in parents_to_move_back:
                bpy.utils.unregister_class(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
icon_collection = {}
def load_icons():
    global icon_collection
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("youtube", os.path.join(my_icons_dir, "Youtube.png"), 'IMAGE')
    pcoll.load("discord", os.path.join(my_icons_dir, "Discord.png"), 'IMAGE')
    pcoll.load("updatered", os.path.join(my_icons_dir, "updatered.png"), 'IMAGE')
    pcoll.load("updategreen", os.path.join(my_icons_dir, "updategreen.png"), 'IMAGE')
    pcoll.load("city", os.path.join(my_icons_dir, "City.png"), 'IMAGE')
    pcoll.load("landscape", os.path.join(my_icons_dir, "landscape.png"), 'IMAGE')
    pcoll.load("animal", os.path.join(my_icons_dir, "Animal.png"), 'IMAGE')
    pcoll.load("tree", os.path.join(my_icons_dir, "Tree.png"), 'IMAGE')
    pcoll.load("car", os.path.join(my_icons_dir, "Car.png"), 'IMAGE')
    pcoll.load("transport", os.path.join(my_icons_dir, "Transport.png"), 'IMAGE')
    pcoll.load("truck", os.path.join(my_icons_dir, "Truck.png"), 'IMAGE')
    pcoll.load("reorder", os.path.join(my_icons_dir, "Reorder.png"), 'IMAGE')
    icon_collection["icons"] = pcoll
prefs_to_save = {
                 'panel_categories':'pc',
                 'pop_out_style':'str',
                 'dropdown_categories':'pc',
                 'workspace_categories':'pc',
                 'addons_to_exclude':'str',
                 'draw_side':'str',
                 'addon_info':'order',
                 'addon_info_for_renaming':'order',
                 'experimental':'bool',
                 'use_sticky_popup':'bool',
                 'columm_layout_for_popup':'str',
                 'use_verticle_menu':'bool',
                 'dropdown_width':'int',
                 'show_dropdown_search':'bool',
                 'auto_backup_addons':'bool',
                 'filtering_method':'str',
                 'show_advanced':'bool',
                 'use_dropdowns':'bool',
                 'sort_per_category':'bool',
                 'holder_tab_name':'str'

}
def savePreferences(self=None,context=None):
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "config"))
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt"), mode='w+', newline='\n', encoding='utf-8') as file:
        for p, t in prefs_to_save.items():
            if p == 'panel_categories':
                for s in preferences().panel_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'dropdown_categories':
                for s in preferences().dropdown_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'workspace_categories':
                for s in preferences().workspace_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}===Icon=>{s.icon}\n")
            elif p == 'addon_info':
                for s in preferences().addon_info:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.addons}===Ordered=>{s.ordered}\n")
            elif p == 'addon_info_for_renaming':
                for s in preferences().addon_info_for_renaming:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.tab_name}\n")
            else:
                file.write(f"{p}=>{t}==={getattr(preferences(),p)}\n")
        order=[]
        for a in preferences().addon_info:
            order.extend(a.addons.split(','))
        #print(order)
        file.write("addon_order=>order===Category>>"+",".join(order)+"\n")

@persistent
def loadPreferences(a=None,b=None):
    all_icons=ALL_ICONS+list(icon_collection["icons"].keys())
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "config"))
    if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt")):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "CP-config.txt"), mode='r', newline='\n', encoding='utf-8') as file:
            prefs = file.readlines()
            preferences().panel_categories.clear()
            preferences().dropdown_categories.clear()
            preferences().workspace_categories.clear()
            preferences().addon_info.clear()
            preferences().addon_info_for_renaming.clear()
            for p in prefs:
                try:
                    attr = p[:p.index("=>")]
                    type = p[p.index("=>")+2:p.index("===")]
                    value = p[p.index("===")+3:]
                    value = value.replace("\n", "")
                    if attr =='panel_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().panel_categories.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='dropdown_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().dropdown_categories.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='workspace_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:value.index("Icon=>")-3]
                        icon=value[value.index("Icon=>")+6:]
                        pc=preferences().workspace_categories.add()
                        pc.name=name
                        pc.panels=panels
                        pc.icon=icon if icon in all_icons else 'NONE'
                    elif attr =='addon_info' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        addons=value[value.index(">>")+2:value.index("Ordered=>")-3]
                        ordered=value[value.index("Ordered=>")+9:]
                        pc=preferences().addon_info.add()
                        pc.name=name
                        pc.addons=addons
                        pc.ordered=ordered
                    elif attr =='addon_info_for_renaming' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        tab_name=value[value.index(">>")+2:]
                        pc=preferences().addon_info_for_renaming.add()
                        pc.name=name
                        pc.tab_name=tab_name
                    elif type=='bool' or type=='int':
                        setattr(preferences(), attr, eval(value))
                    
                    else:
                        
                        setattr(preferences(), attr, value)
                    
                except Exception as e:
                    pass
        setattr(preferences(), 'injected_code', check_for_injection())
        setattr(preferences(), 'injected_code_tracking', check_for_tracking_injection())
def remove_duplicates(list):
    result=[]
    for a in list:
        if a not in result:
            result.append(a)
    return result
def workspace_category_enabled(self, context):
    if not preferences().filtering_method=="Use N-Panel Filtering":
        if self.filter_enabled:
            context.workspace.use_filter_by_owner = True
            categories=[]
            
            for index,a in enumerate(preferences().workspace_categories):
                if getattr(self,f'enabled_{index}',False):
                    #if a.name==context.workspace.pap_active_workspace_category:
                        #categories_string= ''.join(a.panels.split())
                        categories_string=a.panels.split(",")
                        #categories.extend([a.strip() for a in categories_string])
                        categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
            #print(categories)
            for a in [__package__] + categories[:]:
                try:
                    a=sys.modules[a].__name__
                    if a not in [c.name for c in context.workspace.owner_ids]:
                        bpy.ops.wm.owner_enable(owner_id=a)
                except:
                    pass
            for a in preferences().addons_to_exclude.split(",")+addons_to_exclude:
                a=get_module_name_from_addon_name(a)
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
                        if mod.__name__ not in [get_module_name_from_addon_name(a) for a in preferences().addons_to_exclude.split(",")]+addons_to_exclude:
                            #print("Disable",mod.__name__)
                            bpy.ops.wm.owner_disable(owner_id=mod.__name__)
                except:
                        pass
        else:
            context.workspace.use_filter_by_owner = False
    else:
        registered_panels=[]
        for typename in dir(bpy.types):
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, bpy.types.Panel):
                    # if getattr(bl_type,"bl_region_type","None")=='UI' and getattr(bl_type,'bl_space_type',None)=='VIEW_3D':
                    #     registered_panels.append(bl_type)
                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    if "." in package_name:
                        name=package_name[:package_name.index(".")]
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    if name!='bl_ui':
                        registered_panels.append(bl_type)
                        if not getattr(bl_type,'backup_category',None) and getattr(bl_type,'bl_category',None):
                            bl_type.backup_category=bl_type.bl_category
                        if not getattr(bl_type,'renamed_category',None): 
                            if getattr(bl_type,"bl_region_type","None")=='UI' and getattr(bl_type,'bl_space_type',None)=='VIEW_3D':
                                
                                if preferences().addon_info_for_renaming.find(name)>=0 :
                                    bl_type.renamed_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
            except:
                pass
        config_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config","CP-PanelOrder.txt")
        order_of_panels=[]
        if os.path.isfile(config_path):
            with open(config_path, mode='r', newline='\n', encoding='utf-8') as file:
                order_of_panels=file.readlines()
        cleaned_order=[]
        if hasattr(bpy.utils,'panels'):
            if len(getattr(bpy.utils,'panels',[]))>len(order_of_panels):
                order_of_panels=getattr(bpy.utils,'panels',[])
        for o in order_of_panels:
            if o.replace("\n","") not in cleaned_order:
                cleaned_order.append(o.replace("\n",""))
        order_of_panels=cleaned_order
        
        focused_panels=[]
        if self.filter_enabled:
            #context.workspace.use_filter_by_owner = True
            categories=[]
            for a in preferences().addons_to_exclude.split(",")+addons_to_exclude:
                try:
                    if get_module_name_from_addon_name(a)!='--Unknown--':
                        categories.append(get_module_name_from_addon_name(a))
                except:
                    pass
            for index,a in enumerate(preferences().workspace_categories):
                if getattr(self,f'enabled_{index}',False):
                    #if a.name==context.workspace.pap_active_workspace_category:
                        #categories_string= ''.join(a.panels.split())
                        categories_string=a.panels.split(",")
                        #categories.extend([a.strip() for a in categories_string])
                        categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
            
            panels_from_reorder_list=[]
            for a in preferences().addon_info:
                for b in a.addons.split(","):
                    panels_from_reorder_list.append(b)
            panels_from_reorder_list=remove_duplicates(panels_from_reorder_list)
            if not preferences().sort_per_category:
                categories=sort_by_another_list(categories,panels_from_reorder_list)
            modules=[]
            for a in [__package__] + categories[:]:
                try:
                    modules.append(sys.modules[a].__name__)
                except:
                    pass
            panels_to_reregister=[]
            parents=[]
            children=[]
            for bl_type in registered_panels:
                try:
                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    if "." in package_name:
                        name=package_name[:package_name.index(".")]
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    try:                  
                        if bl_type :
                            if (getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)=='VIEW_3D' and getattr(bl_type,"bl_region_type","None")=='UI' ) and not getattr(bl_type,'bl_parent_id',None):
                                package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                if "." in package_name:
                                    name=package_name[:package_name.index(".")]
                                else:
                                    name=package_name
                                if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                if name in modules:
                                    if bl_type.bl_category!='Focused':
                                        bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    if bl_type.bl_category=='Focused':

                                        focused_panels.append((name,bl_type))
                                    else:
                                    #print(bl_type,getattr(bl_type,'backup_category',None))
                                       panels_to_reregister.append((name,bl_type))

                                    # bpy.utils.unregister_class(bl_type)  
                                    # bpy.utils.register_class(bl_type)
                            else:
                                if getattr(bl_type,'bl_parent_id',None) and getattr(bl_type,"bl_region_type","UI")=='UI':
                                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                    if "." in package_name:
                                        name=package_name[:package_name.index(".")]
                                    else:
                                        name=package_name
                                    if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                    if name in modules:
                                        #print(bl_type.bl_category)
                                        #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                        #print(bl_type,getattr(bl_type,'backup_category',None))
                                        
                                        children.append((name,bl_type))
                                        parents.append(bl_type.bl_parent_id)
                                        # bpy.utils.unregister_class(bl_type)  
                                        # bpy.utils.register_class(bl_type)
                    except Exception as e:
                        pass
                        #print(e)
                except:
                    pass
            panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
            children=sort_panels(children,order_of_panels)
            focused_panels=sort_panels(focused_panels,order_of_panels)
            for addon in modules:
                # print(addon)
                for name,p in focused_panels:
                    if name==addon:
                        if preferences().addon_info_for_renaming.find(name)>=0:
                            if getattr(p,'bl_category'):
                                if not getattr(p,'backup_category',None):
                                    p.backup_category=p.bl_category
                            if p.bl_category!='Focused':
                                # if name=='Animation_Layers':
                                #     print(p.bl_category,preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name)
                                p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                                p.renamed_category=p.bl_category
                        try:
                            bpy.utils.unregister_class(p)  
                            register_panel(p)
                        except Exception as e:
                            print(e)
            for addon in modules:
                
                for name,p in panels_to_reregister:
                    if name==addon:
                        if preferences().addon_info_for_renaming.find(name)>=0:
                            if getattr(p,'bl_category'):
                                if not getattr(p,'backup_category',None):
                                    p.backup_category=p.bl_category
                            if p.bl_category!='Focused':
                                p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                                p.renamed_category=p.bl_category
                        try:
                            bpy.utils.unregister_class(p)  
                            register_panel(p)
                        except Exception as e:
                            print(e)
            for name,c in children:
                if preferences().addon_info_for_renaming.find(name)>=0:
                    if getattr(c,'bl_category',None):
                        if not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id in parents:
                        bpy.utils.unregister_class(c)  
                        register_panel(c)
                except Exception as e:
                            print(e)
            for name,c in children:
                if preferences().addon_info_for_renaming.find(name)>=0:
                    if getattr(c,'bl_category',None):
                        if not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id not in parents:
                        bpy.utils.unregister_class(c)  
                        register_panel(c)
                except Exception as e:
                            print(e)
            
            #print([sys.modules[get_module_name_from_addon_name(a)] for a in preferences().addons_to_exclude.split(",")+addons_to_exclude])
            modules_to_remove=[]
            for b in bpy.context.preferences.addons.keys():
                try:
                    #print(b)
                    mod = sys.modules[b]
                    if mod.__name__ not in categories+[__package__]+["cycles",]:
                            a = mod.__name__
                            modules_to_remove.append(a)
                except:
                    pass
                            #print("Marker",a)
            for bl_type in registered_panels:
                try:
                    if issubclass(bl_type, bpy.types.Panel):
                        #print(getattr(bl_type,'bl_parent_id',None))
                        if getattr(bl_type,"bl_region_type","UI")=='UI' and getattr(bl_type,'bl_space_type',"VIEW_3D")=='VIEW_3D' :
                            
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            
                            if "." in package_name:
                                name=package_name[:package_name.index(".")]
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                name=exceptional_names[name]
                            #print(name)
                            if name in modules_to_remove:
                                #print(bl_type)
                                #print("296 setting backup",bl_type.bl_category)
                                if not getattr(bl_type,'backup_category',None):
                                    bl_type.backup_category=bl_type.bl_category if getattr(bl_type,'bl_category',preferences().holder_tab_name)!=preferences().holder_tab_name else (bl_type.backup_category if getattr(bl_type,'backup_category',None) else getattr(bl_type,'bl_category','None'))
                                
                                if getattr(bl_type,'bl_category','None')!='Focused':
                                    bl_type.bl_category=preferences().holder_tab_name
                                # if preferences().addon_info_for_renaming.find(name)>=0 and hasattr(bl_type,'bl_category'):
                                #     bl_type.renamed_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                                #print("removing",bl_type)
                                    bpy.utils.unregister_class(bl_type)  
                                    register_panel(bl_type)
                            
                except:
                    pass
        else:
            panels_to_reregister=[]
            parents=[]
            children=[]
            modules=[]
            focused_panels=[]
            for a in bpy.context.preferences.addons.keys():
                try:
                    if sys.modules[a].__name__ not in ["cycles",]:
                        modules.append(sys.modules[a].__name__)
                except Exception as e:
                    pass
            sorted_modules=[]
            for addon_info in preferences().addon_info:
                for a in addon_info.addons.split(","):
                    if a in modules:
                        sorted_modules.append(a)
            sorted_modules=sorted_modules+[a for a in modules if a not in sorted_modules]
            for bl_type in registered_panels:
                    try:
                            if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)=='VIEW_3D' and not getattr(bl_type,'bl_parent_id',None):
                                
                                package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                
                                if "." in package_name:
                                    name=package_name[:package_name.index(".")]
                                else:
                                    name=package_name
                                if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                #modules=[sys.modules[a].__name__ for a in bpy.context.preferences.addons.keys()]
                                if name in sorted_modules:
                                    #bl_type.backup_category=bl_type.bl_category
                                    if bl_type.bl_category!='Focused':
                                        bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    # bl_type.backup_category=None
                                    #print(bl_type,getattr(bl_type,'backup_category',None))
                                    # if preferences().addon_info_for_renaming.find(name)>=0:
                                    #     print("347 Setting backup",bl_type.bl_category)
                                    #     bl_type.backup_category=bl_type.bl_category
                                    #     #print(name,preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name)
                                    #     bl_type.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                                    if bl_type.bl_category=='Focused':
                                        focused_panels.append((name,bl_type))
                                    else:
                                        panels_to_reregister.append((name,bl_type))
                            else:
                                if bl_type and getattr(bl_type,'bl_parent_id',None):
                                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                    if "." in package_name:
                                        name=package_name[:package_name.index(".")]
                                    else:
                                        name=package_name
                                    if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                    if name!='bl_ui' and name in sorted_modules:
                                        parents.append(bl_type.bl_parent_id)
                                        children.append((name,bl_type))
                    except Exception as e:
                        pass
            panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
            children=sort_panels(children,order_of_panels)
            focused_panels=sort_panels(focused_panels,order_of_panels)
            #print(panels_to_reregister,children)
            # print("Sorted",[a.__name__ for b,a in panels_to_reregister if "RTOO" in a.__name__])
            for addon in sorted_modules:
                
                for name,p in focused_panels:
                    if preferences().addon_info_for_renaming.find(name)>=0 and hasattr(p,'bl_category'):
                        
                        if not getattr(p,'backup_category',None):
                            p.backup_category=p.bl_category
                        if p.bl_category!='Focused':
                            p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                            p.renamed_category=p.bl_category
                    if name==addon:
                        try:
                            bpy.utils.unregister_class(p) 
                            register_panel(p)
                        except:
                            pass
            for addon in sorted_modules:
                
                for name,p in panels_to_reregister:
                    if preferences().addon_info_for_renaming.find(name)>=0 and hasattr(p,'bl_category'):
                        
                        if not getattr(p,'backup_category',None):
                            p.backup_category=p.bl_category
                        if p.bl_category!='Focused':
                            p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                            p.renamed_category=p.bl_category
                    if name==addon:
                        try:
                            bpy.utils.unregister_class(p) 
                            register_panel(p)
                        except:
                            pass
            
            for name,c in children:
                if preferences().addon_info_for_renaming.find(name)>=0 :
                    
                    if getattr(c,'bl_category',None) and not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id in parents:
                        bpy.utils.unregister_class(c)  
                        register_panel(c)
                except:
                    pass
            for name,c in children:
                
                if preferences().addon_info_for_renaming.find(name)>=0 :
                    if getattr(c,'bl_category',None) and not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id not in parents:
                        bpy.utils.unregister_class(c)  
                        register_panel(c)
                except:
                    pass
def load_reordering_list(context):
        for a in preferences().addon_info:
            a.addons=""
            a.ordered=""
        #preferences().addon_info.clear()
        change_panel_category("Turn OFF","Focused")
        workspace_category_enabled(preferences().categories,context) 
        og_filter=preferences().categories.filter_enabled
        preferences().categories.filter_enabled=False
        panels_in_use=[]
        no_fix_required=[]
        base_type = bpy.types.Panel
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)=='VIEW_3D' and getattr(bl_type,'bl_category',None) not in ["Item","View","Tool","Dev",preferences().holder_tab_name]:
                        panels_in_use.append(getattr(bl_type,'bl_category'))
                        if getattr(bl_type,'bl_category') not in [a.name for a in  preferences().addon_info]:
                            t=preferences().addon_info.add()
                            t.name=getattr(bl_type,'bl_category')
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=package_name[:package_name.index(".")]
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                            if name not in t.addons:
                            
                                t.addons=name
                            if getattr(bl_type,'bl_order',None)!=None:
                                if getattr(bl_type,'bl_order',None)==0:
                                    no_fix_required.append(name)
                                t.ordered=name
                                #print(t.name,t.ordered)
                        else:
                            t=preferences().addon_info[preferences().addon_info.find(getattr(bl_type,'bl_category'))]
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=package_name[:package_name.index(".")]
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                            if name not in t.addons:
                                t.addons=t.addons+","+name
                            if getattr(bl_type,'bl_order',None) !=None:
                                if getattr(bl_type,'bl_order',None)==0:
                                    no_fix_required.append(name)
                                if name not in t.ordered:
                                    t.ordered=t.ordered+("," if t.ordered else '') +name
                                    #print(t.name,t.ordered)
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
        # print(no_fix_required)
        # for addon in preferences().addon_info:
        #     temp_array=addon.ordered.split(",")
        #     for a in no_fix_required:
        #         if a in temp_array:
        #             temp_array.remove(a)
        #     print(addon,temp_array)
        #     addon.ordered=",".join(temp_array)
        for addon in preferences().addon_info:
            

            if addon.ordered:
                if addon.ordered!=addon.addons:
                    temp_array=sorted(addon.addons.split(","),key=lambda x:x in addon.ordered)
                    addon.addons=",".join(temp_array)
                    addon.ordered=""
        for addon in preferences().addon_info:
            if addon.name not in panels_in_use:
                if preferences().addon_info.find(addon.name)>-1:
                    preferences().addon_info.remove(preferences().addon_info.find(addon.name))
        # for addon in sorted([a.module for a in context.preferences.addons]):
        #     t=preferences().addon_info.add()
        #     t.name=addon
        # for b in preferences().addon_info:
        #     print(b.name,b.addons)
        savePreferences()
        preferences().categories.filter_enabled=og_filter
def load_renaming_list(context):
    change_panel_category("Turn OFF","Focused")
    workspace_category_enabled(preferences().categories,context) 
    og_filter=preferences().categories.filter_enabled
    preferences().categories.filter_enabled=False
    panels_in_use=[]
    no_fix_required=[]
    base_type = bpy.types.Panel
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)=='VIEW_3D' :
                    
                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    if "." in package_name:
                        name=package_name[:package_name.index(".")]
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    if "bl_ui" not in name:
                        panels_in_use.append(name)
                        if name not in [a.name for a in  preferences().addon_info_for_renaming]:
                            
                            t=preferences().addon_info_for_renaming.add()
                            t.tab_name=getattr(bl_type,'bl_category') if getattr(bl_type,'bl_category',preferences().holder_tab_name) !=preferences().holder_tab_name else (getattr(bl_type,'backup_category',preferences().holder_tab_name))
                            
                            t.name=name
                                #print(t.name,t.ordered)
                        else:
                            t=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)]
                            t.tab_name=getattr(bl_type,'bl_category') if getattr(bl_type,'bl_category',preferences().holder_tab_name) !=preferences().holder_tab_name else (getattr(bl_type,'backup_category',preferences().holder_tab_name))
                            # package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            # if "." in package_name:
                            #     name=package_name[:package_name.index(".")]
                            # else:
                            #     name=package_name
                            # t.name=name
        except Exception as e:
            if str(e)!="issubclass() arg 1 must be a class":
                pass
    #print(panels_in_use)
    for a in preferences().addon_info_for_renaming:
        if a.name not in panels_in_use:
            preferences().addon_info_for_renaming.remove(preferences().addon_info_for_renaming.find(a.name))
    savePreferences()
    preferences().categories.filter_enabled=og_filter