import socket

class Test:
    def __init__(self):
        self.socket = None

    def test(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', 1234))