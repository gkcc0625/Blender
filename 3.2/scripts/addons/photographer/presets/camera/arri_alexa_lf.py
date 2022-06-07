import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'CUSTOM'
camera.sensor_width = 36.7
camera.sensor_height = 25.54
camera.show_passepartout = True
camera.passepartout_alpha = 0.949999988079071
