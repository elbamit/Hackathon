import socket
from datetime import datetime
#from scapy.arch import get_if_addr

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
        self.ip = socket.gethostbyname(socket.gethostname()) #get_if_addr(Server.link_proto) 
        print(self.ip)
        # self.broad_socket.bind(('', self.udp_port))


    def broadcast(self):
        now = datetime.now()
        print("Server started, listening on IP address " + self.ip)
        while True:
            broad_msg = self.magicCookie.to_bytes(byteorder='big', length=4) + self.message_type.to_bytes(byteorder='big', length=1) + self.tcp_port.to_bytes(byteorder='big', length=2)
            
            #TODO change IP to SUBNET + 255.255
            #Broadcast itself
            self.broad_socket.sendto(broad_msg, ('255.255.255.255', self.udp_port))
            # message, clientAddress = self.broad_socket.recvfrom()


server = Server(18121)
server.broadcast()
        



