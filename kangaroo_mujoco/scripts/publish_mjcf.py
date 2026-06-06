#!/usr/bin/env python3
# Copyright (c) 2026 PAL Robotics S.L. All rights reserved.
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

"""Publish a pre-generated MuJoCo MJCF file on a latched ROS 2 topic.

This is a lightweight alternative to running the full URDF->MJCF conversion
pipeline (``robot_description_to_mjcf.sh`` from ``mujoco_ros2_control``) when a
previously generated MJCF already exists on disk. It reads the MJCF, anchors the
(relative) compiler asset directories at the file's own directory so topic
consumers can resolve them, and publishes the document once on a latched
``std_msgs/String`` topic.

The QoS mirrors what ``mujoco_ros2_control``'s ``ros2_control_node`` expects when
loading the model from a topic: depth 1, RELIABLE, TRANSIENT_LOCAL (latched). The
node then spins so the latched sample remains available to late subscribers.

Usage:
    publish_mjcf.py <mjcf_path> [topic]

Arguments:
    mjcf_path  Path to the pre-generated MJCF file to publish.
    topic      Topic to publish the MJCF on (default: ``mujoco_robot_description``).
"""

import argparse
import os
import re
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from rclpy.utilities import remove_ros_args
from std_msgs.msg import String


def absolutize_compiler_asset_dirs(xml_string, base_dir):
    """Rewrite relative ``meshdir``/``texturedir``/``assetdir`` attributes on the
    MJCF ``<compiler>`` tag to absolute paths anchored at ``base_dir``.

    A cached MJCF may carry relative asset directories (e.g. ``meshdir="assets/"``).
    Once published over a topic, the consumer no longer shares the working
    directory the cache was generated in, so relative asset dirs fail to resolve.
    Anchoring them at ``base_dir`` makes the published description self-contained.

    Absolute paths and empty values are left untouched, which makes the call
    idempotent. If there is no ``<compiler>`` tag, or nothing relative to rewrite,
    the original string is returned unchanged (no reformatting). The edit is
    surgical (only the ``<compiler>`` tag's attribute values change) so the rest of
    the document -- in particular the absence of an ``<?xml ?>`` declaration, which
    MuJoCo rejects at the start of the description -- is preserved verbatim.

    Mirrors ``mujoco_ros2_control.urdf_to_mujoco_utils.absolutize_compiler_asset_dirs``;
    duplicated here to keep this node free of that module's heavy import-time
    dependencies (PyKDL, numpy, urdf_parser_py).

    :param xml_string: the MJCF document as a string.
    :param base_dir: directory the relative asset dirs are anchored to (typically
        the directory the MJCF file lives in).
    :returns: the MJCF string with relative compiler asset dirs made absolute.
    """
    compiler_match = re.search(r"<compiler\b[^>]*>", xml_string)
    if not compiler_match:
        return xml_string
    compiler_tag = compiler_match.group(0)

    def _absolutize(attr_match):
        attr, value = attr_match.group(1), attr_match.group(2)
        if value and not os.path.isabs(value):
            return f'{attr}="{os.path.join(base_dir, value)}"'
        return attr_match.group(0)

    new_compiler_tag = re.sub(
        r'\b(meshdir|texturedir|assetdir)\s*=\s*"([^"]*)"', _absolutize, compiler_tag
    )
    if new_compiler_tag == compiler_tag:
        return xml_string
    return xml_string.replace(compiler_tag, new_compiler_tag, 1)


class MjcfFilePublisher(Node):
    """Latched publisher that emits the contents of an MJCF file once and holds it.

    :param mjcf_path: path to the MJCF file to read and publish.
    :param topic: topic name to publish on (a leading ``/`` is stripped).
    :raises FileNotFoundError: if ``mjcf_path`` does not point to a file.
    """

    def __init__(self, mjcf_path, topic):
        super().__init__("mjcf_publisher")

        if not os.path.isfile(mjcf_path):
            raise FileNotFoundError(f"MJCF file not found: {mjcf_path}")

        # Match the QoS of mujoco_ros2_control's subscriber: a single latched,
        # reliable sample so late-joining consumers still receive the model.
        qos_profile = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._publisher = self.create_publisher(String, topic.lstrip("/"), qos_profile)

        with open(mjcf_path) as f:
            xml_content = f.read()
        xml_content = absolutize_compiler_asset_dirs(xml_content, os.path.dirname(mjcf_path))

        msg = String()
        msg.data = xml_content
        self._publisher.publish(msg)
        self.get_logger().info(f"Published MJCF from '{mjcf_path}' on topic '{topic}'.")


def main(argv=None):
    """Entry point: parse args, publish the MJCF once, and spin to keep it latched."""
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        description="Publish a pre-generated MJCF file on a latched ROS 2 topic."
    )
    parser.add_argument("mjcf_path", help="Path to the pre-generated MJCF file")
    parser.add_argument(
        "topic",
        nargs="?",
        default="mujoco_robot_description",
        help="Topic to publish the MJCF on (default: mujoco_robot_description)",
    )

    rclpy.init(args=argv)
    # Drop ROS-injected args (e.g. --ros-args) before handing the rest to argparse.
    parsed_args = parser.parse_args(remove_ros_args(args=argv)[1:])

    node = MjcfFilePublisher(parsed_args.mjcf_path, parsed_args.topic)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
