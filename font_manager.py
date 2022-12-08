import pygame
class FontManager:
    cache = {}

    def get(font, size, bold=False, italic=False):
        id_ = (font, size, bold, italic)
        if not id_ in FontManager.cache:
            FontManager.cache[id_] = pygame.font.SysFont(font, size, bold=bold, italic=italic)
        
        return FontManager.cache[id_]