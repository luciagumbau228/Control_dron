#!/usr/bin/env python3
import rclpy
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


node = None
tf_broadcaster = None

def state_callback(msg):
    model_name = 'iris_demo' 
    
    if model_name in msg.name:
        idx = msg.name.index(model_name)
        pose = msg.pose[idx]
        

        t = TransformStamped()
        t.header.stamp = node.get_clock().now().to_msg()
        t.header.frame_id = 'world'       # El mundo global
        t.child_frame_id = 'base_link'    # El centro de tu dron
        

        t.transform.translation.x = pose.position.x
        t.transform.translation.y = pose.position.y
        t.transform.translation.z = pose.position.z
        

        t.transform.rotation = pose.orientation
        

        tf_broadcaster.sendTransform(t)

def main(args=None):
    global node, tf_broadcaster
    
    rclpy.init(args=args)
    node = rclpy.create_node('drone_tf_broadcaster')
    

    tf_broadcaster = TransformBroadcaster(node)
    node.create_subscription(ModelStates, '/gazebo/model_states', state_callback, 10)
    
    rclpy.spin(node)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
