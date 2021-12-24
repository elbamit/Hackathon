import socket
import time
from datetime import datetime
#from scapy.arch import get_if_addr
from random import random
from threading import Thread


class Server:
    link_proto = 'eth1'
    def __init__(self, tcp_port):
        self.udp_port = 13117
        self.tcp_port = tcp_port

        #Message format
        self.magicCookie = 0xabcddcba
        self.message_type = 0x2

        #Create a new UDP server socket
        #family - IVP4 addresses, type - UDP protocol
        self.broad_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broad_socket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        self.ip = socket.gethostbyname(socket.gethostname())

        self.broad_msg = self.magicCookie.to_bytes(byteorder='big', length=4) + self.message_type.to_bytes(byteorder='big', length=1) + self.tcp_port.to_bytes(byteorder='big', length=2)

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(("", self.tcp_port))

        self.all_clients_connected = False
        self.player1_conn = None
        self.player2_conn = None
        self.player1_name = None
        self.player2_name = None
        print(self.ip)



    def waiting_for_clients(self):
        self.tcp_socket.listen(2)


        while not self.all_clients_connected:
            player_conn, player_addr = self.tcp_socket.accept()
            player_name = player_conn.recv(1024)

            if self.player1_conn is None:
                self.player1_conn = player_conn
                self.player1_name = player_name.decode('UTF-8')
                print("player 1 connected")
                continue

            elif self.player2_conn is None:
                self.player2_conn = player_conn
                self.player2_name = player_name.decode('UTF-8')
                self.all_clients_connected = True
                print("player 2 connected")


    def broadcast(self):
        print("Server started, listening on IP address " + self.ip)
        while not self.all_clients_connected:
            #TODO change IP to SUBNET + 255.255
            #Broadcast itself
            self.broad_socket.sendto(self.broad_msg, ('255.255.255.255', self.udp_port))

            #Free's CPU for 1 second
            time.sleep(1)


    def start_server(self):
    # if __name__ == "__main__":
    #     server = Server(18121)
        t1 = Thread(target=self.broadcast, daemon=True)
        t2 = Thread(target=self.waiting_for_clients, daemon=True)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # after 2 clients connected to server, we start 10 sec countdown
        time.sleep(4) #TODO: change back to 10 sec
        self.game_mode()
        print(self.player1_name)
        print(self.player2_name)

    def game_mode(self):

        number1 = random.randint(0, 9)
        number2 = 9 - number1
        #send welcome to game
        welcome_msg = "Welcome to Quick Maths.\n" \
                      "Player 1: " + self.player1_name + "\n" \
                      "Player 2: Rocket " + self.player2_name + "\n " \
                      "==" \
                      "Please answer the following question as fast as you can:" \
                      "How much is " + str(number1) + "+" + str(number2) + "?"
        self.player1_conn.send(bytes(welcome_msg, 'UTF-8'))
        self.player2_conn.send(bytes(welcome_msg, 'UTF-8'))




