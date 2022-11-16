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
        self.stun_count = 0
        self.dir = 0  # 0, 1, 2, 3 -> right, down, left, up
        self.synced = False