import rclpy
from std_msgs.msg import Float32, Bool
from geometry_msgs.msg import Vector3
from pymavlink import mavutil
import time

# Variables globales
connection = None
node = None
battery_pub = None
current_pos_pub = None


def arm_vehicle():
    global connection, node
    node.get_logger().info('Arming...')
    
    # Bucle de insistencia para armar
    while True:
        connection.mav.command_long_send(
            connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
        
        msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg and (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            node.get_logger().info('Dron ARMADO.')
            break

def takeoff():
    global connection, node
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 6)
    node.get_logger().info(f'Despegando a 6 m...')
    time.sleep(8)     

def body_move_callback(msg):
    global connection, node
    
    forward = msg.x
    right = msg.y
    down = msg.z

    node.get_logger().info(f'Ejecutando movimiento: {forward:.1f}m Frontal, {right:.1f}m Lateral')
    
    connection.mav.set_position_target_local_ned_send(
        0, 
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, 
        0b110111111000, 
        forward,  
        right,    
        down,     
        0, 0, 0,  
        0, 0, 0,  
        0, 0      
    )

def read_battery_loop():
    global connection, battery_pub, current_pos_pub
    
    # 1. Leer Batería
    msg_batt = connection.recv_match(type='BATTERY_STATUS', blocking=True, timeout=0.1)
    if msg_batt:
        battery_pub.publish(Float32(data=float(msg_batt.battery_remaining)))

    # 2. Leer Posición
    msg_pos = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=0.1)
    if msg_pos:
        current_gps = Vector3()
        current_gps.x = msg_pos.lat / 1e7
        current_gps.y = msg_pos.lon / 1e7
        current_gps.z = msg_pos.relative_alt / 1000.0
        current_pos_pub.publish(current_gps)

def land_callback(msg):
    global connection, node
    if msg.data:
        node.get_logger().warn('ATERRIZANDO...')
        connection.mav.command_long_send(
            connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, 0, 0)
        raise SystemExit

def main(args=None):
    global connection, node, battery_pub, current_pos_pub
    
    rclpy.init(args=args)
    node = rclpy.create_node('battery_gps')
    
    #1. Conexión MAVLink
    node.get_logger().info('Conectando al SITL...')
    connection = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    connection.wait_heartbeat()
    node.get_logger().info('¡Conectado a SITL!')

    node.get_logger().info('Calibrando sensores y esperando señal GPS (15 segundos)...')
    time.sleep(15)

    #2. Preparar Dron
    connection.set_mode('GUIDED')
    arm_vehicle()
    takeoff()

    # ROS Setup
    battery_pub = node.create_publisher(Float32, 'battery_status', 10)
    current_pos_pub = node.create_publisher(Vector3, 'current_gps', 10)
    
    node.create_subscription(Vector3, 'body_cmd', body_move_callback, 10)
    node.create_subscription(Bool, 'land_cmd', land_callback, 10)
    
    node.create_timer(1.0, read_battery_loop)

    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()