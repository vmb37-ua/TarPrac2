import rclpy
from rclpy.node import Node
from interfaz.msg import P2pkgMensaje

class NodoSubEjercicio2(Node):
    def __init__(self):
        super().__init__('nodosub_ejercicio2')
        self.subscription = self.create_subscription(
            P2pkgMensaje,
            '/topic_ejercicio2',
            self.listener_callback,
            10)
        self.subscription

    def listener_callback(self, msg):
        self.get_logger().info(f"Recibido -> Fecha: {msg.fecha}, Numero: {msg.numero}, Pos_X: {msg.posicion.position.x:.4f}, Ori_W: {msg.posicion.orientation.w:.4f}")

def main(args=None):
    rclpy.init(args=args)
    nodo = NodoSubEjercicio2()
    rclpy.spin(nodo)
    nodo.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()