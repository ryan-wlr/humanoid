import os
import math
import time
import omni
import carb
from omni.isaac.kit import SimulationApp

# Debug log file (to confirm script execution)
debug_log_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "nova_carter_debug.txt")
)


def _debug_log(message: str) -> None:
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


_debug_log("SCRIPT START")

# Only create SimulationApp when running standalone (not via isaac-sim.bat --run)
simulation_app = None
try:
    import omni.kit.app

    kit_app = omni.kit.app.get_app()
    if kit_app is None or not kit_app.is_running():
        simulation_app = SimulationApp({"headless": False})
except Exception:
    simulation_app = SimulationApp({"headless": False})

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage, open_stage
from pxr import UsdGeom, UsdPhysics, Gf, UsdShade, Sdf, Usd


# Helpers

def _get_stage():
    return omni.usd.get_context().get_stage()


def _app_update():
    if simulation_app is not None:
        simulation_app.update()
    else:
        import omni.kit.app

        omni.kit.app.get_app().update()


def _set_local_translation(prim, translation: Gf.Vec3d) -> None:
    xform = UsdGeom.Xformable(prim)
    translate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = op
            break
    if translate_op is None:
        translate_op = xform.AddTranslateOp()
    translate_op.Set(translation)


def _set_display_color_recursive(prim, color: Gf.Vec3f) -> None:
    if not prim or not prim.IsValid():
        return
    try:
        gprim = UsdGeom.Gprim(prim)
        if gprim:
            gprim.GetDisplayColorAttr().Set([color])
            gprim.GetDisplayOpacityAttr().Set([1.0])
    except Exception:
        pass
    for child in prim.GetChildren():
        _set_display_color_recursive(child, color)


def _bind_solid_material(prim, color: Gf.Vec3f, material_name: str = "AppleMaterial") -> None:
    if not prim or not prim.IsValid():
        return
    stage = prim.GetStage()
    if stage is None:
        return
    material_path = "/World/Materials/" + material_name
    UsdGeom.Xform.Define(stage, "/World/Materials")
    material = UsdShade.Material.Define(stage, material_path)

    # OmniPBR (RTX)
    omni_shader = UsdShade.Shader.Define(stage, material_path + "/OmniPBR")
    omni_shader.CreateIdAttr("OmniPBR")
    omni_shader.CreateInput("diffuse_color", Sdf.ValueTypeNames.Color3f).Set(color)
    omni_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    omni_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.35)
    omni_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0)

    # UsdPreviewSurface (HydraStorm)
    preview_shader = UsdShade.Shader.Define(stage, material_path + "/PreviewSurface")
    preview_shader.CreateIdAttr("UsdPreviewSurface")
    preview_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(color)
    preview_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.35)
    preview_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    preview_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0)

    material.CreateSurfaceOutput().ConnectToSource(
        omni_shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    )
    material.CreateSurfaceOutput("preview").ConnectToSource(
        preview_shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    )

    def _bind_recursive(p):
        if not p or not p.IsValid():
            return
        try:
            gprim = UsdGeom.Gprim(p)
            if gprim:
                UsdShade.MaterialBindingAPI(p).Bind(material)
        except Exception:
            pass
        for c in p.GetChildren():
            _bind_recursive(c)

    _bind_recursive(prim)


def _find_prims_by_keywords(root_prim, keywords):
    results = []
    if not root_prim or not root_prim.IsValid():
        return results
    stack = [root_prim]
    while stack:
        prim = stack.pop()
        name = prim.GetName().lower()
        if any(k in name for k in keywords):
            results.append(prim)
        for child in prim.GetChildren():
            stack.append(child)
    return results


def _get_or_add_translate_op(prim):
    xform = UsdGeom.Xformable(prim)
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return op
    return xform.AddTranslateOp()


def _get_or_add_rotate_x_op(prim):
    xform = UsdGeom.Xformable(prim)
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeRotateX:
            return op
    return xform.AddRotateXOp()


def _get_or_add_rotate_y_op(prim):
    xform = UsdGeom.Xformable(prim)
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
            return op
    return xform.AddRotateYOp()


def _clear_xform_ops(prim) -> None:
    if not prim or not prim.IsValid():
        return
    try:
        xform = UsdGeom.Xformable(prim)
        xform.ClearXformOpOrder()
        props = [p for p in prim.GetProperties() if p.GetName().startswith("xformOp:")]
        for p in props:
            prim.RemoveProperty(p.GetName())
    except Exception:
        pass


def _disable_physics_recursive(prim) -> None:
    if not prim or not prim.IsValid():
        return
    try:
        prim.CreateAttribute("physics:enabled", Sdf.ValueTypeNames.Bool).Set(False)
        prim.CreateAttribute("physxRigidBody:kinematicEnabled", Sdf.ValueTypeNames.Bool).Set(True)
        prim.CreateAttribute("physxRigidBody:disableGravity", Sdf.ValueTypeNames.Bool).Set(True)
    except Exception:
        pass
    for child in prim.GetChildren():
        _disable_physics_recursive(child)


def _remove_physics_apis_recursive(prim) -> None:
    """Make an authored animation rig immune to live PhysX simulation."""
    if not prim or not prim.IsValid():
        return
    for api in (
        UsdPhysics.ArticulationRootAPI,
        UsdPhysics.RigidBodyAPI,
        UsdPhysics.CollisionAPI,
        UsdPhysics.MassAPI,
    ):
        try:
            prim.RemoveAPI(api)
        except Exception:
            pass
    for child in prim.GetChildren():
        _remove_physics_apis_recursive(child)


def _force_visible_recursive(prim) -> None:
    if not prim or not prim.IsValid():
        return
    try:
        prim.GetAttribute("visibility").Set("inherited")
        prim.GetAttribute("purpose").Set("default")
        prim.SetActive(True)
    except Exception:
        pass
    for child in prim.GetChildren():
        _force_visible_recursive(child)


def _force_purpose_default_recursive(prim: Usd.Prim) -> None:
    if not prim or not prim.IsValid():
        return
    try:
        imageable = UsdGeom.Imageable(prim)
        imageable.GetPurposeAttr().Set(UsdGeom.Tokens.default)
    except Exception:
        pass
    for child in prim.GetChildren():
        _force_purpose_default_recursive(child)

# 1. Open Nova Carter environment as the main stage
assets_root = get_assets_root_path()
if assets_root is None:
    raise RuntimeError("Could not find Isaac Sim assets root. Check Nucleus connection.")
carb.log_info(f"Assets root: {assets_root}")
_debug_log(f"Assets root: {assets_root}")

candidate_usd_paths = [
    "C:/Users/ryan_/OneDrive/Documents/isaac_world/nova_carter.usd",
    assets_root + "/Isaac/Environments/Nova_Carter_Warehouse/nova_carter_warehouse.usd",
    assets_root + "/Isaac/Environments/Nova_Carter/warehouse.usd",
    assets_root + "/Isaac/Environments/Nova_Carter/nova_carter_warehouse.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Environments/Nova_Carter_Warehouse/nova_carter_warehouse.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Environments/Nova_Carter/warehouse.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Environments/Nova_Carter/nova_carter_warehouse.usd",
]

custom_usd = os.getenv("NOVA_CARTER_USD")
if custom_usd:
    # If a local file path is provided, use it directly
    if os.path.exists(custom_usd):
        candidate_usd_paths.insert(0, custom_usd)
    # If a folder URL is provided, try to find a USD inside it
    # If a folder URL is provided, try to find a USD inside it
    elif custom_usd.endswith("/") or not custom_usd.lower().endswith(".usd"):
        try:
            result, entries = omni.client.list(custom_usd)
            if result == omni.client.Result.OK:
                usd_candidates = [
                    e for e in entries if e.name.lower().endswith(".usd")
                ]
                # Prefer likely warehouse or nova files
                usd_candidates.sort(
                    key=lambda e: (
                        "warehouse" not in e.name.lower()
                        and "nova" not in e.name.lower(),
                        e.name.lower(),
                    )
                )
                if usd_candidates:
                    folder_usd = custom_usd.rstrip("/") + "/" + usd_candidates[0].name
                    candidate_usd_paths.insert(0, folder_usd)
                    _debug_log(f"Resolved folder USD: {folder_usd}")
                else:
                    _debug_log(f"No USD files found in folder: {custom_usd}")
            else:
                _debug_log(f"Failed to list folder: {custom_usd} -> {result}")
        except Exception as exc:
            _debug_log(f"Exception listing folder {custom_usd}: {exc}")
    else:
        candidate_usd_paths.insert(0, custom_usd)

nova_carter_usd = None
for path in candidate_usd_paths:
    result, _ = omni.client.stat(path)
    if result == omni.client.Result.OK:
        nova_carter_usd = path
        break

if not nova_carter_usd:
    msg = "Could not find a Nova Carter warehouse USD. Checked: " + ", ".join(candidate_usd_paths)
    _debug_log(msg)
    raise RuntimeError(msg)

carb.log_info(f"Opening stage: {nova_carter_usd}")
_debug_log(f"Opening stage: {nova_carter_usd}")

# Open via USD context (more reliable in --run)
context = omni.usd.get_context()
context.open_stage(nova_carter_usd)

# Wait a few frames for the stage to load
for _ in range(60):
    _app_update()

stage = _get_stage()
root_id = stage.GetRootLayer().identifier if stage else ""
carb.log_info(f"Stage root layer: {root_id}")
_debug_log(f"Stage root layer: {root_id}")
try:
    if stage is not None:
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
except Exception:
    pass

# Fallback: if stage is empty, reference the environment under /World/NovaCarter
world_prim = stage.GetPrimAtPath("/World") if stage else None
has_children = bool(world_prim) and any(True for _ in world_prim.GetChildren())
if not root_id or not has_children:
    carb.log_warn("Stage appears empty after open_stage; adding reference under /World/NovaCarter.")
    _debug_log("Stage empty; adding reference under /World/NovaCarter")
    add_reference_to_stage(nova_carter_usd, "/World/NovaCarter")
    for _ in range(60):
        _app_update()

# 2. Ensure /World exists
if stage and not stage.GetPrimAtPath("/World"):
    stage.DefinePrim("/World", "Xform")

# 3. Add a fixed desk (simple cuboid via USD)
# Desk dimensions: 1.2m (x) x 0.6m (y) x 0.75m (z)
# Desk top center height roughly 0.75m
desk_path = "/World/Desk"
desk_xform = UsdGeom.Xform.Define(stage, desk_path)
desk_xformable = UsdGeom.Xformable(desk_xform.GetPrim())
desk_xformable.AddTranslateOp().Set(Gf.Vec3d(0.6, 0.0, 0.375))
desk_xformable.AddScaleOp().Set(Gf.Vec3d(1.2, 0.6, 0.75))
desk_geom = UsdGeom.Cube.Define(stage, desk_path + "/Geom")
desk_geom.CreateSizeAttr(1.0)

# 4. Add apple on the desk
# Use a solid USD sphere so it can't be transparent
stage = _get_stage()
apple_path = "/World/Apple"
apple_xform = UsdGeom.Xform.Define(stage, apple_path)
apple_xformable = UsdGeom.Xformable(apple_xform.GetPrim())
APPLE_REST_POSITION = (0.30, -0.15, 0.79)
apple_xformable.AddTranslateOp().Set(Gf.Vec3d(*APPLE_REST_POSITION))
apple_geom = UsdGeom.Sphere.Define(stage, apple_path + "/Geom")
apple_geom.CreateRadiusAttr(0.04)
apple_prim = apple_xform.GetPrim()
_set_display_color_recursive(apple_prim, Gf.Vec3f(0.85, 0.1, 0.1))
_bind_solid_material(apple_prim, Gf.Vec3f(0.85, 0.1, 0.1), "AppleMaterial")


def _add_colored_cube(path: str, position, scale, color, material_name: str) -> Usd.Prim:
    cube_xform = UsdGeom.Xform.Define(stage, path)
    xformable = UsdGeom.Xformable(cube_xform.GetPrim())
    xformable.AddTranslateOp().Set(Gf.Vec3d(*position))
    xformable.AddScaleOp().Set(Gf.Vec3d(*scale))
    cube = UsdGeom.Cube.Define(stage, path + "/Geom")
    cube.CreateSizeAttr(1.0)
    prim = cube_xform.GetPrim()
    _set_display_color_recursive(prim, Gf.Vec3f(*color))
    _bind_solid_material(prim, Gf.Vec3f(*color), material_name)
    return prim


def _add_sorting_bin(name: str, center, color) -> tuple:
    """Create an open-topped bin and retain its target position for policy consumers."""
    bin_path = "/World/SortingBins/" + name
    UsdGeom.Xform.Define(stage, "/World/SortingBins")
    base_height = 0.82
    wall_height = 0.10
    width = 0.20
    depth = 0.18
    thickness = 0.018
    _add_colored_cube(
        bin_path + "/Base", (center[0], center[1], base_height), (width, depth, thickness),
        color, name + "BinMaterial",
    )
    _add_colored_cube(
        bin_path + "/LeftWall", (center[0] - width / 2, center[1], base_height + wall_height / 2),
        (thickness, depth, wall_height), color, name + "BinMaterial",
    )
    _add_colored_cube(
        bin_path + "/RightWall", (center[0] + width / 2, center[1], base_height + wall_height / 2),
        (thickness, depth, wall_height), color, name + "BinMaterial",
    )
    _add_colored_cube(
        bin_path + "/BackWall", (center[0], center[1] + depth / 2, base_height + wall_height / 2),
        (width, thickness, wall_height), color, name + "BinMaterial",
    )
    _add_colored_cube(
        bin_path + "/FrontWall", (center[0], center[1] - depth / 2, base_height + wall_height / 2),
        (width, thickness, wall_height), color, name + "BinMaterial",
    )
    bin_prim = stage.GetPrimAtPath(bin_path)
    bin_prim.CreateAttribute("fruit_sorting:fruit", Sdf.ValueTypeNames.String).Set(name.lower())
    bin_prim.CreateAttribute("fruit_sorting:drop_position", Sdf.ValueTypeNames.Double3).Set(
        Gf.Vec3d(center[0], center[1], base_height + 0.04)
    )
    return center[0], center[1], base_height + 0.04


APPLE_BIN_POSITION = _add_sorting_bin("Apple", (0.86, -0.18), (0.85, 0.08, 0.08))
_add_sorting_bin("Orange", (0.86, 0.12), (0.95, 0.42, 0.04))
_add_sorting_bin("Banana", (0.60, 0.25), (0.95, 0.82, 0.05))
_add_sorting_bin("Lemon", (0.60, -0.42), (0.95, 0.85, 0.05))

# Static distractor fruit establishes the multi-class sorting task. The red apple
# is animated into its matching bin by the deterministic baseline policy below.
for fruit_name, position, color, radius in (
    ("Orange", (0.37, 0.16, 0.79), (0.95, 0.42, 0.04), 0.043),
    ("Lemon", (0.48, -0.32, 0.79), (0.95, 0.85, 0.05), 0.036),
):
    fruit_xform = UsdGeom.Xform.Define(stage, "/World/Fruits/" + fruit_name)
    UsdGeom.Xform.Define(stage, "/World/Fruits")
    UsdGeom.Xformable(fruit_xform.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(*position))
    fruit_geom = UsdGeom.Sphere.Define(stage, "/World/Fruits/" + fruit_name + "/Geom")
    fruit_geom.CreateRadiusAttr(radius)
    _set_display_color_recursive(fruit_xform.GetPrim(), Gf.Vec3f(*color))
    _bind_solid_material(fruit_xform.GetPrim(), Gf.Vec3f(*color), fruit_name + "Material")

banana_prim = UsdGeom.Xform.Define(stage, "/World/Fruits/Banana").GetPrim()
for index, offset in enumerate(((-0.04, -0.025, 0.0), (0.0, 0.0, 0.008), (0.04, 0.025, 0.0))):
    segment = UsdGeom.Sphere.Define(stage, "/World/Fruits/Banana/Segment" + str(index))
    segment.CreateRadiusAttr(0.027)
    segment_xform = UsdGeom.Xformable(segment.GetPrim())
    segment_xform.AddTranslateOp().Set(Gf.Vec3d(0.43 + offset[0], 0.34 + offset[1], 0.79 + offset[2]))
_set_display_color_recursive(banana_prim, Gf.Vec3f(0.95, 0.82, 0.05))
_bind_solid_material(banana_prim, Gf.Vec3f(0.95, 0.82, 0.05), "BananaMaterial")

# 5. Add Unitree G1 humanoid
g1_candidates = [
    assets_root + "/Isaac/Robots/Unitree/Unitree_G1/unitree_g1.usd",
    assets_root + "/Isaac/Robots/Unitree/G1/unitree_g1.usd",
    assets_root + "/Isaac/Robots/Unitree/G1/g1.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Robots/Unitree/Unitree_G1/unitree_g1.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Robots/Unitree/G1/unitree_g1.usd",
    "omniverse://localhost/NVIDIA/Assets/Isaac/Robots/Unitree/G1/g1.usd",
]
g1_usd = None
for path in g1_candidates:
    result, _ = omni.client.stat(path)
    if result == omni.client.Result.OK:
        g1_usd = path
        break

if g1_usd:
    rig_path = "/World/G1Rig"
    try:
        if stage.GetPrimAtPath(rig_path).IsValid():
            stage.RemovePrim(rig_path)
        if stage.GetPrimAtPath("/World/UnitreeG1").IsValid():
            stage.RemovePrim("/World/UnitreeG1")
    except Exception:
        pass
    UsdGeom.Xform.Define(stage, rig_path)
    add_reference_to_stage(g1_usd, rig_path + "/UnitreeG1")
    rig_prim = _get_stage().GetPrimAtPath(rig_path)
    g1_prim = _get_stage().GetPrimAtPath(rig_path + "/UnitreeG1")
    _disable_physics_recursive(g1_prim)
    _force_visible_recursive(rig_prim)
    _force_purpose_default_recursive(rig_prim)
    try:
        UsdGeom.Xformable(rig_prim).SetResetXformStack(True)
    except Exception:
        pass
    _clear_xform_ops(rig_prim)
    try:
        UsdGeom.Xformable(g1_prim).SetResetXformStack(True)
    except Exception:
        pass
    _clear_xform_ops(g1_prim)
    _force_purpose_default_recursive(g1_prim)
    _set_local_translation(g1_prim, Gf.Vec3d(0.0, 0.0, 0.0))

    # The rig stays at the origin; the animation drives the real G1 joints and base pose
    _set_local_translation(rig_prim, Gf.Vec3d(0.0, 0.0, 0.0))
    _debug_log("Authoring joint-driven G1 walk and pickup")
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import importlib
    import g1_pickup_anim
    importlib.reload(g1_pickup_anim)

    stage = _get_stage()
    for _ in range(10):
        _app_update()
    animation = g1_pickup_anim.G1PickupAnimation(
        stage, stage.GetPrimAtPath(rig_path + "/UnitreeG1"), stage.GetPrimAtPath("/World/Apple"),
        APPLE_REST_POSITION, drop_position=APPLE_BIN_POSITION, log=_debug_log,
    )
    animation.author()
    _remove_physics_apis_recursive(g1_prim)
    frames = g1_pickup_anim.END_FRAME
    raw_demo_output = os.getenv("RAW_DEMO_OUTPUT")
    if raw_demo_output:
        animation.export_raw_demonstration(
            raw_demo_output,
            "pick up the apple from the table and place it in the red apple bin",
        )

    _debug_log(f"Added Unitree G1 from: {g1_usd}")
else:
    _debug_log("Unitree G1 USD not found in known asset paths.")


async def _capture_pickup_video(output_path: str) -> None:
    import numpy as np
    import omni.replicator.core as rep
    import omni.timeline
    from isaacsim.core.utils.viewports import set_camera_view
    from omni.kit.viewport.utility import get_active_viewport

    viewport = get_active_viewport()
    if viewport is None:
        raise RuntimeError("Cannot record video because Isaac Sim has no active viewport.")

    camera_path = "/OmniverseKit_Persp"
    viewport.camera_path = camera_path
    set_camera_view(
        eye=[-0.9, -4.2, 1.7],
        target=[-0.9, 0.0, 0.8],
        camera_prim_path=camera_path,
        viewport_api=viewport,
    )

    output_path = os.path.abspath(output_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    temporary_path = output_path + ".tmp.mp4"
    fps = 24
    video_end_frame = g1_pickup_anim.END_FRAME

    import cv2

    writer = None
    annotator = None
    timeline = omni.timeline.get_timeline_interface()
    frame_count = 0
    video_size = None
    try:
        render_product_path = viewport.render_product_path
        if not render_product_path:
            raise RuntimeError("The active Isaac Sim viewport has no render product.")
        annotator = rep.AnnotatorRegistry.get_annotator("rgb")
        annotator.attach([render_product_path])
        rep.orchestrator.set_capture_on_play(False)
        timeline.stop()

        time_codes_per_second = _get_stage().GetTimeCodesPerSecond()
        for frame in range(video_end_frame + 1):
            timeline.set_current_time(frame / time_codes_per_second)
            cam_eye, cam_target = animation.camera(frame)
            set_camera_view(
                eye=cam_eye.tolist(),
                target=cam_target.tolist(),
                camera_prim_path=camera_path,
                viewport_api=viewport,
            )
            image = None
            for _ in range(5):
                await rep.orchestrator.step_async(
                    rt_subframes=2,
                    delta_time=0.0,
                    pause_timeline=True,
                )
                captured = annotator.get_data()
                if isinstance(captured, dict):
                    captured = captured.get("data")
                if captured is not None:
                    captured = np.asarray(captured)
                    if captured.size:
                        image = captured
                        break
            if image is None:
                raise RuntimeError(f"Viewport returned no image data at frame {frame}.")

            if image.ndim != 3 or image.shape[2] < 3:
                raise RuntimeError(
                    f"Unexpected viewport image shape at frame {frame}: {image.shape}"
                )
            height, width = image.shape[:2]
            current_video_size = (width, height)
            if writer is None:
                writer = cv2.VideoWriter(
                    temporary_path,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    current_video_size,
                )
                if not writer.isOpened():
                    raise RuntimeError(f"Could not open MP4 video writer for {temporary_path}")
                video_size = current_video_size
            elif current_video_size != video_size:
                raise RuntimeError(f"Viewport resolution changed while recording frame {frame}.")
            writer.write(cv2.cvtColor(image[:, :, :3], cv2.COLOR_RGB2BGR))
            frame_count += 1

            if frame_count % 100 == 0:
                _debug_log(f"Video recording progress: {frame_count} frames")

        if writer is None or frame_count == 0:
            raise RuntimeError("No video frames were captured.")
        writer.release()
        writer = None
        timeline.stop()
        timeline.set_current_time(0)

        check = cv2.VideoCapture(temporary_path)
        try:
            ok, first_frame = check.read()
            if not ok or first_frame is None or int(check.get(cv2.CAP_PROP_FRAME_COUNT)) != frame_count:
                raise RuntimeError(f"MP4 validation failed for {temporary_path}.")
        finally:
            check.release()
        os.replace(temporary_path, output_path)
        _debug_log(f"Captured video: {output_path} ({frame_count} frames at {fps} fps)")
    except Exception:
        if writer is not None:
            writer.release()
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise
    finally:
        if annotator is not None:
            annotator.detach()


# 6. Save the stage to assets folder
save_path = os.path.normpath(
    os.path.join(
        os.path.expanduser("~"),
        "OneDrive",
        "Documents",
        "isaac_world",
        "nova_carter_desk_apple.usd",
    )
)
timestamped_save_path = os.path.normpath(
    os.path.join(
        os.path.expanduser("~"),
        "OneDrive",
        "Documents",
        "isaac_world",
        f"nova_carter_desk_apple_{int(time.time() * 1000)}.usd",
    )
)
_debug_log(f"Attempting save to: {save_path}")
try:
    omni.usd.get_context().save_as_stage(save_path)
    _debug_log("save_as_stage completed")
except Exception as exc:
    _debug_log(f"save_as_stage failed: {exc}")

try:
    stage = _get_stage()
    if stage is not None:
        stage.GetRootLayer().Export(save_path)
        _debug_log("RootLayer Export completed")
except Exception as exc:
    _debug_log(f"RootLayer Export failed: {exc}")

try:
    stage = _get_stage()
    if stage is not None:
        stage.GetRootLayer().Export(timestamped_save_path)
        _debug_log(f"Timestamped Export completed: {timestamped_save_path}")
except Exception as exc:
    _debug_log(f"Timestamped Export failed: {exc}")

carb.log_info(f"Saved stage to: {save_path}")
_debug_log(f"Saved stage to: {save_path}")

# 6. Capture a video when requested
video_output = os.getenv("VIDEO_OUTPUT")
if video_output:
    from omni.kit.async_engine import run_coroutine

    video_task = run_coroutine(_capture_pickup_video(video_output))
    try:
        while not video_task.done():
            _app_update()
        video_task.result()
    except Exception:
        import omni.kit.app

        omni.kit.app.get_app().quit()
        raise

# 6. Run simulation (optional)

auto_exit = os.getenv("AUTO_EXIT", "1") == "1"
if auto_exit:
    try:
        import omni.kit.app

        omni.kit.app.get_app().quit()
    except Exception:
        pass
else:
    if simulation_app is not None:
        try:
            import omni.timeline

            timeline = omni.timeline.get_timeline_interface()
            timeline.set_current_time(0)
            timeline.play()
        except Exception:
            pass
        while simulation_app.is_running():
            _app_update()
        simulation_app.close()
    else:
        import omni.kit.app

        app = omni.kit.app.get_app()
        while app.is_running():
            _app_update()
