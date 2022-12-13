#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import os

import pygame

class SoundManager:
    """Manages fonts using a cache"""
    
    cache = {}
    
    def get(path):
        """Loads a sound or get it from the cache

        Args:
            path (str): path to the sound file relative to assets/sounds/

        Returns:
            pygame.mixer.Sound: the corresponding sound
        """
        
        path = os.path.join("assets", "sounds", *path)
        if not path in SoundManager.cache:
            SoundManager.cache[path] = pygame.mixer.Sound(path)
        
        return SoundManager.cache[path]