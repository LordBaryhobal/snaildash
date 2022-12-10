from player import Player
import numpy as np
import pygame
from bonus import Bonus, Bomb, Row, Column, MagicalPotion

class Game:
    WIDTH = 15  # Width of the grid
    HEIGHT = 15  # Height of the grid
    TIMER = 0.25  # Duration in seconds of a turn
    DURATION = 89  # Duration in seconds of the whole game
    COLLIDE_DURATION = 1  # Duration in seconds of the collision animation
    COLLIDE_RADIUS = 4  # Radius in number of tiles of the collision shockwave
    
    def __init__(self, manager):
        self.manager = manager
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.bonus = Bonus
        self.bonus_list = [Bomb, Row, Column, MagicalPotion]
        self.reset()
    
    def reset(self):
        self.trails = np.full([self.HEIGHT, self.WIDTH], -1, dtype="int8")
        self.players[0].reset(0, 0)
        self.players[1].reset(self.WIDTH-1, self.HEIGHT-1)
        
        self.collide_start = 0
        self.collide_pos = [0,0]
        self.trail_changes = []
        self.remaining = self.TIMER
        self.start_time = 0
        self.turn_start = 0

        self.drool = np.full([self.HEIGHT, self.WIDTH], -1, dtype="int8")
        self.bonus_dict = {}
    
    def is_host(self):
        return self.manager.is_host()
    
    def init_host(self):
        self.player = self.players[0]

    def init_guest(self):
        self.player = self.players[1]
    
    def get_trail_count(self):
        return (np.count_nonzero(self.game.trails == 0) + np.count_nonzero(self.game.trails == 2), \
        np.count_nonzero(self.game.trails == 1) + np.count_nonzero(self.game.trails == 3))
    
    def start_turn(self):
        self.turn_start = self.manager.time()
        self.player.synced = False
        self.trail_changes = []
        for player in self.players:
            player.lx, player.ly = player.x, player.y
            player.x, player.y = player.nx, player.ny
            player.dir %= 4
            player.dash = False
            player.reinforced = max(player.reinforced-1, 0)
    
    def handle_key(self, event):
        ndir = self.player.dir%4
        if event.key == pygame.K_w or event.key == pygame.K_UP:
            ndir = 3
        
        elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
            ndir = 1
        
        elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
            ndir = 2
        
        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
            ndir = 0
        if ((event.mod & pygame.KMOD_LSHIFT or event.key == pygame.K_SPACE) and self.player.candash()) or self.player.dash:
            if not self.player.dash:
                self.player.dash = True
                self.player.usedash()
            ndir += 4
        self.player.dir = ndir