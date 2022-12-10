from player import Player
import numpy as np
import random
from math import radians, cos, sin
from bonus import Bonus, Bombe, Row, Column, Magical_potion

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
        self.Bonus_list = [Bombe, Row, Column, Magical_potion]
        self.reset()
    
    def reset(self):
        self.trails = np.array([self.HEIGHT, self.WIDTH], dtype="int8").fill(-1)
        self.players[0].reset(0, 0)
        self.players[1].reset(self.WIDTH-1, self.HEIGHT-1)
        
        self.collide_start = 0
        self.collide_pos = [0,0]
        self.trail_changes = []
        self.remaining = self.TIMER

        self.drool = np.array([self.HEIGHT, self.WIDTH], dtype="int8").fill(-1)
        self.bonus_dict = {}
    
    def is_host(self):
        return self.manager.is_host()
    
    def init_host(self):
        self.player = self.players[0]

    def init_guest(self):
        self.player = self.players[1]