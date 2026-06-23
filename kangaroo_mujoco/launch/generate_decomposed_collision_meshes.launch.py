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

from dataclasses import dataclass

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetLaunchConfiguration, LogInfo, RegisterEventHandler, Shutdown, OpaqueFunction
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, TextSubstitution

from launch_ros.actions import Node

from launch_pal.include_utils import include_scoped_launch_py_description
from launch_pal.arg_utils import LaunchArgumentsBase

from launch_pal.robot_arguments import CommonArgs
from kangaroo_description.launch_arguments import KangarooArgs


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

    # Robot State Publisher
    robot_state_publisher = include_scoped_launch_py_description(
        pkg_name='kangaroo_description',
        paths=['launch', 'robot_state_publisher.launch.py'],
        launch_arguments={
            "use_sim_time": launch_args.use_sim_time,
            "collision_type": launch_args.collision_type,
            "sim_type": launch_args.sim_type,
            "mj_control": launch_args.mj_control,
            "has_head": launch_args.has_head,
            "has_pelvis": launch_args.has_pelvis,
            "arm_type": launch_args.arm_type,
            "feet_type": launch_args.feet_type,
            "end_effector_right": launch_args.end_effector_right,
            "end_effector_left": launch_args.end_effector_left,
            "fixation_type": launch_args.fixation_type,
            "ankle_ft_left": launch_args.ankle_ft_left,
            "ankle_ft_right": launch_args.ankle_ft_right,
            "torso_imu_model": launch_args.torso_imu_model,
            "base_imu_model": launch_args.base_imu_model
            })

    launch_description.add_action(robot_state_publisher)
    
    # Launch the conversion node
    def converter_node_setup(context, *args, **kwargs):
        fixation_type = LaunchConfiguration("fixation_type").perform(context)
        args_list = [
            "-s", 
            "-o", [TextSubstitution(text="mjcf_data_"), LaunchConfiguration("arm_type"), TextSubstitution(text="_"), LaunchConfiguration("end_effector_right"), TextSubstitution(text="_"), LaunchConfiguration("end_effector_left"), TextSubstitution(text="_"), LaunchConfiguration("feet_type")],
            "--convert_stl_to_obj",
            "--no-fuse",
        ]
        if fixation_type == "floating":
            args_list.append("-f")
        
        converter_node = Node(
            package="mujoco_ros2_control",
            executable="robot_description_to_mjcf.sh",
            output="both",
            emulate_tty=True,
            arguments=args_list,
            )
        
        exit_event_handler = RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=converter_node,
                on_exit=[
                    LogInfo(msg='Generation finished! Stopping everything...'),
                    Shutdown()
                ]
            )
        )

        return [converter_node, exit_event_handler]
    
    launch_description.add_action(OpaqueFunction(function=converter_node_setup))
     
    return










