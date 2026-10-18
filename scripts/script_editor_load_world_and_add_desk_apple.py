import os
import omni
from pxr import UsdGeom, Gf
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage

# Load your saved world
world_path = r"C:\Users\ryan_\OneDrive\Documents\isaac_world\nova_carter.usd"

ctx = omni.usd.get_context()
ctx.open_stage(world_path)

# Wait a few frames for the stage to load
for _ in range(60):
    omni.kit.app.get_app().update()

stage = ctx.get_stage()

# Helper to set translation

def set_local_translation(prim, translation):
    xform = UsdGeom.Xformable(prim)
    translate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = op
            break
    if translate_op is None:
        translate_op = xform.AddTranslateOp()
    translate_op.Set(translation)


# Create a simple desk as a cube prim
if not stage.GetPrimAtPath("/World/Desk"):
    desk_prim = stage.DefinePrim("/World/Desk", "Cube")
    set_local_translation(desk_prim, Gf.Vec3d(1.0, 0.0, 0.375))
    UsdGeom.Cube(desk_prim).GetSizeAttr().Set(1.0)  # size is uniform; scale via xform if needed

# Add an apple and place it on the desk
assets_root = get_assets_root_path()
apple_usd = assets_root + "/Isaac/Props/Fruits/apple.usd"
add_reference_to_stage(apple_usd, "/World/Apple")

# Wait for the apple reference to load
for _ in range(30):
    omni.kit.app.get_app().update()

apple_prim = stage.GetPrimAtPath("/World/Apple")
if apple_prim:
    set_local_translation(apple_prim, Gf.Vec3d(1.0, 0.0, 0.8))

print("Loaded world and added desk + apple.")
