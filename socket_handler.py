import socket
from types import FunctionType
from utils import toBase, fromBase
import threading

class SocketHandler:
    PORT = 46953
    
    def __init__(self, on_receive: FunctionType) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]
        s.close()
        
        self.on_receive = on_receive
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
            #print(f"received: {data}")
            self.on_receive(data)