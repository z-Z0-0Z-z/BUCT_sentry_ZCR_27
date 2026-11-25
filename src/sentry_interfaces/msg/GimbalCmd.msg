# 来源：公用消息接口，仿真/真机共用
# 作用：上层只发云台目标角度或速度，不关心底层是 Gazebo 还是串口
# 单位：角度 rad，角速度 rad/s

float32 big_yaw            # 大 yaw 目标角
float32 small_yaw      # 小 yaw 目标角
float32 pitch          # pitch 目标角

float32 yaw_rate       # 大 yaw 角速度，mode=1 时使用
float32 small_yaw_rate # 小 yaw 角速度，mode=1 时使用
float32 pitch_rate     # pitch 角速度，mode=1 时使用
