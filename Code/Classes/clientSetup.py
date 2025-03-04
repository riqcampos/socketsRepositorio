import socket
import threading
import sys
from datetime import datetime

class Client:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    def receive_data(self, conn):
        while True:
            try:
                data = conn.recv(1024).decode('utf-8').strip()
                if data:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {data}")
            except ConnectionResetError:
                break

    def send_commands(self, conn):
        while True:
            command = input().strip()
            if command:
                conn.sendall(command.encode('utf-8'))

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            print(f"Conectado ao servidor em {self.host}:{self.port}")

            thread_recv = threading.Thread(target=self.receive_data, args=(client_socket,))
            thread_send = threading.Thread(target=self.send_commands, args=(client_socket,))
            thread_recv.start()
            thread_send.start()

            thread_recv.join()
            thread_send.join()

if __name__ == "__main__":
    client = Client()
    client.start()