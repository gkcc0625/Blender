import bpy

from bpy.types import Panel, UIList
from bpy.utils import register_class, unregister_class

from .. utility import addon, dpi, insert, update, modifier, previews

authoring_enabled = True
try: from .. utility import matrixmath
except: authoring_enabled = False

import os


def _is_standard_mode(context):
    '''determines whether the standard or authoring panel should be displayed'''
    return not insert.authoring() and not context.scene.kitops.thumbnail

class KO_PT_Main(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'KIT OPS'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'
    bl_idname = "KITOPS_PT_Panel_Main"

    def draw_header_preset(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("ko.open_help_url", icon='QUESTION', text="").url = "http://cw1.me/kitopsdocs"

        row.separator()

    def draw(self, context):
        pass



class KO_PT_KPACKS(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'KPACKS'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'
    bl_parent_id = 'KITOPS_PT_Panel_Main'

    @classmethod
    def poll(cls, context):
        return _is_standard_mode(context)

    def draw_header_preset(self, context):
        layout = self.layout
        preference = addon.preference()
        if authoring_enabled:
            row = layout.row(align=True)
            if not preference.show_favorites:
                row.prop(preference, 'show_favorites', text="", icon="SOLO_OFF", emboss=False)
            if not preference.show_recents:
                row.prop(preference, 'show_recents', text="", icon="MOD_TIME", emboss=False)



    def draw(self, context):
        global authoring_enabled

        layout = self.layout
        preference = addon.preference()
        option = addon.option()
        scene = context.scene

        if len(option.kpack.categories):

            column = layout.column(align=True)

            #fvs and rts
            if authoring_enabled:
                matrixmath.draw_fvs_rcts(column)
                column = column.box().column(align=True)


            row = column.row(align=True)
            if authoring_enabled and option.kpack.active_index < len(option.kpack.categories):
                category = option.kpack.categories[option.kpack.active_index]
                is_favorite = category.name in preference.favorites
                row.operator('ko.add_favorite' if not is_favorite else 'ko.remove_favorite', text='', icon="SOLO_ON" if is_favorite else "SOLO_OFF", depress=is_favorite).kpack_name = category.name

            row.prop(option, 'kpacks', text='')

            row.operator('ko.refresh_kpacks', text='', icon='FILE_REFRESH').record_previous = True


            if option.kpack.active_index < len(option.kpack.categories):
                category = option.kpack.categories[option.kpack.active_index]

                row = column.row(align=True)

                sub = row.row(align=True)
                sub.scale_y = 6
                sub.operator('ko.previous_kpack', text='', icon='TRIA_LEFT')

                row.template_icon_view(category, 'thumbnail', show_labels=preference.thumbnail_labels)

                sub = row.row(align=True)
                sub.scale_y = 6
                sub.operator('ko.next_kpack', text='', icon='TRIA_RIGHT')

                row = column.row(align=True)
                row.scale_y = 1.5
                op = row.operator('ko.add_insert')
                op.location = category.blends[category.active_index].location
                op.material = False
                op.rotation_amount = 0

                row.scale_y = 1.5
                op = row.operator('ko.add_insert_material')
                op.location = category.blends[category.active_index].location
                op.material = True

                row = column.row()
                row.label(text='INSERT Name: {}'.format(category.blends[category.active_index].name))

                if authoring_enabled:
                    row = column.row()
                    row.operator('ko.edit_insert')

                    column.separator()

                    row = column.row()
                    row.operator('ko.replace_insert', text='Replace INSERT(s)')

                layout.separator()


                split = layout.split(factor=0.3)
                split.label(text='Mode')
                row = split.row()
                row.prop(preference, 'mode', expand=True)

class KO_PT_Controls(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'Controls'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'
    bl_parent_id = 'KITOPS_PT_Panel_Main'

    @classmethod
    def poll(cls, context):
        return _is_standard_mode(context)

    def draw(self, context):


        global authoring_enabled

        layout = self.layout
        preference = addon.preference()
        option = addon.option()
        scene = context.scene

        if len(option.kpack.categories):

            column = layout.column(align=True)
            column.enabled = preference.auto_scale
            row = column.row(align=True)
            row.prop(preference, 'insert_scale', expand=True)
            column.prop(preference, '{}_scale'.format(preference.insert_scale.lower()), text='Scale')
            layout.separator()

            layout.prop(preference, 'auto_scale')
            layout.prop(preference, 'parent_inserts', text="Parent INSERTs")

            if authoring_enabled:
                layout.prop(preference, 'place_on_insert')
                layout.prop(preference, 'flip_placement')

                layout.separator()

                col_snap = layout.column(align=True)
                row_snap = col_snap.row(align=True)
                row_snap.label(text="Snap Mode:")


                row_snap.prop_enum(preference, 'snap_mode', 'NONE', text='' , icon='CANCEL')
                row_snap.prop_enum(preference, 'snap_mode', 'VERTEX', text='' , icon='SNAP_VERTEX')
                row_snap.prop_enum(preference, 'snap_mode', 'EDGE', text='' , icon='SNAP_EDGE')
                row_snap.prop_enum(preference, 'snap_mode', 'FACE', text='' , icon='SNAP_FACE')

                if preference.snap_mode == 'EDGE':
                    row_snap = layout.row(align=True)
                    row_snap.alignment = 'RIGHT'
                    row_snap.label(text="Snap to")
                    row_snap.prop(preference, 'snap_mode_edge', expand=True)

            active = context.active_object
            if active and hasattr(active, 'kitops') and active.kitops.insert:

                if preference.mode == 'SMART':
                    layout.separator()

                    if context.active_object.kitops.insert_target and preference.mode == 'SMART':
                        col =layout.column()

                        row = layout.row(align=True)
                        row.label(text='Mirror:')
                        row.prop(context.active_object.kitops, 'mirror_x', text='X', toggle=True)
                        row.prop(context.active_object.kitops, 'mirror_y', text='Y', toggle=True)
                        row.prop(context.active_object.kitops, 'mirror_z', text='Z', toggle=True)

                    col =layout.column()
                    col.label(text='Target Object:')
                    row = col.row(align=True)
                    if context.active_object.kitops.insert_target:
                        row.prop(context.active_object.kitops.insert_target, 'hide_select', text='', icon='RESTRICT_SELECT_OFF' if not context.active_object.hide_select else 'RESTRICT_SELECT_ON')


                    row.prop(context.active_object.kitops, 'insert_target', text='')

            if preference.mode == 'SMART' and context.active_object and context.active_object.kitops.insert_target:
                row = layout.row()
                row.scale_y = 1.5
                row.operator('ko.select_inserts')

                layout.label(text='Align')

                row = layout.row()
                row.scale_y = 1.5
                row.scale_x = 1.5

                row.operator('ko.align_top', text='', icon_value=previews.get(addon.icons['align-top']).icon_id)
                row.operator('ko.align_bottom', text='', icon_value=previews.get(addon.icons['align-bottom']).icon_id)
                row.operator('ko.align_left', text='', icon_value=previews.get(addon.icons['align-left']).icon_id)
                row.operator('ko.align_right', text='', icon_value=previews.get(addon.icons['align-right']).icon_id)

                row = layout.row()
                row.scale_y = 1.5
                row.scale_x = 1.5
                row.operator('ko.align_horizontal', text='', icon_value=previews.get(addon.icons['align-horiz']).icon_id)
                row.operator('ko.align_vertical', text='', icon_value=previews.get(addon.icons['align-vert']).icon_id)
                row.operator('ko.stretch_wide', text='', icon_value=previews.get(addon.icons['stretch-wide']).icon_id)
                row.operator('ko.stretch_tall', text='', icon_value=previews.get(addon.icons['stretch-tall']).icon_id)


class KO_PT_Management(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'Tools'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'
    bl_parent_id = 'KITOPS_PT_Panel_Main'

    @classmethod
    def poll(cls, context):
        return _is_standard_mode(context)

    def draw(self, context):


        global authoring_enabled

        layout = self.layout
        preference = addon.preference()
        option = addon.option()
        scene = context.scene

        if len(option.kpack.categories):

            if context.window_manager.kitops.pro:
                if context.scene.kitops.thumbnail:
                    layout.separator()

                    row = layout.row()
                    row.scale_y = 1.5
                    op = row.operator('ko.render_thumbnail', text='Render thumbnail')
                    op.render = True
                    op.import_scene = False

                # else:
            if not context.scene.kitops.thumbnail:
                layout.separator()

                row = layout.row(align=True)
                row.scale_y = 1.5
                op = row.operator('ko.remove_insert_properties')
                op.remove = False
                op.uuid = ''

                sub = row.row(align=True)
                sub.enabled = context.active_object.kitops.insert if context.active_object else False
                op = sub.operator('ko.remove_insert_properties_x', text='', icon='X')
                op.remove = True
                op.uuid = ''

            if context.window_manager.kitops.pro:
                if not context.scene.kitops.thumbnail:
                    row = layout.row()
                    row.scale_y = 1.5
                    op = row.operator('ko.create_insert', text="Create INSERT *")
                    op.material = False
                    op.children = True

                    row = layout.row()
                    row.scale_y = 1.5
                    op = row.operator('ko.create_insert_material' , text="Create Material INSERT *")
                    op.material = True
                    op.children = False

                    row = layout.row()
                    if bpy.data.filepath:
                        row.label(text="* will automatically save scene.")
                    else:
                        row.label(text="* save file before proceeding.")

            if not context.scene.kitops.thumbnail:

                row = layout.row()
                row.scale_y = 1.5
                row.operator('ko.convert_to_mesh', text='Convert to mesh')


        if not context.scene.kitops.thumbnail:

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.remove_wire_inserts')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.clean_duplicate_materials')

            layout.separator()

            row = layout.row()
            row.enabled = True
            row.alignment = 'RIGHT'
            row.scale_x = 1.5
            row.scale_y = 1.5
            row.operator('ko.store', text='', icon_value=previews.get(addon.icons['cart']).icon_id)
            op = row.operator('ko.documentation', text='', icon_value=previews.get(addon.icons['question-sign']).icon_id)
            op.authoring = False





class KO_PT_Authoring(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'Authoring'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'
    bl_parent_id = 'KITOPS_PT_Panel_Main'

    @classmethod
    def poll(cls, context):
        return not _is_standard_mode(context)

    def draw(self, context):
        global authoring_enabled

        layout = self.layout
        preference = addon.preference()
        option = addon.option()
        scene = context.scene


        if insert.authoring():
            if not authoring_enabled:
                layout.label(icon='ERROR', text='Purchase KIT OPS PRO')
                layout.label(icon='BLANK1', text='To use these features')

            if context.scene.kitops.factory:
                column = layout.column()
                column.enabled = authoring_enabled

                column.label(text='INSERT name')
                column.prop(option, 'insert_name', text='')

            column = layout.column()
            column.enabled = authoring_enabled
            column.label(text='Author')
            column.prop(option, 'author', text='')
            layout.separator()

        if context.active_object and not context.active_object.kitops.temp or scene.kitops.factory:
            if context.active_object.type not in {'LAMP', 'CAMERA', 'SPEAKER', 'EMPTY'}:
                row = layout.row()
                row.enabled = authoring_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
                row.prop(context.active_object.kitops, 'main')

            row = layout.row()
            row.enabled = authoring_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
            row.prop(context.active_object.kitops, 'type', expand=True)

            if context.active_object.type == 'MESH' and context.active_object.kitops.type == 'CUTTER':
                row = layout.row()
                row.enabled = authoring_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
                row.prop(context.active_object.kitops, 'boolean_type', text='Type')

        elif context.active_object and context.active_object.type == 'MESH' and scene.kitops.thumbnail:
            row = layout.row()
            row.enabled = authoring_enabled
            row.prop(context.active_object.kitops, 'ground_box')

        if insert.authoring() or context.scene.kitops.thumbnail:
            layout.separator()

            if context.active_object:
                row = layout.row()
                row.enabled = authoring_enabled and not context.active_object.kitops.main and not context.active_object.kitops.temp
                row.prop(context.active_object.kitops, 'selection_ignore')

            layout.separator()

            if not context.scene.kitops.thumbnail:
                column = layout.column()
                column.enabled = authoring_enabled and bool(context.active_object) and not context.active_object.kitops.temp
                column.prop(scene.kitops, 'animated')
                column.prop(scene.kitops, 'auto_parent')

                layout.separator()

            if not context.scene.kitops.thumbnail or context.scene.kitops.factory:
                row = layout.row()
                row.active = authoring_enabled
                row.scale_y = 1.5
                row.operator('ko.save_insert' if authoring_enabled else 'ko.purchase')

            if insert.authoring() or context.scene.kitops.thumbnail:
                if context.scene.camera:
                    row = layout.row()
                    row.scale_y = 1.5
                    row.operator('ko.camera_to_insert')

                if not context.scene.kitops.thumbnail:
                    row = layout.row()
                    row.scale_y = 1.5
                    # row.operator('ko.render_thumbnail', text='Render thumbnail', icon='BLANK1')
                    op = row.operator('ko.render_thumbnail', text='Load Render Scene', icon='BLANK1')
                    op.render = False
                    op.import_scene = True

            if context.scene.kitops.factory or context.scene.kitops.thumbnail:
                row = layout.row()
                row.active = authoring_enabled and not (context.scene.kitops.factory and not context.scene.kitops.last_edit)
                row.scale_y = 1.5
                row.operator('ko.create_snapshot' if authoring_enabled else 'ko.purchase', text='Render Thumbnail')
                row = layout.row()

            if context.scene.kitops.factory:
                row.active = authoring_enabled
                row.scale_y = 1.5
                row.operator('ko.close_factory_scene' if authoring_enabled else 'ko.purchase')

            elif context.scene.kitops.thumbnail:
                row.active = authoring_enabled
                row.scale_y = 1.5
                row.operator('ko.close_thumbnail_scene' if authoring_enabled else 'ko.purchase')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.remove_wire_inserts')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.clean_duplicate_materials')

            layout.separator()

            row = layout.row()
            row.alignment = 'RIGHT'
            row.scale_x = 1.5
            row.scale_y = 1.5
            op = row.operator('ko.documentation', text='', icon_value=previews.get(addon.icons['question-sign']).icon_id)
            op.authoring = True




class KO_PT_sort_last(Panel):
    bl_label = 'Sort Last'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        preference = addon.preference()
        layout = self.layout

        row = layout.row(align=True)

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
            sub = row.row(align=True)
            sub.enabled = getattr(preference, F'sort_{type.lower()}')
            sub.prop(preference, F'sort_{type.lower()}_last', text='', icon=icon)

        if preference.sort_bevel:
            label_row(preference, 'sort_bevel_ignore_weight', layout.row(), label='Ignore Bevels using Weights')
            label_row(preference, 'sort_bevel_ignore_vgroup', layout.row(), label='Ignore Bevels with VGroups')
            label_row(preference, 'sort_bevel_ignore_only_verts', layout.row(), label='Ignore Bevels using Only Verts')

        layout.separator()

        label_row(preference, 'sort_depth', layout.row(), label='Sort Depth')
        label_row(preference, 'sort_ignore_char', layout.row(), label='Ignore Flag', scale_x_prop=0.35)
        label_row(preference, 'sort_stop_char', layout.row(), label='Stop Flag', scale_x_prop=0.35)


class KO_PT_ui():
    '''Facade class to for use with HOPS so that the panel will still be displayed'''

    def draw(self, context):
        if _is_standard_mode(context):
            KO_PT_KPACKS.draw_header_preset(self, context)
            KO_PT_KPACKS.draw(self, context)
            KO_PT_Controls.draw(self, context)
            KO_PT_Management.draw(self, context)
        else:
            KO_PT_Authoring.draw(self, context)


def label_row(path, prop, row, label='', scale_x_prop=1.0):
    row.label(text=label)
    sub = row.row()
    sub.scale_x = scale_x_prop
    sub.prop(path, prop, text='')


classes = [
    KO_PT_Main,
    KO_PT_KPACKS,
    KO_PT_Controls,
    KO_PT_Management,
    KO_PT_Authoring,
    KO_PT_sort_last]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
