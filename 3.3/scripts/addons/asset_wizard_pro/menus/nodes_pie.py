# Copyright (C) 2022 Thomas Hoppe (h0bB1T). All rights reserved.
#
# Unauthorized copying of this file via any medium is strictly prohibited.
# Proprietary and confidential.

import bpy

from bpy.types import Menu, UILayout


from ..utils.blender import is_valid_node_space, shader_node_wizard_enabled
from ..registries.icons_registry import IconsRegistry
from ..registries.resource_lists_registry import ResourceListsRegistry
from ..operators.import_assets import ASSET_OT_import
from ..operators.std_node_drop import ASSET_OT_std_node_drop


class NODE_MT_awp_nodes_pie_menu(Menu):
    """
    The primary PIE menu, shown when hitting the primary addon button ('S').
    """
    bl_idname = 'NODE_MT_awp_nodes_pie_menu'
    bl_label = 'Asset Wizard Pro'


    @classmethod
    def poll(cls, context):
        return is_valid_node_space(context, ['ShaderNodeTree', 'GeometryNodeTree'])       

 
    def __std_simple_shader(self, l: UILayout, text: str, icon: str, type: str):
        ASSET_OT_std_node_drop.create_ui(l, 'Shader', type, '', '', text, icon, f'Drop a "{text}" node')


    def __std_simple_geometry(self, l: UILayout, text: str, icon: str, type: str, system: str = 'Geometry'):
        ASSET_OT_std_node_drop.create_ui(l, system, type, '', '', text, icon, f'Drop a "{text}" node')


    def __std_math(self, l: UILayout, text:str, mt: str):
        ASSET_OT_std_node_drop.create_ui(
            l, 
            'Shader', 
            'Math', 
            f"'{mt}'", 
            '', 
            text, 
            'DRIVER_TRANSFORM', 
            f'Drop new Math node and set operation to {text}'
        )


    def __std_vmath(self, l: UILayout, text:str, mt: str):
        ASSET_OT_std_node_drop.create_ui(
            l, 
            'Shader', 
            'VectorMath', 
            f"'{mt}'", 
            '', 
            text, 
            'TRACKING_CLEAR_FORWARDS', 
            f'Drop new Vector Math node and set operation to {text}'
        )


    def __std_mixrgb(self, l: UILayout, text:str, mt: str):
        ASSET_OT_std_node_drop.create_ui(
            l, 
            'Shader', 
            'MixRGB', 
            '', 
            f"'{mt}'", 
            text, 
            'IMAGE', 
            f'Drop new Mix RGB node and set blend type to {text}'
        )


    def __draw_std_nodes_shader(self, layout: UILayout):
        layout.ui_units_y = 20
        c = layout
        r = c.row(align=False)

        # Layer Weight, Fresnel, Invert, RGB Curves (Float Curves), Mapping

        s = r.column(align=True)
        self.__std_simple_shader(s, 'Map Range', 'UV_SYNC_SELECT', 'MapRange')
        self.__std_simple_shader(s, 'ColorRamp', 'NODE_TEXTURE', 'ValToRGB')
        self.__std_simple_shader(s, 'Combine XYZ', 'FULLSCREEN_EXIT', 'CombineXYZ')
        self.__std_simple_shader(s, 'Separate XYZ', 'FULLSCREEN_ENTER', 'SeparateXYZ')
        s.separator()
        self.__std_simple_shader(s, 'Geometry', 'MOD_WIREFRAME', 'NewGeometry')
        self.__std_simple_shader(s, 'Texture Coordinate', 'UV', 'TexCoord')
        s.separator()
        self.__std_simple_shader(s, 'Noise Texture', 'MOD_NOISE', 'TexNoise')
        self.__std_simple_shader(s, 'Musgrave Texture', 'RNDCURVE', 'TexMusgrave')
        self.__std_simple_shader(s, 'Voronoi Texture', 'LIGHTPROBE_PLANAR', 'TexVoronoi')
        self.__std_simple_shader(s, 'White Noise', 'SEQ_HISTOGRAM', 'TexWhiteNoise')
        self.__std_simple_shader(s, 'Image Texture', 'IMAGE_DATA', 'TexImage')
        s.separator()
        self.__std_simple_shader(s, 'Hue Saturation', 'COLOR', 'HueSaturation')
        self.__std_simple_shader(s, 'Brightness Contrast', 'IMAGE_ZDEPTH', 'BrightContrast')
        s.separator()
        self.__std_simple_shader(s, 'Bump Map', 'FORCE_TURBULENCE', 'Bump')
        self.__std_simple_shader(s, 'Normal Map', 'MOD_OCEAN', 'NormalMap')
        s.separator()
        self.__std_simple_shader(s, 'Principled BSDF', 'MATERIAL', 'BsdfPrincipled')
        self.__std_simple_shader(s, 'Mix Shader', 'ORIENTATION_GIMBAL', 'MixShader')
        self.__std_simple_shader(s, 'Emission', 'LIGHT', 'Emission')
        self.__std_simple_shader(s, 'Transparent', 'MOD_UVPROJECT', 'BsdfTransparent')
        self.__std_simple_shader(s, 'Principled Volume', 'OUTLINER_DATA_VOLUME', 'VolumePrincipled')

        s = r.column(align=True)
        self.__std_math(s, 'Add', 'ADD')
        self.__std_math(s, 'Sub', 'SUBTRACT')
        self.__std_math(s, 'Mul', 'MULTIPLY')
        self.__std_math(s, 'Div', 'DIVIDE')
        self.__std_math(s, 'MulA', 'MULTIPLY_ADD')
        s.separator()
        self.__std_math(s, 'Pwr', 'POWER')
        self.__std_math(s, 'Abs', 'ABSOLUTE')
        s.separator()
        self.__std_math(s, 'Min', 'MINIMUM')
        self.__std_math(s, 'Max', 'MAXIMUM')
        self.__std_math(s, 'Lt', 'LESS_THAN')
        self.__std_math(s, 'Gt', 'GREATER_THAN')
        self.__std_math(s, 'SMin', 'SMOOTH_MIN')
        self.__std_math(s, 'SMax', 'SMOOTH_MAX')
        s.separator()
        self.__std_math(s, 'Rnd', 'ROUND')
        self.__std_math(s, 'Flr', 'FLOOR')
        self.__std_math(s, 'Ceil', 'CEIL')
        s.separator()
        self.__std_math(s, 'Frc', 'FRACT')
        self.__std_math(s, 'Mod', 'MODULO')
        self.__std_math(s, 'Wrp', 'WRAP')
        self.__std_math(s, 'Snp', 'SNAP')
        self.__std_math(s, 'Pipo', 'PINGPONG')
        s.separator()
        self.__std_math(s, 'Sin', 'SINE')
        self.__std_math(s, 'Cos', 'COSINE')
        self.__std_math(s, 'Tan', 'TANGENT')

        s = r.column(align=True)
        self.__std_vmath(s, 'Add', 'ADD')
        self.__std_vmath(s, 'Sub', 'SUBTRACT')
        self.__std_vmath(s, 'Mul', 'MULTIPLY')
        self.__std_vmath(s, 'Div', 'DIVIDE')
        self.__std_vmath(s, 'MulA', 'MULTIPLY_ADD')
        s.separator()
        self.__std_vmath(s, 'Crs', 'CROSS_PRODUCT')
        self.__std_vmath(s, 'Prj', 'PROJECT')
        self.__std_vmath(s, 'Rfl', 'REFLECT')
        self.__std_vmath(s, 'Rfr', 'REFRACT')
        self.__std_vmath(s, 'FaFo', 'FACEFORWARD')
        self.__std_vmath(s, 'Dot', 'DOT_PRODUCT')
        s.separator()
        self.__std_vmath(s, 'Dst', 'DISTANCE')
        self.__std_vmath(s, 'Len', 'LENGTH')
        self.__std_vmath(s, 'Scl', 'SCALE')
        self.__std_vmath(s, 'Nrm', 'NORMALIZE')
        s.separator()
        self.__std_vmath(s, 'Abs', 'ABSOLUTE')
        self.__std_vmath(s, 'Min', 'MINIMUM')
        self.__std_vmath(s, 'Max', 'MAXIMUM')
        self.__std_vmath(s, 'Flr', 'FLOOR')
        self.__std_vmath(s, 'Ceil', 'CEIL')
        self.__std_vmath(s, 'Frc', 'FRACTION')
        self.__std_vmath(s, 'Mod', 'MODULO')
        self.__std_vmath(s, 'Wrp', 'WRAP')
        self.__std_vmath(s, 'Snp', 'SNAP')

        s = r.column(align=True)
        self.__std_mixrgb(s, 'Mix', 'MIX')
        self.__std_mixrgb(s, 'Darken', 'DARKEN')
        self.__std_mixrgb(s, 'Mul', 'MULTIPLY')
        self.__std_mixrgb(s, 'Burn', 'BURN')
        s.separator()
        self.__std_mixrgb(s, 'Lighten', 'LIGHTEN')
        self.__std_mixrgb(s, 'Screen', 'SCREEN')
        self.__std_mixrgb(s, 'Dodge', 'SCREEN')
        self.__std_mixrgb(s, 'Add', 'ADD')
        s.separator()
        self.__std_mixrgb(s, 'Overlay', 'OVERLAY')
        self.__std_mixrgb(s, 'SLight', 'SOFT_LIGHT')
        self.__std_mixrgb(s, 'LLight', 'LINEAR_LIGHT')
        s.separator()
        self.__std_mixrgb(s, 'Diff', 'DIFFERENCE')
        self.__std_mixrgb(s, 'Sub', 'SUBTRACT')
        self.__std_mixrgb(s, 'Div', 'DIVIDE')
        s.separator()
        self.__std_mixrgb(s, 'Hue', 'HUE')
        self.__std_mixrgb(s, 'Sat', 'SATURATION')
        self.__std_mixrgb(s, 'Color', 'COLOR')
        self.__std_mixrgb(s, 'Value', 'VALUE')


    def __draw_std_nodes_geometry(self, l: UILayout):
        nodes = {
            'Attribute': [
                ( 'Capture Attribute', 'MOD_HUE_SATURATION', 'CaptureAttribute' ),
                ( 'Transfer Attribute', 'MOD_HUE_SATURATION', 'AttributeTransfer' ),
            ],
            'Curve': [
                ( 'Curve to Mesh', 'GP_SELECT_STROKES', 'CurveToMesh' ),
                ( 'Curve to Points', 'DRIVER', 'CurveToPoints' ),
                ( 'Fillet Curve', 'GP_SELECT_BETWEEN_STROKES', 'FilletCurve' ),
                ( 'Sample Curve', 'IPO_BOUNCE', 'SampleCurve' ),
                ( 'Resample Curve', 'IPO_ELASTIC', 'ResampleCurve' ),
            ],
            'Curve Primitives': [
                ( 'Curve Circle', 'CURVE_BEZCIRCLE', 'CurvePrimitiveCircle' ),
                ( 'Curve Line', 'CURVE_PATH', 'CurvePrimitiveLine' ),
            ],
            'Geometry': [
                ( 'Bounding Box', 'META_PLANE', 'BoundBox' ),
                ( 'Convex Hull', 'META_ELLIPSOID', 'ConvexHull' ),
                ( 'Join Geometry', 'MOD_BUILD', 'JoinGeometry' ),
                ( 'Delete Geometry', 'PANEL_CLOSE', 'DeleteGeometry' ),
                ( 'Set Position', 'CON_ROTLIMIT', 'SetPosition' ),
                ( 'Set ID', 'COPYDOWN', 'SetID' ),
            ],
            'Input': [
                ( 'Collection Info', 'ANIM', 'CollectionInfo' ),
                ( 'Object Info', 'ANIM', 'ObjectInfo' ),
                ( 'Is Viewport', 'ANIM', 'IsViewport' ),
                ( 'ID', 'ANIM', 'InputID' ),
                ( 'Index', 'ANIM', 'InputIndex' ),
                ( 'Normal', 'ANIM', 'InputNormal' ),
                ( 'Position', 'ANIM', 'InputPosition' ),
            ],
            'Instances': [
                ( 'Instance on Points', 'FORCE_LENNARDJONES', 'InstanceOnPoints' ),
                ( 'Realize Instances', 'PIVOT_ACTIVE', 'RealizeInstances' ),
                ( 'Rotate Instances', 'DRIVER_ROTATIONAL_DIFFERENCE', 'RotateInstances' ),
                ( 'Scale Instances', 'MOD_WIREFRAME', 'ScaleInstances' ),
                ( 'Translate Instances', 'CON_LOCLIKE', 'TranslateInstances' ),
            ],
            'Material': [
                ( 'Set Material', 'MATERIAL', 'SetMaterial' ),
            ],
            'Mesh': [
                ( 'Extrude Mesh', 'MOD_SOLIDIFY', 'ExtrudeMesh' ),
                ( 'Mesh Boolean', 'MOD_BOOLEAN', 'MeshBoolean' ),
                ( 'Mesh to Curve', 'CURVE_NCURVE', 'MeshToCurve' ),
                ( 'Mesh to Points', 'MOD_PARTICLE_INSTANCE', 'MeshToPoints' ),
                ( 'Scale Elements', 'MOD_WIREFRAME', 'ScaleElements' ),
                ( 'Set Shade Smooth', 'NODE_MATERIAL', 'SetShadeSmooth' ),
            ],
            'Mesh Primitives': [
                ( 'Cube', 'MESH_CUBE', 'MeshCube' ),
                ( 'Cyclinder', 'MESH_CYLINDER', 'MeshCylinder' ),
                ( 'Grid', 'MESH_GRID', 'MeshGrid' ),
                ( 'Ico Sphere', 'MESH_ICOSPHERE', 'MeshIcoSphere' ),        
                ( 'Mesh Line', 'IPO_LINEAR', 'MeshLine' ),        
            ],
            'Point': [
                ( 'Distribute Points on Faces', 'STICKY_UVS_DISABLE', 'DistributePointsOnFaces')
            ],
            'Utilities': [
                ( 'Align Euler to Vector', 'HANDLE_ALIGNED', 'AlignEulerToVector', 'Function' ),
                ( 'Boolean Math', 'SHORTDISPLAY', 'BooleanMath', 'Function' ),
                ( 'Compare', 'SHORTDISPLAY', 'Compare', 'Function' ),
                ( 'Map Range', 'UV_SYNC_SELECT', 'MapRange', 'Shader' ),
                ( 'Math', 'DRIVER_TRANSFORM', 'Math', 'Shader' ),
                ( 'Random Value', 'MOD_NOISE', 'RandomValue', 'Function' ),
            ],
            'Vector': [
                ( 'Combine XYZ' , 'FULLSCREEN_EXIT', 'CombineXYZ', 'Shader' ),
                ( 'Separate XYZ' , 'FULLSCREEN_ENTER', 'SeparateXYZ', 'Shader' ),
                ( 'Vector Math' , 'TRACKING_CLEAR_FORWARDS', 'VectorMath', 'Shader' ),
            ]
        }

        columns = [
            [ 'Mesh', 'Curve', ],
            [ 'Geometry', 'Point', 'Instances', ],
            [ 'Mesh Primitives', 'Curve Primitives' ],
            [ 'Utilities', 'Material', 'Vector', 'Attribute', ],
            [ 'Input', ],
        ]

        l.ui_units_x = 30
        l.ui_units_y = 20
        c = l.grid_flow(columns=len(columns), even_columns=True)

        for i, col in enumerate(columns):
            r = c.column(align=True)
            for k in col:
                #r.label(text=f'{i}{k}:')
                for node in nodes[k]:
                    self.__std_simple_geometry(r, *node)
                r.separator()


    def __draw_imports(self, l: UILayout, is_shader: bool):
        #l.ui_units_x = 30
        l.ui_units_y = 20
        c = l.grid_flow(columns=0, even_columns=True, align=False)

        nodes = ResourceListsRegistry.get().shader_nodes() if is_shader else ResourceListsRegistry.get().geometry_nodes() 
        for k in sorted(nodes.keys()):
            r = c.column(align=True)
            r.label(text=f'{k}:')
            for file, name, short_name, desc in sorted(nodes[k], key=lambda x: x[2]):
                ASSET_OT_import.create_ui(r, 'SHADER' if is_shader else 'GEOMETRY', file, name, short_name, desc)


    def __draw_others_menu(self, l: UILayout):
        if shader_node_wizard_enabled():
            op = l.operator('wm.call_menu_pie', text='Shader Node Wizard', icon_value=IconsRegistry.get_icon('snw-logo-mini'))
            op.name = 'NODE_MT_snw_main_pie_menu'


    def draw(self, context: bpy.context):
        is_shader = context.space_data.tree_type == 'ShaderNodeTree'

        pie = self.layout.menu_pie()

        if is_shader:
            self.__draw_std_nodes_shader(pie.row().column(align=True)) # W
        else:
            self.__draw_std_nodes_geometry(pie.row().column(align=True)) # W

        self.__draw_imports(pie.row().column(align=True), is_shader) # E

        if is_shader:
            self.__draw_others_menu(pie.row().column(align=True)) # S

        c = pie.row().column(align=True) # N
        c.ui_units_x = 6
        c.menu('NODE_MT_add', text='All Nodes') 

