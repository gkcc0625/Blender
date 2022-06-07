import os

import bpy

from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import *
from bpy.utils import register_class, unregister_class

from . utility import addon, shader, update, modifier

from . t3dn_bip.utils import support_pillow


authoring_enabled = True
try: from . utility import matrixmath
except:
    authoring_enabled = False

class folder(PropertyGroup):
    icon: StringProperty(default='FILE_FOLDER')

    name: StringProperty(
        name = 'Path Name',
        default = '')

    visible: BoolProperty(
        name = 'Visible',
        description = 'Show KPACKS from this folder',
        default = True)

    location: StringProperty(
        name = 'Path',
        description = 'Path to KIT OPS library',
        update = update.libpath,
        subtype = 'DIR_PATH',
        default = '')

class favorite(PropertyGroup):
    pass

class recent(PropertyGroup):
    pass

class kitops(AddonPreferences):
    bl_idname = addon.name

    context: EnumProperty(
        name = 'Context',
        description = 'KIT OPS preference settings context',
        items = [
            ('GENERAL', 'General', ''),
            # ('THEME', 'Theme', ''),
            ('FILEPATHS', 'File Paths', '')],
        default = 'GENERAL')

    folders: CollectionProperty(type=folder)

    author: StringProperty(
        name = 'Author',
        description = 'Name that will be used when creating INSERTS',
        default = 'Your Name')

    insert_offset_x: IntProperty(
        name = 'INSERT offset X',
        description = 'Offset used when adding the INSERT from the mouse cursor',
        soft_min = -40,
        soft_max = 40,
        subtype = 'PIXEL',
        default = 0)

    insert_offset_y: IntProperty(
        name = 'INSERT offset Y',
        description = 'Offset used when adding the INSERT from the mouse cursor',
        soft_min = -40,
        soft_max = 40,
        subtype = 'PIXEL',
        default = 20)

    clean_names: BoolProperty(
        name = 'Clean names',
        description = 'Capatilize and clean up the names used in the UI from the KPACKS',
        update = update.kpack,
        default = False)

    clean_datablock_names: BoolProperty(
        name = 'Clean datablock names',
        description = 'Capatilize and clean up the names used for datablocks within INSERTS',
        default = False)

    thumbnail_labels: BoolProperty(
        name = 'Thumbnail labels',
        description = 'Displays names of INSERTS under the thumbnails in the preview popup',
        default = True)

    border_color: FloatVectorProperty(
        name = 'Border color',
        description = 'Color used for the border',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    border_size: IntProperty(
        name = 'Border size',
        description = 'Border size in pixels\n  Note: DPI factored',
        min = 1,
        soft_max = 6,
        subtype = 'PIXEL',
        default = 1)

    border_offset: IntProperty(
        name = 'Border size',
        description = 'Border size in pixels\n  Note: DPI factored',
        min = 1,
        soft_max = 16,
        subtype = 'PIXEL',
        default = 8)

    logo_color: FloatVectorProperty(
        name = 'Logo color',
        description = 'Color used for the KIT OPS logo',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    off_color: FloatVectorProperty(
        name = 'Off color',
        description = 'Color used for the KIT OPS logo when there is not an active insert with an insert target',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (0.448, 0.448, 0.448, 0.1))

    logo_size: IntProperty(
        name = 'Logo size',
        description = 'Logo size in the 3d view\n  Note: DPI factored',
        min = 1,
        soft_max = 500,
        subtype = 'PIXEL',
        default = 10)

    logo_padding_x: IntProperty(
        name = 'Logo padding x',
        description = 'Logo padding in the 3d view from the border corner\n  Note: DPI factored',
        subtype = 'PIXEL',
        default = 18)

    logo_padding_y: IntProperty(
        name = 'Logo padding y',
        description = 'Logo padding in the 3d view from the border corner\n  Note: DPI factored',
        subtype = 'PIXEL',
        default = 12)

    logo_auto_offset: BoolProperty(
        name = 'Logo auto offset',
        description = 'Offset the logo automatically for HardOps and BoxCutter',
        default = True)

    text_color: FloatVectorProperty(
        name = 'Text color',
        description = 'Color used for the KIT OPS help text',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    # displayed in panel
    mode: EnumProperty(
        name = 'Mode',
        description = 'Insert mode',
        items = [
            ('REGULAR', 'Regular', 'Stop creating modifiers for all INSERT objs except for new INSERTS\n  Note: Removes all insert targets'),
            ('SMART', 'Smart', 'Create modifiers as you work with an INSERT on the target obj')],
        update = update.mode,
        default = 'REGULAR')

    insert_scale: EnumProperty(
        name = 'Insert Scale',
        description = 'Insert scale mode based on the active obj when adding an INSERT',
        items = [
            ('LARGE', 'Large', ''),
            ('MEDIUM', 'Medium', ''),
            ('SMALL', 'Small', '')],
        update = update.insert_scale,
        default = 'LARGE')

    large_scale: IntProperty(
        name = 'Primary Scale',
        description = 'Percentage of obj size when adding an INSERT for primary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 100)

    medium_scale: IntProperty(
        name = 'Secondary Scale',
        description = 'Percentage of obj size when adding an INSERT for secondary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 50)

    small_scale: IntProperty(
        name = 'Tertiary Scale',
        description = 'Percentage of obj size when adding an INSERT for tertiary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 25)

    auto_scale: BoolProperty(
        name = 'Auto scale INSERT',
        description = 'Scale INSERTS based on obj size',
        default = True)

    parent_inserts: BoolProperty(
        name = 'Parent INSERTs to the target object',
        description = 'Automatically Parent the INSERTS to the target object',
        default = False)

    boolean_solver: EnumProperty(
        name='Solver',
        description='',
        items=[
            ('FAST', 'Fast', 'fast solver for booleans'),
            ('EXACT', 'Exact', 'exact solver for booleans')],
        default='FAST')

    place_on_insert : BoolProperty(
            name = 'Place on selected INSERT',
            description = ('Place the object on the existing INSERT.  The new INSERT will still be associated with the target object. \n'
                    ' Keyboard shortcut: P'),
            default = False)

    snap_mode : EnumProperty(
            name = 'Snap Mode',
            description = '',
            items = [
                ('NONE', 'None', 'No snapping \n Keyboard shortcut: N', 'CANCEL', 1),
                ('FACE', 'Face', 'Snap to face \n Keyboard shortcut: F', 'SNAP_FACE', 2),
                ('EDGE', 'Edge', 'Snap to edge \n Keyboard shortcut: E [C - Toggle Snap to Edge Center]', 'SNAP_EDGE', 3),
                ('VERTEX', 'Vertex', 'Snap to vertex \n Keyboard shortcut: V', 'SNAP_VERTEX', 4)],
            default = 'NONE')

    snap_mode_edge : EnumProperty(
            name = 'Snap Mode For Edges',
            description = '',
            items = [
                ('NEAREST', 'Nearest', 'Snap to nearest point on edge \n Keyboard shortcut: C'),
                ('CENTER', 'Center', 'Snap to edge center \n Keyboard shortcut: C')],
            default = 'NEAREST')

    flip_placement : BoolProperty(
        name = "Flip Placement",
        description=("Flip the target object placement so the INSERT is added to the inside of the target object \n"
                    " Keyboard shortcut: I"),
        default=False

    )

    favorites : CollectionProperty(type=favorite)

    recently_used : CollectionProperty(type=recent)

    show_favorites: BoolProperty(
        name = 'Show Favorites',
        description = 'Show shortcuts to my favorite KPACKS',
        default = True)

    show_recents: BoolProperty(
        name = 'Show Recently Used',
        description = 'Show shortcuts to my most recently used KPACKS',
        default = True)

    sort_modifiers: BoolProperty(
        name = 'Sort Modifiers',
        description = '\n Sort modifier order',
        update = update.sync_sort,
        default = False)

    sort_smooth: BoolProperty(
        name = 'Sort Smooth',
        description = '\n Ensure smooth modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_bevel: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Ensure bevel modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_weighted_normal: BoolProperty(
        name = 'Sort Weighted Normal',
        description = '\n Ensure weighted normal modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_array: BoolProperty(
        name = 'Sort Array',
        description = '\n Ensure array modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_mirror: BoolProperty(
        name = 'Sort Mirror',
        description = '\n Ensure mirror modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_solidify: BoolProperty(
        name = 'Sort Soldify',
        description = '\n Ensure solidify modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_triangulate: BoolProperty(
        name = 'Sort Triangulate',
        description = '\n Ensure triangulate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_simple_deform: BoolProperty(
        name = 'Sort Simple Deform',
        description = '\n Ensure simple deform modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_decimate: BoolProperty(
        name = 'Sort Decimate',
        description = '\n Ensure decimate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_remesh: BoolProperty(
        name = 'Sort Remesh',
        description = '\n Ensure remesh modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_subsurf: BoolProperty(
        name = 'Sort Subsurf',
        description = '\n Ensure subsurf modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_weld: BoolProperty(
        name = 'Sort Weld',
        description = '\n Ensure weld modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_smooth_last: BoolProperty(
        name = 'Sort Smooth',
        description = '\n Only effect the most recent smooth modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_uv_project: BoolProperty(
        name = 'Sort UV Project',
        description = '\n Ensure uv project modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_bevel_last: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Only effect the most recent bevel modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_weighted_normal_last: BoolProperty(
        name = 'Sort Weighted Normal Last',
        description = '\n Only effect the most recent weighted normal modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_array_last: BoolProperty(
        name = 'Sort Array Last',
        description = '\n Only effect the most recent array modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_mirror_last: BoolProperty(
        name = 'Sort Mirror Last',
        description = '\n Only effect the most recent mirror modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_solidify_last: BoolProperty(
        name = 'Sort Soldify Last',
        description = '\n Only effect the most recent solidify modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_triangulate_last: BoolProperty(
        name = 'Sort Triangulate Last',
        description = '\n Only effect the most recent triangulate modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_simple_deform_last: BoolProperty(
        name = 'Sort Simple Deform Last',
        description = '\n Only effect the most recent simple deform modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_decimate_last: BoolProperty(
        name = 'Sort Decimate Last',
        description = '\n Only effect the most recent decimate modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_remesh_last: BoolProperty(
        name = 'Sort Remesh Last',
        description = '\n Only effect the most recent remesh modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_subsurf_last: BoolProperty(
        name = 'Sort Subsurf Last',
        description = '\n Only effect the most recent subsurface modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_weld_last: BoolProperty(
        name = 'Sort Weld Last',
        description = '\n Only effect the most recent weld modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_uv_project_last: BoolProperty(
        name = 'Sort UV Project Last',
        description = '\n Only effect the most recent uv project modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_weight: BoolProperty(
        name = 'Ignore Weight Bevels',
        description = '\n Ignore bevel modifiers that are using the weight limit method while sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_vgroup: BoolProperty(
        name = 'Ignore VGroup Bevels',
        description = '\n Ignore bevel modifiers that are using the vertex group limit method while sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_only_verts: BoolProperty(
        name = 'Ignore Only Vert Bevels',
        description = '\n Ignore bevel modifiers that are using the only vertices option while sorting',
        update = update.sync_sort,
        default = True)

    sort_depth: IntProperty(
        name = 'Sort Depth',
        description = '\n Number of sortable mods from the end (bottom) of the stack. 0 to sort whole stack',
        min = 0,
        default = 6)

    sort_ignore_char: StringProperty(
        name = 'Ignore Flag',
        description = '\n Prefix the modifier name with this text character and it will be ignored\n  Default: Space',
        update = update.sort_ignore_char,
        maxlen = 1,
        default = ' ')

    sort_stop_char: StringProperty(
        name = 'Stop Flag',
        description = '\n Prefix a modifier name with this text character and it will not sort modifiers previous to it',
        update = update.sort_stop_char,
        maxlen = 1,
        default = '_')


    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(self, 'context', expand=True)

        box = column.box()

        box.separator()
        getattr(self, self.context.lower())(context, box)
        box.separator()


    def general(self, context, layout):
        row = layout.row()
        row.label(text='Author')
        row.prop(self, 'author', text='')

        layout.separator()

        row = layout.row()
        row.label(text='INSERT offset X')
        row.prop(self, 'insert_offset_x', text='')

        row = layout.row()
        row.label(text='INSERT offset Y')
        row.prop(self, 'insert_offset_y', text='')

        if bpy.app.version > (2, 90, 0):
            row = layout.row()
            row.label(text='Boolean Solver')
            row.prop(self, 'boolean_solver', expand=True)

        row = layout.row()
        row.label(text='Thumbnail labels')
        row.prop(self, 'thumbnail_labels', text='')

        row = layout.row()

        row = layout.row()
        row.label(text='Sort Modifiers')
        row.prop(self, 'sort_modifiers', text='')

        if self.sort_modifiers:
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            split = row.split(align=True, factor=0.85)

            row = split.row(align=True)
            for type in modifier.sort_types:
                icon = F'MOD_{type}'
                if icon == 'MOD_WEIGHTED_NORMAL':
                    icon = 'MOD_NORMALEDIT'
                elif icon == 'MOD_SIMPLE_DEFORM':
                    icon = 'MOD_SIMPLEDEFORM'
                elif icon == 'MOD_DECIMATE':
                    icon = 'MOD_DECIM'
                elif icon == 'MOD_WELD':
                    icon = 'AUTOMERGE_OFF'
                elif icon == 'MOD_UV_PROJECT':
                    icon = 'MOD_UVPROJECT'
                row.prop(self, F'sort_{type.lower()}', text='', icon=icon)

            row = split.row(align=True)
            row.scale_x = 1.5
            row.popover('KO_PT_sort_last', text='', icon='SORT_ASC')

        row = layout.row()
        row.operator('ko.export_settings')
        row.operator('ko.import_settings')

        # Pillow

        box = layout.box()
        supported = support_pillow()

        col = box.column()
        if supported:
            col.label(text="Thumbnail Caching: Enabled")
        else:
            col.label(text="Thumbnail Caching: Disabled")

        col.separator()
        col.label(text="While the thumbnail cache accelerator is not required, it provides a superior user experience. ")
        col.label(text="You must have a working INTERNET connection on order to install it, and it only needs to install once.")
        col.separator()

        if supported:
            col.operator('ko.install_pillow', text="Thumbnail Caching Engine Installed Successfully")
        else:
            col.operator('ko.install_pillow', text="Install Thumbnail Caching Engine")

        #Favorites
        if authoring_enabled:
            col = layout.column()
            col.label(text="Favorites")
            col.separator()
            col.operator("ko.clear_favorites_confirm", text="Clear All Favorites")





    def theme(self, context, layout):
        row = layout.row()
        row.label(text='Border color')
        row.prop(self, 'border_color', text='')

        row = layout.row()
        row.label(text='Border size')
        row.prop(self, 'border_size', text='')

        row = layout.row()
        row.label(text='Border offset')
        row.prop(self, 'border_offset', text='')

        row = layout.row()
        row.label(text='Logo color')
        row.prop(self, 'logo_color', text='')

        row = layout.row()
        row.label(text='Off color')
        row.prop(self, 'off_color', text='')

        row = layout.row()
        row.label(text='Logo size')
        row.prop(self, 'logo_size', text='')

        row = layout.row()
        row.label(text='Logo padding x')
        row.prop(self, 'logo_padding_x', text='')

        row = layout.row()
        row.label(text='Logo padding y')
        row.prop(self, 'logo_padding_y', text='')

        row = layout.row()
        row.label(text='Logo auto offset')
        row.prop(self, 'logo_auto_offset', text='')

        row = layout.row()
        row.label(text='Text color')
        row.prop(self, 'text_color', text='')


    def filepaths(self, context, layout):
        for index, folder in enumerate(self.folders):
            row1 = layout.row()
            split = row1.split(factor=0.3)

            row2 = split.row(align=True)
            row2.prop(folder, 'name', text='', emboss=False)
            row2.prop(folder, 'visible', text='', icon='HIDE_OFF' if folder.visible else 'HIDE_ON', emboss=False)

            row3 = split.row(align=True)
            op = row3.operator('ko.move_folder', text='', icon='TRIA_UP')
            op.index, op.direction = index, -1
            op = row3.operator('ko.move_folder', text='', icon='TRIA_DOWN')
            op.index, op.direction = index, 1
            row3.prop(folder, 'location', text='')

            op = row1.operator('ko.remove_kpack_path', text='', emboss=False, icon='PANEL_CLOSE')
            op.index = index

        row = layout.row()
        split = row.split(factor=0.3)

        split.separator()
        split.operator('ko.add_kpack_path', text='', icon='PLUS')

        sub = row.row()
        sub.operator('ko.refresh_kpacks', text='', emboss=False, icon='FILE_REFRESH')


classes = [
    favorite,
    recent,
    folder,
    kitops]


def register():
    for cls in classes:
        register_class(cls)

    addon.preference()


def unregister():
    for cls in classes:
        unregister_class(cls)
