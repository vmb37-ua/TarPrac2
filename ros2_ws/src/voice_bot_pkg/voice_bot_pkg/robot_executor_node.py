#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import json

class RobotExecutor(Node):
    def __init__(self):
        super().__init__('robot_executor')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_voice = self.create_subscription(String, '/voice_command', self.voice_callback, 10)
        self.sub_laser = self.create_subscription(LaserScan, '/scan', self.laser_callback, qos_profile_sensor_data)

        # Las tareas individuales se encolan
        self.cola_tareas = []
        self.comando_actual = "PARAR"
        self.ticks_restantes = 0
        
        self.obstacle_ahead = False
        
        # Bucle a 10 Hz (0.1s por ciclo)
        self.timer = self.create_timer(0.1, self.move_robot)
        self.get_logger().info('Esperando plan JSON...')

    def voice_callback(self, msg):
        try:
            # Intentamos leer el mensaje como JSON
            datos_ia = json.loads(msg.data)
            if "tareas" in datos_ia:
                self.cola_tareas = datos_ia["tareas"]
                self.get_logger().info(f'Nuevo plan recibido: {len(self.cola_tareas)} tareas en cola.')
                # Reseteamos la tarea actual para que empiece de cero
                self.ticks_restantes = 0 
        except json.JSONDecodeError:
            # Si nos llega un comando simple antiguo (no debería ocurrir desde que usamos JSON, pero por si usamos la versión antigua)
            self.cola_tareas = [{"accion": msg.data.upper(), "tiempo": 2.0}]

    def laser_callback(self, msg):
    	# Usamos en todo momento el LIDAR para evitar chocarnos de frente con objetos en un rango de 30º
        cono_frontal = msg.ranges[0:15] + msg.ranges[345:359]
        distancias_validas = [d for d in cono_frontal if 0.0 < d < float('inf')]
        
        if distancias_validas:
            distancia_minima = min(distancias_validas)
            if distancia_minima < 0.4:
                if not self.obstacle_ahead:
                    self.get_logger().warning('CHOQUE CON OBJETO DE FRENTE')
                    # Borramos la cola al chocar y detenemos las tareas
                    self.cola_tareas = [] 
                    self.ticks_restantes = 0
                    self.comando_actual = "PARAR"
                self.obstacle_ahead = True
            else:
                self.obstacle_ahead = False

    def move_robot(self):
        twist = Twist()

        # Si hay algo en frente NO de avanza
        if self.obstacle_ahead and self.comando_actual == "AVANZAR":
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.publisher_.publish(twist)
            return

        if self.ticks_restantes > 0:
            # Si estamos ejecutando una tarea, restamos 1 tick (0.1 segundos)
            self.ticks_restantes -= 1
        else:
            # Si el tiempo ha terminado, pasamos a la siguiente tarea de la cola
            if len(self.cola_tareas) > 0:
                tarea = self.cola_tareas.pop(0)
                self.comando_actual = tarea.get("accion", "PARAR").upper()
                tiempo_segundos = float(tarea.get("tiempo", 1.0))
                self.ticks_restantes = int(tiempo_segundos * 10)
                
                self.get_logger().info(f'Ejecutando: {self.comando_actual} durante {tiempo_segundos}s')
            else:
                self.comando_actual = "PARAR"

        # Movimento de las ruedas
        if self.comando_actual == "AVANZAR":
            twist.linear.x = 0.2
        elif self.comando_actual == "ATRAS":
            twist.linear.x = -0.2
        elif self.comando_actual == "DERECHA":
            twist.angular.z = -0.5
        elif self.comando_actual == "IZQUIERDA":
            twist.angular.z = 0.5
        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = RobotExecutor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
