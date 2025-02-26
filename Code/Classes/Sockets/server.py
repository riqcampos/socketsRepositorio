import socket

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.clients = []

    def accept_client(self):
        client, address = self.socket.accept()
        self.clients.append(client)
        print(f"Connection from {address} has been established! --> 200")

    def send_to_all(self, message):
        for client in self.clients:
            client.send(message.encode("utf-8"))

    def receive_from_all(self):
        for client in self.clients:
            message = client.recv(1024).decode("utf-8")
            print(f"Received message: {message}")

    def close(self):
        self.socket.close()