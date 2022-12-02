import json
import os
import pygame
import time

class Tutorial:
    FPS = 2
    TPS = 1/FPS
    
    def __init__(self, manager, Stage):
        self.manager = manager
        self.Stage = Stage
        self.slide = 0
        self.font_title = pygame.font.SysFont("arial", 50)
        self.font = pygame.font.SysFont("arial", 30)
        self.imgs = {}
        self.anims = {}
        self.load()
        self.start_time = 0
        
        self.main_menu_rect = [0,0,0,0]
        self.prev_rect = None
        self.next_rect = None
        
        self.main_menu_pressed = False
        self.prev_pressed = False
        self.next_pressed = False

    def load(self):
        with open(os.path.join("assets", "tutorials.json"), "r") as f:
            self.slides = json.load(f)
            for slide in self.slides:
                for section in slide["sections"]:
                    if "img" in section:
                        img = pygame.image.load(os.path.join("assets", "tutorial", section["img"]))
                        self.imgs[section["img"]] = img
                    
                    elif "anim" in section:
                        dir_ = os.path.join("assets", "tutorial", section["anim"])
                        imgs = []
                        for f in sorted(os.listdir(dir_)):
                            img = pygame.image.load(os.path.join("assets", "tutorial", section["anim"], f))
                            imgs.append(img)
                        self.anims[section["anim"]] = imgs
    
    def render(self, surf):
        W, H = surf.get_size()
        W2, H2 = W/2, H/2
        W6, H6 = W/6, H/6
        
        surf.fill(0)
        slide = self.slides[self.slide]
        title = self.font_title.render(slide["title"], True, (255,255,255))
        surf.blit(title, [W2-title.get_width()/2, H6/2-title.get_height()/2])
        
        menu = self.font.render("Menu principal", True, (0,0,0))
        self.main_menu_rect = [H6/2, H6/2-menu.get_height()/2-10, menu.get_width()+40, menu.get_height()+20]
        pygame.draw.rect(surf, (133,255,255), self.main_menu_rect)
        surf.blit(menu, [H6/2+20, H6/2-menu.get_height()/2])
        
        self.prev_rect = None
        self.next_rect = None
        
        if self.slide > 0:
            prev = self.font.render("Précédent", True, (0,0,0))
            self.prev_rect = [H6/2, H-H6/2-prev.get_height()/2-10, prev.get_width()+40, prev.get_height()+20]
            pygame.draw.rect(surf, (133,255,255), self.prev_rect)
            surf.blit(prev, [H6/2+20, H-H6/2-prev.get_height()/2])
        
        if self.slide < len(self.slides)-1:
            next_ = self.font.render("Suivant", True, (0,0,0))
            self.next_rect = [W-H6/2-next_.get_width()-40, H-H6/2-next_.get_height()/2-10, next_.get_width()+40, next_.get_height()+20]
            pygame.draw.rect(surf, (133,255,255), self.next_rect)
            surf.blit(next_, [W-H6/2-next_.get_width()-20, H-H6/2-next_.get_height()/2])
        
        section_h = H6*4/len(slide["sections"])
        
        for s, section in enumerate(slide["sections"]):
            oy = s*section_h + H6
            img = None
            
            if "img" in section:
                img = self.imgs[section["img"]]
            elif "anim" in section:
                anim = self.anims[section["anim"]]
                frame = int( (time.time()-self.start_time)/self.TPS )
                frame %= len(anim)
                img = anim[frame]
            
            lines = []
            max_w = 0
            for l in section["text"]:
                txt = self.font.render(l, True, (255,255,255))
                lines.append(txt)
                max_w = max(max_w, txt.get_width())
            
            ox = W/2-max_w/2
            if img:
                align_img = section["align_img"]
                img_ox = W-W6-img.get_width()
                ox = img_ox - 20 - max_w
                
                if align_img == "left":
                    img_ox = W6
                    ox = img_ox + img.get_width() + 20
                
                elif align_img == "center":
                    img_ox = W/2-img.get_width()/2
                
                surf.blit(img, [img_ox, oy+section_h/2-img.get_height()/2])
            
            if lines:
                txt_h = (len(lines)-1)*10 + sum([l.get_height() for l in lines])
                y = oy+section_h/2-txt_h/2
                for line in lines:
                    surf.blit(line, [ox, y])
                    y += line.get_height()+10
        
    def mouse_down(self, x, y):
        r1, r2 ,r3 = self.main_menu_rect, self.prev_rect, self.next_rect
        
        if r1[0] <= x < r1[0]+r1[2] and r1[1] <= y < r1[1]+r1[3]:
            self.main_menu_pressed = True
        
        elif r2 and r2[0] <= x < r2[0]+r2[2] and r2[1] <= y < r2[1]+r2[3]:
            self.prev_pressed = True
        
        elif r3 and r3[0] <= x < r3[0]+r3[2] and r3[1] <= y < r3[1]+r3[3]:
            self.next_pressed = True
        
    def mouse_up(self, x, y):
        r1, r2 ,r3 = self.main_menu_rect, self.prev_rect, self.next_rect
        clicked = False
        
        if r1[0] <= x < r1[0]+r1[2] and r1[1] <= y < r1[1]+r1[3]:
            if self.main_menu_pressed:
                clicked = True
                self.main_menu_pressed = False
                self.manager.stage = self.Stage.MAIN_MENU
        
        elif r2 and r2[0] <= x < r2[0]+r2[2] and r2[1] <= y < r2[1]+r2[3]:
            if self.prev_pressed:
                clicked = True
                self.prev_pressed = False
                self.slide = max(0, self.slide-1)
                self.start_time = time.time()
        
        elif r3 and r3[0] <= x < r3[0]+r3[2] and r3[1] <= y < r3[1]+r3[3]:
            if self.next_pressed:
                clicked = True
                self.next_pressed = False
                self.slide = min(len(self.slides)-1, self.slide+1)
                self.start_time = time.time()
        
        if clicked:
            self.manager.click_sound.play()