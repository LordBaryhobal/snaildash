#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import json
import os

import pygame

from font_manager import FontManager

class GUI:
    """Class managing menus"""
    
    MENUS = ["main", "waiting", "credits", "breakdown", "tutorial", "nameinput"]
    
    def __init__(self):
        """Initializes a GUI instance"""
        
        self.menus = {}
        self._menu = self.MENUS[0]
        self.visible = True
        self.load_menus()

    def load_menus(self):
        """Loads all menu files"""
        
        for m in self.MENUS:
            with open(os.path.join("assets", "menus", f"{m}.json"), "r", encoding="utf-8") as f:
                self.menus[m] = Menu(json.load(f))

    def render(self, surf):
        """Renders the active menu

        Args:
            surf (pygame.Surface): window surface
        """
        
        if self.visible:
            self.get_menu().render(surf)
    
    def get_menu(self):
        """Gets the active menu

        Returns:
            Menu: active menu
        """
        return self.menus[self._menu]

    def set_menu(self, menu):
        """Sets the active menu

        Args:
            menu (str): new active menu name
        """
        self._menu = menu
    
    def on_mouse_down(self, event):
        """Handles a pygame.MOUSEBUTTONDOWN event

        Args:
            event (pygame.EVENT): the pygame event
        """
        if not self.visible: return
        if event.button == 1:
            self.get_menu().on_mouse_down(event)
    
    def on_mouse_up(self, event):
        """Handles a pygame.MOUSEBUTTONUP event

        Args:
            event (pygame.EVENT): the pygame event
        """
        if not self.visible: return
        if event.button == 1:
            self.get_menu().on_mouse_up(event)
            
    def on_key_down(self, event):
        if not self.visible: return
        self.get_menu().on_key_down(event)

class Menu:
    """Class representing a menu, composed of texts and buttons"""
    
    def __init__(self, data):
        """Initializes a Menu instance

        Args:
            data (list[dict]): list of components
        """
        
        self.width, self.height = 0, 0
        self.components = []
        for c in data:
            type_ = c["type"]
            
            if type_ == "button":
                cls = Button
            elif type_ == "text":
                cls = Text
            elif type_ == "input":
                cls = Input
            else:
                continue
            
            self.components.append(cls(self, **c))
    
    def render(self, surf):
        """Renders this menu

        Args:
            surf (pygame.Surface): window surface
        """
        
        self.width, self.height = surf.get_size()
        for c in self.components:
            c.render(surf)
    
    def on_mouse_down(self, event):
        """Handles a pygame.MOUSEBUTTONDOWN event

        Args:
            event (pygame.EVENT): the pygame event
        """
        
        for c in self.components:
            if not isinstance(c, Button): continue
            if not c.visible: continue
            x,y,w,h = c.rect
            if x <= event.pos[0] < x+w and y <= event.pos[1] < y+h:
                c.pressed = True
                break
    
    def on_mouse_up(self, event):
        """Handles a pygame.MOUSEBUTTONDOWN event

        Args:
            event (pygame.EVENT): the pygame event
        """
        
        for c in self.components:
            if not isinstance(c, Button): continue
            if not c.visible: continue
            x,y,w,h = c.rect
            if x <= event.pos[0] < x+w and y <= event.pos[1] < y+h:
                if c.pressed:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT+1, name=c.name))
                
                c.pressed = False
    def on_key_down(self, event):
        for c in self.components:
            if not isinstance(c, Input): continue
            if not c.visible: continue
            c.handle_event(event)
            

class Button:
    """Class representing a clickable button"""
    
    COLOR = (133, 255, 255)
    TXT_COLOR = (0, 0, 0)
    
    def __init__(self, menu, x, y, txt="", name="", width=1, margin=None, pos="relative", color=TXT_COLOR, bg=COLOR, **kwargs):
        """Initializes a Button instance

        Args:
            menu (Menu): parent menu
            x (float): x position factor
            y (float): y position factor
            txt (str, optional): displayed text. Defaults to "".
            name (str, optional): named passed when the button is clicked. Defaults to "".
            width (float, optional): width factor. Defaults to 1.
            margin (int, optional): if not None, margin in pixels and overrides width. Defaults to None.
            pos (str, optional): type of positioning. Either "relative" or "absolute". Defaults to "relative".
            color (tuple[int, int, int], optional): text color. Defaults to TXT_COLOR.
            bg (tuple[int, int, int], optional): background color. Defaults to COLOR.
        """
        
        self.menu = menu
        self.x = x
        self.y = y
        self.txt = txt
        self.name = name
        self.width = width
        self.margin = margin
        self.pos = pos
        self.rect = [0,0,0,0]
        self.pressed = False
        self.color = color
        self.bg = bg
        
        self.visible = True
    
    def render(self, surf):
        """Renders this button

        Args:
            surf (pygame.Surface): window surface
        """
        
        if not self.visible: return
        
        font = FontManager.get("arial", 30)
        txt = font.render(self.txt, True, self.color)
        
        width = self.menu.width*self.width
        height = txt.get_height()+20
        
        if self.margin is not None:
            width = txt.get_width()+2*self.margin
            height = txt.get_height()+self.margin
        
        if self.pos == "relative":
            x = self.menu.width*self.x - width/2
            y = self.menu.height*self.y - height/2
        
        elif self.pos == "absolute":
            x = self.x if self.x >= 0 else self.menu.width+self.x-width
            y = self.y if self.y >= 0 else self.menu.height+self.y-height
            
        else:
            return
        
        self.rect = [x, y, width, height]
        pygame.draw.rect(surf, self.bg, self.rect)
        surf.blit(txt, [x+width/2-txt.get_width()/2, y+height/2-txt.get_height()/2])

class Text:
    """Class representing a text element"""
    
    COLOR = (255, 255, 255)
    
    def __init__(self, menu, x, y, txt="", font_family="arial", size=30, align="center", bold=False, color=COLOR, **kwargs):
        """Initializes a Text instance

        Args:
            menu (Menu): parent menu
            x (float): x position factor
            y (float): y position facor
            txt (str, optional): text content. Defaults to "".
            font_family (str, optional): font family. Defaults to "arial".
            size (int, optional): font size. Defaults to 30.
            align (str, optional): text alignment. One of: "left", "center" or "right". Defaults to "center".
            bold (bool, optional): whether the text is bold. Defaults to False.
            color (tuple[int, int, int], optional): text color. Defaults to COLOR.
        """
        
        self.menu = menu
        self.x = x
        self.y = y
        self.txt = txt
        self.font = FontManager.get(font_family, size, bold=bold)
        self.align = align
        self.color = color
    
    def render(self, surf):
        """Renders this text

        Args:
            surf (pygame.Surface): window surface
        """
        
        txt = self.font.render(self.txt, True, self.color)
        x = self.menu.width*self.x
        y = self.menu.height*self.y
        y = y-txt.get_height()/2
        
        if self.align == "right":
            x -= txt.get_width()
        
        elif self.align == "center":
            x -= txt.get_width()/2
        
        surf.blit(txt, [x, y])


class Input:
    """Class representing an input element"""
    
    COLOR = (255, 255, 255)
    VALID = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    
    def __init__(self, menu, x, y, txt="", font_family="arial", size=30, align="center", color=COLOR, maxlen=10, width=0.3, height=0.1, **kwargs):
        """Initializes an Input instance

        Args:
            menu (Menu): parent menu
            x (float): x position factor
            y (float): y position facor
            txt (str, optional): text content. Defaults to "".
            font_family (str, optional): font family. Defaults to "arial".
            size (int, optional): font size. Defaults to 30.
            align (str, optional): text alignment. One of: "left", "center" or "right". Defaults to "center".
            bold (bool, optional): whether the text is bold. Defaults to False.
            color (tuple[int, int, int], optional): text color. Defaults to COLOR.
        """
        
        self.menu = menu
        self.x = x
        self.y = y
        self.txt = txt
        self.font = FontManager.get(font_family, size)
        self.align = align
        self.color = color
        self.maxlen = maxlen
        self.width = width
        self.height = height
        
        self.visible = True
    
    def render(self, surf):
        """Renders this text

        Args:
            surf (pygame.Surface): window surface
        """
        
        txt = self.font.render(self.txt, True, self.color)
        x = self.menu.width*self.x
        y = self.menu.height*self.y
        
        bx = x - self.width*self.menu.width/2
        by = y - self.height*self.menu.height/2
        
        
        y = y-txt.get_height()/2
        
        if self.align == "right":
            x -= txt.get_width()
        
        elif self.align == "center":
            x -= txt.get_width()/2
        
        pygame.draw.rect(surf, self.color, (bx, by, self.width*self.menu.width, self.height*self.menu.height), width = 2)
        surf.blit(txt, [x, y])
    
    def handle_event(self, event):
        if event.key == pygame.K_BACKSPACE:
                self.set_txt(self.txt[:-1])
            
        elif event.unicode in self.VALID:
            self.set_txt(self.txt + event.unicode)
    
    def set_txt(self, txt):
        if len(txt) > self.maxlen:
            txt = txt[:10]
        self.txt = txt
    
    