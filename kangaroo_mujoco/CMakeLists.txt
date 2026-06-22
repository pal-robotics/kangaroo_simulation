cmake_minimum_required(VERSION 3.8)
project(kangaroo_mujoco)

find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

# Lightweight node that publishes a pre-generated MJCF on a latched topic.
install(PROGRAMS
  scripts/publish_mjcf.py
  scripts/consolidate_model_assets.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_model_assets test/test_model_assets.py)
endif()

ament_auto_package(INSTALL_TO_SHARE launch config models)

