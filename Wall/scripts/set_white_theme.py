import bpy
import os

def set_white_theme():
    # First try to load the light theme preset
    scripts_paths = bpy.utils.preset_paths('interface_theme')
    if scripts_paths:
        preset_path = os.path.join(scripts_paths[0], "blender_light.py")
        if os.path.exists(preset_path):
            bpy.ops.script.execute_preset(filepath=preset_path, menu_idname="USERPREF_MT_interface_theme_presets")
            
    # Now override specific theme colors to be pure white
    theme = bpy.context.preferences.themes[0]
    
    # 3D Viewport
    view3d = theme.view_3d
    view3d.space.gradients.high_gradient = (1.0, 1.0, 1.0)
    view3d.space.gradients.gradient = (1.0, 1.0, 1.0)
    
    # Grid color (make it light gray so it's visible on white)
    view3d.space.gradients.high_gradient = (1.0, 1.0, 1.0)
    
    # Node Editor
    node_editor = theme.node_editor
    node_editor.space.back = (0.95, 0.95, 0.95)
    
    # Save the preferences
    bpy.ops.wm.save_userpref()
    print("White theme successfully applied and saved to user preferences.")

if __name__ == "__main__":
    set_white_theme()
