#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import sys
import time
import math

# Esta funcion normaliza el angulo en el rango
def normalizar(angulo):
    return math.atan2(math.sin(angulo), math.cos(angulo))

class Movimiento(Node):

    def __init__(self, modo):
        super().__init__('movimiento')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)

        self.x       = 0.0
        self.y       = 0.0
        self.yaw     = 0.0
        self.odom_ok = False

        self.get_logger().info("Esperando a conectar con /odom...")
        
        while rclpy.ok() and not self.odom_ok:
            rclpy.spin_once(self, timeout_sec=0.1)
            
        self.get_logger().info("Odometría recibida. Iniciando...")

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
        while time.time() < t_end and rclpy.ok():
            self.pub.publish(msg)
            time.sleep(0.05)

    def parar(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.pub.publish(msg)
        time.sleep(0.2)

    def lineal(self, distancia):
        Kp_lin = 1.0        
        Kp_ang = 2.5        
        Ki_ang = 0.2        
        
        tolerancia_dist = 0.01  
        v_max = 0.2         
        v_min = 0.05        

        rclpy.spin_once(self, timeout_sec=0.05)
        x_inicial = self.x
        y_inicial = self.y
        yaw_inicial = self.yaw  

        integral_yaw = 0.0
        tiempo_anterior = time.time()

        msg = Twist()

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.05)
            
            tiempo_actual = time.time()
            dt = tiempo_actual - tiempo_anterior
            tiempo_anterior = tiempo_actual
            
            if dt <= 0:
                continue

            dist_recorrida = math.sqrt((self.x - x_inicial)**2 + (self.y - y_inicial)**2)
            error_dist = abs(distancia) - dist_recorrida

            if error_dist < tolerancia_dist:
                self.parar()
                break

            v = Kp_lin * error_dist
            
            if v > v_max:
                v = v_max
            elif v < v_min:
                v = v_min
                
            if distancia < 0:
                v = -v

            error_yaw = normalizar(yaw_inicial - self.yaw)

            # Acumulamos el error en la Integral
            integral_yaw += error_yaw * dt
            
            limite_integral = 0.3
            if integral_yaw > limite_integral:
                integral_yaw = limite_integral
            elif integral_yaw < -limite_integral:
                integral_yaw = -limite_integral

            # Formula para corregir el error de rectas haciendo curvas
            w = (Kp_ang * error_yaw) + (Ki_ang * integral_yaw)

            msg.linear.x = v
            msg.angular.z = w
            self.pub.publish(msg)

    def girar_absoluto(self, yaw_objetivo):
        Kp = 2.0
        Ki = 0.2
        tolerancia = 0.005
        w_max = 1.0

        # Normalizacion del angulo
        yaw_objetivo = normalizar(yaw_objetivo)
        
        # Acumulacion del error
        integral_error = 0.0
        tiempo_anterior = time.time()

        msg = Twist()

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.05)
            
            tiempo_actual = time.time()
            dt = tiempo_actual - tiempo_anterior
            tiempo_anterior = tiempo_actual
            
            if dt <= 0:
                continue

            # El error se calcula siempre contra la meta absoluta fija
            error = normalizar(yaw_objetivo - self.yaw)

            if abs(error) < tolerancia:
                self.parar()
                time.sleep(0.5) # Por si aun hay inercia
                break

            integral_error += error * dt
            
            limite_integral = 0.5
            if integral_error > limite_integral: integral_error = limite_integral
            elif integral_error < -limite_integral: integral_error = -limite_integral

            w = (Kp * error) + (Ki * integral_error) # Formula para sacar la velocidad angular correctora

            if w > w_max:
                w = w_max
            elif w < -w_max:
                w = -w_max

            msg.angular.z = w
            self.pub.publish(msg)

    def triangulo(self, lado):
        
        rclpy.spin_once(self, timeout_sec=0.05)
        angulo_actual = self.yaw
        for i in range(3):
            self.lineal(lado)
            angulo_actual-=(2*math.pi/3)
            self.girar_absoluto(angulo_actual)

    def cuadrado(self, lado): 

        rclpy.spin_once(self, timeout_sec=0.05)
        angulo_actual = self.yaw
        for i in range(4):
            self.lineal(lado)
            angulo_actual-=(math.pi/2)
            self.girar_absoluto(angulo_actual)
        
        self.parar()

    def infinito(self):
        lado_vertical = 0.5
        lado_diagonal = 1.0

        rclpy.spin_once(self, timeout_sec=0.05)
        angulo_actual = self.yaw

        angulo_actual += math.pi / 2
        self.girar_absoluto(angulo_actual)
        self.lineal(lado_vertical)

        angulo_actual += 2 * math.pi / 3      # +120°
        self.girar_absoluto(angulo_actual)
        self.lineal(lado_diagonal)

        angulo_actual -= 2 * math.pi / 3      # +120°
        self.girar_absoluto(angulo_actual)
        self.lineal(lado_vertical)

        angulo_actual -= 2 * math.pi / 3      # +120°
        self.girar_absoluto(angulo_actual)
        self.lineal(lado_diagonal)

        self.parar()


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

    # Instanciamos el nodo. Al estar la lógica en el __init__, 
    # se ejecutará el movimiento de forma secuencial.
    nodo_movimiento = Movimiento(modo)

    # Una vez terminan los movimientos en el __init__, destruimos el nodo
    nodo_movimiento.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()