import bpy
import os

repo_path = "/home/fricke/blender/gis_gen/"
textures_path = os.path.join(repo_path, "textures")

def create_flat(name, color_rgb):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    bsdf = nodes.get("Principled BSDF")

    bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)

    bsdf.inputs['Roughness'].default_value = 1.0
    bsdf.inputs['Specular IOR Level'].default_value = 0.0

    return mat

def create_rocky_terrain_material(mat_name="Rocky_Terrain_Material"):
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_tex_coord = nodes.new(type='ShaderNodeTexCoord') # Corrected type
    node_tex_coord.location = (-1400, 0)

    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_mapping.location = (-1200, 0)
    node_mapping.inputs['Scale'].default_value[0] = 12
    node_mapping.inputs['Scale'].default_value[1] = 12

    def create_and_load_tex(name, filename, location, is_color=False):
        node = nodes.new(type='ShaderNodeTexImage')
        node.label = name
        node.location = location

        filepath = os.path.join(textures_path, filename)
        if os.path.exists(filepath):
            img = bpy.data.images.load(filepath)
            img.colorspace_settings.name = 'sRGB' if is_color else 'Non-Color'
            node.image = img
        else:
            print(f"Warning: Could not find {filename} at {filepath}")

        return node

    node_tex_base = create_and_load_tex("Base Color", "rocky_terrain_02_diff.png", (-800, 400), is_color=True)
    node_tex_spec = create_and_load_tex("Specular IOR Level", "rocky_terrain_02_spec.png", (-800, 100))
    node_tex_rough = create_and_load_tex("Roughness", "rocky_terrain_02_rough.png", (-800, -200))
    node_tex_disp = create_and_load_tex("Displacement", "rocky_terrain_02_disp.png", (-800, -500))
    node_tex_normal = create_and_load_tex("Normal Map", "rocky_terrain_02_nor_gl.png", (-800, -800))

    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = (-300, 100)

    node_normal_map = nodes.new(type='ShaderNodeNormalMap')
    node_normal_map.location = (-500, -800)

    node_displacement = nodes.new(type='ShaderNodeDisplacement')
    node_displacement.location = (-300, -500)
    node_displacement.inputs['Midlevel'].default_value = 0.5
    node_displacement.inputs['Scale'].default_value = 1.0

    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (0, 100)

    links.new(node_tex_coord.outputs['UV'], node_mapping.inputs['Vector'])

    for tex_node in [node_tex_base, node_tex_spec, node_tex_rough, node_tex_disp, node_tex_normal]:
        links.new(node_mapping.outputs['Vector'], tex_node.inputs['Vector'])

    links.new(node_tex_base.outputs['Color'], node_principled.inputs['Base Color'])
    links.new(node_tex_spec.outputs['Color'], node_principled.inputs['Specular IOR Level'])
    links.new(node_tex_rough.outputs['Color'], node_principled.inputs['Roughness'])

    links.new(node_tex_normal.outputs['Color'], node_normal_map.inputs['Color'])
    links.new(node_normal_map.outputs['Normal'], node_principled.inputs['Normal'])

    links.new(node_tex_disp.outputs['Color'], node_displacement.inputs['Height'])

    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    links.new(node_displacement.outputs['Displacement'], node_output.inputs['Displacement'])

    return mat
