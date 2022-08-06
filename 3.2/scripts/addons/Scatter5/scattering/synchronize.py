

#  .oooooo..o                                   oooo                                        o8o
# d8P'    `Y8                                   `888                                        `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.   888 .oo.   oooo d8b  .ooooo.  ooo. .oo.   oooo    oooooooo  .ooooo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8  888P"Y88b  `888""8P d88' `88b `888P"Y88b  `888   d'""7d8P  d88' `88b
#      `"Y88b   `88..8'    888   888  888        888   888   888     888   888  888   888   888     .d8P'   888ooo888
# oo     .d8P    `888'     888   888  888   .o8  888   888   888     888   888  888   888   888   .d8P'  .P 888    .o
# 8""88888P'      .8'     o888o o888o `Y8bod8P' o888o o888o d888b    `Y8bod8P' o888o o888o o888o d8888888P  `Y8bod8P'
#             .o..P'
#             `Y8P'

import bpy

from .. resources.translate import translate
from .. resources.icons import cust_icon

from .. utils.extra_utils import dprint
from .. ui import templates

#See synchonisation on update on update factory 


#       .o.                   o8o
#      .888.                  `"'
#     .8"888.     oo.ooooo.  oooo
#    .8' `888.     888' `88b `888
#   .88ooo8888.    888   888  888
#  .8'     `888.   888   888  888
# o88o     o8888o  888bod8P' o888o
#                  888
#                 o888o


class SCATTER5_PROP_channel_members(bpy.types.PropertyGroup):
    """bpy.context.scene.scatter5.sync_channels[i].members"""

    def upd_m_emitter(self,object):
        return len(object.scatter5.particle_systems)>0

    m_emitter : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=upd_m_emitter,
        )
    psy_name : bpy.props.StringProperty(
        default="",
        )

    def api_exists(self):
        if (self.m_emitter==None or self.psy_name==""):
            return False
        if (self.psy_name not in self.m_emitter.scatter5.particle_systems):
            return False
        return True

    def get_psy(self):
        return self.m_emitter.scatter5.particle_systems[self.psy_name]
        #assuming you did api exists check first 


class SCATTER5_PROP_sync_channels(bpy.types.PropertyGroup):
    """bpy.context.scene.scatter5.sync_channels"""

    name      : bpy.props.StringProperty()
    members   : bpy.props.CollectionProperty(type=SCATTER5_PROP_channel_members) #Children Collection
        
    s_color        : bpy.props.BoolProperty(default=True)
    s_distribution : bpy.props.BoolProperty(default=True)
    s_scale        : bpy.props.BoolProperty(default=True)
    s_rot          : bpy.props.BoolProperty(default=True)
    s_pattern      : bpy.props.BoolProperty(default=True)
    s_abiotic      : bpy.props.BoolProperty(default=True)
    s_proximity    : bpy.props.BoolProperty(default=True)
    s_ecosystem    : bpy.props.BoolProperty(default=True)
    s_push         : bpy.props.BoolProperty(default=True)
    s_wind         : bpy.props.BoolProperty(default=True)
    s_visibility   : bpy.props.BoolProperty(default=True)
    s_instances    : bpy.props.BoolProperty(default=True)
    s_display      : bpy.props.BoolProperty(default=True)

    def psy_in_channel(self,m_emitter,psy_name):
        """check if a psy exists in sync channel members"""
        if len(self.members)==0:
            return False
        for m in self.members:
            if (m.m_emitter==m_emitter) and (m.psy_name==psy_name):
                return True
        return False

    def psy_settings_in_channel(self,m_emitter,psy_name,category):
        if not self.psy_in_channel(m_emitter,psy_name):
            return False
        if category not in self.bl_rna.properties.keys():
            return False
        return eval(f"self.{category}")

    def get_sibling_members(self):
        """return a list of psy members"""
        rlist = []
        for m in self.members:
            if m.api_exists():
                psy = m.get_psy()
                if psy not in rlist:
                    rlist.append(psy)   
        return rlist

    def category_list(self):

        rlist = []
        if self.s_color : 
            rlist.append("s_color")
        if self.s_distribution : 
            rlist.append("s_distribution")
        if self.s_scale : 
            rlist.append("s_scale")
        if self.s_rot : 
            rlist.append("s_rot")
        if self.s_pattern : 
            rlist.append("s_pattern")
        if self.s_abiotic : 
            rlist.append("s_abiotic")
        if self.s_proximity : 
            rlist.append("s_proximity")
        if self.s_ecosystem : 
            rlist.append("s_ecosystem")
        if self.s_push : 
            rlist.append("s_push")
        if self.s_wind : 
            rlist.append("s_wind")
        if self.s_instances : 
            rlist.append("s_instances")
        if self.s_visibility : 
            rlist.append("s_visibility")
        if self.s_display : 
            rlist.append("s_display")

        return rlist


#   .oooooo.                 o8o
#  d8P'  `Y8b                `"'
# 888           oooo  oooo  oooo
# 888           `888  `888  `888
# 888     ooooo  888   888   888
# `88.    .88'   888   888   888
#  `Y8bood8P'    `V88V"V8P' o888o


class SCATTER5_PT_sync_cat_menu(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_sync_cat_menu"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text=translate("Synchronization by Category")+" :")

        active_channel = context.ctxt

        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_color", 
            label=translate("Synchronize Color"), 
            icon="COLOR", 
            left_space=False,
            panel_close=False,
            )

        col.separator()

        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_distribution", 
            label=translate("Synchronize Distribution"), 
            icon="STICKY_UVS_DISABLE", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_scale", 
            label=translate("Synchronize Scale"), 
            icon="OBJECT_ORIGIN", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_rot", 
            label=translate("Synchronize Rotation"), 
            icon="CON_ROTLIKE", 
            left_space=False,
            panel_close=False,
            )

        col.separator()

        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_pattern", 
            label=translate("Synchronize Pattern"), 
            icon="TEXTURE", 
            left_space=False,
            panel_close=False,
            )

        col.separator()

        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_abiotic", 
            label=translate("Synchronize Abiotic"), 
            icon="W_TERRAIN", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_proximity", 
            label=translate("Synchronize Proximity"), 
            icon="W_SNAP", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_ecosystem", 
            label=translate("Synchronize Ecosystem"), 
            icon="W_ECOSYSTEM",
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_push", 
            label=translate("Synchronize Offset"), 
            icon="CON_LOCLIKE", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_wind", 
            label=translate("Synchronize Wind"), 
            icon="FORCE_WIND", 
            left_space=False,
            panel_close=False,
            )

        col.separator()

        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_visibility", 
            label=translate("Synchronize Visibility"), 
            icon="HIDE_OFF", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_instances", 
            label=translate("Synchronize Instances"), 
            icon="W_INSTANCE", 
            left_space=False,
            panel_close=False,
            )
        templates.bool_toggle(col, 
            prop_api=active_channel,
            prop_str="s_display", 
            label=translate("Synchronize Display"), 
            icon="CAMERA_STEREO", 
            left_space=False,
            panel_close=False,
            )

        #col.separator(factor=1)
        #col.operator("scatter5.sync_upd",text=translate("Refresh Settings"),icon="FILE_REFRESH")

        col.separator(factor=0.2)
        return


class SCATTER5_PT_sync_cat_members(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_sync_cat_members"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        scat_scene   = context.scene.scatter5
        active_channel = context.ctxt


        if len(active_channel.members)==0:
            col.label(text=translate("No Members Added Yet"))

            add_icon = col.row(align=True)
            add_icon.enabled = bool(len(scat_scene.sync_channels))
            op = add_icon.operator("scatter5.add_sync_member", icon_value=cust_icon("W_MEMBER_ADD"), text=translate("Add New Member"))
            op.channel_idx = [i for i,c in enumerate(scat_scene.sync_channels) if c==active_channel][0]

            col.separator()
            return 


        col.label(text=translate("Synchronization Members")+" :")


        members= col.column()
        if len(active_channel.members)!=0:
            for i,m in enumerate(active_channel.members):

                api_exists = m.api_exists()

                row = members.row(align=True)
                row.scale_y = 1

                if api_exists:
                    clr = row.row(align=True)
                    clr.scale_x = 0.3
                    clr.scale_y = 2
                    clr.prop( m.get_psy(), "s_color", text="")
                
                ptrs = row.column(align=True)
                
                #emitter ptr 
                ptr = ptrs.row(align=True)
                ptr.prop(m, "m_emitter", text="", icon_value=cust_icon("W_EMITTER"),)
                
                #psy ptr 
                ptr = ptrs.row(align=True)
                if m.m_emitter:
                      ptr.prop_search(m, "psy_name", m.m_emitter.scatter5, "particle_systems" ,text="",icon="PARTICLES")
                else: ptr.prop(m, "psy_name", text="", icon="PARTICLES",)

                #remove operator
                remo = row.column(align=True)
                remo.alert = not api_exists
                remo.scale_y=2
                op = remo.operator("scatter5.remove_sync_member",text="",icon="TRASH", emboss=True,)
                op.channel_idx = [i for i,c in enumerate(scat_scene.sync_channels) if c==active_channel][0]
                op.member_idx = i
                
                members.separator(factor=0.1)


        add_icon = col.row(align=True)
        add_icon.enabled = bool(len(scat_scene.sync_channels))
        op = add_icon.operator("scatter5.add_sync_member", icon_value=cust_icon("W_MEMBER_ADD"), text=translate("Add New Member"))
        op.channel_idx = [i for i,c in enumerate(scat_scene.sync_channels) if c==active_channel][0]

        return 


class SCATTER5_UL_sync_channels(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if not item:
            return 

        scat_scene = context.scene.scatter5

        col = layout.column()
        row = col.row()
        
        prop = row.row()
        #prop.alignment = "LEFT"
        prop.prop(item, "name", text="", emboss=False, )#icon_value=cust_icon("W_ARROW_SYNC"))

        menu = row.row()
        menu.scale_y = 0.8
        menu.emboss = "NONE"
        menu.alignment = "RIGHT"
        menu.context_pointer_set("ctxt", item)
        menu.popover(panel="SCATTER5_PT_sync_cat_menu",text="",icon="PREFERENCES")

        menu = row.row()
        menu.scale_y = 0.8
        menu.emboss = "NONE"
        menu.alignment = "RIGHT"
        menu.scale_x = 1
        menu.active = bool(len(item.members))
        menu.context_pointer_set("ctxt", item)
        txt = f"{len(item.members):02}"
        menu.popover(panel="SCATTER5_PT_sync_cat_members",text=txt,icon="COMMUNITY")

        return 


#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"



class SCATTER5_OT_add_sync_channel(bpy.types.Operator):

    bl_idname      = "scatter5.add_sync_channel"
    bl_label       = ""
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    add    : bpy.props.BoolProperty()
    remove : bpy.props.BoolProperty()

    def execute(self, context):
        scat_scene = context.scene.scatter5

        if self.add:
            s = scat_scene.sync_channels.add()
            s.name = f"Sync Channel.{len(scat_scene.sync_channels):02}"
            scat_scene.sync_channels_idx=len(scat_scene.sync_channels)-1

        if self.remove:
            scat_scene.sync_channels.remove(scat_scene.sync_channels_idx)
            if scat_scene.sync_channels_idx>=len(scat_scene.sync_channels):
                scat_scene.sync_channels_idx=len(scat_scene.sync_channels)-1
            pass

        self.remove = self.add = False
        return {'FINISHED'}


class SCATTER5_OT_add_sync_member(bpy.types.Operator):

    bl_idname      = "scatter5.add_sync_member"
    bl_label       = ""
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    channel_idx : bpy.props.IntProperty()

    def execute(self, context):
        scat_scene = context.scene.scatter5

        active_channel = scat_scene.sync_channels[self.channel_idx]
        active_channel.members.add()

        return {'FINISHED'}


class SCATTER5_OT_remove_sync_member(bpy.types.Operator):

    bl_idname      = "scatter5.remove_sync_member"
    bl_label       = ""
    bl_description = translate("Remove this member ?")
    bl_options     = {'INTERNAL','UNDO'}

    member_idx  : bpy.props.IntProperty()
    channel_idx : bpy.props.IntProperty()

    def execute(self, context):
        scat_scene = context.scene.scatter5

        active_channel = scat_scene.sync_channels[self.channel_idx]
        active_channel.members.remove(self.member_idx)

        return {'FINISHED'}


#  .oooooo..o                                      oooooooooooo                                       .    o8o
# d8P'    `Y8                                      `888'     `8                                     .o8    `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.      888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8     888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#      `"Y88b   `88..8'    888   888  888           888    "     888   888   888   888  888         888    888  888   888  888   888
# oo     .d8P    `888'     888   888  888   .o8     888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
# 8""88888P'      .8'     o888o o888o `Y8bod8P'    o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#             .o..P'
#             `Y8P'


def is_synchronized(psy,s_category):
    """check if the psy is being synchronized"""

    scat_scene    = bpy.context.scene.scatter5 
    emitter       = scat_scene.emitter
    sync_channels = scat_scene.sync_channels

    return True in [ch.psy_settings_in_channel(emitter, psy.name, s_category,) for ch in sync_channels]


def sync_info(layout, psy_active, s_category=""):
    """gui synchronization information"""

    #draw GUI
    if is_synchronized(psy_active, s_category) :
        row = layout.row()
        row.scale_y = 0.9
        row.alignment = "CENTER"
        #row.alert = True
        row.active = False
        row.label(text=translate("Settings are Synchronized."), icon_value=cust_icon("W_ARROW_SYNC"))
        return True
    return False


def get_sync_siblings(m_emitter,psy_name):
    """recolt information about what to sync with"""

    scat_scene    = bpy.context.scene.scatter5 
    sync_channels = scat_scene.sync_channels

    d = []

    for ch in sync_channels:
        if ch.psy_in_channel(m_emitter,psy_name):
            category_list=ch.category_list()
            if len(category_list)!=0: 
                d.append({
                    "channel"    : ch.name,
                    "categories" : category_list,
                    "psys"       : ch.get_sibling_members()
                    })

    return d



# class SCATTER5_OT_sync_upd(bpy.types.Operator):
#     """make sure all settings are set to the same values"""

#     bl_idname      = "scatter5.sync_upd"
#     bl_label       = ""
#     bl_description = ""
#     bl_options     = {'INTERNAL','UNDO'}

#     channel_idx : bpy.props.IntProperty()

#     def execute(self, context):
#         scat_scene = context.scene.scatter5

#         active_channel = scat_scene.sync_channels[self.channel_idx]

#         category_list = active_channel.category_list()
#         if len(category_list)==0:
#             return {'FINISHED'}            

#         psy = None 
#         for m in active_channel.members:
#             if m.api_exists():
#                 psy = m.get_psy()
#                 break

#         if psy is None:
#             return {'FINISHED'}            

#         for k,v in psy.bl_rna.properties.items():
#             if len([c for c in category_list if k.startswith(c)])!=0:
#                 setattr(psy,k,eval(f"psy.{k}"))
#         return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'




classes = [

    SCATTER5_UL_sync_channels,
    SCATTER5_OT_add_sync_channel,

    SCATTER5_PT_sync_cat_menu,
    SCATTER5_PT_sync_cat_members,

    SCATTER5_OT_add_sync_member,
    SCATTER5_OT_remove_sync_member,
    #SCATTER5_OT_sync_upd,

    ]


