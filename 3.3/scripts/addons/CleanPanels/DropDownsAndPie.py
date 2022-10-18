

import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
from .utils import *
from .workspace_filtering import *
from .Preferences import *
import inspect
import gc
class CP_PT_Custom_Panel(bpy.types.Panel):
    bl_label = "Clean Panels"
    bl_idname = "CP_PT_CP"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Focused"
    bl_order=1000000
    def draw(self, context):
        pass
class PAP_OT_PopUp(bpy.types.Operator):
    bl_idname = "cp.popuppanel"
    bl_label = ":::"
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    is_popover=False
    name: bpy.props.StringProperty(default="",options={'SKIP_SAVE','HIDDEN'})
    call_panel:bpy.props.BoolProperty(default=False,options={'SKIP_SAVE','HIDDEN'})
    def draw(self, context): 
        if not preferences().use_sticky_popup:
            self.layout.label(text="",icon="GRIP")
            self.layout.separator(factor=1)
        if preferences().pop_out_style=='DropDown' and not self.call_panel:
            
            row=self.layout.column() if preferences().columm_layout_for_popup else self.layout.row()
            count=0
            base_type = bpy.types.Panel
            for typename in dir(bpy.types):
                
                try:
                    bl_type = getattr(bpy.types, typename,None)
                    if issubclass(bl_type, base_type):
                        
                        if (getattr(bl_type,"bl_context","")=="" or getattr(bl_type,"bl_context","None")==get_current_context(context)) and (getattr(bl_type,'bl_category',"None")==self.name or getattr(bl_type,"backup_category","None")==self.name) and getattr(bl_type,'bl_space_type',"None")==context.space_data.type and getattr(bl_type,"bl_parent_id","None")=="None":
                            
                            if getattr(bl_type,'poll',None):
                                    
                                if bl_type.poll(context):
                                    count+=1
                                    if count==5:
                                        
                                        row=self.layout.column() if preferences().columm_layout_for_popup else self.layout.row()
                                    row.popover(bl_type.__name__ if not getattr(bl_type,'bl_idname',None) else bl_type.bl_idname, text=getattr(bl_type,'bl_label',"None"))
                            else:
                                count+=1
                                if count==5:
                                    row=self.layout.column() if preferences().columm_layout_for_popup else self.layout.row()
                                row.popover(bl_type.__name__ if not getattr(bl_type,'bl_idname',None) else bl_type.bl_idname, text=getattr(bl_type,'bl_label',"None"))
                            
                except Exception as e:
                    if str(e)!="issubclass() arg 1 must be a class":
                        print(str(e))
            self.layout.ui_units_x=10 if preferences().columm_layout_for_popup else count*4
        else:
            base_type = bpy.types.Panel
            for typename in dir(bpy.types):
                
                try:
                    bl_type = getattr(bpy.types, typename,None)
                    if issubclass(bl_type, base_type):
                        if bl_type.__name__==self.name:
                            if getattr(bl_type,'poll',None):
                                    
                                if bl_type.poll(context):
                                    #print(self.name,typename)
                                    #print(bl_type.__name__)
                                    try:
                                        temp=bl_type(self)
                                        
                                        temp.draw(context)
                                        del temp
                                    except Exception as er:
                                        try:
                                            bl_type.draw(self, context)
                                        except Exception as e:
                                            try:
                                                bl_type._original_draw(self, context)
                                            except Exception as e:
                                                try:
                                                    for obj in gc.get_objects():
                                                        if isinstance(obj, bl_type) and not gc.is_finalized(obj):
                                                            obj.draw(context)
                                                            break
                                                except Exception as er:
                                                    print("Error:",er)
                            else:
                                try:
                                    temp=bl_type(self)
                                    
                                    temp.draw(context)
                                    del temp
                                except Exception as er:
                                    try:
                                        bl_type.draw(self, context)
                                    except Exception as e:
                                        try:
                                            bl_type._original_draw(self, context)
                                        except Exception as e:
                                            try:
                                                for obj in gc.get_objects():
                                                    if isinstance(obj, bl_type) and not gc.is_finalized(obj):
                                                        obj.draw(context)
                                                        break
                                            except Exception as er:
                                                print("Error:",er)
                except Exception as e:
                    if str(e)!="issubclass() arg 1 must be a class":
                        print(str(e))
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        if preferences().pop_out_style=='DropDown' or self.call_panel:
            if preferences().use_sticky_popup:
                return context.window_manager.invoke_props_dialog(self)
            else:
                return context.window_manager.invoke_popup(self)
        else:
            context.scene.pap_last_panel_subcategory=self.name
            
           
            bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Sub_Pie_Menu")
            return {'FINISHED'}
class PAP_OT_Open_Focused_Panel(bpy.types.Operator):
    bl_idname = "cp.focuspanel"
    bl_label = "Open Focused Panel"
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    name: bpy.props.StringProperty(default="",options={'HIDDEN'})
    def execute(self, context):
        st=time.time()
        change_panel_category(self.name,"Focused")
        workspace_category_enabled(preferences().categories,context) 
        return {'FINISHED'}
class PAP_OT_PopUp_Full_Panel(bpy.types.Operator):
    bl_idname = "cp.popupcompletepanel"
    bl_label = ":::"
    bl_description=""
    bl_options = {'REGISTER', 'UNDO'}
    is_popover=False
    name: bpy.props.StringProperty(default="",options={'SKIP_SAVE','HIDDEN'})
    show_panel_1: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_2: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_3: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_4: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_5: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_6: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_7: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_8: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_9: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_10: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_11: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_12: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_13: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_14: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_15: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_16: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_17: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_18: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_19: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_20: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_21: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_22: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_23: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_24: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_25: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_26: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_27: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_28: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_29: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_30: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_31: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_32: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_33: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_34: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_35: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_36: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_37: bpy.props.BoolProperty(default=True,update=panel_opened)
    show_panel_38: bpy.props.BoolProperty(default=True,update=panel_opened)
    def draw(self, context): 
        if not preferences().use_sticky_popup:
            self.layout.label(text=self.name,icon="GRIP")
            self.layout.separator(factor=1)
        count=0
        panels_open=[]
        if not self.panels_to_draw:
            self.layout.label(text="No Panels found!",icon='ERROR')
            self.layout.operator("cp.removedropdownpanel").name=self.name
        for p,has_parent in self.panels_to_draw:
            if has_parent and getattr(p,'bl_parent_id',"None") not in panels_open:
                continue
            count+=1
            row = self.layout.row(align=True)
            if has_parent:
                row=row.split(factor=0.05)
                row.label(text="")
            
            row.scale_x=4
            row.alignment = 'LEFT'
            
            row.prop(self, f"show_panel_{count}", emboss=False,
                    icon="TRIA_DOWN" if getattr(self,f"show_panel_{count}",False) else "TRIA_RIGHT",text=getattr(p, 'bl_label',"Panel") if getattr(p, 'bl_label',"Panel") else "Panel (No Label)")
            
            if (self.name=='Atmosphere'  or self.name=='Physical Starlight and Atmosphere' )and context.scene.world and not has_parent:
                if getattr(context.scene.world,'psa_general_settings',None):
                    row.prop(context.scene.world.psa_general_settings,'enabled',text="")
                    if not context.scene.world.psa_general_settings.enabled:
                        return
            # if getattr(p,'draw_header',None):
            #     try:
            #         temp=p(self)
            #         temp.draw_header(context)
            #         row.separator(factor=1)
            #     except:
            #         pass
            if getattr(self,f"show_panel_{count}",False):
                
                try:
                    temp=p(self)
                    temp.draw(context)
                    panels_open.append(getattr(p,'bl_idname','None'))
                    panels_open.append(getattr(p,'__name__','None'))
                    del temp
                except Exception as er:
                    try:
                        p.draw(self, context)
                        panels_open.append(getattr(p,'bl_idname','None'))
                        panels_open.append(getattr(p,'__name__','None'))
                    except Exception as e:
                        try:
                            p._original_draw(self, context)
                            panels_open.append(getattr(p,'bl_idname','None'))
                            panels_open.append(getattr(p,'__name__','None'))
                        except Exception as e:
                            try:
                                for obj in gc.get_objects():
                                    if isinstance(obj, p) and not gc.is_finalized(obj):
                                        obj.draw(context)
                                        break
                                panels_open.append(getattr(p,'bl_idname','None'))
                                panels_open.append(getattr(p,'__name__','None'))
                            except Exception as er:
                                print("Error:",er)
            
            if self.name=='Atmosphere' or self.name=='Photographer' or self.name=='Physical Starlight and Atmosphere':
                self.layout.enabled=True
        self.layout.ui_units_x=preferences().dropdown_width
        if self.not_reset:
            context.window.cursor_warp(self.mouse_x,self.mouse_y)
            self.not_reset=False
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        
        self.not_reset=True
        if context.scene.pap_opened_panels.find(self.name)>=0:
            t=context.scene.pap_opened_panels[context.scene.pap_opened_panels.find(self.name)]
            opened=[]
            for i in t.pap_opened_panels.split(","):
                opened.append(eval(i))
                setattr(self,f"show_panel_{i}",True)
            for i in range(39):
                if i not in opened:
                    setattr(self,f"show_panel_{i}",False)
        panels_to_draw=[]
        panels_with_parents=[]
        base_type = bpy.types.Panel
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,"bl_category","None")==self.name or getattr(bl_type,"backup_category","None")==self.name or get_module_name(bl_type)==get_module_name_from_addon_name(self.name):
                        
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
        
        if context.scene.pap_opened_panels.find(self.name)<0:
            
            for i,(p,b) in enumerate(panels_to_draw):
                if 'DEFAULT_CLOSED' in getattr(p,'bl_options',[]):
                    setattr(self,f'show_panel_{i+1}',False)
        self.panels_to_draw=panels_to_draw
        self.mouse_x,self.mouse_y=event.mouse_x,event.mouse_y
        if preferences().use_sticky_popup:
            context.window.cursor_warp(event.mouse_x,event.mouse_y-50)
        if preferences().use_sticky_popup:
            return context.window_manager.invoke_props_dialog(self)
            
        else:
            return context.window_manager.invoke_popup(self)