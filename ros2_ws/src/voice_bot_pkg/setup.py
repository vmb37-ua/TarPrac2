from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'voice_bot_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # ¡IMPORTANTE! Esta línea le dice a ROS 2 que copie la carpeta config
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='tu_nombre',
    maintainer_email='tu_email@ejemplo.com',
    description='Paquete de control por voz para Turtlebot 4',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Aquí registramos nuestros nodos para poder usar 'ros2 run'
            'fake_mic = voice_bot_pkg.voice_listener_node:main',
            'executor = voice_bot_pkg.robot_executor_node:main',
            'real_mic = voice_bot_pkg.real_mic_node:main'
        ],
    },
)