# 来源：ROS 2 官方 rosidl 消息生成模板
# 作用：把 msg/GimbalCmd.msg 编译成 C++/Python 消息代码
cmake_minimum_required(VERSION 3.8)
project(sentry_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(
    ${PROJECT_NAME}
    "msg/GimbalCmd.msg"
)

ament_package()