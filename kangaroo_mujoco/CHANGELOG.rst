^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package kangaroo_mujoco
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
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
