#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件来源：
  本项目编写，按键读取参考 ROS 2 官方 teleop_twist_keyboard 的 termios/cbreak 做法。

文件作用：
  用键盘同时控制：
    1) 底盘：发布 geometry_msgs/msg/Twist 到 /cmd_vel；
    2) 云台：发布 sentry_interfaces/msg/GimbalCmd 到 /cmd_gimbal。

接口约定：
  仿真和真机都只认 /cmd_gimbal，底层由各自的适配器转换：
    仿真：/cmd_gimbal -> sim_gimbal_adapter -> /gimbal_controller/joint_trajectory
    真机：/cmd_gimbal -> real_gimbal_driver -> 串口/CAN

按键：
  W/S 前进/后退，A/D 左右平移，Q/E 自转，空格停车
  J/L 大 yaw，U/O 小 yaw，I/K pitch，C 云台回中，X 退出
"""
#检查键盘有没有输入，但不会卡住程序
import select
#检查键盘有没有输入，但不会卡住程序
import sys
#让终端进入“按一个键就立刻读取”的模式，不用按回车
import termios
import time
#让终端进入“按一个键就立刻读取”的模式，不用按回车
import tty

import rclpy
#底盘速度消息
from geometry_msgs.msg import Twist
from rclpy.node import Node
#（自定）云台命令消息
from sentry_interfaces.msg import GimbalCmd


class SentryTeleop(Node):
    def __init__(self):
        super().__init__('keyboard_control')

        # 底盘速度发布者
        self.cmd_vel_pub = self.create_publisher(Twist, 'sentry/cmd_vel', 10)
        # 云台指令发布者：仿真/真机共用
        self.gimbal_pub = self.create_publisher(GimbalCmd, 'sentry/cmd_gimbal', 10)

        # 底盘速度状态
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        # 云台目标角度（rad）
        self.big_yaw = 0.0
        self.small_yaw = 0.0
        self.pitch = 0.0

        # 速度/步长
        self.linear_speed = 0.5 #前后
        self.strafe_speed = 0.3 #左右
        self.angular_speed = 0.4 #旋转
        self.gimbal_step = 0.02 #云台所有零件步长
        self.small_yaw_left_limit=3.2
        self.small_yaw_right_limit=-0.37
        self.pitch_up_limit = 1.2
        self.pitch_down_limit = -0.2

        # 20Hz 持续发布底盘速度
        self.timer = self.create_timer(0.05, self.publish_cmd_vel)

        self.publish_gimbal()
        self.print_help()

    def publish_cmd_vel(self):
        msg = Twist()
        msg.linear.x = self.vx
        msg.linear.y = self.vy
        msg.linear.z = 0.0
        msg.angular.z = self.wz
        self.cmd_vel_pub.publish(msg)

    def publish_gimbal(self):
        msg = GimbalCmd()
        msg.big_yaw = self.big_yaw
        msg.small_yaw = self.small_yaw
        msg.pitch = self.pitch
        self.gimbal_pub.publish(msg)

    def print_help(self):
        print('\n================ sentry_sim 键盘遥控 ================')
        print('  W / S      前进 / 后退')
        print('  A / D      左平移 / 右平移')
        print('  Q / E      左转 / 右转')
        print('  空格       底盘立即停止')
        print('  J / L      大 yaw 左转 / 右转')
        print('  U / O      小 yaw 左转 / 右转')
        print('  I / K      pitch 抬头 / 低头')
        print('  C          云台回中')
        print('  X          退出')
        print('======================================================\n')

    def handle_key(self, key):
        if key == 'w':
            self.vx = self.linear_speed
        elif key == 's':
            self.vx = -self.linear_speed
        elif key == 'a':
            self.vy = self.strafe_speed
        elif key == 'd':
            self.vy = -self.strafe_speed
        elif key == 'q':
            self.wz = self.angular_speed
        elif key == 'e':
            self.wz = -self.angular_speed
        elif key == ' ':
            self.vx = 0.0
            self.vy = 0.0
            self.wz = 0.0
            print('[底盘] 已停止')
        elif key == 'j':
            self.big_yaw += self.gimbal_step
            self.publish_gimbal()
        elif key == 'l':
            self.big_yaw -= self.gimbal_step
            self.publish_gimbal()
        elif key == 'u':
            self.small_yaw = min(self.small_yaw + self.gimbal_step, self.small_yaw_left_limit)
            self.publish_gimbal()
        elif key == 'o':
            self.small_yaw = max(self.small_yaw - self.gimbal_step, self.small_yaw_right_limit)
            self.publish_gimbal()
        elif key == 'i':
            self.pitch = min(self.pitch + self.gimbal_step, self.pitch_up_limit)
            self.publish_gimbal()
        elif key == 'k':
            self.pitch = max(self.pitch - self.gimbal_step, self.pitch_down_limit)
            self.publish_gimbal()
        elif key == 'c':
            self.big_yaw = 0.0
            self.small_yaw = 0.0
            self.pitch = 0.0
            self.publish_gimbal()
            print('[云台] 已回中')
        elif key == 'x':
            return False
        return True

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0
        self.publish_cmd_vel()
        time.sleep(0.2)


def main():
    rclpy.init()
    node = SentryTeleop()

    if not sys.stdin.isatty():
        node.get_logger().error('请在真实终端里运行本节点。')
        node.destroy_node()
        rclpy.shutdown()
        return

    #sys.stdin 就是“标准输入”，也就是你的键盘。
    #termios.tcgetattr(...) 的意思是：把当前终端的所有设置读出来，存到 settings 里。
    settings = termios.tcgetattr(sys.stdin)
    try:
        #把终端切换成 cbreak 模式(不需要按回车)
        #每个打开的文件/终端在系统里都有一个整数编号，叫文件描述符。fileno() 就是取出这个编号。setcbreak需要
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                key = sys.stdin.read(1)
                if not node.handle_key(key):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
