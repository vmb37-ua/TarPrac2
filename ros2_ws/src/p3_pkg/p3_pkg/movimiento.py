#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import sys
import time
import math

# pasa de un angulo cualquiera a su valor entre -pi y pi
def normalizar(angulo):
    while angulo >  math.pi: angulo -= 2 * math.pi
    while angulo < -math.pi: angulo += 2 * math.pi
    return angulo

class Movimiento(Node):

    def __init__(self, modo):
        super().__init__('movimiento')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)

        self.x       = 0.0
        self.y       = 0.0
        self.yaw     = 0.0
        self.odom_ok = False

        # pequeño tiempo para que el publisher conecte bien
        time.sleep(1.0)

        if modo == 0:
            self.lineal(2.0)
        elif modo == 1:
            self.triangulo(3.0)
        elif modo == 2:
            self.cuadrado(1.0)
        elif modo == 3:
            self.infinito()
        else:
            self.get_logger().info("Modo no válido. Usa 0, 1, 2 o 3.")

        self.parar()

    def odom_cb(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)
        self.odom_ok = True

    def publicar(self, lin=0.0, ang=0.0, dur=1.0):
        msg = Twist()
        msg.linear.x = lin
        msg.angular.z = ang

        t_end = time.time() + dur
        while time.time() < t_end:
            self.pub.publish(msg)
            time.sleep(0.05)

    def parar(self):
        self.publicar(0.0, 0.0, 0.5)
        time.sleep(0.2)

    def lineal(self, distancia):
        v = 0.2
        if distancia < 0:
            v = -0.2
        t = abs(distancia / v)
        self.publicar(v, 0.0, t)
        self.parar()

    def girar(self, angulo):
        Kp         = 1.5
        tolerancia = 0.001   # tolerancia para decidir si ya hemos alcanzado el angulo objetivo
        w_max      = 0.6    
        w_min      = 0.01   

        rclpy.spin_once(self, timeout_sec=0.05)
        yaw_objetivo = normalizar(self.yaw + angulo)

        msg = Twist()

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.05)

            error = normalizar(yaw_objetivo - self.yaw)

            if abs(error) < tolerancia:
                msg.angular.z=0.0
                self.pub.publish(msg)
                break

            # Velocidad proporcional al error, limitada entre w_min y w_max
            w = Kp * error
            signo = 1.0 if w >= 0 else -1.0
            w = signo * max(w_min, min(w_max, abs(w)))

            msg.angular.z = w
            self.pub.publish(msg)

        self.parar()

    def triangulo(self, lado):
        for _ in range(3):
            self.lineal(lado)
            self.girar(2 * math.pi / 3)   # 120 grados

    def cuadrado(self, lado):
        for _ in range(4):
            self.lineal(lado)
            self.girar(-math.pi / 2)       # 90 grados

    def infinito(self):

        lado_vertical = 0.5
        lado_diagonal = 1.0

        self.girar(math.pi / 2)

        self.lineal(lado_vertical)

        self.girar(-math.pi / 3)          # -60°
        self.lineal(lado_diagonal)

        self.girar(2 * math.pi / 3)       # +120°
        self.lineal(lado_diagonal)

        self.girar(2 * math.pi / 3)       # +120°
        self.lineal(lado_vertical)

        self.girar(2 * math.pi / 3)       # +120°
        self.lineal(lado_diagonal)

        self.girar(-2 * math.pi / 3)      # -120°
        self.lineal(lado_diagonal)


def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) < 2:
        print("Uso: ros2 run p3_pkg movimiento <0-3>")
        rclpy.shutdown()
        return

    try:
        modo = int(sys.argv[1])
    except ValueError:
        print("El argumento debe ser un entero: 0, 1, 2 o 3")
        rclpy.shutdown()
        return

    Movimiento(modo)

    rclpy.shutdown()


if __name__ == '__main__':
    main()