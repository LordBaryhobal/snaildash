#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

from math import floor, ceil
from random import randint, random

class Bonus:
    """Static superclass for bonuses"""
    
    DISTANCE_MIN = 4  # Minimum distance between players and new bonuses
    MAX_BONUS = 4  # Maximum numbers of bonuses in the grid
    BONUS_CHANCE = 0.2  # Likelihood of a bonus appearing on each turn
    
    def apply(x, y, game, player):
        """Applies the bonus on the given player at the given position

        Args:
            x (int): x coordinate
            y (int): y coordinate
            game (Game): Game instance
            player (Player): player which has activated the bonus
        """
        pass
    
    def new_bonus(game):
        """Generates a new bonus

        Args:
            game (Game): Game instance
        """

        x, y = randint(0,game.WIDTH-1), randint(0,game.HEIGHT-1)
        id = randint(0,len(game.bonus_list)-1)
        if (x, y) in game.bonus_dict:
            Bonus.new_bonus(game)
            return
        for player in game.players:
            if abs(player.x-x) < Bonus.DISTANCE_MIN and abs(player.y-y) < Bonus.DISTANCE_MIN:
                Bonus.new_bonus(game)
                return
        game.bonus_dict[(x, y)] = id
    
    def try_spawn(game):
        """Tries to generate a new bonus. Called on every turn

        Args:
            game (Game): Game instance
        """

        if len(game.bonus_dict) < Bonus.MAX_BONUS and random() < Bonus.BONUS_CHANCE:
            Bonus.new_bonus(game)

class Bomb:
    """Bonus which places drool in a square area around the player"""

    TEXTURE = "bomb2.png"
    BOMB_SIZE = 5 # Drool bomb size in number of tiles
    
    def apply(x, y, game, player):
        player.use_bonus()
        sx, sy = max(ceil(x-(Bomb.BOMB_SIZE/2)),0), max(ceil(y-(Bomb.BOMB_SIZE/2)), 0)
        ex, ey = min(floor(x + Bomb.BOMB_SIZE/2), game.WIDTH-1)+1, min(floor(y + Bomb.BOMB_SIZE/2), game.HEIGHT-1)+1
        t = player.i if player.reinforced <= 0 else player.i + 2
        for by in range(sy, ey):
            for bx in range(sx, ex):
                game.set_trail(bx, by, t)

class Row:
    """Bonus which places drool on the player's current row"""

    TEXTURE = "row.png"
    def apply(x, y, game, player):
        player.use_bonus()
        t = player.i if player.reinforced <= 0 else player.i + 2
        for rx in range(0,game.WIDTH):
            game.set_trail(rx, y, t)

class Column:
    """Bonus which places drool on the player's current column"""

    TEXTURE = "column.png"
    def apply(x, y, game, player):
        player.use_bonus()
        t = player.i if player.reinforced <= 0 else player.i + 2
        for ry in range(0,game.HEIGHT):
            game.set_trail(x, ry, t)

class MagicalPotion:
    """Bonus which places makes the player's drool stronger for the next REINFORCED_TIME turns"""

    TEXTURE = "potion.png"
    REINFORCED_TIME = 4  # Number of tiles of reinforced drool for each potion
    
    def apply(x, y, game, player):
        player.use_bonus()
        player.reinforced += MagicalPotion.REINFORCED_TIME