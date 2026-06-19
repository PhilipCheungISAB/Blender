import bpy
import bmesh
import math
import random

def setup_physics_world():
    scene = bpy.context.scene
    scene.render.frame_map_old = 1
    scene.render.frame_map_new = 1
    scene.frame_start = 1
    scene.frame_end = 250
    scene.frame_current = 1
    
    if not scene.rigidbody_world:
        bpy.ops.rigidbody.world_add()
    
    rbw = scene.rigidbody_world
    rbw.enabled = True
    rbw.time_scale = 1.0 
    rbw.substeps_per_frame = 50  
    rbw.solver_iterations = 60   

def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        if col.name != "Collection":
            bpy.data.collections.remove(col)

def create_brick_material():
    mat = bpy.data.materials.new(name="RedBrick")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Base Color'].default_value = (0.55, 0.22, 0.15, 1.0)
    node_bsdf.inputs['Roughness'].default_value = 0.9
    node_output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
    return mat

def create_concrete_material():
    mat = bpy.data.materials.new(name="Concrete")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Base Color'].default_value = (0.45, 0.45, 0.48, 1.0)
    node_bsdf.inputs['Roughness'].default_value = 0.8
    node_output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
    return mat

def create_unified_frame(name, concrete_mat):
    cubes = []
    # Columns
    cols = [(-2.4, -2.4), (2.4, -2.4), (2.4, 2.4), (-2.4, 2.4)]
    for x, y in cols:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, 1.25))
        obj = bpy.context.object
        obj.scale = (0.2, 0.2, 2.5)
        cubes.append(obj)
    
    # X Beams
    for y in [-2.4, 2.4]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, y, 2.6))
        obj = bpy.context.object
        obj.scale = (5.0, 0.2, 0.2)
        cubes.append(obj)
        
    # Y Beams
    for x in [-2.4, 2.4]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 2.6))
        obj = bpy.context.object
        obj.scale = (0.2, 4.6, 0.2)
        cubes.append(obj)
        
    # Apply scale on individual cubes first to normalize local mesh vertices
    for obj in cubes:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
    # Join them
    bpy.ops.object.select_all(action='DESELECT')
    for obj in cubes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = cubes[0]
    bpy.ops.object.join()
    
    frame = bpy.context.view_layer.objects.active
    frame.name = name
    if len(frame.data.materials) == 0:
        frame.data.materials.append(concrete_mat)
    else:
        frame.data.materials[0] = concrete_mat
        
    # Apply all transforms on the joined frame so origin is at (0, 0, 0) and scale is (1, 1, 1)
    bpy.ops.object.select_all(action='DESELECT')
    frame.select_set(True)
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    # Subdivide mesh
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Shape Keys
    sk_basis = frame.shape_key_add(name="Basis")
    sk_sway_x = frame.shape_key_add(name="Sway_X")
    sk_sway_y = frame.shape_key_add(name="Sway_Y")
    
    # Allow positive and negative sway without clamping
    sk_sway_x.slider_min = -2.0
    sk_sway_x.slider_max = 2.0
    sk_sway_y.slider_min = -2.0
    sk_sway_y.slider_max = 2.0
    
    # Calculate deformation using absolute height Z with physical S-curve (Hermite Smoothstep)
    for i, vert in enumerate(frame.data.vertices):
        x, y, z = vert.co.x, vert.co.y, vert.co.z
        if z > 0:
            u = z / 2.7
            factor = 3 * u**2 - 2 * u**3  # S-curve
            sk_sway_x.data[i].co.x += 0.5 * factor 
            sk_sway_y.data[i].co.y += 0.5 * factor
    
    # Rigid Body Settings
    bpy.ops.rigidbody.object_add()
    frame.rigid_body.type = 'PASSIVE'
    frame.rigid_body.kinematic = True 
    frame.rigid_body.collision_shape = 'MESH'
    frame.rigid_body.mesh_source = 'DEFORM'
    frame.rigid_body.use_deform = True  
    frame.rigid_body.friction = 1.0
    
    # Set margin to 0.001 to prevent initial explosions
    frame.rigid_body.use_margin = True
    frame.rigid_body.collision_margin = 0.001
    
    # Set to collision group 2 to avoid physical collision conflicts with bricks (group 1)
    frame.rigid_body.collision_collections[0] = False
    frame.rigid_body.collision_collections[1] = True
    
    return frame

def create_brick(name, size, location, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.location = location
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material
        
    bev = obj.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.003
    bev.segments = 2
        
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.mass = 2.0
    obj.rigid_body.friction = 1.0
    obj.rigid_body.restitution = 0.0
    obj.rigid_body.linear_damping = 0.98  # Reverted back to 0.98 for maximum stability and smooth cohesive settling
    obj.rigid_body.angular_damping = 0.98
    
    # Margin to 0.001 to prevent initial explosions
    obj.rigid_body.use_margin = True
    obj.rigid_body.collision_margin = 0.001
    
    return obj

def build_x_wall(y_coord, x_start, x_end, material, name_prefix):
    D = x_end - x_start
    W = 0.2
    g = 0.002
    N = 11
    L = (D - (N - 1) * g) / N
    num_layers = 24
    H = (2.5 - (num_layers - 1) * g) / num_layers
    L_half = (L - g) / 2.0
    dx = 0.0
    
    wall_bricks = []
    for j in range(num_layers):
        layer_bricks = []
        z = j * (H + g) + H/2 + g
        dist_z = abs(z - 1.25)
        
        if j % 2 == 0:
            for i in range(N):
                x = x_start + dx + L/2 + i * (L + g)
                dist_x = abs(x - (x_start + x_end)/2)
                # CRITICAL: 2.0cm initial bow (positive Y for front wall to bulge INWARD)
                bow_y = 0.02 * math.cos(dist_x / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
                brick = create_brick(f"{name_prefix}_L{j}_B{i}", (L, W, H), (x, y_coord + bow_y, z), material)
                layer_bricks.append((brick, 'full', x))
        else:
            x_lhalf = x_start + dx + L_half/2
            dist_x = abs(x_lhalf - (x_start + x_end)/2)
            bow_y = 0.02 * math.cos(dist_x / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
            brick_l = create_brick(f"{name_prefix}_L{j}_B_LHalf", (L_half, W, H), (x_lhalf, y_coord + bow_y, z), material)
            layer_bricks.append((brick_l, 'half', x_lhalf))
            
            for i in range(N - 1):
                x = x_start + dx + L_half + g + L/2 + i * (L + g)
                dist_x = abs(x - (x_start + x_end)/2)
                bow_y = 0.02 * math.cos(dist_x / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
                brick = create_brick(f"{name_prefix}_L{j}_B{i}", (L, W, H), (x, y_coord + bow_y, z), material)
                layer_bricks.append((brick, 'full', x))
                
            x_rhalf = x_start + dx + L_half + g + (N - 1) * (L + g) + L_half/2
            dist_x = abs(x_rhalf - (x_start + x_end)/2)
            bow_y = 0.02 * math.cos(dist_x / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
            brick_r = create_brick(f"{name_prefix}_L{j}_B_RHalf", (L_half, W, H), (x_rhalf, y_coord + bow_y, z), material)
            layer_bricks.append((brick_r, 'half', x_rhalf))
            
        wall_bricks.append(layer_bricks)
    return wall_bricks

def build_y_wall(x_coord, y_start, y_end, material, name_prefix):
    D = y_end - y_start
    W = 0.2
    g = 0.002
    N = 11
    L = (D - (N - 1) * g) / N
    num_layers = 24
    H = (2.5 - (num_layers - 1) * g) / num_layers
    L_half = (L - g) / 2.0
    dy = 0.0
    
    wall_bricks = []
    for j in range(num_layers):
        layer_bricks = []
        z = j * (H + g) + H/2 + g
        dist_z = abs(z - 1.25)
        
        if j % 2 == 0:
            for i in range(N):
                y = y_start + dy + L/2 + i * (L + g)
                dist_y = abs(y - (y_start + y_end)/2)
                # CRITICAL: 2.0cm initial bow (negative X for right wall to bulge INWARD)
                bow_x = -0.02 * math.cos(dist_y / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
                brick = create_brick(f"{name_prefix}_L{j}_B{i}", (W, L, H), (x_coord + bow_x, y, z), material)
                layer_bricks.append((brick, 'full', y))
        else:
            y_lhalf = y_start + dy + L_half/2
            dist_y = abs(y_lhalf - (y_start + y_end)/2)
            bow_x = -0.02 * math.cos(dist_y / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
            brick_l = create_brick(f"{name_prefix}_L{j}_B_LHalf", (W, L_half, H), (x_coord + bow_x, y_lhalf, z), material)
            layer_bricks.append((brick_l, 'half', y_lhalf))
            
            for i in range(N - 1):
                y = y_start + dy + L_half + g + L/2 + i * (L + g)
                dist_y = abs(y - (y_start + y_end)/2)
                bow_x = -0.02 * math.cos(dist_y / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
                brick = create_brick(f"{name_prefix}_L{j}_B{i}", (W, L, H), (x_coord + bow_x, y, z), material)
                layer_bricks.append((brick, 'full', y))
                
            y_rhalf = y_start + dy + L_half + g + (N - 1) * (L + g) + L_half/2
            dist_y = abs(y_rhalf - (y_start + y_end)/2)
            bow_x = -0.02 * math.cos(dist_y / 2.3 * math.pi/2) * math.cos(dist_z / 1.25 * math.pi/2)
            brick_r = create_brick(f"{name_prefix}_L{j}_B_RHalf", (W, L_half, H), (x_coord + bow_x, y_rhalf, z), material)
            layer_bricks.append((brick_r, 'half', y_rhalf))
            
        wall_bricks.append(layer_bricks)
    return wall_bricks

def create_constraint(obj1, obj2, location, threshold, collection, unbreakable=False):
    empty = bpy.data.objects.new(f"Con_{obj1.name}_{obj2.name}", None)
    collection.objects.link(empty)
    empty.location = location
    
    bpy.context.view_layer.objects.active = empty
    bpy.ops.rigidbody.constraint_add()
    
    con = empty.rigid_body_constraint
    con.type = 'FIXED'
    con.object1 = obj1
    con.object2 = obj2
    
    # Allow collisions between constrained bricks to prevent penetration (穿模)!
    con.disable_collisions = False
    
    if unbreakable:
        con.use_breaking = False
    else:
        con.use_breaking = True
        con.breaking_threshold = threshold
        
    empty.empty_display_size = 0.01
    empty.hide_viewport = True
    empty.hide_render = True
    return empty

def create_generic_constraint(obj1, obj2, location, collection, unbreakable=False, threshold=200.0, limit_z_lower=-0.15):
    empty = bpy.data.objects.new(f"Con_{obj1.name}_{obj2.name}", None)
    collection.objects.link(empty)
    empty.location = location
    
    bpy.context.view_layer.objects.active = empty
    bpy.ops.rigidbody.constraint_add()
    
    con = empty.rigid_body_constraint
    con.type = 'GENERIC'
    con.object1 = obj2  # CRITICAL FIX: Swap object1 and object2 so anchor is object1 and brick is object2
    con.object2 = obj1  # This ensures the limits correctly constrain the brick relative to the anchor!
    con.disable_collisions = False
    
    if unbreakable:
        con.use_breaking = False
    else:
        con.use_breaking = True
        con.breaking_threshold = threshold
        
    # Lock X and Y translations
    con.use_limit_lin_x = True
    con.limit_lin_x_lower = 0.0
    con.limit_lin_x_upper = 0.0
    
    con.use_limit_lin_y = True
    con.limit_lin_y_lower = 0.0
    con.limit_lin_y_upper = 0.0
    
    # Allow Z translation (vertical slide)
    con.use_limit_lin_z = True
    con.limit_lin_z_lower = limit_z_lower
    con.limit_lin_z_upper = 0.0
    
    # Lock all rotations
    con.use_limit_ang_x = True
    con.limit_ang_x_lower = 0.0
    con.limit_ang_x_upper = 0.0
    
    con.use_limit_ang_y = True
    con.limit_ang_y_lower = 0.0
    con.limit_ang_y_upper = 0.0
    
    con.use_limit_ang_z = True
    con.limit_ang_z_lower = 0.0
    con.limit_ang_z_upper = 0.0
    
    empty.empty_display_size = 0.01
    empty.hide_viewport = True
    empty.hide_render = True
    return empty

def create_brick_generic_constraint(obj1, obj2, location, collection, limit_xyz=0.01, limit_ang=math.radians(1.5)):
    empty = bpy.data.objects.new(f"Con_{obj1.name}_{obj2.name}", None)
    collection.objects.link(empty)
    empty.location = location
    
    bpy.context.view_layer.objects.active = empty
    bpy.ops.rigidbody.constraint_add()
    
    con = empty.rigid_body_constraint
    con.type = 'GENERIC'
    con.object1 = obj1
    con.object2 = obj2
    con.disable_collisions = False
    con.use_breaking = False  # Unbreakable!
    
    # Linear limits (allow 1.0cm play)
    con.use_limit_lin_x = True
    con.limit_lin_x_lower = -limit_xyz
    con.limit_lin_x_upper = limit_xyz
    
    con.use_limit_lin_y = True
    con.limit_lin_y_lower = -limit_xyz
    con.limit_lin_y_upper = limit_xyz
    
    con.use_limit_lin_z = True
    con.limit_lin_z_lower = -limit_xyz
    con.limit_lin_z_upper = limit_xyz
    
    # Angular limits (allow 1.5 degrees play)
    con.use_limit_ang_x = True
    con.limit_ang_x_lower = -limit_ang
    con.limit_ang_x_upper = limit_ang
    
    con.use_limit_ang_y = True
    con.limit_ang_y_lower = -limit_ang
    con.limit_ang_y_upper = limit_ang
    
    con.use_limit_ang_z = True
    con.limit_ang_z_lower = -limit_ang
    con.limit_ang_z_upper = limit_ang
    
    empty.empty_display_size = 0.01
    empty.hide_viewport = True
    empty.hide_render = True
    return empty

def create_physics_anchor(name, location, anchors_group):
    # Tiny mesh cube to act as active/passive physics mediator
    bpy.ops.mesh.primitive_cube_add(size=0.01, location=location)
    obj = bpy.context.object
    obj.name = name
    
    # Move object to constraints group/collection
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    anchors_group.objects.link(obj)
    
    # Hide from viewport/render
    obj.hide_render = True
    obj.display_type = 'WIRE'
    
    # Passive kinematic rigid body
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'PASSIVE'
    obj.rigid_body.kinematic = True
    obj.rigid_body.use_margin = True
    obj.rigid_body.collision_margin = 0.001
    
    # Set to collision group 2 to avoid collision conflicts with bricks (group 1)
    obj.rigid_body.collision_collections[0] = False
    obj.rigid_body.collision_collections[1] = True
    
    return obj

def add_constraints_wall(wall_bricks, fixed_axis, fixed_coord, frame, foundation, is_x_wall=True):
    g = 0.002
    L = (4.6 - 10 * g) / 11.0
    H = (2.5 - 23 * g) / 24.0
    
    constraints_group = bpy.data.collections.new(f"Constraints_{fixed_axis}_{fixed_coord}")
    bpy.context.scene.collection.children.link(constraints_group)
    
    # Brick constraints set to 45.0 to ensure a cohesive, unified wall panel (plastic-like behavior)
    threshold_brick = 45.0  
    threshold_frame = 200.0
    threshold_foundation = 200.0
            
    # Horizontal constraints (using generic limits for cohesive deformation)
    for j, layer in enumerate(wall_bricks):
        z = j * (H + g) + H/2 + g
        for i in range(len(layer) - 1):
            b1, type1, pos1 = layer[i]
            b2, type2, pos2 = layer[i+1]
            if abs(pos2 - pos1) < (L + g) * 1.1:
                loc = ((b1.location.x + b2.location.x)/2, (b1.location.y + b2.location.y)/2, z)
                create_brick_generic_constraint(b1, b2, loc, constraints_group)
                
    # Vertical constraints (using generic limits for cohesive deformation)
    for j in range(len(wall_bricks) - 1):
        layer1 = wall_bricks[j]
        layer2 = wall_bricks[j+1]
        z = (j + 0.5) * (H + g) + H/2 + g
        for b1, t1, pos1 in layer1:
            w1 = L if t1 == 'full' else (L - g)/2
            for b2, t2, pos2 in layer2:
                w2 = L if t2 == 'full' else (L - g)/2
                if max(pos1 - w1/2, pos2 - w2/2) < min(pos1 + w1/2, pos2 + w2/2):
                    loc = ((b1.location.x + b2.location.x)/2, (b1.location.y + b2.location.y)/2, z)
                    create_brick_generic_constraint(b1, b2, loc, constraints_group)
                    
    anchors_to_animate = []

    # Anchor to foundation (UNBREAKABLE to prevent bottom row from sliding off foundation)
    for b, t, pos in wall_bricks[0]:
        z = H/2 + g
        loc = (b.location.x if is_x_wall else fixed_coord, b.location.y if not is_x_wall else fixed_coord, g/2)
        create_constraint(b, foundation, loc, threshold_foundation, constraints_group, unbreakable=True)
        
    # Anchor to frame (top beam) - GENERIC sliding constraint (limit 2cm slide)
    for idx_b, (b, t, pos) in enumerate(wall_bricks[-1]):
        if idx_b == 0 or idx_b == len(wall_bricks[-1]) - 1:
            continue
        z = (len(wall_bricks)-1) * (H + g) + H/2 + g
        loc = (b.location.x if is_x_wall else fixed_coord, b.location.y if not is_x_wall else fixed_coord, z + H/2 + g/2)
        anchor_obj = create_physics_anchor(f"Anchor_Top_{b.name}", loc, constraints_group)
        create_generic_constraint(b, anchor_obj, loc, constraints_group, unbreakable=True, limit_z_lower=-0.02)
        anchors_to_animate.append((anchor_obj, loc[0], loc[1], loc[2]))
        
    # Anchor to frame (side columns) - GENERIC sliding constraint (limit 2cm slide)
    for j, layer in enumerate(wall_bricks):
        z = j * (H + g) + H/2 + g
        b_l, t_l, pos_l = layer[0]
        loc_l = (b_l.location.x - g/2 if is_x_wall else fixed_coord, b_l.location.y if is_x_wall else b_l.location.y - g/2, z)
        anchor_l = create_physics_anchor(f"Anchor_LCol_{b_l.name}", loc_l, constraints_group)
        create_generic_constraint(b_l, anchor_l, loc_l, constraints_group, unbreakable=True, limit_z_lower=-0.02)
        anchors_to_animate.append((anchor_l, loc_l[0], loc_l[1], loc_l[2]))
        
        b_r, t_r, pos_r = layer[-1]
        loc_r = (b_r.location.x + g/2 if is_x_wall else fixed_coord, b_r.location.y if is_x_wall else b_r.location.y + g/2, z)
        anchor_r = create_physics_anchor(f"Anchor_RCol_{b_r.name}", loc_r, constraints_group)
        create_generic_constraint(b_r, anchor_r, loc_r, constraints_group, unbreakable=True, limit_z_lower=-0.02)
        anchors_to_animate.append((anchor_r, loc_r[0], loc_r[1], loc_r[2]))
        
    # Hide the constraints collection
    layer_col = bpy.context.view_layer.layer_collection.children.get(constraints_group.name)
    if layer_col:
        layer_col.exclude = True 

    return anchors_to_animate

def create_camera(name, location, rotation, lens=50.0):
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = lens
    return cam

def get_seismic_sway(frame_num):
    # Generates seismic shake + permanent drift over 250 frames (10 seconds)
    t = (frame_num - 1) / 25.0  # time in seconds
    
    # 0.5 Hz frequency: exactly 5 cycles in 10 seconds (250 frames)
    omega = math.pi
    decay = math.exp(-0.22 * t)  
    
    # 1. Decaying Oscillation (elliptical sway)
    # Max top displacement is ~3.125 cm (identical to V11 to keep sway rigid and controlled)
    shake_x = 0.07 * math.sin(omega * t) * decay
    shake_y = 0.06 * math.sin(omega * t + math.pi/4) * decay
    
    # 2. Plastic Drift (~3 cm top drift)
    if t < 1.0:
        drift_x = 0.0
        drift_y = 0.0
    elif t < 6.0:
        p = (t - 1.0) / 5.0
        smooth = 3 * p**2 - 2 * p**3
        drift_x = 0.06 * smooth  
        drift_y = 0.045 * smooth  
    else:
        drift_x = 0.06
        drift_y = 0.045
        
    val_x = shake_x + drift_x
    val_y = shake_y + drift_y
    
    return val_x, val_y

def main():
    clear_scene()
    setup_physics_world()
    
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    
    brick_mat = create_brick_material()
    concrete_mat = create_concrete_material()
    
    # 1. Foundation
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.1))
    foundation = bpy.context.object
    foundation.name = "Foundation"
    foundation.scale = (6.0, 6.0, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    foundation.data.materials.append(concrete_mat)
    bpy.ops.rigidbody.object_add()
    foundation.rigid_body.type = 'PASSIVE'
    foundation.rigid_body.use_margin = True
    foundation.rigid_body.collision_margin = 0.001
    
    # 2. Unified Frame with Shape Key Swaying
    frame = create_unified_frame("Unified_Frame", concrete_mat)
    
    # 3. Brick Walls (Front and Right with 2.5cm initial inward bow)
    wall_front = build_x_wall(-2.4, -2.3, 2.3, brick_mat, "Wall_Front")
    wall_right = build_y_wall(2.4, -2.3, 2.3, brick_mat, "Wall_Right")
    
    # 4. Connect walls to frame and ground (collecting anchors for animation sync)
    front_anchors = add_constraints_wall(wall_front, 'X', -2.4, frame, foundation, is_x_wall=True)
    right_anchors = add_constraints_wall(wall_right, 'Y', 2.4, frame, foundation, is_x_wall=False)
    
    all_anchors = front_anchors + right_anchors
    
    # 5. Keyframe shape keys, anchors, and gravity Z-component synchronously
    print("Animating frame shape keys, anchors, and gravity...")
    sk_sway_x = frame.data.shape_keys.key_blocks["Sway_X"]
    sk_sway_y = frame.data.shape_keys.key_blocks["Sway_Y"]
    
    scene = bpy.context.scene
    
    for f in range(1, 251):
        vx, vy = get_seismic_sway(f)
        t = (f - 1) / 25.0
        decay = math.exp(-0.22 * t)
        
        # Keyframe frame shape keys
        sk_sway_x.value = vx
        sk_sway_x.keyframe_insert("value", frame=f)
        sk_sway_y.value = vy
        sk_sway_y.keyframe_insert("value", frame=f)
        
        # Keyframe all physics anchors (position & rotation based on Hermite S-Curve)
        for anchor_obj, loc_x, loc_y, loc_z in all_anchors:
            u = loc_z / 2.7
            # S-curve displacement factor: 3*u^2 - 2*u^3
            factor = (3 * u**2 - 2 * u**3) if loc_z > 0 else 0.0
            dx = vx * 0.5 * factor
            dy = vy * 0.5 * factor
            anchor_obj.location.x = loc_x + dx
            anchor_obj.location.y = loc_y + dy
            anchor_obj.location.z = loc_z
            
            # S-curve slope factor: 3.0/2.7 * (u - u^2)
            slope_factor = (3.0 / 2.7 * (u - u**2)) if loc_z > 0 else 0.0
            rot_y = vx * 0.5 * slope_factor
            rot_x = -vy * 0.5 * slope_factor
            anchor_obj.rotation_euler = (rot_x, rot_y, 0.0)
            
            anchor_obj.keyframe_insert("location", frame=f)
            anchor_obj.keyframe_insert("rotation_euler", frame=f)
            
        # Keyframe gravity Z-component to simulate vertical earthquake acceleration (P-waves)
        # Reduced vertical gravity vibration amplitude to 4.0 m/s^2 for cohesive and stable plastic settling
        gvz = -9.81 + 4.0 * math.sin(2.0 * math.pi * 2.2 * t) * decay
        scene.gravity.z = gvz
        scene.keyframe_insert("gravity", frame=f)
            
    # Camera Array
    cam_front_L = create_camera("Cam_Front_L", (-1.5, -9.0, 1.25), (math.radians(90), 0, math.radians(0)))
    cam_front_R = create_camera("Cam_Front_R", (1.5, -9.0, 1.25), (math.radians(90), 0, math.radians(0)))
    
    cam_right_L = create_camera("Cam_Right_L", (9.0, -1.5, 1.25), (math.radians(90), 0, math.radians(90)))
    cam_right_R = create_camera("Cam_Right_R", (9.0, 1.5, 1.25), (math.radians(90), 0, math.radians(90)))
    
    bpy.context.scene.camera = cam_front_L
    
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun_light = bpy.context.object
    sun_light.data.energy = 5.0
    sun_light.rotation_euler = (math.radians(45), math.radians(30), math.radians(45))
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_perspective = 'CAMERA'
                    space.shading.type = 'SOLID'
                    space.shading.show_shadows = True
                    space.overlay.show_relationship_lines = False
    
    # 6. Bake the physics simulation (rigid bodies) for frames 1-250
    print("Baking rigid body simulation...")
    if bpy.context.scene.rigidbody_world and bpy.context.scene.rigidbody_world.point_cache:
        cache = bpy.context.scene.rigidbody_world.point_cache
        cache.frame_start = 1
        cache.frame_end = 250
        try:
            bpy.ops.ptcache.free_bake_all()
            bpy.ops.ptcache.bake_all(bake=True)
            print("Baking completed successfully.")
        except Exception as e:
            print(f"Bake failed or warning occurred: {e}")
                    
    filepath = "e:\\Antigravity\\Building\\anti_seismic_sim_plastic.blend"
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    print(f"Successfully saved to {filepath}")

if __name__ == "__main__":
    main()
