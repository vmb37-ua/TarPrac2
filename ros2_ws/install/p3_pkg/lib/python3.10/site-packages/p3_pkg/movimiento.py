#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import time
import math


class Movimiento(Node):

    def __init__(self, modo):
        super().__init__('movimiento')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

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

    def lineal(self, distancia):
        v = 0.2
        if distancia < 0:
            v = -0.2
        t = abs(distancia / v)
        self.publicar(v, 0.0, t)
        self.parar()

    def girar(self, angulo):
        w = 0.5
        if angulo < 0:
            w = -0.5
        t = abs(angulo / w)
        self.publicar(0.0, w, t)
        self.parar()

    def triangulo(self, lado):
        for _ in range(3):
            self.lineal(lado)
            self.girar(2 * math.pi / 3)   # 120 grados

    def cuadrado(self, lado):
        for _ in range(4):
            self.lineal(lado)
            self.girar(math.pi / 2)       # 90 grados

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