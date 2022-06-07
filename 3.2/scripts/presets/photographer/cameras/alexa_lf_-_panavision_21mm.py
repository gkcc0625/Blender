import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'CUSTOM'
photographer.aperture = 1.899999976158142
photographer.aperture_preset = '2.8'
photographer.aperture_slider_enable = True
photographer.focus_plane_color = (0.03108576312661171, 1.0, 0.674201488494873, 0.30804598331451416)
camera.sensor_width = 36.7
camera.lens = 21.0
camera.dof.use_dof = False
camera.dof.focus_distance = 10.0
camera.dof.aperture_ratio = 1.0
camera.dof.aperture_blades = 0
camera.dof.aperture_rotation = 0.0
camera.show_passepartout = True
camera.passepartout_alpha = 0.949999988079071
