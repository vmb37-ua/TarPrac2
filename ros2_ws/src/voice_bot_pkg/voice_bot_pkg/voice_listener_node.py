#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class FakeMicNode(Node):
    def __init__(self):
        super().__init__('fake_mic_node')
        # Creamos el publicador en el tópico /voice_command
        self.publisher_ = self.create_publisher(String, '/voice_command', 10)
        self.get_logger().info('Falso micrófono iniciado. Listo para transmitir.')

    def read_and_publish(self):
        # Bucle infinito para seguir pidiendo texto por teclado
        while rclpy.ok():
            try:
                # Pedimos el input por teclado
                comando = input("\n🎙️  Escribe un comando (ej. 'COCINA', 'BASE') y pulsa Enter: ")
                
                # Preparamos y enviamos el mensaje
                msg = String()
                msg.data = comando.strip().upper() # Quitamos espacios y ponemos en mayúsculas
                
                if msg.data:
                    self.publisher_.publish(msg)
                    self.get_logger().info(f'Mensaje enviado: "{msg.data}"')
                    
            except (KeyboardInterrupt, EOFError):
                self.get_logger().info('\nApagando el micrófono...')
                break

def main(args=None):
    rclpy.init(args=args)
    node = FakeMicNode()
    
    # Ejecutamos nuestra función de lectura en lugar del spin habitual
    # ya que input() pausa el programa esperando tu respuesta
    node.read_and_publish()
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()