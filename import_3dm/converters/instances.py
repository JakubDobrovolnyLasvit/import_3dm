# MIT License

# Copyright (c) 2018-2024 Nathan Letwory, Joel Putnam, Tom Svilans, Lukas Fertig

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy
import rhino3dm as r3d
from mathutils import Matrix, Vector
from math import sqrt
from . import utils
from . import material


#TODO
#tag collections and references with guids
#test w/ more complex blocks and empty blocks
#proper exception handling


def handle_instance_definitions(context, model, toplayer, layername, options):
    """
    Import instance definitions from rhino model as empty collections. These
    will later be populated to contain actual geometry.
    """
    create_fresh_blocks = options.get("create_fresh_block_definitions", False)
    
    # Store the original layername for reference
    original_layername = layername

    # Create versioned Instance Definitions collection if creating fresh blocks
    if create_fresh_blocks:
        # Find next available version number for Instance Definitions
        version = 1
        versioned_layername = layername
        while versioned_layername in context.blend_data.collections:
            version += 1
            versioned_layername = f"{layername}_v{version}"
        layername = versioned_layername
        
    # Store the final layername in options for use by import_instance_reference
    options["instance_definitions_layer"] = layername

    if not layername in context.blend_data.collections:
            instance_col = context.blend_data.collections.new(name=layername)
            instance_col.hide_render = True
            toplayer.children.link(instance_col)

    for idef in model.InstanceDefinitions:
        # Modify GUID for fresh blocks to ensure completely separate collections
        if create_fresh_blocks:
            # Create a new GUID by adding the version number to ensure uniqueness
            import uuid
            original_guid = str(idef.Id)
            versioned_guid = uuid.UUID(original_guid)
            # Modify the GUID to make it unique for this version
            versioned_guid = uuid.uuid5(versioned_guid, layername)
            tags = utils.create_tag_dict(versioned_guid, idef.Name, None, None, True)
        else:
            tags = utils.create_tag_dict(idef.Id, idef.Name, None, None, True)
        idef_col=utils.get_or_create_iddata(context.blend_data.collections, tags, None )

        try:
            instance_col.children.link(idef_col)
        except Exception:
            pass

def _duplicate_collection(context : bpy.context, collection : bpy.types.Collection, newname : str):
    new_collection = bpy.context.blend_data.collections.new(name=newname)
    def _recurse_duplicate_collection(collection : bpy.types.Collection):
        for obj in collection.children:
            if type(obj.type) == bpy.types.Collection:
                pass
            else:
                new_obj = context.blend_data.objects.new(name=obj.name, object_data=obj.data)
                new_collection.objects.link(new_obj)
        for child in collection.children:
            new_child = bpy.context.blend_data.collections.new(name=child.name)
            new_collection.children.link(new_child)
            _recurse_duplicate_collection(child,new_child)

def import_instance_reference(context : bpy.context, ob : r3d.File3dmObject, iref : bpy.types.Object, name : str, scale : float, options):
    # To be able to support ByParent material we need to add actual objects
    # instead of collection instances. That will allow us to add material slots
    # to instances and set them to 'OBJECT', which allows us to essentially
    # 'override' the material for the original mesh data
    
    create_fresh_blocks = options.get("create_fresh_block_definitions", False)
    
    if create_fresh_blocks:
        # Use modified GUID to find the fresh block definition collection
        import uuid
        # Get the versioned layer name from options
        layername = options.get("instance_definitions_layer", "Instance Definitions")
        
        original_guid = str(ob.Geometry.ParentIdefId)
        versioned_guid = uuid.UUID(original_guid)
        versioned_guid = uuid.uuid5(versioned_guid, layername)
        tags = utils.create_tag_dict(versioned_guid, "")
    else:
        tags = utils.create_tag_dict(ob.Geometry.ParentIdefId, "")
    
    iref.instance_type='COLLECTION'
    iref.instance_collection = utils.get_or_create_iddata(context.blend_data.collections, tags, None)
    iref.empty_display_size = options.get("empty_display_size", 0.0001)  # Configurable display size
    #instance_definition = utils.get_or_create_iddata(context.blend_data.collections, tags, None)
    #iref.data = instance_definition.data
    xform=list(ob.Geometry.Xform.ToFloatArray(1))
    xform=[xform[0:4],xform[4:8], xform[8:12], xform[12:16]]
    xform[0][3]*=scale
    xform[1][3]*=scale
    xform[2][3]*=scale
    iref.matrix_world = Matrix(xform)


def _reassign_materials_to_block_objects(parent_collection, context, model, options):
    """
    Reassign materials to existing block objects when creating new material versions.
    This ensures that existing blocks use the new materials instead of old ones.
    """
    from . import material as mat_module
    
    # Get materials dictionary that was created during material import
    # We need to access the global materials dict that was created
    rh_model = options.get("rh_model", model)
    
    for obj in parent_collection.objects:
        if not obj.get('rhid'):
            continue
            
        # Find the original Rhino object by GUID to get its material info
        rhino_obj = None
        for rh_obj in rh_model.Objects:
            if str(rh_obj.Attributes.Id) == obj.get('rhid'):
                rhino_obj = rh_obj
                break
                
        if not rhino_obj:
            continue
            
        # Get material info (same logic as in read3dm.py)
        attr = rhino_obj.Attributes
        rhinolayer = rh_model.Layers.FindIndex(attr.LayerIndex)
        
        mat_index = attr.MaterialIndex
        if attr.MaterialSource == r3d.ObjectMaterialSource.MaterialFromLayer:
            mat_index = rhinolayer.RenderMaterialIndex
        rhino_material = rh_model.Materials.FindIndex(mat_index)
        
        if mat_index == -1 or rhino_material.Name == "":
            matname = mat_module.DEFAULT_RHINO_MATERIAL
        else:
            matname = mat_module.material_name(rhino_material)
            
        # Find the new material by name (should have .001, .002 suffix)
        new_material = None
        for mat in context.blend_data.materials:
            if mat.name.startswith(matname) and mat.get('rhid') == str(rhino_material.Id if rhino_material else mat_module.DEFAULT_RHINO_MATERIAL_ID):
                new_material = mat
                break
                
        if new_material and len(obj.material_slots) > 0:
            obj.material_slots[0].material = new_material
            print(f"  Updated object '{obj.name}' to use material '{new_material.name}'")


def populate_instance_definitions(context, model, toplayer, layername, options, scale):
    import_as_grid = options.get("import_instances_grid_layout",False)
    create_fresh_blocks = options.get("create_fresh_block_definitions", False)

    if import_as_grid:
        count = 0
        columns = int(sqrt(len(model.InstanceDefinitions)))
        grid = options.get("import_instances_grid",False) *scale

    # Use the layername already determined by handle_instance_definitions
    if create_fresh_blocks:
        layername = options.get("instance_definitions_layer", layername)
        if not layername or layername == "Instance Definitions":
            # Fallback: Find next available version number if not set
            version = 1
            versioned_layername = "Instance Definitions"
            while versioned_layername in context.blend_data.collections:
                version += 1
                versioned_layername = f"Instance Definitions_v{version}"
            layername = versioned_layername
            options["instance_definitions_layer"] = layername

    # Get or create the Instance Definitions container collection
    if layername not in context.blend_data.collections:
        instance_col = context.blend_data.collections.new(name=layername)
        instance_col.hide_render = True
        toplayer.children.link(instance_col)
    else:
        instance_col = context.blend_data.collections[layername]

    #for every instance definition fish out the instance definition objects and link them to their parent
    for idef in model.InstanceDefinitions:
        # Use the same GUID modification logic as in handle_instance_definitions
        if create_fresh_blocks:
            # Create a new GUID by adding the version number to ensure uniqueness
            import uuid
            original_guid = str(idef.Id)
            versioned_guid = uuid.UUID(original_guid)
            # Modify the GUID to make it unique for this version
            versioned_guid = uuid.uuid5(versioned_guid, layername)
            tags = utils.create_tag_dict(versioned_guid, idef.Name, None, None, True)
        else:
            tags = utils.create_tag_dict(idef.Id, idef.Name, None, None, True)
        parent=utils.get_or_create_iddata(context.blend_data.collections, tags, None)
        objectids=idef.GetObjectIds()
        
        # Ensure the block definition collection is linked to Instance Definitions
        try:
            instance_col.children.link(parent)
        except Exception:
            pass  # Already linked
        
        # Handle block definition preservation logic
        if not create_fresh_blocks and len(parent.objects) > 0:
            # Keep existing block definitions but check if materials need updating
            create_new_materials = options.get("reuse_existing_materials", True) == False
            
            if create_new_materials:
                # User wants new material versions - reassign materials to existing objects
                print(f"Updating materials for existing block definition '{idef.Name}' with {len(parent.objects)} objects")
                _reassign_materials_to_block_objects(parent, context, model, options)
            else:
                # Preserve user's materials/UV work completely
                print(f"Preserving existing block definition '{idef.Name}' with {len(parent.objects)} objects")
            continue
        elif not create_fresh_blocks and len(parent.objects) == 0:
            # New block definition in preserve mode - import it normally
            print(f"Importing new block definition '{idef.Name}' in preserve mode")
        elif create_fresh_blocks:
            # Creating fresh blocks - the parent collection is already fresh due to modified GUID
            print(f"Creating fresh block definition '{idef.Name}'")
            # No need to clear objects since we're using a completely new collection

        if import_as_grid:
            #calculate position offset to lay out block definitions in xy plane
            offset = Vector((count%columns * grid, (count-count%columns)/columns * grid, 0 ))
            parent.instance_offset = offset #this sets the offset for the collection instances (read: resets the origin)
            count +=1

        # Link objects to block definition collection
        linked_count = 0
        for ob in context.blend_data.objects:
            for guid in objectids:
                if ob.get('rhid',None) == str(guid):
                    # For fresh blocks, only link objects that aren't already linked to other collections
                    # This prevents old objects from being included in fresh block definitions
                    if create_fresh_blocks and len(ob.users_collection) > 0:
                        # Skip objects that are already part of other collections (old objects)
                        continue
                    try:
                        parent.objects.link(ob)
                        linked_count += 1
                        if import_as_grid:
                            ob.location += offset #apply the previously calculated offset to all instance definition objects
                    except Exception:
                        pass
        
        # Debug: Print info about block definition population
        if len(objectids) > 0:
            print(f"Block '{idef.Name}': Expected {len(objectids)} objects, linked {linked_count} objects")
