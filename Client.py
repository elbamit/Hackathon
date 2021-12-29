import socket
import time
from struct import pack, unpack



class Client:

    # Init of an instance of a client
    # Creates a UDP socket and bind it to port 13117 for receiving broadcast message from server
    # Creates a TCP socket
    def __init__(self):
        self.udp_port = 13117
        self.tcp_port = None
        self.server_ip = None

        # Message format
        self.magicCookie = 0xabcddcba
        self.message_type = 0x2

        #TODO: need to verify the client team name
        self.team_name = 'AmiTamar_Client'

        # Create a new UDP server socket
        # family - IVP4 addresses, type - UDP protocol
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("" ,self.udp_port))

        # Creates the TCP socket
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.found_server = False

    # Function that makes the client wait for a message from a server (on UDP) to connect to its TCP socket
    def find_server(self):

        # Loops until a message from a server arrives
        while not self.found_server:
            print("Client started, listening for offer requests...")

            # Gets broadcast message from a server
            data, address = self.udp_socket.recvfrom(2048)
            data = unpack('IbH', data)

            # Extracts data from server's broadcast message
            rcv_magicCookie = data[0]
            rcv_message_type = data[1]
            rcv_tcp_port = data[2]

            # Checks that magic cookie and message type match
            # Extract the tcp port that will be used for connection of client-server
            if rcv_magicCookie == self.magicCookie and rcv_message_type == self.message_type:
                self.tcp_port = rcv_tcp_port
                self.server_ip = address[0]

            print("Received offer from " + str(address[0]) + ", attempting to connect...\n")
            self.found_server = True

    # Function that connects the client's TCP socket to the server's TCP socket
    def connect_to_server(self):

        self.tcp_socket.connect((self.server_ip, self.tcp_port))

        # Sends to the server the client's team name
        team_name_msg = bytes(self.team_name, 'UTF-8')
        self.tcp_socket.send(team_name_msg)

    # Game mode - receives the message with the math question from the server, prints it to user, and send response back
    def game_mode(self):
        # Receives question from server
        opening_msg = self.tcp_socket.recv(1024)
        opening_msg = opening_msg.decode('UTF-8')
        # Prints question to user
        print(opening_msg)


        self.tcp_socket.setblocking(0)
        msg_from_server = None

        # Checks if a key has been pressed (but not read already)
        while not msvcrt.kbhit():
            try:
                # Checks if other client already responded - if so, server sends summary message
                msg_from_server = self.tcp_socket.recv(1024)
            except:
                time.sleep(0.1)

            # summary message received - the other client has responded faster
            if msg_from_server != None:
                break

        # If summary message is not received yet - the other client hasn't responded yet
        # That means self (Me, Myself, I) has pressed a key
        if not msg_from_server:

            # Reads the key that has been pressed
            user_answer = getch()

            #Sends it to the server
            self.tcp_socket.send(user_answer)

            # Waits for the server's message
            while not msg_from_server:
                try:
                    msg_from_server = self.tcp_socket.recv(1024)
                except:
                    time.sleep(0.1)

        # Prints the summary message from the server
        print(msg_from_server.decode('UTF-8'))

    # End game mode - closes the connection
    def end_game(self):
        self.tcp_socket.close()
        print("Server disconnected, listening for offer requests...")

    # Function that makes the client find a server, connect to it, play the game then exit it and closes the connection
    def start_client(self):
        self.find_server()
        self.connect_to_server()
        self.game_mode()
        self.end_game()
                
           
if __name__ == "__main__":
    while True:
        client = Client()
        client.start_client()


