# Víctor Mingorance Boix 74536760Q

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class NodoRecolectorContinuo(Node):
    def __init__(self):
        super().__init__('nodo_recolector_fruta')
        
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.arm_client = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')

        # Con el timer podemos medir bien los tiempos (cada tick 0.5s porque son 2Hz)
        self.timer = self.create_timer(0.5, self.control_loop)
        
        self.fase = 'ACERCAMIENTO'
        self.ticks = 0

    def control_loop(self):
        msg = Twist()
        
        if self.fase == 'ACERCAMIENTO': # Solo avanza la primera vez para acercarse a la fila de arboles
            msg.linear.x = 0.15 
            self.get_logger().info('Avanzando hacia los arboles...')
            self.ticks += 1
            if self.ticks >= 6:
                self.fase = 'FRENADO_ESTABLE'
                self.ticks = 0
                
        elif self.fase == 'FRENADO_ESTABLE':
            msg.linear.x = 0.0
            self.get_logger().info('Estabilizando base...')
            self.ticks += 1
            if self.ticks >= 2: 
                self.fase = 'EXTENDER_BRAZO'
                self.mover_brazo([0.0, 0.5, 0.2, -0.7]) # Coordenadas en radianes de los motores del brazo que simbolizan la posición final
                self.ticks = 0
                
        elif self.fase == 'EXTENDER_BRAZO':
            self.get_logger().info('Recolectando fruta madura...')
            self.ticks += 1
            if self.ticks >= 6:  # Damos 3 segundos para que el brazo llegue
                self.fase = 'RETRAER_BRAZO'
                self.mover_brazo([0.0, -1.0, 0.3, 0.7]) # Posición recogida
                self.ticks = 0
                
        elif self.fase == 'RETRAER_BRAZO':
            self.get_logger().info('Retrayendo manipulador...')
            self.ticks += 1
            if self.ticks >= 6:  # Da 3 segundos para que el brazo vuelva
                self.fase = 'GIRAR_IZQ'
                self.ticks = 0
                
        elif self.fase == 'GIRAR_IZQ':
            msg.angular.z = 0.52 
            self.get_logger().info('Girando 90 grados para seguir la fila...')
            self.ticks += 1
            if self.ticks >= 6:  # Aprox 3 segundos girando = ~90 grados ()
                self.fase = 'AVANZAR_FILA'
                self.ticks = 0
                
        elif self.fase == 'AVANZAR_FILA':
            msg.linear.x = 0.15
            self.get_logger().info('Desplazándose al siguiente frutal...')
            self.ticks += 1
            if self.ticks >= 7:  # 3.5 segundos desplazándose lateralmente
                self.fase = 'GIRAR_DER'
                self.ticks = 0
                
        elif self.fase == 'GIRAR_DER':
            msg.angular.z = -0.52
            self.get_logger().info('Encarando el nuevo objetivo...')
            self.ticks += 1
            if self.ticks >= 6:
                self.fase = 'FRENADO_ESTABLE' # El bucle vuelve a comenzar
                self.ticks = 0
                self.get_logger().info('--- INICIANDO NUEVO CICLO DE RECOLECCIÓN ---')

        self.publisher_.publish(msg)

    # Funcion controladora del brazo robótico
    def mover_brazo(self, posiciones_radianes):
        if not self.arm_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().error('Controlador del brazo no disponible.')
            return
            
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
        
        punto = JointTrajectoryPoint()
        punto.positions = posiciones_radianes
        punto.time_from_start = Duration(sec=2, nanosec=0)
        
        goal_msg.trajectory.points = [punto]

        # Le enviamos la peticion al plugin para que mueva el brazo hacia las posiciones en radianes que hemos solicitado
        self.arm_client.send_goal_async(goal_msg)

def main(args=None):
    rclpy.init(args=args)
    nodo = NodoRecolectorContinuo()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
