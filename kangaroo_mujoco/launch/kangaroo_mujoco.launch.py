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
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_pal.include_utils import include_scoped_launch_py_description
from launch_ros.actions import Node
from launch_pal.arg_utils import LaunchArgumentsBase, read_launch_argument
from kangaroo_description.launch_arguments import KangarooArgs
from launch_pal.robot_arguments import CommonArgs


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
    
    # ["ft-leg", "leg", "no-leg"]
    legs_type: DeclareLaunchArgument = KangarooArgs.legs_type
    
    # ["cover", "fake-forearm", "ft-gripper", "gripper", "RA8D"]
    end_effector_type: DeclareLaunchArgument = KangarooArgs.end_effector_type

    # Fixation type ["crane", "fixed", "floating"]
    fixation_type: DeclareLaunchArgument = KangarooArgs.fixation_type


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
    # Robot Bringup
    bringup = include_scoped_launch_py_description(
        pkg_name="kangaroo_bringup",
        paths=["launch", "kangaroo_bringup.launch.py"],
        launch_arguments={
            "use_sim_time": launch_args.use_sim_time,
            "use_mimic": launch_args.use_mimic,
            "collision_type": launch_args.collision_type,
            "sim_type": "mujoco-ros2-control",
            "mj_control": launch_args.mj_control,
            "has_head": launch_args.has_head,
            "has_pelvis": launch_args.has_pelvis,
            "arm_type": launch_args.arm_type,
            "legs_type": launch_args.legs_type,
            "end_effector_type": launch_args.end_effector_type,
            "fixation_type": launch_args.fixation_type,
        },
    )

    launch_description.add_action(bringup)

    # Mujoco Description
    launch_description.add_action(OpaqueFunction(
        function=mujoco_model_publisher))


    # Mujoco Ros2 Control Simulation
    control_node = Node(
        package="mujoco_ros2_simulation",
        executable="ros2_control_node",
        output="both",
        parameters=[
            {"use_sim_time": True},
        ],
    )

    launch_description.add_action(control_node)
    
    # # Moveit2
    # move_group = include_scoped_launch_py_description(
    #     pkg_name='kangaroo_moveit_config',
    #     paths=['launch', 'move_group.launch.py'],
    #     launch_arguments={
    #             "use_sim_time": launch_args.use_sim_time,
    #             "use_mimic": launch_args.use_mimic,
    #             "collision_type": launch_args.collision_type,
    #             "sim_type": "mujoco-ros2-control",
    #             "mj_control": launch_args.mj_control,
    #             "has_head": launch_args.has_head,
    #             "has_pelvis": launch_args.has_pelvis,
    #             "arm_type": launch_args.arm_type,
    #             "legs_type": launch_args.legs_type,
    #             "end_effector_type": launch_args.end_effector_type,
    #             "fixation_type": launch_args.fixation_type,
    #     },
    #     condition=IfCondition(LaunchConfiguration('moveit')))

    # launch_description.add_action(move_group)

    return

def mujoco_model_publisher(context, *args, **kwargs):
    xacro_input_args = {
        "robot_name": "kangaroo",
        "collision_type": read_launch_argument("collision_type", context),
        "sim_type": "mujoco",
        "mj_control": read_launch_argument("mj_control", context),
        "fixation_type": read_launch_argument("fixation_type", context),
        "legs_type": read_launch_argument("legs_type", context),
        "arm_type": read_launch_argument("arm_type", context),
        "end_effector_type": read_launch_argument("end_effector_type", context),
        "has_head": read_launch_argument("has_head", context),
        "has_pelvis": read_launch_argument("has_pelvis", context),
    }

    model_pub = Node(
        package='pal_mujoco_model_loader_ros',
        executable='publisher',
        parameters=[xacro_input_args],
        output='screen'
    )

    return [model_pub]





















