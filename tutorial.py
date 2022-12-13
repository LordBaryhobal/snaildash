#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import json
import os
import time

import pygame

from font_manager import FontManager

class Tutorial:
    """Class managing the tutorial section"""
    
    FPS = 2
    TPS = 1/FPS
    
    def __init__(self, manager):
        self.manager = manager
        self.slide = 0
        self.imgs = {}
        self.anims = {}
        self.load()
        self.start_time = 0

    def load(self):
        """Loads the tutorial slides"""
        
        with open(os.path.join("assets", "tutorials.json"), "r", encoding="utf-8") as f:
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
        """Renders the current slide

        Args:
            surf (pygame.Surface): window surface
        """
        
        W, H = surf.get_size()
        W2, H2 = W/2, H/2
        W6, H6 = W/6, H/6
        
        font_title = FontManager.get("arial", 50)
        font = FontManager.get("arial", 30)
        
        slide = self.slides[self.slide]
        title = font_title.render(slide["title"], True, (255,255,255))
        surf.blit(title, [W2-title.get_width()/2, H6/2-title.get_height()/2])
        
        has_prev = ( self.slide > 0 )
        has_next = ( self.slide < len(self.slides)-1 )
        self.manager.gui.get_menu().components[1].visible = has_prev
        self.manager.gui.get_menu().components[2].visible = has_next
        
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
                txt = font.render(l, True, (255,255,255))
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
    
    def prev_slide(self):
        """Goes to previous slide"""
        
        self.slide = max(0, self.slide-1)
        self.start_time = time.time()
    
    def next_slide(self):
        """Goes to next slide"""
        
        self.slide = min(len(self.slides)-1, self.slide+1)
        self.start_time = time.time()