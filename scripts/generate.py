import bpy
import bmesh
import os
import sys
import importlib
import numpy as np

repo_path = "/home/fricke/blender/gis_gen/"
scripts_path = os.path.join(repo_path, "scripts")
if scripts_path not in sys.path:
    sys.path.append(scripts_path)
import material
import models
import utils

spacing = 2.0
raise_offset = 5.0 # Keep things above the X plane

def init():
    print("--- Running init()")
    ghost_collection = bpy.data.collections.new("init_ghost")
    bpy.context.scene.collection.children.link(ghost_collection)
    ghost_collection.hide_viewport = True

    importlib.reload(models)
    tree_files = [
        os.path.join(repo_path, "models", "tree_1.glb"),
        os.path.join(repo_path, "models", "tree_2.glb"),
        # os.path.join(repo_path, "models", "tree_3.glb"),
        # os.path.join(repo_path, "models", "tree_4.glb"),
        os.path.join(repo_path, "models", "tree_5.glb"),
    ]
    models.load_models_to_collection(tree_files, "source_trees")

    world_collection = bpy.data.collections.new("World")
    bpy.context.scene.collection.children.link(world_collection)

def generate():
    # Python runs new each time, so we want an "init" step when first loading
    # We create a "init_ghost" collection as it is a quick hash map lookup
    first_time = "init_ghost" not in bpy.data.collections
    if first_time:
        init()

    importlib.reload(utils)
    color_image_path = os.path.join(repo_path, "images", "color.png")
    depth_image_path = os.path.join(repo_path, "images", "depth.png")
    color_changed = utils.has_file_changed(color_image_path, "last_color")
    depth_changed = utils.has_file_changed(depth_image_path, "last_depth")
    if not color_changed and not depth_changed:
        return

    importlib.reload(material)

    world_collection = bpy.data.collections["World"]

    if first_time:
        color_img = bpy.data.images.load(color_image_path)
        depth_img = bpy.data.images.load(depth_image_path)
        depth_tex = bpy.data.textures.new(name="GroudDepthMap", type='IMAGE')
        depth_tex.image = depth_img

        # For now, assume the high/width never change between calls
        width, height = depth_img.size

        ground_mesh = bpy.data.meshes.new("GroundMesh")
        ground_obj = bpy.data.objects.new("GroundPlane", ground_mesh)

        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=width-1, y_segments=height-1, size=0.5)
        bmesh.ops.translate(bm, vec=(0.5, 0.5, raise_offset), verts=bm.verts)
        bmesh.ops.scale(bm, vec=(width*spacing, height*spacing, 1.0), verts=bm.verts)
        # Need to set the UVs from (0.0,0.0) to (1.0,1.0)
        # So the texture fits as a 1 to 1
        uv_layer = bm.loops.layers.uv.new("GroupUVMap")
        for face in bm.faces:
            for loop in face.loops:
                x_pos = loop.vert.co.x
                y_pos = loop.vert.co.y
                u = (x_pos / (width * spacing))
                v = (y_pos / (height * spacing))
                loop[uv_layer].uv = (u, v)

        bm.to_mesh(ground_mesh)
        bm.free()

        mat_brown = material.create_rocky_terrain_material()
        ground_mesh.materials.append(mat_brown)
        # Need to link before adding modifiers
        world_collection.objects.link(ground_obj)

        displace_mod = ground_obj.modifiers.new(name="Displace", type='DISPLACE')
        # Negative so black is up
        displace_mod.strength = -1.0 * raise_offset * 2.0
        displace_mod.texture = depth_tex
        displace_mod.texture_coords = 'UV'

        # Apply smooth shading
        count = len(ground_obj.data.polygons)
        smooth_values = np.full(count, True)
        ground_obj.data.polygons.foreach_set("use_smooth", smooth_values)

        ps_mod = ground_obj.modifiers.new(name="TreeParticles", type='PARTICLE_SYSTEM')
        ps_set = ps_mod.particle_system.settings
        ps_set.type = 'HAIR'
        ps_set.hair_length = 4.2
        ps_set.use_advanced_hair = True
        ps_set.use_rotations = True
        ps_set.rotation_mode = 'NONE'
        ps_set.render_type = 'COLLECTION'
        ps_set.particle_size = 0.08
        ps_set.size_random = 0.0
        ps_set.instance_collection = bpy.data.collections["source_trees"]
        # Will pick between tree in collection
        ps_set.use_whole_collection = False
        ps_set.use_collection_pick_random = True
        ps_set.use_rotation_instance = True

        pond_mod = ground_obj.modifiers.new(name="PondSink", type='DISPLACE')
        pond_mod.strength = ground_obj.modifiers["Displace"].strength
        pond_mod.direction = 'Z'

        vg_tree = ground_obj.vertex_groups.new(name="TreeMask")
        tree_particles = ground_obj.modifiers["TreeParticles"]
        tree_particles.particle_system.vertex_group_density = "TreeMask"
        vg_water = ground_obj.vertex_groups.new(name="WaterMask")

        pond_mod.vertex_group = "WaterMask"

        water_mesh = bpy.data.meshes.new("WaterPlane")
        water_obj = bpy.data.objects.new("WaterPlane", water_mesh)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=width-1, y_segments=height-1, size=0.5)
        bmesh.ops.translate(bm, vec=(-0.5, -0.5, -1.1), verts=bm.verts)
        bmesh.ops.scale(bm, vec=(width*spacing, height*spacing, 1.0), verts=bm.verts)
        uv_layer = bm.loops.layers.uv.new("GroupUVMap")
        for face in bm.faces:
            for loop in face.loops:
                x_pos = loop.vert.co.x
                y_pos = loop.vert.co.y
                u = (x_pos / (width * spacing))
                v = (y_pos / (height * spacing))
                loop[uv_layer].uv = (u, v)
        bm.to_mesh(water_mesh)
        bm.free()

        mat_blue = material.create_flat("Mat_Blue", (0, 0, 1))
        water_obj.data.materials.append(mat_blue)
        water_obj.location = (width * spacing, height * spacing, 1 + raise_offset)

        count = len(water_obj.data.polygons)
        smooth_values = np.full(count, True)
        water_obj.data.polygons.foreach_set("use_smooth", smooth_values)

        vg_water2 = water_obj.vertex_groups.new(name="WaterMask")

        world_collection.objects.link(water_obj)

        disp = water_obj.modifiers.new(name="BaseHeight", type='DISPLACE')
        disp.texture = bpy.data.textures["GroudDepthMap"]
        disp.texture_coords = 'UV'
        disp.strength = ground_obj.modifiers["Displace"].strength

        sw = water_obj.modifiers.new(name="SnapToGround", type='SHRINKWRAP')
        sw.target = ground_obj
        sw.vertex_group = "WaterMask" # Need to prevent z-fighting
        sw.wrap_method = 'PROJECT'
        sw.offset = 1.01
        sw.cull_face = 'BACK'
        sw.use_project_z = True
        sw.use_positive_direction = False
        sw.use_negative_direction = True

    else:
        ground_obj = bpy.data.objects["GroundPlane"]
        pond_mod = ground_obj.modifiers["PondSink"]

        ground_obj.vertex_groups.clear()
        vg_tree = ground_obj.vertex_groups.new(name="TreeMask")
        tree_particles = ground_obj.modifiers["TreeParticles"]
        tree_particles.particle_system.vertex_group_density = "TreeMask"
        vg_water = ground_obj.vertex_groups.new(name="WaterMask")

        water_obj = bpy.data.objects["WaterPlane"]
        disp = water_obj.modifiers["BaseHeight"]
        sw = water_obj.modifiers["SnapToGround"]

        # Need copy of vertex group mask
        water_obj.vertex_groups.clear()
        vg_water2 = water_obj.vertex_groups.new(name="WaterMask")

    color_img_name = os.path.basename(color_image_path)
    color_img = bpy.data.images[color_img_name]

    if depth_changed:
        depth_img_name = os.path.basename(depth_image_path)
        depth_img = bpy.data.images[depth_img_name]
        depth_img.filepath = depth_image_path
        depth_img.reload()
    if color_changed:
        color_img.filepath = color_image_path
        color_img.reload()

    #
    # The code that only needs to change per-update for color
    #

    # For now, assume the high/width never change between calls
    width, height = color_img.size
    # [R, G, B, A, R, G, B, A...]
    pixels = np.array(color_img.pixels).reshape((height, width, 4))

    # Gets colors as a 1D array matching the vertices
    r = pixels[:, :, 0]
    g = pixels[:, :, 1]
    b = pixels[:, :, 2]

    # 0.5 is more lenient; 0.8 is stricter.
    # Use np.clip to ensure weights stay between 0.0 and 1.0
    pure_green = np.clip(g - (r + b) * 0.5, 0, 1)
    pure_blue = np.clip(b - (r + g) * 0.5, 0, 1)
    # Remove blue areas from the green mask
    pure_green = np.clip(pure_green - pure_blue, 0, 1)
    # Extra hard check blue is not on green
    pure_green[pure_blue > 0.05] = 0

    green_weights = pure_green.flatten()
    blue_weights = pure_blue.flatten()

    # Extract only the indices/weights that pass the threshold
    valid_mask = green_weights > 0.01
    valid_indices = np.where(valid_mask)[0]
    valid_weights = green_weights[valid_mask]
    # Fast way to loop only over the valid weights we care about
    for idx, weight in zip(valid_indices, valid_weights):
        vg_tree.add([int(idx)], float(weight), 'REPLACE')

    valid_mask_b = blue_weights > 0.01
    v_indices_b = np.where(valid_mask_b)[0]
    v_weights_b = blue_weights[valid_mask_b]
    for idx, weight in zip(v_indices_b, v_weights_b):
        vg_water.add([int(idx)], float(weight), 'REPLACE')
        vg_water2.add([int(idx)], float(weight), 'REPLACE')

    total_green_intensity = np.sum(green_weights)
    total_possible = len(green_weights)
    coverage_pct = total_green_intensity / total_possible
    # We want 0% coverage -> 1 tree
    # We want 30% (or more) coverage -> 200 trees
    tree_particles.particle_system.settings.count = int(np.interp(coverage_pct, [0, 0.4], [1, 250]))