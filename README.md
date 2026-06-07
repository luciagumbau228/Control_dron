# Image-Based Autonomous Drone Navigation System 

An intuitive, point-and-click autonomous drone navigation system developed with ROS 2, Gazebo, and ArduPilot.
Demo video link  ➔ https://drive.google.com/file/d/1fikTxaDn_mR3RfDz8BS8_D01Jo8i8QMb/view?usp=drive_link

##  Overview
This project explores a more intuitive human-drone interaction paradigm by replacing traditional joystick operation and manual waypoint programming with direct image-based target selection.

Using an RGB-D camera, a user can simply click on a location in the live video feed and the system automatically reconstructs the corresponding 3D position in space. The generated target is then sent to the flight controller, allowing the drone to navigate autonomously to the selected location.

To ensure accurate navigation, the system compensates for the camera's fixed angle and continuously processes depth information to estimate spatial displacements relative to the drone. In parallel, autonomous safety behaviors monitor battery status and landing conditions, enabling emergency landing procedures when required.

The complete system was developed using a modular ROS 2 architecture and validated in simulation using Gazebo and ArduPilot SITL, while a Digital Twin in RViz2 provides real-time visualization of the drone state and coordinate frames.

## Key Features
* **Point-and-Click Navigation:** Converts 2D image coordinates into 3D world targets using depth maps and intrinsic camera focal lengths.
* **Pitch Compensation:** Mathematically compensates for the camera's fixed 30-degree downward pitch to accurately calculate forward and lateral displacements.
* **Autonomous Safety Logic:** Monitors battery levels in real-time. Triggers an emergency auto-landing protocol if the battery drops below 20%.
* **Smart Evasive Landing:** Scans the lower half of the depth matrix to evaluate terrain flatness. If an obstacle is detected within 3.0 meters, the drone computes evasive lateral steps to find a clear landing area.
* **Real-Time Digital Twin:** Visualizes the drone's spatial position and coordinate frames concurrently in RViz2 using TF2.

## System Architecture & ROS 2 Nodes
The system follows a modular ROS 2 architecture where perception, mission management, and flight control are implemented as independent nodes communicating through ROS 2 topics. This design improves maintainability, scalability, and allows each subsystem to be developed and tested independently.

`User Click` ➔ `vision_ui` ➔ `mission_control` ➔ `battery_gps` ➔ `MAVLink` ➔ `ArduPilot SITL` ➔ `Gazebo`

### 1. `vision_ui` (Perception)
* Uses `CvBridge` to convert ROS image messages into OpenCV matrices.
* Reads the `32FC1` depth map to extract the exact Z distance of the clicked pixel.
* Computes the 3D optical coordinates from RGB-D information and applies a trigonometric compensation to account for the camera's fixed downward pitch, producing navigation targets relative to the drone reference frame.
* Publishes the target displacement as a `geometry_msgs/Vector3` relative to the `base_link`.

### 2. `mission_control` (Safety Logic)
* Subscribes to the `/battery_status` topic.
* Overrides manual inputs during critical battery states.
* Processes terrain evaluation flags published by the vision node to either confirm a safe landing (`True` boolean) or trigger obstacle evasion maneuvers.

### 3. `battery_gps` (MAVLink Actuation)
* Establishes a UDP socket connection with ArduPilot.
* Sends `SET_POSITION_TARGET_LOCAL_NED` commands via the MAVLink protocol.
* Applies the specific bitmask `0b110111111000` to instruct the flight controller to strictly follow the X, Y, and Z targets while ignoring yaw rotation, ensuring stable translation.

## Technologies & Tools
* **Robotics & Middleware:** ROS 2, TF2, URDF
* **Simulation:** Gazebo, ArduPilot SITL
* **Computer Vision:** OpenCV, CvBridge
* **Communication:** MAVLink, UDP Sockets
* **Visualization:** RViz2
* **Programming Languages:** Python

## Prerequisites & Installation

### 1. System Requirements
* **OS:** Ubuntu 22.04 
* **Middleware:** ROS 2 Humble (or compatible)
* **Simulation Framework:** Gazebo & ArduPilot SITL

### 2. Install Dependencies
Ensure you have the required ROS 2 computer vision packages and Python libraries installed. Open a terminal and run:

```bash
sudo apt update
sudo apt install python3-pip python3-opencv
sudo apt install ros-humble-cv-bridge ros-humble-vision-opencv ros-humble-tf2-ros ros-humble-tf-transformations
pip3 install pymavlink transforms3d
```
### 3. Setup the Workspace
Create a ROS 2 workspace (if you don't have one already) and clone this repository:
```bash
mkdir -p ~/drone_project/src
cd ~/drone_project/src
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
``` 
### 4. Build the Project

Navigate back to the root of your workspace, resolve any missing ROS dependencies, and build the packages:
```bash
cd ~/drone_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```
## How to Run 
To run the full simulation and control system, you will need to launch the different components. Open separate terminals for the following steps:

Terminal 1: Source and Launch the ROS 2 Nodes for simulation
```bash
export ROS_LOCALHOST_ONLY=0
cd ~/dron_project
source install/setup.bash
ros2 launch dron_project dron_simulation_launch.py
```
Terminal 2: Source and Launch the ROS 2 Nodes for control
```bash 
export ROS_LOCALHOST_ONLY=0
cd ~/dron_project
source install/setup.bash
ros2 launch dron_project dron_control_launch.py
```
Once the drone is armed and takes off, you can interact with the live camera feed window to command the drone, and monitor the 3D transformations in RViz2.

Terminal 3: Try out the safety logic for low battery
```bash 
export ROS_LOCALHOST_ONLY=0
cd ~/dron_project
source install/setup.bash
ros2 topic pub --once /battery_status std_msgs/msg/Float32 "{data: 15.0}"
```
## Results
The developed system enables an operator to select navigation targets directly from the camera feed while maintaining autonomous flight execution and safety monitoring.

The integration of ROS 2, OpenCV, Gazebo, ArduPilot SITL, and MAVLink successfully demonstrates the feasibility of image-based drone navigation in a simulated environment, providing both intuitive user interaction and real-time system visualization through RViz2.

## Future Work
* **Hardware Deployment:** Transition the ROS 2 software architecture from the simulation environment to a physical real-world drone.
* **Collision Avoidance:** Implement a forward collision avoidance system to halt the drone if a user selects an unreachable target behind a physical barrier.
* **Object Tracking:** Integrate a Convolutional Neural Network (CNN) to automatically select and track objects of interest without the need for manual operator clicks.
