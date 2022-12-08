import time

import pygame

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
        
        self.start_time = time.time()
        self.win = pygame.display.set_mode([self.WIDTH, self.HEIGHT], pygame.FULLSCREEN)
    
    def host(self):
        self._is_host = True
        self.game.init_host()
        self.socket_handler.host()
    
    def join(self, code):
        self.game.init_guest()
        self.socket_handler.join(code)
    
    def mainloop(self):
        while self.stage != Stage.STOP:
            pygame.display.set_caption(f"Snaildash - {self.clock.get_fps():.2f}fps")
            events = pygame.event.get()
            self.handle_events(events)
            self.render(self.win)
            pygame.display.flip()
            self.clock.tick(self.FPS)