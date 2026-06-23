#!/usr/bin/env python3
# Copyright (c) 2025 PAL Robotics S.L. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from dataclasses import dataclass

from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

from launch.actions import DeclareLaunchArgument, SetLaunchConfiguration, OpaqueFunction

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch_pal.include_utils import include_scoped_launch_py_description
from launch_pal.arg_utils import LaunchArgumentsBase
from launch_pal.robot_arguments import CommonArgs
from kangaroo_description.launch_arguments import KangarooArgs

from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)

@dataclass(frozen=True)
class LaunchArguments(LaunchArgumentsBase):

    ## Common

    # ["True", "False"]
    use_sim_time: DeclareLaunchArgument = CommonArgs.use_sim_time

    # ["false", "position", "motor"]
    mj_control: DeclareLaunchArgument = CommonArgs.mj_control

    # ["True", "False"]
    moveit: DeclareLaunchArgument = CommonArgs.moveit
    
    ## Kangaroo specific

    # ["mujoco-ros2-control", "mujoco", "no-simulation"]
    sim_type: DeclareLaunchArgument = KangarooArgs.sim_type
     
    # ["True", "False"]
    use_mimic: DeclareLaunchArgument = KangarooArgs.use_mimic

    # ["mesh", "capsule"]
    collision_type: DeclareLaunchArgument = KangarooArgs.collision_type

    # [True, False]
    has_head: DeclareLaunchArgument = KangarooArgs.has_head
    
    # [True, False]
    has_pelvis: DeclareLaunchArgument = KangarooArgs.has_pelvis

    # ["no-arm", "4dof", "5dof", "7dof"]
    arm_type: DeclareLaunchArgument = KangarooArgs.arm_type
    
    # ["fixed", "detachable"]
    feet_type: DeclareLaunchArgument = KangarooArgs.feet_type
    
    # ["fake-forearm", "ft-gripper", "gripper", "RA8D"]
    end_effector_right: DeclareLaunchArgument = KangarooArgs.end_effector_right
    end_effector_left: DeclareLaunchArgument = KangarooArgs.end_effector_left

    # Fixation type ["crane", "fixed", "floating"]
    fixation_type: DeclareLaunchArgument = KangarooArgs.fixation_type

    # FT sensor type ["no-ft-sensor", "ati"]
    ft_sensor_right: DeclareLaunchArgument = KangarooArgs.ft_sensor_right
    ft_sensor_left: DeclareLaunchArgument = KangarooArgs.ft_sensor_left

    # Ankle FT sensor type ["no-ft-sensor", "ati"]
    ankle_ft_right: DeclareLaunchArgument = KangarooArgs.ankle_ft_right
    ankle_ft_left: DeclareLaunchArgument = KangarooArgs.ankle_ft_left

    # Torso IMU models ["orientus", "microstrain", "no-imu"]
    torso_imu_model: DeclareLaunchArgument = KangarooArgs.torso_imu_model

    # Base IMU models ["microstrain", "no-imu"]
    base_imu_model: DeclareLaunchArgument = KangarooArgs.base_imu_model


def generate_launch_description():

    # Create the launch description and populate
    ld = LaunchDescription()
    launch_arguments = LaunchArguments()

    launch_arguments.add_to_launch_description(ld)

    declare_actions(ld, launch_arguments)

    return ld


def declare_actions(
    launch_description: LaunchDescription, launch_args: LaunchArguments
):
    launch_description.add_action(SetLaunchConfiguration("use_sim_time", "True"))
    launch_description.add_action(SetLaunchConfiguration("sim_type", "mujoco-ros2-control"))
    launch_description.add_action(SetLaunchConfiguration("mj_control", "motor"))

    # MuJoCo scene
    launch_description.add_action(
        DeclareLaunchArgument(
            "world_name",
            default_value="empty",
            description="MuJoCo scene to load (only from the pregenerated options)",
        )
    )

    # Robot Bringup
    bringup = include_scoped_launch_py_description(
        pkg_name="kangaroo_bringup",
        paths=["launch", "kangaroo_bringup.launch.py"],
        launch_arguments={
            "use_sim_time": launch_args.use_sim_time,
            "use_mimic": launch_args.use_mimic,
            "collision_type": launch_args.collision_type,
            "sim_type": launch_args.sim_type,
            "mj_control": launch_args.mj_control,
            "has_head": launch_args.has_head,
            "has_pelvis": launch_args.has_pelvis,
            "arm_type": launch_args.arm_type,
            "feet_type": launch_args.feet_type,
            "end_effector_right": launch_args.end_effector_right,
            "end_effector_left": launch_args.end_effector_left,
            "ft_sensor_right": launch_args.ft_sensor_right,
            "ft_sensor_left": launch_args.ft_sensor_left,
            "fixation_type": launch_args.fixation_type,
            "ankle_ft_left": launch_args.ankle_ft_left,
            "ankle_ft_right": launch_args.ankle_ft_right,
            "torso_imu_model": launch_args.torso_imu_model,
            "base_imu_model": launch_args.base_imu_model
        },
    )

    launch_description.add_action(bringup)

    # Launch the conversion node.
    #
    # If a previously generated MJCF already exists on disk, publish it directly with
    # the lightweight publish_mjcf.py node (no URDF->MJCF conversion, no Python venv
    # bootstrap). Otherwise fall back to the converter, which regenerates the MJCF
    # from the robot_description and publishes it on the same topic.
    def converter_node_setup(context, *args, **kwargs):
        fixation_type = LaunchConfiguration("fixation_type").perform(context)
        arm_type = LaunchConfiguration("arm_type").perform(context)
        end_effector_right = LaunchConfiguration("end_effector_right").perform(context)
        end_effector_left = LaunchConfiguration("end_effector_left").perform(context)
        feet_type = LaunchConfiguration("feet_type").perform(context)
        world_name = LaunchConfiguration("world_name").perform(context)

        pkg_share = FindPackageShare("kangaroo_mujoco").perform(context)
        assets_cache_dir = os.path.join(
            pkg_share,
            "models",
            f"assets",
        )
        mjcf_file = os.path.join(
            pkg_share,
            "models",
            f"mjcf_data_{arm_type}_{end_effector_right}_{end_effector_left}_{feet_type}_{world_name}",
            "mujoco_description_formatted.xml")

        if os.path.isfile(mjcf_file) and os.path.getsize(mjcf_file) > 0:
            # Pre-generated MJCF found: publish it directly.
            return [Node(
                package="kangaroo_mujoco",
                executable="publish_mjcf.py",
                output="both",
                emulate_tty=True,
                arguments=[mjcf_file, "mujoco_robot_description"],
            )]

        # No cached MJCF: regenerate from the robot_description and publish it.
        args_list = [
            "-p", "mujoco_robot_description",
            "-a", assets_cache_dir,
            "--convert_stl_to_obj",
            "--no-fuse",
        ]
        if fixation_type == "floating":
            args_list.append("-f")

        return [Node(
            package="mujoco_ros2_control",
            executable="robot_description_to_mjcf.sh",
            output="both",
            emulate_tty=True,
            arguments=args_list,
        )]

    launch_description.add_action(OpaqueFunction(function=converter_node_setup))


    parameters_file = PathJoinSubstitution([FindPackageShare("kangaroo_mujoco"), "config", "controller_manager.yaml"]) 
    # Mujoco Ros2 Control Simulation
    control_node = Node(
        package="mujoco_ros2_control",
        executable="ros2_control_node",
        emulate_tty=True,
        output="both",
        parameters=[
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
            parameters_file,
        ],
    )

    launch_description.add_action(control_node)
    
    # Moveit2
    move_group = include_scoped_launch_py_description(
        pkg_name='kangaroo_moveit_config',
        paths=['launch', 'move_group.launch.py'],
        launch_arguments={
            "use_sim_time": launch_args.use_sim_time,
            "use_mimic": launch_args.use_mimic,
            "collision_type": launch_args.collision_type,
            "sim_type": launch_args.sim_type,
            "mj_control": launch_args.mj_control,
            "has_head": launch_args.has_head,
            "has_pelvis": launch_args.has_pelvis,
            "arm_type": launch_args.arm_type,
            "feet_type": launch_args.feet_type,
            "end_effector_right": launch_args.end_effector_right,
            "end_effector_left": launch_args.end_effector_left,
            "ft_sensor_right": launch_args.ft_sensor_right,
            "ft_sensor_left": launch_args.ft_sensor_left,
            "fixation_type": launch_args.fixation_type,
            "ankle_ft_left": launch_args.ankle_ft_left,
            "ankle_ft_right": launch_args.ankle_ft_right,
            "torso_imu_model": launch_args.torso_imu_model,
            "base_imu_model": launch_args.base_imu_model
        },
        condition=IfCondition(LaunchConfiguration('moveit')))
    # To be added once kangaroo_moveit_config is updated
    # launch_description.add_action(move_group)

    return










