#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import os

import pygame

class SoundManager:
    cache = {}
    
    def get(path):
        path = os.path.join("assets", "sounds", *path)
        if not path in SoundManager.cache:
            SoundManager.cache[path] = pygame.mixer.Sound(path)
        
        return SoundManager.cache[path]