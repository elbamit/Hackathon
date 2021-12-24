import socket
class Client:
    def __init__(self):
        self.udp_port = 13117
        self.tcp_port = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("",self.udp_port))
        #Message format
        self.magicCookie = 0xabcddcba
        self.message_type = 0x2


    def find_server(self):
        print("shahar")
        i = 0
        while i< 1:
            try:
                #Gets broadcast message from a server
                data, address = self.udp_socket.recvfrom(2048)
                rcv_magicCookie = hex(int(data.hex()[:8], 16))
                rcv_message_type = data.hex()[9:10]
                rcv_tcp_port = data.hex()[10:]
                
                #Checks that magic cookie and message type match - extract the tcp port that will be used for connection of client-server
                if rcv_magicCookie == hex(self.magicCookie) and int(rcv_message_type) == self.message_type:
                    self.tcp_port = int(rcv_tcp_port, 16)


                print(self.tcp_port)


               
            except:
                print("except")
            
            i += 1

client = Client()
client.find_server()