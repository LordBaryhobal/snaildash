import numpy as np
import pygame
import time

from player import Player

class Game:
    WIDTH = 10
    HEIGHT = 10
    TIMER = 0.25
    DURATION = 120

    def __init__(self, manager):
        self.manager = manager
        self.trails = np.zeros([self.HEIGHT, self.WIDTH], dtype="int8")-1
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.font = pygame.font.SysFont("arial", 30)
        self.player = self.players[0]
        self.timer_start = 0
        self.start_time = 0
        self.trail_changes = []
        self.remaining = self.TIMER

    def loop(self):
        self.remaining = self.timer_start+self.TIMER - time.time()
        
        if self.remaining <= 0:
            if not self.player.synced:
                if not self.manager.is_host:
                    self.player.synced = True
                    self.end_turn()
    
    def render(self, surf):
        #self.ts = min(surf.get_width()/self.WIDTH, surf.get_height()/self.HEIGHT)
        w3, h3 = surf.get_width()/3, surf.get_height()/3
        
        tw = 2*w3/self.WIDTH
        th = 2*h3/self.HEIGHT
        self.ts = min(tw, th)
        surf.fill(0)
        
        ox, oy = surf.get_width()/2 - self.WIDTH/2*self.ts, surf.get_height()/2 - self.HEIGHT/2*self.ts

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                t = self.trails[y, x]
                if t != -1:
                    col = Player.TRAIL_COLORS[t]

                    pygame.draw.circle(surf, col, [ox+(x+0.5)*self.ts, oy+(y+0.5)*self.ts], self.ts/4)
        
        r = 1-max(0,self.remaining)/self.TIMER
        r = max(0, min(1, r))
        for player in self.players:
            x, y = player.x, player.y
            lx, ly = player.lx, player.ly
            X, Y = lx+(x-lx)*r, ly+(y-ly)*r
            
            pygame.draw.circle(surf, Player.COLORS[player.i], [ox+(X+0.5)*self.ts, oy+(Y+0.5)*self.ts], self.ts/2)
            if player.stun_count != 0:
                pygame.draw.line(surf, (0,255,0), [ox+X*self.ts, oy+Y*self.ts], [ox+(X+1)*self.ts, oy+(Y+1)*self.ts])
                pygame.draw.line(surf, (0,255,0), [ox+X*self.ts, oy+(Y+1)*self.ts], [ox+(X+1)*self.ts, oy+Y*self.ts])


        """txt = self.font.render(f"{max(0,self.remaining):.2f}", True, (255,255,255))
        surf.blit(txt, [0, 0])"""
        
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
        
        pygame.draw.polygon(surf, (180,180,180), [a,b,c,d])
        pygame.draw.polygon(surf, Player.COLORS[0], [a,red_e,red_f,d])
        pygame.draw.polygon(surf, Player.COLORS[1], [blue_e,b,c,blue_f])
        
        #pygame.draw.rect(surf, (180,180,180), [w6, h24, W, h24*2])
        #pygame.draw.rect(surf, Player.COLORS[0], [w6, h24, redW, h24*2])
        #pygame.draw.rect(surf, Player.COLORS[1], [w6+W-blueW, h24, blueW, h24*2])
        
        rem = self.collide_start+self.COLLIDE_DURATION-cur_time
        if rem > 0:
            r = 1-rem/self.COLLIDE_DURATION
            r = self.COLLIDE_RADIUS*r*self.ts
            pygame.draw.circle(surf, (255,255,255), [ox+(self.collide_pos[0]+0.5)*self.ts, oy+(self.collide_pos[1]+0.5)*self.ts], r, 3)
    
    def handle_key(self, event):
        if event.key == pygame.K_w:
            self.player.dir = 3
        
        elif event.key == pygame.K_s:
            self.player.dir = 1
        
        elif event.key == pygame.K_a:
            self.player.dir = 2
        
        elif event.key == pygame.K_d:
            self.player.dir = 0
    
    def start_turn(self):
        self.timer_start = time.time()
        self.player.synced = False
        self.trail_changes = []
    
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
                    player.lx, player.ly = x, y
                    player.x, player.y = x2, y2
                    
                    self.trail_changes.append((x, y, player.i))

            for x, y, i in self.trail_changes:
                self.trails[y, x] = i
        
            self.send_sync()
            self.start_turn()
            
        else:
            self.send_sync()
    
    def sync(self, x1, y1, d1, s1, x2, y2, d2, s2, trails=None):
        if self.player.i == 1 or not self.manager.is_host:
            self.players[0].lx = self.players[0].x
            self.players[0].ly = self.players[0].y
            self.players[0].x = x1
            self.players[0].y = y1
            self.players[0].dir = d1
            self.players[0].stun_count = s1
        
        if self.player.i == 0 or not self.manager.is_host:
            self.players[1].lx = self.players[1].x
            self.players[1].ly = self.players[1].y
            self.players[1].x = x2
            self.players[1].y = y2
            self.players[1].dir = d2
            self.players[1].stun_count = s2
        
        if trails:
            for x, y, i in trails:
                self.trails[y, x] = i
                
    def send_sync(self):
        x1 = self.players[0].x
        y1 = self.players[0].y
        d1 = self.players[0].dir
        s1 = int(self.players[0].stun_count)
        x2 = self.players[1].x
        y2 = self.players[1].y
        d2 = self.players[1].dir
        s2 = int(self.players[1].stun_count)
        
        if self.manager.is_host:
            trails = []
            for x, y, i in self.trail_changes:
                trails.append(f"{x}|{y}|{i}")
            
            trails = "/".join(trails)
            msg = f"turnEndHost,{x1},{y1},{d1},{s1},{x2},{y2},{d2},{s2},{trails}"
            
        else:
            msg = f"turnEnd,{x1},{y1},{d1},{s1},{x2},{y2},{d2},{s2}"
        
        self.manager.sh.send(msg.encode("utf-8"))