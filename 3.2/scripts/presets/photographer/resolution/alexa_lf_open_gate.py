import bpy
render = bpy.context.scene.render
photographer = bpy.context.scene.camera.data.photographer

photographer.resolution_mode = 'CUSTOM_RATIO'
photographer.resolution_x = 4448
photographer.resolution_y = 1080
photographer.ratio_x = 1.4365999698638916
photographer.ratio_y = 1.0
photographer.resolution_rotation = 'LANDSCAPE'
photographer.longedge = 1920
render.resolution_percentage = 100
