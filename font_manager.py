#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import os

import pygame

class FontManager:
    cache = {}

    def get(font, size, bold=False, italic=False):
        id_ = (font, size, bold, italic)
        if not id_ in FontManager.cache:
            if font.startswith("file:"):
                path = os.path.join("assets", "fonts", font.split(":", 1)[1])
                FontManager.cache[id_] = pygame.font.Font(path, size)
            
            else:
                FontManager.cache[id_] = pygame.font.SysFont(font, size, bold=bold, italic=italic)
        
        return FontManager.cache[id_]