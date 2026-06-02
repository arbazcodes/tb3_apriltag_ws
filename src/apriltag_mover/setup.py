from setuptools import setup
from glob import glob

package_name = 'apriltag_mover'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        # Install executable to lib/apriltag_mover/ for ros2 launch
        ('lib/' + package_name, ['scripts/mover_node']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
)