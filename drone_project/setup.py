from setuptools import setup
import os
from glob import glob

package_name = 'drone_project'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lucia',
    maintainer_email='lucia@todo.todo',
    description='Paquete para control de dron con vision',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'battery_gps = drone_project.battery_gps:main',
            'mission_control = drone_project.mission_control:main',
            'vision_ui = drone_project.vision_ui:main',
        ],
    },
)
