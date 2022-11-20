class Player:
    COLORS = [(255,100,0), (0,100,255)]
    TRAIL_COLORS = [(255,150,100), (100,150,255)]
    OFFSETS = [
        (1,0),(0,1),(-1,0),(0,-1),
        (2,0),(0,2),(-2,0),(0,-2)
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
    
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.lx, self.ly = x, y
        self.nx, self.ny = x, y
        self.dir = self.i*2
        self.stun_count = 0
        self.synced = False