
###############################################################################################################################################################
#
# oooooooooo.   o8o                                             ooooo         o8o   .o8
# `888'   `Y8b  `"'                                             `888'         `"'  "888
#  888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.        888         oooo   888oooo.  oooo d8b  .oooo.   oooo d8b oooo    ooo
#  888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b       888         `888   d88' `88b `888""8P `P  )88b  `888""8P  `88.  .8'
#  888    `88b  888  888   888  888   888   888  888ooo888       888          888   888   888  888      .oP"888   888       `88..8'
#  888    .88P  888  888   888  888   888   888  888    .o       888       o  888   888   888  888     d8(  888   888        `888'
# o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'      o888ooooood8 o888o  `Y8bod8P' d888b    `Y888""8o d888b        .8'
#                                                                                                                         .o..P'
#                                                                                                                         `Y8P'
###############################################################################################################################################################


import bpy, os, json, re, requests
from datetime import datetime, date

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. import utils
from .. utils.event_utils import get_event

from .. scattering.emitter import poll_emitter as emitter_poll
from .. scattering.emitter import is_ready_for_scattering

# #custom biome pointer property disabled 
#from .. scattering.add_biome import add_jsonbiome_on_pointer_update as emitter_update




# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
#                                 o888o


class SCATTER5_PROP_library(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5.library"""

    #name == path 
    name : bpy.props.StringProperty()

    #direct from json["info"]
    user_name : bpy.props.StringProperty()  
    type : bpy.props.StringProperty() #"Folder"/"Biome"/"Asset"/"Material"/"Online"
    keywords : bpy.props.StringProperty()
    author : bpy.props.StringProperty()
    website : bpy.props.StringProperty()
    description : bpy.props.StringProperty()
    greyed_out : bpy.props.BoolProperty()

    #biomes info 
    estimated_density : bpy.props.FloatProperty(default=-1)
    layercount : bpy.props.IntProperty()

    #dialog system 
    is_dialog : bpy.props.BoolProperty(default=False)

    #filled if .jpg of biome found 
    icon : bpy.props.StringProperty() #iconpath

    #Special for online
    messages : bpy.props.StringProperty() #for "Online" : message list used when clicking on online biome type 
    is_info : bpy.props.BoolProperty(default=False) #for "Online" : used to display other icon if info

    #Used for folder navigation, but already calculated before
    level : bpy.props.IntProperty()
    is_open : bpy.props.BoolProperty()

    #Pointer used to drag and drop biome functionality 
    # emitter : bpy.props.PointerProperty( 
    #     type        = bpy.types.Object, 
    #     poll        = emitter_poll,
    #     update      = emitter_update,
    #     description = translate("Drag and Drop this biome"),
    #     )


#all props under here are dynamically derrived from above, refresh when user click on ui list 
class SCATTER5_PROP_folder_navigation(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()
    level : bpy.props.IntProperty()
    is_open : bpy.props.BoolProperty()
    is_dead_end : bpy.props.BoolProperty()
    is_active : bpy.props.BoolProperty()
    elements_count : bpy.props.IntProperty()
    icon : bpy.props.StringProperty()



# oooooooooo.               o8o  oooo        .o8       oooooooooooo oooo                                                        .
# `888'   `Y8b              `"'  `888       "888       `888'     `8 `888                                                      .o8
#  888     888 oooo  oooo  oooo   888   .oooo888        888          888   .ooooo.  ooo. .oo.  .oo.    .ooooo.  ooo. .oo.   .o888oo  .oooo.o
#  888oooo888' `888  `888  `888   888  d88' `888        888oooo8     888  d88' `88b `888P"Y88bP"Y88b  d88' `88b `888P"Y88b    888   d88(  "8
#  888    `88b  888   888   888   888  888   888        888    "     888  888ooo888  888   888   888  888ooo888  888   888    888   `"Y88b.
#  888    .88P  888   888   888   888  888   888        888       o  888  888    .o  888   888   888  888    .o  888   888    888 . o.  )88b
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888ooooood8 o888o `Y8bod8P' o888o o888o o888o `Y8bod8P' o888o o888o   "888" 8""888P'


#Build whole props-collection of libraries


def biome_in_subpaths(path):
    """check if there's some biomes down this path"""
    for p in utils.path_utils.get_subpaths(path):
        if p.endswith(".biome"):
            return True
    return False


def is_dead_end(path):
    """check if there's some other nested folder with some biomes in this path (for folder navigation ICON gui)"""
    #print(f"is_dead_end({os.path.basename(path)})")
    for p in os.listdir(path):
        p = os.path.join(path,p)
        if os.path.isdir(p):
            if biome_in_subpaths(p):
                return False
    return True



Mapping = []


def rebuild_library():
    """with the Mapping information generated by recur_biomes_mapping(), 
    fill  scatter5.library collection property with information about the library,
    the library will then be read directly in the grid_flow() layout 
    and another collection property will be dynamically generated only for the folder navigation GUI.
    Note that scatter5.library also contain icon path information that will be loaded """

    wm = bpy.context.window_manager

    #remove all existing items from lib
    for i in range(len(wm.scatter5.library)):
        wm.scatter5.library.remove(0)

    #Recur all folder and files within library for navigation
    global Mapping

    def recur_biomes_mapping(path, level=0):
        """will map the _biomes_ folder structure"""

        if not biome_in_subpaths(path):
            return None

        global Mapping
        Mapping.append({
            "path":path,
            "level":level,
            "type":"Folder",
            "is_open": not os.path.exists(os.path.join(path,"_closed_default_")),
            })

        for p in os.listdir(path): #order of list generated by listdir is important..
            p = os.path.join(path,p)

            if os.path.isfile(p):
                if p.endswith(".biome"): 
                    Mapping.append({ 
                        "path":p, 
                        "level":level, 
                        "type":"none", #type will be assigned later,it is cointained in .biome["info"]
                        "is_open":False,
                        })
            elif os.path.isdir(p):
                recur_biomes_mapping(p, level=level+1)

        return None 

    recur_biomes_mapping( directories.lib_biomes ) #gather everything in ../_biomes_
    recur_biomes_mapping( directories.lib_market ) #also gather previews from ../_market_

    #library navigation = list every folder & files
    for element in Mapping:

        #from Mapping, add element in ui list
        e = wm.scatter5.library.add()

        #add basic information needed for navigation
        e.name        = element["path"] #/!\ we are storing path, using os.basename to show name in GUI
        e.level       = element["level"] #used in folder navigation for spacing gui 
        e.type        = element["type"] #temporarily add type, if folder else will be corrected with true type from json dict down below
        e.is_open     = element["is_open"] 

        #if type is not folder,then we will need more information
        #note that the order of picking the element in mapping and here are extremely important
        if e.type!="Folder":

            #find an icon if it exists right next to .biome file? 
            icon_path = e.name.replace(".biome",".jpg")
            if os.path.exists(icon_path):
                e.icon = icon_path #show icon preview in layout.grid_flow()

            #read information detained in .biome json file and transfer them in our element 
            with open(e.name) as f:

                try:
                    biome = json.load(f)
                except Exception as err:
                    print(f"")
                    print(f"/!\\ SCATTER5 BIOME MANAGER WARNING /!\\")
                    print(f"    There was a .biome file that was wrongly encoded!")
                    print(f"    .biome file must follow the .json format, ponctuation is extremely important")
                    print(f"    Path of the wrongly encoded file: {e.name}")
                    print(f"    Error message: {err}")
                    print(f"")
                    continue

            if 'name' in biome["info"]:
                e.user_name = biome["info"].get("name")
            else:
                e.user_name = ".".join(os.path.basename(e.name).replace("_"," ").title().split(".")[:-1])
                if "#" in e.user_name: #used to manage order, everything below # should be ignored 
                    e.user_name = e.user_name.split("#")[-1]

            if "type" in biome["info"]:
                e.type = biome["info"].get("type")

            if "author" in biome["info"]:
                e.author = biome["info"].get("author") 

            if "website" in biome["info"]:
                e.website  = biome["info"].get("website")

            if "estimated_density" in biome["info"]:
                e.estimated_density = biome["info"].get("estimated_density")

            if "layercount" in biome["info"]:
                e.layercount = biome["info"].get("layercount")

            if "description" in biome["info"]:
                e.description = biome["info"].get("description")

            if "messages" in biome["info"]:
                messages = biome["info"].get("messages")
                if type(messages) is list:
                    e.messages = "_#_".join(messages)

            if "is_info" in biome["info"]:
                e.is_info  = biome["info"].get("is_info")

            if "greyed_out" in biome["info"]:
                e.greyed_out = biome["info"].get("greyed_out")

            if "keywords" in biome["info"]:
                if type(biome["info"].get("keywords")) is list:
                      e.keywords = ",".join(biome["info"].get("keywords"))
                else: e.keywords = biome["info"].get("keywords") 
                if (e.type not in e.keywords):
                    e.keywords+= f",{e.type}"
                if (e.layercount==1) and ("Layer" not in e.keywords):
                    e.keywords+= f",Single,Layer"
                elif (e.layercount>1):
                    e.keywords+= f",Multi,Aio"
                e.keywords+= f", {e.author},{e.user_name}"

        continue 

    #Reset Mapping
    Mapping = []

    return 



# oooooooooo.               o8o  oooo        .o8       ooooooooo.                                   o8o
# `888'   `Y8b              `"'  `888       "888       `888   `Y88.                                 `"'
#  888     888 oooo  oooo  oooo   888   .oooo888        888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo   .ooooo.  oooo oooo    ooo  .oooo.o
#  888oooo888' `888  `888  `888   888  d88' `888        888ooo88P'  `888""8P d88' `88b  `88.  .8'  `888  d88' `88b  `88. `88.  .8'  d88(  "8
#  888    `88b  888   888   888   888  888   888        888          888     888ooo888   `88..8'    888  888ooo888   `88..]88..8'   `"Y88b.
#  888    .88P  888   888   888   888  888   888        888          888     888    .o    `888'     888  888    .o    `888'`888'    o.  )88b
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888o        d888b    `Y8bod8P'     `8'     o888o `Y8bod8P'     `8'  `8'     8""888P'



#create previews from scat_win.library that we create above 


#need to store bpy.utils.previews here
LibPreviews = {}

def register_library_previews():
    """Register every previews for each elements of scatter5 manager library"""

    scat_win = bpy.context.window_manager.scatter5

    global LibPreviews 
    from .. resources.icons import get_previews_from_paths
    all_icons = [ e.icon for e in scat_win.library if (e.type!="Folder") and (e.icon!="") ]
    LibPreviews = get_previews_from_paths(all_icons, use_basename=False,)
    
    return

def unregister_library_previews():
    """unregister all icons of library"""

    global LibPreviews 
    from .. resources.icons import remove_previews
    remove_previews(LibPreviews)

    return 

def preview_icon(icon_path):
    """get icon id of given element.icon"""
            
    global LibPreviews 
    if icon_path in LibPreviews:
        return LibPreviews[icon_path].icon_id

    return None



# oooooooooo.               o8o  oooo        .o8       oooooooooooo           oooo        .o8
# `888'   `Y8b              `"'  `888       "888       `888'     `8           `888       "888
#  888     888 oooo  oooo  oooo   888   .oooo888        888          .ooooo.   888   .oooo888   .ooooo.  oooo d8b
#  888oooo888' `888  `888  `888   888  d88' `888        888oooo8    d88' `88b  888  d88' `888  d88' `88b `888""8P
#  888    `88b  888   888   888   888  888   888        888    "    888   888  888  888   888  888ooo888  888
#  888    .88P  888   888   888   888  888   888        888         888   888  888  888   888  888    .o  888
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888o        `Y8bod8P' o888o `Y8bod88P" `Y8bod8P' d888b

#== biome library navigation

#Create dynamically generated properties/ui list used in GUI to navigate
#as there's no way to hide an item from an UI list, we are forsted to dynamically rebuild the data from the list
#(that's why the folder collection property derrived from scatter5.library)


def rebuild_folder_navigation():

    wm = bpy.context.window_manager

    #clean all previous data
    for i in range(len(wm.scatter5.folder_navigation)):
        wm.scatter5.folder_navigation.remove(0)

    #filter if user is closing/opening folders within the interface
    ClosedPaths = [ c.name for c in wm.scatter5.library if (c.type=="Folder") and (not c.is_open) ]
    def is_path_in_closed_folders(path):
        for c in ClosedPaths:
            if (path!=c) and path.startswith(os.path.join(c,"")):
                return True
        return False

    for li in wm.scatter5.library:

        #we want to gather all folder
        if (li.type!="Folder"):
            continue
        #and only folder with stuff inside
        if (is_path_in_closed_folders(li.name)):
            continue 
        #we also want to ignore the market folder, that's not for the biome library navigation 
        if "_market_" in li.name:
            continue 

        fo = wm.scatter5.folder_navigation.add()
        fo.name = li.name
        fo.level = li.level
        fo.is_open = li.is_open
        fo.is_dead_end = is_dead_end(fo.name)
        fo.is_active = os.path.exists(os.path.join(fo.name,"_active_default_"))
        fo.elements_count = len([f for f in utils.path_utils.get_subpaths(fo.name) if f.endswith(".biome")])
        fo.icon = "W_FOLDER" if fo.is_dead_end else "W_FOLDER_CLOSED" if fo.is_open else "W_FOLDER_OPEN"
        
    #never default on "all", search for is_active prop
    if (wm.scatter5.folder_navigation_idx==0):
        for i,e in enumerate(wm.scatter5.folder_navigation):
            if e.is_active:
                wm.scatter5.folder_navigation_idx=i
    return 



class SCATTER5_UL_folder_navigation(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):

        if not item:
            return 

        row = layout.row(align=True)    
        row.separator(factor=item.level*1.15)

        #operator that will open/close in library then rebuild the list
        row.operator("scatter5.open_close_folder_navigation", icon_value=cust_icon(item.icon), emboss=False, depress=True, text="").path = item.name

        basename = os.path.basename(item.name)
        if basename=="_biomes_":
            basename=translate("All")
        row.label(text=basename)

        return 



class SCATTER5_OP_open_close_folder_navigation(bpy.types.Operator):

    bl_idname      = "scatter5.open_close_folder_navigation"
    bl_label       = translate("Open/Close this Folder")
    bl_options     = {'REGISTER', 'INTERNAL'}
    bl_description = translate("Hold [ALT] to open this folder in your File Explorer")

    path : bpy.props.StringProperty()

    def execute(self, context):

        event = get_event()

        if (event.ctrl):
            bpy.ops.scatter5.open_directory(folder=self.path)
            return {'FINISHED'}

        wm = bpy.context.window_manager
        wm.scatter5.library[self.path].is_open = not wm.scatter5.library[self.path].is_open

        #from library navigation, create a dynamic list that will update itself when closing/opening folder
        rebuild_folder_navigation()

        # move active index
        for i,e in enumerate(wm.scatter5.folder_navigation):
            if e.name==self.path:
                break 
                
        wm.scatter5.folder_navigation_idx = i
        bpy.context.area.tag_redraw()

        return {'FINISHED'}


# oooooooooo.                                        o8o
# `888'   `Y8b                                       `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo oooo  ooo. .oo.    .oooooooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'  `888  `888P"Y88b  888' `88b
#  888      888  888      .oP"888    `88..]88..8'    888   888   888  888   888
#  888     d88'  888     d8(  888     `888'`888'     888   888   888  `88bod8P'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'     o888o o888o o888o `8oooooo.
#                                                                     d"     YD
#                                                                     "Y88888P'

def limit_string(word, limit):

    if len(word)>limit-3:
        return word[:limit-3] + "..."

    return word

def match_word(search_string, keyword_string, ):

    search_string, keyword_string = search_string.lower(), keyword_string.lower()
    terms = search_string.split(" ")

    r = []
    for w in terms:
        r.append(w in keyword_string)

    if r:
        return all(r)
    return False 


#  dP""b8 88""Yb 88 8888b.    888888 88     888888 8b    d8 888888 88b 88 888888
# dP   `" 88__dP 88  8I  Yb   88__   88     88__   88b  d88 88__   88Yb88   88
# Yb  "88 88"Yb  88  8I  dY   88""   88  .o 88""   88YbdP88 88""   88 Y88   88
#  YboodP 88  Yb 88 8888Y"    888888 88ood8 888888 88 YY 88 888888 88  Y8   88


def draw_biome_element(e, layout, enabled):

    scat_scene = bpy.context.scene.scatter5
    text_cut = limit_string(e.user_name, scat_scene.library_typo_limit)

    #add a bit of separation on top
    col = layout.column(align=True)
    col.separator(factor=0.7)


    #LargeIcon
    ixon = cust_icon("W_DEFAULT_PREVIEW") if (e.icon=="") else preview_icon(e.icon)
    itembox = col.column(align=True).box()
    itembox.active = not e.greyed_out
    itembox.template_icon( icon_value=ixon , scale=scat_scene.library_item_size ) #PERFORMANCE ISSUE HERE it seem that template icon is really really slow to draw, not sure why, label icon as right is smooth as hell `itembox.label(text="",icon_value=ixon)`

    #Draw Biome Item Operator

    action_row = col.row(align=True)
    action_row.scale_y = 0.95

    if (scat_scene.progress_context==e.name):
    
        progress = action_row.row(align=True)
        progress.ui_units_x = 4
        progress.prop(scat_scene,"progress_bar",text=scat_scene.progress_label,)

        return None 

    ope = action_row.row(align=True)
    ope.ui_units_x = 4
    ope.operator_context = "INVOKE_DEFAULT"
    
    if not enabled: #prolly because no emitter target 
        ope.enabled = False
        if scat_scene.emitter is None:
            text_cut = translate("No Emitter") 

    load = ope.row(align=True)
    op = load.operator("scatter5.load_biome", text=text_cut, emboss=True, depress=False, icon="ADD")
    op.emitter_name = "" #Auto
    op.json_path = e.name
    op.single_layer = -1

    down = ope.row(align=True)
    down.scale_x = 0.95
    down.context_pointer_set("lib_element", e)
    down.menu("SCATTER5_MT_biome_ctrl_click", text="", icon="DOWNARROW_HLT",)

    return None

def draw_online_element(e, layout,):

    scat_scene = bpy.context.scene.scatter5
    text_cut = limit_string( e.user_name, scat_scene.library_typo_limit )

    #add a bit of separation on top
    col = layout.column(align=True)
    col.separator(factor=0.7)


    # #draw item box if open? Nope, canceled this idea, might be too weird..
    # if e.is_dialog:

    #     #draw inside box if dialog enabled, need to manage height and spaces correctly
    #     row = itembox.row()
    #     row.scale_x = 0.7

    #     rensure_height = row.column()
    #     rensure_height.template_icon( icon_value= cust_icon("W_DEFAULT_PREVIEW") , scale=scat_scene.library_item_size )
    #     rensure_height.scale_x = 0.01

    #     box_content = row.column()

    #     lbl = box_content.column()
    #     lbl.scale_y = scat_scene.library_item_size*0.2
    #     lbl.active = False
    #     lbl.separator(factor=3)
    #     lbl.label(text=translate("Website")+":")

    #     #Open Webstite
    #     open_link = box_content.row(align=True)
    #     open_link.operator("wm.url_open", text=translate("Open Link"),).url = e.website
        
    #     row.separator()

    #else draw only icon
    #else:

    #LargeIcon
    ixon = cust_icon("W_DEFAULT_PREVIEW") if (e.icon=="") else preview_icon(e.icon) 
    itembox = col.column(align=True).box()
    itembox.active = not e.greyed_out
    itembox.template_icon( icon_value=ixon , scale=scat_scene.library_item_size )

    #Operations Under Icon

    #Display correct icon!
    kwargs = {"text":text_cut, "emboss":True, "depress":e.is_dialog,}
    #Is this an info?
    if e.is_info:
          kwargs["icon"] = "INFO"
    #do the user possess this pack? no?
    elif (utils.path_utils.search_for_path(directories.lib_library, os.path.basename(e.name).replace(".biome",".userhave").split('#')[1],'.userhave') == ""):
          kwargs["icon_value"] = cust_icon("W_SUPERMARKET")
    #if yes then use checkmark icon
    else: kwargs["icon_value"] = cust_icon("W_CHECKMARK") #kwargs["icon"] = "CHECKBOX_HLT"

    #Open Url Operator
    action_row = col.row(align=True)
    action_row.scale_y = 0.95

    ope = action_row.row(align=True)
    ope.ui_units_x = 4
    load = ope.row(align=True)
    load.operator("wm.url_open", **kwargs).url = e.website

    #op = open_dialog.operator("scatter5.exec_line", **kwargs)
    #op.description = translate("Show me more about this item")
    #op.api = f"for e in bpy.context.window_manager.scatter5.library: e.is_dialog=e.name==r'{e.name}'"

    return None 


# 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP      dP""b8 88""Yb 88 8888b.
# 88     88 88__dP 88__dP   dPYb   88__dP  YbdP      dP   `" 88__dP 88  8I  Yb
# 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P       Yb  "88 88"Yb  88  8I  dY
# 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP         YboodP 88  Yb 88 8888Y"


def draw_library_grid(self, layout): 
    """Draw user Biome Library"""

    addon_prefs     = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene      = bpy.context.scene.scatter5
    scat_win        = bpy.context.window_manager.scatter5
    enabled         = is_ready_for_scattering()

    grid = layout.grid_flow(row_major=True, columns=0 if scat_scene.library_adaptive_columns else scat_scene.library_columns, even_columns=False, even_rows=False, align=False,)

    count = 0
    for i,e in enumerate(scat_win.library):
            
        #We don't want to see any folder element here
        if (e.type=="Folder"): 
            continue

        #If element coming from _market_ just ignore
        if ("_market_" in e.name):
            continue 

        #Filter by active navigation tab 
        if not e.name.startswith(os.path.join(scat_win.folder_navigation[scat_win.folder_navigation_idx].name,"")):
            continue 

        #filter search bar? 
        if (scat_scene.library_search != ""):
            if not match_word( scat_scene.library_search, e.keywords,):
                continue 

        count += 1

        #Draw Biome Element 
        if e.type=="Biome":
            draw_biome_element(e, grid, enabled)
            continue

        #Draw Material Element 
        # elif e.type=="Material":
        #     operator = action_row.row(align=True)
        #     operator.ui_units_x = 4
        #     operator.enabled = enabled
        #     operator.operator("scatter5.dummy", text=text_cut, emboss=True, depress=False, icon="SHADING_TEXTURE")

        #     #Material Ptr, #TODO will need to create one
        #     ptr = action_row.row(align=True)
        #     ptr.scale_x = 0.175
        #     ptr.enabled = enabled
        #     ptr.prop(e,"emitter",text=" ",icon="BLANK1", emboss=True)
        #     continue

        # #Draw Asset Element
        # elif e.type=="Asset":
        #     operator = action_row.row(align=True)
        #     operator.ui_units_x = 4
        #     operator.enabled = enabled
        #     operator.operator("scatter5.dummy", text=text_cut, emboss=True, depress=False, icon="OBJECT_DATAMODE")
        #     continue

        #Draw Online Element
        elif e.type=="Online":
            draw_online_element(e, grid)
            continue

        continue

    # Add a few more just to space out
    if (count!=0):

        for i in range(20):
            block = grid.column()
            preview = block.column(align=True)
            block.separator(factor=0.2)
            preview.template_icon( icon_value=cust_icon("W_BLANK1") , scale=scat_scene.library_item_size )
            operator = preview.row()
            operator.label(text="")
            operator.scale_y = 0.9

        scroll = layout.row()
        scroll.operator("scatter5.scroll_to_top", text=translate("Lost? Scroll to Top"),emboss=False)

    # If nothing Found
    if (count==0):

        if len(scat_win.folder_navigation)==0:

            if not biome_in_subpaths(directories.lib_biomes):

                empty = layout.row()
                empty.active = False
                empty.label(text=translate("Your Biome Library seem to be Empty")+" :")
                layout.operator("scatter5.open_directory", emboss=False, text='"'+directories.lib_biomes+'"').folder = directories.lib_biomes 
                
            else:
                youmay = layout.row()
                youmay.active = False
                youmay.label(text=translate("You may need to reload your library by pressing the button below"))
        
                reloading= layout.row()
                reloading.separator(factor=5)
                reloading.operator("scatter5.reload_biome_library", text=translate("Reload"), icon="FILE_REFRESH")
                reloading.separator(factor=5)


        elif scat_scene.library_search != "":
            badsearch = layout.row()
            badsearch.active = False
            badsearch.label(icon="VIEWZOOM", text=f'{translate("Nothing found with Keyword")}  "{scat_scene.library_search}"  {translate("In Active Folder")}')

        else:
            # Not probable at all 
            nothing = layout.column()
            nothing.active = False
            nothing.label(text="This Folder Seems to be empty!")
            nothing.label(text='"'+scat_win.folder_navigation[scat_win.folder_navigation_idx].name+'"')

    return 


#  dP"Yb  88b 88 88     88 88b 88 888888      dP""b8 88""Yb 88 8888b.
# dP   Yb 88Yb88 88     88 88Yb88 88__       dP   `" 88__dP 88  8I  Yb
# Yb   dP 88 Y88 88  .o 88 88 Y88 88""       Yb  "88 88"Yb  88  8I  dY
#  YbodP  88  Y8 88ood8 88 88  Y8 888888      YboodP 88  Yb 88 8888Y" 



def draw_online_grid(self, layout): 
    """Draw Online Store"""

    addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_win    = bpy.context.window_manager.scatter5

    grid = layout.grid_flow(row_major=True, columns=0 if scat_scene.library_adaptive_columns else scat_scene.library_columns, even_columns=False, even_rows=False, align=False,)

    count = 0
    for i,e in enumerate(scat_win.library):
            
        #Only Show Online Items
        if (e.type!="Online"): 
            continue

        #Only Show item in market and onlin
        if ("_market_" not in e.name): 
            continue

        #Draw Element 
        draw_online_element(e, grid)

        count += 1
        continue

    # Add a few more just to space out

    if count!=0:

        for i in range(20):
            block = grid.column()
            preview = block.column(align=True)
            block.separator(factor=0.2)
            preview.template_icon( icon_value=cust_icon("W_BLANK1") , scale=scat_scene.library_item_size )
            operator = preview.row()
            operator.label(text="")
            operator.scale_y = 0.9

        scroll = layout.row()
        scroll.operator("scatter5.scroll_to_top", text=translate("Lost? Scroll to Top"),emboss=False)

    # If nothing Found : 

    if count==0:

        youmay = layout.row()
        youmay.active = False
        youmay.label(text=translate("It seem that there's nothing in the store? Please Refresh"))

        reloading= layout.row()
        reloading.separator(factor=5)
        reloading.operator("scatter5.manual_fetch_from_git", text=translate("Refresh"), icon="FILE_REFRESH")
        reloading.separator(factor=5)

    return 



#   .oooooo.               oooo   o8o                             oooooooooooo               .             oooo
#  d8P'  `Y8b              `888   `"'                             `888'     `8             .o8             `888
# 888      888 ooo. .oo.    888  oooo  ooo. .oo.    .ooooo.        888          .ooooo.  .o888oo  .ooooo.   888 .oo.
# 888      888 `888P"Y88b   888  `888  `888P"Y88b  d88' `88b       888oooo8    d88' `88b   888   d88' `"Y8  888P"Y88b
# 888      888  888   888   888   888   888   888  888ooo888       888    "    888ooo888   888   888        888   888
# `88b    d88'  888   888   888   888   888   888  888    .o       888         888    .o   888 . 888   .o8  888   888
#  `Y8bood8P'  o888o o888o o888o o888o o888o o888o `Y8bod8P'      o888o        `Y8bod8P'   "888" `Y8bod8P' o888o o888o

#Gather Previews from github server to "_market_" Folder


def fetching_from_git():

    try: 
        print("")
        print("SCATTER5 Will Try to update the `_market_` Folder :")

        from .. resources.directories import lib_market
        last_fetch_path = os.path.join(lib_market,"last_fetch.json")


        print(f"         -Removing all files from _market_ folder...")
        for file in os.listdir(lib_market):
            os.remove(os.path.join(lib_market, file))

        url = "https://raw.githubusercontent.com/DB3D/scatter-fetch/main/_market_.zip"
        print(f"         -Downloading .zip (containting only json and image files) from github sever...")
        print(f"          {url}")
        adress = requests.get(url)
        fetched_scatpack = os.path.join(lib_market, "_market_.zip")
        with open(fetched_scatpack, 'wb') as f:
            f.write(adress.content)

        #unzip in location
        print(f"         -Unzipping in _market_ folder location...")
        from .. resources.packaging import unzip_in_location
        unzip_in_location(fetched_scatpack,lib_market)
        
        #Update Last Fetch Infomration on disk as json file
        print(f"         -Updating `last_fetch.json` last refresh information...")
        now = datetime.now()
        dump_dict = {"year":now.year,"month":now.month,"day":now.day}
        with open(last_fetch_path, 'w') as f:
            json.dump(dump_dict, f, indent=4)

        print(f"         -Online fetch successful! Your _market_ folder is now up to date.")
        print(f"          We will now proceed to reload your library")

    except Exception as e:
        print(f"         -Couldn't connect to the internet.",e)

    return None 



def automatic_fetch():
    """Write all Previews on disk every X Days or if last_fetch_path path not found"""

    def fetch_condition():

        from .. resources.directories import lib_market
        last_fetch_path = os.path.join(lib_market,"last_fetch.json")

        addon_prefs = bpy.context.preferences.addons["Scatter5"].preferences

        if not addon_prefs.fetch_automatic_allow:
            return False

        #Fetch if no last_fetch_path
        if not os.path.exists(last_fetch_path):
            return True

        #Fetch if last fetch was too long ago
        now = datetime.now()
        with open(last_fetch_path) as f:
            date_dict = json.load(f)
            last_date = date(date_dict["year"], date_dict["month"], date_dict["day"])
        current_date = date(now.year, now.month, now.day)
        delta = current_date - last_date

        if delta.days>=addon_prefs.fetch_automatic_daycount:
            print(f"SCATTER5 `_market_` Folder Last Fetch: {delta.days} days ago")
            return True
        return False

    if fetch_condition():
        fetching_from_git()

    return None 



class SCATTER5_OT_manual_fetch_from_git(bpy.types.Operator):

    bl_idname      = "scatter5.manual_fetch_from_git"
    bl_label       = "manual_fetch_from_git"
    bl_description = ""
    bl_options     = {'INTERNAL'}

    def execute(self, context):
                
        fetching_from_git()
        bpy.ops.scatter5.reload_biome_library()
        
        return {'FINISHED'}



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooooooo
#  888ooo88P'  d88' `88b 888' `88b
#  888`88b.    888ooo888 888   888
#  888  `88b.  888    .o `88bod8P'
# o888o  o888o `Y8bod8P' `8oooooo.
#                        d"     YD
#                        "Y88888P'


class SCATTER5_OP_reload_biome_library(bpy.types.Operator):

    bl_idname  = "scatter5.reload_biome_library"
    bl_label   = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        unregister()
        register()
        return {'FINISHED'}



def register():

    #fetch from github in "_market_" folder, this won't happend that often
    automatic_fetch()

    #build library item list from directories
    rebuild_library()

    #from scatter5.library, load all previews
    register_library_previews()

    #from scatter5.library, create a dynamic list that will update itself when closing/opening folder
    rebuild_folder_navigation()

    return 

def unregister():

    unregister_library_previews()

    return 



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = [

    SCATTER5_UL_folder_navigation,

    SCATTER5_OP_reload_biome_library,
    SCATTER5_OP_open_close_folder_navigation,

    SCATTER5_OT_manual_fetch_from_git,

    ]