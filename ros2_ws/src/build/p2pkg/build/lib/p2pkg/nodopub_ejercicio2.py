import rclpy
from rclpy.node import Node
from interfaz.msg import P2pkgMensaje
from random import random
from datetime import date

class NodoPubEjercicio2(Node):
    def __init__(self):
        super().__init__('nodopub_ejercicio2')
        
        self.declare_parameter('numero', 5)
        
        self.publisher_ = self.create_publisher(P2pkgMensaje, '/topic_ejercicio2', 10)
        
        timer_period = 1.0
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        msg = P2pkgMensaje()
        
        msg.numero = self.get_parameter('numero').get_parameter_value().integer_value
        
        msg.fecha = str(date.today())
        
        msg.posicion.position.x = random()
        msg.posicion.position.y = random()
        msg.posicion.position.z = random()
        msg.posicion.orientation.x = random()
        msg.posicion.orientation.y = random()
        msg.posicion.orientation.z = random()
        msg.posicion.orientation.w = random()
        
        self.publisher_.publish(msg)
        
        self.get_logger().info(f"Publicando -> Fecha: {msg.fecha}, Numero: {msg.numero}, Pos_X: {msg.posicion.position.x:.4f}, Ori_W: {msg.posicion.orientation.w:.4f}")

def main(args=None):
    rclpy.init(args=args)
    nodo = NodoPubEjercicio2()
    rclpy.spin(nodo)
    nodo.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()