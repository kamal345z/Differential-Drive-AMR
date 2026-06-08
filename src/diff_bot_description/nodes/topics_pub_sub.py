#!/usr/bin/env python3

import rclpy
import time
import math
import serial
import threading

from rclpy.node import Node
from sensor_msgs.msg import JointState
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist



class DiffControllerNode(Node):
    """A node that publishes messages and listens to the same topic."""

    def __init__(self):
        super().__init__('diff_controller_node')
        self.jointState_ = self.create_publisher(JointState, 'joint_states', 10)
        self.imu_ = self.create_publisher(Imu, 'imu', 10)
        self.cmd_vel_sub_ = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_ang_vel_callback,
            10
        )
        
        self.refresh_rate = 60
        
        self.timer = self.create_timer(1.0/self.refresh_rate, self.timer_callback)
        
        # Initialize Variables
        self.yaw = 0.0
        self.enc_ang = [0.0]*2  # [angR, angL]
        self.enc_ang_vel = [0.0]*2  # [ang_velR, ang_velL]
        self.sent_ang_vel = [0.0]*2  # [ang_velR, ang_velL]
        self.ang_vel_limit = 18.0  # rad/s
        
        # Initialize Joint State
        self.joint_msg = JointState()
        self.joint_msg.name = ['bottom_left_joint', 'bottom_right_joint']
         
        # Initialize IMU message (we'll publish yaw only) 
        self.imu_msg = Imu()
        
        # Serial Port Setup
        self.port = '/dev/ttyUSB0'
        self.baudrate = 115200
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.serial.flush()  # Clear buffer

            # Wait for Arduino to initialize
            timer = time.monotonic()
            while self.serial.read() != b'#':
                if time.monotonic() - timer > 12:
                    self.get_logger().error(
                        f'Failed to initialize serial port {self.port}')
                    self.destroy_node()
                    return
                self.serial.write(b'?')
            self.serial.flush()
            self.serial.write(b'!')  # Acknowledge
            self.get_logger().info(
                f'Serial port {self.port} opened successfully')

            self.serial_thread = threading.Thread(target=self.serial_read)
            self.serial_thread.daemon = True
            self.serial_thread.start()
        except serial.SerialException as e:
            self.get_logger().warn(
                f'Failed to open serial port {self.port}: {e}')
            self.destroy_node()
            
    def cmd_ang_vel_callback(self, msg):
        vx = msg.linear.x
        wz = msg.angular.z
        
        R = 0.229  # Robot radius (m)
        r = 0.035   # Wheel radius (m)
        
        # Calculate angular velocities for right and left wheels
        self.sent_ang_vel[0] = (vx - wz*R) / r  # wheel radius = 0.035m
        self.sent_ang_vel[1] = (vx + wz*R) / r
        
        # Clamp velocities to max limits
        self.sent_ang_vel[0] = max(-self.ang_vel_limit, min(self.ang_vel_limit, self.sent_ang_vel[0]))
        self.sent_ang_vel[1] = max(-self.ang_vel_limit, min(self.ang_vel_limit, self.sent_ang_vel[1]))
        
        self.arduino_callback()  # Send commands to Arduino
        
        
    def serial_read(self):
        while rclpy.ok():
            try:
                data = self.serial.readline().decode().strip()
                if data.startswith('{') and data.endswith('}'):
                    data = data[1:-1].split('|')
                    if len(data) == 5:  # 4 if yaw is not published
                        self.enc_ang = [float(data[0]), float(data[1])]
                        self.enc_ang_vel = [float(data[2]), float(data[3])]
                        self.yaw = float(data[4])
                    else:
                        self.get_logger().warn(f'Invalid format: {data}')
                elif data == '#':
                    self.get_logger().error('Acknowledge received during Operation!')
                else:
                    self.get_logger().warn(f'Invalid data: {data}')
            except serial.SerialException as e:
                self.get_logger().error(f'Serial error: {e}')
                break
 
    def timer_callback(self):
        current_time = self.get_clock().now().to_msg()
        
        # Publish Joint States
        self.joint_msg.header.stamp = current_time
        self.joint_msg.position = self.enc_ang
        self.joint_msg.velocity = self.enc_ang_vel
        self.jointState_.publish(self.joint_msg)
        
        # Publish IMU (yaw only)
        self.imu_msg.header.stamp = current_time
        half_yaw = self.yaw / 2.0
        self.imu_msg.orientation.z = math.sin(half_yaw)
        self.imu_msg.orientation.w = math.cos(half_yaw)
        self.imu_.publish(self.imu_msg)

    def arduino_callback(self):
        # This callback can be used to send commands to the Arduino if needed
        command = f'[{self.sent_ang_vel[0]}|{self.sent_ang_vel[1]}]'
        try:
            self.serial.write(command.encode())
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write error: {e}')
        

def main(args=None):
    rclpy.init(args=args)
    node = DiffControllerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
