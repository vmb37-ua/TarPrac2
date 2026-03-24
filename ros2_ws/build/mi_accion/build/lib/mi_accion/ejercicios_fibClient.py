import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from interfaz.action import EjFibonacci
from std_msgs.msg import String 

class EjFibonacciClient(Node):

    def __init__(self):
        super().__init__('ejercicios_fibClient')
        
        self._action_client = ActionClient(self, EjFibonacci, 'ejFibonacci')
        
        self.declare_parameter('orden', 10)
        
        self.estado_pub = self.create_publisher(String, '/estado_accion', 10)
        
        self.en_proceso = False
        self.timer = self.create_timer(0.5, self.timer_callback)

    def timer_callback(self):
        if self.en_proceso:
            msg = String()
            msg.data = 'en proceso'
            self.estado_pub.publish(msg)

    def send_goal(self):
        goal_msg = EjFibonacci.Goal()
        goal_msg.orden = self.get_parameter('orden').get_parameter_value().integer_value

        self.get_logger().info(f'Enviando objetivo con orden: {goal_msg.orden}')
        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Objetivo rechazado :(')
            return

        self.get_logger().info('Objetivo aceptado :)')
        self.en_proceso = True

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        self.en_proceso = False 
        
        result = future.result().result
        self.get_logger().info(f'Resultado final de la secuencia: {result.secuencia_final}')
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Feedback recibido (Raíz media int): {feedback.secuencia_actual}')

def main(args=None):
    rclpy.init(args=args)
    action_client = EjFibonacciClient()
    action_client.send_goal()
    rclpy.spin(action_client)

if __name__ == '__main__':
    main()