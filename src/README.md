## Differential Drive Bot
This repo contains the necessary ROS files required for building a Differential Drive Bot.

1) To Run the Gazebo Sim: empty_world
```ros2 launch diff_bot_description gazebo.launch.py```

2)- To Run the Gazebo Sim: eyrc
```ros2 launch diff_bot_description eyrc_ws.launch.py```


3) To Run the Gazebo Sim: re_ws
```ros2 launch diff_bot_description rs_ws.launch.py```


4) For Rviz: 
```rviz2 -d "~path/to/the/file.rviz"```

5)- For Teleop: 
```ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped```


--------- Before that install slam_toolbox and nav2---------------------


6)- For Slam toolbox online async (mapping)

 '''ros2 launch slam_toolbox online_async_launch.py slam_params_file:=$HOME/diff_drive_amr/src/diff_bot_description/config/mapper_params_online_async.yaml use_sim_time:=true'''

7) For Slam toolbox online async (localization)
''' ros2 launch diff_bot_description localization.launch.py

8) For AMCL localization 
   i) run mapper server 
        '''  ros2 run nav2_map_server map_server --ros-args   -p yaml_filename:=/home/kamal/diff_drive_amr/src/diff_bot_description/map/f_map.yaml   -p use_sim_time:=true  '''

  ii) then configure and activate /mapper_server
  
       ros2 lifecycle set /map_server configure
       ros2 lifecycle set /map_server activate

  iii) then run amcl localization 
        
       ''' ros2 run nav2_amcl amcl --ros-args   --params-file ~/diff_drive_amr/src/diff_bot_description/config/nav2_params.yaml '''
       
    iv) then  configure and activate /amcl
  
       ros2 lifecycle set /amcl configure
       ros2 lifecycle set /amcl activate
       

9) For nav2 navigation 

  ''' ros2 launch diff_bot_description navigation_launch.py '''





