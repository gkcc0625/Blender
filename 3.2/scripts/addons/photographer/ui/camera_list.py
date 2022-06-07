import bpy

from ..functions import list_collections, traverse_tree, list_cameras
from ..constants import addon_name


def camera_row(context,cam,col):
    cam_obj = bpy.data.objects.get(cam)
    cam_settings = cam_obj.data.photographer
    scene = context.scene

    row = col.row(align=True)
    row.scale_y = 1.25
    if scene.camera and scene.camera == bpy.data.objects.get('MasterCamera'):
        target_camera = scene.camera.data.photographer.target_camera
        icn = "PLAY"
        if target_camera and cam == target_camera.name:
            icn = "RADIOBUT_ON"
        row.operator("view3d.switch_camera", text="", icon=icn).camera=cam
    else:
        row.prop(cam_settings, "renderable", text="")

    if scene.camera == bpy.data.objects.get(cam):
        row.operator("mastercamera.look_through", text="", icon='RESTRICT_RENDER_OFF').camera=cam
    else:
        row.operator("mastercamera.look_through", text="", icon='RESTRICT_RENDER_ON').camera=cam

    sel = row.operator("photographer.select", text='',
                    icon="%s" % 'RESTRICT_SELECT_OFF'if cam_obj.select_get()
                    else 'RESTRICT_SELECT_ON').obj_name = cam


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

    # Master camera UI
    if bpy.context.preferences.addons[addon_name].preferences.show_master_camera:
        box = layout.box()
        master_row = box.row(align=True)

        if master_cam: #in cam_list:
            if context.scene.camera == bpy.data.objects.get(master_cam):
                master_row.operator("mastercamera.look_through", text="", icon='VIEW_CAMERA').camera=master_cam
            else:
                master_row.operator("mastercamera.look_through", text="", icon='CAMERA_DATA').camera=master_cam
            master_row.operator("photographer.select", text=master_cam).obj_name=master_cam
            master_row.operator("mastercamera.delete_cam", text="", icon="PANEL_CLOSE", emboss=False).camera=master_cam
            col = box.column(align=True)
            col.prop(bpy.data.objects.get(master_cam).data.photographer, "match_speed", slider=True)
            if context.scene.camera == bpy.data.objects.get(master_cam):
                col.operator("mastercamera.set_key", text='Set Key', icon='KEY_HLT')
        else:
            master_row.operator("mastercamera.add_mastercam", text='Add Master Camera', icon='OUTLINER_DATA_CAMERA')

    # Camera list UI
    box = layout.box()
    row = box.row(align=False)
    row.operator("mastercamera.add_cam")
    sub = row.row(align=True)
    sub.operator('view3d.cycle_camera', text='', icon='TRIA_LEFT').previous=True
    sub.operator('view3d.cycle_camera', text='', icon='TRIA_RIGHT').previous=False
    row.prop(scene.photographer,'cam_list_sorting', icon_only=True, expand=True)

    if not cam_list:
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="No Camera in the Scene", icon='INFO')

    if scene.photographer.cam_list_sorting == 'COLLECTION':
        # collections = list_collections(context)

        for coll in cam_collections:
            coll_cams = [obj.name for obj in coll.objects if obj.type=='CAMERA']
            if coll_cams:
                if master_cam in coll_cams:
                    coll_cams.remove('MasterCamera')
                coll_cams= sorted(coll_cams)
                # If not in a Collection, add camera to the base layout
                if coll.name in {'Master Collection', 'Scene Collection'}:
                    coll_box = box.column(align=True)
                    exclude = False
                else:
                    coll_box = box.box()
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
                        camera_row(context,cam,parent_col)
    else:
        # Alphabetical Sorting
        col = box.column(align=True)
        for cam in cam_list:
            camera_row(context,cam,col)

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
        layout.operator("photographer.applyphotographersettings", text="Refresh Photographer Settings")

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


class PHOTOGRAPHER_PT_ViewPanel_CameraList(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Camera List"
    bl_order = 0

    def draw(self, context):
        camera_list_panel(context,self.layout)
