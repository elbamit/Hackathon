import socket
import time
from queue import Queue
from random import randint
from threading import Thread, Event
from struct import pack, unpack



class Server:
    link_proto = 'eth1'

    # Init of an instance of a server
    # Creates a UDP socket on port 13117 for broadcasting
    # Creates a TCP socket on given tcp_port for connecting with clients during the game
    def __init__(self, tcp_port):
        self.udp_port = 13117
        self.tcp_port = tcp_port

        # Message format
        self.magicCookie = 0xabcddcba
        self.message_type = 0x2

        # Create a new UDP server socket
        # family - IVP4 addresses, type - UDP protocol
        self.broad_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.broad_socket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)

        self.local_ip = socket.gethostbyname(socket.gethostname())
        ip_splited = self.local_ip.split('.')
        self.broad_ip = ip_splited[0] + '.' + ip_splited[1] + '.255.255'



        # Creates the message that will broadcast to clients
        self.broad_msg = pack('IbH', self.magicCookie, self.message_type, self.tcp_port)

        # Creates the TCP socket
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(("", self.tcp_port))
        # self.tcp_socket.settimeout(20)
        # TODO: think about the timeout

        self.all_clients_connected = False
        self.player1_conn = None
        self.player2_conn = None
        self.player1_name = None
        self.player2_name = None

    # Function that makes the TCP socket of the server listen for incoming clients until 2 clients are connected
    def waiting_for_clients(self):
        self.tcp_socket.listen(2)

        # Loops until we have 2 connected clients
        while not self.all_clients_connected:

            # Accepts a client connection
            player_conn, player_addr = self.tcp_socket.accept()

            # Receives the player team's name that client send after connecting
            player_name = player_conn.recv(1024)

            # Connects player 1
            if self.player1_conn is None:
                self.player1_conn = player_conn
                # The connection is set to non-blocking - very important for get_answer() function
                self.player1_conn.setblocking(False)
                self.player1_name = player_name.decode('UTF-8')
                continue

            # Connects player 2
            elif self.player2_conn is None:
                self.player2_conn = player_conn
                # The connection is set to non-blocking - very important for get_answer() function
                self.player2_conn.setblocking(False)
                self.player2_name = player_name.decode('UTF-8')
                self.all_clients_connected = True

    # Function that makes the UDP socket of the server broadcast on the subnet and "advertise" his TCP port number
    def broadcast(self):
        print("Server started, listening on IP address " + self.local_ip)

        # Loops until 2 clients are connected
        while not self.all_clients_connected:

            #TODO change IP to SUBNET + 255.255

            # Sends a packet with the broadcast message to all the subnet every second
            self.broad_socket.sendto(self.broad_msg, ('255.255.255.255', self.udp_port))

            # Free's CPU for 1 second - makes a 1 second wait between each sent message
            time.sleep(1)

    # Function that receives the answer of the player who typed his answer first
    # Exits this state if 10 seconds have passed and no answer has been received
    def get_answer(self, player_conn, stop_event, queue):

        # Sample current time and calculates 10 seconds from it
        now = time.time()
        end_game_time = now + 10
        answer = None

        # Loops until a stop event is triggered
        while not stop_event.is_set():
            try:
                # Tries to receive message from the client.
                # We made sure the connection is non-blocking so the function can keep checking if timer has elapsed
                answer = player_conn.recv(1024)

            # If message hasn't been received - an exeption is thrown
            except:
                pass

            # Samples current time again and checks if 10 seconds passed from original time sample
            curr_time = time.time()
            if curr_time >= end_game_time:
                # 10 seconds passed and none of the clients has answered yet - exit the function
                stop_event.set()
                break

            # Received a message from the client - enqueue it and exits the function
            if answer is not None:
                stop_event.set()
                queue.put((answer, player_conn))
                break

    # Function that runs the game - sends a math question to both clients and gets their answers
    # Prepares a summary message and sends it to the clients
    def game_mode(self):
        # Randomly chooses 2 numbers for the math problem
        number1 = randint(0, 9)
        number2 = randint(0, 9-number1)

        # Sends to both clients the welcome message with the math problem
        welcome_msg = "Welcome to Quick Maths.\n" \
                      "Player 1: " + self.player1_name + "\n" \
                      "Player 2: " + self.player2_name + "\n " \
                      "==\n" \
                      "Please answer the following question as fast as you can:\n" \
                      "How much is " + str(number1) + "+" + str(number2) + "?\n"

        welcome_msg = bytes(welcome_msg, 'UTF-8')
        self.player1_conn.send(welcome_msg)
        self.player2_conn.send(welcome_msg)

        queue = Queue()
        stop_event = Event()

        # Starts 2 threads that wait for an answer from one of the clients.
        # A client's answer finishes the game even if the other client hasn't answered
        t1 = Thread(target=self.get_answer, args=[self.player1_conn, stop_event, queue])
        t2 = Thread(target=self.get_answer, args=[self.player2_conn, stop_event, queue])

        t1.start()
        t2.start()

        # Wait for the game to finish by either a client's answer or a draw (10 seconds timer for game)
        while not stop_event.is_set():
            time.sleep(0.1)

        # Prepare the summary message according to the answer (or lack of answer) provided
        summary_msg = "Game over!\nThe correct answer was " + str(number1+number2) + "!\n"

        if queue.empty():
            summary_msg += "Game end with draw. No one entered an answer"
            return summary_msg

        first_ans, player_conn = queue.get()
        first_ans = first_ans.decode('UTF-8')

        if player_conn == self.player1_conn:
            if first_ans == str(number1 + number2):
                summary_msg += "Congratulations to the winner: " + self.player1_name
            else:
                summary_msg += "Congratulations to the winner: " + self.player2_name
        else:
            if first_ans == str(number1 + number2):
                summary_msg += "Congratulations to the winner: " + self.player2_name
            else:
                summary_msg += "Congratulations to the winner: " + self.player1_name

        return summary_msg

    # Function that sets off the end game mode - sends the summary message to both clients and closes the connection
    def end_game(self, summary_msg):
        summary_msg = bytes(summary_msg, 'UTF-8')
        self.player1_conn.send(summary_msg)
        self.player2_conn.send(summary_msg)

        print("Game over, sending out offer requests...")
        self.tcp_socket.close()

    # Function that makes the server broadcast, accept clients, play a game and quit the game neatly
    def start_server(self):

        # One thread broadcasts the message, another thread accepts the clients
        t1 = Thread(target=self.broadcast, daemon=True)
        t2 = Thread(target=self.waiting_for_clients, daemon=True)

        t1.start()
        t2.start()

        # Both threads need to finish before starting the game
        t1.join()
        t2.join()

        # 10 seconds countdown after both clients are connected
        time.sleep(2) #TODO: change back to 10 sec

        # Game mode - Runs the game and returns a summary message with the correct answer and which player won
        summary_msg = self.game_mode()

        # End game mode - Sends the summary message to both clients and closes the tcp connection
        self.end_game(summary_msg)


if __name__ == "__main__":
    while True:
        server = Server(18121)
        server.start_server()




