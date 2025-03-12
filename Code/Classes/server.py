import socket
import threading
import psutil
import time
from datetime import datetime

class Server:

    """
    Represents a server that handles multiple clients and command processes.
    
    Attributes:
    host : str
        The host address of the server.
    port : int
        The port number on which the server listens.
    clients : list
        A list to store connected clients.
    commands : list
        A list to store received commands.
    lock : threading.Lock
        A lock to synchronize access to shared resources.
    """

    def __init__(self, host='0.0.0.0', port=5000):

        """
        Constructs all the necessary attributes for the server object.

        Parameters:
        host : str
            The host address of the server (default is '0.0.0.0').
        port : int
            The port number on which the server listens (default is 5000).
        """

        self.host = host
        self.port = port
        self.clients = []
        self.commands = []
        self.connection_limits = 0
        self.lock = threading.Lock()    # Ensure thread-safe access to shared resources
        self.closing_connections = set()  # Track connections being closed
    

    def server_command_shell(self, prompt):

        """
        Process inputs in the command prompt while the program is running.
        This is an abstraction to return the value from input, which is then assigned to variables in init.
        
        Parameters:
        prompt : str
            The prompt to display when requesting input.
            
        Returns:
        str
            The user input that can be assigned to a variable.
        """

        print(prompt, end=' ')
        user_input = input()
        return user_input


    def client_stop(self, conn):
        
        """
        Stops the client connection and removes it from the list of connected clients.

        Parameters:
        conn : socket
            The socket object for the connected client.
        """

        with self.lock:
            # Mark this connection as being closed
            self.closing_connections.add(conn)
            if conn in self.clients:
                self.clients.remove(conn)
        
        # Give receive_commands thread a moment to see the flag and exit
        time.sleep(0.1)
        
        # Now it's safe to close the connection
        conn.close()
        
        # Clean up after closing
        with self.lock:
            if conn in self.closing_connections:
                self.closing_connections.remove(conn)


    def handle_client_limit(self):

        """
        Check if the client limit has been reached.
        """
        
        if len(self.clients) > self.connection_limits:     
            return True
        else:
            return False
    

    def handle_client(self, conn, addr):

        """
        Handles a connected client by starting threads for receiving commands and sending data.

        Parameters:
        conn : socket
            The socket object for the connected client.
        addr : tuple
            The address of the connected client.
        """

        if self.handle_client_limit() == True:
                        print("Client Connection Refused: Connection limit reached.")
                        conn.sendall("Server > Connection Refused (ERROR: 508). Server limits reached, try again later.\n".encode('utf-8'))
                        self.client_stop(conn)
                        # print(self.clients)
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} > Connection Established!")
            print(f">> Number of clients: {len(self.clients)}\n")
            conn.sendall(f" Server > Connection Established!\n".encode('utf-8'))

            thread_recv = threading.Thread(target=self.receive_commands, args=(conn,))
            thread_send = threading.Thread(target=self.send_data, args=(conn, addr))
            thread_recv.start()
            thread_send.start()

            thread_recv.join()
            thread_send.join()
            conn.close()
        

    def receive_commands(self, conn):
        
        """
        Receives commands from the connected client and stores them in the commands list.

        Parameters:
        conn : socket
            The socket object for the connected client.
        """

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

                        ##   Test module for command list status
                        # print(f"command list status: {self.commands}")
                        # print(f"Received command: {self.commands[-1]}")

            except ConnectionResetError:
                break
            except OSError:  # Add explicit handling for Bad file descriptor errors
                break


    def send_data(self, conn, addr):
        
        """
        Sends data to the connected client based on the received commands.

        Parameters:
        conn : socket
            The socket object for the connected client.
        """

        current_command = None

        conn.sendall("WELCOME TO THE RESOURCE VISUALIZER SERVER!\n\n".encode('utf-8'))
        conn.sendall("""\n\n-------------LIST OF COMMANDS--------------
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
                        if self.commands and self.commands[0] != 'memoria':
                            break
                    memory_usage = psutil.virtual_memory().percent
                    conn.sendall(f"Memory: {memory_usage}%\n".encode('utf-8'))
                    time.sleep(1.5)   # Sleep for 1.5 seconds

            elif current_command == 'X':
                current_command = None   # Reset the command to stop sending data
                continue

            elif current_command == '/SHUTDOWN':
                conn.sendall("Server > Shutting down...\n".encode('utf-8'))
                with self.lock:
                    self.running = False
                break

            elif current_command == '/EXIT':
                conn.sendall("Server > Connection Closed!\n".encode('utf-8'))
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Client {addr} > Disconnected >> Number of clients: {len(self.clients)}")                
                self.client_stop(conn)
                print(f">> Number of clients: {len(self.clients)}\n")
                break
                
            current_command = None


    def stop(self):

        """
        Stops the server and closes all client connections.
        """

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

        """
        Starts the server to listen for incoming connections and handle them.
        """

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
                    with self.lock:
                        self.clients.append(conn)
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