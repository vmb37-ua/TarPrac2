#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


VEL_LINEAL          = 0.15  # m/s
VEL_ANGULAR         = 0.4   # rad/s
DIST_PARED_OBJETIVO = 0.5   # m — distancia ideal a la pared derecha
DIST_OBSTACULO      = 0.45  # m — obstáculo al frente
DIST_PARED_CERCA    = 1.2   # m — a partir de aquí considera que HAY pared
Kp                  = 1.2   # ganancia proporcional

# Estados del robot
BUSCANDO_PARED  = 0   # fase inicial: avanza recto hasta encontrar cualquier pared
SIGUIENDO_PARED = 1   # fase normal: sigue la pared derecha


class ResolverLaberinto(Node):

    def __init__(self):
        super().__init__('resolver_laberinto')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)

        self.frente    = float('inf')
        self.derecha   = float('inf')
        self.izquierda = float('inf')
        self.scan_ok   = False

        self.estado = BUSCANDO_PARED
        self.get_logger().info('Fase inicial: buscando pared...')

        self.timer = self.create_timer(0.1, self.control_loop)

    # ── LiDAR ─────────────────────────────────────────────────────────────────
    def scan_cb(self, msg):
        ranges = msg.ranges
        n = len(ranges)

        def sector_min(centro, apertura=15):
            vals = []
            for d in range(-apertura, apertura + 1):
                v = ranges[(centro + d) % n]
                if msg.range_min < v < msg.range_max:
                    vals.append(v)
            return min(vals) if vals else float('inf')

        self.frente    = sector_min(0)
        self.derecha   = sector_min(270)
        self.izquierda = sector_min(90)
        self.scan_ok   = True

    # ── Bucle de control ──────────────────────────────────────────────────────
    def control_loop(self):
        if not self.scan_ok:
            return

        self.get_logger().info(
            f'[{"BUSCANDO" if self.estado == BUSCANDO_PARED else "SIGUIENDO"}] '
            f'frente={self.frente:.2f} der={self.derecha:.2f} izq={self.izquierda:.2f}')

        cmd = Twist()

        # ── Fase 0: BUSCANDO_PARED ────────────────────────────────────────────
        # El robot avanza recto hasta que detecta una pared cerca en cualquier
        # dirección. Cuando la encuentra, gira para colocarla a su derecha
        # y pasa a la fase de seguimiento.
        if self.estado == BUSCANDO_PARED:

            pared_minima = min(self.frente, self.derecha, self.izquierda)

            if pared_minima > DIST_PARED_CERCA:
                # Todavía no hay ninguna pared cerca: avanzar recto
                self.get_logger().info('Avanzando en busca de pared...')
                cmd.linear.x  = VEL_LINEAL
                cmd.angular.z = 0.0

            else:
                # Encontramos una pared: orientarnos para tenerla a la derecha
                # Giramos a la derecha hasta que la pared quede en el sector derecho
                if self.derecha <= DIST_PARED_CERCA:
                    # La pared ya está a la derecha, pasamos a seguimiento
                    self.get_logger().info('Pared encontrada a la derecha. Iniciando seguimiento.')
                    self.estado = SIGUIENDO_PARED
                else:
                    # La pared está al frente o a la izquierda: girar a la derecha
                    self.get_logger().info('Pared encontrada. Girando para colocarla a la derecha...')
                    cmd.linear.x  = 0.0
                    cmd.angular.z = -VEL_ANGULAR

        # ── Fase 1: SIGUIENDO_PARED ───────────────────────────────────────────
        else:

            if self.frente < DIST_OBSTACULO:
                # Obstáculo al frente: girar izquierda
                self.get_logger().info('Obstaculo al frente → girando izquierda')
                cmd.linear.x  = 0.0
                cmd.angular.z = VEL_ANGULAR

            elif self.derecha > DIST_PARED_CERCA:
                # Perdimos la pared derecha (esquina): avanzar recto
                self.get_logger().info('Sin pared derecha → avanzando recto')
                cmd.linear.x  = VEL_LINEAL
                cmd.angular.z = 0.0

            else:
                # Seguir la pared con controlador proporcional
                w = VEL_ANGULAR
                cmd.linear.x  = VEL_LINEAL
                cmd.angular.z = w

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ResolverLaberinto()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()