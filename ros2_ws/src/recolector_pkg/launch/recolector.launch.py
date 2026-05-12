import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Buscamos la ruta de nuestro paquete y nuestro mundo
    pkg_recolector = get_package_share_directory('recolector_pkg')
    world_path = os.path.join(pkg_recolector, 'worlds', 'huerto.world')

    # Buscamos el lanzador oficial del robot manipulador
    pkg_tb3_gazebo = get_package_share_directory('turtlebot3_manipulation_gazebo')
    tb3_sim_launch = os.path.join(pkg_tb3_gazebo, 'launch', 'gazebo.launch.py')

    # Incluimos el lanzador oficial pero inyectando nuestro mundo personalizado
    tb3_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(tb3_sim_launch),
        launch_arguments={'world': world_path}.items()
    )

    return LaunchDescription([
        tb3_sim
    ])  