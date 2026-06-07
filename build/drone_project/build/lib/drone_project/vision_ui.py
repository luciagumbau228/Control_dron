import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Vector3
from cv_bridge import CvBridge
import cv2
import numpy as np
import math
from rclpy.qos import qos_profile_sensor_data

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
FOV_VERTICAL = 1.068  
FOV_HORIZONTAL = 1.396 
CAM_PITCH_DEG = 30.0

node = None
move_pub = None
safe_zone_pub = None 
bridge = CvBridge()

current_image = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), np.uint8)
current_depth = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH), np.float32) 
current_altitude = 0.0 

def gps_callback(msg):
    global current_altitude
    current_altitude = max(0.0, msg.z)
    
def depth_callback(msg):
    global current_depth, bridge, node
    try:
        current_depth = bridge.imgmsg_to_cv2(msg, "32FC1")
        h, w = current_depth.shape
        
        # BÚSQUEDA DE ZONA DE ATERRIZAJE (Mitad inferior de la imagen)
        col_start_land = int(w * 0.2) 
        col_end_land = int(w * 0.8)
        row_start_land = int(h * 0.5) 
        row_end_land = h
        
        land_region = current_depth[row_start_land:row_end_land, col_start_land:col_end_land]
        valid_depths = land_region[np.isfinite(land_region)]
        valid_depths = valid_depths[valid_depths > 0.1] # Quitar ruido
        
        sz_msg = Vector3()
        if valid_depths.size > 0:
            min_depth = np.min(valid_depths)
            
            # Subimos el umbral a 3.0m. Si hay más de 3m libres en diagonal, asumimos que es suelo despejado.
            if min_depth > 3.0:
                sz_msg.x = 0.0 
                sz_msg.y = 0.0
                sz_msg.z = 1.0 # ¡Vía libre para bajar!
            else:
                # ¡HAY UN EDIFICIO / OBSTÁCULO! 
                # En lugar de avanzar hacia él, damos medio metro hacia atrás y buscamos por la derecha.
                sz_msg.x = -0.5 # Paso atrás para no rozar la cornisa
                sz_msg.y = 2.0  # Moverse de lado para rodear el edificio
                sz_msg.z = 1.0
        else:
            sz_msg.x = 0.0
            sz_msg.y = 0.0
            sz_msg.z = -1.0 # Sensor ciego
            
        safe_zone_pub.publish(sz_msg)

    except Exception as e:
        pass

def mouse_callback(event, x, y, flags, param):
    global node, move_pub, current_depth
    
    # CLIC IZQUIERDO: Navegación normal 2D a 3D
    if event == cv2.EVENT_LBUTTONDOWN:
        z_optico = current_depth[y, x]

        if math.isnan(z_optico) or math.isinf(z_optico) or z_optico <= 0.1:
            node.get_logger().warn('¡Punto inválido! Haz clic en otra parte.')
            return
            
        cy = IMAGE_HEIGHT / 2.0
        cx = IMAGE_WIDTH / 2.0
        focal_length_y = cy / math.tan(FOV_VERTICAL  / 2.0)
        focal_length_x = cx / math.tan(FOV_HORIZONTAL / 2.0)
        
        x_optico = (x - cx) * z_optico / focal_length_x  
        y_optico = (y - cy) * z_optico / focal_length_y  

        cam_pitch_rad = math.radians(CAM_PITCH_DEG)
        distancia_frontal = (z_optico * math.cos(cam_pitch_rad)) - (y_optico * math.sin(cam_pitch_rad))
        distancia_lateral = x_optico 
        
        msg = Vector3()
        msg.x = float(distancia_frontal)
        msg.y = float(distancia_lateral)
        msg.z = 0.0
        move_pub.publish(msg)
        
    # CLIC DERECHO: Forzar aterrizaje
    elif event == cv2.EVENT_RBUTTONDOWN:
        node.get_logger().warn('¡Usuario solicita aterrizaje forzado!')
        msg = Vector3()
        msg.x = 0.0
        msg.y = 0.0
        msg.z = -99.0 # Dispara el aterrizaje
        move_pub.publish(msg)
        
def image_callback(msg):
    global current_image, bridge, node, current_altitude
    try:
        current_image = bridge.imgmsg_to_cv2(msg, "bgr8")
        center_y = int(IMAGE_HEIGHT/2)
        cv2.line(current_image, (0, center_y), (IMAGE_WIDTH, center_y), (0, 255, 0), 1)
        if current_altitude > 0.5:
            cv2.putText(current_image, f"ALT: {current_altitude:.2f}m", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(current_image, "WAITING TAKEOFF...", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    except Exception as e:
        pass

def display_loop():
    global current_image
    cv2.imshow("FRONTAL VIEW", current_image)
    cv2.setMouseCallback("FRONTAL VIEW", mouse_callback)
    cv2.waitKey(1)

def main(args=None):
    global node, move_pub, safe_zone_pub
    rclpy.init(args=args)
    node = rclpy.create_node('vision_ui')

    move_pub = node.create_publisher(Vector3, 'vision_cmd', 10)
    safe_zone_pub = node.create_publisher(Vector3, 'safe_landing_zone', 10) 

    node.create_subscription(Vector3, 'current_gps', gps_callback, 10)
    node.create_subscription(Image, '/camera/image_raw', image_callback, qos_profile_sensor_data)
    node.create_subscription(Image, '/camera/depth/image_raw', depth_callback, qos_profile_sensor_data)
    
    node.create_timer(0.1, display_loop)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()