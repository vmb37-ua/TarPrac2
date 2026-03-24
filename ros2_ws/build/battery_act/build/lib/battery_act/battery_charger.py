import time
import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.node import Node
from interfaz.action import Battery

class BatteryCharger(Node):
    def __init__(self):
        super().__init__('battery_charger')
        self._action_server = ActionServer(
            self,
            Battery,
            'battery_discharge',
            execute_callback=self.execute_callback,
            cancel_callback=self.cancel_callback
        )

    def cancel_callback(self, cancel_request):
        self.get_logger().info('¡Petición de cancelación recibida!')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.get_logger().info('Comenzando descarga de batería...')
        
        feedback_msg = Battery.Feedback()
        current_battery = 100
        target = goal_handle.request.target_percentage
        
        while current_battery > target:
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Acción cancelada.')
                result = Battery.Result()
                result.warning = "Descarga abortada por el usuario."
                return result
            
            feedback_msg.current_percentage = current_battery
            self.get_logger().info(f'Batería al {current_battery}%')
            goal_handle.publish_feedback(feedback_msg)
            
            current_battery -= 5
            time.sleep(1.0)
        
        goal_handle.succeed()
        result = Battery.Result()
        result.warning = "Batería Baja, ¡por favor cargue el robot!"
        return result

def main(args=None):
    rclpy.init(args=args)
    node = BatteryCharger()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()