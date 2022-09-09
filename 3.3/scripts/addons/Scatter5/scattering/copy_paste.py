



import bpy
from .. resources.translate import translate
from .. resources.icons import cust_icon

from . import presetting
from .. ui import templates


#   .oooooo.                                         88 ooooooooo.                          .                   .oooooo..o               .       .
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  d8P'    `Y8             .o8     .o8
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       `"Y8888o.  d88' `88b   888     888
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888           `"Y88b 888ooo888   888     888
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o      oo     .d8P 888    .o   888 .   888 .
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888"
#                         888       .o..P'
#                        o888o      `Y8P'

#universal copy paste following settings naming system 


BufferSettings = {}

def category_existence(s_category):

    global BufferSettings
    if (s_category not in BufferSettings):
        BufferSettings[s_category] = {}

    return None 

def is_buffer_filled(s_category):

    category_existence(s_category)
    global BufferSettings

    return len(BufferSettings[s_category])!=0 #if empty not copied

def stringify_buffer(s_category):

    return "".join([f"   {k} : {str(v)}\n" for k,v in get_buffer_by_category(s_category)])

def get_buffer_by_category(s_category):

    category_existence(s_category)
    global BufferSettings

    return BufferSettings[s_category].items()

def settings_to_buffer(psy, s_category,):

    buffer = BufferSettings[s_category] 
    for k in psy.bl_rna.properties.keys():
        if k.startswith(s_category):
            buffer[k] = eval(f"psy.{k}") #it's MEH but i'm forced to use eval() -> psy.get(k) will get me enum int and i want string

    return buffer.items() 

def buffer_to_settings(psy, s_category,):
    
    if psy.is_locked(s_category):
        return None
    for k,v in get_buffer_by_category(s_category): #no need to paste every single settings perhaps? (slower)
        if k in psy.bl_rna.properties.keys() : 
            setattr(psy, k, v)

    return None



class SCATTER5_OT_copy_paste(bpy.types.Operator): #Old pasteall copyall was overkill and i disable the dialog box, user can simply copy/paste per category now 

    bl_idname      = "scatter5.copy_paste"
    bl_label       = translate("Paste Buffer Content to Selected System(s)")
    bl_description = ""
    bl_options     = {'REGISTER', 'INTERNAL'}

    s_category : bpy.props.StringProperty()
    copy : bpy.props.BoolProperty()
    paste : bpy.props.BoolProperty()

    @classmethod
    def description(cls, context, properties): 
        prp = properties

        if prp.paste:
            if is_buffer_filled(prp.s_category):
                  return translate("Paste Buffer to settings below") +"\n"+ translate("Content of Buffer") +" : \n"+ stringify_buffer(prp.s_category)
            else: return translate("the Buffer is Empty")
        
        if prp.copy:
            return translate("Copy settings below to Buffer")

        return None 

    def execute(self, context):

        #find emitter object & active psy
        emitter = bpy.context.scene.scatter5.emitter
        
        if self.copy:
            settings_to_buffer(emitter.scatter5.get_psy_active(), self.s_category,)
            self.copy = False #Restore
            return {'FINISHED'}

        if self.paste:
            buffer_to_settings(emitter.scatter5.get_psy_active(), self.s_category,)
            bpy.ops.ed.undo_push(message=translate("Pasting Buffer to Settings"))
            self.paste = False #Restore
            return {'FINISHED'}

        return {'FINISHED'}


# ooooooooo.                                    .         .oooooo..o               .       .
# `888   `Y88.                                .o8        d8P'    `Y8             .o8     .o8
#  888   .d88'  .ooooo.   .oooo.o  .ooooo.  .o888oo      Y88bo.       .ooooo.  .o888oo .o888oo
#  888ooo88P'  d88' `88b d88(  "8 d88' `88b   888         `"Y8888o.  d88' `88b   888     888
#  888`88b.    888ooo888 `"Y88b.  888ooo888   888             `"Y88b 888ooo888   888     888
#  888  `88b.  888    .o o.  )88b 888    .o   888 .      oo     .d8P 888    .o   888 .   888 .
# o888o  o888o `Y8bod8P' 8""888P' `Y8bod8P'   "888"      8""88888P'  `Y8bod8P'   "888"   "888"



class SCATTER5_OP_reset_settings_to_default(bpy.types.Operator):

    bl_idname      = "scatter5.reset_settings_to_default"
    bl_label       = translate("Reset Settings to their Default Values")
    bl_description = translate("Reset Settings to their Default Values")
    bl_options     = {'INTERNAL', 'UNDO'}

    s_category : bpy.props.StringProperty()
    method : bpy.props.StringProperty(default="selection")

    def execute(self, context):

        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]
        
        settings = [k for k in psys[0].bl_rna.properties.keys() if k.startswith(self.s_category) ]
        for p in psys:
            for s in settings:
                try:
                    #try to find default
                    pro = p.bl_rna.properties[s] 
                    if (pro.type=="ENUM") or (pro.type=="STRING") or (pro.type=="BOOLEAN"):
                        default= pro.default
                    elif (pro.type=="FLOAT"):
                        if pro.array_length==0:
                              default= pro.default
                        else: default= pro.default_array
                    setattr(p, s, default)
                except Exception as e:
                    pass
                    
        return {'FINISHED'}


#   .oooooo.                                         88 ooooooooo.                          .                  ooooooooo.
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  `888   `Y88.
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.        888   .d88'  .oooo.o oooo    ooo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       888ooo88P'  d88(  "8  `88.  .8'
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888       888         `"Y88b.    `88..8'
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o       888         o.  )88b    `888'
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      o888o        8""888P'     .8'
#                         888       .o..P'                                                                                           .o..P'
#                        o888o      `Y8P'                                                                                            `Y8P'



BufferPsy = {}

def is_bufferpsy_filled():

    global BufferPsy

    return len(BufferPsy)!=0

def clear_bufferpsy():

    global BufferPsy
    BufferPsy.clear()

    return None 



class SCATTER5_OP_copy_paste_systems(bpy.types.Operator):

    bl_idname      = "scatter5.copy_paste_systems"
    bl_label       = translate("Copy Selected/Paste particle-system(s)")
    bl_description = translate("Copy Selected/Paste particle-system(s)")
    bl_options     = {'INTERNAL', 'UNDO'}

    copy : bpy.props.BoolProperty()
    paste : bpy.props.BoolProperty()
    synchronize : bpy.props.BoolProperty()
    emitter : bpy.props.StringProperty()
    method : bpy.props.StringProperty(default="selection")

    @classmethod
    def description(cls, context, properties): 
        txt =""
        if properties.copy ==True:
            txt+= translate("Copy the selected particle-system(s)")
        else: 
            txt+= translate("Paste particle_system(s) from Buffer")
        if properties.synchronize==True:
            txt+= " "
            txt+= translate("and Synchronize their settings with the source")
        return txt

    def execute(self, context):

        global BufferPsy

        #define obj
        scat_scene = bpy.context.scene.scatter5
        #find emitter obj
        if self.emitter=="":
              emitter = scat_scene.emitter
        else: emitter = bpy.data.objects[self.emitter]
        #find selected psys
        psys = emitter.scatter5.get_psys_selected() if (self.method=="selection") else [ emitter.scatter5.get_psy_active() ]

        if self.copy==True:

            clear_bufferpsy()

            for p in psys:

                d = presetting.settings_to_dict(p, use_random_seed=False, texture_is_unique=False, texture_random_loc=False, get_estimated_density=False,)

                #add extra info
                d["initial_instances"]= list(p.s_instances_coll_ptr.objects) #add info for instances
                d["initial_emitter"]= emitter.name #add info for synchronization if needed

                #add dict to buffer
                BufferPsy[p.name]= d 

        elif self.paste==True:

            if is_bufferpsy_filled():

                bpy.ops.scatter5.toggle_selection(deselect=True)

                for initial_name, d in BufferPsy.items():

                    p = emitter.scatter5.add_virgin_psy( psy_name=initial_name+"_copy", instances=d["initial_instances"],)
                    p.sel=True
                    p.hide_viewport=True

                    presetting.dict_to_settings( d, p, )

                    #synchronize? only if initial psy still exists
                    #IDEALLY SHOULD BE DONE WITH : scat_scene.sync_channels.synchronize_members(m1,m2,m..)

                    if self.synchronize==True:

                        initial_emitter = bpy.data.objects.get( d["initial_emitter"] )
                        if initial_emitter is not None:
                            if initial_name in initial_emitter.scatter5.particle_systems:

                                #create new channel
                                sync_channels= scat_scene.sync_channels
                                if initial_name not in sync_channels:
                                      ch = bpy.context.scene.scatter5.sync_channels.add()
                                      ch.name= initial_name
                                else: ch = sync_channels[initial_name]
                                #add new members to channel
                                if not ch.psy_in_channel(initial_emitter.name, initial_name):
                                    mem = ch.members.add()
                                    mem.psy_name = initial_name
                                    mem.m_emitter = initial_emitter
                                #add new members to channel
                                if not ch.psy_in_channel(emitter.name, p.name):
                                    mem = ch.members.add()
                                    mem.psy_name = p.name
                                    mem.m_emitter = emitter

        #reset properties
        self.copy = self.paste = self.synchronize = False    
        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = [

    SCATTER5_OT_copy_paste,
    SCATTER5_OP_copy_paste_systems,
    SCATTER5_OP_reset_settings_to_default,

    ]
