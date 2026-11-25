cmake_minimum_required(VERSION 3.8)
project(sentry_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf worlds models launch 
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/sim_gimbal_adapter.py
  DESTINATION lib/${PROJECT_NAME} RENAME sim_gimbal_adapter
)

ament_package()

