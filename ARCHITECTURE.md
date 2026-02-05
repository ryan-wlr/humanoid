# Architecture Documentation

This document provides a technical overview of the Unitree G1 Apple Grabbing simulation architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Isaac Sim Environment                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Physics Engine                        │  │
│  │  - Collision detection                                    │  │
│  │  - Rigid body dynamics                                    │  │
│  │  - Contact simulation                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Scene Components                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ Unitree  │  │   Desk   │  │  Apple   │               │  │
│  │  │    G1    │  │          │  │          │               │  │
│  │  │  Robot   │  │          │  │    🍎    │               │  │
│  │  └──────────┘  └──────────┘  └──────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Control System (Python)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  simulation.py - Main Simulation Loop                     │  │
│  │  ├─ Scene Setup                                           │  │
│  │  ├─ World Step (Physics Tick)                            │  │
│  │  └─ Rendering                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  robot_controller.py - State Machine                      │  │
│  │                                                            │  │
│  │     IDLE → APPROACHING → GRASPING                         │  │
│  │              ↓                                             │  │
│  │     DONE ← RETRACTING ← LIFTING                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  object_detection.py - Apple Localization                 │  │
│  │  ├─ Detect apple position                                 │  │
│  │  ├─ Calculate grasp pose                                  │  │
│  │  └─ Verify grasp success                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Initialization Phase

```
launch/g1_manipulation.launch.py
    ↓
scripts/simulation.py
    ↓
AppleGrabbingSimulation.__init__()
    ↓
setup_scene()
    ├─ add_default_ground_plane()
    ├─ create desk (DynamicCuboid)
    ├─ create apple (VisualSphere)
    └─ setup_robot()
        └─ load G1 model or use placeholder
    ↓
world.reset()
    ↓
initialize_controller()
    └─ UnitreeG1Controller(robot, target_position)
```

### 2. Runtime Loop

```
while simulation_app.is_running():
    world.step(render=True)
        ├─ Physics simulation (dt step)
        ├─ Update all prims
        └─ Render scene
    
    if world.is_playing():
        controller.update(dt)
            ├─ State machine logic
            ├─ Generate joint commands
            └─ Apply actions to robot
        
        Print status (every 100 frames)
```

## State Machine Details

### State Transitions

```
IDLE (1.0s wait)
  │
  ├─ Time elapsed > 1.0s
  │
  ↓
APPROACHING (2.0s)
  │
  ├─ Move arm towards apple
  ├─ Interpolate joint positions
  │
  ↓
GRASPING (2.0s)
  │
  ├─ Close gripper fingers
  ├─ Apply closing motion
  │
  ↓
LIFTING (2.0s)
  │
  ├─ Raise arm vertically
  ├─ Maintain grip
  │
  ↓
RETRACTING (2.0s)
  │
  ├─ Return to initial pose
  ├─ Interpolate back
  │
  ↓
DONE
  │
  └─ Task complete
```

### State Actions

Each state performs specific actions:

| State | Joint Control | Gripper | Purpose |
|-------|--------------|---------|---------|
| IDLE | Hold initial | Open | Wait before starting |
| APPROACHING | Move forward | Open | Reach towards apple |
| GRASPING | Hold position | Close | Grab the apple |
| LIFTING | Move upward | Closed | Lift the apple |
| RETRACTING | Move backward | Closed | Return to neutral |
| DONE | Hold final | Closed | Task complete |

## Configuration System

### Robot Configuration (`config/robot_config.yaml`)

```yaml
robot:
  - Physical parameters (height, weight)
  - Arm DOF and reach
  - Gripper specifications
  
control:
  - PID gains
  - Velocity/acceleration limits
  
initial_pose:
  - Default joint angles
```

### Scene Configuration (`config/scene_config.yaml`)

```yaml
scene:
  desk:
    - Position, size, color, mass
  
  apple:
    - Position, radius, color, mass
  
  robot:
    - Initial placement
  
  camera & lighting:
    - View configuration
```

## Data Flow

### Object Detection Pipeline

```
AppleDetector.detect()
    ↓
apple.get_world_pose()
    ↓
position [x, y, z]
    ↓
get_grasp_pose()
    ↓
grasp_position (approach from above)
    ↓
UnitreeG1Controller.target_position
```

### Control Pipeline

```
Controller.update(dt)
    ↓
Check current state
    ↓
Execute state-specific function
    ↓
Calculate target joint positions
    ↓
ArticulationAction(joint_positions=...)
    ↓
robot.apply_action(action)
    ↓
Physics engine applies forces
    ↓
Robot moves
```

## Extension Points

### Adding New Features

1. **Vision-based Detection**
   - Add camera sensor to robot
   - Implement image processing in `object_detection.py`
   - Use RGB-D for 3D localization

2. **Inverse Kinematics**
   - Replace joint interpolation with IK solver
   - Add end-effector position control
   - Implement trajectory planning

3. **Multiple Objects**
   - Extend detection to handle multiple targets
   - Add object classification
   - Implement task sequencing

4. **Force Control**
   - Add force sensors to gripper
   - Implement adaptive grasping
   - Handle different object properties

### Customization Points

| Component | File | Purpose |
|-----------|------|---------|
| Scene layout | `config/scene_config.yaml` | Change positions, add objects |
| Robot params | `config/robot_config.yaml` | Tune control, modify DOF |
| State timing | `robot_controller.py` | Adjust phase durations |
| Detection logic | `object_detection.py` | Change detection method |
| Main loop | `simulation.py` | Add logging, metrics |

## Performance Considerations

### Optimization Strategies

1. **Physics Timestep**: Balance accuracy vs. speed
   - Smaller dt = more accurate but slower
   - Larger dt = faster but less stable

2. **Rendering**: Disable for headless testing
   - `world.step(render=False)` for faster execution

3. **Joint Control**: Use position vs. velocity control
   - Position: Simpler, more stable
   - Velocity: More realistic, requires tuning

4. **Collision Geometry**: Simplify for performance
   - Use simple shapes for collision
   - Detailed meshes for visuals only

## Debugging Guide

### Common Issues and Solutions

1. **Robot doesn't move**
   - Check: Controller initialized?
   - Check: Robot model loaded?
   - Debug: Print joint positions

2. **Gripper doesn't grasp**
   - Check: Gripper joint indices
   - Check: Contact geometry
   - Debug: Visualize forces

3. **Simulation is unstable**
   - Reduce physics timestep
   - Increase solver iterations
   - Check mass ratios

4. **Performance issues**
   - Profile physics vs. rendering
   - Reduce object complexity
   - Use LOD for distant objects

## Testing Strategy

### Unit Tests
- Test state transitions
- Test joint position calculations
- Test detection accuracy

### Integration Tests
- Test full manipulation sequence
- Test error recovery
- Test different object positions

### System Tests
- Run full simulation
- Measure success rate
- Profile performance

## Future Enhancements

1. **Machine Learning Integration**
   - Train policy with RL
   - Imitation learning from demonstrations
   - Vision-based grasping

2. **Multi-robot Coordination**
   - Synchronize multiple G1 robots
   - Collaborative manipulation
   - Task allocation

3. **Real Robot Transfer**
   - Domain randomization
   - Sim-to-real pipeline
   - Hardware interface

---

This architecture is designed to be modular, extensible, and maintainable for both research and production use cases.
