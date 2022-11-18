import pygame
from game import Game
from socket_handler import SocketHandler
import time
from math import floor
import struct

WIDTH, HEIGHT = 600, 600

class Stage:
    STOP = -1
    MAIN_MENU = 0
    WAITING_OPPONENT = 1
    COUNTDOWN = 2
    IN_GAME = 3
    BREAKDOWN = 4

class Manager:
    COUNTDOWN = 4

    def __init__(self):
        self.stage = Stage.MAIN_MENU
        self.logo = pygame.image.load("snaildash.png")
        self.font = pygame.font.SysFont("arial", 30)
        self.cd_font = pygame.font.SysFont("arial", 50, bold=True, italic=True)
        self.sh = SocketHandler(self.on_receive)
        self.game = Game(self)
        self.play_btn_rect = [0,0,0,0]
        self.play_btn_pressed = False
        self.is_host = False
        self.countdown_start = 0
        
        print(f"The code for this machine is: {self.sh.get_code()}")
        code = input("Code of the other machine (leave empty to host): ")
        if len(code) == 0:
            self.host()
        
        else:
            self.join(code)
    
    def host(self):
        self.is_host = True
        self.game.player = self.game.players[0]
        self.sh.host()
    
    def join(self, code):
        self.game.player = self.game.players[1]
        self.sh.join(code)
    
    def quit(self, send=False):
        if send:
            self.sh.send(b"quit")
        self.sh.running = False
        self.sh.socket.close()
        self.stage = Stage.STOP
    
    def render(self, surf):
        if self.stage == Stage.MAIN_MENU:
            self.render_menu(surf)
        
        elif self.stage == Stage.WAITING_OPPONENT:
            self.render_waiting(surf)
        
        elif self.stage == Stage.COUNTDOWN:
            r = max(0, self.countdown_start+self.COUNTDOWN - time.time())
            rem = round(r)
            self.game.render(surf)
            rem = "Go" if rem == 0 else str(rem)
            txt = self.cd_font.render(rem, True, (133, 255, 255))
            y0 = surf.get_height()/2-txt.get_height()/2
            y1 = -txt.get_height()
            r = 1 - (r - round(r))
            r = max(0, 2.5*(r-0.6))
            #r = max(0, 5*r-4)
            r = r**2
            y = r*(y1-y0)+y0

            surf.blit(txt, [surf.get_width()/2-txt.get_width()/2, y])
        
        elif self.stage == Stage.IN_GAME:
            self.game.render(surf)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.quit(True)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0 and event.mod & pygame.KMOD_CTRL:
                    self.quit(True)
                
                if self.stage == Stage.IN_GAME:
                    self.game.handle_key(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.stage == Stage.MAIN_MENU:
                    if event.button == 1:
                        x, y = event.pos
                        r = self.play_btn_rect
                        if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                            self.play_btn_pressed = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.stage == Stage.MAIN_MENU:
                    if event.button == 1:
                        x, y = event.pos
                        r = self.play_btn_rect
                        if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                            if self.play_btn_pressed:
                                self.play_btn_pressed = False
                                self.sh.send(b"ready")
                                self.stage = Stage.WAITING_OPPONENT
            
            elif event.type == pygame.USEREVENT:
                self.game.start_turn()
        
        if self.stage == Stage.COUNTDOWN:
            rem = self.countdown_start+self.COUNTDOWN-time.time()
            if rem <= 0:
                self.stage = Stage.IN_GAME
                self.game.start_time = time.time()
                self.game.start_turn()

        elif self.stage == Stage.IN_GAME:
            self.game.loop()

    def render_menu(self, surf):
        surf.fill(0)
        surf.blit(self.logo, [surf.get_width()/2-self.logo.get_width()/2, 0])
        txt = self.font.render("Jouer", True, (0,0,0))
        w, h = txt.get_size()
        tx, ty = surf.get_width()/2-w/2, surf.get_height()/2-h/2
        self.play_btn_rect = [tx-100, ty-10, w+200, h+20]
        pygame.draw.rect(surf, (133, 255, 255), self.play_btn_rect)
        surf.blit(txt, [surf.get_width()/2-txt.get_width()/2, surf.get_height()/2-txt.get_height()/2])
    
    def render_waiting(self, surf):
        t = time.time()
        dots = int(t)%4
        txt = "En attente de l'adversaire ..."
        size = self.font.size(txt)
        txt = self.font.render(txt[:len(txt)-3+dots], True, (255,255,255))
        surf.fill(0)
        surf.blit(txt, [surf.get_width()/2-size[0]/2, surf.get_height()/2-size[1]/2])
    
    def play(self, send=False):
        print(f"play, send={send}")
        if send:
            self.sh.send(b"start")
        
        """
        self.stage = Stage.IN_GAME
        self.game.start_time = time.time()
        self.game.start_turn()
        """
        self.countdown_start = time.time()
        self.stage = Stage.COUNTDOWN
    
    def on_receive(self, data: bytes):
        #data = data.decode("utf-8")
        if data == b"quit":
            self.quit()
            return

        if self.stage == Stage.WAITING_OPPONENT:
            if data == b"ready":
                self.play(True)
            
            elif data == b"start":
                self.play()
        
        elif self.stage == Stage.IN_GAME:
            if data.startswith(b"turnEnd"):
                if data.startswith(b"turnEndHost"):
                    x1, y1, d1, s1, x2, y2, d2, s2, trails_count = struct.unpack(">BBBBBBBBB", data[11:20])
                    data = data[20:]
                    trails = []
                    for j in range(trails_count):
                        x, y, i = struct.unpack(">BBB", data[3*j:3*j+3])
                        trails.append((x, y, i))
                    
                    data = data[3*trails_count:]
                    col_start, col_x, col_y = struct.unpack(">dBB", data)
                    #_, x1, y1, d1, s1, x2, y2, d2, s2, trails, col_start, col_x, col_y = data.split(",")
                    #trails = trails.split("/")
                    #trails = list(map(lambda t: tuple(map(int, t.split("|"))), trails))
                    #col_start = float(col_start)
                
                else:
                    x1, y1, d1, s1, x2, y2, d2, s2 = struct.unpack(">BBBBBBBB", data[7:])
                    #_, x1, y1, d1, s1, x2, y2, d2, s2 = data.split(",")
                    trails = None
                    col_start, col_x, col_y = 0, 0, 0
                
                #x1, y1, d1, s1, x2, y2, d2, s2, col_x, col_y = map(int, [x1, y1, d1, s1, x2, y2, d2, s2, col_x, col_y])
                
                self.game.sync(x1, y1, d1, s1, x2, y2, d2, s2, trails, col_start, col_x, col_y)
                if self.is_host:
                    self.game.end_turn()
                
                else:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT))
                    #self.game.start_turn()

if __name__ == "__main__":
    pygame.init()
    win = pygame.display.set_mode([WIDTH, HEIGHT], pygame.RESIZABLE)
    pygame.display.set_caption("Snaildash")
    clock = pygame.time.Clock()
    
    manager = Manager()

    while manager.stage != Stage.STOP:
        events = pygame.event.get()
        manager.handle_events(events)
        manager.render(win)
        pygame.display.flip()
        clock.tick(30)