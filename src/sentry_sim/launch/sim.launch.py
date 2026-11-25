#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件来源：本项目编写，参考 ROS 2 Humble 官方 gazebo_ros / nav2_bringup launch。
文件作用：
  一键启动完整仿真 + 导航：
    1) Gazebo 2027 3V3 场地
    2) 机器人、云台 ros2_control、Mid-360、IMU
    3) 云台指令适配器
    4) RViz
    5) 延时 include sentry_navigation 的 nav.launch.py
       （Nav2 + /scan 累积 + 生命周期启动 + 可选巡逻，仿真和真机共用）

用法：
  ros2 launch sentry_sim sim.launch.py
  ros2 launch sentry_sim sim.launch.py patrol:=true
  ros2 launch sentry_sim sim.launch.py gui:=false rviz:=false
"""

import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # =========================================================================
    # 1. 路径（绝对路径）
    # =========================================================================
    sim_share = get_package_share_directory('sentry_sim')
    description_share = get_package_share_directory('sentry_description')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    world_path = os.path.join(sim_share, 'worlds', 'rmul_2027.world')
    xacro_path = os.path.join(sim_share, 'urdf', 'sentry_sim.xacro')

    # =========================================================================
    # 2. 机器人描述
    # 来源：xacro 官方 Python API
    # 作用：展开仿真 xacro，并把 package:// 换成 file://
    #       Gazebo 11 遇到 package:// 会静默跳过模型级插件。
    # =========================================================================
    #在 ROS/ROS2 里把 .xacro 文件解析成 URDF 字符串：
    robot_description = xacro.process_file(xacro_path).toxml()
    robot_description = robot_description.replace(
        'package://sentry_description',
        'file://' + description_share,#这里是 sentry_description 的绝对路径
    )
    # =========================================================================
    # 3.发布机器人各个关节状态的节点
    # =========================================================================
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )
    # =========================================================================
    # 4. Gazebo 环境变量
    # =========================================================================
    models_path = os.path.join(sim_share, 'models')
    existing_model_path = os.environ.get('GAZEBO_MODEL_PATH', '')
    gazebo_model_path = os.pathsep.join(
        [p for p in (models_path, '/usr/share/gazebo-11/models', existing_model_path) if p]
    )
    # =========================================================================
    # 5. Gazebo
    # =========================================================================
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
        }.items(),
    )
    # =========================================================================
    # 7. 在 Gazebo 中生成机器人
    # 蓝方侧空地 (10.05, 3.20)，朝向 -X
    # =========================================================================
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'sentry',
            '-x', '10.05',
            '-y', '0.50',
            '-z', '0.00',
            '-Y', '3.14159',
        ]
    )
    # =========================================================================
    # 9. 云台适配器：/cmd_gimbal -> /gimbal_controller/joint_trajectory
    # =========================================================================
    sim_gimbal_adapter = Node(
        package='sentry_sim',
        executable='sim_gimbal_adapter',
        name='sim_gimbal_adapter',
        output='screen',
        parameters=[{
            'use_sim_time': True,
        }],
    )

    return LaunchDescription([
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', gazebo_model_path),
        robot_state_publisher,
        gazebo,
        TimerAction(period=2.0,actions=[spawn_entity]),#延时2秒后生成机器人
        TimerAction(period=5.0, actions=[sim_gimbal_adapter]),
    ])