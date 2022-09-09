import bpy
render = bpy.context.scene.render
photographer = bpy.context.scene.camera.data.photographer

photographer.resolution_mode = '169'
photographer.resolution_x = 1920
photographer.resolution_y = 1080
photographer.ratio_x = 16.0
photographer.ratio_y = 9.0
photographer.resolution_rotation = 'LANDSCAPE'
photographer.longedge = 3840
render.resolution_percentage = 100
