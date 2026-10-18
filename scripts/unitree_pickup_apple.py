import omni
from omni.isaac.kit import SimulationApp

# Only needed if running standalone, not in Script Editor
simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage, open_stage
from pxr import Usd, UsdGeom, Gf

# 1. Create the world
world = World(stage_units_in_meters=1.0)

# 2. Load warehouse environment (open as the main stage)
warehouse_usd = get_assets_root_path() + "/Isaac/Environments/Simple_Warehouse/warehouse.usd"
open_stage(warehouse_usd)

# 3. Add Unitree humanoid
unitree_usd = get_assets_root_path() + "/Isaac/Robots/Unitree/humanoid.usd"
add_reference_to_stage(unitree_usd, "/World/Unitree")

# 4. Add apple
apple_usd = get_assets_root_path() + "/Isaac/Props/Fruits/apple.usd"
add_reference_to_stage(apple_usd, "/World/Apple")

# Helpers
def _get_stage() -> Usd.Stage:
    return omni.usd.get_context().get_stage()


def _get_world_translation(prim: Usd.Prim) -> Gf.Vec3d:
    xform_cache = UsdGeom.XformCache()
    world_xf = xform_cache.GetLocalToWorldTransform(prim)
    return world_xf.ExtractTranslation()


def _set_local_translation(prim: Usd.Prim, translation: Gf.Vec3d) -> None:
    xform = UsdGeom.Xformable(prim)
    translate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = op
            break
    if translate_op is None:
        translate_op = xform.AddTranslateOp()
    translate_op.Set(translation)


def _set_world_translation(prim: Usd.Prim, translation: Gf.Vec3d) -> None:
    # Works reliably for prims directly under /World
    _set_local_translation(prim, translation)


def _find_hand_prim(root_prim: Usd.Prim) -> Usd.Prim:
    if not root_prim or not root_prim.IsValid():
        return None
    candidates = [
        "right_hand",
        "r_hand",
        "right_wrist",
        "r_wrist",
        "hand_r",
        "righthand",
        "handright",
    ]
    for prim in Usd.PrimRange(root_prim):
        name = prim.GetName().lower()
        if any(token in name for token in candidates):
            return prim
    return None


# 5. Set positions
stage = _get_stage()
unitree_prim = stage.GetPrimAtPath("/World/Unitree")
apple_prim = stage.GetPrimAtPath("/World/Apple")

_set_world_translation(unitree_prim, Gf.Vec3d(0.0, 0.0, 0.0))
_set_world_translation(apple_prim, Gf.Vec3d(0.6, 0.0, 0.9))

# 6. Script humanoid to pick up apple (simple follow-hand animation)
hand_prim = _find_hand_prim(unitree_prim)
if not hand_prim:
    print("[WARN] Could not find right hand prim. Apple will stay in place.")

# 7. Run simulation
world.reset()
settle_frames = 120
approach_frames = 240
hold_frames = 600
offset = Gf.Vec3d(0.0, 0.0, 0.08)

frame = 0
while simulation_app.is_running():
    world.step(render=True)
    frame += 1

    if not hand_prim:
        continue

    if frame < settle_frames:
        continue

    hand_pos = _get_world_translation(hand_prim)
    target = hand_pos + offset

    if frame < settle_frames + approach_frames:
        t = (frame - settle_frames) / float(approach_frames)
        start = Gf.Vec3d(0.6, 0.0, 0.9)
        interp = (1.0 - t) * start + t * target
        _set_world_translation(apple_prim, interp)
    else:
        _set_world_translation(apple_prim, target)

# Only needed if running standalone
simulation_app.close()
