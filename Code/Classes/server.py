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
        self.connection_limits = 0
        self.lock = threading.Lock()    # Ensure thread-safe access to shared resources
        self.closing_connections = set()  # Track connections being closed

    def server_command_shell(self, prompt):
        print(prompt, end=' ')
        user_input = input()
        return user_input

    def client_stop(self, conn, addr, notify=True):
        with self.lock:
            # Mark this connection as being closed
            self.closing_connections.add(conn)
            if conn in self.clients:
                self.clients.remove(conn)
        
        # Give receive_commands thread a moment to see the flag and exit
        time.sleep(0.2)
        
        # Now it's safe to close the connection
        conn.close()
        
        # Clean up after closing
        with self.lock:
            if conn in self.closing_connections:
                self.closing_connections.remove(conn)
        
        if notify:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} > Disconnected >> Number of clients: {len(self.clients)}")

    def handle_client_limit(self):
        return len(self.clients) > self.connection_limits

    def handle_client(self, conn, addr):
        if self.handle_client_limit():
            print("Client Connection Refused: Connection limit reached.")
            conn.sendall("Server > Connection Refused (ERROR: 508). Server limits reached, try again later.\n".encode('utf-8'))
            self.client_stop(conn, addr, notify=False)
        else:
            with self.lock:
                self.clients.append(conn)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} > Connection Established!")
            print(f">> Number of clients: {len(self.clients)}\n")
            conn.sendall("Server > Connection Established!\n".encode('utf-8'))

            thread_recv = threading.Thread(target=self.receive_commands, args=(conn,))
            thread_send = threading.Thread(target=self.send_data, args=(conn, addr))
            thread_recv.start()
            thread_send.start()

            thread_recv.join()
            thread_send.join()
            self.client_stop(conn, addr, notify=False)

    def receive_commands(self, conn):
        while True:
            try:
                # Check if this connection is being closed
                with self.lock:
                    if conn in self.closing_connections:
                        break
                    
                data = conn.recv(1024).decode('utf-8').strip()
                
                if data:
                    with self.lock:
                        self.commands.append(data)
            except ConnectionResetError:
                break
            except OSError:  # Add explicit handling for Bad file descriptor errors
                break

    def send_data(self, conn, addr):
        current_command = None

        conn.sendall("WELCOME TO THE RESOURCE VISUALIZER SERVER!\n\n".encode('utf-8'))
        conn.sendall("""\n\n.\n-------------LIST OF COMMANDS--------------
|    cpu -> view cpu usage                |
|    memory -> view memory usage          |
|    /exit -> exit from client application|
|    /shutdown -> turn off server         |
-------------------------------------------""".encode('utf-8'))
        conn.sendall("\n\n".encode('utf-8'))
        while True:
            with self.lock:
                if self.commands:
                    current_command = self.commands.pop(0)

            if current_command == 'CPU':
                conn.sendall("Monitoring CPU usage. Type 'X' to stop.\n".encode('utf-8'))

                while True:
                    with self.lock:
                        if self.commands and self.commands[0] != 'CPU':
                            break
                    cpu_usage = psutil.cpu_percent(interval=1)
                    conn.sendall(f"CPU: {cpu_usage}%\n".encode('utf-8'))
                    time.sleep(1.5)    # Sleep for 1.5 seconds

            elif current_command == 'MEMORY':
                conn.sendall("Monitoring memory usage. Type 'X' to stop.\n".encode('utf-8'))

                while True:
                    with self.lock:
                        if self.commands and self.commands[0] != 'MEMORY':
                            break
                    memory_usage = psutil.virtual_memory().percent
                    conn.sendall(f"Memory: {memory_usage}%\n".encode('utf-8'))
                    time.sleep(1.5)   # Sleep for 1.5 seconds

            elif current_command == 'X':
                current_command = None   # Reset the command to stop sending data
                continue

            elif current_command == '/SHUTDOWN':
                conn.sendall("Server > Shutting down...\n".encode('utf-8'))
                print("Server > Shutting down > Client resorce")
                with self.lock:
                    self.running = False
                break

            elif current_command == '/EXIT':
                try:
                    conn.sendall("Server > Connection Closed!\n".encode('utf-8'))
                except ConnectionResetError:
                    pass
                self.client_stop(conn, addr)
                break
                
            current_command = None

    def stop(self):
        self.running = False
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        if hasattr(self, 'server_socket') and self.server_socket:
            self.server_socket.close()
        print("Server stopped")

    def start(self):
        self.running = True     # Flag to indicate if the server is running
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server Initialized on {self.host}:{self.port}")

        try:
            self.connection_limits = int(self.server_command_shell("Enter the client limit: ")) # Stablish client connection limits
            print(f"Connection limits was set for {self.connection_limits} simultaneously clients.")
            while self.running: 
                try:
                    self.server_socket.settimeout(1.0)      # Allow checking self.running every second
                    conn, addr = self.server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    client_thread.daemon = True     # Set as daemon so it exits when main thread exits
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error: {e}")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()