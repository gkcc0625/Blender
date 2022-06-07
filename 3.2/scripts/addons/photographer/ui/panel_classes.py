from .. import camera_panel, render_queue, lightmixer
from . import camera_list, emissive_mixer, world_mixer

photographer_panel_classes = (
    camera_list.PHOTOGRAPHER_PT_ViewPanel_CameraList,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Camera,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Lens,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_DOF_Char,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Exposure,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_DOF,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Focus,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Autofocus,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_WhiteBalance,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Resolution,
    render_queue.PHOTOGRAPHER_PT_ViewPanel_RenderQueue,
)

lightmixer_panel_classes = (
    lightmixer.LIGHTMIXER_PT_ViewPanel,
    emissive_mixer.LIGHTMIXER_PT_EmissiveViewPanel,
    world_mixer.LIGHTMIXER_PT_WorldViewPanel,
)

# image_panel_classes = (
#     camera_panel.PHOTOGRAPHER_PT_ImageEditor_Exposure,
#     camera_panel.PHOTOGRAPHER_PT_NodeEditor_Exposure,
#     camera_panel.PHOTOGRAPHER_PT_ImageEditor_WhiteBalance,
#     camera_panel.PHOTOGRAPHER_PT_NodeEditor_WhiteBalance,
#     render_queue.PHOTOGRAPHER_PT_ImageEditor_RenderQueue,
#     render_queue.PHOTOGRAPHER_PT_NodeEditor_RenderQueue,
# )
