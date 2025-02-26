import threading

class threadParalelismSystem:
    def __init__(self, numThreads):
        self.numThreads = numThreads
        self.threads = []
        self.threadLock = threading.Lock