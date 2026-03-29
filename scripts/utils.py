import bpy
import os

def deep_clean():
    for block in [bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.collections]:
        for item in list(block):
            block.remove(item)

def has_file_changed(filepath, storage_key):
    if not os.path.exists(filepath):
        return True

    current_mtime = os.path.getmtime(filepath)
    # Check if we saved a previous time in Blender's scene properties
    last_mtime = bpy.context.scene.get(storage_key, 0.0)

    if current_mtime > last_mtime:
        # File has been updated! Save the new time.
        bpy.context.scene[storage_key] = current_mtime
        return True

    return False