import socket
import time
from queue import Queue
from random import randint
from threading import Thread, Event





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
        # self.tcp_socket.settimeout(20)
        #TODO: think about the timeout

        self.all_clients_connected = False
        self.player1_conn = None
        self.player2_conn = None
        self.player1_name = None
        self.player2_name = None



    def waiting_for_clients(self):
        self.tcp_socket.listen(2)


        while not self.all_clients_connected:

            player_conn, player_addr = self.tcp_socket.accept()
            player_name = player_conn.recv(1024)



            if self.player1_conn is None:
                self.player1_conn = player_conn
                self.player1_conn.setblocking(False)
                self.player1_name = player_name.decode('UTF-8')
                continue

            elif self.player2_conn is None:
                self.player2_conn = player_conn
                self.player2_conn.setblocking(False)
                self.player2_name = player_name.decode('UTF-8')
                self.all_clients_connected = True


    def broadcast(self):
        print("Server started, listening on IP address " + self.ip)
        while not self.all_clients_connected:
            #TODO change IP to SUBNET + 255.255
            #Broadcast itself
            self.broad_socket.sendto(self.broad_msg, ('255.255.255.255', self.udp_port))

            #Free's CPU for 1 second
            time.sleep(1)

    def get_answer(self, player_conn, stop_event, queue):

        now = time.time()
        end_game_time = now + 10
        answer = None
        while not stop_event.is_set():
            try:
                answer = player_conn.recv(1024)
            except:
                pass
            curr_time = time.time() # activate timer
            if curr_time >= end_game_time:
                stop_event.set()
                break

            if answer is not None:
                stop_event.set()
                queue.put((answer, player_conn))
                break



    def start_server(self):
        t1 = Thread(target=self.broadcast, daemon=True)
        t2 = Thread(target=self.waiting_for_clients, daemon=True)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # after 2 clients connected to server, we start 10 sec countdown
        time.sleep(2) #TODO: change back to 10 sec
        summary_msg = self.game_mode()
        self.end_game(summary_msg)


    def game_mode(self):

        number1 = randint(0, 9)
        number2 = randint(0, 9-number1)
        #send welcome to game
        welcome_msg = "Welcome to Quick Maths.\n" \
                      "Player 1: " + self.player1_name + "\n" \
                      "Player 2: " + self.player2_name + "\n " \
                      "==\n" \
                      "Please answer the following question as fast as you can:\n" \
                      "How much is " + str(number1) + "+" + str(number2) + "?\n"
        self.player1_conn.send(bytes(welcome_msg, 'UTF-8'))
        self.player2_conn.send(bytes(welcome_msg, 'UTF-8'))

        queue = Queue()
        stop_event = Event()

        t1 = Thread(target=self.get_answer, args=[self.player1_conn, stop_event, queue])
        t2 = Thread(target=self.get_answer, args=[self.player2_conn, stop_event, queue])

        t1.start()
        t2.start()

        while not stop_event.is_set():
            time.sleep(0.1)

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

    def end_game(self, summary_msg):
        self.player1_conn.send(bytes(summary_msg, 'UTF-8'))
        self.player2_conn.send(bytes(summary_msg, 'UTF-8'))

        print("Game over, sending out offer requests...")
        time.sleep(3)
        self.tcp_socket.close()


if __name__ == "__main__":
    while True:
        server = Server(18121)
        server.start_server()




