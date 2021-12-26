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
                self.player1_conn.setblocking(False)
                self.player1_name = player_name.decode('UTF-8')
                print("player 1 connected")
                continue

            elif self.player2_conn is None:
                self.player2_conn = player_conn
                self.player2_conn.setblocking(False)
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
    # if __name__ == "__main__":
    #     server = Server(18121)
        t1 = Thread(target=self.broadcast, daemon=True)
        t2 = Thread(target=self.waiting_for_clients, daemon=True)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # after 2 clients connected to server, we start 10 sec countdown
        time.sleep(2) #TODO: change back to 10 sec
        self.game_mode()
        print(self.player1_name)
        print(self.player2_name)

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

        t1 = Thread(target=self.get_answer, args=[self.player1_conn, stop_event, queue], daemon=True)
        t2 = Thread(target=self.get_answer, args=[self.player2_conn, stop_event, queue], daemon=True)

        t1.start()
        t2.start()

        while not stop_event.is_set():
            time.sleep(0.1)


        print("Game over!\n"
              "The correct answer was " + str(number1+number2) + "!\n")
        if queue.empty():
            print("Game end with draw, No one entered an answer")
            return

        first_ans, player_conn = queue.get()
        first_ans = first_ans.decode('UTF-8')

        if player_conn == self.player1_conn:
            if first_ans == str(number1 + number2):
                print("Congratulations to the winner: " + self.player1_name)
            else:
                print("Congratulations to the winner: " + self.player2_name)
        else:
            if first_ans == str(number1 + number2):
                print("Congratulations to the winner: " + self.player2_name)
            else:
                print("Congratulations to the winner: " + self.player1_name)




if __name__ == "__main__":
    server = Server(18121)
    server.start_server()




