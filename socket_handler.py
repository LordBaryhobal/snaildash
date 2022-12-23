#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import socket
import threading
import time

class SocketHandler:
    """Class handling communication between the two devices"""
    
    SEND_INTERVAL = 0.1  # interval in seconds between send loops
    LAN = 0
    WAN = 1
    
    def __init__(self, manager):
        """Initializes a SocketHandler instance

        Args:
            manager (Manager): manager instance
        """
        
        self.manager = manager
        self.running = False
        self.sock = None
        self.in_thread = None
        self.out_thread = None
        self.connect_s = None
        self.type = None
    
    def reset(self):
        """Resets messages state"""
        
        self._msgs = {}
        self._last_recv = -1
        self._latest = -1
        self._msg_id = 0
        self.type = None
    
    def connect(self):
        """Connects to the match-making server and waits for opponent"""
        
        self.reset()
        self.running = True
        
        if self.connect_s is None:
            self.connect_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            config = self.manager.config["connection_server"]
            self.connect_s.connect((config["url"], config["port"]))
            self.connect_s.settimeout(2)

            local_ip, local_port = self.connect_s.getsockname()
            musername = self.manager.musername
            msg = f"{local_ip}|{local_port}|{musername}"
            self.local_addr = (local_ip, local_port)
            self.connect_s.sendall(msg.encode("utf-8"))
            self.connect_thread = threading.Thread(target=self.wait_for_opponent)
            self.connect_thread.start()
        
    
    def wait_for_opponent(self):
        """Waits for opponent asynchronously"""
        
        connected = False
        while self.running:
            try:
                data = self.connect_s.recv(2048)
            
            except socket.timeout:
                continue
            
            else:
                if data == b"ping": continue
                
                is_host, pub_ip, pub_port, priv_ip, priv_port = data.decode("utf-8").split("|")
                is_host, pub_port, priv_port = bool(int(is_host)), int(pub_port), int(priv_port)
                
                if is_host:
                    self.manager.init_host()
                else:
                    self.manager.init_guest()
                
                self.pub_addr = (pub_ip, pub_port)
                self.priv_addr = (priv_ip, priv_port)
                
                self.finalize_connection()
                connected = True
                break
        
        if not connected:
            self.connect_s.sendall(b"cancel")
        
        self.connect_s.close()
        self.connect_s = None
    
    def finalize_connection(self):
        """Establishes the connection with the opponent"""
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(self.local_addr)
        self.sock.settimeout(0.1)

        while self.running:
            self.sock.sendto(b"handshake-priv|0", self.priv_addr)
            self.sock.sendto(b"handshake-pub|0", self.pub_addr)
            try:
                data = self.sock.recv(2048)
            except socket.timeout:
                data = b""
            
            if data == b"handshake-priv|1":
                self.sock.connect(self.priv_addr)
                self.type = self.LAN
                break
            
            elif data == b"handshake-pub|1":
                self.sock.connect(self.pub_addr)
                self.type = self.WAN
                break
                
            elif data == b"handshake-priv|0":
                self.sock.sendto(b"handshake-priv|1", self.priv_addr)
                
            elif data == b"handshake-pub|0":
                self.sock.sendto(b"handshake-pub|1", self.pub_addr)
        
        if self.running:
            m = f"handshake-{['priv', 'pub'][self.type]}|1"
            self._msgs[-1] = [m, False]
        
        self.sock.settimeout(1)
        self.in_thread = threading.Thread(target=self.listen_loop)
        self.out_thread = threading.Thread(target=self.send_loop)
        
        self.in_thread.start()
        self.out_thread.start()
        
        self.manager.on_connected()

    def sock_send(self, msg):
        """Sends a message through the socket. If the socket is closed,
        the message will silently be ignored

        Args:
            msg (str or bytes): the message to send
        """
        
        if not self.running or self.sock is None: return
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        self.sock.sendall(msg)

    def listen_loop(self):
        """Listens for incoming messages asynchronously and responds accordingly.
        This method implements TCP features over UDP
        """
        
        while self.running:
            try:
                data = self.sock.recv(2048)
            except:
                continue
            
            if data == "": continue
            if data.startswith(b"handshake"): continue
            
            data = data.split(b"|", 2)
            type_, id_ = data[:2]
            id_ = int(id_.decode("utf-8"))
            
            # Message
            if type_ == b"msg":
                if id_ > self._last_recv+1:
                    self._latest = max(self._latest, id_)
                    self.sock_send(f"res|{self._last_recv+1}")
                
                elif id_ <= self._last_recv:
                    self.sock_send(f"ack|{id_}")
                    
                else:
                    self.manager.on_receive(data[2])
                    if id_ < self._latest:
                        self.sock_send(f"res|{id_+1}")
                    
                    else:
                        self._latest = id_
                    
                    self._last_recv = id_
            
            # Acknowledge
            elif type_ == b"ack":
                self._msgs[id_][1] = True
            
            # Resend
            elif type_ == b"res":
                self.sock_send(self._msgs[id_][0])
            

    def send_loop(self):
        """Sends un-acknowledged messages asynchronously every SEND_INTERVAL seconds"""
        
        while self.running:
            msgs = self._msgs.copy()
            for id_, [msg, ack] in msgs.items():
                if not ack:
                    self.sock_send(msg)
            
            time.sleep(self.SEND_INTERVAL)

    def send(self, msg):
        """Adds a msg to the send queue

        Args:
            msg (bytes): data to send
        """
        
        if self.running and self.sock:
            m = f"msg|{self._msg_id}|"
            m = m.encode("utf-8")+msg
            self.sock.send(m)
            self._msgs[self._msg_id] = [m, False]
            self._msg_id += 1
    
    def quit(self):
        """Closes the socket and stops the listening thread"""
        
        if self.running:
            self.running = False
            if self.sock:
                self.sock.close()
                self.sock = None