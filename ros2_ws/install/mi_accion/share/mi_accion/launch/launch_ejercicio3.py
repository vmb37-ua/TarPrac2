from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    orden_arg = DeclareLaunchArgument(
        'orden',
        default_value='7',
        description='Orden de la secuencia de Fibonacci a calcular'
    )

    nodo_server = Node(
        package='mi_accion',
        executable='server',
        name='fibonacci_server',
    )


    nodo_client = Node(
        package='mi_accion',
        executable='client',
        name='fibonacci_client',
        parameters=[{
            'orden': LaunchConfiguration('orden')
        }]
    )

    return LaunchDescription([
        orden_arg,
        nodo_server,
        nodo_client
    ])