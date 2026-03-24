#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time
import math


class Aparcamiento(Node):

    def __init__(self):
        super().__init__('aparcamiento')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        time.sleep(1.0)

        self.aparcar()
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
        v = 0.15 if distancia >= 0 else -0.15
        t = abs(distancia / v)
        self.publicar(v, 0.0, t)
        self.parar()

    def girar(self, angulo):
        w = 0.3 if angulo >= 0 else -0.3
        t = abs(angulo / w)
        self.publicar(0.0, w, t)
        self.parar()

    def aparcar(self):
        # avanzar hasta quedar frente al centro de la plaza
        self.lineal(1.5)

        # girar 90 grados a la derecha para encarar la entrada
        self.girar(-math.pi / 2 - 0.1)

        # entrar en la plaza hasta el centro
        self.lineal(1.5)

        # ponerse de cara hacia afuera
        self.girar(math.pi + 0.1)

        self.get_logger().info('Aparcamiento completado')


def main(args=None):
    rclpy.init(args=args)
    Aparcamiento()
    rclpy.shutdown()


if __name__ == '__main__':
    main()