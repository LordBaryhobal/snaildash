import numpy as np
import pygame
import time
from math import floor, ceil
import struct
import random

from player import Player

class Game:
    WIDTH = 15
    HEIGHT = 15
    TIMER = 0.25
    DURATION = 60
    COLLIDE_DURATION = 1
    COLLIDE_RADIUS = 4
    BOMB_SIZE = 3

    def __init__(self, manager):
        self.manager = manager
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.font = pygame.font.SysFont("arial", 30)
        self.bonus = [self.bomb, self.row, self.column]
        self.player = self.players[0]
        self.timer_start = 0
        self.start_time = 0
        self.ts = 1
        self.reset()

    def reset(self):
        self.trails = np.zeros([self.HEIGHT, self.WIDTH], dtype="int8")-1
        self.players[0].reset(0, 0)
        self.players[1].reset(self.WIDTH-1, self.HEIGHT-1)
        
        self.collide_start = 0
        self.collide_pos = [0,0]
        self.trail_changes = []
        self.remaining = self.TIMER

        self.drool = np.zeros([self.HEIGHT, self.WIDTH], dtype="int8")-1
        self.bonus_list = {
            (2,2): 1,
            (4,4):2,
            (8,8):0,
        }

    def loop(self):
        self.remaining = self.timer_start+self.TIMER - time.time()
        
        if self.remaining <= 0:
            if not self.player.synced:
                if not self.manager.is_host:
                    self.player.synced = True
                    self.end_turn()
    
    def render(self, surf, render_players=True):
        cur_time = time.time()
        
        w3, h3 = surf.get_width()/3, surf.get_height()/3
        
        tw = 2*w3/self.WIDTH
        th = 2*h3/self.HEIGHT
        ts = min(tw, th)
        if self.ts != ts:
            self.ts = ts
            self.resize()
        
        surf.fill(0)
        
        ox, oy = surf.get_width()/2 - self.WIDTH/2*self.ts, surf.get_height()/2 - self.HEIGHT/2*self.ts

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                t = self.trails[y, x]
                if t != -1:
                    drool_i = self.drool[y, x]
                    texture = self.drool_textures[drool_i][t]
                    
                    surf.blit(texture, [ox+(x-0.5)*self.ts, oy+(y-0.5)*self.ts])
        for b in self.bonus_list:
            b_id = self.bonus_list[b]
            x, y = b
            surf.blit(self.bonus_textures[b_id], [ox + (x-0.5)*self.ts, oy + (y-0.5)*self.ts])
        
        r = 1-max(0,self.remaining)/self.TIMER
        r = max(0, min(1, r))
        for player in self.players:
            x, y = player.x, player.y
            lx, ly = player.lx, player.ly
            X, Y = lx+(x-lx)*r, ly+(y-ly)*r
            
            if render_players:
                pygame.draw.circle(surf, Player.COLORS[player.i], [ox+(X+0.5)*self.ts, oy+(Y+0.5)*self.ts], self.ts/2)

                if player.stun_count != 0:
                    pygame.draw.line(surf, (0,255,0), [ox+X*self.ts, oy+Y*self.ts], [ox+(X+1)*self.ts, oy+(Y+1)*self.ts])
                    pygame.draw.line(surf, (0,255,0), [ox+X*self.ts, oy+(Y+1)*self.ts], [ox+(X+1)*self.ts, oy+Y*self.ts])
        
        remaining = self.start_time+self.DURATION - cur_time
        W = 2*w3
        w6 = w3/2
        w = W*remaining/self.DURATION
        pygame.draw.rect(surf, (255,255,255), [w6, surf.get_height()-10, w, 10])
        
        red = np.count_nonzero(self.trails == 0)
        blue = np.count_nonzero(self.trails == 1)
        full = self.WIDTH * self.HEIGHT
        redW = W*red/full
        blueW = W*blue/full
        
        h24 = h3/8
        w20 = W/20
        
        a = [w6+w20,   h24]
        b = [w6+W+w20, h24]
        c = [w6+W-w20, h24*2]
        d = [w6-w20,   h24*2]
        
        red_e  = [w6+w20+redW,    h24]
        blue_e = [w6+W+w20-blueW, h24]
        red_f  = [w6-w20+redW,    h24*2]
        blue_f = [w6+W-w20-blueW, h24*2]
        
        pygame.draw.polygon(surf, Player.COLORS[0], [a,red_e,red_f,d])
        pygame.draw.polygon(surf, Player.COLORS[1], [blue_e,b,c,blue_f])
        
        rem = self.collide_start+self.COLLIDE_DURATION-cur_time
        if rem > 0:
            r = 1-rem/self.COLLIDE_DURATION
            r = self.COLLIDE_RADIUS*r*self.ts
            pygame.draw.circle(surf, (255,255,255), [ox+(self.collide_pos[0]+0.5)*self.ts, oy+(self.collide_pos[1]+0.5)*self.ts], r, 3)
    
    def resize(self):
        self.drool_textures = []
        for i in range(16):
            texture = pygame.image.load(f"assets/textures/drool/{i}.png")
            texture = pygame.transform.scale(texture, [self.ts*2, self.ts*2])
            red, blue = texture.copy(), texture.copy()
            red.fill(Player.TRAIL_COLORS[0]+(255,), None, pygame.BLEND_RGBA_MULT)
            blue.fill(Player.TRAIL_COLORS[1]+(255,), None, pygame.BLEND_RGBA_MULT)
            self.drool_textures.append((red, blue))
        self.bonus_textures = []
        for b in ("bomb", "row", "column"):
            if b =="column":
                texture = pygame.transform.rotate(pygame.image.load(f"assets/textures/bonus/row.png"), 90)
            else:
                texture = pygame.image.load(f"assets/textures/bonus/{b}.png")
            texture = pygame.transform.scale(texture, [self.ts*2, self.ts*2])
            self.bonus_textures.append(texture)
    
    def handle_key(self, event):
        ndir = self.player.dir%4
        if event.key == pygame.K_w:
            ndir = 3
        
        elif event.key == pygame.K_s:
            ndir = 1
        
        elif event.key == pygame.K_a:
            ndir = 2
        
        elif event.key == pygame.K_d:
            ndir = 0
        
        if (event.mod & pygame.KMOD_LSHIFT and self.player.candash()) or self.player.dash:
            if not self.player.dash:
                self.player.dash = True
                self.player.usedash()
            ndir += 4
        self.player.dir = ndir 

    
    def start_turn(self):
        self.timer_start = time.time()
        self.player.synced = False
        self.trail_changes = []
        for player in self.players:
            player.lx, player.ly = player.x, player.y
            player.x, player.y = player.nx, player.ny
            player.dir %= 4
            player.dash = False
    
    def end_turn(self):
        if self.manager.is_host:
            for player in self.players:
                player.synced = False
                if player.stun_count != 0:
                    player.stun_count -= 1
                
                else:
                    dx, dy = Player.OFFSETS[player.dir]
                    x, y = player.x, player.y
                    x2, y2 = x+dx, y+dy
                    x2 = max(0, min(self.WIDTH-1, x2))
                    y2 = max(0, min(self.HEIGHT-1, y2))
                    
                    player.nx, player.ny = x2, y2
                    if player.dir > 3:
                        dx, dy = Player.OFFSETS[player.dir%4]
                        for i in range(Player.DASH_SIZE):
                            tx, ty = x+dx*i, y+dy*i
                            if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT:
                                if self.trails[ty, tx] != player.i:
                                    self.trail_changes.append((tx, ty, player.i))
                    elif self.trails[y, x] != player.i:
                        self.trail_changes.append((x, y, player.i))

            p1, p2 = self.players
            if p1.dir <=3:
                if p2.dir <=3:
                    if (p1.nx == p2.nx and p1.ny == p2.ny) or (p1.x == p2.nx and p1.y == p2.ny and p2.x == p1.nx and p2.y == p1.ny):
                        p1.nx, p1.ny = p1.x, p1.y
                        p2.nx, p2.ny = p2.x, p2.y
                        self.collide()
                else:
                    dx, dy = Player.OFFSETS[p2.dir%4]
                    p2_cells = [ (p2.x + dx*i, p2.y + dy*i) for i in range(1, Player.DASH_SIZE+1)]
                    if (p1.nx, p1.ny) in p2_cells:
                        p2.nx, p2.ny = p1.nx - dx, p1.ny - dy
                        p1.nx, p1.ny = p1.x, p1.y
                        self.collide()
            else:
                if p2.dir <=3:
                    dx, dy = Player.OFFSETS[p1.dir%4]
                    p1_cells = [(p1.x + dx*i, p1.y + dy*i) for i in range(1, Player.DASH_SIZE+1)]
                    if (p2.nx, p2.ny) in p1_cells:
                        p1.nx, p1.ny = p2.nx - dx, p2.ny - dy
                        p2.nx, p2.ny = p2.x, p2.y
                        self.collide()
                else:
                    #double dash
                    dx_1, dy_1 = Player.OFFSETS[p1.dir%4]
                    dx_2, dy_2 = Player.OFFSETS[p2.dir%4]
                    for i in range(1, Player.DASH_SIZE):
                        cx1, cy1 = p1.x + dx_1*i, p1.y + dy_1*i
                        cx2, cy2 = p2.x + dx_2*i, p2.y + dy_2*i
                        if (cx1, cy1) == (cx2, cy2):
                            p1.nx, p1.ny = cx1 -dx_1, cy1 -dy_1
                            p2.nx, p2.ny = cx2 -dx_2, cy2 -dy_2
                            self.collide()
                            break
            
            for player in self.players:
                if self.trails[player.ny, player.nx] == player.i:
                    player.add_dashscore()
                pos = (player.nx, player.ny)
                if pos in self.bonus_list:
                    self.bonus[self.bonus_list[pos]](*pos, player.i)
                    self.bonus_list.pop(pos)
            for x, y, i in self.trail_changes:
                self.trails[y, x] = -1 if i == 2 else i
                self.drool[y, x] = random.randint(0,15)
            self.send_sync()
            pygame.event.post(pygame.event.Event(pygame.USEREVENT))
            
        else:
            self.send_sync()
    
    def sync(self, x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails=None, col_start=0, col_x=0, col_y=0):
        if self.player.i == 1 or not self.manager.is_host:
            self.players[0].lx = self.players[0].x
            self.players[0].ly = self.players[0].y
            self.players[0].nx = x1
            self.players[0].ny = y1
            self.players[0].dir = d1
            self.players[0].stun_count = s1
            self.players[0].dashscore = ds1
        
        if self.player.i == 0 or not self.manager.is_host:
            self.players[1].lx = self.players[1].x
            self.players[1].ly = self.players[1].y
            self.players[1].nx = x2
            self.players[1].ny = y2
            self.players[1].dir = d2
            self.players[1].stun_count = s2
            self.players[1].dashscore = ds2
        
        if trails:
            for x, y, i in trails:
                self.trails[y, x] = -1 if i == 2 else i
                self.drool[y, x] = random.randint(0,15)
            
            self.collide_start = col_start
            self.collide_pos = [col_x, col_y]
                
    def send_sync(self):
        x1 = self.players[0].nx
        y1 = self.players[0].ny
        d1 = self.players[0].dir
        s1 = int(self.players[0].stun_count)
        ds1 = self.players[0].dashscore
        x2 = self.players[1].nx
        y2 = self.players[1].ny
        d2 = self.players[1].dir
        s2 = int(self.players[1].stun_count)
        ds2 = self.players[1].dashscore
        
        if self.manager.is_host:
            trails = []
            for x, y, i in self.trail_changes:
                trails.append(f"{x}|{y}|{i}")
            
            trails = "/".join(trails)
            msg = b"turnEndHost" + struct.pack(">BBBBBBBBBBB", x1,y1,d1,s1,ds1,x2,y2,d2,s2,ds2,len(self.trail_changes))
            for x, y, i in self.trail_changes:
                msg += struct.pack(">BBB", x,y,i)
            
            msg += struct.pack(">dBB", self.collide_start, self.collide_pos[0], self.collide_pos[1])
            
        else:
            msg = b"turnEnd" + struct.pack(">BBBBBBBBBB", x1,y1,d1,s1,ds1,x2,y2,d2,s2,ds2)
        
        self.manager.sh.send(msg)
    
    def collide(self):
        p1, p2 = self.players
        for p in self.players:
            if not (p.dir == 0 and p.x == self.WIDTH-1) and not (p.dir == 1 and p.y == self.HEIGHT-1) and not (p.dir == 2 and p.x == 0) and not (p.dir == 3 and p.y== 0):
                p.dir = (p.dir%4+2)%4
        
        ox, oy = (p1.x+p2.x)/2, (p1.y+p2.y)/2
        
        self.collide_start = time.time()
        self.collide_pos = [int(ox), int(oy)]
        
        x1, y1 = floor(ox-2), floor(oy-2)
        x2, y2 = ceil(ox+2), ceil(oy+2)
        
        x1, x2 = max(0, min(self.WIDTH-1, x1)), max(0, min(self.WIDTH-1, x2))
        y1, y2 = max(0, min(self.HEIGHT-1, y1)), max(0, min(self.HEIGHT-1, y2))
        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self.trail_changes.append((x, y, 2))
            
    def bomb(self, x, y, i):
        sx, sy = max(ceil(x-(self.BOMB_SIZE/2)),0), max(ceil(y-(self.BOMB_SIZE/2)), 0)
        esx, esy = min(floor(x + self.BOMB_SIZE/2), self.WIDTH-1)+1, min(floor(y + self.BOMB_SIZE/2), self.HEIGHT-1)+1
        for by in range(sy, esy):
            for bx in range(sx, esx):
                self.trail_changes.append((bx, by, i))
    
    def row(self, x, y, i):
        for rx in range(0,self.WIDTH):
            self.trail_changes.append((rx, y, i))
        
    def column(self, x, y, i):
        for ry in range(0,self.HEIGHT):
            self.trail_changes.append((x, ry, i))
        