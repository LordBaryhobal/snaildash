import pygame
from game import Game
from socket_handler import SocketHandler
import time
import struct
from player import Player
import numpy as np

WIDTH, HEIGHT = 600, 600

class Stage:
    STOP = -1
    MAIN_MENU = 0
    WAITING_OPPONENT = 1
    COUNTDOWN = 2
    IN_GAME = 3
    GAME_TO_BREAKDOWN = 4
    BREAKDOWN_BAR = 5
    BREAKDOWN_BONUSES = 6

class Manager:
    COUNTDOWN = 4
    BREAKDOWN_IN_DUR = 2
    BREAKDOWN_BAR_DUR = 4
    BREAKDOWN_BAR_PAUSE = 0.5
    BREAKDOWN_BAR_END_DUR = 0.2
    BREAKDOWN_INTERVAL = 1

    def __init__(self):
        self.stage = Stage.MAIN_MENU
        self.logo = pygame.image.load("snaildash.png")
        self.font = pygame.font.SysFont("arial", 30)
        self.cd_font = pygame.font.SysFont("arial", 50, bold=True, italic=True)
        self.pct_font = pygame.font.SysFont("arial", 20)
        self.sh = SocketHandler(self.on_receive)
        self.game = Game(self)
        self.play_btn_rect = [0,0,0,0]
        self.play_btn_pressed = False
        self.is_host = False
        self.countdown_start = 0
        self.breakdown_start = 0
        self.bonus_scores = []
        self.home_btn_rect = None
        self.home_btn_pressed = False
        
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
        
        elif self.stage == Stage.GAME_TO_BREAKDOWN:
            self.render_breakdown_transition(surf)
        
        elif self.stage == Stage.BREAKDOWN_BAR:
            self.render_breakdown_bar(surf)
        
        elif self.stage == Stage.BREAKDOWN_BONUSES:
            self.render_breakdown_bonuses(surf)

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
                x, y = event.pos
                if self.stage == Stage.MAIN_MENU:
                    if event.button == 1:
                        r = self.play_btn_rect
                        if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                            self.play_btn_pressed = True
                
                elif self.stage == Stage.BREAKDOWN_BONUSES:
                    if event.button == 1:
                        r = self.home_btn_rect
                        if r:
                            if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                                self.home_btn_pressed = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                if self.stage == Stage.MAIN_MENU:
                    if event.button == 1:
                        r = self.play_btn_rect
                        if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                            if self.play_btn_pressed:
                                self.play_btn_pressed = False
                                self.sh.send(b"ready")
                                self.stage = Stage.WAITING_OPPONENT
                
                elif self.stage == Stage.BREAKDOWN_BONUSES:
                    if event.button == 1:
                        r = self.home_btn_rect
                        if r:
                            if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]:
                                if self.home_btn_pressed:
                                    self.home_btn_pressed = False
                                    self.stage = Stage.MAIN_MENU
            
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
            rem = self.game.start_time+self.game.DURATION-time.time()
            if rem <= 0:
                self.stage = Stage.GAME_TO_BREAKDOWN
                self.breakdown_start = time.time()
                p1, p2 = self.game.players
                ts = self.game.ts
                ox, oy = win.get_width()/2 - self.game.WIDTH/2*ts, win.get_height()/2 - self.game.HEIGHT/2*ts
                
                self.p1Ps, self.p2Ps = [ox+(p1.x+0.5)*ts, oy+(p1.y+0.5)*ts], [ox+(p2.x+0.5)*ts, oy+(p2.y+0.5)*ts]
                self.p1Pe, self.p2Pe = [ox, oy], [ox+self.game.WIDTH*ts, oy]
        
        elif self.stage == Stage.GAME_TO_BREAKDOWN:
            rem = self.breakdown_start+self.BREAKDOWN_IN_DUR-time.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BAR
                self.breakdown_start = time.time()
        
        elif self.stage == Stage.BREAKDOWN_BAR:
            rem = self.breakdown_start+self.BREAKDOWN_BAR_DUR-time.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BONUSES
                self.breakdown_start = time.time()
                self.bonus_scores = [
                    ("Test 1", 13, 42),
                    ("Test 2", 83, 23),
                    ("Essai 3", 4085, 384)
                ]

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
    
    def render_breakdown_transition(self, surf):
        self.game.render(surf, False)
        fade = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        t = time.time()
        r = self.breakdown_start+self.BREAKDOWN_IN_DUR-t
        r = 1-r/self.BREAKDOWN_IN_DUR
        r = max(0, min(1, r))
        fade.fill((0,0,0,int(r*255)))
        surf.blit(fade, [0,0])
        p1P = [(self.p1Pe[0]-self.p1Ps[0])*r+self.p1Ps[0], (self.p1Pe[1]-self.p1Ps[1])*r+self.p1Ps[1]]
        p2P = [(self.p2Pe[0]-self.p2Ps[0])*r+self.p2Ps[0], (self.p2Pe[1]-self.p2Ps[1])*r+self.p2Ps[1]]
        R = self.game.ts * (r+1)/2
        pygame.draw.circle(surf, Player.COLORS[0], p1P, R)
        pygame.draw.circle(surf, Player.COLORS[1], p2P, R)
    
    def render_breakdown_bar(self, surf):
        surf.fill(0)
        
        t = time.time()
        
        r_bar = self.breakdown_start+self.BREAKDOWN_BAR_DUR-self.BREAKDOWN_BAR_PAUSE-self.BREAKDOWN_BAR_END_DUR-t
        r_end = self.breakdown_start+self.BREAKDOWN_BAR_DUR-t
        r_bar = 1-r_bar/(self.BREAKDOWN_BAR_DUR-self.BREAKDOWN_BAR_PAUSE-self.BREAKDOWN_BAR_END_DUR)
        r_end = 1-r_end/self.BREAKDOWN_BAR_END_DUR
        r_bar = max(0, min(1, r_bar))
        
        red = np.count_nonzero(self.game.trails == 0)
        blue = np.count_nonzero(self.game.trails == 1)
        full = self.game.WIDTH * self.game.HEIGHT
        pct_red = red/full*100
        pct_blue = blue/full*100
        
        p1, p2 = self.p1Pe, self.p2Pe
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        width = p2[0]-p1[0]-2*self.game.ts-40
        bar_h = self.game.ts
        ox, oy = mx-width/2, my-bar_h/2
        
        pct_red, pct_blue = r_bar*pct_red, r_bar*pct_blue
        r_red, r_blue = r_bar*red/full, r_bar*blue/full
        pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width*r_red, bar_h])
        pygame.draw.rect(surf, Player.COLORS[1], [ox+width-width*r_blue, oy, width*r_blue, bar_h])
        
        pygame.draw.circle(surf, Player.COLORS[0], p1, self.game.ts)
        pygame.draw.circle(surf, Player.COLORS[1], p2, self.game.ts)
        
        pct_red = self.pct_font.render(f"{pct_red:.1f}%", True, (255,255,255))
        pct_blue = self.pct_font.render(f"{pct_blue:.1f}%", True, (255,255,255))
        
        surf.blit(pct_red, [p1[0]-pct_red.get_width()/2, p1[1]-pct_red.get_height()/2])
        surf.blit(pct_blue, [p2[0]-pct_blue.get_width()/2, p2[1]-pct_blue.get_height()/2])
        
        if r_end >= 0:
            r_end = min(1, r_end)**2
            
            if red > blue:
                w = width*red/full
                w = (width-w)*r_end + w
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-width*blue/full, oy, width*blue/full, bar_h])
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, w, bar_h])
            
            elif blue > red:
                w = width*blue/full
                w = (width-w)*r_end + w
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width*red/full, bar_h])
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-w, oy, w, bar_h])
            
            else:
                w_red = width*red/full
                w_red = (width/2-w_red)*r_end + w_red
                w_blue = width*blue/full
                w_blue = (width/2-w_blue)*r_end + w_blue
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, w_red, bar_h])
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-w_blue, oy, w_blue, bar_h])
    
    def render_breakdown_bonuses(self, surf):
        surf.fill(0)
        
        # Bar
        red = np.count_nonzero(self.game.trails == 0)
        blue = np.count_nonzero(self.game.trails == 1)
        full = self.game.WIDTH * self.game.HEIGHT
        pct_red = red/full*100
        pct_blue = blue/full*100
        
        p1, p2 = self.p1Pe, self.p2Pe
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        width = p2[0]-p1[0]-2*self.game.ts-40
        bar_h = self.game.ts
        ox, oy = mx-width/2, my-bar_h/2
        
        pygame.draw.circle(surf, Player.COLORS[0], p1, self.game.ts)
        pygame.draw.circle(surf, Player.COLORS[1], p2, self.game.ts)
        
        pct_red = self.pct_font.render(f"{pct_red:.1f}%", True, (255,255,255))
        pct_blue = self.pct_font.render(f"{pct_blue:.1f}%", True, (255,255,255))
        
        surf.blit(pct_red, [p1[0]-pct_red.get_width()/2, p1[1]-pct_red.get_height()/2])
        surf.blit(pct_blue, [p2[0]-pct_blue.get_width()/2, p2[1]-pct_blue.get_height()/2])
            
        if red > blue:
            pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width, bar_h])
        
        elif blue > red:
            pygame.draw.rect(surf, Player.COLORS[1], [ox, oy, width, bar_h])
        
        else:
            pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width/2, bar_h])
            pygame.draw.rect(surf, Player.COLORS[1], [ox+width/2, oy, width/2, bar_h])
        
        # Bonus scores
        cur = time.time()
        step = int( (cur-self.breakdown_start)//self.BREAKDOWN_INTERVAL )
        x1, x2 = self.p1Pe[0], self.p2Pe[0]
        xm = (x1+x2)/2
        
        ys = self.p1Pe[1]+100
        ye = surf.get_height()-150
        h = (ye-ys)/len(self.bonus_scores)
        
        for i in range(min(step, len(self.bonus_scores))):
            name, red, blue = self.bonus_scores[i]
            y = ys + i*h + h/2
            txtName = self.font.render(name, True, (255,255,255))
            txtRed = self.font.render(str(red), True, (255,255,255))
            txtBlue = self.font.render(str(blue), True, (255,255,255))
            surf.blit(txtRed, [x1-txtRed.get_width()/2, y-txtRed.get_height()/2])
            surf.blit(txtBlue, [x2-txtBlue.get_width()/2, y-txtBlue.get_height()/2])
            surf.blit(txtName, [xm-txtName.get_width()/2, y-txtName.get_height()/2])
        
        if step > len(self.bonus_scores):
            txt = self.font.render("Menu principal", True, (0,0,0))
            w, h = txt.get_size()
            tx, ty = surf.get_width()/2-w/2, surf.get_height()-75-h/2
            self.home_btn_rect = [tx-100, ty-10, w+200, h+20]
            pygame.draw.rect(surf, (133, 255, 255), self.home_btn_rect)
            surf.blit(txt, [surf.get_width()/2-txt.get_width()/2, surf.get_height()-75-txt.get_height()/2])
    
    def play(self, send=False):
        print(f"play, send={send}")
        if send:
            self.sh.send(b"start")
        
        self.game.reset()
        
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
                    x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails_count = struct.unpack(">BBBBBBBBBBB", data[11:22])
                    data = data[22:]
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
                    x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2 = struct.unpack(">BBBBBBBBBB", data[7:])
                    #_, x1, y1, d1, s1, x2, y2, d2, s2 = data.split(",")
                    trails = None
                    col_start, col_x, col_y = 0, 0, 0
                
                #x1, y1, d1, s1, x2, y2, d2, s2, col_x, col_y = map(int, [x1, y1, d1, s1, x2, y2, d2, s2, col_x, col_y])
                
                self.game.sync(x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails, col_start, col_x, col_y)
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
        pygame.display.set_caption(f"Snaildash - {clock.get_fps():.2f}fps")
        events = pygame.event.get()
        manager.handle_events(events)
        manager.render(win)
        pygame.display.flip()
        clock.tick(30)