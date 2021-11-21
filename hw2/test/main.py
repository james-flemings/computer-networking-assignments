import time 
import threading

class foo():
    def __init__(self):
        self.queue = {} 
        self.base = 0

    def re(self, n):
        print(n)
        if n in self.queue:
            self.queue[n] = threading.Timer(1.0, self.re, args=[n]).start()
        else:
            self.base += 1

    def send(self, n):
        self.queue[n] = threading.Timer(1.0, self.re, args=[n]).start()
        return

f = foo()
f.send(1)
f.send(2)

