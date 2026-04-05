#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry

# Tiempo para que se ajuste bien la rotación
PAUSA_ASENTAMIENTO = 0.5  

# Velocidades
VEL_LINEAL = 0.2
VEL_LINEAL_LENTO = 0.07
VEL_ANGULAR_SUAVE = 0.08  

# Vlores de ajuste
KP_GIRO = 1.2
KP_ALINEACION = 1.0   
W_MAX = 0.25
W_MIN = 0.04
ZONA_FRENADO = 0.12
TOLERANCIA = 0.020 

# Umbrales
DIST_FRENTE_PARAR = 0.50
DIST_EMERGENCIA = 0.30
DIST_WARNING = 0.45
DIST_LEJOS = 0.65
DIST_DETECTAR_PARED = 1.2
DIST_AVANCE_PASILLO = 0.45 

# Estados
BUSCANDO = 0 # Buscando la pared (primera)
SIGUIENDO = 1 # Siguiendo la pared
GIRANDO = 2 # Girando
AVANZANDO = 3 # Avanzando
ESPERANDO = 4 # Esperando a asentarse


def normalizar(a):
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


class ResolverLaberinto(Node):

    def __init__(self):
        super().__init__('resolver_laberinto')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)

        self.frente = float('inf')
        self.derecha = float('inf')
        self.yaw = 0.0
        self.x, self.y = 0.0, 0.0
        self.scan_ok = False
        self.odom_ok = False

        self.estado = BUSCANDO
        self.yaw_objetivo = 0.0
        self.dir_giro = 1.0
        self.estado_post_espera = SIGUIENDO 
        self.tiempo_inicio_espera = 0.0

        self.create_timer(0.05, self.loop)
        self.get_logger().info('Iniciando')

    def scan_cb(self, msg):
        n = len(msg.ranges)
        # Devuelve el minimo escaneo del lidar en el rango
        def minimo(centro, ap):
            vals = [msg.ranges[(centro+d)%n]
                    for d in range(-ap, ap+1)
                    if msg.range_min < msg.ranges[(centro+d)%n] < msg.range_max]
            return min(vals) if vals else float('inf')
        self.frente  = minimo(0,   10) 
        self.derecha = minimo(270, 20)
        self.scan_ok = True

    def odom_cb(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.yaw = math.atan2(2.0*(q.w*q.z + q.x*q.y), 1.0-2.0*(q.y*q.y + q.z*q.z))
        self.odom_ok = True

    def cmd(self, lin, ang):
        msg = Twist()
        msg.linear.x  = lin
        msg.angular.z = ang
        self.pub.publish(msg)

    def parar(self):
        self.pub.publish(Twist())

    def iniciar_giro(self, angulo, proximo_estado):
        # Gira en la dirección establecida mediante odometría
        yaw_base = round(self.yaw / (math.pi / 2.0)) * (math.pi / 2.0)
        self.yaw_objetivo = normalizar(yaw_base + angulo)
        self.dir_giro = 1.0 if angulo > 0 else -1.0
        
        self.estado_post_espera = proximo_estado
        self.estado = GIRANDO
        self.get_logger().info(f'GIRANDO hacia {math.degrees(self.yaw_objetivo):.0f}°')

    def loop(self):
        if not self.scan_ok or not self.odom_ok: return

        # Espera para evitar inercia tras girar
        if self.estado == ESPERANDO:
            tiempo_actual = self.get_clock().now().nanoseconds / 1e9
            if tiempo_actual - self.tiempo_inicio_espera >= PAUSA_ASENTAMIENTO:
                if self.estado_post_espera == AVANZANDO:
                    self.start_x, self.start_y = self.x, self.y
                self.estado = self.estado_post_espera
            else:
                self.parar() 
            return
        
        # Gira de forma proporcional al error del ángulo al que apunta
        if self.estado == GIRANDO:
            error = normalizar(self.yaw_objetivo - self.yaw)
            if abs(error) < TOLERANCIA:
                self.parar()
                self.estado = ESPERANDO
                self.tiempo_inicio_espera = self.get_clock().now().nanoseconds / 1e9
            else:
                w = KP_GIRO * error
                w = math.copysign(max(W_MIN, min(W_MAX, abs(w))), w)
                if abs(error) < ZONA_FRENADO: w = self.dir_giro * W_MIN
                self.cmd(0.0, w)
            return
        
        # Avanza recto para encontrar la pared
        if self.estado == AVANZANDO:
            dist = math.hypot(self.x - self.start_x, self.y - self.start_y)
            if dist >= DIST_AVANCE_PASILLO or self.frente < DIST_FRENTE_PARAR:
                self.parar()
                self.estado = SIGUIENDO
            else:
                self.cmd(VEL_LINEAL, 0.0)
            return
        
        # Encuentra la primera pared y se pone paralelo a ella
        if self.estado == BUSCANDO:
            if self.frente < DIST_FRENTE_PARAR:
                self.parar()
                self.iniciar_giro(math.pi / 2, SIGUIENDO)
            else:
                self.cmd(VEL_LINEAL, 0.0)
            return

        # Seguieminto de la pared
        if self.estado == SIGUIENDO:
            yaw_ideal = round(self.yaw / (math.pi / 2.0)) * (math.pi / 2.0)
            error_yaw = normalizar(yaw_ideal - self.yaw)
            es_paralelo = abs(error_yaw) < 0.15 
            
            dist_ortogonal = self.derecha * math.cos(error_yaw)
            
            # Frente bloqueado
            if self.frente < DIST_FRENTE_PARAR:
                self.parar()
                self.get_logger().info('Frente bloqueado. Giro a la izquierda')
                self.iniciar_giro(math.pi / 2, SIGUIENDO)
                
            # Manejo de camino nuevo a la derecha
            elif self.derecha > DIST_DETECTAR_PARED:
                if es_paralelo:
                    self.parar()
                    self.get_logger().info('CAMINO A LA DERECHA CONFIRMADO. VOY PARA ALLA')
                    self.iniciar_giro(-math.pi / 2, AVANZANDO)
                else:
                    # Nos detenemos para enderezarnos. Si el hueco era falso, desaparecerá al estar rectos.
                    self.get_logger().info('Posible camino derecha, pausando avance para enderezar y confirmar...')
                    correccion = KP_ALINEACION * error_yaw
                    correccion = math.copysign(max(W_MIN, min(W_MAX, abs(correccion))), correccion)
                    self.cmd(0.0, correccion) # VELOCIDAD LINEAL 0 ABSOLUTA. NO NOS MOVEMOS MIENTRAS GIRAMOS
                
            # Correcciones del seguimiento
            elif dist_ortogonal < DIST_EMERGENCIA:
                self.cmd(VEL_LINEAL_LENTO, VEL_ANGULAR_SUAVE)
                
            elif dist_ortogonal < DIST_WARNING:
                self.cmd(VEL_LINEAL_LENTO, VEL_ANGULAR_SUAVE / 2.0)
                
            elif dist_ortogonal > DIST_LEJOS:
                self.cmd(VEL_LINEAL, -VEL_ANGULAR_SUAVE)
                
            # Zona segura
            else:
                
                # Manejo de paralelismo con respecto a la pared de la derecha (es muy importante porque si gira las medidas del lidar pueden tomar falsas entradas)
                if not es_paralelo:
                    correccion = KP_ALINEACION * error_yaw
                    correccion = math.copysign(max(W_MIN, min(W_MAX, abs(correccion))), correccion)
                    self.cmd(0.0, correccion) 
                else:
                    self.cmd(VEL_LINEAL, 0.0)


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