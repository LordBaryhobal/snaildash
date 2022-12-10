import struct
import time

import pygame

from display_manager import DisplayManager
from game import Game
from gui import GUI
from socket_handler import SocketHandler
from sound_manager import SoundManager
from stage import Stage

class Manager:
    WIDTH, HEIGHT = 800, 800 #1920, 1080
    FPS = 30
    
    COUNTDOWN_DUR = 4  # Duration in seconds of the start countdown
    BREAKDOWN_IN_DUR = 2  # Duration in seconds of the game to breakdown transition
    BREAKDOWN_BAR_DUR = 4  # Duration in seconds of the progress bar animation
    BREAKDOWN_BAR_PAUSE = 0.5  # Duration in seconds before the progress bar end fill
    BREAKDOWN_BAR_END_DUR = 0.2  # Duration in seconds of the bar end fill
    BREAKDOWN_INTERVAL = 1  # Interval in seconds between each bonus score reveal

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snaildash")
        self.clock = pygame.time.Clock()
        self.stage = Stage.MAIN_MENU
        self.socket_handler = SocketHandler(self)
        self.game = Game(self)
        self.gui = GUI()
        self.display_manager = DisplayManager(self)
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
        self.win = pygame.display.set_mode([self.WIDTH, self.HEIGHT], pygame.RESIZABLE)#, pygame.FULLSCREEN)
    
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
            self.display_manager.render(self.win)
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
            
            elif event.type == pygame.USEREVENT+1:
                SoundManager.get(["click.wav"]).play()
                
                name = event.name
                if name == "main.play":
                    self.socket_handler.send(b"ready")
                    self.gui.set_menu("waiting")
                    self.stage = Stage.WAITING_OPPONENT
                
                elif name == "main.tutorial":
                    self.tutorial.start_time = time.time()
                    self.stage = Stage.TUTORIAL
                
                elif name == "main.credits":
                    self.gui.set_menu("credits")
                    self.stage = Stage.CREDITS
                
                elif name in ["waiting.main", "credits.main", "breakdown.main"]:
                    self.gui.set_menu("main")
                    self.stage = Stage.MAIN_MENU
        
        if self.stage == Stage.COUNTDOWN:
            rem = self.countdown_start+self.COUNTDOWN_DUR-time.time()
            if rem <= 0:
                self.stage = Stage.IN_GAME
                #pygame.mixer.music.play()
                self.game.start_time = self.time()
                self.game.start_turn()

        elif self.stage == Stage.IN_GAME:
            self.game.loop()
            rem = self.game.start_time+self.game.DURATION-self.time()
            if rem <= 0:
                self.stage = Stage.GAME_TO_BREAKDOWN
                self.game_to_breakdown_start = self.time()
        
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
    
    def play(self, send=False):
        if send:
            self.socket_handler.send(b"start")
        
        self.game.reset()
        
        self.countdown_start = time.time()
        self.stage = Stage.COUNTDOWN
        self.time_origin = time.time()
        self.gui.visible = False