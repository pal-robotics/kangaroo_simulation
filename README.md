# Kangaroo Simulation Package
This package provides the ROS2 launchfiles and config files that allow launching Kangaroo Robot simulation with its different configurations.
The current supported simulations are:
- kangaroo_mujoco: MuJoCo's simulation integrated with ROS2 Control.

**NOTE: This package is under development. Expect braking changes and missing features.**

## Installation

**Clone packages**
- kangaroo robot (branch sma/humble_devel):
```bash
git clone git@gitlab:robots/kangaroo_robot.git
cd kangaroo_robot/ && git checkout sma/humble-devel
```
- kangaroo_simulation (branch humble_devel):
```bash
git clone git@gitlab:robots/kangaroo_simulation.git
```
- kangaroo_moveit_config (branch sma/humble-devel):
```bash
git clone git@gitlab:robots/kangaroo_moveit_config.git
cd kangaroo_moveit_config/ && git checkout sma/humble-devel
```
- pal_mujoco_scenes (branch humble-devel):
```bash
git clone git@gitlab:common/pal_mujoco_scenes.git
```
- mujoco_ros2_control (branch fix/make_mjcf_outputpath_bug):
```bash
git clone git@github.com:pal-robotics-forks/mujoco_ros2_control.git
cd mujoco_ros2_control && git checkout fix/make_mjcf_outputpath_bug
```

**Compile your package**
If compilation crashes due to missing package, please install them all manually using sudo apt install <package_name> 

**Launch simulaiton**
Once compiled, source your workspace and follow the next steps:

- **1st**. Generate the model optimized meshes you will use. By default is is the kangaroo with pelvis and 4dof arm:
```bash
ros2 launch kangaroo_mujoco generate_decomposed_collision_meshes.launch.py
```
If you want to generate for a specific configuration use the following arguments:
```bash
# example 5dof arm
ros2 launch kangaroo_mujoco generate_decomposed_collision_meshes.launch.py arm_type:=5dof end_effector_type:=no-end-effector

# example 7dof arm
ros2 launch kangaroo_mujoco generate_decomposed_collision_meshes.launch.py arm_type:=7dof end_effector_type:=no-end-effector
```
You need to generate them before launching the simulation, otherwise the simulation will optimize the meshes each time you run it, which takes quite some time.

- **2nd**. Launch simulation:
```bash
# default 4dof configuration
ros2 launch kangaroo_mujoco kangaroo_mujoco.launch.py

# 5dof arm configuration
ros2 launch kangaroo_mujoco kangaroo_mujoco.launch.py arm_type:=5dof end_effector_type:=no-end-effector

# 7dof arm configuration 
ros2 launch kangaroo_mujoco kangaroo_mujoco.launch.py arm_type:=7dof end_effector_type:=no-end-effector
```