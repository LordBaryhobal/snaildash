import os

import pygame

class SoundManager:
    cache = {}
    
    def get(path):
        path = os.path.join("assets", "sounds", *path)
        if not path in SoundManager.cache:
            SoundManager.cache[path] = pygame.mixer.Sound(path)
        
        return SoundManager.cache[path]