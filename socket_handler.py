#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import socket
import threading

from utils import fromBase, toBase

class SocketHandler:
    """Class handling communication between the two devices"""
    
    PORT = 46953
    
    def __init__(self, manager):
        """Initializes a SocketHandler instance

        Args:
            manager (Manager): manager instance
        """
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip = s.getsockname()[0]
        s.close()
        
        self.manager = manager
        self.socket = None
        self.running = True
    
    def get_code(self):
        """Returns the encoded ip address

        Returns:
            str: connection code
        """

        ip = list(map(int, self.ip.split(".")))
        code = self.ip2str(ip)
        return code
        
    def ip2str(self, ip):
        """Converts the ip address to a base36 code

        Args:
            ip (list[int, int, int, int]): ip address

        Returns:
            str: encoded address
        """
        
        n = ip[0]<<24 | ip[1]<<16 | ip[2]<<8 | ip[3]
        return toBase(n, 36)
    
    def str2ip(self, s):
        """Converts a base36 code to an ip address

        Args:
            s (str): encoded address

        Returns:
            list[int, int, int, int]: ip address
        """
        
        n = fromBase(s, 36)
        return [n>>24, (n>>16) & 0xff, (n>>8) & 0xff, n&0xff]

    def host(self):
        """Initializes this instance as the host (listen for connections)"""
        
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
        """Initializes this instance as the guest (connect to host)"""
        
        ip = self.str2ip(code)
        ip = ".".join(map(str, ip))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect((ip, self.PORT))
        print("Connected to other device")
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()
    
    def send(self, msg):
        """Sends data to the other device

        Args:
            msg (bytes): data to send
        """
        self.socket.send(msg)
    
    def loop(self):
        """Listening loop calls Manager.on_receive asynchornously"""
        
        while self.running:
            data = self.socket.recv(2048)
            if not data:
                break
            self.manager.on_receive(data)
    
    def quit(self):
        """Closes the socket and stops the listening thread"""
        
        self.running = False
        self.socket.close()