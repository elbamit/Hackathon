import socket
import time
from datetime import datetime
#from scapy.arch import get_if_addr
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



if __name__ == "__main__":
    server = Server(18121)
    t1 = Thread(target=server.broadcast, daemon=True)
    t2 = Thread(target=server.waiting_for_clients, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print(server.player1_name)
    print(server.player2_name)




