#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from os.path import join
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    warehouse = get_package_share_directory("rs_warehouse")
    diff_drive_description_pkg_path = get_package_share_directory('diff_bot_description')
    xacro_file = os.path.join(diff_drive_description_pkg_path, 'description', 'bot.urdf.xacro')

    # Process xacro with absolute mesh path
    robot_description = xacro.process_file(
        xacro_file,
        mappings={'mesh_path': diff_drive_description_pkg_path}
    ).toxml()

    world_file = LaunchConfiguration(
        "world_file",
        default=join(warehouse,"worlds", "warehouse_world.sdf")
    )


    # Tell Gazebo where to find ROS package meshes
    set_env = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=os.path.join(diff_drive_description_pkg_path, '..', '..')
    )

    # Start Gazebo Fortress
    # Start Gazebo Fortress
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            # We removed PythonExpression and added '-v 4' for deep logging
            "gz_args": ['-r -v 4 ', world_file] 
        }.items(),
    )
    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    # Spawn robot in Gazebo after delay
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-name', 'diff_bot',
                    '-topic', 'robot_description',
                    '-x', '-13.5592',
                    '-y', '-4.894',
                    '-z', '0.3',
                ],
                output='screen'
            )
        ]
    )

    # ROS-Gazebo Bridge
    bridge_config_path = os.path.join(
        get_package_share_directory('rs_warehouse'),
        'config',
        'bridge.yaml'
    )

    # ROS-Gazebo Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config_path,
        }],
        output='screen'
    )


    return LaunchDescription([
        set_env,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
       
    ])