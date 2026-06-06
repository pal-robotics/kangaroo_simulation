cmake_minimum_required(VERSION 3.8)
project(kangaroo_mujoco)

find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

# Lightweight node that publishes a pre-generated MJCF on a latched topic.
install(PROGRAMS
  scripts/publish_mjcf.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_auto_package(INSTALL_TO_SHARE launch config models)

