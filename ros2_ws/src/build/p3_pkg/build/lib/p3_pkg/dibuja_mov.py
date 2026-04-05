#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt


class DibujaMovimiento(Node):
    def __init__(self):
        super().__init__('dibuja_mov')
        self.xs = []
        self.ys = []

        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.get_logger().info('Escuchando /odom y guardando trayectoria...')

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.xs.append(x)
        self.ys.append(y)



def main(args=None):
    rclpy.init(args=args)
    node = DibujaMovimiento()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('Detenido por teclado. Dibujando trayectoria...')
    finally:
        xs = node.xs
        ys = node.ys

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

        if xs and ys:
            plt.figure()
            plt.plot(xs, ys, marker='o')
            plt.xlabel('X (m)')
            plt.ylabel('Y (m)')
            plt.title('Trayectoria del robot')
            plt.grid(True)
            plt.axis('equal')
            plt.show()
        else:
            print('No se recogieron puntos de /odom.')


if __name__ == '__main__':
    main()