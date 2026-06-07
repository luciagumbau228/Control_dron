import rclpy
from std_msgs.msg import Float32, Bool
from geometry_msgs.msg import Vector3

node = None
drone_cmd_pub = None
land_pub = None

safe_zone_cmd = None
battery_critical = False
landing_in_progress = False

def send_movement(x, y, z):
    cmd = Vector3()
    cmd.x, cmd.y, cmd.z = float(x), float(y), float(z)
    drone_cmd_pub.publish(cmd)

def vision_callback(msg):
    global node, drone_cmd_pub, battery_critical
    
    if msg.z == -99.0:
        node.get_logger().error('¡INICIANDO AUTO-ATERRIZAJE FORZADO!')
        battery_critical = True # Engañamos al sistema para que active el bucle de aterrizaje
        send_movement(0.0, 0.0, 0.0)
        return
        
    if battery_critical:
        node.get_logger().warn('Comando manual ignorado: Modo aterrizaje activo.')
        return 
        
    node.get_logger().info(f'Navegando a: Avanzar {msg.x:.1f}m, Lateral {msg.y:.1f}m')
    drone_cmd_pub.publish(msg)

def battery_callback(msg):
    global node, battery_critical
    
    if msg.data <= 20.0 and not battery_critical and not msg.data == 0.0:
        node.get_logger().error(f'BATERÍA BAJA ({msg.data}%). INICIANDO BÚSQUEDA Y ATERRIZAJE.')
        battery_critical = True
        send_movement(0.0, 0.0, 0.0) 

def safe_zone_callback(msg):
    global safe_zone_cmd
    safe_zone_cmd = msg

def emergency_landing_loop():
    global node, land_pub, safe_zone_cmd, landing_in_progress, battery_critical
    
    if not battery_critical or landing_in_progress:
        return

    if safe_zone_cmd is not None and safe_zone_cmd.z > 0.0:
        dist_fwd = safe_zone_cmd.x
        dist_lat = safe_zone_cmd.y
        
        # Como ahora vision_ui manda x=0, y=0 cuando el suelo debajo es seguro, esto se cumplirá rápido
        if abs(dist_fwd) < 1.5 and abs(dist_lat) < 1.5:
            node.get_logger().info('¡Suelo despejado detectado! Enviando orden a motores para bajar.')
            msg = Bool()
            msg.data = True
            land_pub.publish(msg)
            landing_in_progress = True
        else:
            node.get_logger().info('Suelo no seguro. Avanzando para buscar otra zona...')
            send_movement(dist_fwd, dist_lat, 0.0)
    else:
        node.get_logger().info('Buscando suelo despejado...')
        send_movement(2.0, 0.0, 0.0)

def main(args=None):
    global node, drone_cmd_pub, land_pub
    
    rclpy.init(args=args)
    node = rclpy.create_node('mission_control')
    
    drone_cmd_pub = node.create_publisher(Vector3, 'body_cmd', 10)
    land_pub = node.create_publisher(Bool, 'land_cmd', 10) # <-- OJO A ESTO

    node.create_subscription(Vector3, 'vision_cmd', vision_callback, 10)
    node.create_subscription(Float32, 'battery_status', battery_callback, 10)
    node.create_subscription(Vector3, 'safe_landing_zone', safe_zone_callback, 10) 

    node.create_timer(2.0, emergency_landing_loop)

    node.get_logger().info('Mission Control Listo - Clic Izquierdo (Mover) / Clic Derecho (Aterrizar).')

    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()