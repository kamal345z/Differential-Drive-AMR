import os
from os.path import join
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    AppendEnvironmentVariable,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    warehouse = get_package_share_directory("eyantra_warehouse")
    diff_drive_description_pkg_path = get_package_share_directory("diff_bot_description")
    xacro_file = os.path.join(diff_drive_description_pkg_path, "description", "bot.urdf.xacro")

    # Process xacro with absolute mesh path
    robot_description = xacro.process_file(
        xacro_file,
        mappings={'mesh_path': diff_drive_description_pkg_path}
    ).toxml()
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )
    
    # ── Tell Gazebo where to find ROS package meshes
    world_file = LaunchConfiguration(
        "world_file",
        default=join(warehouse, "worlds", "eyantra_warehouse_task2.world")
    )
    gz_sim = IncludeLaunchDescription(PythonLaunchDescriptionSource(
            join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": PythonExpression(["'", world_file, " -r'"])
        }.items(),)
    
    
    # set_env = SetEnvironmentVariable(
    #     name='IGN_GAZEBO_RESOURCE_PATH',
    #     value=os.path.join(diff_drive_description_pkg_path, '..', '..') 
    #       # points to install/share
    # )

    spawn_robot = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-name', 'diff_bot',
                    '-topic', 'robot_description',
                    "-x", "-1.4170",
                    "-y", "-6.9092",
                    "-z", "0.0493",
                    "-Y", "1.5707",
                ],
                output='screen'
            )]
    )
    
    # ROS-Gazebo Bridge
    bridge_config_path = os.path.join(
        get_package_share_directory('eyantra_warehouse'),
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
    DeclareLaunchArgument(
        "world_file",
        default_value=join(warehouse, "worlds", "eyantra_warehouse_task2.world")
    ),
    AppendEnvironmentVariable(
        name="IGN_GAZEBO_RESOURCE_PATH",
        value=join(warehouse, "worlds")
    ),
    AppendEnvironmentVariable(
        name="IGN_GAZEBO_RESOURCE_PATH",
        value=join(warehouse, "models")
    ),
    AppendEnvironmentVariable(
        name="IGN_GAZEBO_RESOURCE_PATH",
        value=os.path.join(diff_drive_description_pkg_path, '..', '..')
    ),
    SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=f"{warehouse}:{join(warehouse, 'models')}"
    ),
    SetEnvironmentVariable(
        name='IGN_GAZEBO_RENDER_ENGINE',
        value='ogre'          # software-compatible, no hardware GPU needed
    ),
    gz_sim,
    robot_state_publisher,
    spawn_robot,
    bridge,
    # joint_state_bridge,
])