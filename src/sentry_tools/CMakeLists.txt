cmake_minimum_required(VERSION 3.8)
project(sentry_tools)

find_package(ament_cmake REQUIRED)

#注意注意 PROGRAMS + 指向文件 + lib
install(PROGRAMS
  scripts/keyboard_control.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
