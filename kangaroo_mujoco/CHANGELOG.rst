^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package kangaroo_mujoco
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* Merge branch 'improve/ankle_fusion' into 'humble-devel'
  Improve ankle inertia fusion
  See merge request robots/kangaroo_simulation!20
* Add collision exclude between knee and ankle link
* Add fixed base mujoco simulation
* Remove duplicate density setting
* Refine the collision capsules for the new covers
* Add the capsules for the new feet with covers
* Update to new ankle configuration data
* Merge branch 'add/fixation_type/folder_naming' into 'humble-devel'
  Add fixation type to the folder naming
  See merge request robots/kangaroo_simulation!19
* Add fixation type to the folder naming
* Contributors: Sai Kishor Kothakota

2.4.0 (2026-06-23)
------------------
* Merge branch 'add/stairs' into 'humble-devel'
  Stairs world for lower body with detachable feet
  See merge request robots/kangaroo_simulation!18
* Stairs world for lower body with detachable feet
* Merge branch 'refine/models' into 'humble-devel'
  Refine models  + Add lower body with detached foot
  See merge request robots/kangaroo_simulation!17
* Add lower body with detached foot precompiled simulation
* Remove pal_mujoco_scenes dependency
* Set --no-fuse for only fixed fixation type
* Set density to zero for the foot capsules
* Merge branch 'add/readme' into 'humble-devel'
  Add README to the package
  See merge request robots/kangaroo_simulation!16
* rename the script
* fix the generate decomposed pregenerated mjcf script
* Update README
* Merge branch 'add/worlds' into 'humble-devel'
  Adding world argument
  See merge request robots/kangaroo_simulation!15
* Adding world argument
  World suffix + launch option. Only works with pregenerated models. Will
  fallback gracefully to generating with empty if a given world name
  doesn't exist
* Merge branch 'add/cached_models_with_feet_type' into 'humble-devel'
  Add feet type to the cached models folder naming
  See merge request robots/kangaroo_simulation!14
* Add feet type to the cached models folder naming
* Merge branch 'add/density/foot_capsules' into 'humble-devel'
  Set foot capsules density set to zero
  See merge request robots/kangaroo_simulation!13
* Set foot capsules density set to zero
* Adding 5dof with RH8D pregenerated
* Contributors: Sai Kishor Kothakota, oscarmartinez, Óscar Martínez

2.3.0 (2026-06-21)
------------------
* Merge branch 'add/imu_args' into 'humble-devel'
  Add IMU args to the mujoco simulator
  See merge request robots/kangaroo_simulation!11
* Add IMU args to the mujoco simulator
* Contributors: Sai Kishor Kothakota

2.2.1 (2026-06-09)
------------------
* Merge branch 'fix/ankle_ft_missing_args' into 'humble-devel'
  Add missing ankle ft sensor arguments
  See merge request robots/kangaroo_simulation!10
* Add conditioning to pal_mujoco_scenes dependency
* Add missing ankle ft sensor arguments
* Contributors: Sai Kishor Kothakota

2.2.0 (2026-06-09)
------------------
* Merge branch 'update/models' into 'humble-devel'
  Update kangaroo models of 4DoF and lower body to local frozen mjcfs
  See merge request robots/kangaroo_simulation!9
* Add a script to publish the mujoco description if it is already generated
* Remove the bodies of the torso cameras
* Use capsules for the foot contact
* Add --cache-dir arg to reuse the generated mjcfs
* make meshdir, texturedir and assetdir relative paths
* Add the robot with configuration of lower body only
* rename the cached folder to mjcf_data_4dof_fake-forearm_fake-forearm
* Remove leg_type argument assuming is always leg
* Add new arguments as end_effector\_<side> and feet_type
* Contributors: Aina, Sai Kishor Kothakota

2.1.1 (2026-04-23)
------------------
* Add missing dependency mujoco_ros2_control
* Contributors: Noel Jimenez

2.1.0 (2026-02-25)
------------------
* apply format
* removed unnecessary imports
* updated model
* set motor actuator default
* Enable topic publishing and also add emulate_tty for better noticing of logs
* Set back to 2kHz
* added test model and config to rl inference
* Contributors: Sai Kishor Kothakota, sergiacosta

2.0.1 (2026-02-11)
------------------
* updated model loading path
* updated installation rules
* added decomposed model
* Contributors: sergiacosta

2.0.0 (2026-02-04)
------------------
* updated metadata
* set package version to 2.0.0 for first release ros2
* update package metadata
* added PIDs for mujoco ros2 control
* update launchfiles to use last features
* update mjcf converter execution
* update model generation logic
* improved generation logic
* created launchfile for mesh decomposition
* fixed package name
* cleaned imports
* Updated command to run the mjcf generator
* added convinient display rviz config
* added moveit to launch
* created kangaroo mujoco simulation
* Contributors: Ortisa Poci, sergiacosta
