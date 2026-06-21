import bpy
import os
import math
import mathutils
import mathutils.noise

def main():
    print("Starting simulation script...")
    
    # Set default camera settings variable to None
    saved_camera_settings = None
    
    # Helper to select only one object and make it active
    def select_only(obj):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    
    # 1. Clear ALL existing objects in the scene for a clean slate
    print("Clearing all objects in the scene...")
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
            
    # 2. Import the bone model
    glb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brachial_bone_humerus_chicken.glb")
    if not os.path.exists(glb_path):
        print(f"Error: GLB file not found at {glb_path}")
        return
        
    print(f"Importing bone model from: {glb_path}")
    try:
        bpy.ops.wm.gltf_import(filepath=glb_path)
        print("Imported using wm.gltf_import")
    except Exception as e:
        print(f"Failed to import with wm.gltf_import: {e}")
        try:
            bpy.ops.import_scene.gltf(filepath=glb_path)
            print("Imported using import_scene.gltf")
        except Exception as e2:
            print(f"Failed to import with import_scene.gltf: {e2}")
            return

    # Find the imported mesh object
    imported_mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            imported_mesh = obj
            break
            
    if not imported_mesh:
        print("Error: No mesh object imported")
        return
        
    # Rename to Chicken_Bone
    imported_mesh.name = "Chicken_Bone"
    Chicken_Bone = imported_mesh
    print(f"Renamed imported mesh to: {Chicken_Bone.name}")
    
    # Make active and clear any object-level parent transform/rotation/scale first
    select_only(Chicken_Bone)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    # 3. Orient bone vertically and scale down to exactly 8cm
    verts = Chicken_Bone.data.vertices
    # Sample every 10th vertex to find the furthest pair (very fast)
    sampled_cos = [v.co.copy() for i, v in enumerate(verts) if i % 10 == 0]
    max_dist = 0.0
    p1, p2 = None, None
    for i in range(len(sampled_cos)):
        for j in range(i + 1, len(sampled_cos)):
            d = (sampled_cos[i] - sampled_cos[j]).length
            if d > max_dist:
                max_dist = d
                p1, p2 = sampled_cos[i], sampled_cos[j]
                
    if p1 is not None and p2 is not None:
        midpoint = (p1 + p2) / 2
        bone_dir = (p1 - p2).normalized()
        if bone_dir.z < 0:
            bone_dir = -bone_dir
            
        # Rotation to align bone length vector with Z axis
        target_dir = mathutils.Vector((0, 0, 1))
        rot_q = bone_dir.rotation_difference(target_dir)
        
        # Scale factor to make bone height exactly 8cm (0.08m)
        scale_factor = 0.08 / max_dist
        
        # Apply orientation, centering, and scale directly to vertex coordinates
        for v in verts:
            v.co = rot_q @ (v.co - midpoint) * scale_factor
            
        Chicken_Bone.data.update()
        print(f"Re-oriented bone vertically, centered at origin, and scaled to exactly 8cm (scale_factor={scale_factor})")
    else:
        print("Error: Could not determine bone orientation")
        return
        
    # 4. Calculate bounding box for the transformed bone
    z_coords = [v.co.z for v in verts]
    z_min = min(z_coords)
    z_max = max(z_coords)
    z_height = z_max - z_min
    
    x_coords = [v.co.x for v in verts]
    y_coords = [v.co.y for v in verts]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    center_z = (z_min + z_max) / 2
    
    size_x = x_max - x_min
    size_y = y_max - y_min
    
    print(f"Bone bounds: X=[{x_min:.5f}, {x_max:.5f}], Y=[{y_min:.5f}, {y_max:.5f}], Z=[{z_min:.5f}, {z_max:.5f}]")
    print(f"Bone height: {z_height:.5f} (meters)")
    
    # Group thresholds: clamps cover more bone (22% of height on each end)
    top_threshold = z_max - 0.22 * z_height
    bottom_threshold = z_min + 0.22 * z_height
    
    # Create groups for clamps (we keep them for visual positioning)
    group_top = Chicken_Bone.vertex_groups.new(name="Group_Top")
    group_bottom = Chicken_Bone.vertex_groups.new(name="Group_Bottom")
    
    top_indices = []
    bottom_indices = []
    
    for v in verts:
        if v.co.z >= top_threshold:
            top_indices.append(v.index)
        elif v.co.z <= bottom_threshold:
            bottom_indices.append(v.index)
            
    if top_indices:
        group_top.add(top_indices, 1.0, 'ADD')
    if bottom_indices:
        group_bottom.add(bottom_indices, 1.0, 'ADD')
    
    # 5. Create Clamps at the centroids of top and bottom groups
    top_cos = [verts[idx].co for idx in top_indices]
    bottom_cos = [verts[idx].co for idx in bottom_indices]
    
    clamp_top_loc = sum(top_cos, mathutils.Vector()) / len(top_cos) if top_cos else mathutils.Vector((center_x, center_y, z_max))
    clamp_bottom_loc = sum(bottom_cos, mathutils.Vector()) / len(bottom_cos) if bottom_cos else mathutils.Vector((center_x, center_y, z_min))
    
    clamp_top = bpy.data.objects.new("Clamp_Top", None)
    clamp_top.location = clamp_top_loc
    clamp_top.empty_display_type = 'CUBE'
    clamp_top.empty_display_size = z_height * 0.22  # Fit display to clamp coverage
    bpy.context.collection.objects.link(clamp_top)
    
    clamp_bottom = bpy.data.objects.new("Clamp_Bottom", None)
    clamp_bottom.location = clamp_bottom_loc
    clamp_bottom.empty_display_type = 'CUBE'
    clamp_bottom.empty_display_size = z_height * 0.22
    bpy.context.collection.objects.link(clamp_bottom)
    
    print(f"Created clamps: Clamp_Top at {clamp_top_loc}, Clamp_Bottom at {clamp_bottom_loc}")
    
    # 6. Create and configure Lattice for necking and stretching
    # The Lattice will handle both stretching (Z-translation) and necking (X/Y scale).
    # To keep clamped regions rigid:
    # W=0, W=1: displacement=0, necking=0 (rigid bottom clamp)
    # W=3, W=4: displacement=max_stretch, necking=0 (rigid top clamp)
    # W=2: displacement=0.5*max_stretch, necking=max_necking (middle zone)
    lattice_data = bpy.data.lattices.new("Lattice_Data")
    lattice_obj = bpy.data.objects.new("Lattice_Obj", lattice_data)
    bpy.context.collection.objects.link(lattice_obj)
    
    middle_height = top_threshold - bottom_threshold
    lattice_obj.location = (center_x, center_y, center_z)
    lattice_obj.scale = (size_x * 1.5, size_y * 1.5, middle_height * 1.2) # Pad slightly beyond middle zone
    
    lattice_data.points_u = 3
    lattice_data.points_v = 3
    lattice_data.points_w = 5
    
    basis = lattice_obj.shape_key_add(name="Basis", from_mix=False)
    necking_key = lattice_obj.shape_key_add(name="Necking", from_mix=False)
    
    u_dim = lattice_data.points_u
    v_dim = lattice_data.points_v
    w_dim = lattice_data.points_w
    
    # Max stretch is 2.0mm (0.0020m) and max necking is 2mm (0.002m)
    max_stretch = 0.0020
    max_necking = 0.002
    necking_ratio = max_necking / size_x
    if necking_ratio > 0.5:
        necking_ratio = 0.3
        
    for w in range(w_dim):
        # Determine displacement and necking factors for each layer
        if w == 0 or w == 1:
            z_factor = 0.0
            neck_factor = 1.0  # Rigid bottom
        elif w == 3 or w == 4:
            z_factor = 1.0
            neck_factor = 1.0  # Rigid top
        else: # w == 2
            z_factor = 0.5
            neck_factor = 1.0 - necking_ratio  # Maximum necking at center
            
        for v in range(v_dim):
            for u in range(u_dim):
                idx = u + v * u_dim + w * u_dim * v_dim
                orig_co = basis.data[idx].co
                
                # Apply X/Y necking
                necking_key.data[idx].co.x = orig_co.x * neck_factor
                necking_key.data[idx].co.y = orig_co.y * neck_factor
                
                # Apply Z stretching (local Z offset = world Z offset / lattice scale Z)
                local_z_disp = (max_stretch * z_factor) / lattice_obj.scale.z
                necking_key.data[idx].co.z = orig_co.z + local_z_disp
                
    # Animate Lattice shape key (perfectly proportional to clamp displacement)
    # Max stretch is 2.00mm. Shape key value is 1.0 at 2.00mm.
    # So value = displacement / 2.00mm.
    necking_keyframes = {
        1: 0.0,
        10: 0.175,
        20: 0.175,
        30: 0.35,
        40: 0.35,
        50: 0.525,
        60: 0.525,
        70: 0.70,
        80: 0.70,
        90: 0.90,
        100: 0.90,
        110: 1.0,
        120: 1.0
    }
    
    for frame, val in necking_keyframes.items():
        necking_key.value = val
        necking_key.keyframe_insert(data_path="value", frame=frame)
        
    # Set shape key F-curve interpolation to LINEAR
    if necking_key.id_data.animation_data and necking_key.id_data.animation_data.action:
        for fcurve in necking_key.id_data.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'
    
    # Add Lattice modifier (applies to whole bone for smooth normal-distributed stretch, no vertex group restriction!)
    lattice_mod = Chicken_Bone.modifiers.new(name="Lattice_Mod", type='LATTICE')
    lattice_mod.object = lattice_obj
    print("Setup Lattice modifier for normal-distributed stretching and necking")
    
    # 7. Animate Clamp_Top Z movement (Axial step-loading)
    # 1-80 frames: 4 elastic stages of exactly 0.35mm stretch each.
    # 80-90 frames: 1 plastic stage (+0.40mm stretch, reaching 1.80mm at frame 90).
    # 100-110 frames: 1 fracture stage (+0.20mm stretch, reaching 2.00mm at frame 110).
    # 110-120 frames: empty stretch of exactly 1.00mm (reaching 3.00mm at frame 120).
    # All values are cleanly rounded.
    clamp_keyframes = {
        1: 0.0,
        10: 0.00035,
        20: 0.00035,
        30: 0.00070,
        40: 0.00070,
        50: 0.00105,
        60: 0.00105,
        70: 0.00140,
        80: 0.00140,
        90: 0.00180,
        100: 0.00180,
        110: 0.00200,
        120: 0.00300
    }
    
    for frame, val in clamp_keyframes.items():
        clamp_top.location.z = clamp_top_loc.z + val
        clamp_top.keyframe_insert(data_path="location", index=2, frame=frame)
        
    # Linear/constant steps interpolation for Clamp_Top
    if clamp_top.animation_data and clamp_top.animation_data.action:
        for fcurve in clamp_top.animation_data.action.fcurves:
            if fcurve.data_path == "location" and fcurve.array_index == 2:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'LINEAR'
                    
    # Keyframe Clamp_Bottom location (stationary)
    clamp_bottom.location = clamp_bottom_loc
    clamp_bottom.keyframe_insert(data_path="location", frame=1)
    clamp_bottom.keyframe_insert(data_path="location", frame=120)
    print("Setup Clamp animation with step-loading profile")

    # 8. Duplicate and Bisect for Fracture
    # Duplicate Bone_Top
    bone_top = Chicken_Bone.copy()
    bone_top.data = Chicken_Bone.data.copy()
    bone_top.name = "Bone_Top"
    bpy.context.collection.objects.link(bone_top)
    
    # Duplicate Bone_Bottom
    bone_bottom = Chicken_Bone.copy()
    bone_bottom.data = Chicken_Bone.data.copy()
    bone_bottom.name = "Bone_Bottom"
    bpy.context.collection.objects.link(bone_bottom)
    
    # Bisect with a 10-degree tilted plane for a natural, organic fracture slope
    # normal = (sin(10 deg), 0, cos(10 deg))
    tilted_normal = (math.sin(math.radians(10)), 0.0, math.cos(math.radians(10)))
    
    # Bisect Bone_Top
    select_only(bone_top)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(center_x, center_y, center_z),
        plane_no=tilted_normal,
        clear_inner=True,
        clear_outer=False,
        use_fill=True
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    selected_verts_top = [v.index for v in bone_top.data.vertices if abs(v.co.z - center_z) < 0.005]  # Adjusted for Z-range
    vg_top_fracture = bone_top.vertex_groups.new(name="Group_Fracture_Top")
    if selected_verts_top:
        vg_top_fracture.add(selected_verts_top, 1.0, 'ADD')
        
    # Bisect Bone_Bottom
    select_only(bone_bottom)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(center_x, center_y, center_z),
        plane_no=tilted_normal,
        clear_inner=False,
        clear_outer=True,
        use_fill=True
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    selected_verts_bottom = [v.index for v in bone_bottom.data.vertices if abs(v.co.z - center_z) < 0.005]
    vg_bottom_fracture = bone_bottom.vertex_groups.new(name="Group_Fracture_Bottom")
    if selected_verts_bottom:
        vg_bottom_fracture.add(selected_verts_bottom, 1.0, 'ADD')
        
    print("Completed Bisecting for Bone_Top and Bone_Bottom with tilted cut")
    
    # 8b. Create and animate shape keys on Bone_Top and Bone_Bottom for left-to-right crack propagation
    print("Creating shape keys on Bone_Top and Bone_Bottom for crack propagation...")
    tan_10 = math.tan(math.radians(10))
    z_cut_right = center_z - (x_max - center_x) * tan_10
    pivot_pt = mathutils.Vector((x_max, center_y, z_cut_right))
    
    # Add shape keys to Bone_Top
    basis_top = bone_top.shape_key_add(name="Basis", from_mix=False)
    crack_keys_top = {}
    
    # Add shape keys to Bone_Bottom
    basis_bottom = bone_bottom.shape_key_add(name="Basis", from_mix=False)
    crack_keys_bottom = {}
    
    # Displacement magnitude for roughness (noise) - reduced to 0.16mm for realistic scale
    disp_magnitude = z_height * 0.002
    
    for f in range(100, 111):
        t = (f - 100) / 10.0
        angle_deg = 1.5 * (t ** 2)  # Max angle is 1.5 degrees
        angle_rad = math.radians(angle_deg)
        p = t ** 2  # crack progress from 0.0 (left) to 1.0 (right)
        
        # Create shape keys
        key_top = bone_top.shape_key_add(name=f"Crack_{f}", from_mix=False)
        crack_keys_top[f] = key_top
        
        key_bottom = bone_bottom.shape_key_add(name=f"Crack_{f}", from_mix=False)
        crack_keys_bottom[f] = key_bottom
        
        # Bone_Top vertices
        for v in bone_top.data.vertices:
            P = v.co
            x_norm = (P.x - x_min) / (x_max - x_min)
            
            # Crack weight - sharp transition to prevent tape-like stretching/holes
            delta = 0.01
            if x_norm > p + delta:
                w_crack = 1.0
            elif x_norm < p - delta:
                w_crack = 0.0
            else:
                w_crack = (x_norm - (p - delta)) / (2.0 * delta)
                
            # Z-fade factor (only for vertices near the cut)
            z_fade = 1.0 - (P.z - center_z) / (0.3 * z_height)
            if z_fade < 0.0:
                z_fade = 0.0
            elif z_fade > 1.0:
                z_fade = 1.0
            w_total = w_crack * z_fade
            
            # Roughness displacement
            z_on_plane = center_z - (P.x - center_x) * tan_10
            dist_to_plane = abs(P.z - z_on_plane)
            roughness_fade = 1.0 - dist_to_plane / 0.005
            if roughness_fade < 0.0:
                roughness_fade = 0.0
                
            # Evaluate noise at baseline position P
            noise_val = mathutils.noise.noise(P * 500.0)
            disp_z = disp_magnitude * noise_val * roughness_fade
            
            # Open position: rotate around pivot_pt by angle_rad around Y-axis
            P_local = P - pivot_pt
            cos_th = math.cos(angle_rad)
            sin_th = math.sin(angle_rad)
            rx = P_local.x * cos_th + P_local.z * sin_th
            ry = P_local.y
            rz = -P_local.x * sin_th + P_local.z * cos_th
            P_open = pivot_pt + mathutils.Vector((rx, ry, rz))
            
            # Add roughness displacement (upwards for top bone)
            P_open_rough = P_open + mathutils.Vector((0.0, 0.0, disp_z))
            
            # Final position
            P_final = w_total * P + (1.0 - w_total) * P_open_rough
            key_top.data[v.index].co = P_final
            
        # Bone_Bottom vertices
        for v in bone_bottom.data.vertices:
            P = v.co
            x_norm = (P.x - x_min) / (x_max - x_min)
            
            # Crack weight - sharp transition to prevent tape-like stretching/holes
            delta = 0.01
            if x_norm > p + delta:
                w_crack = 1.0
            elif x_norm < p - delta:
                w_crack = 0.0
            else:
                w_crack = (x_norm - (p - delta)) / (2.0 * delta)
                
            # Z-fade factor (only for vertices near the cut)
            z_fade = 1.0 - (center_z - P.z) / (0.3 * z_height)
            if z_fade < 0.0:
                z_fade = 0.0
            elif z_fade > 1.0:
                z_fade = 1.0
            w_total = w_crack * z_fade
            
            # Roughness displacement
            z_on_plane = center_z - (P.x - center_x) * tan_10
            dist_to_plane = abs(P.z - z_on_plane)
            roughness_fade = 1.0 - dist_to_plane / 0.005
            if roughness_fade < 0.0:
                roughness_fade = 0.0
                
            noise_val = mathutils.noise.noise(P * 500.0)
            disp_z = disp_magnitude * noise_val * roughness_fade
            
            # Open position: add roughness displacement (downwards for bottom bone)
            P_open_rough = P - mathutils.Vector((0.0, 0.0, disp_z))
            
            # Final position
            P_final = w_total * P + (1.0 - w_total) * P_open_rough
            key_bottom.data[v.index].co = P_final
            
    # Keyframe shape keys value over time for both halves
    for crack_keys_dict in [crack_keys_top, crack_keys_bottom]:
        for f_key, key in crack_keys_dict.items():
            # Set value to 0 at frame 1
            key.value = 0.0
            key.keyframe_insert(data_path="value", frame=1)
            
            # Set value to 0 at frame f_key - 1 (if f_key > 100)
            if f_key > 100:
                key.value = 0.0
                key.keyframe_insert(data_path="value", frame=f_key - 1)
                
            # Set value to 1 at frame f_key
            key.value = 1.0
            key.keyframe_insert(data_path="value", frame=f_key)
            
            # Set value to 0 at frame f_key + 1 (if f_key < 110)
            if f_key < 110:
                key.value = 0.0
                key.keyframe_insert(data_path="value", frame=f_key + 1)
                
            # Set value to 0 at frame 120
            key.value = 0.0
            key.keyframe_insert(data_path="value", frame=120)
        
    # Set shape key F-curves to LINEAR
    for obj in [bone_top, bone_bottom]:
        if obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action:
            for fcurve in obj.data.shape_keys.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'LINEAR'
                
    # Keep Lattice modifier strength constant at 1.0 (no rubbery shape recovery/rebound)
    for obj in [bone_top, bone_bottom]:
        lat_mod = obj.modifiers.get("Lattice_Mod")
        if lat_mod:
            lat_mod.strength = 1.0
            lat_mod.keyframe_insert(data_path="strength", frame=1)
            lat_mod.keyframe_insert(data_path="strength", frame=120)
            
    print("Applied shape key displacement and separation to fracture faces")
    
    # 9. Animate Fracture Separation & Rotation (Tilt)
    # Timeline:
    # 1-110 (110 frames): bone_top is stationary in object space (tilt is handled by shape keys)
    bone_top.rotation_mode = 'XYZ'
    
    bone_top.location = (0.0, 0.0, 0.0)
    bone_top.keyframe_insert(data_path="location", frame=1)
    bone_top.keyframe_insert(data_path="location", frame=100)
    bone_top.keyframe_insert(data_path="location", frame=110)
    
    bone_top.rotation_euler = (0.0, 0.0, 0.0)
    bone_top.keyframe_insert(data_path="rotation_euler", frame=1)
    bone_top.keyframe_insert(data_path="rotation_euler", frame=100)
    bone_top.keyframe_insert(data_path="rotation_euler", frame=110)
    
    # 110-120 (10 frames): empty stretch of 1mm, snaps open and separates, tilt recovers.
    # We define the post-fracture states at keyframes 111, 113, 120
    # Keep tilt constant at 1.5 degrees to eliminate rotation snapback
    post_fracture_states = {
        111: {"angle_deg": 1.5, "z_sep": 0.00005},
        113: {"angle_deg": 1.5, "z_sep": 0.0007},
        120: {"angle_deg": 1.5, "z_sep": 0.0010}
    }
    
    for f, state in post_fracture_states.items():
        theta = math.radians(state["angle_deg"])
        z_sep = state["z_sep"]
        
        # Calculate object-level translation and rotation to rotate around pivot_pt
        cos_th = math.cos(theta)
        sin_th = math.sin(theta)
        
        T_x = pivot_pt.x - (pivot_pt.x * cos_th + pivot_pt.z * sin_th)
        T_y = 0.0
        T_z = pivot_pt.z - (-pivot_pt.x * sin_th + pivot_pt.z * cos_th) + z_sep
        
        bone_top.location = (T_x, T_y, T_z)
        bone_top.rotation_euler.y = theta
        
        bone_top.keyframe_insert(data_path="location", frame=f)
        bone_top.keyframe_insert(data_path="rotation_euler", frame=f)
        
    # Bone_Bottom Location Z (Nearly stationary, fixed bottom clamp)
    bone_bottom.location.z = 0.0
    bone_bottom.keyframe_insert(data_path="location", index=2, frame=1)
    bone_bottom.keyframe_insert(data_path="location", index=2, frame=100)
    bone_bottom.location.z = -0.0001
    bone_bottom.keyframe_insert(data_path="location", index=2, frame=110)
    bone_bottom.location.z = -0.0002
    bone_bottom.keyframe_insert(data_path="location", index=2, frame=120)
    
    # Make all these F-curves LINEAR for precise velocity transitions
    for obj in [bone_top, bone_bottom]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'LINEAR'
                    
    print("Setup multi-stage fracture separation and tilt animation")
    
    # 10. Visibility Animation (swap at frame 100)
    def animate_visibility(obj, start_visible, hide_frame):
        if start_visible:
            # Visible from 1 to hide_frame
            obj.hide_viewport = False
            obj.keyframe_insert(data_path="hide_viewport", frame=1)
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame)
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_render", frame=1)
            obj.keyframe_insert(data_path="hide_render", frame=hide_frame)
            
            # Hidden from hide_frame + 1 onwards
            obj.hide_viewport = True
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame + 1)
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_render", frame=hide_frame + 1)
        else:
            # Hidden from 1 to hide_frame
            obj.hide_viewport = True
            obj.keyframe_insert(data_path="hide_viewport", frame=1)
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame)
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_render", frame=1)
            obj.keyframe_insert(data_path="hide_render", frame=hide_frame)
            
            # Visible from hide_frame + 1 onwards
            obj.hide_viewport = False
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame + 1)
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_render", frame=hide_frame + 1)
            
    animate_visibility(Chicken_Bone, start_visible=True, hide_frame=100)
    animate_visibility(bone_top, start_visible=False, hide_frame=100)
    animate_visibility(bone_bottom, start_visible=False, hide_frame=100)
    print("Animate visibility for fracture transition")
    
    # 11. Create and Assign DIC Speckle Material
    def setup_material(mat_name, texture_path):
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (400, 0)
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (600, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.location = (200, 0)
        try:
            img = bpy.data.images.load(texture_path)
            tex_node.image = img
            print(f"Loaded speckle image: {texture_path}")
        except Exception as e:
            print(f"Error loading texture: {e}")
            
        mapping_node = nodes.new(type='ShaderNodeMapping')
        mapping_node.location = (0, 0)
        # Scale by 1.3333 to make the speckle particles 50% larger than 1/2 size state (2.0 / 1.5 = 1.3333)
        mapping_node.inputs['Scale'].default_value = (1.3333, 1.3333, 1.3333)
        
        coord_node = nodes.new(type='ShaderNodeTexCoord')
        coord_node.location = (-200, 0)
        
        links.new(coord_node.outputs['UV'], mapping_node.inputs['Vector'])
        links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        
        bsdf.inputs['Roughness'].default_value = 0.8
        return mat
        
    tex_path = r"E:\Antigravity\Chicken Bone\speckle.jpg"
    mat = setup_material("DIC_Material", tex_path)
    
    for obj in [Chicken_Bone, bone_top, bone_bottom]:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        
    print("Setup and applied DIC Material to bone models")
        
    # 12. Setup Camera, Camera_R, Background Plane, and Lights
    # Original Camera setup
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    
    # Position Camera exactly at (0, -0.2, 0) pointing straight along +Y (towards origin)
    camera.location = (0.0, -0.2, 0.0)
    camera.rotation_euler = (math.radians(90), 0.0, 0.0)
    camera_data.lens = 50.0
    camera_data.clip_start = 0.005
    camera_data.clip_end = 2.0
    
    bpy.context.scene.camera = camera
    
    # Camera_R Setup at (0.1, -0.2, 0) with a 14-degree angle relative to Camera
    camera_r_data = bpy.data.cameras.new("Camera_R")
    camera_r = bpy.data.objects.new("Camera_R", camera_r_data)
    bpy.context.collection.objects.link(camera_r)
    
    # Copy intrinsics from original camera
    camera_r_data.type = camera_data.type
    camera_r_data.lens = camera_data.lens
    camera_r_data.sensor_width = camera_data.sensor_width
    camera_r_data.clip_start = camera_data.clip_start
    camera_r_data.clip_end = camera_data.clip_end
    camera_r_data.ortho_scale = camera_data.ortho_scale
    
    # Position Camera_R at exactly (0.1, -0.2, 0) and rotate 14 degrees inwards around Z
    camera_r.location = (0.1, -0.2, 0.0)
    camera_r.rotation_euler = (math.radians(90), 0.0, math.radians(14))
    
    print(f"Set up Camera at {camera.location} (rot={camera.rotation_euler}) and Camera_R at {camera_r.location} (rot={camera_r.rotation_euler})")
    
    # Setup Background Plane with bg.jpg
    print("Setting up background plane with bg.jpg...")
    # Place it behind the bone (0.16m in Y direction), sized 0.6m (large enough to fill view)
    bpy.ops.mesh.primitive_plane_add(size=0.6, location=(0.0, 0.16, 0.0))
    bg_plane = bpy.context.active_object
    bg_plane.name = "Background_Plane"
    # Rotate to stand vertically
    bg_plane.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    
    bg_mat = bpy.data.materials.new(name="BG_Material")
    bg_mat.use_nodes = True
    bg_nodes = bg_mat.node_tree.nodes
    bg_links = bg_mat.node_tree.links
    bg_nodes.clear()
    
    bg_bsdf = bg_nodes.new(type='ShaderNodeBsdfPrincipled')
    bg_bsdf.location = (400, 0)
    bg_bsdf.inputs['Roughness'].default_value = 0.9
    # In Blender 4.5, specular input is called 'Specular IOR Level'
    bg_bsdf.inputs['Specular IOR Level'].default_value = 0.1
    
    bg_output = bg_nodes.new(type='ShaderNodeOutputMaterial')
    bg_output.location = (600, 0)
    bg_links.new(bg_bsdf.outputs['BSDF'], bg_output.inputs['Surface'])
    
    bg_tex = bg_nodes.new(type='ShaderNodeTexImage')
    bg_tex.location = (100, 0)
    bg_img_path = r"E:\Antigravity\Chicken Bone\bg.jpg"
    try:
        bg_img = bpy.data.images.load(bg_img_path)
        bg_tex.image = bg_img
        print(f"Loaded background image: {bg_img_path}")
    except Exception as e:
        print(f"Error loading background image: {e}")
        
    bg_coord = bg_nodes.new(type='ShaderNodeTexCoord')
    bg_coord.location = (-100, 0)
    bg_links.new(bg_coord.outputs['Generated'], bg_tex.inputs['Vector'])
    bg_links.new(bg_tex.outputs['Color'], bg_bsdf.inputs['Base Color'])
    
    bg_plane.data.materials.clear()
    bg_plane.data.materials.append(bg_mat)
    
    sun_data = bpy.data.lights.new(name="Sun_Key", type='SUN')
    sun_data.energy = 3.0
    sun_obj = bpy.data.objects.new("Sun_Key", sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (center_x - z_height, center_y - z_height, center_z + z_height)
    sun_obj.rotation_euler = (math.radians(45), 0, math.radians(-45))
    
    fill_data = bpy.data.lights.new(name="Sun_Fill", type='SUN')
    fill_data.energy = 1.0
    fill_obj = bpy.data.objects.new("Sun_Fill", fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (center_x + z_height, center_y - z_height, center_z - z_height)
    fill_obj.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120
    bpy.context.scene.frame_current = 1
    
    # Save the file
    blend_path = r"E:\Antigravity\Chicken Bone\chicken_bone.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved project file to: {blend_path}")

if __name__ == "__main__":
    main()
