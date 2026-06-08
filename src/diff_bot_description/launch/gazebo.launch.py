import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, SetEnvironmentVariable

from launch_ros.actions import Node
import xacro


def generate_launch_description():

    diff_drive_description_pkg_path = get_package_share_directory('diff_bot_description')
    xacro_file = os.path.join(diff_drive_description_pkg_path, 'description', 'bot.urdf.xacro')

    # Process xacro with absolute mesh path
    robot_description = xacro.process_file(
        xacro_file,
        mappings={'mesh_path': diff_drive_description_pkg_path}
    ).toxml()

    # Tell Gazebo where to find ROS package meshes
    set_env = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=os.path.join(diff_drive_description_pkg_path, '..', '..')
    )

    # Start Gazebo Fortress
    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', 'empty.sdf'],
        output='screen'
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
                    '-x', '0.0',
                    '-y', '-0.5',
                    '-z', '0.3',
                ],
                output='screen'
            )
        ]
    )
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
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
       
    ])