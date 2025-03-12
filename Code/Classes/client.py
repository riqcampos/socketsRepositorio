import socket
import threading
import sys
from datetime import datetime

class Client:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.running = True
        self.client_socket = None

    def receive_data(self, conn):
        while self.running:
            try:
                data = conn.recv(1024).decode('utf-8').strip()

                # if not data:
                #     print("Connection closed by server.")
                #     self.running = False    
                #     break
                
                # Could be better defined to display messages more gracefully...
                if data:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {data}")
                    if data == "Server > Connection Refused (ERROR: 508). Server limits reached, try again later." or data == "Server > Shutting down..." or data == "Server > Connection closed.":
                        self.running = False
                        break

            except ConnectionResetError:
                print("Server connection lost.")
                self.running = False
                break
            except socket.error as e:
                # Socket errors that occur during normal shutdown should be silenced
                if self.running:
                    # Only show error if it wasn't caused by deliberate shutdown
                    print(f"Error receiving data: {e}")
                self.running = False
                break
            except Exception as e:
                print(f"Error receiving data: {e}")
                self.running = False
                break

    def send_commands(self, conn):
        # print("Type /exit to quit")
        while self.running:
            try:
                command = input().strip().upper()
                if command and self.running:
                    conn.sendall(command.encode('utf-8'))
                    if command == "/EXIT":
                        self.running = False
                        # Close the socket to unblock the receiving thread
                        if self.client_socket:
                            self.client_socket.close()
                        break
            except Exception as e:
                print(f"Error sending data: {e}")
                self.running = False
                break

    def start(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.client_socket.connect((self.host, self.port))
                print(f"Trying to connect to server at {self.host}:{self.port}...")

                thread_recv = threading.Thread(target=self.receive_data, args=(self.client_socket,))
                thread_send = threading.Thread(target=self.send_commands, args=(self.client_socket,))
                
                thread_recv.daemon = True
                thread_send.daemon = True
                
                thread_recv.start()
                thread_send.start()
                
                # Use a loop to check for running status instead of join()
                while self.running:
                    thread_send.join(0.5)
                    if not thread_send.is_alive():
                        break
                
            except ConnectionRefusedError:
                print(f"Could not connect to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.running = False
            if self.client_socket:
                self.client_socket.close()
            print("Client stopped.")

if __name__ == "__main__":
    client = Client()
    client.start()