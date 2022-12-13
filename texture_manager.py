#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import os

import pygame

class TextureManager:
    """Manages textures using a cache"""
    
    cache = {}

    def get(path, width, height=None):
        """Loads a texture or get it from the cache

        Args:
            path (str): path to the texture file relative to assets/textures/
            width (int): width to which the image is resized
            hight (bool, optional): height to which the image is resized, if None, same as width. Defaults to None.

        Returns:
            pygame.Surface: the corresponding surface
        """
        
        if height is None:
            height = width
        
        if not (path, width, height) in TextureManager.cache:
            texture = pygame.image.load(os.path.join("assets", "textures", *path))
            TextureManager.cache[(path, width, height)] = pygame.transform.scale(texture, [width, height])
        
        return TextureManager.cache[(path, width, height)]