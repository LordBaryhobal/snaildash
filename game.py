#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

from math import ceil, floor
from random import randint
import struct

import numpy as np
import pygame

from bonus import Bonus, Bomb, Row, Column, MagicalPotion
from player import Player

class Game:
    """Main class managing the game's state"""

    WIDTH = 15  # Width of the grid
    HEIGHT = 15  # Height of the grid
    TIMER = 0.25  # Duration in seconds of a turn
    DURATION = 89  # Duration in seconds of the whole game
    COLLIDE_DURATION = 1  # Duration in seconds of the collision animation
    COLLIDE_RADIUS = 4  # Radius in number of tiles of the collision shockwave
    
    def __init__(self, manager):
        """Initializes a Game instance

        Args:
            manager (Manager): manager instance
        """
        
        self.manager = manager
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.bonus_list = [Bomb, Row, Column, MagicalPotion]
        self.reset()
    
    def reset(self):
        """Resets the state and different values before a new game"""

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
        """Returns whether this instance is the host or not

        Returns:
            bool: True if host, False if guest
        """
        return self.manager.is_host()
    
    def init_host(self):
        """Initializes the game as the host"""
        self.player = self.players[0]

    def init_guest(self):
        """Initializes the game as the guest"""
        self.player = self.players[1]
    
    def get_trail_count(self):
        """Returns the number of cells covered in drool for each player

        Returns:
            tuple[int, int]: counts for (red, blue)
        """
        return (np.count_nonzero(self.trails == 0) + np.count_nonzero(self.trails == 2), \
        np.count_nonzero(self.trails == 1) + np.count_nonzero(self.trails == 3))
    
    def start_turn(self):
        """Starts a new turn"""

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
        """Handles a pygame.KEYDOWN event

        Args:
            event (pygame.EVENT): the pygame event
        """

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
    
    def end_turn(self):
        """Finalizes the current turn"""

        if self.manager.is_host():
            for player in self.players:
                player.synced = False
                dx, dy = Player.OFFSETS[player.dir]
                x, y = player.x, player.y
                x2, y2 = x+dx, y+dy
                x2 = max(0, min(self.WIDTH-1, x2))
                y2 = max(0, min(self.HEIGHT-1, y2))
                
                player.nx, player.ny = x2, y2
                if player.dir > 3:
                    player.dashed_count += 1
                    dx, dy = Player.OFFSETS[player.dir%4]
                    for i in range(Player.DASH_SIZE):
                        tx, ty = x+dx*i, y+dy*i
                        if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT:
                            t = player.i
                            if player.reinforced > 0:
                                t += 2
                            self.set_trail(tx, ty, t)
                else:
                    t = player.i
                    if player.reinforced > 0:
                        t += 2
                    self.set_trail(x, y, t)
            
            self.check_collsion()
            
            for player in self.players:
                if self.trails[player.ny, player.nx] == player.i or self.trails[player.ny, player.nx] == player.i+2:
                    player.add_dashscore()
                pos = (player.nx, player.ny)
                if pos in self.bonus_dict:
                    self.bonus_list[self.bonus_dict[pos]].apply(*pos, self, player)
                    self.bonus_dict.pop(pos)
            for x, y, i in self.trail_changes:
                self.trails[y, x] = -1 if i == 255 else i
                self.drool[y, x] = randint(0,15)
            
            Bonus.try_spawn(self)

            self.send_sync()
            pygame.event.post(pygame.event.Event(pygame.USEREVENT))
            
        else:
            self.send_sync()
            
    def check_collsion(self):
        """Checks the movements of each player to process collisions"""

        p1, p2 = self.players
        if p1.dir <=3:
            if p2.dir <=3:
                if (p1.nx == p2.nx and p1.ny == p2.ny) or (p1.x == p2.nx and p1.y == p2.ny and p2.x == p1.nx and p2.y == p1.ny):
                    center = (p1.nx, p1.ny) if p1.nx == p2.nx else ((p1.x + p2.y)/2, (p1.y + p2.y)/2)
                    p1.nx, p1.ny = p1.x, p1.y
                    p2.nx, p2.ny = p2.x, p2.y
                    self.collide(center)
            else:
                dx, dy = Player.OFFSETS[p2.dir%4]
                p2_cells = [ (p2.x + dx*i, p2.y + dy*i) for i in range(1, Player.DASH_SIZE+1)]
                if (p1.nx, p1.ny) in p2_cells:
                    center = (p1.nx, p1.ny)
                    p2.nx, p2.ny = p1.nx - dx, p1.ny - dy
                    p1.nx, p1.ny = p1.x, p1.y
                    self.collide(center)
                for cell in p2_cells:
                    if cell in self.bonus_dict:
                        self.bonus_list[self.bonus_dict[cell]].apply(*cell, self, p2)
                        self.bonus_dict.pop(cell)
        else:
            if p2.dir <=3:
                dx, dy = Player.OFFSETS[p1.dir%4]
                p1_cells = [(p1.x + dx*i, p1.y + dy*i) for i in range(1, Player.DASH_SIZE+1)]
                if (p2.nx, p2.ny) in p1_cells:
                    center = (p2.nx, p2.ny)
                    p1.nx, p1.ny = p2.nx - dx, p2.ny - dy
                    p2.nx, p2.ny = p2.x, p2.y
                    self.collide(center)
                for cell in p1_cells:
                    if cell in self.bonus_dict:
                        self.bonus_list[self.bonus_dict[cell]].apply(*cell, self, p1)
                        self.bonus_dict.pop(cell)
            else:
                #double dash
                dx_1, dy_1 = Player.OFFSETS[p1.dir%4]
                dx_2, dy_2 = Player.OFFSETS[p2.dir%4]
                for i in range(1, Player.DASH_SIZE):
                    cx1, cy1 = p1.x + dx_1*i, p1.y + dy_1*i
                    cx2, cy2 = p2.x + dx_2*i, p2.y + dy_2*i
                    if (cx1, cy1) in self.bonus_dict:
                        self.bonus_list[self.bonus_dict[(cx1, cy1)]].apply(cx1, cy1, self, p1)
                        self.bonus_dict.pop((cx1, cy1))
                    if (cx2, cy2) in self.bonus_dict:
                        self.bonus_list[self.bonus_dict[(cx2, cy2)]].apply(cx2, cy2, self, p2)
                        self.bonus_dict.pop((cx2, cy2))
                    if (cx1, cy1) == (cx2, cy2):
                        center = (cx1, cy1)
                        p1.nx, p1.ny = cx1 -dx_1, cy1 -dy_1
                        p2.nx, p2.ny = cx2 -dx_2, cy2 -dy_2
                        self.collide(center)
                        break
        
    def collide(self, center):
        """Process a collision

        Args:
            center (tuple[int, int]): position in tiles of the collision's center
        """

        for p in self.players:
            if not (p.dir == 0 and p.x == self.WIDTH-1) and not (p.dir == 1 and p.y == self.HEIGHT-1) and not (p.dir == 2 and p.x == 0) and not (p.dir == 3 and p.y== 0):
                p.dir = (p.dir%4+2)%4
        
        ox, oy = center
        
        self.collide_start = self.manager.time()
        self.collide_pos = [int(ox), int(oy)]
        
        x1, y1 = floor(ox-2), floor(oy-2)
        x2, y2 = ceil(ox+2), ceil(oy+2)
        
        x1, x2 = max(0, min(self.WIDTH-1, x1)), max(0, min(self.WIDTH-1, x2))
        y1, y2 = max(0, min(self.HEIGHT-1, y1)), max(0, min(self.HEIGHT-1, y2))
        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self.set_trail(x,y,255)

    def loop(self):
        """Main game loop (executed on every frame)"""

        self.remaining = self.turn_start+self.TIMER - self.manager.time()
        
        if self.remaining <= 0:
            if not self.player.synced:
                if not self.manager.is_host():
                    self.player.synced = True
                    self.end_turn()
    
    def sync(self, x1, y1, d1, ds1, x2, y2, d2, ds2, trails=None, bonus_dict=None, col_start=0, col_x=0, col_y=0):
        """Process synchronization info received from the other device

        Args:
            x1 (int): x position of player 1
            y1 (int): y position of player 1
            d1 (int): direction of player 1
            ds1 (int): dashscore of player 1
            x2 (int): x position of player 2
            y2 (int): y position of player 2
            d2 (int): direction of player 2
            ds2 (int): dashscore of player 2
            trails (list[tuple[int, int, int]], optional): list of trail changes. Defaults to None.
            bonus_dict (dict[tuple[int, int], int], optional): dictionary of placed bonuses. Defaults to None.
            col_start (float, optional): start time of collision. Defaults to 0.
            col_x (int, optional): x position of the collision. Defaults to 0.
            col_y (int, optional): y position of the collision. Defaults to 0.
        """
        
        if self.player.i == 1 or not self.manager.is_host():
            self.players[0].lx = self.players[0].x
            self.players[0].ly = self.players[0].y
            self.players[0].nx = x1
            self.players[0].ny = y1
            self.players[0].dir = d1
            self.players[0].dashscore = ds1
        
        if self.player.i == 0 or not self.manager.is_host():
            self.players[1].lx = self.players[1].x
            self.players[1].ly = self.players[1].y
            self.players[1].nx = x2
            self.players[1].ny = y2
            self.players[1].dir = d2
            self.players[1].dashscore = ds2
        
        if trails is not None:
            for x, y, i in trails:
                self.trails[y, x] = -1 if i == 255 else i
                self.drool[y, x] = randint(0,15)
                
            self.bonus_dict = bonus_dict
            self.collide_start = col_start
            self.collide_pos = [col_x, col_y]
                
    def send_sync(self):
        """Sends synchronization info to the other device"""
        
        x1 = self.players[0].nx
        y1 = self.players[0].ny
        d1 = self.players[0].dir
        ds1 = self.players[0].dashscore
        x2 = self.players[1].nx
        y2 = self.players[1].ny
        d2 = self.players[1].dir
        ds2 = self.players[1].dashscore
        
        if self.manager.is_host():
            msg = b"turnEndHost" + struct.pack(">BBBBBBBBBB", x1,y1,d1,ds1,x2,y2,d2,ds2,len(self.trail_changes),len(self.bonus_dict))
            for x, y, i in self.trail_changes:
                msg += struct.pack(">BBB", x,y,i)
            
            for (x, y), i in self.bonus_dict.items():
                msg += struct.pack(">BBB", x,y,i)
            
            msg += struct.pack(">dBB", self.collide_start, self.collide_pos[0], self.collide_pos[1])
            bonus_scores = self.manager.get_bonus_scores()
            msg += struct.pack(">B", len(bonus_scores))
            for n, r, b in bonus_scores:
                msg += struct.pack(">II", r, b)
            
        else:
            msg = b"turnEnd" + struct.pack(">BBBBBBBB", x1,y1,d1,ds1,x2,y2,d2,ds2)
        
        self.manager.socket_handler.send(msg)
    
    def set_trail(self, x, y, i):
        """Sets the drool at a given position

        Args:
            x (int): x coordinate
            y (int): y coordinate
            i (int): drool id (0:red, 1:blue, 2:reinf. red, 3:reinf. blue, -1/255:none)
        """
        
        if i != -1 and i != 255:
            cur = self.trails[y,x]
            if i == cur: return
            if i%2 == cur%2:
                if i < cur: return
            elif cur > 1:
                i = cur-2
        
        if i > 1 and i != 255:
            self.players[i%2].reinforced_placed += 1
        
        self.trail_changes.append((x,y,i))
