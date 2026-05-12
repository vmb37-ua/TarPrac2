#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket

class UdpMicNode(Node):
    def __init__(self):
        super().__init__('udp_mic_node')
        self.publisher_ = self.create_publisher(String, '/voice_command', 10)
        
        # Creamos el socket para recibir los datos
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 9999))
        self.sock.setblocking(False) 
        
        self.timer = self.create_timer(0.1, self.check_udp)
        self.get_logger().info("Actualización de recepción de datos por el socket")

    def check_udp(self):
        try:
            # Leemos el JSON
            data, _ = self.sock.recvfrom(4096)
            texto_json = data.decode('utf-8')
            
            self.get_logger().info(f"--> JSON recibido por UDP. Reenviando...")

            # Pasamos el JSON intacto al topic de ROS2
            msg = String()
            msg.data = texto_json
            self.publisher_.publish(msg)
                    
        except BlockingIOError:
            pass 

def main():
    rclpy.init()
    node = UdpMicNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
