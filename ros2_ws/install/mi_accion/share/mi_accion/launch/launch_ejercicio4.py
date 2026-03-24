from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    nodo_server = Node(
        package='mi_accion',
        executable='server',
        name='fibonacci_server',
        namespace='miGrupo',
        remappings=[
            ('/fibonacci', '/miGrupo/fibonacci') 
        ],
    )

    nodo_client = Node(
        package='mi_accion',
        executable='client',
        name='fibonacci_client',
        namespace='miGrupo', 
        remappings=[
            ('/fibonacci', '/miGrupo/fibonacci')
        ],
    )

    return LaunchDescription([
        nodo_server,
        nodo_client
    ])