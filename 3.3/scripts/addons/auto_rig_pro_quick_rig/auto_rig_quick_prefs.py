import bpy

def update_all_tab_names(self, context):
    try:
        from . import auto_rig_quick
        auto_rig_quick.update_arp_tab()       
    except:
        pass

class ARP_MT_arp_quick_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    arp_tab_name : bpy.props.StringProperty(name="Interface Tab", description="Name of the tab to display the interface in", default="ARP", update=update_all_tab_names)    
    custom_presets_path: bpy.props.StringProperty(name="Custom Presets Path", subtype='FILE_PATH', default="C:\\Quick Rig Presets/")
    
    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(self, "arp_tab_name", text="Interface Tab")
        col.prop(self, "custom_presets_path", text="Custom Presets Path")

def register():
    from bpy.utils import register_class

    try:
        register_class(ARP_MT_arp_quick_addon_preferences)
    except:
        pass   
    
def unregister():
    from bpy.utils import unregister_class
    unregister_class(ARP_MT_arp_quick_addon_preferences)
   