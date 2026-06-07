import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable
from launch_ros.actions import Node

def generate_launch_description():
    # Rutas base
    base_path = '/home/lucia/Documents/GitHub/IR2136/drone_project'
    world_path = os.path.join(base_path, 'ardupilot_gazebo/worlds/test_city.world')
    
    # Rutas de modelos
    models_path = os.path.join(base_path, 'ardupilot_gazebo/models')
    
    
    current_gazebo_models = os.environ.get('GAZEBO_MODEL_PATH', '')
    new_gazebo_models = f"{models_path}:{current_gazebo_models}"

    drone_urdf_path = os.path.join(models_path, 'iris_with_ardupilot', 'drone_rviz.urdf')
    with open(drone_urdf_path, 'r') as infp:
        robot_desc = infp.read()

    # Gazebo
    gazebo = ExecuteProcess(
        cmd=[
            'gazebo', 
            '--verbose', 
            '-s', 'libgazebo_ros_init.so', 
            '-s', 'libgazebo_ros_factory.so', 
            world_path
        ],
        output='screen',
        additional_env={'GAZEBO_MODEL_PATH': new_gazebo_models}
    )

    # ArduPilot SITL
    ardupilot_sitl = ExecuteProcess(
        cmd=[
            'sim_vehicle.py', 
            '-v', 'ArduCopter', 
            '-f', 'gazebo-iris', 
            '--console'
        ],
        output='screen'
    )
    
    #Rviz
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', '/home/lucia/Documents/GitHub/IR2136/drone_project/rviz/vision_3d.rviz'] 
    )
    
    tf_broadcaster_process = ExecuteProcess(
        cmd=['python3', '/home/lucia/Documents/GitHub/IR2136/drone_project/drone_project/tf_broadcaster.py'],
        output='screen'
    )

    return LaunchDescription([
        # Seteamos las variables de entorno globalmente por si otros nodos las necesitan
        SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=new_gazebo_models),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
        
        # Lanzamiento de procesos
        gazebo,
        ardupilot_sitl,
        robot_state_publisher_node,
        tf_broadcaster_process,
        rviz_node, 
     
    ])
