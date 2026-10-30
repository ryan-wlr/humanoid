"""Joint-driven walk-and-pickup animation for the Unitree G1 (29 DoF with hands).

The G1 USD is a set of rigid links connected by PhysX revolute joints. This module
reads those joints, does forward kinematics itself, solves inverse kinematics for
the right arm and writes the resulting link transforms as USD time samples. The
physics simulation is not needed, so the result plays back identically on the
timeline and in video capture.
"""
import json
import math
import os

import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdPhysics

FPS = 24
WALK_FRAMES = 115
PRE_FRAME = 150
GRASP_FRAME = 175
ATTACH_FRAME = 197
LIFT_FRAME = 228
PLACE_FRAME = 285
RELEASE_FRAME = 307
END_FRAME = 455
TURN_START = 340
TURN_END = 380
AWAY_DIST = 1.5

START_X = -1.95
END_X = -0.15
STAND_HIP, STAND_KNEE = -0.10, 0.20
ANKLE_HEIGHT = 0.04  # ankle roll link origin height above the floor

ARM_JOINTS = [
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]
GROOT_FULL_BODY_JOINT_ORDER = (
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_pitch_joint", "waist_roll_joint", "waist_yaw_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "left_hand_index_0_joint", "left_hand_index_1_joint", "left_hand_middle_0_joint",
    "left_hand_middle_1_joint", "left_hand_thumb_0_joint", "left_hand_thumb_1_joint",
    "left_hand_thumb_2_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
    "right_hand_index_0_joint", "right_hand_index_1_joint", "right_hand_middle_0_joint",
    "right_hand_middle_1_joint", "right_hand_thumb_0_joint", "right_hand_thumb_1_joint",
    "right_hand_thumb_2_joint",
)
IK_JOINTS = ["waist_pitch_joint"] + ARM_JOINTS
READY = {
    "waist_pitch_joint": 0.0, "right_shoulder_pitch_joint": 0.0,
    "right_shoulder_roll_joint": -0.12, "right_shoulder_yaw_joint": 0.0,
    "right_elbow_joint": 0.4, "right_wrist_roll_joint": 0.0,
    "right_wrist_pitch_joint": 0.0, "right_wrist_yaw_joint": 0.0,
}


def _np(m):
    return np.array([list(r) for r in m], dtype=float).T


def _gf(m):
    return Gf.Matrix4d(m.T.tolist())


def _rot_axis(axis, q):
    c, s = math.cos(q), math.sin(q)
    r = np.eye(4)
    if axis == "X":
        r[1:3, 1:3] = [[c, -s], [s, c]]
    elif axis == "Y":
        r[0, 0], r[0, 2], r[2, 0], r[2, 2] = c, s, -s, c
    else:
        r[0:2, 0:2] = [[c, -s], [s, c]]
    return r


def _rot_z(yaw):
    return _rot_axis("Z", yaw)[:3, :3]


def _frame(pos, quat):
    w, x, y, z = quat.GetReal(), *quat.GetImaginary()
    t = np.eye(4)
    t[:3, :3] = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    t[:3, 3] = [pos[0], pos[1], pos[2]]
    return t


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


class _Joint:
    pass


class G1PickupAnimation:
    def __init__(self, stage, g1_prim, apple_prim, apple_rest, drop_position=None, log=print):
        self.stage = stage
        self.g1_prim = g1_prim
        self.apple_prim = apple_prim
        self.apple_rest = np.array(apple_rest, dtype=float)
        self.drop_position = np.array(
            drop_position if drop_position is not None else apple_rest, dtype=float
        )
        self.log = log
        self._read_rig()
        self._calibrate()

    # ----- rig description -------------------------------------------------
    def _rest_world(self, prim):
        xf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        return _np(xf)

    def _read_rig(self):
        stage, g1 = self.stage, self.g1_prim
        self.root = None
        for p in Usd.PrimRange(g1):
            if p.HasAPI(UsdPhysics.ArticulationRootAPI):
                self.root = p.GetPath()
                break
        edges = []
        for p in Usd.PrimRange(g1):
            if not p.IsA(UsdPhysics.Joint):
                continue
            j = UsdPhysics.Joint(p)
            t0, t1 = j.GetBody0Rel().GetTargets(), j.GetBody1Rel().GetTargets()
            if t0 and t1:
                edges.append((p, t0[0], t1[0]))
        self.limits = {}
        self.rest = {}
        self.joints = []
        seen = {self.root}
        queue = [self.root]
        while queue:
            cur = queue.pop(0)
            for p, a, b in edges:
                if cur not in (a, b):
                    continue
                child = b if cur == a else a
                if child in seen:
                    continue
                seen.add(child)
                queue.append(child)
                jt = _Joint()
                jt.parent, jt.child = cur, child
                j = UsdPhysics.Joint(p)
                if child == b:
                    local = _frame(j.GetLocalPos1Attr().Get(), j.GetLocalRot1Attr().Get())
                else:
                    local = _frame(j.GetLocalPos0Attr().Get(), j.GetLocalRot0Attr().Get())
                t_p = self._rest_world(stage.GetPrimAtPath(cur))
                t_c = self._rest_world(stage.GetPrimAtPath(child))
                t_j = t_c @ local
                jt.A = np.linalg.inv(t_p) @ t_j
                jt.B = np.linalg.inv(t_j) @ t_c
                jt.axis = None
                jt.name = p.GetName()
                if p.IsA(UsdPhysics.RevoluteJoint):
                    jt.axis = UsdPhysics.RevoluteJoint(p).GetAxisAttr().Get()
                    lo = j.GetPrim().GetAttribute("physics:lowerLimit").Get()
                    hi = j.GetPrim().GetAttribute("physics:upperLimit").Get()
                    self.limits[jt.name] = (math.radians(lo), math.radians(hi))
                self.joints.append(jt)
        self.bodies = {self.root} | {jt.child for jt in self.joints}
        for path in self.bodies:
            self.rest[path] = self._rest_world(stage.GetPrimAtPath(path))
        self.rest_all = {}
        for p in Usd.PrimRange(g1):
            self.rest_all[p.GetPath()] = self._rest_world(p)
        self.log(f"G1 rig: root={self.root}, bodies={len(self.bodies)}, revolute={len(self.limits)}")

    def _path(self, suffix):
        for path in self.bodies:
            if path.name == suffix:
                return path
        raise KeyError(suffix)

    def fk(self, q, base):
        t = {self.root: base}
        for jt in self.joints:
            r = _rot_axis(jt.axis, q.get(jt.name, 0.0)) if jt.axis else np.eye(4)
            t[jt.child] = t[jt.parent] @ jt.A @ r @ jt.B
        return t

    def base_pose(self, x, y, z, yaw):
        r0 = self.rest[self.root]
        base = np.eye(4)
        base[:3, :3] = _rot_z(yaw) @ r0[:3, :3]
        base[:3, 3] = [x, y, z]
        return base

    def _grounded(self, q, x, y, yaw):
        base = self.base_pose(x, y, self.rest[self.root][2, 3], yaw)
        t = self.fk(q, base)
        low = min(t[self.ankles[0]][2, 3], t[self.ankles[1]][2, 3])
        dz = ANKLE_HEIGHT - low
        base[2, 3] += dz
        return base

    # ----- calibration of hand geometry -----------------------------------
    def _close_values(self, side, frac):
        q = {}
        for name, (lo, hi) in self.limits.items():
            if not name.startswith(f"{side}_hand_"):
                continue
            lim = hi if abs(hi) > abs(lo) else lo
            if "thumb_0" in name:
                q[name] = 0.0
            elif "thumb_1" in name:
                q[name] = 0.5 * lim * frac
            elif "thumb_2" in name:
                q[name] = 0.8 * lim * frac
            elif name.endswith("_0_joint"):
                q[name] = 0.7 * lim * frac
            else:
                q[name] = 0.85 * lim * frac
        return q

    def _calibrate(self):
        self.ankles = (self._path("left_ankle_roll_link"), self._path("right_ankle_roll_link"))
        self.ankle_rest_z = min(self.rest[a][2, 3] for a in self.ankles)
        self.palm = {s: self._path(f"{s}_hand_palm_link") for s in ("left", "right")}
        self.finger_idx = self._path("right_hand_index_1_link")
        palm_rest = self.rest[self.palm["right"]]
        inv = np.linalg.inv(palm_rest)
        tips = [self.rest[p][:3, 3] for p in self.bodies
                if p.name.startswith("right_hand_") and p.name.endswith("_1_link")
                and "thumb" not in p.name]
        tip_local = inv[:3, :3] @ np.mean(tips, axis=0) + inv[:3, 3]
        f = tip_local / np.linalg.norm(tip_local)
        base = self.rest[self.root]
        t_open = self.fk({}, base)[self.finger_idx]
        t_closed = self.fk(self._close_values("right", 1.0), base)[self.finger_idx]
        delta = inv[:3, :3] @ (t_closed[:3, 3] - t_open[:3, 3])
        delta -= f * float(delta @ f)
        c = delta / np.linalg.norm(delta)
        self.f_local, self.c_local = f, c
        self.grasp_local = f * 0.075 + c * 0.045
        self.log(f"Hand frame: finger_dir={np.round(f, 3)} curl_dir={np.round(c, 3)}")

        stand = self.stand_q()
        self.stand_base = self._grounded(stand, END_X, 0.0, 0.0)
        self.walk_pelvis_z = self.stand_base[2, 3]

        q = dict(stand)
        sp = "right_shoulder_pitch_joint"
        wrist = self._path("right_wrist_yaw_link")
        x0 = self.fk(q, self.stand_base)[wrist][0, 3]
        q[sp] = 0.4
        x1 = self.fk(q, self.stand_base)[wrist][0, 3]
        self.arm_forward_sign = 1.0 if x1 > x0 else -1.0
        self.log(f"Shoulder pitch + moves wrist x by {x1 - x0:+.3f} (forward sign {self.arm_forward_sign:+.0f})")

    def stand_q(self):
        q = {}
        for side in ("left", "right"):
            q[f"{side}_hip_pitch_joint"] = STAND_HIP
            q[f"{side}_knee_joint"] = STAND_KNEE
            q[f"{side}_ankle_pitch_joint"] = -(STAND_HIP + STAND_KNEE)
        q["left_shoulder_roll_joint"] = 0.12
        q["left_elbow_joint"] = 0.4
        q.update(READY)
        return q

    # ----- inverse kinematics --------------------------------------------
    def _palm_state(self, q):
        t = self.fk(q, self.stand_base)[self.palm["right"]]
        r = t[:3, :3]
        return r @ self.grasp_local + t[:3, 3], r @ self.f_local, r @ self.c_local

    def solve_ik(self, target, f_t, c_t, seeds, w_o=0.12):
        names = IK_JOINTS
        lo = np.array([self.limits[n][0] for n in names])
        hi = np.array([self.limits[n][1] for n in names])
        lo[0], hi[0] = -0.3, 0.35
        x_ready = np.array([READY[n] for n in names])
        base_q = self.stand_q()

        def resid(x):
            q = dict(base_q)
            q.update(zip(names, x))
            g, f, c = self._palm_state(q)
            return np.concatenate([g - target, w_o * (f - f_t), w_o * (c - c_t), 0.02 * (x - x_ready)])

        best = None
        for x in seeds:
            x = np.clip(np.array(x, dtype=float), lo, hi)
            r = resid(x)
            cost, lam = r @ r, 1e-2
            for _ in range(45):
                jac = np.empty((len(r), len(x)))
                for i in range(len(x)):
                    xp = x.copy()
                    xp[i] += 1e-4
                    jac[:, i] = (resid(xp) - r) / 1e-4
                step = np.linalg.solve(jac.T @ jac + lam * np.eye(len(x)), -jac.T @ r)
                xn = np.clip(x + step, lo, hi)
                rn = resid(xn)
                if rn @ rn < cost:
                    x, r, cost, lam = xn, rn, rn @ rn, max(lam * 0.3, 1e-6)
                else:
                    lam *= 4
                if np.linalg.norm(step) < 1e-6:
                    break
            if best is None or cost < best[0]:
                best = (cost, x)
        return best[1], best[0]

    def _plan_arm(self):
        rng = np.random.RandomState(3)
        names = IK_JOINTS
        lo = np.array([self.limits[n][0] for n in names])
        hi = np.array([self.limits[n][1] for n in names])
        seeds = [[READY[n] for n in names]] + [rng.uniform(lo * 0.6, hi * 0.6) for _ in range(7)]
        apple = self.apple_rest
        f_t = np.array([1.0, 0.0, 0.0])
        candidates = {
            "palm faces +y": np.array([0.0, 1.0, 0.0]),
            "palm faces down": np.array([0.0, 0.0, -1.0]),
            "palm diagonal": np.array([0.0, 0.7071, -0.7071]),
        }
        best = None
        for label, c_t in candidates.items():
            x, cost = self.solve_ik(apple, f_t, c_t, seeds)
            self.log(f"Grasp IK '{label}': cost={cost:.5f}")
            if best is None or cost < best[0]:
                best = (cost, x, label, c_t)
        _, x_grasp, label, c_t = best
        self.log(f"Using grasp orientation: {label}")
        warm = [x_grasp]
        x_pre, _ = self.solve_ik(apple + np.array([-0.12, 0.0, 0.14]), f_t, c_t, warm)
        x_lift, _ = self.solve_ik(apple + np.array([-0.10, 0.02, 0.24]), f_t, c_t, warm)
        x_place, _ = self.solve_ik(
            self.drop_position + np.array([-0.06, 0.0, 0.18]), f_t, c_t, warm
        )
        x_release, _ = self.solve_ik(
            self.drop_position + np.array([-0.04, 0.0, 0.07]), f_t, c_t, [x_place]
        )
        err_g = np.linalg.norm(self._palm_state(self._q_from(x_grasp))[0] - apple)
        self.log(f"Grasp IK position error: {err_g * 1000:.1f} mm")
        x_ready = np.array([READY[n] for n in names])
        self.waypoints = [
            (WALK_FRAMES, x_ready), (PRE_FRAME, x_pre), (GRASP_FRAME, x_grasp),
            (ATTACH_FRAME, x_grasp), (LIFT_FRAME, x_lift), (PLACE_FRAME, x_place),
            (RELEASE_FRAME, x_release),
        ]

    def _q_from(self, x):
        q = self.stand_q()
        q.update(zip(IK_JOINTS, x))
        return q

    # ----- per-frame pose --------------------------------------------------
    def _walk_envelope(self, f):
        u = f / WALK_FRAMES
        if u >= 1.0:
            return 0.0
        return min(1.0, u / 0.12, (1.0 - u) / 0.12)

    def _arm_x(self, f):
        if f <= WALK_FRAMES:
            return self.waypoints[0][1]
        for (f0, x0), (f1, x1) in zip(self.waypoints, self.waypoints[1:]):
            if f <= f1:
                return x0 + (x1 - x0) * _smooth((f - f0) / (f1 - f0))
        return self.waypoints[-1][1]

    def _finger_frac(self, f):
        if f < RELEASE_FRAME:
            return _smooth((f - (GRASP_FRAME + 2)) / (ATTACH_FRAME - GRASP_FRAME))
        return 1.0 - _smooth((f - RELEASE_FRAME) / 12.0)

    def _gait(self, f):
        if f <= WALK_FRAMES:
            u = f / WALK_FRAMES
            return min(1.0, u / 0.12, (1.0 - u) / 0.12) if u < 1.0 else 0.0, 6.0 * math.pi * u
        if f >= TURN_START:
            u = (f - TURN_START) / (END_FRAME - TURN_START)
            env = min(1.0, u / 0.1, (1.0 - u) / 0.1)
            return max(0.0, env), 8.0 * math.pi * u + math.pi
        return 0.0, 0.0

    def _base_xy_yaw(self, f):
        if f <= WALK_FRAMES:
            u = f / WALK_FRAMES
            return START_X + (END_X - START_X) * (0.6 * u + 0.4 * _smooth(u)), 0.0
        yaw = math.pi * _smooth((f - TURN_START) / (TURN_END - TURN_START))
        px = END_X
        if f > TURN_END:
            px = END_X - AWAY_DIST * _smooth((f - TURN_END) / (END_FRAME - TURN_END))
        return px, yaw

    def pose(self, f):
        q = self.stand_q()
        env, phase = self._gait(f)
        for side, offset in (("right", 0.0), ("left", math.pi)):
            ph = phase + offset
            fwd = 0.30 * env * math.sin(ph)
            q[f"{side}_hip_pitch_joint"] = STAND_HIP - fwd
            q[f"{side}_knee_joint"] = STAND_KNEE + 0.15 * env + 0.75 * env * max(0.0, math.cos(ph))
            q[f"{side}_ankle_pitch_joint"] = -(q[f"{side}_hip_pitch_joint"] + q[f"{side}_knee_joint"])
        swing = 0.35 * env * math.sin(phase) * self.arm_forward_sign
        q["right_shoulder_pitch_joint"] = READY["right_shoulder_pitch_joint"] - swing
        q["left_shoulder_pitch_joint"] = swing
        q["waist_yaw_joint"] = 0.08 * env * math.sin(phase)
        x = self._arm_x(f)
        if f > WALK_FRAMES:
            q.update(zip(IK_JOINTS, x))
        q.update(self._close_values("right", self._finger_frac(f)))
        px, yaw = self._base_xy_yaw(f)
        base = self._grounded(q, px, 0.0, yaw)
        return q, base

    def apple_position(self, f, transforms):
        if f < ATTACH_FRAME:
            return self.apple_rest
        if f >= RELEASE_FRAME:
            return self.drop_position
        palm = self.palm["right"]
        if not hasattr(self, "_attach_inv"):
            _, base = self.pose(ATTACH_FRAME)
            self._attach_inv = np.linalg.inv(self.fk(self.pose(ATTACH_FRAME)[0], base)[palm])
        rel = self._attach_inv @ np.append(self.apple_rest, 1.0)
        return (transforms[palm] @ rel)[:3]

    def camera(self, f):
        wide = (np.array([-0.9, -4.2, 1.7]), np.array([-0.9, 0.0, 0.8]))
        close = (np.array([0.45, -2.0, 1.6]), np.array([0.0, -0.05, 0.9]))
        a = _smooth((f - (WALK_FRAMES - 25)) / 45.0)
        eye = wide[0] + (close[0] - wide[0]) * a
        target = wide[1] + (close[1] - wide[1]) * a
        b = _smooth((f - TURN_START) / (TURN_END - TURN_START))
        px, _ = self._base_xy_yaw(f)
        follow = (np.array([px + 0.8, -3.3, 1.5]), np.array([px, 0.0, 0.85]))
        return eye + (follow[0] - eye) * b, target + (follow[1] - target) * b

    # ----- authoring -------------------------------------------------------
    def _world_of(self, path, targets):
        if path in targets:
            return targets[path]
        if path in self._cache:
            return self._cache[path]
        parent = path.GetParentPath()
        if path not in self.rest_all or parent not in self.rest_all:
            world = self.rest_all.get(path, np.eye(4))
        else:
            local = np.linalg.inv(self.rest_all[parent]) @ self.rest_all[path]
            world = self._world_of(parent, targets) @ local
        self._cache[path] = world
        return world

    def author(self):
        self._plan_arm()
        stage = self.stage
        ops = {}
        for path in self.bodies:
            xf = UsdGeom.Xformable(stage.GetPrimAtPath(path))
            xf.ClearXformOpOrder()
            ops[path] = xf.AddTransformOp()
        apple_xf = UsdGeom.Xformable(self.apple_prim)
        apple_op = None
        for op in apple_xf.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                apple_op = op
        if apple_op is None:
            apple_op = apple_xf.AddTranslateOp()

        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(END_FRAME)
        stage.SetTimeCodesPerSecond(FPS)
        stage.SetFramesPerSecond(FPS)
        for f in range(END_FRAME + 1):
            q, base = self.pose(f)
            targets = self.fk(q, base)
            self._cache = {}
            for path in self.bodies:
                parent_world = self._world_of(path.GetParentPath(), targets)
                local = np.linalg.inv(parent_world) @ targets[path]
                ops[path].Set(_gf(local), Usd.TimeCode(f))
            pos = self.apple_position(f, targets)
            apple_op.Set(Gf.Vec3d(*[float(v) for v in pos]), Usd.TimeCode(f))
            if f in (0, WALK_FRAMES, GRASP_FRAME, ATTACH_FRAME, END_FRAME):
                g, _, _ = self._palm_state_at(targets)
                self.log(
                    f"Frame {f}: pelvis={np.round(targets[self.root][:3, 3], 3)} "
                    f"grasp_pt={np.round(g, 3)} apple={np.round(pos, 3)}"
                )

    def export_raw_demonstration(self, output_path, task_description):
        """Export the authored trajectory for later G1 dataset conversion.

        This intentionally records raw named joints rather than a GR00T action
        vector. A converter must validate the Unitree joint order and pair each
        state with a rendered camera frame before the episode is used for
        post-training.
        """
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joint_names = list(GROOT_FULL_BODY_JOINT_ORDER)
        missing_joints = [name for name in joint_names if name not in self.limits]
        if missing_joints:
            raise RuntimeError(
                "The G1 rig does not expose all required GR00T joints: "
                + ", ".join(missing_joints)
            )
        frames = []
        for frame in range(END_FRAME + 1):
            state, base = self.pose(frame)
            next_state, _ = self.pose(min(frame + 1, END_FRAME))
            transforms = self.fk(state, base)
            frames.append(
                {
                    "frame": frame,
                    "timestamp": frame / FPS,
                    "joint_position": [float(state.get(name, 0.0)) for name in joint_names],
                    "next_joint_position": [
                        float(next_state.get(name, 0.0)) for name in joint_names
                    ],
                    "base_position": [float(value) for value in base[:3, 3]],
                    "apple_position": [
                        float(value) for value in self.apple_position(frame, transforms)
                    ],
                }
            )
        episode = {
            "schema_version": 1,
            "recording_type": "raw_simulated_demonstration",
            "training_ready": False,
            "reason_not_training_ready": (
                "Camera frames and a validated Unitree G1 joint-to-modality map "
                "are required before GR00T LeRobot conversion."
            ),
            "task_description": task_description,
            "fps": FPS,
            "joint_names": joint_names,
            "target_bin": "apple",
            "target_drop_position": [float(value) for value in self.drop_position],
            "success_frame": RELEASE_FRAME,
            "success": True,
            "frames": frames,
        }
        with open(output_path, "w", encoding="utf-8") as stream:
            json.dump(episode, stream, separators=(",", ":"))
        self.log(
            f"Exported raw demonstration: {output_path} "
            f"({len(frames)} frames, {len(joint_names)} joints)"
        )

    def _palm_state_at(self, targets):
        t = targets[self.palm["right"]]
        r = t[:3, :3]
        return r @ self.grasp_local + t[:3, 3], r @ self.f_local, r @ self.c_local
