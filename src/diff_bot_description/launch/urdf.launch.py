import os, xacro

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.conditions import IfCondition


def generate_launch_description():

    # Check if we're told to use sim time
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_ros2_control = LaunchConfiguration('use_ros2_control')

    # Process the URDF file
    pkg_path = os.path.join(get_package_share_directory('diff_bot_description'))
    xacro_file = os.path.join(pkg_path,'description','bot.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file).toxml()

    # Create a RViz node
    rviz_config = os.path.join(pkg_path, 'config', 'urdf_view.rviz')
    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )
    
    # Create a robot_state_publisher node
    params = {'robot_description': robot_description_config, 'use_sim_time': use_sim_time}
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    # Create a joint_state_publisher_gui node
    node_jsp_gui = Node(
    package='joint_state_publisher_gui',
    executable='joint_state_publisher_gui',
    name='joint_state_publisher',
    output='screen',
    condition=IfCondition(LaunchConfiguration('use_jsp'))
  )


    # Launch!
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Use rviz if true'),
        DeclareLaunchArgument(
            'use_jsp',
            default_value='true',
            description='Use joint_state_publisher_gui if true'),
        node_robot_state_publisher,
        node_rviz,
        node_jsp_gui
    ])
