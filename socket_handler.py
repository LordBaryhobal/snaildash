import socket
import threading
from utils import fromBase, toBase

class SocketHandler:
    PORT = 46953
    
    def __init__(self, manager):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]
        s.close()
        
        self.manager = manager
        self.socket = None
        self.running = True
    
    def get_code(self):
        ip = list(map(int, self.ip.split(".")))
        code = self.ip2str(ip)
        return code
        
    def ip2str(self, ip):
        n = ip[0]<<24 | ip[1]<<16 | ip[2]<<8 | ip[3]
        return toBase(n, 36)
    
    def str2ip(self, s):
        n = fromBase(s, 36)
        return [n>>24, (n>>16) & 0xff, (n>>8) & 0xff, n&0xff]

    def host(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.PORT))
        self.socket.listen(0)
        conn, addr = self.socket.accept()
        self.socket.close()
        self.socket = conn
        print("Connected to other device")
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()
    
    def join(self, code):
        ip = self.str2ip(code)
        ip = ".".join(map(str, ip))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((ip, self.PORT))
        print("Connected to other device")
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()
    
    def send(self, msg):
        self.socket.send(msg)
    
    def loop(self):
        while self.running:
            data = self.socket.recv(2048)
            if not data:
                break
            self.manager.on_receive(data)
    
    def quit(self):
        self.running = False
        self.socket.close()