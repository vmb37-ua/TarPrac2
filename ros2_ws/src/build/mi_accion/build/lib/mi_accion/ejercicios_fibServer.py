import time
import math

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from interfaz.action import EjFibonacci


class FibonacciActionServer(Node):

    def __init__(self):
        super().__init__('ejercicios_fibServer')
        self._action_server = ActionServer(
            self,
            EjFibonacci,
            'ejFibonacci',
            self.execute_callback)

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        feedback_msg = EjFibonacci.Feedback()
        secuencia = [0, 1]

        for i in range(1, goal_handle.request.orden):
            secuencia.append(secuencia[i] + secuencia[i-1])
            suma = sum(secuencia)
            media = suma / len(secuencia)
    
            feedback_msg.secuencia_actual = [math.sqrt(media)]
            
            self.get_logger().info('Feedback: {0}'.format(math.sqrt(media)))
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()

        result = EjFibonacci.Result()
        result.secuencia_final = secuencia
        return result


def main(args=None):
    rclpy.init(args=args)
    fibonacci_action_server = FibonacciActionServer()
    rclpy.spin(fibonacci_action_server)

if __name__ == '__main__':
    main()