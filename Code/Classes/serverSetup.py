import socket
import threading
import psutil
import time
from datetime import datetime

class Server:
    def __init__(self, host='0.0.0.0', port=5000): 
        self.host = host
        self.port = port
        self.clients = []
        self.commands = []
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {addr} CONECTADO!!")
        conn.sendall(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: CONECTADO!!\n".encode('utf-8'))

        thread_recv = threading.Thread(target=self.receive_commands, args=(conn,))
        thread_send = threading.Thread(target=self.send_data, args=(conn,))
        thread_recv.start()
        thread_send.start()

        thread_recv.join()
        thread_send.join()
        conn.close()

    def receive_commands(self, conn):
        while True:
            try:
                data = conn.recv(1024).decode('utf-8').strip()
                if data:
                    with self.lock:
                        self.commands.append(data)
            except ConnectionResetError:
                break

    def send_data(self, conn):
        current_command = None
        while True:
            with self.lock:
                if self.commands:
                    current_command = self.commands.pop(0)

            if current_command == 'CPU':
                while True:
                    with self.lock:
                        if self.commands and self.commands[0] != 'CPU':
                            break
                    cpu_usage = psutil.cpu_percent(interval=1)
                    conn.sendall(f"CPU: {cpu_usage}%\n".encode('utf-8'))

            elif current_command == 'memoria':
                while True:
                    with self.lock:
                        if self.commands and self.commands[0] != 'memoria':
                            break
                    memory_usage = psutil.virtual_memory().percent
                    conn.sendall(f"Memória: {memory_usage}%\n".encode('utf-8'))

            elif current_command == 'stop':
                current_command = None   # Reset the command to stop sending data
                continue

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Servidor iniciado em {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()

if __name__ == "__main__":
    server = Server()
    server.start()