import bpy

def load_models_to_collection(file_paths, collection_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)

    for path in file_paths:
        before_objs = set(bpy.data.objects.keys())

        bpy.ops.import_scene.gltf(filepath=path)

        after_objs = set(bpy.data.objects.keys())
        new_objs = [bpy.data.objects[name] for name in (after_objs - before_objs)]

        for obj in new_objs:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            collection.objects.link(obj)

    # Hides the original
    if collection.name in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.unlink(collection)

    return collection