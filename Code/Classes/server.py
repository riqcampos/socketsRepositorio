import socket
import threading
import psutil
import time
from datetime import datetime

class Server:

    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = {}
        self.connection_limits = 0
        self.running = True
        self.lock = threading.Lock()
    
    def server_command_shell(self, prompt):
        return input(prompt + ' ')

    def client_stop(self, conn, addr):
        with self.lock:
            if addr in self.clients:
                del self.clients[addr]
        conn.close()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} disconnected. Active clients: {len(self.clients)}")

    def handle_client(self, conn, addr):
        with self.lock:
            if len(self.clients) >= self.connection_limits:
                conn.sendall("Server > Connection Refused. Limit reached.\n".encode('utf-8'))
                conn.close()
                return
            self.clients[addr] = conn
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} connected. Active clients: {len(self.clients)}")
        conn.sendall("WELCOME TO THE RESOURCE VISUALIZER SERVER!\n".encode('utf-8'))
        conn.sendall("\n.\n------------- LIST OF COMMANDS --------------\n".encode('utf-8'))
        conn.sendall("|    CPU -> view CPU usage                  |\n".encode('utf-8'))
        conn.sendall("|    MEMORY -> view memory usage            |\n".encode('utf-8'))
        conn.sendall("|    /EXIT -> exit client session           |\n".encode('utf-8'))
        conn.sendall("|    /SHUTDOWN -> turn off server           |\n".encode('utf-8'))
        conn.sendall("--------------------------------------------\n\n".encode('utf-8'))
        
        while self.running:
            try:
                conn.settimeout(1.0)
                data = conn.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                
                if data.upper() == "CPU":
                    self.send_data(conn, "CPU", lambda: psutil.cpu_percent(interval=1))
                elif data.upper() == "MEMORY":
                    self.send_data(conn, "MEMORY", lambda: psutil.virtual_memory().percent)
                elif data.upper() == "/EXIT":
                    conn.sendall("Server > Connection Closed!\n".encode('utf-8'))
                    break
                elif data.upper() == "/SHUTDOWN":
                    conn.sendall("Server > Shutting down...\n".encode('utf-8'))
                    self.running = False
                    break
                else:
                    conn.sendall("Server > Invalid Command!\n".encode('utf-8'))
            except socket.timeout:
                continue
            except ConnectionResetError:
                break
        
        self.client_stop(conn, addr)
    
    def send_data(self, conn, label, fetch_data):
        conn.sendall(f"Monitoring {label} usage. Type another command or 'X' to stop.\n".encode('utf-8'))
        while True:
            try:
                conn.settimeout(1.5)
                conn.sendall(f"{label}: {fetch_data()}%\n".encode('utf-8'))
                time.sleep(1.5)
                try:
                    data = conn.recv(1024).decode('utf-8').strip()
                    if data.upper() in ["CPU", "MEMORY"]:
                        return self.send_data(conn, data.upper(), lambda: psutil.cpu_percent(interval=1) if data.upper() == "CPU" else psutil.virtual_memory().percent)
                    if data.upper() == 'X':
                        break
                except socket.timeout:
                    continue
            except (socket.timeout, ConnectionResetError, OSError):
                break
        conn.sendall(f"Stopped monitoring {label}.\n".encode('utf-8'))
    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server started on {self.host}:{self.port}")

        self.connection_limits = int(self.server_command_shell("Enter the client limit:"))
        print(f"Connection limit set to {self.connection_limits}")
        
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")
        
        self.server_socket.close()
        print("Server stopped")

if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.running = False
