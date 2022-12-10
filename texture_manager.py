import os

import pygame

class TextureManager:
    cache = {}

    def get(path, width, height=None):
        if height is None:
            height = width
        
        if not (path, width, height) in TextureManager.cache:
            texture = pygame.image.load(os.path.join("assets", "textures", *path))
            TextureManager.cache[(path, width, height)] = pygame.transform.scale(texture, [width, height])
        
        return TextureManager.cache[(path, width, height)]