import bpy
import json
import os
from urllib import request
from bpy.types import (
        PropertyGroup,
        Operator,
        Scene,
        AddonPreferences,
        Panel
        )
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        PointerProperty,
        FloatVectorProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )
from ._m_tt import KeTTHeader


kekit_version = 2014
new_version = None
old_pf = False

# Prefs File Path
path = bpy.utils.user_resource('CONFIG')
old_path = bpy.utils.script_path_user()


def write_prefs(data):
    jsondata = json.dumps(data, indent=1, ensure_ascii=True)
    file_name = path + "/ke_prefs" + ".json"
    with open(file_name, "w") as text_file:
        text_file.write(jsondata)
    text_file.close()


def read_prefs(prefs_path):
    file_name = prefs_path + "/ke_prefs.json"
    try:
        with open(file_name, "r") as jf:
            prefs = json.load(jf)
            jf.close()
    except (OSError, IOError):
        prefs = None
    return prefs


def get_scene_prefs(context):
    pd = {}
    for key in context.scene.kekit.__annotations__.keys():
        k = getattr(context.scene.kekit, key)
        if str(type(k)) == "<class 'bpy_prop_array'>":
            pd[key] = k[:]
        else:
            pd[key] = k
    return pd


def version_check():
    ver = 0
    try:
        ver = int(request.urlopen("https://artbykjell.com/bversion.v").read())
    except Exception as e:
        print("\nkeKit Version Check Error:\n", e)
        pass
    if ver > kekit_version:
        global new_version
        new_version = ver


def set_tt_icon_pos(self, context):
    bpy.types.VIEW3D_HT_header.remove(KeTTHeader.draw)
    bpy.types.VIEW3D_MT_editor_menus.remove(KeTTHeader.draw)
    if bpy.context.preferences.addons[__package__].preferences.tt_icon_pos == "CENTER":
        bpy.types.VIEW3D_MT_editor_menus.append(KeTTHeader.draw)
    elif bpy.context.preferences.addons[__package__].preferences.tt_icon_pos == "RIGHT":
        bpy.types.VIEW3D_HT_header.append(KeTTHeader.draw)
    elif bpy.context.preferences.addons[__package__].preferences.tt_icon_pos == "LEFT":
        bpy.types.VIEW3D_HT_header.prepend(KeTTHeader.draw)
    # ...else REMOVE only


# READ PROPS FILE
read_v = read_prefs(path)
if read_v is None:
    read_v = read_prefs(old_path)
    if read_v is not None:
        old_pf = True
        print("keKit: Old path prefs file found...attempting upgrade to config location")


# DEFAULT VALUES
dv = {
    'version'               : kekit_version,
    'fitprim_select'	    : False,
    'fitprim_modal'			: True,
    'fitprim_item'			: False,
    'fitprim_sides'			: 16,
    'fitprim_sphere_seg'	: 32,
    'fitprim_sphere_ring'	: 16,
    'fitprim_unit'			: 0.2,
    'fitprim_quadsphere_seg': 8,
    'unrotator_reset'		: True,
    'unrotator_connect'		: True,
    'unrotator_nolink'		: False,
    'unrotator_nosnap'		: False,
    'unrotator_invert'		: False,
    'unrotator_center'		: False,
    'opc1_obj_o'			: "1GLOBAL",
    'opc1_obj_p'			: "1MEDIAN_POINT",
    'opc1_edit_o'			: "1GLOBAL",
    'opc1_edit_p'			: "1MEDIAN_POINT",
    'opc2_obj_o'			: "2LOCAL",
    'opc2_obj_p'			: "3INDIVIDUAL_ORIGINS",
    'opc2_edit_o'			: "3NORMAL",
    'opc2_edit_p'			: "5ACTIVE_ELEMENT",
    'opc3_obj_o'			: "1GLOBAL",
    'opc3_obj_p'			: "3INDIVIDUAL_ORIGINS",
    'opc3_edit_o'			: "2LOCAL",
    'opc3_edit_p'			: "3INDIVIDUAL_ORIGINS",
    'opc4_obj_o'			: "6CURSOR",
    'opc4_obj_p'			: "4CURSOR",
    'opc4_edit_o'			: "6CURSOR",
    'opc4_edit_p'			: "4CURSOR",
    'opc5_obj_o'		    : "1GLOBAL",
    'opc5_obj_p'			: "4CURSOR",
    'opc5_edit_o'			: "1GLOBAL",
    'opc5_edit_p'			: "5ACTIVE_ELEMENT",
    'opc6_obj_o'		    : "5VIEW",
    'opc6_obj_p'			: "1MEDIAN_POINT",
    'opc6_edit_o'			: "5VIEW",
    'opc6_edit_p'			: "5ACTIVE_ELEMENT",
    'selmode_mouse'			: False,
    'quickmeasure'			: True,
    'fit2grid'				: 0.01,
    'vptransform'			: False,
    'loc_got'				: True,
    'rot_got'				: True,
    'scl_got'				: True,
    'qs_user_value'			: 1.0,
    'qs_unit_size'			: True,
    'clean_doubles'			: True,
    'clean_doubles_val'		: 0.0001,
    'clean_loose'			: True,
    'clean_interior'		: True,
    'clean_degenerate'		: True,
    'clean_tinyedge'		: True,
    'clean_tinyedge_val'	: 0.002,
    'clean_collinear'		: True,
    'cursorfit'				: True,
    'lineararray_go'		: False,
    'idm01'					: (1.0, 0.0, 0.0, 1.0),
    'idm02'					: (0.6, 0.0, 0.0, 1.0),
    'idm03'					: (0.3, 0.0, 0.0, 1.0),
    'idm04'					: (0.0, 1.0, 0.0, 1.0),
    'idm05'					: (0.0, 0.6, 0.0, 1.0),
    'idm06'					: (0.0, 0.3, 0.0, 1.0),
    'idm07'					: (0.0, 0.0, 1.0, 1.0),
    'idm08'					: (0.0, 0.0, 0.6, 1.0),
    'idm09'					: (0.0, 0.0, 0.3, 1.0),
    'idm10'					: (1.0, 1.0, 1.0, 1.0),
    'idm11'					: (0.5, 0.5, 0.5, 1.0),
    'idm12'					: (0.0, 0.0, 0.0, 1.0),
    'idm01_name'			: "ID_RED",
    'idm02_name'			: "ID_RED_M",
    'idm03_name'			: "ID_RED_L",
    'idm04_name'			: "ID_GREEN",
    'idm05_name'			: "ID_GREEN_M",
    'idm06_name'			: "ID_GREEN_L",
    'idm07_name'			: "ID_BLUE",
    'idm08_name'			: "ID_BLUE_M",
    'idm09_name'			: "ID_BLUE_L",
    'idm10_name'			: "ID_ALPHA",
    'idm11_name'			: "ID_ALPHA_M",
    'idm12_name'			: "ID_ALPHA_L",
    'object_color' 			: False,
    'matvp_color' 			: False,
    'vpmuted' 				: False,
    'vp_level' 				: 2,
    'render_level' 			: 2,
    'flat_edit' 			: False,
    'boundary_smooth'		: "PRESERVE_CORNERS",
    'limit_surface'			: False,
    'optimal_display'		: True,
    'on_cage'				: False,
    'subd_autosmooth'       : True,
    'snap_elements1'        : "INCREMENT",
    'snap_elements2'        : "INCREMENT",
    'snap_elements3'        : "INCREMENT",
    'snap_elements4'        : "INCREMENT",
    'snap_elements5'        : "INCREMENT",
    'snap_elements6'        : "INCREMENT",
    'snap_targets1'         : "ACTIVE",
    'snap_targets2'         : "ACTIVE",
    'snap_targets3'         : "ACTIVE",
    'snap_targets4'         : "ACTIVE",
    'snap_targets5'         : "ACTIVE",
    'snap_targets6'         : "ACTIVE",
    'snap_bools1'           : [True, False, False, True, False, False, True, False, False],
    'snap_bools2'           : [True, False, False, True, False, False, True, False, False],
    'snap_bools3'           : [True, False, False, True, False, False, True, False, False],
    'snap_bools4'           : [True, False, False, True, False, False, True, False, False],
    'snap_bools5'           : [True, False, False, True, False, False, True, False, False],
    'snap_bools6'           : [True, False, False, True, False, False, True, False, False],
    'combo_autosnap'        : False,
    'paste_merge'           : True,
    'opc1_name'             : "OPC1",
    'opc2_name'             : "OPC2",
    'opc3_name'             : "OPC3",
    'opc4_name'             : "OPC4",
    'opc5_name'             : "OPC5",
    'opc6_name'             : "OPC6",
    'h_delete'              : False,
    'tt_mode'               : [True, False, False],
    'tt_handles'            : True,
    'tt_select'             : True,
    'tt_extrude'            : False,
    'renderslotcycle'       : False,
    'ra_autoarrange'        : False,
    'renderslotfullwrap'    : False,
    'getset_ep'             : False,
    'mc_relative'           : 10,
    'mc_fixed'              : 0,
    'mc_center'             : True,
    'mc_prefs'              : [0.1, 0, 0, 0,
                               0.1, 1, 0, 0,
                               0.05, 1, 0, 0,
                               0.05, 0, 0, 0,
                               0, 0, 0.05, 1,
                               0, 1, 0.05, 1,
                               0, 1, 0.01, 1,
                               0, 0, 0.01, 1],
    'mc_name0'              : "10-90",
    'mc_name1'			    : "10-50-90",
    'mc_name2'			    : "5-50-95",
    'mc_name3'			    : "5-95",
    'mc_name4'			    : "5 cm",
    'mc_name5'			    : "5 cm (C)",
    'mc_name6'              : "1 cm (C)",
    'mc_name7'              : "1 cm",
    'snap_name1'            : "Snap Combo 1",
    'snap_name2'            : "Snap Combo 2",
    'snap_name3'            : "Snap Combo 3",
    'snap_name4'            : "Snap Combo 4",
    'snap_name5'            : "Snap Combo 5",
    'snap_name6'            : "Snap Combo 6",
    'tt_linkdupe'           : False,
    'dlc_so'                : False,
    'shading_tris'          : False,
    'frame_mo'              : False,
    'mam_scl'               : True,
    'qm_running'            : False,
    'korean'                : False,
    'sel_type_coll'         : False,
    'unbevel_autoring'      : False,
    'context_select_h'      : False,
}


# Default values if no prefs-file
if not read_v:
    print("keKit Prefs: Using Default Preferences")

# Update prefs if changes. NEW 2.0: Checking version instead of count, so I can retire/repurpopse old props
elif read_v:
    update = False
    if "version" in read_v:
        if read_v["version"] < kekit_version:
            read_v["version"] = kekit_version
            update = True
    elif old_pf:
        update = True

    if update:
        change = []
        for p, v in dv.items():
            if p not in read_v:
                read_v[p] = dv.get(p)
                change.append(p)
        write_prefs(read_v)
        print("keKit Prefs: Old/missing items - User Preferences File Updated:\n", " ->", change)
    else:
        print("keKit Prefs: Using Custom User Preferences")
    dv = read_v


class KeKitProperties(PropertyGroup):
    # Version
    version: FloatProperty(default=dv["version"])
    # Fitprim
    fitprim_select: BoolProperty(default=dv["fitprim_select"])
    fitprim_modal: BoolProperty(default=dv["fitprim_modal"])
    fitprim_item: BoolProperty(default=dv["fitprim_item"])
    fitprim_sides: IntProperty(min=3, max=256, default=dv["fitprim_sides"])
    fitprim_sphere_seg: IntProperty(min=3, max=256, default=dv["fitprim_sphere_seg"])
    fitprim_sphere_ring: IntProperty(min=3, max=256, default=dv["fitprim_sphere_ring"])
    fitprim_unit: FloatProperty(min=.00001, max=256, default=dv["fitprim_unit"])
    fitprim_quadsphere_seg: IntProperty(min=1, max=128, default=dv["fitprim_quadsphere_seg"])
    # Unrotator
    unrotator_reset: BoolProperty(default=dv["unrotator_reset"])
    unrotator_connect: BoolProperty(description="Connect linked faces from selection", default=dv["unrotator_connect"])
    unrotator_nolink: BoolProperty(description="Duplicated Objects will not be data-linked",
                                   default=dv["unrotator_nolink"])
    unrotator_nosnap: BoolProperty(description="Toggles on face surface snapping or not",
                                   default=dv["unrotator_nosnap"])
    unrotator_invert: BoolProperty(description="Invert (Z) rotation (Separate from the redo-panel)",
                                   default=dv["unrotator_invert"])
    unrotator_center: BoolProperty(description="Place geo on the target face center", default=dv["unrotator_center"])
    # Orientation & Pivot Combo 1
    opc1_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc1_obj_o"])
    opc1_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc1_obj_p"])
    opc1_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc1_edit_o"])
    opc1_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc1_edit_p"])
    # Orientation & Pivot Combo 2
    opc2_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc2_obj_o"])
    opc2_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc2_obj_p"])
    opc2_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc2_edit_o"])
    opc2_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc2_edit_p"])
    # Orientation & Pivot Combo 3
    opc3_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc3_obj_o"])
    opc3_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc3_obj_p"])
    opc3_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc3_edit_o"])
    opc3_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc3_edit_p"])
    # Orientation & Pivot Combo 4
    opc4_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc4_obj_o"])
    opc4_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc4_obj_p"])
    opc4_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc4_edit_o"])
    opc4_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc4_edit_p"])
    # Orientation & Pivot Combo 5
    opc5_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc5_obj_o"])
    opc5_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc5_obj_p"])
    opc5_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc5_edit_o"])
    opc5_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc5_edit_p"])
    # Orientation & Pivot Combo 6
    opc6_obj_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc6_obj_o"])
    opc6_obj_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc6_obj_p"])
    opc6_edit_o: EnumProperty(
        items=[("1GLOBAL", "Global", ""), ("2LOCAL", "Local", ""), ("3NORMAL", "Normal", ""), ("4GIMBAL", "Gimbal", ""),
               ("5VIEW", "View", ""), ("6CURSOR", "Cursor", "")], name="Orientation", default=dv["opc6_edit_o"])
    opc6_edit_p: EnumProperty(
        items=[("1MEDIAN_POINT", "Median Point", ""), ("2BOUNDING_BOX_CENTER", "Bounding Box Center", ""),
               ("3INDIVIDUAL_ORIGINS", "Individual Origins", ""), ("4CURSOR", "Cursor", ""),
               ("5ACTIVE_ELEMENT", "Active Element", "")], name="Pivot Transform", default=dv["opc6_edit_p"])
    # OPC naming
    opc1_name: StringProperty(description="Name OPC1", default=dv["opc1_name"])
    opc2_name: StringProperty(description="Name OPC2", default=dv["opc2_name"])
    opc3_name: StringProperty(description="Name OPC3", default=dv["opc3_name"])
    opc4_name: StringProperty(description="Name OPC4", default=dv["opc4_name"])
    opc5_name: StringProperty(description="Name OPC5", default=dv["opc5_name"])
    opc6_name: StringProperty(description="Name OPC6", default=dv["opc6_name"])
    # QuickMeasure
    # Mouse Over Mode Toggle
    selmode_mouse: BoolProperty(name="", description="Mouse-Over Element Mode Selection for old Sel.mode script",
                                default=dv["selmode_mouse"])
    # QuickMeasure  - default: 1
    quickmeasure: BoolProperty(default=dv["quickmeasure"])
    qm_running: BoolProperty(default=dv["qm_running"])
    # Fit2Grid - default : 0.01
    fit2grid: FloatProperty(min=.00001, max=10000, default=dv["fit2grid"])
    # ViewPlane Contextual - default : 1
    vptransform: BoolProperty(name="VPAutoGlobal", description="Sets Global orientation. Overrides GOT options",
                              default=dv["vptransform"])
    loc_got: BoolProperty(name="Grab GlobalOrTool", description="VPGrab when Global, otherwise Transform (gizmo)",
                          default=dv["loc_got"])
    rot_got: BoolProperty(name="Rotate GlobalOrTool", description="VPRotate when Global, otherwise Rotate (gizmo)",
                          default=dv["rot_got"])
    scl_got: BoolProperty(name="Scale GlobalOrTool", description="VPResize when Global, otherwise Scale (gizmo)",
                          default=dv["scl_got"])
    # Quick Scale
    qs_user_value: FloatProperty(default=dv["qs_user_value"],
                                 description="Set dimension (Unit meter) or Unit sized to fit value with chosen axis. "
                                             "Obj & Edit mode (selection)",
                                 precision=3, subtype="DISTANCE", unit="LENGTH")
    qs_unit_size: BoolProperty(default=dv["qs_unit_size"])
    # Cleaning Tools
    clean_doubles: BoolProperty(name="Double Geo", default=dv["clean_doubles"],
                                description="Vertices occupying the same location (within 0.0001)")
    clean_doubles_val: FloatProperty(name="Double Geo Distance", default=dv["clean_doubles_val"], precision=4)
    clean_loose: BoolProperty(name="Loose Verts/Edges", default=dv["clean_loose"],
                              description="Verts/Edges not attached to faces")
    clean_interior: BoolProperty(name="Interior Faces", default=dv["clean_interior"],
                                 description="Faces where all edges have more than 2 face users")
    clean_degenerate: BoolProperty(name="Degenerate Geo", default=dv["clean_degenerate"],
                                   description="Non-Manifold geo: Edges with no length & Faces with no area")
    clean_tinyedge: BoolProperty(name="Tiny Edges", default=dv["clean_tinyedge"],
                                 description="Edges that are shorter than the Tiny-Edge Value set\n"
                                             "Selection only - will select also in Clean Mode")
    clean_tinyedge_val: FloatProperty(name="Tiny Edge Limit", default=dv["clean_tinyedge_val"], precision=4,
                                      description="Shortest allowed Edge length for Tiny Edge Selection")
    clean_collinear: BoolProperty(name="Collinear Verts", default=dv["clean_collinear"],
                                  description="Additional(Superfluous) verts in a straight line on an edge")
    # Cursor Fit OP Option
    cursorfit: BoolProperty(description="Also set Orientation & Pivot to Cursor", default=dv["cursorfit"])
    # Linear Array Global Only Option
    lineararray_go: BoolProperty(description="Applies Rotation and usese Global Orientation & Pivot during modal",
                                 default=dv["lineararray_go"])
    # Material ID Colors
    idm01: FloatVectorProperty(name="IDM01", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv["idm01"])
    idm02: FloatVectorProperty(name="IDM02", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv["idm02"])
    idm03: FloatVectorProperty(name="IDM03", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv["idm03"])
    idm04: FloatVectorProperty(name="IDM04", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv["idm04"])
    idm05: FloatVectorProperty(name="IDM05", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm05'])
    idm06: FloatVectorProperty(name="IDM06", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm06'])
    idm07: FloatVectorProperty(name="IDM07", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm07'])
    idm08: FloatVectorProperty(name="IDM08", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm08'])
    idm09: FloatVectorProperty(name="IDM09", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm09'])
    idm10: FloatVectorProperty(name="IDM10", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm10'])
    idm11: FloatVectorProperty(name="IDM11", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm11'])
    idm12: FloatVectorProperty(name="IDM12", subtype='COLOR', size=4, min=0.0, max=1.0, default=dv['idm12'])
    # Material ID Names
    idm01_name: StringProperty(default=dv["idm01_name"])
    idm02_name: StringProperty(default=dv["idm02_name"])
    idm03_name: StringProperty(default=dv["idm03_name"])
    idm04_name: StringProperty(default=dv["idm04_name"])
    idm05_name: StringProperty(default=dv["idm05_name"])
    idm06_name: StringProperty(default=dv["idm06_name"])
    idm07_name: StringProperty(default=dv["idm07_name"])
    idm08_name: StringProperty(default=dv["idm08_name"])
    idm09_name: StringProperty(default=dv["idm09_name"])
    idm10_name: StringProperty(default=dv["idm10_name"])
    idm11_name: StringProperty(default=dv["idm11_name"])
    idm12_name: StringProperty(default=dv["idm12_name"])
    # Material ID Options
    object_color: BoolProperty(description="Set ID color also to Object Viewport Display", default=dv["object_color"])
    matvp_color: BoolProperty(description="Set ID color also to Material Viewport Display", default=dv["matvp_color"])
    vpmuted: BoolProperty(description="Tone down ID colors slightly for Viewport Display (only)", default=dv["vpmuted"])
    # Subd Toggle
    vp_level: IntProperty(min=0, max=64, description="Viewport Levels to be used", default=dv["vp_level"])
    render_level: IntProperty(min=0, max=64, description="Render Levels to be used", default=dv["render_level"])
    flat_edit: BoolProperty(description="Set Flat Shading when Subd is Level 0", default=dv["flat_edit"])
    boundary_smooth: EnumProperty(items=[("PRESERVE_CORNERS", "Preserve Corners", ""), ("ALL", "All", "")],
                                  description="Controls how open boundaries are smoothed",
                                  default=dv["boundary_smooth"])
    limit_surface: BoolProperty(description="Use Limit Surface", default=dv["limit_surface"])
    optimal_display : BoolProperty(description="Use Optimal Display", default=dv["optimal_display"])
    on_cage: BoolProperty(description="Show On Edit Cage", default=dv["on_cage"])
    subd_autosmooth: BoolProperty(description="ON:Autosmooth is turned off by toggle when subd is on - and vice versa\n"
                                              "OFF:Autosmooth is not changed by toggle", name="Autosmooth Toggle",
                                  default=dv["subd_autosmooth"])
    # Snapping Combos
    snap_elements1: StringProperty(description="Snapping Element Combo 1", default=dv["snap_elements1"])
    snap_elements2: StringProperty(description="Snapping Element Combo 2", default=dv["snap_elements2"])
    snap_elements3: StringProperty(description="Snapping Element Combo 3", default=dv["snap_elements3"])
    snap_elements4: StringProperty(description="Snapping Element Combo 4", default=dv["snap_elements4"])
    snap_elements5: StringProperty(description="Snapping Element Combo 5", default=dv["snap_elements5"])
    snap_elements6: StringProperty(description="Snapping Element Combo 6", default=dv["snap_elements6"])
    snap_targets1: StringProperty(description="Snapping Targets Combo 1", default=dv["snap_targets1"])
    snap_targets2: StringProperty(description="Snapping Targets Combo 2", default=dv["snap_targets2"])
    snap_targets3: StringProperty(description="Snapping Targets Combo 3", default=dv["snap_targets3"])
    snap_targets4: StringProperty(description="Snapping Targets Combo 4", default=dv["snap_targets4"])
    snap_targets5: StringProperty(description="Snapping Targets Combo 5", default=dv["snap_targets5"])
    snap_targets6: StringProperty(description="Snapping Targets Combo 6", default=dv["snap_targets6"])
    snap_bools1: BoolVectorProperty(description="Snapping Bools Combo 1", size=9, default=dv["snap_bools1"])
    snap_bools2: BoolVectorProperty(description="Snapping Bools Combo 2", size=9, default=dv["snap_bools2"])
    snap_bools3: BoolVectorProperty(description="Snapping Bools Combo 3", size=9, default=dv["snap_bools3"])
    snap_bools4: BoolVectorProperty(description="Snapping Bools Combo 4", size=9, default=dv["snap_bools4"])
    snap_bools5: BoolVectorProperty(description="Snapping Bools Combo 5", size=9, default=dv["snap_bools5"])
    snap_bools6: BoolVectorProperty(description="Snapping Bools Combo 6", size=9, default=dv["snap_bools6"])
    # snap combo naming
    snap_name1: StringProperty(description="Snapping Combo 1 Name", default=dv["snap_name1"])
    snap_name2: StringProperty(description="Snapping Combo 2 Name", default=dv["snap_name2"])
    snap_name3: StringProperty(description="Snapping Combo 3 Name", default=dv["snap_name3"])
    snap_name4: StringProperty(description="Snapping Combo 4 Name", default=dv["snap_name4"])
    snap_name5: StringProperty(description="Snapping Combo 5 Name", default=dv["snap_name5"])
    snap_name6: StringProperty(description="Snapping Combo 6 Name", default=dv["snap_name6"])
    # Auto activation Option
    combo_autosnap: BoolProperty(name="Auto-Activate Snap",
                                 description="Auto activate snapping mode when using snap combo",
                                 default=dv["combo_autosnap"])
    # paste+ merge option
    paste_merge: BoolProperty(
        description="(Paste+ Object Mode) ON:Merge (edit mode) cache to selected object. OFF:Make new object",
        default=dv["paste_merge"])
    # Context Delete Hierarchy
    h_delete: BoolProperty(description="And the children too (in Object Mode)", default=dv["h_delete"])
    # Transform Toggle
    tt_mode: BoolVectorProperty(description="Toggles between default transform tools, MouseAxis or VP", size=3,
                                default=dv["tt_mode"])
    tt_handles: BoolProperty(description="TT Default uses the handle tools or the classic style ('Grab' etc.)",
                             default=dv["tt_handles"])
    tt_select: BoolProperty(
        description="Switches to Select Tool (Tweak) for when default handle tools are active when toggling TT",
        default=dv["tt_select"])
    tt_extrude: BoolProperty(description="Use TT Mode for transform: Default, MouseAxis and VP, except faces",
                             default=dv["tt_extrude"])
    tt_linkdupe: BoolProperty(description="Global TT Duplicate Linked Toggle (includes Mouse Axis Dupe & VP Dupe)",
                              default=dv["tt_linkdupe"])
    # Use Render Slot Cycling
    renderslotcycle: BoolProperty(name="Render Slot Cycle",
                                  description="Enable render slot cycling (to the first empty render slot)",
                                  default=dv["renderslotcycle"])
    # radial array autoarrange
    ra_autoarrange: BoolProperty(name="Auto-arrange/In-place Toggle",
                                 description="Auto-arrange object to Radial Array or use current placement",
                                 default=dv["ra_autoarrange"])
    # RISC notify or wrap to 1st toggle
    renderslotfullwrap: BoolProperty(
        name="Render Slot Full-Wrap",
        description="Back to 1st slot when full and cycle step fwd, or stop and notify",
        default=dv["renderslotfullwrap"])
    # Get Set Edit Mode Element Pick
    getset_ep: BoolProperty(name="Get & Set Edit with Element Pick",
                            description="(In Edit Mode) Component Mode based on element under mouse "
                                        "(Vert, Edge or Face)", default=dv["getset_ep"])
    # Multi Cut prefs
    mc_relative: IntProperty(name="Relative Offset from endpoint. Mirrored automatically to the other end point.",
                             min=1, max=49, default=dv["mc_relative"], subtype="PERCENTAGE")
    mc_fixed: FloatProperty(name="Fixed Offset from endpoint. Mirrored automatically to the other end point.", min=0,
                            default=dv["mc_fixed"], subtype="DISTANCE", unit="LENGTH")
    mc_center: IntProperty(name="Center Cut. 1 or 0 for none.", min=0, max=1, default=dv["mc_center"])
    mc_prefs: FloatVectorProperty(size=32, precision=4, default=dv["mc_prefs"])
    mc_name0: StringProperty(description="MultiCut Preset 1", default=dv["mc_name0"])
    mc_name1: StringProperty(description="MultiCut Preset 2", default=dv["mc_name1"])
    mc_name2: StringProperty(description="MultiCut Preset 3", default=dv["mc_name2"])
    mc_name3: StringProperty(description="MultiCut Preset 4", default=dv["mc_name3"])
    mc_name4: StringProperty(description="MultiCut Preset 5", default=dv["mc_name4"])
    mc_name5: StringProperty(description="MultiCut Preset 6", default=dv["mc_name5"])
    mc_name6: StringProperty(description="MultiCut Preset 7", default=dv["mc_name6"])
    mc_name7: StringProperty(description="MultiCut Preset 8", default=dv["mc_name7"])
    # DLC sel only
    dlc_so: BoolProperty(name="Selection-Only Toggle",
                         description="No mouse-pick, selected element only (nearest selected edge in face limit "
                                     "selection)\nAffects all 'Direct' operators",
                         default=dv["dlc_so"])
    # Shading Toggle Tri mode
    shading_tris: BoolProperty(name="Flat Shading Triangulate",
                               description="Flat Shading Triangulate:\n"
                                           "Use Triangulate Modifier (always last) for more accurate flat shading",
                               default=dv["shading_tris"])
    # Frame All Mesh Only
    frame_mo: BoolProperty(name="Geo Only",
                           description="Ignore non-geo objects (lights, cameras etc) for Frame All (not selected)",
                           default=dv["frame_mo"])
    # Mouse Axis Move - Scale ignore
    mam_scl: BoolProperty(name="MAS",
                          description="Mouse Axis Scale - Uncheck for default (unlocked) Scale behaviour for "
                                      "TT Scale MouseAxis",
                          default=dv["mam_scl"])
    # korean toggle
    korean: BoolProperty(name="Korean/Flat Bevel Toggle",
                         description="Toggles Korean / Flat Bevel preset for Context Bevel and keKit subdtools bevels",
                         default=dv["korean"])
    # select by display type active collection only toggle
    sel_type_coll: BoolProperty(name="Active Collection Only",
                                description="Select by display type in active collection only",
                                default=dv["sel_type_coll"])
    # Unbevel Auto-Edge Ring
    unbevel_autoring: BoolProperty(name="Unbevel Auto-EdgeRing",
                                   description="Runs Edge-Ring selection before Unbevel",
                                   default=dv["unbevel_autoring"])
    # Context Select Object Mode Full Hierarchy
    context_select_h: BoolProperty(name="FH",
                                   description="Context Select Object Mode Full Hierarchy "
                                               "(not just the children, but the parents too)"
                                               "Note: Also applies to Expand/Contract",
                                   default=dv["context_select_h"])


class KeSavePrefs(bpy.types.Operator):
    bl_idname = "view3d.ke_prefs_save"
    bl_label = "Save keKit Settings"
    bl_description = "Saves current kit settings (JSON-file, settings are global & persistent)"

    def execute(self, context):
        prefs = get_scene_prefs(context)
        ver = context.preferences.addons[__package__].preferences.kekit_version
        if "version" in prefs:
            prefs["version"] = ver
        write_prefs(prefs)
        # bpy.ops.ke.kit_keymap(mode="SAVE")
        self.report({"INFO"}, "keKit Settings Saved!")
        return {'FINISHED'}


class KeKitPropertiesTemp(PropertyGroup):
    slush: StringProperty(default="")
    view_query: StringProperty(default=" N/A ")
    toggle: BoolProperty(default=False)
    is_rendering: BoolProperty(default=False)
    cursorslot1: FloatVectorProperty(size=6)
    cursorslot2: FloatVectorProperty(size=6)
    cursorslot3: FloatVectorProperty(size=6)
    cursorslot4: FloatVectorProperty(size=6)
    cursorslot5: FloatVectorProperty(size=6)
    cursorslot6: FloatVectorProperty(size=6)
    viewslot1: FloatVectorProperty(size=9)
    viewslot2: FloatVectorProperty(size=9)
    viewslot3: FloatVectorProperty(size=9)
    viewslot4: FloatVectorProperty(size=9)
    viewslot5: FloatVectorProperty(size=9)
    viewslot6: FloatVectorProperty(size=9)
    viewtoggle: FloatVectorProperty(size=9)
    viewcycle: IntProperty(default=0, min=0, max=5)
    focus: BoolVectorProperty(size=16)
    focus_stats: BoolProperty()
    kcm_axis: EnumProperty(items=[
        ("X", "X", "", 1),
        ("Y", "Y", "", 2),
        ("Z", "Z", "", 3)],
        name="Cursor Axis", default="Y", description="Which of the cursors (local) axis to rotate around")
    kcm_rot_preset: EnumProperty(items=[
        ("5", "5\u00B0", "", 1),
        ("15", "15\u00B0", "", 2),
        ("45", "45\u00B0", "", 3),
        ("90", "90\u00B0", "", 4)],
        name="Step Presets", default="90", description="Preset rotation values for step-rotate")
    kcm_custom_rot: FloatProperty(name="Custom Step", default=0, subtype="ANGLE", unit="ROTATION", precision=3,
                                  description="Custom rotation (non zero will override preset-use) for step-rotate")


class KeMouseOverInfo(Operator):
    bl_idname = "ke_mouseover.info"
    bl_label = "Info"

    text: StringProperty(name="Info", description="Info", default='')

    @classmethod
    def description(cls, context, properties):
        return properties.text

    def execute(self, context):
        return {'INTERFACE'}


class KeIconPreload(bpy.types.Header):
    bl_idname = "VIEW3D_HT_KE_ICONPRELOAD"
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        # Terrible OpenGL style preloading to avoid seeing (the most used) icons load...
        layout = self.layout
        row = layout.row()
        row.ui_units_x = 0.01
        row.scale_y = 0.01
        row.scale_x = 0.01
        # SNAPPING
        row.label(icon_value=pcoll['kekit']['ke_snap1'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_snap2'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_snap3'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_snap4'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_snap5'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_snap6'].icon_id)
        # OPC
        row.label(icon_value=pcoll['kekit']['ke_opc1'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_opc2'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_opc3'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_opc4'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_opc5'].icon_id)
        row.label(icon_value=pcoll['kekit']['ke_opc6'].icon_id)


class UIKeKitMain(Panel):
    bl_idname = "UI_PT_kekit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = __package__
    bl_label = 'keKit v2.%s' % str(kekit_version)[1:]
    bl_description = 'keKit Main Panel'

    def draw_header_preset(self, context):
        layout = self.layout
        layout.emboss = 'NONE'
        row = layout.row(align=True)
        if new_version is not None:
            row.scale_x = 0.85
            row.operator("wm.url_open", text="%s" % str(new_version)[1:],
                         icon="ERROR").url = "https://artbykjell.com/blender.html"
            # row.separator()
        elif not bpy.context.preferences.addons[__package__].preferences.version_check:
            # row.scale_x = 0.6
            row.label(text="", icon="ERROR")
            row.separator(factor=0.5)
            row.label(text="", icon="X")
            row.separator(factor=2)
        row.scale_x = 1
        row.operator('view3d.ke_prefs_save', text="", icon="FILE_CACHE")
        row.separator()

    def draw(self, context):
        layout = self.layout


class KeKitAddonPreferences(AddonPreferences):
    bl_idname = __package__

    prefs_loc: StringProperty(name="Prefs File(s) Location", default="",
                              description="Export directory. Hard-coded. For reference (clipboard use) only")

    kekit_version: FloatProperty(default=kekit_version)
    version_check: BoolProperty(name="New Version Check", default=True,
                                description="Check for newer keKit kekit_version at startup")

    modal_color_header: FloatVectorProperty(name="Header Color", subtype='COLOR',
                                            size=4, default=[0.8, 0.8, 0.8, 1.0])
    modal_color_text: FloatVectorProperty(name="Text Color", subtype='COLOR',
                                          size=4, default=[0.8, 0.8, 0.8, 1.0])
    modal_color_subtext: FloatVectorProperty(name="Sub-Text Color", subtype='COLOR',
                                             size=4, default=[0.5, 0.5, 0.5, 1.0])

    ui_scale: FloatProperty(name="Text Scale", default=1.0, min=0.1, max=10,
                            description="keKIT modal UI text scale - multiplied to Blender UI Scale")

    m_modes: BoolProperty(name="0: Modes", default=False, description="Read Docs/Wiki")
    m_dupe: BoolProperty(name="1: Duplication", default=True, description="Read Docs/Wiki")
    m_main: BoolProperty(name="2: Main", default=True, description="Read Docs/Wiki")
    m_render: BoolProperty(name="3: Render", default=True, description="Read Docs/Wiki")
    m_bookmarks: BoolProperty(name="4: Bookmarks", default=True, description="Read Docs/Wiki")
    m_selection: BoolProperty(name="5: Select & Align", default=True, description="Read Docs/Wiki")
    m_modeling: BoolProperty(name="6: Modeling", default=True, description="Read Docs/Wiki")
    m_directloopcut: BoolProperty(name="6A: DirectLoopCut", default=True, description="Read Docs/Wiki")
    m_multicut: BoolProperty(name="6B: MultiCut", default=True, description="Read Docs/Wiki")
    m_subd: BoolProperty(name="6C: SubD Tools", default=True, description="Read Docs/Wiki")
    m_unrotator: BoolProperty(name="6D: Unrotator", default=True, description="Read Docs/Wiki")
    m_fitprim: BoolProperty(name="6E: FitPrim", default=True, description="Read Docs/Wiki")
    m_contexttools: BoolProperty(name="6F: Context Tools", default=True, description="Read Docs/Wiki")
    m_tt: BoolProperty(name="7: Transform Tools", default=True, description="Read Docs/Wiki")
    m_idmaterials: BoolProperty(name="8: ID Materials", default=True, description="Read Docs/Wiki")
    m_cleanup: BoolProperty(name="9: Clean-Up Tools", default=True, description="Read Docs/Wiki")
    m_piemenus: BoolProperty(name="10: Pie Menus", default=True, description="Read Docs/Wiki")
    kcm: BoolProperty(name="keKit Cursor Menu", default=True, description="Show KeKit Cursor Menu icon in toolbar\n"
                                                                          "Note: Requires keKit Select & Align Module")

    tt_icon_pos: EnumProperty(
        name="TT Icon Placement",
        description="Viewport icons for Transform Tools (TT) module",
        items=[("LEFT", "Left", ""),
               ("CENTER", "Center", ""),
               ("RIGHT", "Right", ""),
               ("REMOVE", "Remove", "")
               ],
        update=set_tt_icon_pos,
        default="CENTER")

    def draw(self, context):
        layout = self.layout
        self.prefs_loc = bpy.utils.user_resource('CONFIG')
        g = layout.row()
        g.label(text="Version: 2." + str(kekit_version)[1:] + ":")
        g.prop(self, "version_check", text="Version Check", toggle=True)
        g.label(text="keKit Cursor Menu")
        g.prop(self, "kcm", text="Show", toggle=True)

        if bpy.context.preferences.addons[__package__].preferences.m_tt:
            g = layout.row()
            g.label(text="Viewport TT Icons:")
            g.prop(self, "tt_icon_pos", expand=True)

        layout.prop(self, "prefs_loc", text="")
        layout.operator("view3d.ke_prefs_save", icon="FILE_CACHE", text="Save keKit Settings")

        box = layout.box()
        row = box.row()
        row.label(text="keKit Main Panel Modules:")
        row.operator("script.reload", text="Reload Add-ons", icon="FILE_REFRESH")
        g = box.row()
        g.prop(self, "m_modes", toggle=True)
        g.prop(self, "m_dupe", toggle=True)
        g.prop(self, "m_main", toggle=True)
        g.prop(self, "m_render", toggle=True)

        row = box.row()
        row.label(text="keKit Modules:")
        g = box.grid_flow(row_major=True, columns=4)
        g.prop(self, "m_bookmarks", toggle=True)
        g.prop(self, "m_selection", toggle=True)
        g.prop(self, "m_modeling", toggle=True)
        g.prop(self, "m_directloopcut", toggle=True)
        g.prop(self, "m_multicut", toggle=True)
        g.prop(self, "m_subd", toggle=True)
        g.prop(self, "m_unrotator", toggle=True)
        g.prop(self, "m_fitprim", toggle=True)
        g.prop(self, "m_contexttools", toggle=True)
        g.prop(self, "m_tt", toggle=True)
        g.prop(self, "m_idmaterials", toggle=True)
        g.prop(self, "m_cleanup", toggle=True)
        g.prop(self, "m_piemenus", toggle=True)

        layout.label(text="Modal Text:")
        g = layout.grid_flow(row_major=True, columns=2)
        g.use_property_split = True
        g.prop(self, "ui_scale")
        g.prop(self, 'modal_color_header')
        g.prop(self, 'modal_color_text')
        g.prop(self, 'modal_color_subtext')


classes = (
    KeKitAddonPreferences,
    UIKeKitMain,
    KeKitProperties,
    KeKitPropertiesTemp,
    KeSavePrefs,
    KeMouseOverInfo,
    KeIconPreload
)

modules = ()

pcoll = {}
icons = ["ke_bm1.png", "ke_bm2.png", "ke_bm3.png", "ke_bm4.png", "ke_bm5.png", "ke_bm6.png",
         "ke_cursor1.png", "ke_cursor2.png", "ke_cursor3.png", "ke_cursor4.png", "ke_cursor5.png", "ke_cursor6.png",
         "ke_dot1.png", "ke_dot2.png", "ke_dot3.png", "ke_dot4.png", "ke_dot5.png", "ke_dot6.png",
         "ke_opc1.png", "ke_opc2.png", "ke_opc3.png", "ke_opc4.png", "ke_opc5.png", "ke_opc6.png",
         "ke_snap1.png", "ke_snap2.png", "ke_snap3.png", "ke_snap4.png", "ke_snap5.png", "ke_snap6.png",
         "ke_uncheck.png"]


def register():

    from bpy.utils import previews
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pr = previews.new()
    for i in icons:
        name = i[:-4]
        pr.load(name, os.path.join(icons_dir, i), 'IMAGE')
    pcoll['kekit'] = pr

    for cls in classes:
        bpy.utils.register_class(cls)

    if bpy.context.preferences.addons[__package__].preferences.version_check:
        version_check()

    Scene.kekit_temp = PointerProperty(type=KeKitPropertiesTemp)
    Scene.kekit = PointerProperty(type=KeKitProperties)

    bpy.types.VIEW3D_HT_header.append(KeIconPreload.draw)


def unregister():

    bpy.types.VIEW3D_HT_header.remove(KeIconPreload.draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    try:
        del Scene.kekit
        del Scene.kekit_temp
    except Exception as e:
        print('unregister fail:\n', e)
        pass

    for pr in pcoll.values():
        bpy.utils.previews.remove(pr)
    pcoll.clear()


if __name__ == "__main__":
    register()
