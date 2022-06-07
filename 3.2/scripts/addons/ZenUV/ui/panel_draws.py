# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

""" Zen UV draws functions for panels """
import bpy
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.texel_density import is_td_display_activated
from ZenUV.ico import icon_get


def draw_packer_props(self, context):
    addon_prefs = get_prefs()
    box = self.layout.box()
    row = box.row(align=True)
    row.label(text=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL + ": ")
    row.prop(addon_prefs, 'td_im_size_presets', text="")
    if addon_prefs.td_im_size_presets == 'Custom':
        col = box.column(align=True)
        col.prop(addon_prefs, 'TD_TextureSizeX', text="Custom Res X")
        col.prop(addon_prefs, 'TD_TextureSizeY', text="Custom Res Y")

    # General Settings
    box.prop(addon_prefs, 'averageBeforePack')
    box.prop(addon_prefs, 'rotateOnPack')

    # UVP Settings
    if addon_prefs.packEngine == 'UVP':
        # layout.prop(addon_prefs, "keepStacked")
        box.prop(addon_prefs, "packFixedScale")
        box.prop(addon_prefs, "lock_overlapping_mode")
        # UVP2 Packing Modes 'Single Tile', 'Tiles', 'Groups Together', 'Groups To Tiles'
        if hasattr(bpy.types, bpy.ops.uvpackmaster2.uv_pack.idname()):
            if hasattr(context.scene, "uvp2_props") and hasattr(context.scene.uvp2_props, "margin"):
                uvp_2_scene_props = context.scene.uvp2_props
                pm = box.column(align=True)
                pm.label(text="PackingMode:")
                pm.prop(uvp_2_scene_props, "pack_mode", text='')
                if uvp_2_scene_props.pack_mode in ["2", "3"]:
                    col = box.column(align=True)
                    col.label(text="Grouping Method:")
                    col.prop(uvp_2_scene_props, "group_method", text='')
                if uvp_2_scene_props.pack_mode == "2":
                    pm.prop(uvp_2_scene_props, "group_compactness")
                if uvp_2_scene_props.pack_mode == "3":
                    pm.prop(uvp_2_scene_props, "tiles_in_row")
                if uvp_2_scene_props.pack_mode in ["1", ]:
                    col = box.column(align=True)
                    tile_col = col.column(align=True)
                    # tile_col.enabled = tile_col_enabled
                    tile_col.prop(uvp_2_scene_props, "tile_count")
                    tile_col.prop(uvp_2_scene_props, "tiles_in_row")


def draw_progress_bar(self, context):
    if context.scene.zenuv_progress >= 0:
        self.layout.separator()
        text = context.scene.zenuv_progress_text
        self.layout.prop(
            context.scene,
            "zenuv_progress",
            text=text,
            slider=True
            )


def draw_select(self, context):
    layout = self.layout
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_select_island", icon_value=icon_get('select'), text='Islands')
    row.operator("uv.zenuv_select_loop", text="Int. Loop")
    row = col.row(align=True)
    row.operator("uv.zenuv_select_uv_overlap", text="Overlapped")
    row.operator("uv.zenuv_select_flipped", text="Flipped")
    if context.area.type == 'VIEW_3D':
        row = col.row(align=True)
        row.operator("mesh.zenuv_select_seams", text="Seam")
        row.operator("mesh.zenuv_select_sharp", text="Sharp")
    col.operator("uv.zenuv_select_similar", text="Similar")
    layout.operator("uv.zenuv_isolate_island")


def draw_texel_density(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    label_units = 'px/' + context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.bl_rna.properties['td_unit'].enum_items[addon_prefs.td_unit].name
    col = layout.column(align=True)
    row = col.row(align=True)
    r = row.split(factor=0.7, align=True)
    r.prop(addon_prefs, 'TexelDensity', text="")
    r.label(text=label_units)
    sel_by_td = row.operator(
        "zen_tdpr.select_by_texel_density",
        text="",
        icon="RESTRICT_SELECT_OFF"
        )
    sel_by_td.by_value = True
    sel_by_td.texel_density = addon_prefs.TexelDensity
    sel_by_td.sel_underrated = False
    sel_by_td.sel_overrated = False
    row.popover(panel="TD_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator('uv.zenuv_get_texel_density')
    row.operator('uv.zenuv_set_texel_density')
    row = col.row(align=True)
    row.prop(addon_prefs, "td_set_mode", text="")
    # label_display_td = ZuvLabels.OT_DISPLAY_TD_LABEL

    col = layout.column(align=True)
    row = col.row(align=True)
    td_checker_value = str(round(addon_prefs.td_checker, 2))
    if context.area.type == 'VIEW_3D':
        row.label(text="TD Checker: " + td_checker_value + " " + label_units)
        row.operator("zenuv.set_current_td_to_checker_td", text="", icon='IMPORT')
        row.popover(panel="TD_PT_Checker_Properties", text="", icon="PREFERENCES")
        # if is_td_display_activated(context):
        #     label_display_td = ZuvLabels.OT_REFRESH_TD_LABEL
    if context.area.type == 'VIEW_3D':
        row = layout.row(align=True)
        row.operator("uv.zenuv_display_td_balanced", icon='HIDE_OFF')
        row.operator("uv.zenuv_hide_texel_density").map_type = "ALL"


def draw_finished_section(self, context):
    """ Finished Section """
    layout = self.layout
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_islands_sorting", text=ZuvLabels.SORTING_LABEL)
    row.popover(panel="FINISHED_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator("uv.zenuv_tag_finished")
    row.operator("uv.zenuv_untag_finished")

    # col.operator("uv.zenuv_batch_finished",
    #         text=ZuvLabels.BATCH_FINISHED_HIDE_ENUM_LABEL).Action = "HIDE"
    col.operator("uv.zenuv_select_finished")

    # col.operator("uv.zenuv_display_finished")
    col.prop(context.scene.zen_display, "finished", toggle=True, icon='HIDE_OFF')


def draw_native_unwrap(self, context):
    row = self.layout.row(align=True)
    row.operator('uv.smart_project')
    row.operator('uv.cube_project')
    row.operator('uv.cylinder_project')
    row.operator('uv.sphere_project')


def draw_unwrap(self, context):
    layout = self.layout

    # Zen Unwrap Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator(
        "uv.zenuv_unwrap",
        icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO)).action = "NONE"
    row.popover(panel="ZENUNWRAP_PT_Properties", text="", icon="PREFERENCES")

    # draw_native_unwrap(self, context)

    # Seams Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_auto_mark")
    row.popover(panel="MARK_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator(
        "uv.zenuv_mark_seams",
        icon_value=icon_get(ZuvLabels.OT_MARK_ICO))
    row.operator(
        "uv.zenuv_unmark_seams",
        icon_value=icon_get(ZuvLabels.OT_UNMARK_ICO))
    col.operator("uv.zenuv_unmark_all")

    # Seam By Section

    # col = col.column(align=True)
    row = col.row(align=True)
    row.prop(context.scene.zen_uv, "sl_convert", text="")
    row.operator("uv.zenuv_unified_mark", icon='KEYFRAME_HLT', text="")
    # col.operator("uv.zenuv_seams_by_uv_islands")
    # col.operator("uv.zenuv_seams_by_sharp")
    # col.operator("uv.zenuv_sharp_by_seams")
    # col.operator("uv.zenuv_seams_by_open_edges")
    layout.operator("mesh.zenuv_mirror_seams")

    # col = layout.column(align=True)
    layout.operator("view3d.zenuv_set_smooth_by_sharp")

    # draw_finished_section(self, context)

    # Quadrify Section

    # col = layout.column(align=True)
    # row = col.row(align=True)
    # row.operator("uv.zenuv_quadrify", icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))
    # row.popover(panel="QUADRIFY_PT_Properties", text="", icon="PREFERENCES")


def uv_draw_unwrap(self, context):
    pass
    # layout = self.layout

    # Zen Unwrap Section
    # col = layout.column(align=True)
    # draw_native_unwrap(self, context)
    # col.operator('uv.project_from_view')
    # Finished Section
    # col = layout.column(align=True)
    # row = col.row(align=True)
    # row.operator("uv.zenuv_islands_sorting", text=ZuvLabels.SORTING_LABEL)
    # row.popover(panel="FINISHED_PT_Properties", text="", icon="PREFERENCES")
    # row = col.row(align=True)
    # row.operator("uv.zenuv_tag_finished")
    # row.operator("uv.zenuv_untag_finished")
    # col.operator("uv.zenuv_select_finished")

    # Quadrify Section
    # col = layout.column(align=True)
    # row = col.row(align=True)
    # row.operator("uv.zenuv_quadrify", icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))
    # row.popover(panel="QUADRIFY_PT_Properties", text="", icon="PREFERENCES")
    # layout.operator("uv.zenuv_distribute", text="Straight Islands").relax_linked = True


def draw_pack(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    prop = context.scene.zen_uv

    # Pack Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_pack", icon_value=icon_get('pack')).display_uv = True
    row.popover(panel="PACK_PT_Properties", text="", icon="PREFERENCES")
    if not addon_prefs.packEngine == "UVPACKER":
        if addon_prefs.margin_show_in_px:
            col.prop(addon_prefs, 'margin_px')
        else:
            col.prop(addon_prefs, 'margin')
    else:
        col.prop(prop, "pack_uv_packer_margin")
    row = layout.row(align=True)
    uv_coverage_label = "UV Coverage: " + str(round(addon_prefs.UVCoverage, 2)) + " %"
    row.label(text=uv_coverage_label)
    row.operator("uv.zenuv_get_uv_coverage", icon="FILE_REFRESH", text="")


def draw_stack(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    layout.split()
    col = layout.column(align=True)
    row = col.row(align=True)
    st = row.operator("uv.zenuv_stack_similar", text="Stack", icon_value=icon_get(ZuvLabels.ZEN_STACK_ICO))
    ust = row.operator("uv.zenuv_unstack", text="Unstack")
    if addon_prefs.st_stack_mode == 'ALL':
        st.selected = ust.selected = False
    elif addon_prefs.st_stack_mode == 'SELECTED':
        st.selected = ust.selected = True
    row.popover(panel="STACK_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.prop(get_prefs(), "st_stack_mode", text="")
    if context.area.type == 'VIEW_3D':
        layout.split()
        deferred_displaying = ('PRIMARY', 'REPLICAS', 'SINGLES')
        row = layout.row(align=True)
        eye_row = row.row(align=True)
        if context.scene.zen_display.stack_display_mode not in deferred_displaying:
            eye_row.prop(context.scene.zen_display, "stack_display_solver", text="", toggle=True, icon='HIDE_OFF')
        row.prop(context.scene.zen_display, "stack_display_mode", text="")
        if context.scene.zen_display.stack_display_mode == 'STACKED':
            row.popover(panel="STACK_PT_DrawProperties", text="", icon="PREFERENCES")
            row.operator("uv.zenuv_select_stacked", text="", icon="RESTRICT_SELECT_OFF")
        if context.scene.zen_display.stack_display_mode in deferred_displaying:
            solver = context.scene.zen_display.stack_display_mode
            if solver == 'PRIMARY':
                desc = ZuvLabels.OT_SELECT_STACK_PRIMARY_DESC
            elif solver == 'REPLICAS':
                desc = ZuvLabels.OT_SELECT_STACK_REPLICAS_DESC
            elif solver == 'SINGLES':
                desc = ZuvLabels.OT_SELECT_STACK_SINGLES_DESC
            row.operator("uv.zenuv_select_stack", text="", icon="RESTRICT_SELECT_OFF").desc = desc


def draw_copy_paste(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("uv.zenuv_copy_uv", icon="COPYDOWN")
    row.operator("uv.zenuv_paste_uv", icon="PASTEDOWN")


def draw_transform_panel(self, context):
    layout = self.layout
    prop = context.scene.zen_uv
    box = layout.box()
    col = box.column(align=True)
    col.prop(prop, "tr_pivot_mode")
    col.prop(prop, "tr_type")

    col = box.column(align=True)
    row = col.row(align=False)
    row.alignment = "CENTER"
    row.scale_x = 1.2
    row.scale_y = 1.2

    row.prop(prop, "tr_mode", text="Mode", expand=True, icon_only=True)

    col = box.column(align=True)
    row = col.row()

    con_col = row.column(align=True)

    row = row.row(align=False)
    col = row.column()

    if prop.tr_mode == "2DCURSOR":
        if 'IMAGE_EDITOR' in [area.type for area in context.screen.areas]:
            top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        else:
            warn = """Cursor data is missing. To manipulate the 2D cursor, open the UV editor"""
            col.label(text=warn)

    if prop.tr_mode == "MOVE":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        # row = col.row()
        if context.space_data.type == 'VIEW_3D':
            if context.scene.tool_settings.transform_pivot_point == "CURSOR":
                col.label(text="To 2D Cursor")
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"] = True
            else:
                col.prop(prop, "tr_move_inc", text="Move Increment")
                # enb_cen.enabled = False
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"] = False
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["icon"] = "tr_control_off"

        # transform_pivot_point
        elif context.space_data.type == 'IMAGE_EDITOR':
            if prop.tr_pivot_mode == "CURSOR":
                col.label(text="To 2D Cursor")
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"] = True
            else:
                col.prop(prop, "tr_move_inc", text="Move Increment")
                # enb_cen.enabled = False
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"] = False
                ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["icon"] = "tr_control_off"

    if prop.tr_mode == "SCALE":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        col.prop(prop, "tr_scale")

    if prop.tr_mode == "FIT":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        # col.prop(prop, "tr_fit_keep_proportion")
        fill = col.operator("uv.zenuv_unified_transform", text=ZuvLabels.TR_FILL_NO_PROPORTION_LABEL)
        fill.desc = ZuvLabels.TR_FILL_NO_PROPORTION_DESC
        fill.fit_keep_proportion = False
        fill.pp_pos = "cen"

        col.prop(prop, "tr_fit_padding")
        col.prop(prop, "tr_fit_bound")

    if prop.tr_mode == "FLIP":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"] = False
        ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["icon"] = "tr_control_off"

    if prop.tr_mode == "ROTATE":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        # row = col.row()
        col.prop(prop, "tr_rot_inc")
        if prop.tr_type == 'ISLAND':
            orient_row = box.row(align=True)
            # orient_row.alignment = "RIGHT"
            orient_row.label(text="Orient by selected:")
            orient_row.operator(
                "uv.zenuv_unified_transform",
                text="",
                icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS["ROTATE"]["cen"]["icon"])
            ).orient_by_selected = True

            orient_v = orient_row.operator(
                "uv.zenuv_unified_transform",
                text="",
                icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS["ROTATE"]["tc"]["icon"])
            )
            orient_v.pp_pos = "tc"
            orient_v.orient_by_selected = True

            orient_h = orient_row.operator(
                "uv.zenuv_unified_transform",
                text="",
                icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS["ROTATE"]["lc"]["icon"])
            )
            orient_h.pp_pos = "lc"
            orient_h.orient_by_selected = True

    if prop.tr_mode == "ALIGN":
        top_row, mid_row, bot_row = draw_unified_control(prop, con_col)
        col.prop(prop, "tr_uv_area_bounds")

    if prop.tr_mode == "DISTRIBUTE":
        if prop.tr_type == "ISLAND":
            col.operator("uv.zenuv_distribute_islands", text="Distribute & Sort")
            col.operator("uv.zenuv_arrange_transform")
        else:
            distr = col.operator("uv.zenuv_distribute", text="Distribute")
            distr.desc = ZuvLabels.PROP_DISTRIBUTE_DESC
            distr.relax_linked = False

    # layout.separator()
    col = layout.column(align=True)
    col.operator("uv.zenuv_randomize_transform")
    row = col.row(align=True)
    row.operator("uv.zenuv_quadrify", icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))
    row.popover(panel="QUADRIFY_PT_Properties", text="", icon="PREFERENCES")
    if context.area.type == 'IMAGE_EDITOR':
        straight = col.operator("uv.zenuv_distribute", text="Straighten Island")
        straight.desc = ZuvLabels.PROP_STRAIGHTEN_DESC
        straight.relax_linked = True


def draw_unified_control(prop, con_col):
    # Transform Main Control ==================================================
    # Top Row Section:----------------------
    top_row = con_col.row(align=True)

    # Top Left Control (tl)
    enb_tl = top_row.row(align=True)
    enb_tl.enabled = True
    tl = enb_tl.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tl"]["icon"]),
        text=""
    )
    tl.pp_pos = "tl"
    tl.fit_keep_proportion = True
    tl.orient_by_selected = False
    tl.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tl"]["desc"]

    # Top Center Control (tc)
    enb_tc = top_row.row(align=True)
    enb_tc.enabled = True
    tc = enb_tc.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tc"]["icon"]),
        text=""
    )
    tc.pp_pos = "tc"
    tc.orient_by_selected = False
    tc.fit_keep_proportion = True
    tc.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tc"]["desc"]

    # Top Right Control (tr)
    enb_tr = top_row.row(align=True)
    enb_tr.enabled = True
    tr = enb_tr.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tr"]["icon"]),
        text=""
    )
    tr.pp_pos = "tr"
    tr.orient_by_selected = False
    tr.fit_keep_proportion = True
    tr.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["tr"]["desc"]
    # END Top Row Section:------------------

    # Mid Row Section:----------------------
    mid_row = con_col.row(align=True)

    # Left Center Control (lc)
    enb_lc = mid_row.row(align=True)
    enb_lc.enabled = True
    lc = enb_lc.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["lc"]["icon"]),
        text=""
    )
    lc.pp_pos = "lc"
    lc.orient_by_selected = False
    lc.fit_keep_proportion = True
    lc.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["lc"]["desc"]

    # Center Control (cen)
    enb_cen = mid_row.row(align=True)
    enb_cen.enabled = True
    cen = enb_cen.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["icon"]),
        text="",
        emboss=ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["enable"]
    )
    cen.pp_pos = "cen"
    cen.fit_keep_proportion = True
    cen.orient_by_selected = False
    cen.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["cen"]["desc"]

    # Right Center Control (rc)
    enb_rc = mid_row.row(align=True)
    enb_rc.enabled = True
    rc = enb_rc.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["rc"]["icon"]),
        text=""
    )
    rc.pp_pos = "rc"
    rc.fit_keep_proportion = True
    rc.orient_by_selected = False
    rc.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["rc"]["desc"]
    # END Mid Row Section:------------------

    # Botom Row Section:--------------------
    bot_row = con_col.row(align=True)

    # Bottom Left Control (bl)
    enb_bl = bot_row.row(align=True)
    enb_bl.enabled = True
    bl = enb_bl.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["bl"]["icon"]),
        text=""
    )
    bl.pp_pos = "bl"
    bl.fit_keep_proportion = True
    bl.orient_by_selected = False
    bl.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["bl"]["desc"]

    # Bottom Center Control (bc)
    enb_bc = bot_row.row(align=True)
    enb_bc.enabled = True
    bc = enb_bc.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["bc"]["icon"]),
        text=""
    )
    bc.pp_pos = "bc"
    bc.fit_keep_proportion = True
    bc.orient_by_selected = False
    bc.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["bc"]["desc"]

    # Bottom Right Control (br)
    enb_br = bot_row.row(align=True)
    enb_br.enabled = True
    br = enb_br.operator(
        "uv.zenuv_unified_transform",
        icon_value=icon_get(ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["br"]["icon"]),
        text=""
    )
    br.pp_pos = "br"
    br.fit_keep_proportion = True
    br.orient_by_selected = False
    br.desc = ZuvLabels.TRANSFORM_LABELS[prop.tr_mode]["br"]["desc"]
    # END Botom Row Section:------------------

    # END Transform Main Control ==================================================
    return top_row, mid_row, bot_row
