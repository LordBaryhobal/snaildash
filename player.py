class Player:
    COLORS = [(255,100,0), (0,100,255)]
    TRAIL_COLORS = [(255,150,100), (100,150,255)]
    MAX_DASHSCORE = 4
    DASH_COST = 2
    DASH_SIZE = 3
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
        self.stun_count = 0
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
        self.stun_count = 0
        self.synced = False
        self.dashscore = 0
        self.dash = False
        
    def candash(self):
        return self.dashscore >= self.DASH_COST
        
    def add_dashscore(self):
        self.dashscore = min(self.dashscore + 1, self.MAX_DASHSCORE)
        
    def usedash(self):
        self.dashscore -= 2
