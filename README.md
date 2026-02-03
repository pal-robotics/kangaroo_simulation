# Kangaroo Simulation Package

This metapackage contains the simulation resources and configurations for the Kangaroo robot.

## Supported Simulators

*   **MuJoCo**: The primary supported simulator is [mujoco_ros2_control](https://github.com/ros-controls/mujoco_ros2_control). It provides a high-fidelity physics simulation fully integrated with `ros2_control`, allowing for seamless transition between simulation and real hardware using the same controllers.

## Packages

*   `kangaroo_mujoco`: Contains launch files and configurations specific to the MuJoCo simulation environment.
*   `kangaroo_simulation`: The metapackage definition.


