import os
import json

import pygame

from font_manager import FontManager

class GUI:
    MENUS = ["main", "waiting", "credits", "breakdown"]
    
    def __init__(self):
        self.menus = {}
        self._menu = self.MENUS[0]
        self.load_menus()

    def load_menus(self):
        for m in self.MENUS:
            with open(os.path.join("assets", "menus", f"{m}.json"), "r") as f:
                self.menus[m] = Menu(json.load(f))

    def render(self, surf):
        self.get_menu().render(surf)
    
    def get_menu(self):
        return self.menus[self._menu]

    def set_menu(self, menu):
        self._menu = menu
    
    def on_mouse_down(self, event):
        if event.button == 1:
            self.get_menu().on_mouse_down(event)
    
    def on_mouse_up(self, event):
        if event.button == 1:
            self.get_menu().on_mouse_up(event)

class Menu:
    def __init__(self, data):
        self.width, self.height = 0, 0
        self.components = []
        for c in data:
            type_ = c["type"]
            
            if type_ == "button":
                cls = Button
            elif type_ == "text":
                cls = Text
            else:
                continue
            
            self.components.append(cls(self, **c))
    
    def render(self, surf):
        self.width, self.height = surf.get_size()
        for c in self.components:
            c.render(surf)
    
    def on_mouse_down(self, event):
        for c in self.components:
            if not isinstance(c, Button): continue
            x,y,w,h = c.rect
            if x <= event.pos[0] < x+w and y <= event.pos[1] < y+h:
                c.pressed = True
                break
    
    def on_mouse_up(self, event):
        for c in self.components:
            if not isinstance(c, Button): continue
            x,y,w,h = c.rect
            if x <= event.pos[0] < x+w and y <= event.pos[1] < y+h:
                if c.pressed:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT+1, name=c.name))
                
                c.pressed = False

class Button:
    COLOR = (133, 255, 255)
    TXT_COLOR = (0, 0, 0)
    
    def __init__(self, menu, x, y, txt="", name="", width=1, color=TXT_COLOR, bg=COLOR, **kwargs):
        self.menu = menu
        self.x = x
        self.y = y
        self.txt = txt
        self.name = name
        self.width = width
        self.rect = [0,0,0,0]
        self.pressed = False
        self.color = color
        self.bg = bg
    
    def render(self, surf):
        x = self.menu.width*self.x
        y = self.menu.height*self.y
        width = self.menu.width*self.width
        font = FontManager.get("arial", 30)
        txt = font.render(self.txt, True, self.color)
        height = txt.get_height()+20
        self.rect = [x-width/2, y-height/2, width, height]
        pygame.draw.rect(surf, self.bg, self.rect)
        surf.blit(txt, [x-txt.get_width()/2, y-txt.get_height()/2])

class Text:
    COLOR = (255, 255, 255)
    
    def __init__(self, menu, x, y, txt="", font_family="arial", size=30, align="center", color=COLOR, **kwargs):
        self.menu = menu
        self.x = x
        self.y = y
        self.txt = txt
        self.font = FontManager.get(font_family, size)
        self.align = align
        self.color = color
    
    def render(self, surf):
        txt = self.font.render(self.txt, True, self.color)
        x = self.menu.width*self.x
        y = self.menu.height*self.y
        y = y-txt.get_height()/2
        
        if self.align == "right":
            x -= txt.get_width()
        
        elif self.align == "center":
            x -= txt.get_width()/2
        
        surf.blit(txt, [x, y])