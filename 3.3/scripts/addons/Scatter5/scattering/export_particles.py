
# oooooooooooo                                               .
# `888'     `8                                             .o8
#  888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo
#  888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888
#  888    "       Y888'     888   888 888   888  888       888
#  888       o  .o8"'88b    888   888 888   888  888       888 .
# o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888"
#                           888
#                          o888o


import bpy, json, os  

from .. resources.icons import cust_icon
from .. resources.translate import translate



def get_instance_data(scatter_obj, dic=None, loc=None):
    """
    return list of points location or return filled dic:

        "particle system name": {

            "instance idx": {
                "instance name":"",
                "location": [],
                "rotation_euler": [],
                "scale": [],

                },
            },
    """
    d = bpy.context.evaluated_depsgraph_get()
    instances = []
    for i in d.object_instances:
        if(i.is_instance):
            if(i.parent.original == scatter_obj):
                instances.append((i.object.original, i.matrix_world.copy()))
    
    #fill given dic with info? 
    if dic is not None: 

        psy_name = scatter_obj.name.replace("scatter_obj : ","")     
        dic[psy_name] = {}

        for i, v in enumerate(instances):
            b, m = v
            l, r, s = m.decompose()
            e = r.to_euler('XYZ', )
            dic[psy_name][str(i)]= {
                "instance name":b.name,
                "location":tuple(l),
                "rotation_euler":(e.x, e.y, e.z, ),
                "scale":tuple(s),
                }
        
        return dic

    if loc is not None:

        for i, v in enumerate(instances):
            _, m = v
            l, _, _ = m.decompose()
            loc.append(l)

        return loc 

    return None 



def get_export_dict(psys):
    """get the export dict information of selected given psys"""

    dic = {}
    for p in psys:
        dic = get_instance_data(p.scatter_obj, dic)

    return dic 



#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o



class SCATTER5_OT_export_to_json(bpy.types.Operator):

    bl_idname  = "scatter5.export_to_json"
    bl_label   = translate("Choose Folder")
    bl_description = translate("Export Selected System(s) Instances visible in the viewport as .json information data.")

    filepath : bpy.props.StringProperty(subtype="DIR_PATH")
    popup_menu : bpy.props.BoolProperty(default=True)

    def execute(self, context):

        if not os.path.isdir(self.filepath): 
            bpy.ops.scatter5.popup_menu(title=translate("Error!"), msgs=translate("Please Select a valid Folder"), icon="ERROR",)
            return {'FINISHED'}

        scat_scene = bpy.context.scene.scatter5 
        emitter    = scat_scene.emitter
        psys_sel   = emitter.scatter5.get_psys_selected()

        dic = get_export_dict(psys_sel)

        #write dict to json in disk
        json_path = os.path.join( self.filepath, "scatter5_export.json" )
        with open(json_path, 'w') as f:
            json.dump(dic, f, indent=4)

        #Great Success!
        if self.popup_menu:
            bpy.ops.scatter5.popup_menu(title=translate("Success!"), msgs=translate("Export Successful"), icon="CHECKMARK", )
        self.popup_menu = True

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}        


class SCATTER5_OT_export_to_instance(bpy.types.Operator):

    bl_idname  = "scatter5.export_to_instance"
    bl_label   = translate("Merge Selected System(s) as Instance")
    bl_description = translate("Merge Selected System(s) Instances visible in the viewport as 'Real' Instances in a newly created export collection.")
    bl_options = {'INTERNAL','UNDO'}

    option : bpy.props.StringProperty() #"remove"/"hide"
    popup_menu : bpy.props.BoolProperty(default=True)

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5 
        emitter    = scat_scene.emitter
        psys_sel   = emitter.scatter5.get_psys_selected()

        dic = get_export_dict(psys_sel)

        #Link Instances

        from .. utils.coll_utils import create_new_collection, collection_clear_obj

        exp_coll = create_new_collection("Scatter5 Export",  parent_name="Scatter5")
        exp_coll.hide_viewport = True 


        for PsyName in dic.keys():
            psy_exp_coll = create_new_collection(f"Export: {PsyName}", parent_name=exp_coll.name)
            collection_clear_obj(psy_exp_coll)

            d = dic[PsyName]
            for k,v in d.items():

                obj = bpy.data.objects.get(v["instance name"])
                mesh = obj.data

                inst = bpy.data.objects.new(name=obj.name+"."+k, object_data=mesh)
                inst.location=v["location"]
                inst.rotation_euler=v["rotation_euler"] 
                inst.scale=v["scale"] 
                psy_exp_coll.objects.link(inst)


        exp_coll.hide_viewport = False
        if self.option=="hide":
            for p in psys_sel: 
                p.hide_viewport = True 
        elif self.option=="remove":
            bpy.ops.scatter5.remove_system(method="selection", undo_push=False, emitter_name=emitter.name) 

        #Great Success!
        if self.popup_menu:
            bpy.ops.scatter5.popup_menu(title=translate("Success!"), msgs=translate("Export Successful"), icon="CHECKMARK",)
        self.popup_menu = True

        return {'FINISHED'}


    def invoke(self, context, event):

        def draw(self, context):
            layout=self.layout
            layout.label(text=translate("What would you like to do with system(s) after Conversion?"))
            layout.separator()
            layout.operator("scatter5.export_to_instance",text=translate("Remove"),icon="TRASH").option = "remove"
            layout.operator("scatter5.export_to_instance",text=translate("Hide"),icon="RESTRICT_VIEW_ON").option = "hide"
            return

        bpy.context.window_manager.popup_menu(draw)

        return {'FINISHED'}        


#           oooo
#           `888
#  .ooooo.   888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# d88' `"Y8  888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888        888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# 888   .o8  888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
# `Y8bod8P' o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = [
    
    SCATTER5_OT_export_to_instance,
    SCATTER5_OT_export_to_json,

    ]