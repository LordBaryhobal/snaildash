from math import floor, ceil
from random import randint, random

class Bonus:
    DISTANCE_MIN = 4  # Minimum distance between players and new bonuses
    MAX_BONUS = 4  # Maximum numbers of bonuses in the grid
    BONUS_CHANCE = 0.2  # Likelihood of a bonus appearing on each turn
    
    def apply(x, y, game, player):
        pass
    
    def new_bonus(game):
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
        if len(game.bonus_dict) < Bonus.MAX_BONUS and random() < Bonus.BONUS_CHANCE:
            Bonus.new_bonus(game)

class Bomb:
    TEXTURE = "bomb2.png"
    BOMB_SIZE = 5 # Drool bomb size in number of tiles
    
    def apply(x, y, game, player):
        player.use_bonus()
        sx, sy = max(ceil(x-(Bomb.BOMB_SIZE/2)),0), max(ceil(y-(Bomb.BOMB_SIZE/2)), 0)
        ex, ey = min(floor(x + Bomb.BOMB_SIZE/2), game.WIDTH-1)+1, min(floor(y + Bomb.BOMB_SIZE/2), game.HEIGHT-1)+1
        t = player.i if player.poisoned <= 0 else player.i + 2
        for by in range(sy, ey):
            for bx in range(sx, ex):
                game.set_trail(bx, by, t)

class Row:
    TEXTURE = "row.png"
    def apply(x, y, game, player):
        player.use_bonus()
        t = player.i if player.poisoned <= 0 else player.i + 2
        for rx in range(0,game.WIDTH):
            game.set_trail(rx, y, t)

class Column:
    TEXTURE = "column.png"
    def apply(x, y, game, player):
        player.use_bonus()
        t = player.i if player.poisoned <= 0 else player.i + 2
        for ry in range(0,game.HEIGHT):
            game.set_trail(x, ry, t)

class MagicalPotion:
    TEXTURE = "poison.png"
    REINFORCED_TIME = 4  # Number of tiles of reinforced drool for each potion
    
    def apply(x, y, game, player):
        player.use_bonus()
        player.poisoned += MagicalPotion.POISON_TIME