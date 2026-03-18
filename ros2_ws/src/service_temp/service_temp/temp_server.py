import rclpy
from rclpy.node import Node
from interfaz.srv import ConvertTemp

class TempServer(Node):
    def __init__(self):
        super().__init__('temp_server')
        self.srv = self.create_service(ConvertTemp, 'convertir_temp', self.convert_callback)

    def convert_callback(self, request, response):
        if request.conversion_type == 'Cel_to_Far':
            response.converted_temp = (request.input_temp * 9.0/5.0) + 32.0
            self.get_logger().info(f"Convirtiendo {request.input_temp} C a F")
        elif request.conversion_type == 'Far_to_Cel':
            response.converted_temp = (request.input_temp - 32.0) * 5.0/9.0
            self.get_logger().info(f"Convirtiendo {request.input_temp} F a C")
        else:
            self.get_logger().warn("Tipo de conversión inválido.")
            response.converted_temp = 0.0

        return response

def main(args=None):
    rclpy.init(args=args)
    node = TempServer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
