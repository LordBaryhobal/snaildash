class Player:
    COLORS = [(255,100,0), (0,100,255)]
    TRAIL_COLORS = [(255,150,100), (100,150,255)]
    MAX_DASHSCORE = 4  # Maximum dash tank value
    DASH_COST = 2  # Cost for one dash
    DASH_SIZE = 3  # Length of dash in tiles
    OFFSETS = [
        (1,0),(0,1),(-1,0),(0,-1),
        (DASH_SIZE,0),(0,DASH_SIZE),(-DASH_SIZE,0),(0,-DASH_SIZE)
    ]

    def __init__(self, game, i, x, y):
        self.game = game
        self.i = i
        self.x = x
        self.y = y
        self.lx, self.ly = x, y
        self.nx, self.ny = x, y
        self.dir = i*2  # 0, 1, 2, 3 -> right, down, left, up
        self.synced = False
        self.dashscore = 0
        self.dash = False

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.lx, self.ly = x, y
        self.nx, self.ny = x, y
        self.dir = self.i*2
        self.synced = False
        self.dashscore = 0
        self.dash = False
        self.reinforced = 0
        self.reinforced_placed = 0
        self.used_bonus = 0
        self.dashed_count = 0

    def candash(self):
        return self.dashscore >= self.DASH_COST
        
    def add_dashscore(self):
        self.dashscore = min(self.dashscore + 1, self.MAX_DASHSCORE)
        
    def usedash(self):
        self.dashscore -= 2
    
    def use_bonus(self):
        self.used_bonus += 1