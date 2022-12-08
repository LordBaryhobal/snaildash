from player import Player

class Game:
    WIDTH = 15  # Width of the grid
    HEIGHT = 15  # Height of the grid
    TIMER = 0.25  # Duration in seconds of a turn
    DURATION = 89  # Duration in seconds of the whole game
    COLLIDE_DURATION = 1  # Duration in seconds of the collision animation
    COLLIDE_RADIUS = 4  # Radius in number of tiles of the collision shockwave
    BOMB_SIZE = 5  # Drool bomb size in number of tiles
    DISTANCE_MIN = 4  # Minimum distance between players and new bonuses
    MAX_BONUS = 4  # Maximum numbers of bonuses in the grid
    BONUS_CHANCE = 0.2  # Likelihood of a bonus appearing on each turn
    REINFORCED_TIME = 4  # Number of tiles of reinforced drool for each potion
    
    def __init__(self, manager):
        self.manager = manager
        self.players = [
            Player(self, 0, 0, 0),
            Player(self, 1, self.WIDTH-1, self.HEIGHT-1)
        ]
    
    def is_host(self):
        return self.manager.is_host()
    
    def init_host(self):
        self.player = self.players[0]

    def init_guest(self):
        self.player = self.players[1]