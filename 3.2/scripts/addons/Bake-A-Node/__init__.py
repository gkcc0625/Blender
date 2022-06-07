bl_info = {
    "name": "Bake-A-Node",
    "author": "Amandeep",
    "description": "Bake the output of any shader node",
    "blender": (2, 83, 0),
    "version": (2, 0, 0),
    "location": "N-Panel > Node > Bake-A-Node",
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

import bpy
import os
def bake_texture(context,obj,mat,active_node,res,bake_type="EMIT",samples_to_use=1):
        image_name = obj.name + f"_{active_node.name}_{res}"
                    
        if image_name not in bpy.data.images.keys():
            img = bpy.data.images.new(image_name,res,res,alpha=True,float_buffer=True)
        else:
            #img=bpy.data.images[image_name]
            bpy.data.images.remove(bpy.data.images[image_name])
            img = bpy.data.images.new(image_name,res,res,alpha=True,float_buffer=True)
 
        nodes = mat.node_tree.nodes
        links=mat.node_tree.links
        #if 'Texture_Bake_Node' in [n.name for n in nodes]:
        #    texture_node=nodes.get('Texture_Bake_Node')
        #else:
        texture_node =nodes.new('ShaderNodeTexImage')
        texture_node.name = 'Texture_Bake_Node'
        texture_node.location=-900,-200
        ogLinks=[]
        newLinks=[]
        texture_node.select = True
        nodes.active = texture_node
        texture_node.image = img
         #Assign the image to the node
        engine=bpy.context.scene.render.engine
        use_direct=bpy.context.scene.render.bake.use_pass_direct
        use_indirect=bpy.context.scene.render.bake.use_pass_indirect
        if bake_type in {"COMBINED",}:
            bpy.context.scene.render.bake.use_pass_direct=True
            bpy.context.scene.render.bake.use_pass_indirect=True
        else:
            bpy.context.scene.render.bake.use_pass_direct=True
            bpy.context.scene.render.bake.use_pass_indirect=True
        bpy.context.scene.render.engine = 'CYCLES'
        samples=bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples=samples_to_use
        bpy.context.scene.cycles.device='GPU'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.bake(type=bake_type)
        
        for mat,link in newLinks:
            mat.node_tree.links.remove(link)
        for mat,link in ogLinks:
            mat.node_tree.links.new(link[0],link[1])
        bpy.context.scene.render.engine=engine
        bpy.context.scene.cycles.samples=samples
        bpy.context.scene.render.bake.use_pass_direct=use_direct
        bpy.context.scene.render.bake.use_pass_indirect=use_indirect
        
        if bpy.data.is_saved:            
            filename = bpy.path.basename(bpy.data.filepath)
            filename = os.path.splitext(filename)[0]
            blendname = bpy.path.basename(bpy.data.filepath).rpartition('.')[0]
            filepath = os.path.splitext(bpy.data.filepath)[0] 
            fname=image_name
            if not os.path.exists(filepath):
                os.mkdir(filepath)

            files = [file for file in os.listdir(filepath)
                    if file.startswith(blendname)]
            i=0
            name=image_name
            while(fname+".png" in files):
                fname = f"{name}_{i}"
                #print(fname)
                i+=1
            final_name = os.path.join(filepath, fname+".png")

            if not img:
                return "ERROR"

            img.save_render(final_name, scene=None)
        
        return texture_node

class BAN_PT_Bake_A_Node(bpy.types.Panel):
    bl_label = "Bake-A-Node"
    bl_idname = "OBJECT_PT_BAKE_A_NODE"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Node"
    
    def draw(self, context):
        layout= self.layout
        layout.operator("ban.bakenode")

def sockets(self, context):
    if context.active_node and [(a.name,a.name,a.name) for a in context.active_node.outputs]:
        return [(a.name,a.name,a.name) for a in context.active_node.outputs]
    else:
        return [("None","None","None"),]
def availableuvmaps(self, context):
    return [(uv.name,uv.name,uv.name) for uv in context.active_object.data.uv_layers]
class BAN_OT_Bake_Node(bpy.types.Operator):
    bl_idname = "ban.bakenode"
    bl_label = "Bake Node"
    bl_description = "Bake selected node"
    bl_options = {"REGISTER","UNDO"}
    res:bpy.props.IntProperty(default=1024,name="Resolution",step=1024)
    samples_to_use:bpy.props.IntProperty(default=1,name="Samples")
    socket:bpy.props.EnumProperty(items=sockets,options={'SKIP_SAVE'},name="Output")
    replace:bpy.props.BoolProperty(default=False,name="Replace node with Baked Result",options={'SKIP_SAVE'})
    anotheruv:bpy.props.BoolProperty(default=False,name="Use Another UV Map",options={'SKIP_SAVE'})
    uvsource:bpy.props.EnumProperty(items=availableuvmaps,name="UV Map")
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' and context.material and context.active_node and context.selected_objects and context.selected_nodes
    def draw(self, context):
        layout= self.layout
        layout.prop(self,"res")
        layout.prop(self,"samples_to_use")
        layout.prop(self,"socket")
        layout.prop(self,"replace")
        layout.prop(self,"anotheruv",toggle=True,icon="TRIA_DOWN")
        if self.anotheruv:
            layout.prop(self,"uvsource")
    def execute(self,context):
        socket=self.socket
        mat=context.material
        obj=context.active_object
        active_node=context.active_node
        node_tree=mat.node_tree
        last_output_socket=None
        output_node=None
        baked_node=None
        last_active_uv=None
        for n in node_tree.nodes:
            if n.type=='OUTPUT_MATERIAL' and n.inputs[0].is_linked:
                output_node=n
                last_output_socket=n.inputs[0].links[0].from_socket
        #print(active_node.outputs[self.socket].type)
        if self.anotheruv:
            for a in obj.data.uv_layers:
                if a.active:
                    last_active_uv=a
            for a in obj.data.uv_layers:
                    if a.name==self.uvsource:
                        a.active=True
        if active_node.outputs[socket].type!="SHADER":
            viewer_node=node_tree.nodes.new(type='ShaderNodeEmission')
            node_tree.links.new(active_node.outputs[socket],viewer_node.inputs[0])
            node_tree.links.new(viewer_node.outputs[0],output_node.inputs[0])
            baked_node=bake_texture(context,obj,mat,active_node,self.res,samples_to_use=self.samples_to_use)
        else:
            node_tree.links.new(active_node.outputs[0],output_node.inputs[0])
            baked_node=bake_texture(context,obj,mat,active_node,self.res,bake_type="COMBINED",samples_to_use=self.samples_to_use)
            
        if last_output_socket:
            node_tree.links.new(last_output_socket,output_node.inputs[0])
        if active_node.outputs[socket].type!="SHADER":
            node_tree.nodes.remove(viewer_node)
        if last_active_uv:
            last_active_uv.active=True
        if baked_node and self.replace:
            baked_node.location=active_node.location
            if self.anotheruv:
                uvmap_node=mat.node_tree.nodes.new('ShaderNodeUVMap')
                uvmap_node.uv_map=self.uvsource
                uvmap_node.location=baked_node.location.x-200,baked_node.location.y
                mat.node_tree.links.new(uvmap_node.outputs[0],baked_node.inputs[0])
            for link in active_node.outputs[socket].links:
                node_tree.links.new(baked_node.outputs[0],link.to_socket)
        active_node.select=True
        node_tree.nodes.active=active_node
        return {'FINISHED'}
    def invoke(self, context,event):
        return context.window_manager.invoke_props_dialog(self)
classes = (BAN_OT_Bake_Node,BAN_PT_Bake_A_Node
)

icon_collection={}
addon_keymaps = []

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    kmaps = [
    ]

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        for (op, k, sp) in kmaps:

            kmi = km.keymap_items.new(
                op,
                type=k,
                value="PRESS",
                alt="alt" in sp,
                shift="shift" in sp,
                ctrl="ctrl" in sp,
            )
            addon_keymaps.append((km, kmi))
def unregister():

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
if __name__ == "__main__":
    register()

