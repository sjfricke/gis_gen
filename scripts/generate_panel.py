import bpy
import sys
import importlib

SCRIPTS_PATH = "/home/fricke/blender/gis_gen/scripts"
if SCRIPTS_PATH not in sys.path:
    sys.path.append(SCRIPTS_PATH)

import generate

class MESH_OT_run_gen(bpy.types.Operator):
    bl_idname = "mesh.run_gen"
    bl_label = "Generate"

    def execute(self, context):
        importlib.reload(generate)
        generate.generate()
        return {'FINISHED'}

class VIEW3D_PT_generate_panel(bpy.types.Panel):
    bl_label = "Generator"
    bl_idname = "VIEW3D_PT_generate_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Generate'

    def draw(self, context):
        self.layout.operator("mesh.run_gen", icon='GRID')

addon_keymaps = []

def register():
    bpy.utils.register_class(MESH_OT_run_gen)
    bpy.utils.register_class(VIEW3D_PT_generate_panel)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(MESH_OT_run_gen.bl_idname, 'PERIOD', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # Remove the hotkey first
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(MESH_OT_run_gen)
    bpy.utils.unregister_class(VIEW3D_PT_generate_panel)

if __name__ == "__main__":
    register()