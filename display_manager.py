#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

from math import radians, sin, cos, pi
import random
import time

import pygame

from font_manager import FontManager
from player import Player
from stage import Stage
from texture_manager import TextureManager

class DisplayManager:
    """Manages the rendering of the game and menus"""

    CD_COLOR = (133, 255, 255)
    PCT_COLOR = (255, 255, 255)
    END_STMT_COLOR = (255, 255, 255)
    BONUS_SCORE_COLOR = (255, 255, 255)
    
    def __init__(self, manager):
        """Initializes a DisplayManager instance

        Args:
            manager (Manager): Manager instance
        """
        
        self.manager = manager
        self.player_i = self.manager.game.player.i
        self.ts = 1
        self.gen_stars()
    
    def gen_stars(self):
        """Generates the stars shown in the main menu and in the game's background"""

        self.main_menu_stars = [
            [random.randint(0, self.manager.WIDTH), random.randint(-40, 40), random.random()]
            for i in range(20)
        ]
        
        self.stars = []
        a = radians(random.randint(0,359))
        self.star_vx = cos(a)*0.005
        self.star_vy = sin(a)*0.005
        for i in range(200):
            x, y = random.random(), random.random()
            f = random.random()/2+0.5
            self.stars.append([x,y,f])
    
    def resize(self):
        """Reloads and resizes textures according to the new tile size"""

        self.drool_textures = []
        for i in range(16):
            normal = TextureManager.get(("drool", f"{i}.png"), self.ts*2)
            reinforced = TextureManager.get(("drool_reinforced", f"{i}.png"), self.ts*2)
            red, blue = normal.copy(), normal.copy()
            redr, bluer = reinforced.copy(), reinforced.copy()
            red.fill(Player.TRAIL_COLORS[0]+(255,), None, pygame.BLEND_RGBA_MULT)
            blue.fill(Player.TRAIL_COLORS[1]+(255,), None, pygame.BLEND_RGBA_MULT)
            redr.fill(Player.TRAIL_COLORS[0]+(255,), None, pygame.BLEND_RGBA_MULT)
            bluer.fill(Player.TRAIL_COLORS[1]+(255,), None, pygame.BLEND_RGBA_MULT)
            self.drool_textures.append((red, blue, redr, bluer))
        
        self.snail = []
        for i in range(5):
            red = TextureManager.get(("snail", "red", f"{i}.png"), self.ts*2)
            blue = TextureManager.get(("snail", "blue", f"{i}.png"), self.ts*2)
            self.snail.append((red, blue))
            
        self.bonus_textures = []
        for cls in self.manager.game.bonus_list:
            texture = TextureManager.get(("bonus", cls.TEXTURE), self.ts*2)
            self.bonus_textures.append(texture)
        
        self.dashscore_textures = []
        for i in range(5):
            texture = TextureManager.get(("dash_score_bar", f"{i}.png"), self.ts*2, self.ts*8)
            texture = texture.copy()
            texture.fill(Player.COLORS[self.manager.game.player.i]+(255,), None, pygame.BLEND_RGBA_MULT)
            self.dashscore_textures.append(texture)
    
    def render(self, surf):
        """Main render method. Calls dedicated methods for the different parts

        Args:
            surf (pygame.Surface): window surface
        """

        mgr = self.manager
        stage = mgr.stage
        
        w3, h3 = surf.get_width()/3, surf.get_height()/3
        
        tw = 2*w3/mgr.game.WIDTH
        th = 2*h3/mgr.game.HEIGHT
        ts = min(tw, th)
        if self.ts != ts:
            self.ts = ts
            self.resize()
        
        elif self.player_i != self.manager.game.player.i:
            self.player_i = self.manager.game.player.i
            self.resize()
        
        surf.fill(0)
        
        if stage in [Stage.MAIN_MENU, Stage.WAITING_OPPONENT, Stage.CREDITS, Stage.TUTORIAL, Stage.BREAKDOWN_BONUSES, Stage.NAMEINPUT]:
            mgr.gui.render(surf)
            if stage == Stage.MAIN_MENU:
                self.render_main_menu(surf)
        
        if stage == Stage.COUNTDOWN:
            self.render_game(surf)
            
            r = max(0, mgr.countdown_start+mgr.COUNTDOWN_DUR - time.time())
            rem_sec = round(r)
            rem_sec = "Go" if rem_sec == 0 else str(rem_sec)
            font = FontManager.get("arial", 50, True, True)
            txt = font.render(rem_sec, True, self.CD_COLOR)
            y0 = surf.get_height()/2-txt.get_height()/2
            y1 = -txt.get_height()
            
            # Animation
            r = 1 - (r - round(r))
            r = max(0, 2.5*(r-0.6))
            r = r**2
            y = r*(y1-y0)+y0

            surf.blit(txt, [surf.get_width()/2-txt.get_width()/2, y])
        
        elif stage == Stage.IN_GAME:
            self.render_game(surf)
        
        elif stage == Stage.GAME_TO_BREAKDOWN:
            self.render_breakdown_transition(surf)
        
        elif stage == Stage.BREAKDOWN_BAR:
            self.render_breakdown_bar(surf)
        
        elif stage == Stage.BREAKDOWN_BONUSES:
            self.render_breakdown_bonuses(surf)
        
        elif stage == Stage.TUTORIAL:
            mgr.tutorial.render(surf)
    
    def render_main_menu(self, surf):
        """Renders the main menu

        Args:
            surf (pygame.Surface): window surface
        """

        oy = 0.25*surf.get_height()
        for i, [x, y, v] in enumerate(self.main_menu_stars):
            pygame.draw.ellipse(surf, (150,150,150), [
                x-15,
                oy+y-2,
                30,
                4
            ])
            x -= v*20 + 15
            x %= surf.get_width()
            self.main_menu_stars[i][0] = x
        
        t = time.time()-self.manager.startup_time
        r = (t/8)%1
        f = (t/0.5)%1
        f = 4 - abs(f-0.5)*8
        snail = self.snail[int(f)][self.manager.game.player.i]
        snail = pygame.transform.rotate(snail, -90)
        w = surf.get_width()
        x = r*w
        dy = sin(10*pi*r)*20
        surf.blit(snail, [x, oy+dy-snail.get_height()/2])
        surf.blit(snail, [x-w, oy+dy-snail.get_height()/2])

    def render_game(self, surf, render_players=True):
        """Renders the game

        Args:
            surf (pygame.Surface): window surface
            render_players (bool, optional): Whether the player should be rendered. Defaults to True.
        """
        
        cur_time = self.manager.time()
        game = self.manager.game
        
        ox, oy = surf.get_width()/2 - game.WIDTH/2*self.ts, surf.get_height()/2 - game.HEIGHT/2*self.ts

        # Stars
        for i, [x, y, f] in enumerate(self.stars):
            col = int(200*f)
            pygame.draw.circle(surf, (col, col, col), [x*surf.get_width(), y*surf.get_height()], f*4)
            x, y = x+self.star_vx*f, y+self.star_vy*f
            x %= 1
            y %= 1
            self.stars[i] = [x, y, f]

        # Black bg
        pygame.draw.rect(surf, (0,0,0), [ox, oy, game.WIDTH*self.ts, game.HEIGHT*self.ts])
        
        # Grid
        for y in range(game.HEIGHT+1):
            pygame.draw.line(surf, (150,150,150), [ox, oy+y*self.ts], [ox+game.WIDTH*self.ts, oy+y*self.ts])
        
        for x in range(game.WIDTH+1):
            pygame.draw.line(surf, (150,150,150), [ox+x*self.ts, oy], [ox+x*self.ts, oy+game.HEIGHT*self.ts])

        # Drool
        for y in range(game.HEIGHT):
            for x in range(game.WIDTH):
                t = game.trails[y, x]
                if t != -1:
                    drool_i = game.drool[y, x]
                    texture = self.drool_textures[drool_i][t]
                    
                    surf.blit(texture, [ox+(x-0.5)*self.ts, oy+(y-0.5)*self.ts])
        
        # Bonus
        bonus_l = game.bonus_dict.copy()
        for (x, y), i in bonus_l.items():
            surf.blit(self.bonus_textures[i], [ox + (x-0.5)*self.ts, oy + (y-0.5)*self.ts])
        
        # Players
        r = 1-max(0,game.remaining)/game.TIMER
        r = max(0, min(1, r))
        
        if render_players:
            for player in game.players:
                x, y = player.x, player.y
                lx, ly = player.lx, player.ly
                X, Y = lx+(x-lx)*r, ly+(y-ly)*r

                _ = 4 - abs(r-0.5)*8
                texture = self.snail[int(_)][player.i]
                if player.dir % 4 != 3:
                    texture = pygame.transform.rotate(texture, -((player.dir+1)%4)*90)
                surf.blit(texture, [ox+(X-0.5)*self.ts, oy+(Y-0.5)*self.ts])
        
        # Time bar
        remaining = game.start_time+game.DURATION - cur_time
        if game.start_time == 0: remaining = game.DURATION
        w3 = surf.get_width()/3
        w6 = w3/2
        W = 2*w3
        w = W * max(0, min(1, remaining/game.DURATION))
        pygame.draw.rect(surf, (255,255,255), [w6, surf.get_height()-10, w, 10])
        
        # Collision shockwave
        if game.collide_start != 0:
            rem = game.collide_start+game.COLLIDE_DURATION-cur_time
            if rem > 0:
                r = 1-rem/game.COLLIDE_DURATION
                r = game.COLLIDE_RADIUS*r*self.ts
                pygame.draw.circle(surf, (255,255,255), [ox+(game.collide_pos[0]+0.5)*self.ts, oy+(game.collide_pos[1]+0.5)*self.ts], r, 3)
        
        # Dash bar
        ds_texture = self.dashscore_textures[min(Player.MAX_DASHSCORE, game.player.dashscore)]
        surf.blit(ds_texture, [ox-ds_texture.get_width()-self.ts, surf.get_height()/2-ds_texture.get_height()/2])
    
    def render_breakdown_transition(self, surf):
        """Renders the transition between the game and breakdown phase

        Args:
            surf (pygame.Surface): window surface
        """
        
        self.render_game(surf, False)
        mgr = self.manager
        game = mgr.game
        
        # Fade to black
        fade = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        t = mgr.time()
        r = mgr.game_to_breakdown_start+mgr.BREAKDOWN_IN_DUR-t
        r = 1-r/mgr.BREAKDOWN_IN_DUR
        r = max(0, min(1, r))
        fade.fill((0, 0, 0, int(r*255)))
        surf.blit(fade, [0,0])
        
        # Players animation
        ox, oy = surf.get_width()/2 - game.WIDTH/2*self.ts, surf.get_height()/2 - game.HEIGHT/2*self.ts
        p1, p2 = game.players
        p1Ps = [ox + (p1.x+0.5)*self.ts, oy + (p1.y+0.5)*self.ts]
        p2Ps = [ox + (p2.x+0.5)*self.ts, oy + (p2.y+0.5)*self.ts]
        p1Pe, p2Pe = [ox, oy], [ox + game.WIDTH*self.ts, oy]
        
        p1P = [
            (p1Pe[0]-p1Ps[0])*r + p1Ps[0],
            (p1Pe[1]-p1Ps[1])*r + p1Ps[1]
        ]
        p2P = [
            (p2Pe[0]-p2Ps[0])*r + p2Ps[0],
            (p2Pe[1]-p2Ps[1])*r + p2Ps[1]
        ]
        
        red = self.snail[0][0]
        blue = self.snail[0][1]
        a_red = -((p1.dir+1)%4)*90
        a_blue = -((p2.dir+1)%4)*90
        red = pygame.transform.rotate(red, a_red-a_red*r)
        blue = pygame.transform.rotate(blue, a_blue-a_blue*r)
        
        surf.blit(red, [p1P[0]-red.get_width()/2, p1P[1]-red.get_height()/2])
        surf.blit(blue, [p2P[0]-blue.get_width()/2, p2P[1]-blue.get_height()/2])
    
    def render_breakdown_bar(self, surf):
        """Renders the breakdown bar filling

        Args:
            surf (pygame.Surface): window surface
        """
        
        mgr = self.manager
        game = mgr.game
        t = mgr.time()
        
        bar_fill_dur = mgr.BREAKDOWN_BAR_DUR-mgr.BREAKDOWN_BAR_PAUSE-mgr.BREAKDOWN_BAR_END_DUR
        bar_end_dur = mgr.BREAKDOWN_BAR_END_DUR
        start = mgr.breakdown_bar_start
        
        r_bar = start + bar_fill_dur - t
        r_end = start + mgr.BREAKDOWN_BAR_DUR - t
        r_bar = 1-r_bar/(bar_fill_dur)
        r_end = 1-r_end/bar_end_dur
        r_bar = max(0, min(1, r_bar))
        
        red, blue = game.get_trail_count()
        full = game.WIDTH * game.HEIGHT
        pct_red = red/full*100
        pct_blue = blue/full*100
        
        ox, oy = surf.get_width()/2 - game.WIDTH/2*self.ts, surf.get_height()/2 - game.HEIGHT/2*self.ts
        p1, p2 = [ox, oy], [ox + game.WIDTH*self.ts, oy]
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        width = p2[0] - p1[0] - 2*self.ts - 40
        bar_h = self.ts
        ox, oy = mx-width/2, my-bar_h/2
        
        pct_red, pct_blue = r_bar*pct_red, r_bar*pct_blue
        r_red, r_blue = r_bar*red/full, r_bar*blue/full
        pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width*r_red, bar_h])
        pygame.draw.rect(surf, Player.COLORS[1], [ox+width-width*r_blue, oy, width*r_blue, bar_h])
        
        red_snail = self.snail[0][0]
        blue_snail = self.snail[0][1]
        
        surf.blit(red_snail, [p1[0]-red_snail.get_width()/2, p1[1]-red_snail.get_height()/2])
        surf.blit(blue_snail, [p2[0]-blue_snail.get_width()/2, p2[1]-blue_snail.get_height()/2])
        
        font = FontManager.get("arial", 20)
        pct_red = font.render(f"{pct_red:.1f}%", True, self.PCT_COLOR)
        pct_blue = font.render(f"{pct_blue:.1f}%", True, self.PCT_COLOR)
        
        surf.blit(pct_red,  [p1[0] - pct_red.get_width()/2,  p1[1] - pct_red.get_height()/2 ])
        surf.blit(pct_blue, [p2[0] - pct_blue.get_width()/2, p2[1] - pct_blue.get_height()/2])
        
        if r_end >= 0:
            r_end = min(1, r_end)**2  # end fills exponentially
            
            # If red won -> red fills the whole bar
            if red > blue:
                w = width*red/full
                w = (width-w)*r_end + w
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-width*blue/full, oy, width*blue/full, bar_h])
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, w, bar_h])
            
            # If blue won -> blue fills the whole bar
            elif blue > red:
                w = width*blue/full
                w = (width-w)*r_end + w
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width*red/full, bar_h])
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-w, oy, w, bar_h])
            
            # Else (tie) -> both fill to the middle
            else:
                w_red = width*red/full
                w_red = (width/2-w_red)*r_end + w_red
                w_blue = width*blue/full
                w_blue = (width/2-w_blue)*r_end + w_blue
                pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, w_red, bar_h])
                pygame.draw.rect(surf, Player.COLORS[1], [ox+width-w_blue, oy, w_blue, bar_h])
    
    def render_breakdown_bonuses(self, surf):
        """Renders the breakdown of bonus scores

        Args:
            surf (pygame.Surface): window surface
        """
        
        mgr = self.manager
        game = mgr.game
        
        red, blue = game.get_trail_count()
        full = game.WIDTH * game.HEIGHT
        pct_red = red/full*100
        pct_blue = blue/full*100
        
        ox, oy = surf.get_width()/2 - game.WIDTH/2*self.ts, surf.get_height()/2 - game.HEIGHT/2*self.ts
        p1, p2 = [ox, oy], [ox + game.WIDTH*self.ts, oy]
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        width = p2[0] - p1[0] - 2*self.ts - 40
        bar_h = self.ts
        ox, oy = mx-width/2, my-bar_h/2
        
        # Players
        red_snail = self.snail[0][0]
        blue_snail = self.snail[0][1]
        
        surf.blit(red_snail, [p1[0]-red_snail.get_width()/2, p1[1]-red_snail.get_height()/2])
        surf.blit(blue_snail, [p2[0]-blue_snail.get_width()/2, p2[1]-blue_snail.get_height()/2])
        
        # Percentages
        font = FontManager.get("arial", 20)
        pct_red = font.render(f"{pct_red:.1f}%", True, self.PCT_COLOR)
        pct_blue = font.render(f"{pct_blue:.1f}%", True, self.PCT_COLOR)
        
        surf.blit(pct_red,  [p1[0] - pct_red.get_width()/2,  p1[1] - pct_red.get_height()/2 ])
        surf.blit(pct_blue, [p2[0] - pct_blue.get_width()/2, p2[1] - pct_blue.get_height()/2])
        
        # End statement (won / lost / tie)
        if red > blue:
            pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width, bar_h])
            txt = "Vous avez "+["gagné", "perdu"][game.player.i]
        
        elif blue > red:
            pygame.draw.rect(surf, Player.COLORS[1], [ox, oy, width, bar_h])
            txt = "Vous avez "+["perdu", "gagné"][game.player.i]
        
        else:
            pygame.draw.rect(surf, Player.COLORS[0], [ox, oy, width/2, bar_h])
            pygame.draw.rect(surf, Player.COLORS[1], [ox+width/2, oy, width/2, bar_h])
            txt = "Vous êtes à égalité"
        
        font = FontManager.get("arial", 30)
        txt = font.render(txt, True, self.END_STMT_COLOR)
        surf.blit(txt, [
            ox + width/2 - txt.get_width()/2,
            oy + bar_h/2 - txt.get_height()/2
        ])
        
        # Bonus scores
        bonus_scores = mgr.get_bonus_scores()
        cur = mgr.time()
        step = int( (cur-mgr.breakdown_start)//mgr.BREAKDOWN_INTERVAL )
        x1, x2 = p1[0], p2[0]
        xm = (x1+x2)/2
        
        ys = p1[1]+100
        ye = surf.get_height()*6/7
        h = (ye-ys)/len(bonus_scores)
        
        font = FontManager.get("arial", 30)
        for i in range(min(step, len(bonus_scores))):
            name, red, blue = bonus_scores[i]
            y = ys + i*h + h/2
            txtName = font.render(name, True, self.BONUS_SCORE_COLOR)
            txtRed = font.render(str(red), True, self.BONUS_SCORE_COLOR)
            txtBlue = font.render(str(blue), True, self.BONUS_SCORE_COLOR)
            surf.blit(txtRed,  [x1 - txtRed.get_width()/2,  y - txtRed.get_height()/2 ])
            surf.blit(txtBlue, [x2 - txtBlue.get_width()/2, y - txtBlue.get_height()/2])
            surf.blit(txtName, [xm - txtName.get_width()/2, y - txtName.get_height()/2])
            
            if red >= blue:
                pygame.draw.circle(surf, Player.COLORS[0], [x1, y], (x2-x1)/16, 2)
            
            if blue >= red:
                pygame.draw.circle(surf, Player.COLORS[1], [x2, y], (x2-x1)/16, 2)

        if step > len(bonus_scores) and not mgr.gui.visible:
            mgr.gui.set_menu("breakdown")
            mgr.gui.visible = True