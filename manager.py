import struct
import time

import pygame

from font_manager import FontManager
from game import Game
from socket_handler import SocketHandler
from stage import Stage

class Manager:
    WIDTH, HEIGHT = 1920, 1080
    FPS = 30
    
    COUNTDOWN_DUR = 4  # Duration in seconds of the start countdown
    BREAKDOWN_IN_DUR = 2  # Duration in seconds of the game to breakdown transition
    BREAKDOWN_BAR_DUR = 4  # Duration in seconds of the progress bar animation
    BREAKDOWN_BAR_PAUSE = 0.5  # Duration in seconds before the progress bar end fill
    BREAKDOWN_BAR_END_DUR = 0.2  # Duration in seconds of the bar end fill
    BREAKDOWN_INTERVAL = 1  # Interval in seconds between each bonus score reveal
    
    CD_COLOR = (133, 255, 255)

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snaildash")
        self.clock = pygame.time.Clock()
        self.stage = Stage.MAIN_MENU
        self.socket_handler = SocketHandler(self)
        self.game = Game(self)
        self._is_host = False
        
        self.init()
    
    def is_host(self):
        return self._is_host
    
    def init(self):
        print(f"The code for this machine is: {self.socket_handler.get_code()}")
        code = input("Code of the other machine (leave empty to host): ")
        if len(code) == 0:
            self.host()
        
        else:
            self.join(code)
        
        self.startup_time = time.time()
        self.win = pygame.display.set_mode([self.WIDTH, self.HEIGHT], pygame.FULLSCREEN)
    
    def host(self):
        self._is_host = True
        self.game.init_host()
        self.socket_handler.host()
    
    def join(self, code):
        self.game.init_guest()
        self.socket_handler.join(code)
    
    def quit(self, send=False):
        if send:
            self.socket_handler.send(b"quit")
        self.socket_handler.quit()
        self.stage = Stage.STOP
    
    def mainloop(self):
        while self.stage != Stage.STOP:
            pygame.display.set_caption(f"Snaildash - {self.clock.get_fps():.2f}fps")
            events = pygame.event.get()
            self.handle_events(events)
            self.render(self.win)
            pygame.display.flip()
            self.clock.tick(self.FPS)
    
    def time(self):
        return time.time()-self.time_origin
    
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
                self.on_mouse_down(event)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.on_mouse_up(event)
            
            elif event.type == pygame.USEREVENT:
                self.game.start_turn()
        
        if self.stage == Stage.COUNTDOWN:
            rem = self.countdown_start+self.COUNTDOWN-time.time()
            if rem <= 0:
                self.stage = Stage.IN_GAME
                pygame.mixer.music.play()
                self.game.start_time = self.time()
                self.game.start_turn()

        elif self.stage == Stage.IN_GAME:
            self.game.loop()
            rem = self.game.start_time+self.game.DURATION-self.time()
            if rem <= 0:
                self.stage = Stage.GAME_TO_BREAKDOWN
                self.game_to_breakdown_start = self.time()
                
                """p1, p2 = self.game.players
                ts = self.game.ts
                ox, oy = self.win.get_width()/2 - self.game.WIDTH/2*ts, self.win.get_height()/2 - self.game.HEIGHT/2*ts
                
                self.p1Ps, self.p2Ps = [ox+(p1.x+0.5)*ts, oy+(p1.y+0.5)*ts], [ox+(p2.x+0.5)*ts, oy+(p2.y+0.5)*ts]
                self.p1Pe, self.p2Pe = [ox, oy], [ox+self.game.WIDTH*ts, oy]"""
        
        elif self.stage == Stage.GAME_TO_BREAKDOWN:
            rem = self.game_to_breakdown_start+self.BREAKDOWN_IN_DUR-self.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BAR
                self.breakdown_bar_start = self.time()
        
        elif self.stage == Stage.BREAKDOWN_BAR:
            rem = self.breakdown_bar_start+self.BREAKDOWN_BAR_DUR-self.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BONUSES
                self.finished_breakdown = False
                self.breakdown_start = self.time()
    
    def render(self, surf):
        if self.stage == Stage.MAIN_MENU:
            self.gui.render(surf)
        
        elif self.stage == Stage.WAITING_OPPONENT:
            self.gui.render(surf)
        
        elif self.stage == Stage.COUNTDOWN:
            self.game.render(surf)
            
            r = max(0, self.countdown_start+self.COUNTDOWN - time.time())
            rem_sec = round(r)
            rem_sec = "Go" if rem_sec == 0 else str(rem_sec)
            font = FontManager.get("arial", 50, True, True)
            txt = font.render(rem_sec, True, self.CD_COLOR)
            y0 = surf.get_height()/2-txt.get_height()/2
            y1 = -txt.get_height()
            
            # Animation
            r = 1 - (r - rem_sec)
            r = max(0, 2.5*(r-0.6))
            r = r**2
            y = r*(y1-y0)+y0

            surf.blit(txt, [surf.get_width()/2-txt.get_width()/2, y])
        
        elif self.stage == Stage.IN_GAME:
            self.game.render(surf)
        
        elif self.stage == Stage.GAME_TO_BREAKDOWN:
            self.game.render_breakdown_transition(surf)
        
        elif self.stage == Stage.BREAKDOWN_BAR:
            self.game.render_breakdown_bar(surf)
        
        elif self.stage == Stage.BREAKDOWN_BONUSES:
            self.game.render_breakdown_bonuses(surf)
        
        elif self.stage == Stage.TUTORIAL:
            self.tutorial.render(surf)
        
        elif self.stage == Stage.CREDITS:
            self.gui.render(surf)
    
    def on_mouse_down(self, event):
        self.gui.on_mouse_down(event)
    
    def on_mouse_up(self, event):
        self.gui.on_mouse_up(event)
    
    def on_receive(self, data):
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
                    x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails_count, bonus_count = struct.unpack(">BBBBBBBBBBBB", data[11:23])
                    data = data[23:]
                    trails = []
                    for j in range(trails_count):
                        x, y, i = struct.unpack(">BBB", data[3*j:3*j+3])
                        trails.append((x, y, i))

                    data = data[3*trails_count:]
                    
                    bonus_list = {}
                    for j in range(bonus_count):
                        x, y, i = struct.unpack(">BBB", data[3*j:3*j+3])
                        bonus_list[(x, y)] = i
                    
                    data = data[3*bonus_count:]
                    col_start, col_x, col_y, bonus_scores_count = struct.unpack(">dBBB", data[:11])
                    data = data[11:]
                    for i in range(bonus_scores_count):
                        r, b = struct.unpack(">II", data[8*i:8*i+8])
                        self.bonus_scores[i][1] = r
                        self.bonus_scores[i][2] = b
                
                else:
                    x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2 = struct.unpack(">BBBBBBBBBB", data[7:])
                    trails = None
                    bonus_list = None
                    col_start, col_x, col_y = 0, 0, 0
                
                self.game.sync(x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails, bonus_list, col_start, col_x, col_y)
                if self.is_host():
                    self.game.end_turn()
                
                else:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT))