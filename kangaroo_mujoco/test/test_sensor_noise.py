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

"""Regression test for IMU sensor noise values across model variants.

Invariant locked in by this test:

The reference model
(``mjcf_data_floating_4dof_no-end-effector_no-end-effector_fixed``) defines
``noise`` attributes on its torso IMU sensors (``framequat``, ``gyro``,
``accelerometer``). Every other ``mjcf_data_*`` variant that carries the same
sensors must use matching ``noise`` values, so IMU readings are equally noisy
regardless of which model variant a policy is trained or evaluated against.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
MODELS = PKG_ROOT / "models"
sys.path.insert(0, str(PKG_ROOT / "scripts"))

from consolidate_model_assets import _find_model_dirs  # noqa: E402

REFERENCE_MODEL = "mjcf_data_floating_4dof_no-end-effector_no-end-effector_fixed"
FORMATTED_XML = "mujoco_description_formatted.xml"
IMU_SITE = "torso_imu_link"

# MJCF sensor tag -> attribute that names the site/object it is attached to.
_SENSOR_NAME_ATTR = {
    "framequat": "objname",
    "gyro": "site",
    "accelerometer": "site",
}


def _imu_noises(xml_path: Path) -> dict:
    """Return {sensor tag: noise attribute value} for the torso IMU sensors.

    Only sensors attached to ``torso_imu_link`` are considered; other sensors
    (e.g. ankle F/T sensors) are out of scope for this test.
    """
    root = ET.parse(xml_path).getroot()
    sensor_el = root.find("sensor")
    noises = {}
    if sensor_el is None:
        return noises
    for tag, name_attr in _SENSOR_NAME_ATTR.items():
        for el in sensor_el.findall(tag):
            if el.get(name_attr) == IMU_SITE:
                noises[tag] = el.get("noise")
    return noises


def test_imu_noise_matches_reference_across_variants():
    """Every variant's torso IMU sensors must carry the reference noise values."""
    reference_path = MODELS / REFERENCE_MODEL / FORMATTED_XML
    reference_noises = _imu_noises(reference_path)
    assert reference_noises, (
        f"Reference model {reference_path} defines no torso IMU sensors — "
        "nothing to propagate."
    )
    assert all(reference_noises.values()), (
        f"Reference model {reference_path} has torso IMU sensors missing "
        f"'noise' attributes: {reference_noises}"
    )

    model_dirs = _find_model_dirs(MODELS)
    assert model_dirs, f"No mjcf_data_* directories found under {MODELS}."

    failures = []
    for model_dir in model_dirs:
        xml_path = model_dir / FORMATTED_XML
        if not xml_path.is_file():
            continue
        noises = _imu_noises(xml_path)
        for tag, expected in reference_noises.items():
            actual = noises.get(tag)
            if actual != expected:
                failures.append(
                    f"{xml_path.relative_to(PKG_ROOT)}: <{tag}> noise="
                    f"{actual!r}, expected {expected!r}"
                )

    assert not failures, (
        "One or more variants have torso IMU sensor noise values that don't "
        f"match the reference model ({REFERENCE_MODEL}):\n"
        + "\n".join(f"  {f}" for f in failures)
    )
