import numpy as np
import pygame
import time
from math import floor, ceil
import struct
import random
import os

from player import Player

class Game:
    WIDTH = 15
    HEIGHT = 15
    TIMER = 0.25
    DURATION = 90
    COLLIDE_DURATION = 1
    COLLIDE_RADIUS = 4
    BOMB_SIZE = 5
    DISTANCE_MIN = 4
    MAX_BONUS = 4
    BONUS_CHANCE = 0.2
    POISON_TIME = 4

    def __init__(self, manager):
        self.manager = manager
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.font = pygame.font.SysFont("arial", 30)
        self.bonus = [self.bomb, self.row, self.column, self.poison]
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
        }

    def loop(self):
        self.remaining = self.timer_start+self.TIMER - self.manager.time()
        
        if self.remaining <= 0:
            if not self.player.synced:
                if not self.manager.is_host:
                    self.player.synced = True
                    self.end_turn()
    
    def render(self, surf, render_players=True):
        cur_time = self.manager.time()
        
        w3, h3 = surf.get_width()/3, surf.get_height()/3
        
        tw = 2*w3/self.WIDTH
        th = 2*h3/self.HEIGHT
        ts = min(tw, th)
        if self.ts != ts:
            self.ts = ts
            self.resize()
        
        surf.fill(0)
        
        ox, oy = surf.get_width()/2 - self.WIDTH/2*self.ts, surf.get_height()/2 - self.HEIGHT/2*self.ts

        surf.blit(self.tiles, [ox, oy])

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                t = self.trails[y, x]
                if t != -1:
                    drool_i = self.drool[y, x]
                    texture = self.drool_textures[drool_i][t]
                    
                    surf.blit(texture, [ox+(x-0.5)*self.ts, oy+(y-0.5)*self.ts])
        bonus_l = self.bonus_list.copy()
        for (x, y), i in bonus_l.items():
            surf.blit(self.bonus_textures[i], [ox + (x-0.5)*self.ts, oy + (y-0.5)*self.ts])
        
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
        if self.start_time == 0: remaining = self.DURATION
        W = 2*w3
        w6 = w3/2
        w = W * max(0, min(1, remaining/self.DURATION))
        pygame.draw.rect(surf, (255,255,255), [w6, surf.get_height()-10, w, 10])
        
        if self.collide_start != 0:
            rem = self.collide_start+self.COLLIDE_DURATION-cur_time
            if rem > 0:
                r = 1-rem/self.COLLIDE_DURATION
                r = self.COLLIDE_RADIUS*r*self.ts
                pygame.draw.circle(surf, (255,255,255), [ox+(self.collide_pos[0]+0.5)*self.ts, oy+(self.collide_pos[1]+0.5)*self.ts], r, 3)
        
        ds_texture = self.dashscore_textures[min(Player.MAX_DASHSCORE, self.player.dashscore)]
        surf.blit(ds_texture, [ox-ds_texture.get_width()-self.ts, surf.get_height()/2-ds_texture.get_height()/2])
    
    def resize(self):
        tile = pygame.image.load(os.path.join("assets","textures","grass2.png"))
        w, h = tile.get_size()
        self.tiles = pygame.Surface([self.WIDTH*w, self.HEIGHT*h])
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                self.tiles.blit(tile, [x*w, y*h])
        self.tiles = pygame.transform.scale(self.tiles, [self.WIDTH*self.ts, self.HEIGHT*self.ts])

        self.drool_textures = []
        for i in range(16):
            texture = pygame.image.load(os.path.join("assets","textures","drool",f"{i}.png"))
            texture_poison = pygame.image.load(os.path.join("assets","textures","drool_poison",f"{i}.png"))
            texture = pygame.transform.scale(texture, [self.ts*2, self.ts*2])
            texture_poison = pygame.transform.scale(texture_poison, [self.ts*2, self.ts*2])
            red, blue = texture.copy(), texture.copy()
            redp, bluep = texture_poison.copy(), texture_poison.copy()
            red.fill(Player.TRAIL_COLORS[0]+(255,), None, pygame.BLEND_RGBA_MULT)
            blue.fill(Player.TRAIL_COLORS[1]+(255,), None, pygame.BLEND_RGBA_MULT)
            redp.fill(Player.TRAIL_COLORS[0]+(255,), None, pygame.BLEND_RGBA_MULT)
            bluep.fill(Player.TRAIL_COLORS[1]+(255,), None, pygame.BLEND_RGBA_MULT)
            self.drool_textures.append((red, blue, redp, bluep))
        self.bonus_textures = []
        for b in ("bomb2", "row", "column", "poison"):
            if b =="column":
                texture = pygame.transform.rotate(pygame.image.load(os.path.join("assets","textures","bonus","row.png")), 90)
            else:
                texture = pygame.image.load(os.path.join("assets","textures","bonus",f"{b}.png"))
            texture = pygame.transform.scale(texture, [self.ts*2, self.ts*2])
            self.bonus_textures.append(texture)
        
        self.dashscore_textures = []
        for i in range(5):
            texture = pygame.image.load(os.path.join("assets","textures","dash_score_bar",f"{i}.png"))
            texture = pygame.transform.scale(texture, [self.ts*2, self.ts*8])
            texture.fill(Player.COLORS[self.player.i]+(255,), None, pygame.BLEND_RGBA_MULT)
            self.dashscore_textures.append(texture)
    
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

    
    def start_turn(self):
        self.timer_start = self.manager.time()
        self.player.synced = False
        self.trail_changes = []
        for player in self.players:
            player.lx, player.ly = player.x, player.y
            player.x, player.y = player.nx, player.ny
            player.dir %= 4
            player.dash = False
            player.poisoned = max(player.poisoned-1, 0)
    
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
                                t = player.i
                                if player.poisoned > 0:
                                    t += 2
                                self.set_trail(tx, ty, t)
                    else:
                        t = player.i
                        if player.poisoned > 0:
                            t += 2
                        self.set_trail(x, y, t)

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
                    for cell in p2_cells:
                        if cell in self.bonus_list:
                            self.bonus[self.bonus_list[cell]](*cell, p2.i)
                            self.bonus_list.pop(cell)
            else:
                if p2.dir <=3:
                    dx, dy = Player.OFFSETS[p1.dir%4]
                    p1_cells = [(p1.x + dx*i, p1.y + dy*i) for i in range(1, Player.DASH_SIZE+1)]
                    if (p2.nx, p2.ny) in p1_cells:
                        p1.nx, p1.ny = p2.nx - dx, p2.ny - dy
                        p2.nx, p2.ny = p2.x, p2.y
                        self.collide()
                    for cell in p1_cells:
                        if cell in self.bonus_list:
                            self.bonus[self.bonus_list[cell]](*cell, p1.i)
                            self.bonus_list.pop(cell)
                else:
                    #double dash
                    dx_1, dy_1 = Player.OFFSETS[p1.dir%4]
                    dx_2, dy_2 = Player.OFFSETS[p2.dir%4]
                    for i in range(1, Player.DASH_SIZE):
                        cx1, cy1 = p1.x + dx_1*i, p1.y + dy_1*i
                        cx2, cy2 = p2.x + dx_2*i, p2.y + dy_2*i
                        if (cx1, cy1) in self.bonus_list:
                            self.bonus[self.bonus_list[(cx1, cy1)]](cx1, cy1, p1.i)
                            self.bonus_list.pop((cx1, cy1))
                        if (cx2, cy2) in self.bonus_list:
                            self.bonus[self.bonus_list[(cx2, cy2)]](cx2, cy2, p2.i)
                            self.bonus_list.pop((cx2, cy2))
                        if (cx1, cy1) == (cx2, cy2):
                            p1.nx, p1.ny = cx1 -dx_1, cy1 -dy_1
                            p2.nx, p2.ny = cx2 -dx_2, cy2 -dy_2
                            self.collide()
                            break
            
            for player in self.players:
                if self.trails[player.ny, player.nx] == player.i or self.trails[player.ny, player.nx] == player.i+2:
                    player.add_dashscore()
                pos = (player.nx, player.ny)
                if pos in self.bonus_list:
                    self.bonus[self.bonus_list[pos]](*pos, player.i)
                    self.bonus_list.pop(pos)
            for x, y, i in self.trail_changes:

                self.trails[y, x] = -1 if i == 255 else i
                self.drool[y, x] = random.randint(0,15)
            
            if len(self.bonus_list) < self.MAX_BONUS and random.random() < self.BONUS_CHANCE:
                self.new_bonus()

            self.send_sync()
            pygame.event.post(pygame.event.Event(pygame.USEREVENT))
            
        else:
            self.send_sync()
    
    def sync(self, x1, y1, d1, s1, ds1, x2, y2, d2, s2, ds2, trails=None, bonus_list=None, col_start=0, col_x=0, col_y=0):
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
                self.trails[y, x] = -1 if i == 255 else i
                self.drool[y, x] = random.randint(0,15)
            
            self.bonus_list = bonus_list
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
            msg = b"turnEndHost" + struct.pack(">BBBBBBBBBBBB", x1,y1,d1,s1,ds1,x2,y2,d2,s2,ds2,len(self.trail_changes),len(self.bonus_list))
            for x, y, i in self.trail_changes:
                msg += struct.pack(">BBB", x,y,i)
            
            for (x, y), i in self.bonus_list.items():
                msg += struct.pack(">BBB", x,y,i)
            
            msg += struct.pack(">dBB", self.collide_start, self.collide_pos[0], self.collide_pos[1])
            msg += struct.pack(">B", len(self.manager.bonus_scores))
            for n, r, b in self.manager.bonus_scores:
                msg += struct.pack(">BB", r, b)
            
        else:
            msg = b"turnEnd" + struct.pack(">BBBBBBBBBB", x1,y1,d1,s1,ds1,x2,y2,d2,s2,ds2)
        
        self.manager.sh.send(msg)
    
    def collide(self):
        p1, p2 = self.players
        for p in self.players:
            if not (p.dir == 0 and p.x == self.WIDTH-1) and not (p.dir == 1 and p.y == self.HEIGHT-1) and not (p.dir == 2 and p.x == 0) and not (p.dir == 3 and p.y== 0):
                p.dir = (p.dir%4+2)%4
        
        ox, oy = (p1.x+p2.x)/2, (p1.y+p2.y)/2
        
        self.collide_start = self.manager.time()
        self.collide_pos = [int(ox), int(oy)]
        
        x1, y1 = floor(ox-2), floor(oy-2)
        x2, y2 = ceil(ox+2), ceil(oy+2)
        
        x1, x2 = max(0, min(self.WIDTH-1, x1)), max(0, min(self.WIDTH-1, x2))
        y1, y2 = max(0, min(self.HEIGHT-1, y1)), max(0, min(self.HEIGHT-1, y2))
        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self.set_trail(x,y,255)
            
    def bomb(self, x, y, i):
        sx, sy = max(ceil(x-(self.BOMB_SIZE/2)),0), max(ceil(y-(self.BOMB_SIZE/2)), 0)
        esx, esy = min(floor(x + self.BOMB_SIZE/2), self.WIDTH-1)+1, min(floor(y + self.BOMB_SIZE/2), self.HEIGHT-1)+1
        for by in range(sy, esy):
            for bx in range(sx, esx):
                t = i
                if self.players[i].poisoned > 0:
                    t += 2
                self.set_trail(bx, by, t)
    
    def row(self, x, y, i):
        for rx in range(0,self.WIDTH):
            t = i
            if self.players[i].poisoned > 0:
                t += 2
            self.set_trail(rx, y, t)
        
    def column(self, x, y, i):
        for ry in range(0,self.HEIGHT):
            t = i
            if self.players[i].poisoned > 0:
                t += 2
            self.set_trail(x, ry, t)
    
    def poison(self, x, y, i):
        self.players[i].poisoned = self.POISON_TIME
    
    def new_bonus(self):
        x, y = random.randint(0,self.WIDTH-1), random.randint(0,self.HEIGHT-1)
        id = random.randint(0,len(self.bonus)-1)
        if (x, y) in self.bonus_list:
            self.new_bonus()
            return
        for player in self.players:
            if abs(player.x-x) < self.DISTANCE_MIN and abs(player.y-y) < self.DISTANCE_MIN:
                self.new_bonus()
                return
        self.bonus_list[(x, y)] = id
    
    def set_trail(self, x, y, i):
        if i != -1 and i != 255:
            cur = self.trails[y,x]
            if i == cur: return
            if i%2 == cur%2:
                if i < cur: return
            elif cur > 1:
                i = cur-2
        
        if i > 1:
            self.manager.bonus_scores[0][i%2 + 1] += 1
        self.trail_changes.append((x,y,i))