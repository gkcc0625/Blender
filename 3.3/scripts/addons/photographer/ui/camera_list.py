import bpy
from ..functions import traverse_tree, list_cameras
from ..constants import addon_name
from ..rigs.build_rigs import get_camera_rig


def camera_row(context,cam,col):
    # cam_obj = bpy.data.objects.get(cam)
    cam_obj = cam
    cam = cam.name
    scene = context.scene

    # if cam_obj.type=='CAMERA':
    cam_settings = cam_obj.data.photographer

    row = col.row(align=True)
    # row.scale_y = 1
    if scene.camera and scene.camera == bpy.data.objects.get('MasterCamera'):
        target_camera = scene.camera.data.photographer.target_camera
        icn = "PLAY"
        if target_camera and cam == target_camera.name:
            icn = "RADIOBUT_ON"
        row.operator("view3d.switch_camera", text="", icon=icn).camera=cam
    else:
        row.prop(cam_settings, "renderable", text="")

    if scene.camera == cam_obj:
        row.operator("mastercamera.look_through", text="", icon='RESTRICT_RENDER_OFF').camera=cam
    else:
        row.operator("mastercamera.look_through", text="", icon='RESTRICT_RENDER_ON').camera=cam

    sel = row.operator("photographer.select", text='',
                    icon="%s" % 'RESTRICT_SELECT_OFF'if cam_obj.select_get()
                    else 'RESTRICT_SELECT_ON').obj_name = cam

    if cam_obj.get('is_rigged', False):
        rig_obj = get_camera_rig(cam_obj)
        if rig_obj:
            row.operator("photographer.select", text='',
                        icon="%s" % 'OUTLINER_OB_ARMATURE'if rig_obj.select_get()
                        else 'ARMATURE_DATA').obj_name = rig_obj.name

    row.prop(bpy.data.objects[cam], "name", text='')
    if cam_settings.show_focus_plane:
        row.operator("photographer.delete_focus_plane", text="", icon='CANCEL').camera=cam
    else:
        row.operator("photographer.create_focus_plane", text="", icon='NORMALS_FACE').camera=cam
    if cam_settings.target_enabled:
        row.operator("photographer.target_delete", text="", icon='CANCEL').obj_name=cam
    else:
        row.operator("photographer.target_add", text="", icon='TRACKER').obj_name=cam
    row.operator("mastercamera.delete_cam", text="", icon='PANEL_CLOSE', emboss=False).camera=cam

    if cam not in context.view_layer.objects:
        row.enabled = False


def camera_list_panel(context,parent_ui):
    layout = parent_ui
    scene = context.scene

    cam_list,master_cam,cam_collections = list_cameras(context)

    # Camera list UI
    box = layout.box()
    panel_row = box.row(align=False)
    panel_col = panel_row.column()

    if not cam_list:
        row = panel_col.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="No Camera in the Scene", icon='INFO')

    if scene.photographer.cam_list_sorting == 'COLLECTION':
        # collections = list_collections(context)

        for coll in cam_collections:
            coll_cams = [obj.name for obj in coll.objects if obj.type=='CAMERA' and obj.name!='MasterCamera']
            if coll_cams:
                coll_cams= sorted(coll_cams)
                # If not in a Collection, add camera to the base layout
                if coll.name in {'Master Collection', 'Scene Collection'}:
                    coll_box = panel_col.row(align=True)
                    exclude = False
                else:
                    
                    coll_box = panel_col.box()
                    coll_row = coll_box.row(align=True)
                    exp = coll_row.operator("photographer.collection_expand", text="",
                                    icon='TRIA_DOWN' if coll.get('cl_expand', True) else 'TRIA_RIGHT',
                                    emboss=False)
                    exp.collection=coll.name
                    exp.cam_list=True

                    if bpy.app.version >= (2, 91, 0):
                        color_tag = 'OUTLINER_COLLECTION'if coll.color_tag == 'NONE' else 'COLLECTION_'+ coll.color_tag
                    else:
                        color_tag = 'GROUP'
                    sel = coll_row.operator('photographer.select_collection', text='', icon=color_tag)
                    sel.coll_name = coll.name
                    sel.coll_type = 'CAMERA'
                    coll_row.prop(coll, "name", text='')

                    # Find Layer Collection inside the tree
                    lc = [c for c in traverse_tree(context.view_layer.layer_collection) if c.name == coll.name][0]
                    coll_row.prop(lc, "exclude", text='', icon_only=True, emboss=False)
                    # coll_row.prop(coll, "hide_viewport", text='', icon_only=True, emboss=False)
                    coll_row.prop(coll, "hide_render", text='', icon_only=True, emboss=False)
                    exclude = lc.exclude

                # Add cameras into Collection box
                if coll.get('cl_expand', True) and not exclude:
                    parent_col = coll_box.column(align=True)
                    for cam in coll_cams:
                        # Disable light boxes if Collection is hidden in Viewport
                        if coll.hide_viewport:
                            col.enabled = False
                        cam_obj = bpy.data.objects.get(cam)
                        camera_row(context,cam_obj,parent_col)
    else:
        # # Alphabetical Sorting
        # col = box.column(align=True)
        # for cam in cam_list:
        #     camera_row(context,cam,col)
        panel_col.template_list("PHOTOGRAPHER_UL_ViewPanel_CameraList", "Camera List", bpy.data,
                "objects", scene.photographer, "active_camera_index")
    col = panel_row.column(align=True)
    col.operator("mastercamera.add_cam", text='', icon="ADD")
    col.operator("mastercamera.duplicate_cam",text="", icon='DUPLICATE')
    col.separator()
    order = True
    if scene.photographer.cam_filter_reverse:
        order = not order
    col.operator('view3d.cycle_camera', text='', icon='TRIA_UP').previous=order
    col.operator('view3d.cycle_camera', text='', icon='TRIA_DOWN').previous=not order
    col.separator()
    col.prop(scene.photographer,'cam_list_sorting', icon_only=True, expand=True)

    # Lock Camera to View and Border
    view = context.space_data
    render = scene.render
    if view.lock_camera:
        icon="LOCKVIEW_ON"
    else:
        icon="LOCKVIEW_OFF"

    row = layout.row()
    split = row.split(factor=0.7, align=False)
    split.prop(view, "lock_camera", text="Lock Camera to View", icon=icon )
    split.prop(render, "use_border", text="Border")

    if scene.camera and scene.camera.type == 'CAMERA':
        # photographer = context.scene.camera.data.photographer
        layout.operator("photographer.applyphotographersettings",
            text="Refresh Photographer Settings",
            icon='FILE_REFRESH')
        

    # Master camera UI
    if bpy.context.preferences.addons[addon_name].preferences.show_master_camera:
        box = layout.box()
        master_row = box.row(align=True)

        if master_cam: #in cam_list:
            if context.scene.camera == bpy.data.objects.get(master_cam):
                icn ='RESTRICT_RENDER_OFF'
            else:
                icn = 'RESTRICT_RENDER_ON'
            master_row.operator("photographer.select", text="",
                icon="%s" % 'RESTRICT_SELECT_OFF' if bpy.data.objects['MasterCamera'].select_get()
                else 'RESTRICT_SELECT_ON').obj_name=master_cam
            master_row.operator("mastercamera.look_through", text=master_cam, icon=icn).camera=master_cam
            master_row.operator("mastercamera.delete_cam", text="", icon="PANEL_CLOSE", emboss=False).camera=master_cam
            col = box.column(align=True)
            col.prop(bpy.data.objects.get(master_cam).data.photographer, "match_speed", slider=True)
            if context.scene.camera == bpy.data.objects.get(master_cam):
                col.operator("mastercamera.set_key", text='Set Key', icon='KEY_HLT')
        else:
            master_row.operator("mastercamera.add_mastercam", text='Add Master Camera', icon='OUTLINER_DATA_CAMERA')

    # # Render button
    # if scene.camera:
    #     if scene.camera == bpy.data.objects.get(master_cam):
    #         layout.operator("render.render",text="Render Master Camera").write_still=True
    #     else:
    #         col = layout.column(align=True)
    #         row = col.row(align=True)
    #         row.operator("render.render",text="Render Active").write_still=True
    #         row.operator("render.renderallbutton")
    #         renderable_cams = [c for c in cameras if c.data.photographer.renderable == True]
    #         row = col.row(align=True)
    #         row.prop(render, "filepath", text="")


class PHOTOGRAPHER_UL_ViewPanel_CameraList(bpy.types.UIList):
    """View Layer List for View Panel"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index):
        col = layout.column(align=True)
        camera_row(context,item,col)

    def draw_filter(self, context, layout):
        settings = context.scene.photographer
        layout.separator()
        col_main = layout.column(align=True)

        row = col_main.row(align=True)
        row.prop(settings, 'cam_filter', text='', icon='VIEWZOOM')
        if settings.cam_filter:
            row.operator("photographer.button_string_clear", text='',icon='PANEL_CLOSE',emboss=False).prop='cam_filter'
        row.prop(self, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(settings, 'cam_filter_reverse', text='', icon='SORT_DESC' if settings.cam_filter_reverse else "SORT_ASC")

    def filter_items(self,context,data,propname):
        settings = context.scene.photographer
        filtered = []
        ordered = []
        items = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        filtered = [self.bitflag_filter_item] * len(items)
        self.use_filter_sort_reverse = settings.cam_filter_reverse

        ordered = helper_funcs.sort_items_by_name(items, "name")

        filtered_items = self.get_props_filtered_items()

        for i, item in enumerate(items):
            if not item in filtered_items:
                filtered[i] &= ~self.bitflag_filter_item

        return filtered,ordered

    def get_props_filtered_items(self):
        settings = bpy.context.scene.photographer

        filtered_items = [o for o in bpy.context.scene.objects if o.type=='CAMERA' and o.name!='MasterCamera']
        if settings.cam_filter:
            filtered_items = [o for o in filtered_items if not o.name.lower().find(settings.cam_filter.lower()) == -1]

        return filtered_items

class PHOTOGRAPHER_PT_ViewPanel_CameraList(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Camera List"
    bl_order = 0

    def draw_header_preset(self, context):
        layout = self.layout
        if context.preferences.addons[addon_name].preferences.show_compact_ui:
            cam_list,master_cam,cam_collections = list_cameras(context)
            if not cam_list:
                layout.operator("mastercamera.add_cam", text='Add Camera', icon="ADD")
            else:
                layout.prop(context.scene.photographer, "active_scene_camera",text='')
            
            layout.separator()

    def draw(self, context):
        camera_list_panel(context,self.layout)
