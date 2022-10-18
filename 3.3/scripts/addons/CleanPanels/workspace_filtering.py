import os
from webbrowser import get
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
import inspect



    

            
def toggle_filtering_OnOff():
    #print("Initializing")
    if preferences().filtering_method=="Use N-Panel Filtering":
        #workspace_category_enabled(preferences().categories,bpy.context)
        # print("Loading Lists")
        load_renaming_list(bpy.context)
        load_reordering_list(bpy.context)
class PAP_Enable_Category(bpy.types.Operator):
    bl_idname = "cp.enablecategory"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()
    @classmethod
    def description(self, context,properties):
        return preferences().workspace_categories[properties.index].name
    def invoke(self, context, event):
        if not preferences().filtering_method=="Use N-Panel Filtering":
            enabled=[getattr(context.workspace.category_indices,f'enabled_{i}') for i in range(50) if getattr(context.workspace.category_indices,f'enabled_{i}')]
            
            if not event.shift:
                for a in range(50):
                    if a!=self.index:
                        setattr(context.workspace.category_indices,f"enabled_{a}",False)        
            if len(enabled)>1 and not event.shift:
                setattr(context.workspace.category_indices,f"enabled_{self.index}",True)
            else:
                
                setattr(context.workspace.category_indices,f"enabled_{self.index}",not getattr(context.workspace.category_indices,f"enabled_{self.index}",False))
            workspace_category_enabled(context.workspace.category_indices,context)
        else:
            enabled=[getattr(preferences().categories,f'enabled_{i}') for i in range(50) if getattr(preferences().categories,f'enabled_{i}')]
            
            if not event.shift:
                for a in range(50):
                    if a!=self.index:
                        setattr(preferences().categories,f"enabled_{a}",False)        
            if len(enabled)>1 and not event.shift:
                setattr(preferences().categories,f"enabled_{self.index}",True)
            else:
                
                setattr(preferences().categories,f"enabled_{self.index}",not getattr(preferences().categories,f"enabled_{self.index}",False))
            workspace_category_enabled(preferences().categories,context)
        return {"FINISHED"}