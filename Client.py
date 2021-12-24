import socket
class Client:
    def __init__(self):
        self.udp_port = 13117
        self.tcp_port = None
        self.server_ip = None

        self.team_name = 'AmiTamar_Client'

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("",self.udp_port))

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Message format
        self.magicCookie = 0xabcddcba
        self.message_type = 0x2

        self.found_server = False


    def find_server(self):
        print("shahar")

        while not self.found_server:
            print("Client started, listening for offer requests...")

            #Gets broadcast message from a server
            data, address = self.udp_socket.recvfrom(2048)

            #Extracts data from server's broadcast message
            rcv_magicCookie = hex(int(data.hex()[:8], 16))
            rcv_message_type = data.hex()[9:10]
            rcv_tcp_port = data.hex()[10:]



            #Checks that magic cookie and message type match - extract the tcp port that will be used for connection of client-server
            if rcv_magicCookie == hex(self.magicCookie) and int(rcv_message_type) == self.message_type:
                self.tcp_port = int(rcv_tcp_port, 16)
                self.server_ip = address[0]

            print("Received offer from " + str(address[0]) + ", attempting to connect...")
            self.found_server = True




    def connect_to_server(self):
        self.tcp_socket.connect((self.server_ip, self.tcp_port))

        team_name_msg = bytes(self.team_name, 'UTF-8')
        self.tcp_socket.send(team_name_msg)

if __name__ == "__main__":
    client = Client()
    client.find_server()
    client.connect_to_server()