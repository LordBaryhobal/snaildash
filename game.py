import numpy as np
import pygame
import time

from player import Player

class Game:
    WIDTH = 20
    HEIGHT = 20
    TIMER = 1.5
    DURATION = 120

    def __init__(self, manager):
        self.manager = manager
        self.trails = np.zeros([self.HEIGHT, self.WIDTH], dtype="int8")-1
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
        self.turn = 0
        self.font = pygame.font.SysFont("arial", 30)
        self.player = self.players[0]
        self.timer_start = 0
        self.start_time = 0
        self.moved = False
    
    def cur_player(self):
        return self.players[self.turn]

    def loop(self):
        self.remaining = self.timer_start+self.TIMER - time.time()
        
        if self.remaining <= 0:
            self.end_turn()
    
    def render(self, surf):
        self.ts = min(surf.get_width()/self.WIDTH, surf.get_height()/self.HEIGHT)
        surf.fill(0)

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                t = self.trails[y, x]
                if t != -1:
                    col = Player.TRAIL_COLORS[t]

                    pygame.draw.circle(surf, col, [(x+0.5)*self.ts, (y+0.5)*self.ts], self.ts/4)
        
        for player in self.players:
            pygame.draw.circle(surf, Player.COLORS[player.i], [(player.x+0.5)*self.ts, (player.y+0.5)*self.ts], self.ts/2)
            if player.stunned:
                pygame.draw.line(surf, (0,255,0), [player.x*self.ts, player.y*self.ts], [(player.x+1)*self.ts, (player.y+1)*self.ts])
                pygame.draw.line(surf, (0,255,0), [player.x*self.ts, (player.y+1)*self.ts], [(player.x+1)*self.ts, player.y*self.ts])


        col = (255,255,255) if self.player.i == self.turn else (150,150,150)
        txt = self.font.render(f"{max(0,self.remaining):.2f}", True, col)
        x = 0 if self.player.i == self.turn else surf.get_width()-txt.get_width()
        surf.blit(txt, [x, 0])
        
        remaining = self.start_time+self.DURATION - time.time()
        W = surf.get_width()
        w = W*remaining/self.DURATION
        pygame.draw.rect(surf, (255,255,255), [0, surf.get_height()-10, w, 10])
        
        red = np.count_nonzero(self.trails == 0)
        blue = np.count_nonzero(self.trails == 1)
        full = self.WIDTH * self.HEIGHT
        redW = W*red/full
        blueW = W*blue/full
        pygame.draw.rect(surf, (180,180,180), [0, 0, W, 10])
        pygame.draw.rect(surf, Player.COLORS[0], [0, 0, redW, 10])
        pygame.draw.rect(surf, Player.COLORS[1], [W-blueW, 0, blueW, 10])
    
    def handle_key(self, event):
        if self.turn == self.player.i and not self.player.stunned:
            x, y = self.player.x, self.player.y
            if event.key == pygame.K_w:
                if y > 0:
                    self.player.move(0, -1)
            
            elif event.key == pygame.K_s:
                if y < self.HEIGHT-1:
                    self.player.move(0, 1)
            
            elif event.key == pygame.K_a:
                if x > 0:
                    self.player.move(-1, 0)
            
            elif event.key == pygame.K_d:
                if x < self.WIDTH-1:
                    self.player.move(1, 0)
    
    def start_turn(self):
        self.timer_start = time.time()
        self.moved = False
        
        #if self.player.i == self.turn:
        cur = self.cur_player()
        if cur.stunned:
            if time.time() >= cur.stun_start+Player.STUN_TIMER:
                cur.stunned = False
                cur.stun_start = 0
            elif cur is self.player:
                self.end_turn()
    
    def end_turn(self):
        if self.player.i == self.turn:
            if not self.moved and not self.player.stunned:
                self.player.stunned = True
                self.player.stun_start = time.time()
            
            if self.trails[self.player.y, self.player.x] == 1-self.player.i:
                self.player.hurt()
            
            self.send_sync()
        
        self.turn = 1-self.turn
        
        self.start_turn()
    
    def sync(self, x1, y1, x2, y2, s1, s2, s1s, s2s, trails):
        self.players[0].x = x1
        self.players[0].y = y1
        self.players[1].x = x2
        self.players[1].y = y2
        self.players[0].stunned = s1
        self.players[1].stunned = s2
        self.players[0].stun_start = s1s
        self.players[1].stun_start = s2s
        
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                c = int(trails[x+y*self.WIDTH])
                if c == 2: c = -1
                self.trails[y, x] = c
                
    def send_sync(self):
        x1 = self.players[0].x
        y1 = self.players[0].y
        x2 = self.players[1].x
        y2 = self.players[1].y
        s1 = int(self.players[0].stunned)
        s2 = int(self.players[1].stunned)
        s1s = self.players[0].stun_start
        s2s = self.players[1].stun_start
        
        trails = ""
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                c = self.trails[y, x]
                if c == -1: c = 2
                trails += str(c)
        
        msg = f"turnEnd,{x1},{y1},{x2},{y2},{s1},{s2},{s1s},{s2s},{trails}"
        self.manager.sh.send(msg.encode("utf-8"))