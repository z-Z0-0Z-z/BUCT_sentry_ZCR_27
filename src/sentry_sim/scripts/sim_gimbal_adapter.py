#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件来源：本项目编写（参考 ZCR_27_sentry 同名文件）。
文件作用：订阅 /sentry/cmd_gimbal（GimbalCmd），发布
         /sentry/gimbal_trajectory（JointTrajectory），由 Gazebo 的
         joint_pose_trajectory 插件直接设定三个关节角。
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sentry_interfaces.msg import GimbalCmd

class SimGimbalAdapter(Node):
    def __init__(self):
        super().__init__('sim_gimbal_adapter')
        self.sub = self.create_subscription(GimbalCmd, '/sentry/cmd_gimbal', self.kb_cmd_callback, 10)
        self.pub = self.create_publisher(JointTrajectory,'/sentry/gimbal_trajectory', 10)
        self.big_yaw = 0.0
        self.small_yaw = 0.0
        self.pitch = 0.0
        #在tools里限位
        self.timer = self.create_timer(0.05,self.publish_trajectory)
        self.publish_trajectory()

    def kb_cmd_callback(self, msg):
        self.big_yaw = msg.big_yaw
        self.small_yaw =msg.small_yaw
        self.pitch = msg.pitch
        # 注意：不在这里 publish，等定时器统一发，避免一次按键发两帧

    def publish_trajectory(self):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        # 来源：gazebo_ros_joint_pose_trajectory.cpp 的硬性要求。
        # 它读 header.frame_id，若既不是 "world" 也不是 "map"，
        # 就去 world 里找同名 link，找不到直接打印
        # "Plugin needs a reference link [] as frame_id, aborting." 并 return。
        msg.header.frame_id = 'world'
        # 顺序必须与插件的 joint_name 声明一致
        msg.joint_names = ['bigyawjoint', 'smallyawjoint', 'pitchjoint']
        point = JointTrajectoryPoint()
        point.positions = [self.big_yaw, self.small_yaw, self.pitch]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 200_000_000
        msg.points = [point]
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = SimGimbalAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()