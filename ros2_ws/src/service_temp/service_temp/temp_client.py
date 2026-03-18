import sys
import rclpy
from rclpy.node import Node
from interfaz.srv import ConvertTemp

class TempClient(Node):
    def __init__(self):
        super().__init__('temp_client')
        self.cli = self.create_client(ConvertTemp, 'convertir_temp')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Servicio no disponible, esperando...')
        self.req = ConvertTemp.Request()

    def send_request(self, temp, conv_type):
        self.req.input_temp = float(temp)
        self.req.conversion_type = conv_type
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) != 3:
        print("Uso: ros2 run service_temp client <temperatura> <Cel_to_Far|Far_to_Cel>")
        sys.exit(1)

    client = TempClient()
    temp_input = sys.argv[1]
    conv_type = sys.argv[2]

    response = client.send_request(temp_input, conv_type)
    client.get_logger().info(f'Resultado: {response.converted_temp:.2f}')

    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
