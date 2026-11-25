# 作用：只安装共用描述资源，不安装 Gazebo/场地/驱动
cmake_minimum_required(VERSION 3.8)
project(sentry_description)

find_package(ament_cmake REQUIRED)

install(
    DIRECTORY meshes rviz urdf launch
    DESTINATION share/${PROJECT_NAME}
)

ament_package()