import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    world_path = '/home/lucia/Documents/GitHub/IR2136/drone_project/ardupilot_gazebo/worlds/neighborhood.world'
    models_path = '/home/lucia/Documents/GitHub/IR2136/drone_project/ardupilot_gazebo/models'
    
    # 2. Configurar el entorno 
    current_gazebo_models = os.environ.get('GAZEBO_MODEL_PATH', '')
    new_gazebo_models = f"{current_gazebo_models}:{models_path}"

    #Nodo Battery GPS
    battery_gps_node = Node(
        package='drone_project',
        executable='battery_gps',
        name='battery_gps',
        output='screen'
    )

    #Nodo Mission Control
    mission_control_node = Node(
        package='drone_project',
        executable='mission_control',
        name='mission_control',
        output='screen'
    )

    #Nodo Vision UI
    vision_ui_node = Node(
        package='drone_project',
        executable='vision_ui',
        name='vision_ui',
        output='screen'
    )

    return LaunchDescription([
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
    
        battery_gps_node,
        mission_control_node,
        vision_ui_node
    ])
